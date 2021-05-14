from maya import cmds
from maya.api import OpenMayaAnim, OpenMaya
from maya.api.OpenMaya import MPoint, MVector, MTime, MColor, MGlobal
from maya.api.OpenMayaUI import M3dView

from anim.paint_face import PaintFace
from tools.paint_system import PaintPoint, LockAxis
from core.debug import fail_exit

global tool


def paint_face_press():
    global tool
    tool.brush.anchor_point = PaintPoint(cmds.draggerContext(tool.context, query=True, anchorPoint=True))

    tool.update_view_points()  # we may have moved the camera

    tool.update_feather_mask(tool.paintable_points, tool.brush.anchor_point.world_point)
    tool.brush.last_drag_point = tool.brush.anchor_point
    tool.brush.modifier = cmds.draggerContext(tool.context, query=True, modifier=True)
    tool.draw_paint_points()


def paint_face_drag():
    global tool
    drag_point = PaintPoint(cmds.draggerContext(tool.context, query=True, dragPoint=True))
    button = cmds.draggerContext(tool.context, query=True, button=True)

    tool.update_lock_axis_leash(drag_point, 5)
    if button == 1:
        if 'ctrl' in tool.brush.modifier:
            if tool.brush.lock_axis is LockAxis.kVertical:
                tool.drag_smooth_timeline(drag_point)
            elif tool.brush.lock_axis is LockAxis.kHorizontal:
                print("undefined")
        else:
            tool.draw_brush_circles(drag_point.view_point)
            if 'shift' in tool.brush.modifier:
                tool.update_feather_mask(tool.paintable_points, drag_point.world_point)
                tool.relax_points()
                print("undefined")
            else:
                tool.drag_points(drag_point.world_point)
                tool.update_driven_objects()

    if button == 2:
        adjust = int(min(max(-10, drag_point.view_point.x - tool.brush.last_drag_point.view_point.x), 10))

        if 'ctrl' in tool.brush.modifier:
            if tool.brush.lock_axis is LockAxis.kVertical:
                print("undefined")
            elif tool.brush.lock_axis is LockAxis.kHorizontal:
                print("undefined")
        else:
            if tool.brush.lock_axis is LockAxis.kHorizontal:
                if 'shift' in tool.brush.modifier:
                    tool.brush.adjust_inner_radius(adjust)
                else:
                    tool.brush.adjust_radius(adjust)
                tool.draw_brush_circles(tool.brush.anchor_point.view_point, MColor((1.0, 1.0, 1.0, 0.5)), True)
                cmds.headsUpMessage("radius: " + str(tool.brush.inner_radius) + " / " + str(tool.brush.radius), time=1.0)

    tool.draw_paint_points()
    tool.update_view_points()
    M3dView.active3dView().refresh()
    tool.brush.last_drag_point = drag_point


def paint_face_release():
    global tool
    if tool.brush.anchor_point is tool.brush.last_drag_point:
        print("{m} click it".format(m=tool.brush.modifier))
        if 'ctrl' in tool.brush.modifier:
            tool.update_feather_mask(tool.paintable_points, tool.brush.last_drag_point.world_point)
            tool.lock_points()
            tool.draw_paint_points()
    if 'ctrl' in tool.brush.modifier:
        if tool.brush.lock_axis is LockAxis.kVertical:
            current_time = round(OpenMayaAnim.MAnimControl.currentTime().asUnits(MTime.uiUnit()))
            OpenMayaAnim.MAnimControl.setCurrentTime(MTime(current_time, MTime.uiUnit()))
    else:
        tool.key_driven_objects()

    tool.draw_brush_circles(tool.brush.last_drag_point.view_point, MColor((0.0, 0.0, 0.0, 0.0)), False)
    tool.brush.lock_axis = LockAxis.kNothing



def paint_face_setup():
    global tool
    tool.build_draw_shapes()
    print("tool setup")


def paint_face_exit():
    global tool
    for p in tool.paintable_scene_objects:
        cmds.showHidden(p.scene_name)
    tool.draw_points = []
    tool.delete_ui_draw_group()
    print("tool exited")


def paint_face_init():
    cmds.setToolTo('selectSuperContext')  # TODO remove for final just here for rapid code testing
    global tool
    tool = PaintFace()
    cmds.draggerContext(tool.context, edit=cmds.draggerContext(tool.context, exists=True),
                        pressCommand='paint_face_press()',
                        dragCommand='paint_face_drag()',
                        releaseCommand='paint_face_release()',
                        initialize='paint_face_setup()',
                        finalize='paint_face_exit()',
                        projection="viewPlaneproject",
                        space='world', cursor='crossHair', undoMode="step", )

    cmds.setToolTo(tool.context)
