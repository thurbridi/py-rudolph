import numpy as np
from math import cos, sin, radians

from linalg import Vec3


# ------------------------------------------------------------------------------
# 2D transformations
# ------------------------------------------------------------------------------


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


def ndc_matrix(window: 'Window') -> np.ndarray:
    '''Matrix for transforming world coordinates into Normalized Device
    Coordinates'''
    return (
        offset_matrix(-window.centroid.x, -window.centroid.y)
        @ rotation_matrix(-window.angle)
        @ scale_matrix(2 / window.width, 2 / window.height)
    )


def viewport_matrix(viewport: 'Rect') -> np.ndarray:
    '''Matrix for transforming Normalized Device Coordinates into viewport
    coordinates'''
    return (
        scale_matrix(viewport.width / 2, -viewport.height / 2)
        @ offset_matrix(viewport.centroid.x, viewport.centroid.y)
    )


# ------------------------------------------------------------------------------
# 3D transformations
# ------------------------------------------------------------------------------


def offset_matrix_3d(offset: Vec3) -> np.ndarray:
    return np.array(
        [
            1, 0, 0, 0,
            0, 1, 0, 0,
            0, 0, 1, 0,
            offset.x, offset.y, offset.z, 1,
        ],
        dtype=float
    ).reshape(4, 4)


def scale_matrix_3d(scale: Vec3) -> np.ndarray:
    return np.array(
        [
            scale.x, 0, 0, 0,
            0, scale.y, 0, 0,
            0, 0, scale.z, 0,
            0, 0, 0, 1,
        ],
        dtype=float
    ).reshape(3, 3)


def x_rotation_matrix_3d(angle: float) -> np.ndarray:
    '''Creates a 3D rotation matrix over the X axis.'''
    return np.array(
        [
            1, 0, 0, 0,
            0, cos(angle), sin(angle), 0,
            0, -sin(angle), cos(angle), 0,
            0, 0, 0, 1,
        ],
        dtype=float
    ).reshape(4, 4)


def y_rotation_matrix_3d(angle: float) -> np.ndarray:
    '''Creates a 3D rotation matrix over the Y axis.'''
    return np.array(
        [
            cos(angle), 0, -sin(angle), 0,
            0, 1, 0, 0,
            sin(angle), 0, cos(angle), 0,
            0, 0, 0, 1,
        ],
        dtype=float
    ).reshape(4, 4)


def z_rotation_matrix_3d(angle: float) -> np.ndarray:
    '''Creates a 3D rotation matrix over the Z axis.'''
    return np.array(
        [
            cos(angle), sin(angle), 0, 0,
            -sin(angle), cos(angle), 0, 0,
            0, 0, 1, 0,
            0, 0, 0, 1,
        ],
        dtype=float
    ).reshape(4, 4)


def rotation_matrix_3d(
    angle_x: float,
    angle_y: float,
    angle_z: float,
) -> np.ndarray:
    '''Creates a 3D rotation matrix in X -> Y -> Z order.'''
    angle_x, angle_y, angle_z = (
        radians(angle) for angle in (angle_x, angle_y, angle_z)
    )

    return (
        x_rotation_matrix_3d(angle_x) @
        y_rotation_matrix_3d(angle_y) @
        z_rotation_matrix_3d(angle_z)
    )
