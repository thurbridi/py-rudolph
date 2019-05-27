'''3D graphics API.'''
import math
from dataclasses import dataclass

import numpy as np
from cairo import Context

from graphics import GraphicObject, Polygon
from transformations import (
    offset_matrix_3d,
    scale_matrix_3d,
    rotation_matrix_3d,
    x_rotation_matrix_3d,
    y_rotation_matrix_3d,
    ndc_matrix,
)
from linalg import Vec2, Vec3


@dataclass
class Window3D:
    '''A window specific for 3D world.

    vpn (Vec3): View Plane Normal.'''
    min: Vec3
    max: Vec3
    vpn: Vec3


class GraphicObject3D(GraphicObject):
    def translate(self, offset: Vec3):
        self.transform(offset_matrix_3d(offset))

    def scale(self, factor: Vec3):
        self.transform(scale_matrix_3d(factor))

    def rotate(
        self,
        angle_x: float,
        angle_y: float,
        angle_z: float,
        reference: Vec3
    ):
        print(f'GraphicObject3D rotation')
        self.transform(
            offset_matrix_3d(-reference)
            @ rotation_matrix_3d(angle_x, angle_y, angle_z)
            @ offset_matrix_3d(reference)
        )

    def draw(
        self,
        cr: Context,
        vp_matrix: np.ndarray,
    ):
        self.filled = False
        Polygon.draw(self, cr, vp_matrix)

    def update_ndc(self, window: Window3D):
        vpn = Vec3(0, 0, 1)

        vpn_angle = Vec2(
            math.acos(vpn.x / math.sqrt(vpn.x ** 2 + vpn.y ** 2 + vpn.z ** 2)),
            math.asin(vpn.x / math.sqrt(vpn.x ** 2 + vpn.y ** 2 + vpn.z ** 2)),
        )

        v_t_matrix = (
            x_rotation_matrix_3d(vpn_angle.x)
            @ y_rotation_matrix_3d(vpn_angle.y)
        )

        v = [v @ v_t_matrix for v in self.vertices]
        v = [Vec2(v.x, v.y) for v in v]

        t_matrix = ndc_matrix(window)
        self.vertices_ndc = [v @ t_matrix for v in v]
