from maya.api.OpenMaya import MMatrix, MVector


class Basis:
    def __init__(self, transliation, offset, inclusive_matrix, inverse_matrix):  # type: (MVector, MVector, MMatrix, MMatrix) -> None
        self.translation = transliation
        self.offset = offset
        self.inclusive_matrix = inclusive_matrix
        self.inverse_matrix = inverse_matrix


def set_matrix_translation(matrix, translation):
    matrix.setElement(3, 0, translation.x)
    matrix.setElement(3, 1, translation.y)
    matrix.setElement(3, 2, translation.z)


def get_matrix_x(matrix):
    return MVector(matrix.getElement(0, 0), matrix.getElement(0, 1), matrix.getElement(0, 2))


def get_matrix_y(matrix):
    return MVector(matrix.getElement(1, 0), matrix.getElement(1, 1), matrix.getElement(1, 2))


def get_matrix_z(matrix):
    return MVector(matrix.getElement(2, 0), matrix.getElement(2, 1), matrix.getElement(2, 2))


def get_matrix_translation(matrix):
    return MVector(matrix.getElement(3, 0), matrix.getElement(3, 1), matrix.getElement(3, 2))


def get_matrix_components(matrix):
    x = get_matrix_x(matrix)
    y = get_matrix_y(matrix)
    z = get_matrix_z(matrix)
    return x, y, z, get_matrix_translation(matrix)


def build_rotation_matrix(target, up):  # type: (MVector, MVector) -> MMatrix
    cross = target ^ up
    final = cross ^ target
    rot_mat = MMatrix([target.x, target.y, target.z, 0.,
                       cross.x, cross.y, cross.z, 0.,
                       final.x, final.y, final.z,
                       0., 0., 0., 0., 1.])
    return rot_mat

