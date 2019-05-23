'''3D graphics API.'''
from graphics import GraphicObject
from transformations import (
    offset_matrix_3d,
    scale_matrix_3d,
    rotation_matrix_3d,
)

from linalg import Vec3


class GraphicObject3D(GraphicObject):
    def translate(self, offset: Vec3):
        self.transform(offset_matrix_3d(offset))

    def scale(self, factor: Vec3):
        self.transform(scale_matrix_3d(factor))

    def rotate_3d(
        self,
        angle_x: float,
        angle_y: float,
        angle_z: float,
        reference: Vec3
    ):
        self.transform(
            offset_matrix_3d(-reference)
            @ rotation_matrix_3d(angle_x, angle_y, angle_z)
            @ offset_matrix_3d(reference)
        )
