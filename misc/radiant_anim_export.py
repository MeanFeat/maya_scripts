import os

import maya.mel as mel
import maya.cmds as cmds



def get_export_settings(path, file_name):
    mel.eval('FBXExportBakeComplexAnimation -v 1;')
    start = cmds.playbackOptions(q=1, min=1)
    end = cmds.playbackOptions(q=1, max=1)
    mel.eval("FBXExportBakeComplexStart -v " + str(start))
    mel.eval("FBXExportBakeComplexEnd -v " + str(end))
    return 'FBXExport -f "' + path + file_name + '.fbx" -s;'


def get_file_path():
    split_path = cmds.file(query=True, expandName=True).split('.')[0]  # Get the full path file name
    split_path = split_path.split('/')
    file_name = split_path[-1]
    split_path.pop()  # Remove file name so only path remains
    path = ''
    for item in split_path:  # Set to Export Path
        if item == 'Source':
            path += 'Import/'
            continue
        path += item + "/"
    return path, file_name


def do_it():
    original_selection = cmds.ls(selection=True)
    cmds.select('*:root', replace=True, hi=True)
    cmds.select("*:*Vex_Head_*", add=True)
    path, file_name = get_file_path()
    mel.eval(get_export_settings(path, file_name))
    cmds.select(original_selection)


for folder in ['Facial', 'HeadGestures', 'Visemes']:
    for root, dirs, files in os.walk('D:/Gamedev/Archiact/RadiantArt/Source/Animation/ProceduralAnimation/' + folder + '/'):
        for f in files:
            if f.endswith(".ma"):
                file_path = root + '/' + f
                cmds.file(file_path, o=True, f=True)
                do_it()
