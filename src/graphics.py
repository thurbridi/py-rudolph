'''Contains displayable object definitions.'''
from abc import ABC, abstractmethod
from copy import deepcopy
from typing import Optional, List

import numpy as np
from cairo import Context

from linalg import Vec2, Vec3
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
        method: 'LineClippingMethod',
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
        for i in range(0, len(self.vertices_ndc)):
            next_vp = self.vertices_ndc[i] @ vp_matrix
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
    def __init__(self, vertices, type='bezier', name=''):
        super().__init__(vertices=vertices, name=name)
        self.control_points = vertices
        self.type = type
        self.vertices = self.create_curve()

    @property
    def n_curves(self) -> int:
        return int((len(self.control_points) - 1) / 3)

    def bezier_matrix(self):
        return np.array(
            [
                -1, 3, -3, 1,
                3, -6, 3, 0,
                -3, 3, 0, 0,
                1, 0, 0, 0
            ],
            dtype=float
        ).reshape(4, 4)

    def bspline_matrix(self):
        return np.array(
            [
                -1, 3, -3, 1,
                3, -6, 3, 0,
                -3, 0, 3, 0,
                1, 4, 1, 0
            ],
            dtype=float
        ).reshape(4, 4) / 6

    def ff_matrix(delta):
        d = delta
        return np.array([
                0, 0, 0, 1,
                d**3, d**2, d, 0,
                6*d**3, 2*d**2, 0, 0,
                6*d**3, 0, 0, 0,
            ],
            dtype=float
        ).reshape(4, 4)

    def create_curve(self, n_points=20):
        proj_x = np.array([v.x for v in self.control_points], dtype=float)
        proj_y = np.array([v.y for v in self.control_points], dtype=float)

        points = []

        if self.type == 'bezier':
            bezier_matrix = self.bezier_matrix()
            for k in range(0, self.n_curves * 3, 3):
                for t in np.linspace(0, 1, n_points):
                    T = np.array([t**3, t**2, t, 1], dtype=float)
                    M = T @ bezier_matrix
                    x = M @ proj_x[k:k + 4]
                    y = M @ proj_y[k:k + 4]
                    points.append(Vec2(x, y))
        elif self.type == 'b-spline':
            mbs = self.bspline_matrix()
            p = self.control_points

            gbs = [
                [
                    Vec3(*p[i-3]),
                    Vec3(*p[i-2]),
                    Vec3(*p[i-1]),
                    Vec3(*p[i]),
                ]
                for i in range(self.n_curves)
            ]

            C = mbs * gbs[0]

            dv = Curve.ff_matrix(1/n_points) * C

            v = Vec3(*p[0])
            points.append(v)

            print(f'gbs:\n{gbs}')
            print(f'C:\n{C}')
            print(f'v:\n{v}')
            print(f'dv:\n{dv}')

            for i in range(self.n_curves * 3):
                v += dv[0]
                dv[0] += dv[1]
                dv[1] += dv[2]

                points.append(deepcopy(v))
                print(f'v:\n{v}')
                print(f'points: {points}')

            points = [Vec2(*list(p)[:2]) for p in points]
            print(f'points: {points}')

        return points

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
