from maya.api.OpenMaya import MMatrix, MVector


class Basis:
    def __init__(self, transliation, offset, inclusive_matrix, inverse_exclusive_matrix):  # type: (MVector, MVector, MMatrix, MMatrix) -> None
        self.translation = transliation
        self.offset = offset
        self.inclusive_matrix = inclusive_matrix
        self.inverse_exclusive_matrix = inverse_exclusive_matrix


def build_plane_normal(a, b, c):  # type: (MVector, MVector, MVector) -> MVector
    x = ((b.y - a.y) * (c.z - a.z)) - ((b.z - a.z) * (c.y - a.y))
    y = ((b.z - a.z) * (c.x - a.x)) - ((b.x - a.x) * (c.z - a.z))
    z = ((b.x - a.x) * (c.y - a.y)) - ((b.y - a.y) * (c.x - a.x))
    return MVector(x, y, z).normal()


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
                       final.x, final.y, final.z,  0.,
                       0., 0., 0., 1.])
    return rot_mat


def build_matrix(a, b, c, translation=MVector(0, 0, 0)):
    result = MMatrix([a.x, a.y, a.z, 0.,
                      b.x, b.y, b.z, 0.,
                      c.x, c.y, c.z,  0.,
                      0., 0., 0., 1.])
    set_matrix_translation(result, translation)
    return result
