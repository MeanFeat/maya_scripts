import maya.cmds as cmds


def ConnectMorphTargets():
    sel = cmds.ls(selection=True)
    for attr in cmds.listAttr(sel[0], multi=True, keyable=True):
        cmds.connectAttr("AutoRig_Morpher.{}".format(attr), "{}.{}".format(sel[0], attr))


def ConnectLimits():
    sel = cmds.ls(selection=True)
    for attr in ["minTransLimit", "maxTransLimit", "minTransLimitEnable", "maxTransLimitEnable"]:
        cmds.connectAttr("{}.{}".format(sel[0], attr), "{}.{}".format(sel[1], attr))


def GetFacialSymmetryMap():
    return ["AR_OuterBrow_", "grp_outer_brow_"], \
           ["AR_InnerBrow_", "grp_inner_brow_"], \
           ["AR_UpperEye_", "grp_eye_upper_lid_"], \
           ["AR_EyeCorner_", "grp_eye_corner_"], \
           ["AR_LowerEye_", "grp_eye_lower_lid_"], \
           ["AR_EyeBall_", "eye_rotation_helper_"], \
           ["AR_Cheek_", "grp_upper_cheek_"], \
           ["AR_NoseFlank_", "grp_nose_flank_"], \
           ["AR_MouthSnarlUpper_", "grp_upper_snarl_"], \
           ["AR_MouthSnarlLower_", "grp_lower_snarl_"], \
           ["AR_MouthCorner_", "grp_corner_mouth_"]


def GetFacialCenterMap():
    return ["AR_NoseBridge", "grp_nose_bridge"], \
           ["AR_MouthShrug_Upper", "grp_mouth_shrug_upper"], \
           ["AR_MouthPosition", "grp_mouth_pos"], \
           ["AR_MouthShrug_Lower", "grp_mouth_shrug_lower"], \
           ["AR_Jaw", "grp_jaw"], \
           ["AR_Tongue01", "grp_tongue_01"], \
           ["AR_Tongue02", "grp_tongue_02"]
