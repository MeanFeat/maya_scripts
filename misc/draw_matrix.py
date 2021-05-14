
import maya.api.OpenMaya as OpenMaya
from maya import cmds
from maya.OpenMaya import MVector, MSpace

from core.basis import get_matrix_components
from ui.ui_draw_manager import UIDrawLine, ui_draw_manager_plugin_path

'''
path, name = ui_draw_manager_plugin_path()
if cmds.pluginInfo('ui_draw_manager.py', q=True, loaded=False):
    cmds.loadPlugin('D:/GameDev/maya_scripts/ui/ui_draw_manager.py')
'''


def draw_matrix(matrix, pos, alpha=1.0):
    x_dir, y_dir, z_dir, p = get_matrix_components(matrix)

    x_line = UIDrawLine()
    y_line = UIDrawLine()
    z_line = UIDrawLine()
    x_line.set(pos, pos + x_dir*500, (1., 0., 0., alpha), 2, True)
    y_line.set(pos, pos + y_dir*500, (0., 1., 0., alpha), 2, True)
    z_line.set(pos, pos + z_dir*500, (0., 0., 1., alpha), 2, True)


original_selection = cmds.ls(selection=True)
selection_list = OpenMaya.MGlobal.getActiveSelectionList()
if not selection_list.isEmpty():
    for i in range(0, selection_list.length()):
        dag_path = selection_list.getDagPath(i)
        position = OpenMaya.MFnTransform(dag_path).rotatePivot(MSpace.kWorld)
        draw_matrix(dag_path.inclusiveMatrix(), position)
cmds.select(original_selection)
