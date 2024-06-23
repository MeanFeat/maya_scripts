import maya.mel as mel
import maya.cmds as cmds
import core.file_util as file_util


def select_export_joints():
    cmds.select('root', replace=True, hi=True)


def get_export_settings(path, file_name, suffix):
    return 'FBXExport -f "' + path + file_name + suffix + '.fbx" -s;'


def get_import_file_path():
    split_path = cmds.file(query=True, expandName=True).split('.')[0]  # Get the full path file name
    split_path = split_path.split('/')
    file_name = split_path[-1].replace('SK_', 'SK_NPC_')
    folder_name = split_path[-1].replace('SK_', '')
    split_path.pop()  # Remove file name so only path remains
    path = ''
    for item in split_path:
        if item == 'Source':
            path += 'Import/Character/' + folder_name + '/'
            break
        path += item + "/"
    return path, file_name


def Export_Head():
    path, file_name = get_import_file_path()
    file_util.verify_directory(path)
    head_mesh = []
    for mesh in cmds.ls(type="mesh"):
        if "Head" in mesh:
            if "shape" not in mesh:
                head_mesh = cmds.listRelatives(mesh, parent=True, type='transform')[0]

    done = False
    head_group = head_mesh
    while not done:
        p = cmds.listRelatives(head_group, parent=True)
        if p is None:
            done = True
        else:
            head_group = p[0]

    select_export_joints()
    cmds.select(head_group, add=True, hi=True)
    mel.eval(get_export_settings(path, file_name, '_Head'))


def Export_Hair():
    path, file_name = get_import_file_path()
    file_name = file_name.replace('SK_', 'SM_')
    file_util.verify_directory(path)
    hair_mesh = []
    for mesh in cmds.ls(type="mesh"):
        if "Hair" in mesh or "Hat" in mesh:
            if "shape" not in mesh:
                hair_mesh = cmds.listRelatives(mesh, parent=True, type='transform')[0]
            hair_export_name = '_Hair'
            if "Hat" in mesh:
                hair_export_name = "_Hat"
    temp_hair = cmds.duplicate(hair_mesh)[0]
    cmds.select(temp_hair)
    axis = ['x', 'y', 'z']
    for ax in axis:
        cmds.setAttr(temp_hair + '.' + 't' + ax, lock=False)
    x, y, z = cmds.xform(temp_hair, rotatePivot=True, absolute=True, q=True)
    cmds.xform(temp_hair, t=[-x, -y, -z])
    cmds.makeIdentity(temp_hair, apply=True, t=True)
    mel.eval(get_export_settings(path, file_name, hair_export_name))
    cmds.delete(temp_hair)


def Export_Body():
    path, file_name = get_import_file_path()
    file_util.verify_directory(path)
    body_mesh = []
    for mesh in cmds.ls(type="mesh"):
        if "Outfit" in mesh or "Body" in mesh:
            if "shape" not in mesh:
                body_mesh = cmds.listRelatives(mesh, parent=True, type='transform')[0]
    select_export_joints()
    cmds.select(body_mesh, add=True)
    mel.eval(get_export_settings(path, file_name, '_Body'))


def Export_Chosen_Parts(head, hair, body):
    original_selection = cmds.ls(selection=True)
    if head:
        Export_Head()
    if hair:
        Export_Hair()
    if body:
        Export_Body()
    cmds.select(original_selection, replace=True)


def Export_Menu():
    menu_win = cmds.window("RadiantCharacterExport", title="RadiantCharacterExport", iconName='RadiantCharacterExport',
                           resizeToFitChildren=True, te=100, le=800)
    cmds.columnLayout(adjustableColumn=True)
    cmds.checkBox("Head_CheckBox", label='Head', v=True)
    cmds.checkBox("Hair_CheckBox", label='Hair', v=True)
    cmds.checkBox("Body_CheckBox", label='Body', v=True)
    cmds.button(label="Export", command=lambda x: Export_Chosen_Parts(cmds.checkBox("Head_CheckBox", v=True, q=True), cmds.checkBox("Hair_CheckBox", v=True, q=True), cmds.checkBox("Body_CheckBox", v=True, q=True)))
    cmds.setParent('..')
    cmds.showWindow(menu_win)


