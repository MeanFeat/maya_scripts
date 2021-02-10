from maya.api.OpenMaya import MEulerRotation, MMatrix, MVector


class Basis:
    def __init__(self, translation, rotation, offset, matrix):  # type: (MVector, MEulerRotation, MVector, MMatrix) -> None
        self.translation = translation
        self.rotation = rotation
        self.offset = offset
        self.matrix = matrix
        self.x_vector = MVector(matrix.getElement(0, 0), matrix.getElement(0, 1), matrix.getElement(0, 2))
        self.y_vector = MVector(matrix.getElement(1, 0), matrix.getElement(1, 1), matrix.getElement(1, 2))
        self.z_vector = MVector(matrix.getElement(2, 0), matrix.getElement(2, 1), matrix.getElement(2, 2))
