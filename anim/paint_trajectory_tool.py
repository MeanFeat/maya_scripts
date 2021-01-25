import math
import sys

import maya.cmds as cmds
import maya.mel as mel
from maya.api import OpenMaya
from maya.api import OpenMayaUI
from maya.api import OpenMayaAnim
from anim.anim_layer import anim_layer

params = None
maya_useNewAPI = True


class PaintTrajectoryParams:
    motion_trail_points = None

    normalize_to_origin = True
    normalization_dist = 12

    loop_animation = False

    anim_layer = anim_layer('paint_trajectory_layer')

    def __init__(self, selection_list, context='paint_trajectory_ctx'):
        self.context = context
        self.brush = PaintParams()
        animated_dag_path, animated_object = selection_list.getComponent(0)

        if not OpenMayaAnim.MAnimUtil.isAnimated(animated_dag_path):
            cancel_tool("please select an animated object")

        start_frame = int(OpenMayaAnim.MAnimControl.minTime().asUnits(OpenMaya.MTime.uiUnit()))
        end_frame = int(OpenMayaAnim.MAnimControl.maxTime().asUnits(OpenMaya.MTime.uiUnit()))
        print('start frame ' + str(start_frame) + ' end frame ' + str(end_frame))

        # TODO remove spaceLocator hack and get correct absolute world space translation
        temp_locator = cmds.spaceLocator()
        cmds.parentConstraint(animated_dag_path, temp_locator, maintainOffset=False)
        self.animated_translations = []

        original_ctx = OpenMaya.MDGContext(OpenMaya.MTime(0, OpenMaya.MTime.uiUnit()))
        original_ctx = original_ctx.makeCurrent()
        for i in range(start_frame, end_frame):
            time_ctx = OpenMaya.MDGContext(OpenMaya.MTime(i, OpenMaya.MTime.uiUnit()))
            time_ctx.makeCurrent()
            t = cmds.xform(temp_locator, query=True, translation=True, worldSpace=True)
            self.animated_translations.append(OpenMaya.MVector(t[0], t[1], t[2]))
        original_ctx.makeCurrent()
        cmds.delete(temp_locator)


class Point:
    screen_point = OpenMaya.MPoint()
    world_point = OpenMaya.MPoint()

    def __init__(self, w, f=0):
        self.set_world_point(OpenMaya.MPoint(w[0], w[1], w[2]))
        self.feathering = f

    def set_world_point(self, p):
        self.world_point = p
        self.screen_point = world_to_view(p)

    def set_screen_point(self, p):
        self.screen_point = p
        self.world_point = view_to_world(p)

    def within_dist(self, other, t):
        ss_other = world_to_view(other)
        delta = OpenMaya.MVector(self.screen_point - ss_other)
        if abs(delta.x) < t and abs(delta.y) < t:
            dist = delta.length()
            if dist < t:
                return True, dist
        return False, 0

    def __str__(self):
        result = 'world ' + str(self.world_point) + ' screen ' + str(self.screen_point)
        return result


def world_to_view(p):
    x, y, b = OpenMayaUI.M3dView.active3dView().worldToView(p)
    return OpenMaya.MPoint(x, y)


def view_to_world(p):
    wp = OpenMaya.MPoint()
    wv = OpenMaya.MVector()
    OpenMayaUI.M3dView.active3dView().viewToWorld(int(p.x), int(p.y), wp, wv)
    return wp


class PaintParams:
    def __init__(self):
        self.modifier = ''
        self.radius = 50
        self.inner_radius = 10
        self.current_anchor_point = OpenMaya.MPoint()
        self.last_drag_point = OpenMaya.MPoint()
        self.string = ''

    def adjust_radius(self, value):
        self.radius += value
        if self.radius <= 5:
            self.radius = 5
        if self.radius <= self.inner_radius:
            self.inner_radius = self.radius
        if self.radius >= 300:
            self.radius = 300

    def adjust_inner_radius(self, value):
        self.inner_radius += value
        if self.inner_radius <= 5:
            self.inner_radius = 5
        if self.inner_radius >= self.radius:
            self.inner_radius = self.radius
        elif self.inner_radius >= 300:
            self.inner_radius = 300

    def get_feathering(self, dist):
        # smooth non-linearity based on TanH
        if dist < self.inner_radius:
            return 1
        x = dist - self.inner_radius
        y = self.radius - self.inner_radius
        z = x / y
        a = 3 * z ** 2
        b = 1 - a / (z + 0.00001)
        c = math.tanh(b) / 1.75
        result = c + 0.57
        return result


