'''Contains displayable object definitions.'''
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Callable, List
from math import cos, sin, radians

from transformations import offset_matrix, scale_matrix, rotation_matrix

import numpy as np
from cairo import Context


np.set_printoptions(formatter={'float': lambda x: '{0:0.2f}, '.format(x)})


class Vec2(np.ndarray):
    def __new__(cls, x: float = 0, y: float = 0):
        obj = np.asarray([x, y, 1], dtype=float).view(cls)
        return obj

    @property
    def x(self) -> float:
        return self[0]

    @property
    def y(self) -> float:
        return self[1]


class Vec3(np.ndarray):
    def __new__(cls, x: float = 0, y: float = 0, z: float = 0):
        obj = np.asarray([x, y, z, 1], dtype=float).view(cls)
        return obj

    @property
    def x(self) -> float:
        return self[0]

    @property
    def y(self) -> float:
        return self[1]

    @property
    def z(self) -> float:
        return self[2]


TransformType = Callable[[Vec2], Vec2]


def identity(v: Vec2) -> Vec2:
    return v


@dataclass
class Rect:
    min: Vec2
    max: Vec2

    @property
    def width(self) -> float:
        return self.max.x - self.min.x

    @property
    def height(self) -> float:
        return self.max.y - self.min.y

    def offset(self, offset: Vec2):
        self.min += offset
        self.max += offset

    def rotate(self, angle: float):
        self.min = self.min @ rotation_matrix(angle)
        self.max = self.max @ rotation_matrix(angle)

    def zoom(self, amount: float):
        self.max *= amount
        self.min *= amount

    def center(self) -> Vec2:
        return (self.max + self.min) / 2

    def with_margin(self, margin: float) -> 'Rect':
        return Rect(
            self.min + Vec2(margin, margin),
            self.max - Vec2(margin, margin),
        )


@dataclass
class Viewport:
    region: Rect
    window: Rect

    @property
    def min(self) -> float:
        return self.region.min

    @property
    def max(self) -> float:
        return self.region.max

    @property
    def width(self) -> float:
        return self.region.width

    @property
    def height(self) -> float:
        return self.region.height

    def transform(self, p: Vec2) -> Vec2:
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

    def draw(self, cr: Context):
        _min = self.min
        _max = self.max

        cr.set_source_rgb(0.0, 0.8, 0.0)
        cr.move_to(_min.x, _min.y)
        for x, y in [
                (_max.x, _min.y),
                (_max.x, _max.y),
                (_min.x, _max.y),
                (_min.x, _min.y),
        ]:
            cr.line_to(x, y)
            cr.move_to(x, y)
        cr.stroke()


class GraphicObject(ABC):
    def __init__(self, name=''):
        super().__init__()
        self.name = name

    @abstractmethod
    def draw(
            self,
            cr: Context,
            viewport: Viewport,
            transform: TransformType,
    ):
        pass

    @abstractmethod
    def transform(self, matrix: np.ndarray):
        pass

    def translate(self, offset: Vec2):
        self.transform(offset_matrix(offset.x, offset.y))

    def scale(self, factor: Vec2):
        cx = self.centroid.x
        cy = self.centroid.y
        t_matrix = (
            offset_matrix(-cx, -cy) @
            scale_matrix(factor.x, factor.y) @
            offset_matrix(cx, cy)
        )
        self.transform(t_matrix)

    def rotate(self, angle: float, reference: Vec2):
        refx = reference.x
        refy = reference.y
        t_matrix = (
            offset_matrix(-refx, -refy) @
            rotation_matrix(angle) @
            offset_matrix(refx, refy)
        )
        self.transform(t_matrix)

    @abstractmethod
    def centroid():
        pass

    @abstractmethod
    def normalize(self, angle: float, window: Rect):
        pass


