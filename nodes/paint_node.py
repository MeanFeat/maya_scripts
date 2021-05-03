import maya.api.OpenMaya as OpenMaya
import maya.api.OpenMayaUI as OpenMayaUI


class PaintNode(OpenMayaUI.MPxLocatorNode):
    id = OpenMaya.MTypeId(0x0018002A)

    def __init__(self):
        OpenMayaUI.MPxLocatorNode.__init__(self)

    @staticmethod
    def creator():
        return PaintNode()

    @staticmethod
    def initialize():
        pass
