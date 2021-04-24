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


def maya_useNewAPI():  # required for MObject
    pass


class UIDraw(OpenMayaUI.MPxLocatorNode):
    id = OpenMaya.MTypeId(0x0008002A)
    drawDbClassification = "drawdb/geometry/uiDrawManager"
    drawRegistrantId = "uiDrawManagerPlugin"

    shape = -1
    view_position = MPoint(0, 0, 0)
    size = 1
    world_position = MPoint(0, 0, 0)
    line_end = MPoint(0, 0, 0)
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

        # TODO Look into MFnPointArrayData

        numeric_attribute = OpenMaya.MFnNumericAttribute()

        UIDraw.shape = numeric_attribute.create("shape", "shp", OpenMaya.MFnNumericData.kInt)
        OpenMaya.MPxNode.addAttribute(UIDraw.shape)

        UIDraw.view_position = numeric_attribute.create("view_position", "vp", OpenMaya.MFnNumericData.k3Double)
        OpenMaya.MPxNode.addAttribute(UIDraw.view_position)

        UIDraw.size = numeric_attribute.create("size", "r", OpenMaya.MFnNumericData.kInt)
        OpenMaya.MPxNode.addAttribute(UIDraw.size)

        UIDraw.world_position = numeric_attribute.create("world_position", "ls0", OpenMaya.MFnNumericData.k3Double)
        OpenMaya.MPxNode.addAttribute(UIDraw.world_position)
        UIDraw.line_end = numeric_attribute.create("line_end", "le1", OpenMaya.MFnNumericData.k3Double)
        OpenMaya.MPxNode.addAttribute(UIDraw.line_end)

        UIDraw.color = numeric_attribute.create("color", "clr", OpenMaya.MFnNumericData.k4Double)
        OpenMaya.MPxNode.addAttribute(UIDraw.color)
        UIDraw.line_width = numeric_attribute.create("line_width", "lw", OpenMaya.MFnNumericData.kInt)
        OpenMaya.MPxNode.addAttribute(UIDraw.line_width)


def get_ui_draw_group():
    group_name = 'ui_draw_group'
    existing = cmds.ls(group_name)
    if not existing:
        return cmds.group(em=True, name=group_name)
    else:
        return existing


class UIDrawShape(object):
    kInvalid = -1
    kCircle = 0
    kLine = 1
    kPoint = 2
    shape = kInvalid
    color = (1, 1, 1, 1)
    width = 1

    def __init__(self):
        self.node = cmds.createNode('uiDrawManager')
        draw_group = get_ui_draw_group()
        original_parent = cmds.listRelatives(self.node, parent=True)[0]
        cmds.parent(self.node, draw_group, shape=True)
        self.parent = cmds.listRelatives(self.node, parent=True)[0]
        cmds.delete(original_parent)

    def set_color(self, color):
        self.color = color
        for i in range(4):
            cmds.setAttr(self.node + '.color.color' + str(i), self.color[i])

    def set_line_width(self, width):
        self.width = width
        cmds.setAttr(self.node + '.line_width', self.width)

    def set_visible(self, is_visible):
        cmds.setAttr(self.parent + '.visibility', int(is_visible))


class UIDrawLine(UIDrawShape):

    def __init__(self):
        super(UIDrawLine, self).__init__()
        self.shape = UIDrawShape.kLine

    def set(self, start, end, color=None, width=None, visible=True):
        cmds.setAttr(self.node + '.shape', self.shape)
        cmds.setAttr(self.node + '.world_position.world_position0', start.x)
        cmds.setAttr(self.node + '.world_position.world_position1', start.y)
        cmds.setAttr(self.node + '.world_position.world_position2', start.z)
        cmds.setAttr(self.node + '.line_end.line_end0', end.x)
        cmds.setAttr(self.node + '.line_end.line_end1', end.y)
        cmds.setAttr(self.node + '.line_end.line_end2', end.z)
        self.set_visible(visible)
        if color is not None:
            self.set_color(color)
        if width is not None:
            self.set_line_width(width)


