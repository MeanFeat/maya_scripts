import maya.cmds as cmds
import sys


def GetSide():
    selection = cmds.ls(selection=True)
    if len(selection) > 0:
        if '_L' in selection[0]:
            return "L"
        if '_R' in selection[0]:
            return "R"
    else:
        cmds.warning("Select a component of the arm to match")
        sys.exit()


def MatchFKtoIK():
    side = GetSide()
    froms = "*:IKArm0_" + side, "*:IKArm1_" + side
    tos = "*:UrArm_" + side, "*:FArm_" + side
    attrs = ".rotateX", ".rotateY", ".rotateZ"
    for i in range(0, len(froms)):
        for a in attrs:
            if not (cmds.getAttr(tos[i] + a, lock=True)):
                cmds.setAttr(tos[i] + a, cmds.getAttr(froms[i] + a))
    tempCnst = cmds.orientConstraint("*:IKHand_" + side, "*:FKHand_" + side, mo=False)
    cmds.delete(tempCnst)


def MatchIKtoFK():
    side = GetSide()
    pc = cmds.parentConstraint("*:FKHand_" + side, "*:IKHand_" + side, mo=False)
    cmds.delete(pc)
    pc = cmds.parentConstraint("*:FArm_" + side, "*:IKArmVector_" + side, mo=False)
    cmds.delete(pc)
    cmds.setAttr("*:IKArmVector_" + side + ".rotateX", 0.0)
    cmds.setAttr("*:IKArmVector_" + side + ".rotateY", 0.0)
    cmds.setAttr("*:IKArmVector_" + side + ".rotateZ", 0.0)


MatchFKtoIK()
