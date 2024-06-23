import maya.cmds as cmds
import maya.mel as mel

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


def remap_morph_targets():
    sel = cmds.ls(selection=True)
    desired_shape = sel[-1]
    original_shape = sel[-2]

    for morph in sel:
        if morph != desired_shape and morph != original_shape:
            new = cmds.duplicate(original_shape)
            bs = cmds.blendShape(morph, desired_shape, new)
            cmds.blendShape(bs, edit=True, w=[(0, 1.0), (1, 1.0)])
            cmds.delete(new, constructionHistory=True)
            old = cmds.rename(morph, morph + '_old')
            cmds.rename(new, morph)
            cmds.delete(old)


def remove_morph_target_prefix(prefix = 'HR_'):
    history = cmds.listHistory( cmds.ls(selection=True) )
    blendshapes = cmds.ls( history, type = "blendShape")

    for blendshapenode in blendshapes:
        for i in range(len(cmds.getAttr(blendshapenode + ".w")[0])):
            shapename = cmds.attributeName(blendshapenode + ".w[{}]".format(i))
            
            if prefix in shapename:
                shapename = shapename.replace(prefix, '')
                mel.eval("blendShapeRenameTargetAlias {} {} {}".format(blendshapenode, i, shapename))


def remove_morph_target_suffix(suffix='Shape'):
    history = cmds.listHistory(cmds.ls(selection=True))
    blendshapes = cmds.ls(history, type="blendShape")

    for blendshapenode in blendshapes:
        for i in range(len(cmds.getAttr(blendshapenode + ".w")[0])):
            shapename = cmds.attributeName(blendshapenode + ".w[{}]".format(i))

            if suffix in shapename:
                shapename = shapename.replace(suffix, '')
                mel.eval("blendShapeRenameTargetAlias {} {} {}".format(blendshapenode, i, shapename))


def copy_vertex_colors():
    selection = cmds.ls(selection=True)
    source = selection[0]
    destination = selection[1]

    num_vertices = cmds.polyEvaluate(source, vertex=True)

    for i in range(num_vertices):
        color_data = cmds.polyColorPerVertex("{}.vtx[{}]".format(source, i), query=True, rgb=True)
        cmds.polyColorPerVertex("{}.vtx[{}]".format(destination, i), rgb=color_data)


def update_bind_pose_recursive(node):
    children = cmds.listRelatives(node, children=True, fullPath=True) or []

    for child in children:
        if cmds.nodeType(child) == "joint":
            bind_pose = cmds.dagPose(child, query=True, bindPose=True)

            if bind_pose:
                cmds.dagPose(bind_pose[0], restore=True)
                cmds.dagPose(bind_pose[0], save=True)

        # recursively call this function on the child
        update_bind_pose_recursive(child)


def clean_skeleton(root):
    children = cmds.listRelatives(root, children=True, fullPath=True) or []

    # delete all skin clusters and bind poses
    for child in children:
        if cmds.nodeType(child) == "joint":
            bind_pose = cmds.dagPose(child, query=True, bindPose=True)

            if bind_pose:
                for pose in bind_pose:
                    cmds.delete(pose)

            skin_cluster = cmds.listConnections(child, type="skinCluster")

            if skin_cluster:
                for skin in skin_cluster:
                    if cmds.objExists(skin):
                        cmds.delete(skin)

