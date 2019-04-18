from graphics import Scene, Vec2, Point, Line, Polygon, Rect


class ObjCodec:
    @classmethod
    def encode_vec2(cls, v: Vec2) -> str:
        return f'{v.x} {v.y} 1.0'

    @classmethod
    def encode(cls, scene: Scene) -> str:
        # Writes a subset of the Wavefront OBJ file format in ASCII
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
            obj_type = type(obj)
            objects_txt += f'o {obj.name}\n'

            if obj_type == Point:
                vertices_txt += f'v {cls.encode_vec2(obj.pos)}\n'

                objects_txt += f'p {idx}\n'
                idx += 1
            elif obj_type == Line:
                vertices_txt += f'v {cls.encode_vec2(obj.start)}\n'
                vertices_txt += f'v {cls.encode_vec2(obj.end)}\n'

                objects_txt += f'l {idx} {idx + 1}\n'
                idx += 2
            elif obj_type == Polygon:
                n = len(obj.vertices)
                indexes = ''
                for i in range(0, n):
                    vertices_txt += f'v {cls.encode_vec2(obj.vertices[i])}\n'
                    indexes += f'{idx + i} '
                indexes += f'{idx}'

                if obj.filled:
                    objects_txt += f'usemtl filled\n'
                objects_txt += f'l {indexes}\n'
                idx += n

        return vertices_txt + objects_txt

    @classmethod
    def decode(cls, obj_file: str) -> Scene:
        # Returns a Scene with the window and objects found
        vertices = []
        objs = []
        window = None

        current_name = ''
        filled = False

        for line in obj_file.splitlines():
            cmd, *args = line.split(' ')

            if cmd == 'v':
                vertices.append(Vec2(float(args[0]), float(args[1])))
            elif cmd == 'o':
                current_name = args[0]
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
                window = Rect(
                    min=vertices[int(args[0]) - 1],
                    max=vertices[int(args[1]) - 1]
                )

        return Scene(objs=objs, window=window)
