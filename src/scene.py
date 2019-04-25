import numpy as np
from typing import List, Reversible, Iterable

from geometry import Vec2
from graphics import GraphicObject, Window
from transformations import translated, rotated, scaled


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
        if self.window is not None:
            self.window.min, self.window.max = (
                translated([self.window.min, self.window.max], offset)
            )

    def zoom_window(self, factor: float):
        if self.window is not None:
            self.window.min, self.window.max = (
                scaled([self.window.min, self.window.max], Vec2(factor, factor))
            )

    def rotate_window(self):
        pass

    def clip_objects(self):
        pass

