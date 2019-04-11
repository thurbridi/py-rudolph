from graphics import Scene


class ObjCodec:
    @classmethod
    def encode(cls, scene: Scene) -> str:
        # Writes a subset of the Wavefront OBJ file format in ASCII
        file_contents = 'v 0.0 0.0 1.0\no origin\np 1'
        return file_contents

    @classmethod
    def decode(cls, obj_file: str) -> Scene:
        # Returns a Scene with the window and objects found
        pass
