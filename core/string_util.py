import maya.cmds as cmds

def remove_namespace(string):
    return string.split(':')[-1]
