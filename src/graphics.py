from abc import ABC, abstractmethod
import numpy as np
from collections import namedtuple


Vec2 = namedtuple('Vec2', ['x', 'y'])


class GraphicObject(ABC):
    def __init__(self, name=""):
        super().__init__()
        self.name = name

    @abstractmethod
    def draw():
        pass


class Point(GraphicObject):
    def __init__(self, x=0, y=0, name=""):
        super().__init__(name)

        self.coord = np.array([x, y], dtype=float)

    @property
    def x(self):
        return self.coord[0]

    @property
    def y(self):
        return self.coord[1]

    def draw(self, cr):
        cr.move_to(self.x, self.y)
        cr.arc(self.x, self.y, 1, 0, 2 * np.pi)


class Line(GraphicObject):
    def __init__(self, x1=0, y1=0, x2=0, y2=0, name=""):
        super().__init__(name)

        self.points = np.array([[x1, y1], [x2, y2]], dtype=float)

    @property
    def x1(self):
        return self.points[0, 0]

    @property
    def y1(self):
        return self.points[0, 1]

    @property
    def x2(self):
        return self.points[1, 0]

    @property
    def y2(self):
        return self.points[1, 1]

    def draw(self, cr):
        cr.move_to(self.x1, self.y1)
        cr.line_to(self.x2, self.y2)


class Polygon(GraphicObject):
    def __init__(self, vertices, name=""):
        self.name = name
        self.vertices = np.array(vertices, dtype=float)

    def draw(self, cr):
        start = self.vertices[0, :]
        cr.move_to(start[0], start[1])

        for i in range(1, len(self.vertices)):
            next = self.vertices[i, :]
            cr.line_to(next[0], next[1])
            cr.move_to(next[0], next[1])

        cr.line_to(start[0], start[1])
