'''Contains displayable object definitions.'''
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, List

import numpy as np
from cairo import Context

from linalg import Vec2, TransformType
from transformations import (
    offset_matrix,
    scale_matrix,
    rotation_matrix,
    ndc_matrix
)

np.set_printoptions(formatter={'float': lambda x: '{0:0.2f}'.format(x)})


class GraphicObject(ABC):
    def __init__(self, vertices=[], name=''):
        super().__init__()
        self.name = name
        self.vertices: List[Vec2] = vertices
        self.vertices_ndc: List[Vec2] = []

    @abstractmethod
    def draw(
            self,
            cr: Context,
            vp_matrix: np.ndarray
    ):
        pass

    @property
    def centroid(self):
        return sum(self.vertices) / len(self.vertices)

    def update_ndc(self, window: 'Window'):
        t_matrix = ndc_matrix(window)
        self.vertices_ndc = [v @ t_matrix for v in self.vertices]

    def transform(self, matrix: np.ndarray):
        self.vertices = [v @ matrix for v in self.vertices]

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
            offset_matrix(-refx, -refy)
            @ rotation_matrix(angle)
            @ offset_matrix(refx, refy)
        )
        self.transform(t_matrix)

    def clipped(
        self,
        window: 'Window',
        method=None,
    ) -> Optional['GraphicObject']:
        return self


class Point(GraphicObject):
    def __init__(self, pos: Vec2, name=''):
        super().__init__(vertices=[pos], name=name)

    @property
    def pos(self) -> float:
        return self.vertices[0]

    @pos.setter
    def pos(self, value: Vec2):
        self.vertices[0] = value

    def draw(
            self,
            cr: Context,
            vp_matrix: np.ndarray
    ):
        pos_vp = self.vertices_ndc[0] @ vp_matrix
        cr.move_to(pos_vp.x, pos_vp.y)
        cr.arc(pos_vp.x, pos_vp.y, 1, 0, 2 * np.pi)
        cr.fill()

    def clipped(self, window: 'Window', *args, **kwargs) -> Optional['Point']:
        wmin = window.min
        wmax = window.max
        pos = self.pos

        return (
            self if (pos.x >= wmin.x
                     and pos.x <= wmax.x
                     and pos.y >= wmin.y
                     and pos.y <= wmax.y)
            else None
        )


class Line(GraphicObject):
    def __init__(self, start: Vec2, end: Vec2, name=''):
        super().__init__(vertices=[start, end], name=name)

    @property
    def start(self):
        return self.vertices[0]

    @start.setter
    def start(self, value: Vec2):
        self.vertices[0] = value

    @property
    def end(self):
        return self.vertices[1]

    @end.setter
    def end(self, value: Vec2):
        self.vertices[1] = value

    def draw(
            self,
            cr: Context,
            vp_matrix: np.ndarray
    ):
        start_vp, end_vp = [v @ vp_matrix for v in self.vertices_ndc]

        cr.move_to(start_vp.x, start_vp.y)
        cr.line_to(end_vp.x, end_vp.y)
        cr.stroke()

    def clipped(
        self,
        window: 'Window',
        method: 'LineClippingMethod',
    ) -> Optional[GraphicObject]:
        from clipping import line_clip
        center = window.centroid

        m = (
            offset_matrix(-center.x, -center.y) @
            rotation_matrix(-window.angle) @
            offset_matrix(center.x, center.y)
        )

        line = Line(self.start @ m, self.end @ m)

        return line_clip(line, window, method)


class Polygon(GraphicObject):
    def __init__(self, vertices, name='', filled=False):
        super().__init__(vertices=vertices, name=name)
        self.filled = filled

    def draw(
            self,
            cr: Context,
            vp_matrix: np.ndarray
    ):
        for i in range(0, len(self.vertices)):
            next_vp = self.vertices_ndc[i] @ vp_matrix
            cr.line_to(next_vp.x, next_vp.y)
        cr.close_path()

        if self.filled:
            cr.stroke_preserve()
            cr.fill()
        else:
            cr.stroke()

    def clipped(
        self,
        window: 'Window',
        method: 'LineClippingMethod',
    ) -> Optional['Polygon']:
        from clipping import poly_clip
        center = window.centroid

        m = (
            offset_matrix(-center.x, -center.y) @
            rotation_matrix(-window.angle) @
            offset_matrix(center.x, center.y)
        )

        p = Polygon([v @ m for v in self.vertices], filled=self.filled)

        return poly_clip(p, window, method)


class Rect(GraphicObject):
    def __init__(self, min: Vec2, max: Vec2, name=''):
        super().__init__(vertices=[min, max], name=name)

    @property
    def min(self):
        return self.vertices[0]

    @property
    def max(self):
        return self.vertices[1]

    @min.setter
    def min(self, value: Vec2):
        self.vertices[0] = value

    @max.setter
    def max(self, value: Vec2):
        self.vertices[1] = value

    @property
    def width(self) -> float:
        return self.max.x - self.min.x

    @property
    def height(self) -> float:
        return self.max.y - self.min.y

    def draw(
            self,
            cr: Context,
            viewport: 'Viewport',
            transform: TransformType,
    ):
        pass

    def with_margin(self, margin: float) -> 'Rect':
        return Rect(
            self.min + Vec2(margin, margin),
            self.max - Vec2(margin, margin),
        )


class Window(Rect):
    def __init__(self, min: Vec2, max: Vec2, angle: float = 0.0):
        super().__init__(min, max)
        self.angle = angle


@dataclass
class Viewport:
    region: Rect
    window: Window

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

        cr.set_source_rgb(0.4, 0.4, 0.4)
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
