import maya.mel as mel
import maya.cmds as cmds

character_types = ['Enemies', 'Guardians', 'NPC', 'Player']  # Shared folder names from source and import
character_names = ['Larg', 'Necrus', 'Primordia', 'Vorn']


def select_export_joints():
    cmds.select('*:ExportJoints', replace=True, hi=True)


def get_export_settings(path, file_name):
    mel.eval('FBXExportBakeComplexAnimation -v 1;')
    start = cmds.playbackOptions(q=1, min=1)
    end = cmds.playbackOptions(q=1, max=1)
    mel.eval("FBXExportBakeComplexStart -v " + str(start))
    mel.eval("FBXExportBakeComplexEnd -v " + str(end))
    return 'FBXExport -f "' + path + file_name + '.fbx" -s;'


def build_file_name(split_path):
    file_name_full = split_path[-1].split('_')
    file_name_full[0] = "ANIM"
    file_name = ''
    for e in range(len(file_name_full)):
        file_name += file_name_full[e]
        if e < len(file_name_full) - 1:
            file_name += "_"
    return file_name


def find_keyword(items, keywords):
    for item in items:  # Add key folder
        for key in keywords:
            if item == key:
                return key + '/'
    return ''


def get_file_path():
    split_path = cmds.file(query=True, expandName=True).split('.')[0]  # Get the full path file name
    split_path = split_path.split('/')
    file_name = build_file_name(split_path)  # Replace SK_ with ANIM_
    split_path.pop()  # Remove file name so only path remains
    path = ''
    for item in split_path:  # Set to Export Path
        if item == 'Content':
            path += 'Content/Import/Animations/'
            break
        path += item + "/"
    path += find_keyword(split_path, character_types)
    path += find_keyword(split_path, character_names)
    return path, file_name


def do_it():
    original_selection = cmds.ls(selection=True)
    select_export_joints()
    path, file_name = get_file_path()
    mel.eval(get_export_settings(path, file_name))
    cmds.select(original_selection)


do_it()


