import math
from maya import cmds, mel
from maya.api import OpenMaya, OpenMayaAnim
from maya.api.OpenMaya import MEulerRotation, MPoint, MVector, MTime, MSpace, MQuaternion
from maya.api.OpenMayaUI import M3dView
from maya.api.MDGContextGuard import MDGContextGuard

from core.debug import fail_exit
from anim.anim_layer import AnimLayer
from core.scene_util import world_to_view, view_to_world
from core.basis import Basis

tool = None
maya_useNewAPI = True


class LockAxis:
    kNothing = 0
    kHorizontal = 1
    kVertical = 2

    def __init__(self): pass


class PTPoint:
    view_point = MPoint()
    world_point = MPoint()

    def __init__(self, wp=None, f=0):
        if wp is None:
            wp = [0, 0, 0]
        self.set_world_point(MPoint(wp[0], wp[1], wp[2]))
        self.feathering = f

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


class AnimatedObject:
    scene_name = None
    dag_path = None
    transform_func = None
    dag_func = None
    basis_frames = []

    def __init__(self):
        pass


class PaintTrajectoryTool:
    motion_trail_points = None

    normalize_to_origin = True
    normalization_dist = 12

    loop_animation = True
    smooth_strength = 0.125
    animated_object = AnimatedObject()
    anim_layer = AnimLayer('paint_trajectory_layer')

    def __init__(self, selection_list, context='paint_trajectory_ctx'):
        self.context = context
        self.brush = BrushParams()
        self.animated_object.scene_name = selection_list.getSelectionStrings()[0]
        self.anim_layer.add_rotation(self.animated_object.scene_name)
        self.animated_object.dag_path = selection_list.getDagPath(0)
        self.animated_object.dag_func = OpenMaya.MFnDagNode(self.animated_object.dag_path)
        self.animated_object.transform_func = OpenMaya.MFnTransform(self.animated_object.dag_path)
        print(self.animated_object.transform_func.rotationOrder())
        if not OpenMayaAnim.MAnimUtil.isAnimated(self.animated_object.dag_path):
            fail_exit("please select an animated object")

        self.start_frame = int(OpenMayaAnim.MAnimControl.minTime().asUnits(MTime.uiUnit()))
        self.end_frame = int(OpenMayaAnim.MAnimControl.maxTime().asUnits(MTime.uiUnit()))
        self.frame_count = self.end_frame - self.start_frame

        self.get_motion_trail_from_scene()
        self.create_base_frames()
        self.normalization_dist = MVector(self.animated_object.basis_frames[0].translation
                                          - MVector(self.motion_trail_points[0].world_point)).length()

    def create_base_frames(self):
        for i in range(self.start_frame, self.end_frame + 1):
            basis = self.build_basis_at_frame(i)
            self.animated_object.basis_frames.append(basis)

    def build_basis_at_frame(self, frame):
        # noinspection PyUnusedLocal
        with MDGContextGuard(OpenMaya.MDGContext(MTime(frame, MTime.uiUnit()))) as guard:
            t = self.animated_object.transform_func.rotatePivot(MSpace.kWorld)
            r = self.animated_object.transform_func.rotation()
            o = MVector(self.motion_trail_points[frame].world_point - t).normalize()
            matrix = self.animated_object.dag_path.inclusiveMatrix()
            x = MVector(matrix.getElement(0, 0), matrix.getElement(0, 1), matrix.getElement(0, 2))
            y = MVector(matrix.getElement(1, 0), matrix.getElement(1, 1), matrix.getElement(1, 2))
            z = MVector(matrix.getElement(2, 0), matrix.getElement(2, 1), matrix.getElement(2, 2))
        return Basis(t, r, o, x, y, z)

    def adjust_normalization_dist(self, value):
        self.normalization_dist += value
        if self.normalization_dist <= 5:
            self.normalization_dist = 5
        elif self.normalization_dist >= 1000:
            self.normalization_dist = 1000
        self.update_normalization_dist()
        self.set_actual_trail()
        M3dView.active3dView().refresh()

    def get_lock_axis_delta(self, end, start):
        if self.brush.lock_axis is LockAxis.kHorizontal:
            delta = end.x - start.x
        else:
            delta = end.y - start.y
        return min(max(-1, delta), 1)

    def drag_trail_frame_range(self, end):
        start = self.brush.last_drag_point
        adjustment = MVector(end.view_point - start.view_point).length() * self.get_lock_axis_delta(end.view_point, start.view_point) * 0.125
        current = cmds.getAttr('motionTrail1HandleShape.preFrame')
        result = min(max(1, current + adjustment), int(self.frame_count / 2))
        cmds.setAttr('motionTrail1HandleShape.preFrame', result)
        cmds.setAttr('motionTrail1HandleShape.postFrame', result)

    def drag_normalization_dist(self, end):
        start = self.brush.last_drag_point
        adjustment = MVector(end.world_point - start.world_point).length()
        delta = self.get_lock_axis_delta(end.view_point, start.view_point)
        self.normalization_dist = max(1, self.normalization_dist + adjustment * delta)
        cmds.headsUpMessage("distance: " + str(int(self.normalization_dist)), time=1.0)

    def drag_smooth_timeline(self, end):
        start = self.brush.last_drag_point
        current_time = OpenMayaAnim.MAnimControl.currentTime().asUnits(MTime.uiUnit())
        adjustment = MVector(end.view_point - start.view_point).length() * self.get_lock_axis_delta(end.view_point, start.view_point) * 0.125
        new_time = current_time + -adjustment

        if new_time > self.end_frame:
            new_time -= self.frame_count
        elif new_time < self.start_frame:
            new_time += self.frame_count

        OpenMayaAnim.MAnimControl.setCurrentTime(MTime(new_time, MTime.uiUnit()))

    def update_feather_mask(self, position):
        for p in self.motion_trail_points:  # type: PTPoint
            result, dist = p.within_dist(position, self.brush.radius)
            if result:
                p.feathering = self.brush.get_feathering(dist)
            else:
                p.feathering = 0

    def get_motion_trail_from_scene(self):
        self.motion_trail_points = []
        for trail_point in cmds.getAttr('motionTrail1.points'):
            p = PTPoint(trail_point)
            self.motion_trail_points.append(p)

    @staticmethod
    def smooth_adjacent_points(prv, cur, nxt, amount):
        """ opperate in-place on point and two neighbours """
        to_prev = MVector(prv.world_point - cur.world_point)
        to_next = MVector(nxt.world_point - cur.world_point)
        combined = (to_next + to_prev) * amount
        cur.set_world_point(MPoint(MVector(cur.world_point) + (combined * cur.feathering)))
        prv.set_world_point(MPoint(MVector(prv.world_point) + (-combined * prv.feathering ** 2)))
        nxt.set_world_point(MPoint(MVector(nxt.world_point) + (-combined * nxt.feathering ** 2)))
        cur.feathering = 0

    def smooth_points(self):
        for i in range(len(self.motion_trail_points)):
            if self.motion_trail_points[i].feathering > 0:
                # if we're not looping do nothing with the the first and last frames
                if i == len(self.motion_trail_points) - 1 and self.loop_animation:
                    self.smooth_adjacent_points(self.motion_trail_points[-2],
                                                self.motion_trail_points[-1],
                                                self.motion_trail_points[0],
                                                self.smooth_strength)
                elif i == 0 and self.loop_animation:
                    self.smooth_adjacent_points(self.motion_trail_points[-1],
                                                self.motion_trail_points[0],
                                                self.motion_trail_points[1],
                                                self.smooth_strength)
                else:
                    self.smooth_adjacent_points(self.motion_trail_points[i - 1],
                                                self.motion_trail_points[i],
                                                self.motion_trail_points[i + 1],
                                                self.smooth_strength)

    def set_actual_trail(self):
        coordinates = ''
        for p in self.motion_trail_points:  # type: PTPoint
            coordinates += str(p.world_point.x) + ' ' + str(p.world_point.y) + ' ' + str(p.world_point.z) + ' ' + str(p.world_point.w) + ' '
        cmd = 'setAttr motionTrail1.points -type pointArray ' + str(len(self.motion_trail_points)) + ' ' + coordinates + ' ;'
        mel.eval(cmd)

    def update_normalization_dist(self):
        for i in range(len(self.motion_trail_points) - 1):
            p = self.motion_trail_points[i]
            origin = self.animated_object.basis_frames[i].translation
            vec = (MVector(p.world_point) - MVector(origin)).normal()
            p.set_world_point(MPoint(origin + MVector(vec.normal() * self.normalization_dist)))

    def drag_points(self, drag_point):
        for p in self.motion_trail_points:
            if p.feathering > 0:
                p.set_world_point((p.world_point + (drag_point - self.brush.last_drag_point.world_point) * p.feathering))

    def update_lock_axis_leash(self, drag_point, leash):
        if self.brush.lock_axis is LockAxis.kNothing:
            delta = drag_point.view_point - self.brush.anchor_point.view_point
            if MVector(delta).length() >= leash:
                self.brush.lock_axis = LockAxis.kHorizontal if abs(delta.x) > abs(delta.y) else LockAxis.kVertical

    def update_animated_frames(self):
        for i in range(len(self.animated_object.basis_frames)):
            p = self.motion_trail_points[i]
            b = self.animated_object.basis_frames[i]
            origin = b.translation
            vec = (MVector(p.world_point) - MVector(origin)).normal()
            direction = b.offset.normal()
            quat = direction.rotateTo(vec)
            rot_key = quat.asEulerRotation()
            axis_correct = MQuaternion().setToXAxis(-rot_key.x)  # TODO spin axis should be arbitrary
            final_rot = b.rotation + (quat * axis_correct).asEulerRotation()

            cmds.setKeyframe(self.animated_object.scene_name, animLayer=self.anim_layer.scene_name, minimizeRotation=True,
                             v=OpenMaya.MAngle(final_rot.x).asDegrees(), at='rotateX', time=i)
            cmds.setKeyframe(self.animated_object.scene_name, animLayer=self.anim_layer.scene_name, minimizeRotation=True,
                             v=OpenMaya.MAngle(final_rot.y).asDegrees(), at='rotateY', time=i)
            cmds.setKeyframe(self.animated_object.scene_name, animLayer=self.anim_layer.scene_name, minimizeRotation=True,
                             v=OpenMaya.MAngle(final_rot.z).asDegrees(), at='rotateZ', time=i)


