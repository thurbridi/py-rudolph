from typing import List, Optional, Reversible


from linalg import Vec2
from graphics import GraphicObject, Window
from cgcodecs import ObjCodec


class Scene:
    def __init__(self, objs: List[GraphicObject] = [], window: Window = None):
        self.objs = objs
        self.window: Optional[Window] = window

    def add_object(self, obj: GraphicObject):
        if self.window is not None:
            obj.update_ndc(self.window)
        self.objs.append(obj)

    def remove_objects(self, indexes: Reversible[int]):
        for i in reversed(indexes):
            self.objs.pop(i)

    def translate_window(self, offset: Vec2):
        if self.window is not None:
            self.window.translate(offset)
        self.update_ndc()

    def zoom_window(self, factor: float):
        if self.window is not None:
            self.window.scale(Vec2(factor, factor))
        self.update_ndc()

    def rotate_window(self):
        pass
        self.update_ndc()

    def update_ndc(self):
        for obj in self.objs:
            obj.update_ndc(self.window)

    @classmethod
    def load(self, path: str):
        with open(path) as file:
            contents = file.read()
            return ObjCodec.decode(contents)

    def save(self, path: str):
        with open(path, 'w+') as file:
            contents = ObjCodec.encode(self)
            file.write(contents)

    def clip_objects(self):
        pass
