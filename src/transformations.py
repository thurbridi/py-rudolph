import numpy as np
from math import cos, sin, radians


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