class UIDrawCircle(UIDrawShape):
    position = MPoint()
    size = 1

    def __init__(self):
        super(UIDrawCircle, self).__init__()
        self.shape = UIDrawShape.kCircle

    def set(self, position, size, color=None, width=None, visible=True):
        cmds.setAttr(self.node + '.shape', self.shape)
        cmds.setAttr(self.node + '.view_position.view_position0', position.x)
        cmds.setAttr(self.node + '.view_position.view_position1', position.y)
        cmds.setAttr(self.node + '.view_position.view_position2', position.z)
        cmds.setAttr(self.node + '.size', size)
        self.set_visible(visible)
        if color is not None:
            self.set_color(color)
        if width is not None:
            self.set_line_width(width)


class UIDrawPoint(UIDrawShape):
    position = MPoint()
    size = 1

    def __init__(self):
        super(UIDrawPoint, self).__init__()
        self.shape = UIDrawShape.kPoint

    def set(self, start, size, color=None, visible=True):
        cmds.setAttr(self.node + '.shape', self.shape)
        cmds.setAttr(self.node + '.world_position.world_position0', start.x)
        cmds.setAttr(self.node + '.world_position.world_position1', start.y)
        cmds.setAttr(self.node + '.world_position.world_position2', start.z)
        cmds.setAttr(self.node + '.size', size)
        self.set_visible(visible)
        if color is not None:
            self.set_color(color)


class UIDrawData(OpenMaya.MUserData):
    shape = UIDrawShape.kInvalid
    view_position = MPoint(0, 0, 0)
    size = 1
    world_position = MPoint()
    line_end = MPoint()
    color = MColor((1, 1, 1, 1))
    line_width = 1

    def __init__(self):
        OpenMaya.MUserData.__init__(self, False)


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

        plug = OpenMaya.MPlug(ui_draw_manager_node, UIDraw.shape)
        data.shape = plug.asInt()

        plug = OpenMaya.MPlug(ui_draw_manager_node, UIDraw.color)
        o = plug.asMObject()
        numeric_data = OpenMaya.MFnNumericData(o)
        data.color = OpenMaya.MColor(numeric_data.getData())

        plug = OpenMaya.MPlug(ui_draw_manager_node, UIDraw.line_width)
        data.line_width = plug.asInt()

        # circle
        plug = OpenMaya.MPlug(ui_draw_manager_node, UIDraw.view_position)
        o = plug.asMObject()
        numeric_data = OpenMaya.MFnNumericData(o)
        data.view_position = OpenMaya.MPoint(numeric_data.getData())

        plug = OpenMaya.MPlug(ui_draw_manager_node, UIDraw.size)
        data.size = plug.asInt()

        # line
        plug = OpenMaya.MPlug(ui_draw_manager_node, UIDraw.world_position)
        o = plug.asMObject()
        numeric_data = OpenMaya.MFnNumericData(o)
        data.world_position = OpenMaya.MPoint(numeric_data.getData())

        plug = OpenMaya.MPlug(ui_draw_manager_node, UIDraw.line_end)
        o = plug.asMObject()
        numeric_data = OpenMaya.MFnNumericData(o)
        data.line_end = OpenMaya.MPoint(numeric_data.getData())

        return data

    def hasUIDrawables(self, **kwargs):
        return True

    def addUIDrawables(self, object_path, draw_manager, frame_context, data):
        draw_manager.setColor(data.color)
        draw_manager.setLineWidth(data.line_width)
        if data.shape == UIDrawShape.kLine:
            draw_manager.line2d(world_to_view(data.world_position), world_to_view(data.line_end))
        elif data.shape == UIDrawShape.kCircle:
            draw_manager.circle2d(data.view_position, data.size)
        elif data.shape == UIDrawShape.kPoint:
            draw_manager.circle2d(world_to_view(data.world_position), data.size, True)

        draw_manager.endDrawable()


# noinspection PyPep8Naming
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


# noinspection PyPep8Naming
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
