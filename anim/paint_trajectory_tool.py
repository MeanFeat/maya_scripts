import maya.cmds as cmds
import maya.mel as mel
from maya.api import OpenMaya
from maya.api import OpenMayaUI
import math


params = None


class PaintTrajectoryParams:
    motion_trail_points = None

    def __init__(self, context='paint_trajectory_ctx'):
        self.context = context
        self.brush = PaintParams()


def world_to_view(p):
    x, y, b = OpenMayaUI.M3dView.active3dView().worldToView(p)
    return OpenMaya.MPoint(x, y)


def view_to_world(p):
    world_point = OpenMaya.MPoint()
    world_vec = OpenMaya.MVector()
    OpenMayaUI.M3dView.active3dView().viewToWorld(int(p.x), int(p.y), world_point, world_vec)
    return world_point


class Point:
    screen_point = OpenMaya.MPoint()
    world_point = OpenMaya.MPoint()

    def __init__(self, w, f=0):
        self.world_point = OpenMaya.MPoint(w[0], w[1], w[2])
        self.feathering = f

    def update_screen_point(self):
        self.screen_point = world_to_view(self.world_point)

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
        # smooth non-linearity based on tanh
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


def press():
    global params
    update_actual_trail()

    params.brush.current_anchor_point = Point(cmds.draggerContext(params.context, query=True, anchorPoint=True))
    
    update_feather_mask(params.brush.current_anchor_point.world_point)
    params.brush.last_drag_point = params.brush.current_anchor_point
    params.brush.modifier = cmds.draggerContext(params.context, query=True, modifier=True)


def update_actual_trail():
    global params
    params.motion_trail_points = []
    for trail_point in cmds.getAttr('motionTrail1.points'):
        p = Point(trail_point)
        params.motion_trail_points.append(p)
        p.update_screen_point()


def drag():
    global params
    drag_position = Point(cmds.draggerContext(params.context, query=True, dragPoint=True))
    button = cmds.draggerContext(params.context, query=True, button=True)

    if button == 1:
        adjust = 1

        if 'ctrl' in params.brush.modifier:
            print('ctrl')
        elif 'shift' in params.brush.modifier:
            adjust *= -1

        for p in params.motion_trail_points:
            feathering = p.feathering * adjust
            p.world_point = p.world_point + ((drag_position.world_point - params.brush.last_drag_point.world_point) * feathering)
            p.update_screen_point()
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


def paint_trajectory_init():
    global params

    params = PaintTrajectoryParams()

    cmds.draggerContext(params.context, edit=cmds.draggerContext(params.context, exists=True),
                        pressCommand='press()', dragCommand='drag()',
                        space='world', cursor='crossHair', undoMode="step")
    cmds.setToolTo(params.context)
