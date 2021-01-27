from maya import cmds, mel
from maya.api import OpenMayaUI, OpenMaya


def get_playback_slider():
    return mel.eval('$tmpVar=$gPlayBackSlider')


def get_timeline_selection():
    return cmds.timeControl(get_playback_slider(), query=True, rangeArray=True)


# TODO set up with actual transforms
def create_null_on_object(item, suffix):
    temp_null = cmds.group(empty=True, name=item + suffix)
    temp_parent_constraint = cmds.parentConstraint(item, temp_null, mo=False)
    cmds.delete(temp_parent_constraint)
    cmds.makeIdentity(temp_null, apply=True, t=1, r=0, s=0)
    return temp_null


def get_camera_position():  # TODO move to utility file
    view = OpenMayaUI.M3dView.active3dView()
    camera = OpenMayaUI.M3dView.getCamera(view)
    cam_matrix = camera.exclusiveMatrix()
    return OpenMaya.MVector(cam_matrix.getElement(3, 0), cam_matrix.getElement(3, 1), cam_matrix.getElement(3, 2))
