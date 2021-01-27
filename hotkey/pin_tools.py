from maya import cmds


# TODO re-write to use actual translations and matrices
def pin_translate(sel):
    for s in sel:
        pin_name = s + "_TranslatePin"
        if cmds.ls(pin_name):
            cmds.delete(pin_name)
        else:
            temp_null = cmds.spaceLocator(name=pin_name)
            cmds.delete(cmds.pointConstraint(s, temp_null, mo=False))
            cmds.pointConstraint(temp_null, s, mo=True)
            cmds.select(sel)


def pin_rotate(sel):
    for s in sel:
        pin_name = s + "_RotatePin"
        if cmds.ls(pin_name):
            cmds.delete(pin_name)
        else:
            temp_null = cmds.spaceLocator(name=pin_name)
            cmds.delete(cmds.parentConstraint(s, temp_null, mo=False))
            cmds.orientConstraint(temp_null, s, mo=True)
            cmds.select(sel)
