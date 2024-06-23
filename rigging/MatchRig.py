"""
from importlib import reload
import rigging.MatchRig as MatchRig
reload(rigging.MatchRig)
from rigging.MatchRig import *
DoMatch()
"""

import maya.cmds as cmds
import rigging.AutoRigHelpers as arh


def SnapAll(mov, tar):
    pos = (cmds.xform(tar, q=True, ws=True, rp=True))
    cmds.move(pos[0], pos[1], pos[2], mov, ws=True)
    rotX = cmds.getAttr(tar + '.rotateX')
    rotY = cmds.getAttr(tar + '.rotateY')
    rotZ = cmds.getAttr(tar + '.rotateZ')
    cmds.setAttr(mov + '.rotateX', rotX)
    cmds.setAttr(mov + '.rotateY', rotY)
    cmds.setAttr(mov + '.rotateZ', rotZ)
    print("Snapped {} to {}".format(mov, tar))


def SnapPar(movesel, refsel):
    cmds.select(cmds.listRelatives(movesel, children=True))
    for constraint in cmds.ls(selection=True, type="constraint"):
        print("Warning: Constraints found on {} consider using SnapALL".format(movesel))
    pc = cmds.parentConstraint(refsel, movesel, mo=False, w=1.0)
    cmds.delete(pc)
    print("Snapped {} to {}".format(movesel, refsel))


def SnapPos(movesel, refsel):
    cmds.select(refsel, hi=True)
    pc = cmds.pointConstraint(refsel, movesel, mo=False, w=1.0)
    cmds.delete(pc)
    print("Snapped {} to {}".format(movesel, refsel))


def SnapParPair(item, dest, all=False):
    for side in {"_L", "_R"}:
        if all:
            SnapAll(item + side, dest + side)
        else:
            SnapPar(item + side, dest + side)
    print("Snapped {} to {}".format(item, dest))


def SnapPolePair(item):
    for side in {"_L", "_R"}:
        SetPoleVector(item + side)

def ToggleIK(attr):
    for side in {"_L", "_R"}:
        cmds.setAttr("LegikHandle1" + side + ".ikBlend", attr)
        cmds.setAttr("LegikHandle2" + side + ".ikBlend", attr)
        cmds.setAttr("ikHandleArm" + side + ".ikBlend", attr)


def SetPoleVector(pV):
    cmds.makeIdentity(pV, apply=True, t=1)
    cmds.move(-100.0, pV, objectSpace=True, moveZ=True)
    cmds.setAttr(pV + '.rotateX', 0)
    cmds.setAttr(pV + '.rotateY', 0)
    cmds.setAttr(pV + '.rotateZ', 0)
    cmds.makeIdentity(pV, apply=True, t=1)


# Spine and Head
def Center():
    SnapPar('GrpCOGCtrl', 'AR_CoG')
    SnapPar('GrpSpineLowerCtrl', 'AR_Spine_LowerPointer')
    SnapPar('SpineMidHelper', 'AR_Spine_MidPointer')
    SnapPar('ChestHelper', 'AR_Chest')
    SnapPar('GrpNeckCtrl', 'AR_Neck')
    SnapPar('GrpHeadCtrl', 'AR_Head')
    SnapPar('GrpLookAtCtrl', 'AR_Head')
    SnapPos('AimNull', 'AR_Head')
    SnapAll('HeadAimBlendHelper', 'AR_Head')
    SnapPos('grp_BS_EyeBall_L', 'AR_EyeBall_L')
    SnapPos('grp_BS_EyeBall_R', 'AR_EyeBall_R')


def Legs():
    for side in ['L', 'R']:
        SnapAll('HipHelper_' + side, 'AR_LegHelper_' + side)
        SnapPar('AnkleHelper_' + side, 'AR_Foot_' + side)
        SnapPar('GrpFootCtrl_' + side, 'AR_Foot_' + side)
        SnapPar('GrpFootBall_' + side, 'AR_Toe_' + side)
        thigh_length = cmds.getAttr("thigh_length_helper.distance")
        cmds.setAttr('IKLeg1_' + side + '.translateX', thigh_length)
        calf_length = cmds.getAttr("calf_length_helper.distance")
        cmds.setAttr('IKLeg2_' + side + '.translateX', calf_length)
        cmds.parentConstraint('HipsCtrl', 'HipHelper_' + side, mo=True)
        SnapAll('LegikHandle1_' + side, 'AR_Foot_' + side)
        SnapAll('LegikHandle2_' + side, 'AR_Foot_' + side)
        SnapPar('KneeVectorHelper_'+side, 'AR_Shin_'+side)


def Arms():
    for side in ['L', 'R']:
        SnapPar('gClavicleCtrl_' + side, 'AR_Clavicle_' + side)
        SnapPar('ShoulderHelper_' + side, 'AR_UpperArm_' + side)
        SnapAll('IKArm0_' + side, 'AR_UpperArm_' + side)
        SnapPar('UArmFK_' + side, 'AR_UpperArm_' + side)
        SnapAll('BlendArm0_' + side, 'AR_UpperArm_' + side)
        SnapPar('IKArmVector_' + side, 'AR_ForeArm_' + side)
        SetPoleVector('IKArmVector_' + side)
        SnapPar('IKArm1_' + side, 'AR_ForeArm_' + side)
        SnapPar('gFarm_' + side, 'AR_ForeArm_' + side)
        SnapAll('BlendArm1_' + side, 'AR_ForeArm_' + side)
        SnapPar('GrpIKHand_' + side, 'AR_Hand_' + side)
        SnapPar('IKArm2_' + side, 'AR_Hand_' + side)


def Hands():
    for side in ['L', 'R']:
        for digit in range(0, 2):
            SnapPar('GrpThumb' + str(digit) + '_' + side, 'AR_Thumb' + str(digit) + '_' + side)
        for finger in ['A', 'B', 'C', 'D']:
            for digit in range(0, 3):
                SnapPar('GrpFinger' + finger + str(digit) + '_' + side, 'AR_Finger' + finger + str(digit) + '_' + side)


def AfterIK():
    for side in ['L', 'R']:
        SnapPar('KneeVector_SideNull_' + side, 'KneeVector_SideNullHelper_' + side)
        SnapPar('KneeVector_' + side, 'KneeVectorHelper_' + side)
        SnapAll('BlendArm2_' + side, 'ikHandleArm_' + side)
        SnapPar('GrpFKHand_' + side, 'AR_Hand_' + side)
        SnapPos('BlendWrist_' + side, 'AR_Wrist_' + side)


def Face():
    for side in ['L', 'R']:
        for pair in arh.GetFacialSymmetryMap():
            SnapPos(pair[1] + side, pair[0] + side)
    for pair in arh.GetFacialCenterMap():
        SnapPos(pair[1], pair[0])


def DoMatch():
    ToggleIK(0)
    Center()
    Legs()
    Arms()
    ToggleIK(1)
    AfterIK()
    Hands()
    Face()
    cmds.SelectNone()
