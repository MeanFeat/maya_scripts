"""
import rigging.SnapJoints
from imp import reload
reload(rigging.SnapJoints)
from rigging.SnapJoints import *
snap_joints()

"""

import maya.cmds as cmds
import rigging.SnapJointsMap as snap_map


def snap_joints():
    for pair in snap_map.get_map():
        joint = pair[0]
        snap = pair[1]
        if len(cmds.ls(joint)) > 0 and len(cmds.ls(snap)) > 0:
            cmds.parentConstraint(snap, joint)


def clear_constraints():
    cmds.select('root', hi=True)
    constraints = cmds.ls(selection=True, type="constraint")
    cmds.delete(constraints)
