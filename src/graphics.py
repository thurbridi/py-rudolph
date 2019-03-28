'''Contains displayable object definitions.'''
import numpy as np
from abc import ABC, abstractmethod
from typing import NamedTuple


class Vec2(np.ndarray):
    def __new__(cls, x: int, y: int):
        obj = np.asarray([x, y]).view(cls)
        return obj

    @property
    def x(self):
        return self[0]

    @property
    def y(self):
        return self[1]


class Rect():
    def __init__(self, min, max):
        self.min = np.array(min, dtype=float)
        self.max = np.array(max, dtype=float)

    @property
    def xmin(self):
        return self.min[0]

    @property
    def ymin(self):
        return self.min[1]

    @property
    def xmax(self):
        return self.max[0]

    @property
    def ymax(self):
        return self.max[1]

    @property
    def width(self):
        return self.xmax - self.xmin

    @property
    def height(self):
        return self.ymax - self.ymin


class Viewport(NamedTuple):
    min: Vec2
    max: Vec2
    window: Rect

    def transform(self, p: Vec2):
        if not isinstance(p, Vec2):
            p = Vec2(p[0], p[1])

        view_size = Vec2(
            self.max.x - self.min.x,
            self.max.y - self.min.y
        )

        win_size = Vec2(
            self.window.max.x - self.window.min.x,
            self.window.max.y - self.window.min.y
        )
        return Vec2(
            (p.x - self.min.x) * view_size.x / win_size.x,
            (p.y - self.min.y) * view_size.y / win_size.y,
        )



class GraphicObject(ABC):
    def __init__(self, name=''):
        super().__init__()
        self.name = name

    @abstractmethod
    def draw(self, cr, transform):
        pass


class Point(GraphicObject):
    def __init__(self, pos: Vec2, name=''):
        super().__init__(name)

        self.pos = np.array(pos, dtype=float)

    @property
    def x(self):
        return self.pos[0]

    @property
    def y(self):
        return self.pos[1]

    def draw(self, cr, transform=lambda v: v):
        coord_vp = transform(Vec2(self.x, self.y))
        cr.move_to(coord_vp.x, coord_vp.y)
        cr.arc(coord_vp.x, coord_vp.y, 1, 0, 2 * np.pi)
        cr.fill()


class Line(GraphicObject):
    def __init__(self, start: Vec2, end: Vec2, name=''):
        super().__init__(name)

        self.points = np.array([start, end], dtype=float)

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

    def draw(self, cr, transform=lambda v: v):
        coord_vp1 = transform(Vec2(self.x1, self.y1))
        coord_vp2 = transform(Vec2(self.x2, self.y2))

        cr.move_to(coord_vp1.x, coord_vp1.y)
        cr.line_to(coord_vp2.x, coord_vp2.y)
        cr.stroke()


class Polygon(GraphicObject):
    def __init__(self, vertices, name=''):
        self.name = name
        self.vertices = np.array(vertices, dtype=float)

    def draw(self, cr, transform=lambda v: v):
        start = self.vertices[0, :]
        start_vp = transform(Vec2(start[0], start[1]))
        cr.move_to(start_vp.x, start_vp.y)

        for i in range(1, len(self.vertices)):
            next = self.vertices[i, :]
            next_vp = transform(Vec2(next[0], next[1]))

            cr.line_to(next_vp.x, next_vp.y)
            cr.move_to(next_vp.x, next_vp.y)

        cr.line_to(start_vp.x, start_vp.y)
        cr.stroke()
