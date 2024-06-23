from maya import cmds, mel
from maya.api import OpenMaya, OpenMayaUI
from maya.api.OpenMaya import MVector, MPoint
from maya.api.OpenMayaUI import M3dView


def get_timeline_range():
    return cmds.playbackOptions(q=True, min=True), cmds.playbackOptions(q=True, max=True)


def get_playback_slider():
    return mel.eval('$tmpVar=$gPlayBackSlider')


def get_timeline_selection():
    return cmds.timeControl(get_playback_slider(), query=True, rangeArray=True)


def create_null_on_object(item, suffix):  # TODO set up with actual transforms
    temp_null = cmds.group(empty=True, name=item + suffix)
    temp_parent_constraint = cmds.parentConstraint(item, temp_null, mo=False)
    cmds.delete(temp_parent_constraint)
    cmds.makeIdentity(temp_null, apply=True, t=1, r=0, s=0)
    return temp_null


def get_camera_position():
    view = OpenMayaUI.M3dView.active3dView()
    camera = OpenMayaUI.M3dView.getCamera(view)
    cam_matrix = camera.exclusiveMatrix()
    return MVector(cam_matrix.getElement(3, 0), cam_matrix.getElement(3, 1), cam_matrix.getElement(3, 2))


def get_world_right():
    return OpenMaya.MVector(1, 0, 0)


def get_world_up():
    if cmds.upAxis(query=True, axis=True) == 'z':
        return OpenMaya.MVector(0, 0, 1)
    else:
        return OpenMaya.MVector(0, 1, 0)


def get_world_forward():
    if cmds.upAxis(query=True, axis=True) == 'z':  # not going to work when mirroring along the Y axis
        return OpenMaya.MVector(0, 1, 0)
    else:
        return OpenMaya.MVector(0, 0, 1)


def world_to_view(p):  # type (MPoint) -> MPoint
    x, y, b = M3dView.active3dView().worldToView(p)
    return MPoint(x, y)


def view_to_world(p):  # type (MPoint) -> MPoint
    wp = MPoint()
    wv = MVector()
    M3dView.active3dView().viewToWorld(int(p.x), int(p.y), wp, wv)
    return wp


def select_layer_objects(layer_name):
    cmds.select(cmds.editDisplayLayerMembers(layer_name, query=True))