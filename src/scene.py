import numpy as np
from typing import List, Iterable

from linalg import Vec2
from graphics import GraphicObject, Window
from cgcodecs import ObjCodec


class Scene:
    def __init__(self, objs: List[GraphicObject] = [], window: Window = None):
        self.objs = objs
        self.window = window

    def add_object(self, obj: GraphicObject):
        self.objs.append(obj)

    def remove_objects(self, indexes: Reversible[int]):
        for i in reversed(indexes):
            self.objs.pop(i)

    def translate_window(self, offset: Vec2):
        self.window.translate(offset)

    def zoom_window(self, factor: float):
        self.window.scale(Vec2(factor, factor))

    def rotate_window(self):
        pass

    def clip_objects(self):
        pass

