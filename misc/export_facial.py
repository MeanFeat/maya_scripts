import os

import maya.mel as mel
import maya.cmds as cmds
import core.file_util as file_util

"""
import misc.export_facial as export_facial
from lib import reload
reload(export_facial)
export_facial.BatchExport()
"""

def get_export_settings(path, file_name):
    mel.eval('FBXExportBakeComplexAnimation -v 1;')
    start = cmds.playbackOptions(q=1, min=1)
    end = cmds.playbackOptions(q=1, max=1)
    mel.eval("FBXExportBakeComplexStart -v " + str(start))
    mel.eval("FBXExportBakeComplexEnd -v " + str(end))
    return 'file -force -options "v=0;" -typ "FBX export" -pr -es "' + path + file_name + '.fbx";'

def do_it():
    original_selection = cmds.ls(selection=True)
    cmds.select('*:root', replace=True, hi=True)
    cmds.select("*:*Erinye_Head_LOD0*", add=True)
    mel.eval(get_export_settings("D:/Temp/SAGA_TEMP/Facial_Angry/", file_util.get_file_name() ))
    cmds.select(original_selection)


def BatchExport():
    #for folder in ['Facial', 'HeadGestures', 'Visemes']:
    for folder in ['Visemes']:
        for root, dirs, files in os.walk('D:/Gamedev/Archiact/RadiantArt/Source/Animation/ProceduralAnimation/' + folder + '/'):
            for f in files:
                if f.endswith(".ma") and "Angry" in f:
                    file_path = root + '/' + f
                    cmds.file(file_path, o=True, f=True)
                    do_it()

