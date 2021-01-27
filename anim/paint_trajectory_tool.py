import math
from maya import cmds, mel
from maya.api import OpenMaya, OpenMayaUI, OpenMayaAnim
from anim.anim_layer import AnimLayer
from core.debug import fail_exit

params = None
maya_useNewAPI = True


class PaintTrajectoryParams:
    motion_trail_points = None

    normalize_to_origin = True
    normalization_dist = 12

    loop_animation = False

    anim_layer = AnimLayer('paint_trajectory_layer')

    def __init__(self, selection_list, context='paint_trajectory_ctx'):
        self.context = context
        self.brush = PaintParams()
        animated_dag_path, animated_object = selection_list.getComponent(0)

        if not OpenMayaAnim.MAnimUtil.isAnimated(animated_dag_path):
            fail_exit("please select an animated object")

        start_frame = int(OpenMayaAnim.MAnimControl.minTime().asUnits(OpenMaya.MTime.uiUnit()))
        end_frame = int(OpenMayaAnim.MAnimControl.maxTime().asUnits(OpenMaya.MTime.uiUnit()))
        print('start frame ' + str(start_frame) + ' end frame ' + str(end_frame))

        self.animated_translations = []
        animated_func = OpenMaya.MFnTransform(animated_dag_path)
        original_ctx = OpenMaya.MDGContext.current()
        for i in range(start_frame, end_frame):
            time_ctx = OpenMaya.MDGContext(OpenMaya.MTime(i, OpenMaya.MTime.uiUnit()))
            time_ctx.makeCurrent()
            t = animated_func.rotatePivot(OpenMaya.MSpace.kWorld)
            self.animated_translations.append(OpenMaya.MVector(t))
        original_ctx.makeCurrent()

    def adjust_normalization_dist(self, value):
        self.normalization_dist += value
        if self.normalization_dist <= 5:
            self.normalization_dist = 5
        elif self.normalization_dist >= 1000:
            self.normalization_dist = 1000
        update_normalization_dist()
        set_actual_trail(self.motion_trail_points)
        OpenMayaUI.M3dView.active3dView().refresh()


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
        """ [bool, distance] when false returns a distance of 0 """
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
        fail_exit("motion trail points ("+str(len(params.motion_trail_points))+")  not the same length as animated translations ("
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
    fail_exit("smooth not implemented")
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
            update_normalization_dist()
        if params.loop_animation:
            params.motion_trail_points[0] = params.motion_trail_points[-1]
        set_actual_trail(params.motion_trail_points)
        OpenMayaUI.M3dView.active3dView().refresh()

    if button == 2:
        adjust = 2
        if drag_position.world_point.x < params.brush.last_drag_point.world_point.x:
            adjust *= -1

        if 'ctrl' in params.brush.modifier:
            params.adjust_normalization_dist(adjust)
            cmds.headsUpMessage("distance: " + str(params.normalization_dist), time=1.0)
        else:
            if 'shift' in params.brush.modifier:
                params.brush.adjust_inner_radius(adjust)
            else:
                params.brush.adjust_radius(adjust)
            cmds.headsUpMessage("radius: " + str(params.brush.inner_radius) + " / " + str(params.brush.radius), time=1.0)

    params.brush.last_drag_point = drag_position


def update_normalization_dist():
    global params
    for i in range(len(params.motion_trail_points) - 1):
        p = params.motion_trail_points[i]
        origin = params.animated_translations[i]
        vec = OpenMaya.MVector(p.world_point) - origin
        p.set_world_point(OpenMaya.MPoint(origin + (vec.normal() * params.normalization_dist)))


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
        fail_exit("please select an object")
        cmds.exitTool()

    cmds.draggerContext(params.context, edit=cmds.draggerContext(params.context, exists=True),
                        pressCommand='paint_trajectory_press()', dragCommand='paint_trajectory_drag()',
                        releaseCommand='paint_trajectory_release()',
                        space='world', cursor='crossHair', undoMode="step")
    cmds.setToolTo(params.context)


