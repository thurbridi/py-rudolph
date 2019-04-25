from math import cos, sin, radians
from typing import List

import numpy as np

from linalg import Vec2
from geometry import Rect


def offset_matrix(dx: float, dy: float) -> np.ndarray:
    return np.array(
        [
            1, 0, 0,
            0, 1, 0,
            dx, dy, 1,
        ],
        dtype=float
    ).reshape(3, 3)


def scale_matrix(sx: float, sy: float) -> np.ndarray:
    return np.array(
        [
            sx, 0, 0,
            0, sy, 0,
            0, 0, 1,
        ],
        dtype=float
    ).reshape(3, 3)


def rotation_matrix(angle: float) -> np.ndarray:
    angle = radians(angle)

    return np.array(
        [
            cos(angle), -sin(angle), 0,
            sin(angle), cos(angle), 0,
            0, 0, 1,
        ],
        dtype=float
    ).reshape(3, 3)


def ndc_matrix(window: Rect) -> np.ndarray:
    '''Normalized Device Coordinates Transformation.'''
    return (
        offset_matrix(-window.centroid.x, -window.centroid.y)
        @ rotation_matrix(-window.angle)
        @ scale_matrix(2 / window.width, 2 / window.height)
    )


def viewport_matrix(viewport: Rect) -> np.ndarray:
    '''Transform NDC coordinates into viewport coordinates.'''
    return (
        scale_matrix(viewport.width / 2, -viewport.height / 2)
        @ offset_matrix(viewport.centroid.x, viewport.centroid.y)
    )


def transformed(vertices: List[Vec2], matrix: np.ndarray) -> List[Vec2]:
    return [v @ matrix for v in vertices]


def translated(vertices: List[Vec2], offset: Vec2) -> List[Vec2]:
    return transformed(vertices, offset_matrix(offset.x, offset.y))

def rotated(vertices: List[Vec2], angle: float, reference: Vec2) -> List[Vec2]:
    refx = reference.x
    refy = reference.y
    t_matrix = (
        offset_matrix(-refx, -refy)
        @ rotation_matrix(angle)
        @ offset_matrix(refx, refy)
    )
    return transformed(vertices, t_matrix)

def scaled(vertices: List[Vec2], factor: Vec2) -> List[Vec2]:
    return transformed(vertices, scale_matrix(factor.x, factor.y))
