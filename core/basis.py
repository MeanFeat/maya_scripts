from maya.api.OpenMaya import MMatrix, MVector


class Basis:
    def __init__(self, transliation, offset, inclusive_matrix, inverse_matrix):  # type: (MVector, MVector, MMatrix, MMatrix) -> None
        self.translation = transliation
        self.offset = offset
        self.inclusive_matrix = inclusive_matrix
        self.inverse_matrix = inverse_matrix


def build_rotation_matrix(target, up):  # type: (MVector, MVector) -> MMatrix
    cross = target ^ up
    final = cross ^ target
    rot_mat = MMatrix([target.x, target.y, target.z, 0.,
                       cross.x, cross.y, cross.z, 0.,
                       final.x, final.y, final.z,
                       0., 0., 0., 0., 1.])
    return rot_mat

