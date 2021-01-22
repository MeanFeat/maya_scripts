import maya.cmds as cmds
import maya.mel as mel
import maya.OpenMaya as OpenMaya
import math


params = None

class PaintTrajectoryParams():
    motion_trail_points = None
    def __init__(self, context = 'paint_trajectory_ctx' ):
        self.context = context
        self.brush = PaintParams()
        self.camera = CameraParams()


class CameraParams:
    def __init__(self, name='persp'):
        selList = OpenMaya.MSelectionList()
        selList.add(name)
        self.name = name
        self.dag_path = OpenMaya.MDagPath()
        selList.getDagPath(0, self.dag_path)
        self.dag_path.extendToShape()

        self.res_width = cmds.getAttr('defaultResolution.width')
        self.res_height = cmds.getAttr('defaultResolution.height')

    def get_inv_matrix(self):
        return self.dag_path.inclusiveMatrix().inverse()


def world_to_screen(test_point, cam):
    # use a camera function set to get projection matrix, convert the MFloatMatrix
    # into a MMatrix for multiplication compatibility
    fn_cam = OpenMaya.MFnCamera(cam.dag_path)
    cam_matrix = fn_cam.projectionMatrix()
    proj_mtx = OpenMaya.MMatrix(cam_matrix.matrix)

    # multiply all together and do the normalisation
    p = OpenMaya.MPoint(test_point.x, test_point.y, test_point.z) * cam.get_inv_matrix() * proj_mtx
    x = (p[0] / p[3] / 2 + .5) * cam.res_width
    y = (p[1] / p[3] / 2 + .5) * cam.res_height
    return OpenMaya.MPoint(x, y)


class Point:
    screen_point = OpenMaya.MPoint()
    world_point = OpenMaya.MPoint()

    def __init__(self, w, f=0):
        self.world_point = OpenMaya.MPoint(w[0], w[1], w[2])
        self.feathering = f

    def update_screen_point(self, cam):
        self.screen_point = world_to_screen(self.world_point, cam)

    def within_dist(self, other, cam, t):
        ss_other = world_to_screen(other, cam)
        delta = self.screen_point - ss_other
        x = self.screen_point[0] - ss_other[0]
        y = self.screen_point[1] - ss_other[1]
        if abs(delta.x) < t and abs(delta.y) < t:
            dist_sqr = get_dist_sqr(x, y)
            if dist_sqr < t ** 2:
                return True, dist_sqr
        return False, 0


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

    def get_feathering(self, dist_sqr):
        # smooth non-linearity based on tanh
        if dist_sqr < self.inner_radius ** 2:
            return 1
        x = math.sqrt(dist_sqr) - self.inner_radius
        y = self.radius - self.inner_radius
        z = x / y
        a = 3 * z ** 2
        b = 1 - a / z
        c = math.tanh(b) / 1.75
        result = c + 0.57
        return result


def get_dist_sqr(x, y):
    result = x * x + y * y
    return result


def update_feather_mask(brush_location):
    global params
    for p in params.motion_trail_points:
        result, dist_sqr = p.within_dist(brush_location, params.camera, params.brush.radius)
        if result:
            p.feathering = params.brush.get_feathering(dist_sqr)
        else:
            p.feathering = 0


def press():
    global params
    for p in params.motion_trail_points:
        p.update_screen_point(params.camera)

    params.brush.current_anchor_point = Point(cmds.draggerContext(params.context, query=True, anchorPoint=True))
    update_feather_mask(params.brush.current_anchor_point.world_point)
    params.brush.last_drag_point = params.brush.current_anchor_point
    params.brush.modifier = cmds.draggerContext(params.context, query=True, modifier=True)


def update_actual_trail(trail_points):
    coordinates = ''
    for p in trail_points:
        coordinates += str(p.world_point.x) + ' ' + str(p.world_point.y) + ' ' + str(p.world_point.z) + ' ' + str(p.world_point.w) + ' '
    cmd = 'setAttr motionTrail1.points -type pointArray ' + str(len(trail_points)) + ' ' + coordinates + ' ;'
    mel.eval(cmd)


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
            p.update_screen_point(params.camera)
        update_actual_trail(params.motion_trail_points)
        cmds.refresh()

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

    params.motion_trail_points = []
    for trail_point in cmds.getAttr('motionTrail1.points'):
        point = Point(trail_point)
        point.update_screen_point(params.camera)
        params.motion_trail_points.append(point)

    cmds.draggerContext(params.context, edit=cmds.draggerContext(params.context, exists=True),
                        pressCommand='press()',
                        dragCommand='drag()',
                        space='world', cursor='crossHair', undoMode="step")
    cmds.setToolTo(params.context)
