from maya import cmds
from maya.api import OpenMayaAnim, OpenMaya
from maya.api.OpenMaya import MPoint, MVector, MTime
from maya.api.OpenMayaUI import M3dView

from anim.paint_trajectory import PTPoint, LockAxis, PaintTrajectory
from core.debug import fail_exit

tool = None


def paint_trajectory_press():
    global tool
    tool.get_motion_trail_from_scene()  # update from the scene in case we undo
    tool.brush.anchor_point = PTPoint(cmds.draggerContext(tool.context, query=True, anchorPoint=True))
    tool.update_feather_mask(tool.brush.anchor_point.world_point)
    tool.brush.last_drag_point = tool.brush.anchor_point
    tool.brush.modifier = cmds.draggerContext(tool.context, query=True, modifier=True)
    tool.visible_range.update_range()


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
        tool = PaintTrajectory(selection_list)
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
