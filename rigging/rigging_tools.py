import maya.cmds as cmds


def select_driven(side):
    cmds.select(clear=True)
    for alph in {"A", "B", "C", "D"}:
        for ind in {"0", "1", "2"}:
            cmds.select("GrpFinger" + alph + ind + side, add=True)


def set_key(side):
    for alph in {"A", "B", "C", "D"}:
        for ind in {"1", "2"}:
            cmds.setDrivenKeyframe("GrpFinger" + alph + ind + side + ".rotateZ",
                                   currentDriver="fingerHelperDriver" + alph + side + ".translateX")
        cmds.setDrivenKeyframe("GrpFinger" + alph + "0" + side + ".rotateZ",
                               currentDriver="knuckleHelperDriver" + alph + side + ".translateX")


def bake_selected_curves(step_size=0.1):
    curves = cmds.ls(selection=True)
    for c in curves:
        key_index = (cmds.keyframe(c, indexValue=True, q=True))[-1]
        end = cmds.getAttr(c + ".keyTimeValue[" + str(key_index) + "].keyTime")
        print(cmds.keyframe(c, query=True, timeChange=True))
        caret = cmds.getAttr(c + ".keyTimeValue[0].keyTime")
        while caret < end:
            caret += step_size
            cmds.setKeyframe(c, insert=True, f=caret)
