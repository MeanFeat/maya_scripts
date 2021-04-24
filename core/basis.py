from maya.api.OpenMaya import MMatrix, MVector, MQuaternion, MEulerRotation


class Basis:
    up_vector = MVector(0, 1, 0)

    def __init__(self, translation, rotation, offset, inclusive_matrix, inverse_matrix):  # type: (MVector, MQuaternion, MVector, MMatrix) -> None
        self.translation = translation
        self.rotation = rotation
        self.offset = offset
        self.inclusive_matrix = inclusive_matrix
        self.inverse_matrix = inverse_matrix
        self.x_vector = MVector(inclusive_matrix.getElement(0, 0), inclusive_matrix.getElement(0, 1), inclusive_matrix.getElement(0, 2))
        self.y_vector = MVector(inclusive_matrix.getElement(1, 0), inclusive_matrix.getElement(1, 1), inclusive_matrix.getElement(1, 2))
        self.z_vector = MVector(inclusive_matrix.getElement(2, 0), inclusive_matrix.getElement(2, 1), inclusive_matrix.getElement(2, 2))

    def set_offset(self, o):
        self.offset = o


def get_matrix_rotation(target, up, inv_mat):  # type: (MVector, MVector, MMatrix) -> MEulerRotation
    cross = target ^ up
    final = cross ^ target
    rot_mat = MMatrix([target.x, target.y, target.z, 0.,
                       cross.x, cross.y, cross.z, 0.,
                       final.x, final.y, final.z,
                       0., 0., 0., 0., 1.])
    final_matrix = rot_mat * inv_mat
    return MEulerRotation.decompose(final_matrix, MEulerRotation.kXYZ)
