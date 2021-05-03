import sys
import maya.api.OpenMaya as OpenMaya
from paint_node import PaintNode


# noinspection PyPep8Naming
def maya_useNewAPI():
    pass


# noinspection PyPep8Naming
def initializePlugin(obj):
    plugin = OpenMaya.MFnPlugin(obj, "Autodesk", "3.0", "Any")
    try:
        plugin.registerNode("paintNode", PaintNode.id, PaintNode.creator, PaintNode.initialize, OpenMaya.MPxNode.kLocatorNode)
    except:
        sys.stderr.write("Failed to register node\n")
        raise


# noinspection PyPep8Naming
def uninitializePlugin(obj):
    plugin = OpenMaya.MFnPlugin(obj)
    try:
        plugin.deregisterNode(PaintNode.id)
    except:
        sys.stderr.write("Failed to deregister node\n")
        raise