def paint_trajectory_press():
    global tool
    tool.get_motion_trail_from_scene()  # update from the scene in case we undo
    tool.brush.anchor_point = PTPoint(cmds.draggerContext(tool.context, query=True, anchorPoint=True))
    tool.update_feather_mask(tool.brush.anchor_point.world_point)
    tool.brush.last_drag_point = tool.brush.anchor_point
    tool.brush.modifier = cmds.draggerContext(tool.context, query=True, modifier=True)


def paint_trajectory_drag():
    global tool
    drag_point = PTPoint(cmds.draggerContext(tool.context, query=True, dragPoint=True))
    button = cmds.draggerContext(tool.context, query=True, button=True)

    tool.update_lock_axis_leash(drag_point, 5)
    if button == 1:
        if 'ctrl' in tool.brush.modifier:
            if tool.brush.lock_axis is LockAxis.kVertical:
                tool.drag_smooth_timeline(drag_point)

        elif 'shift' in tool.brush.modifier:
            tool.update_feather_mask(drag_point.world_point)
            tool.smooth_points()
        else:
            tool.drag_points(drag_point.world_point)

        if tool.normalize_to_origin:
            # TODO update after setting rotations?
            tool.update_normalization_dist()

        if tool.loop_animation:
            average = MPoint((MVector(tool.motion_trail_points[0].world_point) + MVector(tool.motion_trail_points[-1].world_point)) * 0.5)
            tool.motion_trail_points[0].set_world_point(average)
            tool.motion_trail_points[-1].set_world_point(average)

    if button == 2:
        adjust = int(min(max(-1, drag_point.view_point.x - tool.brush.last_drag_point.view_point.x), 1))

        if 'ctrl' in tool.brush.modifier:
            if tool.brush.lock_axis is LockAxis.kVertical:
                tool.drag_normalization_dist(drag_point)
                tool.update_normalization_dist()
            elif tool.brush.lock_axis is LockAxis.kHorizontal:
                tool.drag_trail_frame_range(drag_point)
        else:
            if tool.brush.lock_axis is LockAxis.kHorizontal:
                if 'shift' in tool.brush.modifier:
                    tool.brush.adjust_inner_radius(adjust)
                else:
                    tool.brush.adjust_radius(adjust)
                cmds.headsUpMessage("radius: " + str(tool.brush.inner_radius) + " / " + str(tool.brush.radius), time=1.0)

    tool.set_actual_trail()
    M3dView.active3dView().refresh()
    tool.brush.last_drag_point = drag_point