def update_feather_mask(brush_location):
    global params
    for p in params.motion_trail_points:
        result, dist = p.within_dist(brush_location, params.brush.radius)
        if result:
            p.feathering = params.brush.get_feathering(dist)
        else:
            p.feathering = 0


def set_actual_trail(trail_points):
    coordinates = ''
    for p in trail_points:
        coordinates += str(p.world_point.x) + ' ' + str(p.world_point.y) + ' ' + str(p.world_point.z) + ' ' + str(p.world_point.w) + ' '
    cmd = 'setAttr motionTrail1.points -type pointArray ' + str(len(trail_points)) + ' ' + coordinates + ' ;'
    mel.eval(cmd)


def paint_trajectory_press():
    global params

    # update from the scene in case we undo
    get_motion_trail_from_scene()
    """
    if len(params.motion_trail_points) is not len(params.animated_translations):
        cancel_tool("motion trail points ("+str(len(params.motion_trail_points))+")  not the same length as animated translations ("
                    + str(len(params.animated_translations)) + ")")
    """
    params.brush.current_anchor_point = Point(cmds.draggerContext(params.context, query=True, anchorPoint=True))

    update_feather_mask(params.brush.current_anchor_point.world_point)
    params.brush.last_drag_point = params.brush.current_anchor_point
    params.brush.modifier = cmds.draggerContext(params.context, query=True, modifier=True)


def get_motion_trail_from_scene():
    global params
    params.motion_trail_points = []
    for trail_point in cmds.getAttr('motionTrail1.points'):
        p = Point(trail_point)
        params.motion_trail_points.append(p)


def smooth_points():
    cancel_tool("smooth not implemented")
    pass


def paint_trajectory_drag():
    global params
    drag_position = Point(cmds.draggerContext(params.context, query=True, dragPoint=True))
    button = cmds.draggerContext(params.context, query=True, button=True)

    if button == 1:
        if 'shift' in params.brush.modifier:
            smooth_points()
        else:
            drag_points(params.brush, drag_position.world_point, params.motion_trail_points)

        if params.normalize_to_origin:
            for i in range(len(params.motion_trail_points) - 1):
                p = params.motion_trail_points[i]
                origin = params.animated_translations[i]
                vec = OpenMaya.MVector(p.world_point) - origin
                p.set_world_point(OpenMaya.MPoint(origin + (vec.normal() * params.normalization_dist)))
        if params.loop_animation:
            params.motion_trail_points[0] = params.motion_trail_points[-1]
        set_actual_trail(params.motion_trail_points)
        OpenMayaUI.M3dView.active3dView().refresh()

    if button == 2:
        adjust = 2
        if drag_position.world_point.x < params.brush.last_drag_point.world_point.x:
            adjust *= -1

        if 'shift' in params.brush.modifier:
            params.brush.adjust_inner_radius(adjust)
        else:
            params.brush.adjust_radius(adjust)
        cmds.headsUpMessage("radius: " + str(params.brush.inner_radius) + " / " + str(params.brush.radius), time=1.0)

    params.brush.last_drag_point = drag_position


def drag_points(brush, drag_point, points):
    for p in points:
        if p.feathering > 0:
            p.set_world_point(p.world_point + ((drag_point - brush.last_drag_point.world_point) * p.feathering))


def paint_trajectory_release():
    return


def paint_trajectory_init():
    global params
    selection_list = OpenMaya.MGlobal.getActiveSelectionList()
    if not selection_list.isEmpty():
        params = PaintTrajectoryParams(selection_list)
    else:
        cancel_tool("please select an obect")

    cmds.draggerContext(params.context, edit=cmds.draggerContext(params.context, exists=True),
                        pressCommand='paint_trajectory_press()', dragCommand='paint_trajectory_drag()',
                        releaseCommand='paint_trajectory_release()',
                        space='world', cursor='crossHair', undoMode="step")
    cmds.setToolTo(params.context)


def cancel_tool(string):
    print(string)
    cmds.headsUpMessage(string, time=2.0)
    sys.exit()
