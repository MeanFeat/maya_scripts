import maya.cmds as cmds
from maya.api.OpenMaya import MVector

from core.basis import build_plane_normal, build_rotation_matrix, build_matrix
from core.scene_util import get_world_up

scene_triangulation = ['loc1', 'loc2', 'loc3']
vectors = []


def create_loc_at(vec):
    locator = cmds.spaceLocator()
    cmds.move(vec[0], vec[1], vec[2], locator)
    return locator


def get_vector(scene_object):
    p = cmds.xform(scene_object, query=True, translation=True)
    return MVector(p[0], p[1], p[2])


for item in scene_triangulation:
    loc = cmds.ls(item)
    vectors.append(get_vector(item))

plane_normal = build_plane_normal(vectors[0], vectors[1], vectors[2])
rotation_matrix = build_matrix((plane_normal ^ vectors[-1]).normal(), plane_normal, vectors[-1].normal())
'''
create_loc_at(vectors[-1].normal())
create_loc_at(plane_normal)
create_loc_at((plane_normal^vectors[-1]).normal())
'''
for i, item in enumerate(cmds.ls(selection=True)):
    v = rotation_matrix * get_vector(item)
    cmds.move(v[0], v[1], v[2], item)

