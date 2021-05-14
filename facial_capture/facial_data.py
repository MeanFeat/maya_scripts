import maya.cmds as cmds
from maya.api.OpenMaya import MVector

from core.basis import build_plane_normal, build_rotation_matrix, set_matrix_translation
from core.scene_util import get_world_up

scene_items = ['loc1', 'loc2', 'loc3']
vectors = []


def create_loc_at(vec):
    locator = cmds.spaceLocator()
    cmds.move(vec[0], vec[1], vec[2], locator)
    return locator


def get_vector(scene_object):
    p = cmds.xform(scene_object, query=True, translation=True)
    return MVector(p[0], p[1], p[2])


for item in scene_items:
    loc = cmds.ls(item)
    vectors.append(get_vector(item))

plane_normal = build_plane_normal(vectors[0], vectors[1], vectors[2])

rotation_matrix = build_rotation_matrix(vectors[-1], plane_normal)


for i, item in enumerate(scene_items):
    v = rotation_matrix * vectors[i]
    cmds.move(v[0], v[1], v[2], item)
