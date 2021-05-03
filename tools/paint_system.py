import math
import maya.cmds as cmds
from maya.api import OpenMayaAnim
from core.scene_util import world_to_view, view_to_world
from maya.api.OpenMaya import MPoint, MVector, MSpace, MTime, MColor
from ui.ui_draw_manager import ui_draw_manager_plugin_path, UIDrawLine, UIDrawCircle, UIDrawPoint, get_ui_draw_group


class LockAxis:
    kNothing = 0
    kHorizontal = 1
    kVertical = 2

    def __init__(self): pass


class PTPoint:
    view_point = MPoint()
    world_point = MPoint()

    def __init__(self, wp=None, locked=False):
        if wp is None:
            wp = [0, 0, 0]
        self.set_world_point(MPoint(wp[0], wp[1], wp[2]))
        self.feathering = 0
        self.is_locked = locked

    def set_world_point(self, p):  # type :(MPoint) -> None
        self.world_point = p
        self.view_point = world_to_view(p)

    def set_view_point(self, p):  # type :(MPoint) -> None
        self.view_point = p
        self.world_point = view_to_world(p)

    def within_dist(self, other, radius, space=MSpace.kWorld):
        if space is MSpace.kWorld:
            other = world_to_view(other)
        delta = MVector(self.view_point - other)
        if abs(delta.x) < radius and abs(delta.y) < radius:
            dist = delta.length()
            if dist < radius:
                return True, dist
        return False, 0.0

    def __str__(self):
        result = 'world ' + str(self.world_point) + ' view ' + str(self.view_point)
        return result


class BrushParams:
    lock_axis = LockAxis.kNothing

    def __init__(self):
        self.modifier = ''
        self.radius = 50
        self.inner_radius = 10
        self.anchor_point = PTPoint()
        self.last_drag_point = PTPoint()
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


class PaintSystem:
    # timeline
    scrub_scale = 0.125
    scrub_discrete = False

    # drawables
    brush_circles = []

    def __init__(self):
        self.brush = BrushParams()

        self.start_frame = int(OpenMayaAnim.MAnimControl.minTime().asUnits(MTime.uiUnit()))
        self.end_frame = int(OpenMayaAnim.MAnimControl.maxTime().asUnits(MTime.uiUnit()))
        self.frame_count = self.end_frame - self.start_frame
        '''
        # TODO figure this bullshit out
        # noinspection PyUnusedLocal
        path, name = ui_draw_manager_plugin_path()
        if cmds.pluginInfo('ui_draw_manager.py', q=True, loaded=False):
            cmds.loadPlugin('D:/GameDev/maya_scripts/ui/ui_draw_manager.py')
            '''

    def get_lock_axis_delta(self, end, start):
        if self.brush.lock_axis is LockAxis.kHorizontal:
            delta = end.x - start.x
        else:
            delta = end.y - start.y
        return min(max(-1, delta), 1)

    def drag_smooth_timeline(self, end):
        start = self.brush.last_drag_point
        current_time = OpenMayaAnim.MAnimControl.currentTime().asUnits(MTime.uiUnit())
        adjustment = MVector(end.view_point - start.view_point).length() * self.get_lock_axis_delta(end.view_point, start.view_point) * self.scrub_scale
        new_time = current_time + -adjustment

        if new_time > self.end_frame:
            new_time -= self.frame_count
        elif new_time < self.start_frame:
            new_time += self.frame_count

        if self.scrub_discrete:
            new_time = round(new_time)

        OpenMayaAnim.MAnimControl.setCurrentTime(MTime(new_time, MTime.uiUnit()))

    def update_feather_mask(self, points, position):
        for p in points:  # type: PTPoint
            result, dist = p.within_dist(position, self.brush.radius)
            if result:
                p.feathering = self.brush.get_feathering(dist)
            else:
                p.feathering = 0

    def update_lock_axis_leash(self, drag_point, leash):
        if self.brush.lock_axis is LockAxis.kNothing:
            delta = drag_point.view_point - self.brush.anchor_point.view_point
            if MVector(delta).length() >= leash:
                self.brush.lock_axis = LockAxis.kHorizontal if abs(delta.x) > abs(delta.y) else LockAxis.kVertical

    def build_draw_shapes(self):
        self.brush_circles.append(UIDrawCircle())
        self.brush_circles.append(UIDrawCircle())

    def draw_brush_circles(self, pos, color=MColor((1, 1, 1, .1)), is_visible=True):
        self.brush_circles[0].set(pos, self.brush.radius, color, 1, is_visible)
        self.brush_circles[1].set(pos, self.brush.inner_radius, color, 1, is_visible)

    @staticmethod
    def delete_ui_draw_group():
        cmds.delete(get_ui_draw_group())

