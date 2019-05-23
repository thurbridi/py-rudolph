from __future__ import annotations  # for postponed annotations
from pathlib import Path
from typing import List


from graphics import Vec2, GraphicObject, Point, Line, Polygon, Curve, Window
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
        idx = 1
        if scene.window is not None:
            vertices_txt += f'v {cls.encode_vec2(scene.window.min)}\n'
            vertices_txt += f'v {cls.encode_vec2(scene.window.max)}\n'

            objects_txt += f'o window\n'
            objects_txt += f'w {idx} {idx + 1}\n'
            idx += 2

        for obj in scene.objs:
            objects_txt += f'o {obj.name}\n'

            if isinstance(obj, Point):
                vertices_txt += f'v {cls.encode_vec2(obj.pos)}\n'

                objects_txt += f'p {idx}\n'
                idx += 1

            elif isinstance(obj, Line):
                vertices_txt += f'v {cls.encode_vec2(obj.start)}\n'
                vertices_txt += f'v {cls.encode_vec2(obj.end)}\n'

                objects_txt += f'l {idx} {idx + 1}\n'
                idx += 2

            elif isinstance(obj, Polygon):
                n = len(obj.vertices)
                indexes = ''
                for i in range(n):
                    vertices_txt += f'v {cls.encode_vec2(obj.vertices[i])}\n'
                    indexes += f'{idx + i} '
                indexes += f'{idx}'

                if obj.filled:
                    objects_txt += f'usemtl filled\n'
                objects_txt += f'l {indexes}\n'
                idx += n

            elif isinstance(obj, Curve):
                n = len(obj.vertices)
                indexes = ''
                for i in range(0, n):
                    vertices_txt += f'v {cls.encode_vec2(obj.vertices[i])}\n'
                    indexes += f'{idx + i} '
                indexes = indexes.strip()

                objects_txt += f'l {indexes}\n'
                idx += n

        return vertices_txt + objects_txt

    @classmethod
    def decode(cls, obj_file: str) -> 'Scene':
        from scene import Scene
        # Returns a Scene with the window and objects found
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
                elif args[0] == args[-1]:
                    objs.append(
                        Polygon(
                            vertices=[vertices[int(i) - 1] for i in args[:-1]],
                            name=current_name,
                            filled=filled
                        )
                    )
                    filled = False
                else:
                    objs.append(
                        Curve(
                            vertices=[vertices[int(i) - 1] for i in args],
                            name=current_name,
                        )
                    )
            elif cmd == 'w':
                window = Window(
                    min=vertices[int(args[0]) - 1],
                    max=vertices[int(args[1]) - 1]
                )

        return Scene(objs=objs, window=window)


def load_scene(path: Path) -> Scene:
    with open(path) as file:
        contents = file.read()
        return ObjCodec.decode(contents)


def save_scene(scene: Scene, path: Path):
    with open(path, 'w+') as file:
        contents = ObjCodec.encode(scene)
        file.write(contents)