class Point(GraphicObject):
    def __init__(self, pos: Vec2, name=''):
        super().__init__(name)

        self.pos = pos
        self.normalize(0, Rect(min=Vec2(), max=Vec2()))

    @property
    def x(self) -> float:
        return self.pos[0]

    @property
    def y(self) -> float:
        return self.pos[1]

    def draw(
            self,
            cr: Context,
            viewport: Viewport,
            transform: TransformType = identity,
    ):
        coord_vp = self.normalized

        coord_vp = transform(coord_vp)
        cr.move_to(coord_vp.x, coord_vp.y)
        cr.arc(coord_vp.x, coord_vp.y, 1, 0, 2 * np.pi)
        cr.fill()

    def transform(self, matrix: np.ndarray):
        self.pos = self.pos @ matrix

    @property
    def centroid(self):
        return self.pos

    def normalize(self, angle: float, window: Rect):
        center = window.center()

        norm_matrix = (
            offset_matrix(-center.x, -center.y) @
            rotation_matrix(-angle) @
            offset_matrix(center.x, center.y)
        )

        self.normalized = self.pos @ norm_matrix


class Line(GraphicObject):
    def __init__(self, start: Vec2, end: Vec2, name=''):
        super().__init__(name)
        self.start = start
        self.end = end
        self.normalize(0, Rect(min=Vec2(), max=Vec2()))

    @property
    def x1(self):
        return self.start[0]

    @property
    def y1(self):
        return self.start[1]

    @property
    def x2(self):
        return self.end[0]

    @property
    def y2(self):
        return self.end[1]

    def draw(
            self,
            cr: Context,
            viewport: Viewport,
            transform: TransformType = identity
    ):
        scale = scale_matrix(viewport.region.width, viewport.region.height)

        coord_vp1 = transform(self.normalized[0])
        coord_vp2 = transform(self.normalized[1])

        cr.move_to(coord_vp1.x, coord_vp1.y)
        cr.line_to(coord_vp2.x, coord_vp2.y)
        cr.stroke()

    def transform(self, matrix: np.ndarray):
        self.start = self.start @ matrix
        self.end = self.end @ matrix

    @property
    def centroid(self):
        return (self.start + self.end) / 2

    def normalize(self, angle: float, window: Rect):
        center = window.center()

        norm_matrix = (
            offset_matrix(-center.x, -center.y) @
            rotation_matrix(-angle) @
            offset_matrix(center.x, center.y)
        )

        self.normalized = [
            self.start @ norm_matrix,
            self.end @ norm_matrix
        ]


class Polygon(GraphicObject):
    def __init__(self, vertices, name=''):
        self.name = name
        self.vertices = vertices
        self.normalized = self.vertices

    @property
    def centroid(self):
        center = np.sum(self.vertices, 0) / len(self.vertices)
        return Vec2(center[0], center[1])

    def draw(
            self,
            cr: Context,
            viewport: Viewport,
            transform: TransformType = identity
    ):
        start = self.normalized[0]
        start_vp = transform(Vec2(start[0], start[1]))
        cr.move_to(start_vp.x, start_vp.y)

        for i in range(1, len(self.vertices)):
            next = self.normalized[i]
            next_vp = transform(Vec2(next[0], next[1]))

            cr.line_to(next_vp.x, next_vp.y)
            cr.move_to(next_vp.x, next_vp.y)

        cr.line_to(start_vp.x, start_vp.y)
        cr.stroke()

    def transform(self, matrix: np.ndarray):
        for i, vertex in enumerate(self.vertices):
            self.vertices[i] = vertex @ matrix

    def normalize(self, angle: float, window: Rect):
        center = window.center()
        norm_matrix = (
            offset_matrix(-center.x, -center.y) @
            rotation_matrix(-angle) @
            offset_matrix(center.x, center.y)
        )

        self.normalized = [
            vertex @ norm_matrix
            for vertex in self.vertices
        ]


@dataclass
class Scene:
    objs: List[GraphicObject]
    window: Rect = None
