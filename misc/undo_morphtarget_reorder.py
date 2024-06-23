"""
from misc.undo_morphtarget_reorder import *
fix_blendshape_animcurves()
"""

import maya.cmds as cmds
from core.string_util import remove_namespace

def fix_blendshape_animcurves():
    blendshape_nodes = cmds.ls(type='blendShape')
    if not blendshape_nodes:
        print("No blendShape nodes selected or found.")
        return

    animcurves = cmds.ls(type='animCurve')

    # disconnect all animCurves from blendShape nodes
    for blendshape_node in blendshape_nodes:
        weights = cmds.listAttr(blendshape_node + '.weight', multi=True)
        for target_index, target_name in enumerate(weights):
            target_attr = "{}.weight[{}]".format(blendshape_node, target_index)
            connections = cmds.listConnections(target_attr, s=True, d=False, plugs=True) or []

            for conn in connections:
                if remove_namespace(blendshape_node) not in conn:
                    #print("Skipping connection: {}".format(conn))
                    continue

                conn_name = remove_namespace(conn.split('.')[0])
                # Check if this connection is from an animCurve and disconnect it
                if conn_name in animcurves:
                    print("Disconnecting {} from {}".format(conn, target_attr))
                    cmds.disconnectAttr(conn, target_attr)
                    cmds.setAttr(target_attr, 0)

        for curve in animcurves:
            if remove_namespace(blendshape_node) in curve:
                for target_index, target_name in enumerate(weights):
                    target_attr = "{}.weight[{}]".format(blendshape_node, target_index)
                    if target_name in curve:
                        print("Reconnecting {} to {}".format(curve, target_attr))
                        cmds.connectAttr(curve + '.output', target_attr, force=True)
                        break