def paint_trajectory_release():
    global tool
    if tool.brush.anchor_point is tool.brush.last_drag_point:
        print("{m} click it".format(m=tool.brush.modifier))

    if 'ctrl' in tool.brush.modifier and tool.brush.lock_axis is LockAxis.kVertical:
        current_time = round(OpenMayaAnim.MAnimControl.currentTime().asUnits(MTime.uiUnit()))
        OpenMayaAnim.MAnimControl.setCurrentTime(MTime(current_time, MTime.uiUnit()))

    tool.brush.lock_axis = LockAxis.kNothing
    tool.update_animated_frames()


def paint_trajectory_setup():
    print("tool setup")


def paint_trajectory_exit():
    print("tool exited")


def paint_trajectory_init():
    cmds.setToolTo('selectSuperContext')  # TODO remove for final just here for rapid code testing
    global tool
    selection_list = OpenMaya.MGlobal.getActiveSelectionList()
    if not selection_list.isEmpty():
        tool = PaintTrajectoryTool(selection_list)
    else:
        fail_exit("please select an object")

    cmds.draggerContext(tool.context, edit=cmds.draggerContext(tool.context, exists=True),
                        pressCommand='paint_trajectory_press()',
                        dragCommand='paint_trajectory_drag()',
                        releaseCommand='paint_trajectory_release()',
                        initialize='paint_trajectory_setup()',
                        finalize='paint_trajectory_exit()',
                        projection="viewPlaneproject",
                        space='world', cursor='crossHair', undoMode="step", )

    cmds.setToolTo(tool.context)
