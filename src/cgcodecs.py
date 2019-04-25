from typing import List

from graphics import GraphicObject, Vec2, Point, Line, Polygon, Window
from scene import Scene


class ObjCodec:
    @classmethod
    def encode_vec2(cls, v: Vec2) -> str:
        return f'{v.x} {v.y} 1.0'

    @classmethod
    def encode(cls, scene: Scene) -> str:
        '''Writes a subset of the Wavefront OBJ file format in ASCII.'''
        vertices_txt = ''
        objects_txt = ''
        index = 1

        if scene.window is not None:
            vertices_txt += f'v {cls.encode_vec2(scene.window.min)}\n'
            vertices_txt += f'v {cls.encode_vec2(scene.window.max)}\n'

            objects_txt += f'o window\n'
            objects_txt += f'w {index} {index + 1}\n'
            index += 2

        for obj in scene.objs:
            objects_txt += f'o {obj.name}\n'

            if isinstance(obj, Point):
                vertices_txt += f'v {cls.encode_vec2(obj.pos)}\n'

                objects_txt += f'p {index}\n'
            elif isinstance(obj, Line):
                vertices_txt += f'v {cls.encode_vec2(obj.start)}\n'
                vertices_txt += f'v {cls.encode_vec2(obj.end)}\n'

                objects_txt += f'l {index} {index + 1}\n'
            elif isinstance(obj, Polygon):
                indexes = ''

                for i, v in enumerate(obj.vertices):
                    vertices_txt += f'v {cls.encode_vec2(obj.vertices[i])}\n'
                    indexes += f'{index + i} '
                indexes += f'{index}'

                if obj.filled:
                    objects_txt += f'usemtl filled\n'
                objects_txt += f'l {indexes}\n'
            index += len(obj.vertices)

        return vertices_txt + objects_txt

    @classmethod
    def decode(cls, obj_file: str) -> Scene:
        '''Returns a Scene with the window and objects found.'''
        vertices = []
        objs: List[GraphicObject] = []
        window = None

        current_name = ''
        filled = False

        for line in obj_file.splitlines():
            cmd, *args = line.split(' ')

            if cmd == 'v':
                vertices.append(Vec2(float(args[0]), float(args[1])))
            elif cmd == 'o':
                current_name = ' '.join(args)
            elif cmd == 'usemtl':
                if args[0] == 'filled':
                    filled = True
            elif cmd == 'p':
                objs.append(
                    Point(pos=vertices[int(args[0]) - 1], name=current_name)
                )
            elif cmd == 'l':
                if len(args) == 2:
                    objs.append(
                        Line(
                            start=vertices[int(args[0]) - 1],
                            end=vertices[int(args[1]) - 1],
                            name=current_name
                        )
                    )
                else:
                    objs.append(
                        Polygon(
                            vertices=[vertices[int(i) - 1] for i in args[:-1]],
                            name=current_name,
                            filled=filled
                        )
                    )
                    filled = False
            elif cmd == 'w':
                window = Window(
                    min=vertices[int(args[0]) - 1],
                    max=vertices[int(args[1]) - 1]
                )

        return Scene(objs=objs, window=window)
