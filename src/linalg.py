'''Linear Algebra functions and definitions.'''
from typing import Callable

import numpy as np


class Vec2(np.ndarray):
    def __new__(cls, x: float = 0, y: float = 0):
        obj = np.asarray([x, y, 1], dtype=float).view(cls)
        return obj

    @property
    def x(self) -> float:
        return self[0]

    @x.setter
    def x(self, value):
        self[0] = value

    @property
    def y(self) -> float:
        return self[1]

    @y.setter
    def y(self, value):
        self[1] = value


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
