from maya.api.OpenMaya import MMatrix, MVector, MQuaternion, MEulerRotation


class Basis:
    up_vector = MVector(0, 1, 0)

    def __init__(self, translation, rotation, offset, exclusive_matrix, inclusive_matrix, inverse_matrix):  # type: (MVector, MQuaternion, MVector, MMatrix, MMatrix, MMatrix) -> None
        self.translation = translation
        self.rotation = rotation
        self.offset = offset
        self.exclusive_matrix = exclusive_matrix
        self.inclusive_matrix = inclusive_matrix
        self.inverse_matrix = inverse_matrix
        self.x_vector = MVector(inclusive_matrix.getElement(0, 0), inclusive_matrix.getElement(0, 1), inclusive_matrix.getElement(0, 2))
        self.y_vector = MVector(inclusive_matrix.getElement(1, 0), inclusive_matrix.getElement(1, 1), inclusive_matrix.getElement(1, 2))
        self.z_vector = MVector(inclusive_matrix.getElement(2, 0), inclusive_matrix.getElement(2, 1), inclusive_matrix.getElement(2, 2))

    def set_offset(self, o):
        self.offset = o


def build_rotation_matrix(target, up): # type: (MVector, MVector) -> MMatrix
    cross = target ^ up
    final = cross ^ target
    rot_mat = MMatrix([target.x, target.y, target.z, 0.,
                       cross.x, cross.y, cross.z, 0.,
                       final.x, final.y, final.z,
                       0., 0., 0., 0., 1.])
    return rot_mat

