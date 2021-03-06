'''Contains displayable object definitions.'''
from abc import ABC, abstractmethod
from typing import Any, Optional, List

import numpy as np
from cairo import Context

from linalg import Vec2
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
        self.vertices_ndc: List[Vec2] = vertices

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
        method: Optional[Any] = None,
    ) -> Optional['GraphicObject']:
        return self


class Point(GraphicObject):
    def __init__(self, pos: Vec2, name=''):
        super().__init__(vertices=[pos], name=name)

    @property
    def pos(self) -> Vec2:
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

    def clipped(self, *args, **kwargs) -> Optional['Point']:
        pos = self.vertices_ndc[0]

        return (
            self if (pos.x >= -1
                     and pos.x <= 1
                     and pos.y >= -1
                     and pos.y <= 1)
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

    def draw(self, cr: Context, vp_matrix: np.ndarray):
        start_vp, end_vp = [v @ vp_matrix for v in self.vertices_ndc]

        cr.move_to(start_vp.x, start_vp.y)
        cr.line_to(end_vp.x, end_vp.y)
        cr.stroke()

    def clipped(
        self,
        method: Optional['LineClippingMethod'] = None,
    ) -> Optional[GraphicObject]:
        from clipping import line_clip

        return line_clip(self, method)


class Polygon(GraphicObject):
    def __init__(self, vertices, name='', filled=False):
        super().__init__(vertices=vertices, name=name)
        self.filled = filled

    def draw(
            self,
            cr: Context,
            vp_matrix: np.ndarray
    ):
        for v in self.vertices_ndc:
            next_vp = v @ vp_matrix
            cr.line_to(next_vp.x, next_vp.y)
        cr.close_path()

        if self.filled:
            cr.stroke_preserve()
            cr.fill()
        else:
            cr.stroke()

    def clipped(self, *args, **kwargs) -> Optional['Polygon']:
        from clipping import poly_clip

        return poly_clip(self)


class Curve(GraphicObject):
    def __init__(self, vertices, name=''):
        super().__init__(vertices=vertices, name=name)

    @classmethod
    def from_control_points(
        cls,
        control_points,
        type='bezier',
        name='',
        n_points=20
    ):
        proj_x = np.array([v.x for v in control_points], dtype=float)
        proj_y = np.array([v.y for v in control_points], dtype=float)

        vertices = []
        if type == 'bezier':
            for i in range(0, len(control_points) - 1, 3):
                for t in np.linspace(0, 1, n_points):
                    T = np.array([t**3, t**2, t, 1], dtype=float)
                    M = T @ cls.bezier_matrix()
                    x = M @ proj_x[i:i + 4]
                    y = M @ proj_y[i:i + 4]
                    vertices.append(Vec2(x, y))
        elif type == 'b-spline':
            for i in range(0, len(control_points) - 3):
                Gbs_x = proj_x[i:i + 4]
                Gbs_y = proj_y[i:i + 4]

                Cx = cls.bspline_matrix() @ Gbs_x
                Cy = cls.bspline_matrix() @ Gbs_y

                Dx = cls.fd_matrix(1.0 / n_points) @ Cx
                Dy = cls.fd_matrix(1.0 / n_points) @ Cy

                for k in range(n_points + 1):
                    x = Dx[0]
                    y = Dy[0]
                    print(f'{k}:')
                    print(f'\tx={x}')
                    print(f'\ty={y}')

                    Dx = Dx + np.append(Dx[1:], 0)
                    Dy = Dy + np.append(Dy[1:], 0)

                    vertices.append(Vec2(x, y))

        return cls(vertices, name=name)

    @classmethod
    def bezier_matrix(cls):
        return np.array(
            [
                -1, 3, -3, 1,
                3, -6, 3, 0,
                -3, 3, 0, 0,
                1, 0, 0, 0
            ],
            dtype=float
        ).reshape(4, 4)

    @classmethod
    def bspline_matrix(cls):
        return np.array(
            [
                -1, 3, -3, 1,
                3, -6, 3, 0,
                -3, 0, 3, 0,
                1, 4, 1, 0
            ],
            dtype=float
        ).reshape(4, 4) / 6

    @classmethod
    def fd_matrix(cls, delta):
        return np.array(
            [
                0, 0, 0, 1,
                delta**3, delta**2, delta, 0,
                6 * delta**3, 2 * delta**2, 0, 0,
                6 * delta**3, 0, 0, 0,
            ],
            dtype=float
        ).reshape(4, 4)

    def draw(self, cr: Context, vp_matrix: np.ndarray):
        for i in range(len(self.vertices_ndc)):
            next_vp = self.vertices_ndc[i] @ vp_matrix
            cr.line_to(next_vp.x, next_vp.y)
        cr.stroke()

    def clipped(self, *args, **kwargs):
        from clipping import curve_clip
        return curve_clip(self)


class Rect(GraphicObject):
    def __init__(self, min: Vec2, max: Vec2, name=''):
        super().__init__(vertices=[min, max], name=name)

    @property
    def min(self) -> Vec2:
        return self.vertices[0]

    @min.setter
    def min(self, value: Vec2):
        self.vertices[0] = value

    @property
    def max(self) -> Vec2:
        return self.vertices[1]

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
        vp_matrix: np.ndarray
    ):
        _min = self.min
        _max = self.max

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

    def with_margin(self, margin: float) -> 'Rect':
        return Rect(
            self.min + Vec2(margin, margin),
            self.max - Vec2(margin, margin),
        )


class Window(Rect):
    def __init__(self, min: Vec2, max: Vec2, angle: float = 0.0):
        super().__init__(min, max)
        self.angle = angle
