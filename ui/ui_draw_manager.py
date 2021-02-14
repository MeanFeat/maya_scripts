import os, sys
from maya import cmds
import maya.api.OpenMaya as OpenMaya
import maya.api.OpenMayaUI as OpenMayaUI
import maya.api.OpenMayaRender as OpenMayaRender
from maya.api.OpenMaya import MPoint, MColor

from core.scene_util import world_to_view


def ui_draw_manager_plugin_path():
    path = os.path.abspath(__file__).rstrip('cd').replace('\\', '/')
    name = path.split('/')[-1]
    return path, name


def maya_useNewAPI():
    pass


class UIDraw(OpenMayaUI.MPxLocatorNode):
    id = OpenMaya.MTypeId(0x0008002A)
    drawDbClassification = "drawdb/geometry/uiDrawManager"
    drawRegistrantId = "uiDrawManagerPlugin"

    start = MPoint(0, 0, 0)
    end = MPoint(0, 0, 0)
    color = (1., 1., 1., 1.)
    line_width = 1

    def __init__(self):
        OpenMayaUI.MPxLocatorNode.__init__(self)
        self.data = []

    @staticmethod
    def creator():
        return UIDraw()

    @staticmethod
    def initialize():
        """
        OpenMaya api 2.0 doesn't allow array attributes yet, so we will
        need a new node for each shape we draw.
        """
        numeric_attribute = OpenMaya.MFnNumericAttribute()
        UIDraw.start = numeric_attribute.create("world_start", "s0", OpenMaya.MFnNumericData.k3Double)
        OpenMaya.MPxNode.addAttribute(UIDraw.start)
        UIDraw.end = numeric_attribute.create("world_end", "s1", OpenMaya.MFnNumericData.k3Double)
        OpenMaya.MPxNode.addAttribute(UIDraw.end)
        UIDraw.color = numeric_attribute.create("color", "clr", OpenMaya.MFnNumericData.k4Double)
        OpenMaya.MPxNode.addAttribute(UIDraw.color)
        UIDraw.line_width = numeric_attribute.create("line_width", "lw", OpenMaya.MFnNumericData.kInt)
        OpenMaya.MPxNode.addAttribute(UIDraw.line_width)


class UIDrawShape(object):
    kLine = 0
    kCircle = 1
    type = None
    color = (1, 1, 1, 1)
    width = 1

    def __init__(self):
        self.node = cmds.createNode('uiDrawManager')
        self.parent = cmds.listRelatives(self.node, parent=True)[0]

    def set_color(self, color):
        self.color = color
        for i in range(4):
            cmds.setAttr(self.node + '.color.color'+str(i), self.color[i])

    def set_line_width(self, width):
        self.width = width
        cmds.setAttr(self.node + '.line_width', self.width)


class UIDrawData(OpenMaya.MUserData):
    start = MPoint()
    end = MPoint()
    color = MColor((1, 1, 1, 1))
    line_width = 1

    def __init__(self):
        OpenMaya.MUserData.__init__(self, False)


class UIDrawLine2D(UIDrawShape):
    type = UIDrawShape.kLine

    def __init__(self):
        super(UIDrawLine2D, self).__init__()

    def set(self, start, end, color=None, width=None, visible=True):
        cmds.setAttr(self.node + '.world_start.world_start0', start.x)
        cmds.setAttr(self.node + '.world_start.world_start1', start.y)
        cmds.setAttr(self.node + '.world_start.world_start2', start.z)
        cmds.setAttr(self.node + '.world_end.world_end0', end.x)
        cmds.setAttr(self.node + '.world_end.world_end1', end.y)
        cmds.setAttr(self.node + '.world_end.world_end2', end.z)
        self.set_visible(visible)
        if color is not None:
            self.set_color(color)
        if width is not None:
            self.set_line_width(width)

    def set_visible(self, is_visible):
        cmds.setAttr(self.parent + '.visibility', int(is_visible))


class UIDrawCircle(UIDrawShape):
    type = UIDrawShape.kCircle

    def __init__(self, position, radius):
        super(UIDrawCircle, self).__init__()
        self.position = position
        self.radius = radius


# noinspection PyMethodOverriding
class UIDrawOverride(OpenMayaRender.MPxDrawOverride):
    def __init__(self, obj):
        OpenMayaRender.MPxDrawOverride.__init__(self, obj, None)

    @staticmethod
    def creator(obj):
        return UIDrawOverride(obj)

    def supportedDrawAPIs(*args, **kwargs):
        return OpenMayaRender.MRenderer.kOpenGL | OpenMayaRender.MRenderer.kDirectX11 | OpenMayaRender.MRenderer.kOpenGLCoreProfile

    def isBounded(*args, **kwargs):
        return False

    def boundingBox(*args, **kwargs):
        return OpenMaya.MBoundingBox()

    def prepareForDraw(self, object_path, camera_path, frame_context, old_data):
        data = old_data
        if not isinstance(data, UIDrawData):
            data = UIDrawData()

        ui_draw_manager_node = object_path.node()
        if ui_draw_manager_node.isNull():
            return

        plug = OpenMaya.MPlug(ui_draw_manager_node, UIDraw.start)
        o = plug.asMObject()
        numeric_data = OpenMaya.MFnNumericData(o)
        data.start = OpenMaya.MPoint(numeric_data.getData())

        plug = OpenMaya.MPlug(ui_draw_manager_node, UIDraw.end)
        o = plug.asMObject()
        numeric_data = OpenMaya.MFnNumericData(o)
        data.end = OpenMaya.MPoint(numeric_data.getData())

        plug = OpenMaya.MPlug(ui_draw_manager_node, UIDraw.color)
        o = plug.asMObject()
        numeric_data = OpenMaya.MFnNumericData(o)
        data.color = OpenMaya.MColor(numeric_data.getData())

        plug = OpenMaya.MPlug(ui_draw_manager_node, UIDraw.line_width)
        data.line_width = plug.asInt()

        return data

    def hasUIDrawables(self, **kwargs):
        return True

    def addUIDrawables(self, object_path, draw_manager, frame_context, data):
        draw_manager.setColor(data.color)
        draw_manager.setLineWidth(data.line_width)
        draw_manager.line2d(world_to_view(data.start), world_to_view(data.end))

        draw_manager.endDrawable()


def initializePlugin(obj):
    plugin = OpenMaya.MFnPlugin(obj, "Autodesk", "3.0", "Any")
    try:
        plugin.registerNode("uiDrawManager", UIDraw.id, UIDraw.creator, UIDraw.initialize, OpenMaya.MPxNode.kLocatorNode, UIDraw.drawDbClassification)
    except:
        sys.stderr.write("Failed to register node\n")
        raise

    try:
        OpenMayaRender.MDrawRegistry.registerDrawOverrideCreator(UIDraw.drawDbClassification, UIDraw.drawRegistrantId, UIDrawOverride.creator)
    except:
        sys.stderr.write("Failed to register override\n")
        raise


def uninitializePlugin(obj):
    plugin = OpenMaya.MFnPlugin(obj)
    try:
        plugin.deregisterNode(UIDraw.id)
    except:
        sys.stderr.write("Failed to deregister node\n")
        raise

    try:
        OpenMayaRender.MDrawRegistry.deregisterGeometryOverrideCreator(UIDraw.drawDbClassification, UIDraw.drawRegistrantId)
    except:
        sys.stderr.write("Failed to deregister override\n")
        raise
