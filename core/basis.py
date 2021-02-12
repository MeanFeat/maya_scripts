from maya.api.OpenMaya import MEulerRotation, MMatrix, MVector


class Basis:
    def __init__(self, translation, rotation, offset, inclusive_matrix):  # type: (MVector, MEulerRotation, MVector, MMatrix) -> None
        self.translation = translation
        self.rotation = rotation
        self.offset = offset
        self.inclusive_matrix = inclusive_matrix
        self.x_vector = MVector(inclusive_matrix.getElement(0, 0), inclusive_matrix.getElement(0, 1), inclusive_matrix.getElement(0, 2))
        self.y_vector = MVector(inclusive_matrix.getElement(1, 0), inclusive_matrix.getElement(1, 1), inclusive_matrix.getElement(1, 2))
        self.z_vector = MVector(inclusive_matrix.getElement(2, 0), inclusive_matrix.getElement(2, 1), inclusive_matrix.getElement(2, 2))

    def set_offset(self, o):
        self.offset = o
