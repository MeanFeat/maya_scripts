import maya.cmds as cmds
import maya.mel
import maya

'''
Button/Hotkey code
import TrajectoryGuide
reload(TrajectoryGuide)
from TrajectoryGuide import *
'''

t_guide = None
t_guide_group = None
owner = None
pc = None
motion_trail = None
unit_adjust = None


def set_to_motion_trail():
    global t_guide
    print("Switching to : MotionTrail")
    orig_selection = cmds.ls(selection=True)
    cmds.setAttr("TrajectoryGuideShape.ghosting", 0)
    select_guide()
    cmds.CreateMotionTrail()
    cmds.setAttr("motionTrail1Handle.trailDrawMode", 1)
    cmds.setAttr("motionTrail1Handle.trailThickness", 3.0)
    cmds.setAttr("motionTrail1HandleShape.fadeInoutFrames", 15)
    cmds.setAttr("motionTrail1HandleShape.preFrame", 15)
    cmds.setAttr("motionTrail1HandleShape.postFrame", 15)
    cmds.select(orig_selection)


def set_to_ghosting():
    print("Switching to : Ghosting")
    orig_selection = cmds.ls(selection=True)
    frames_val = cmds.intSliderGrp('framesSlider', q=True, v=True)
    select_guide()
    cmds.setAttr("TrajectoryGuideShape.ghosting", 0)
    maya.mel.eval('doGhost "3" { "1", "0", "2", %s, %s, "1", " 3 1 10 20", "1", "120", "0", "1", "1", "0", "0"};' % (
        frames_val, frames_val))
    cmds.select(orig_selection)
    trails = cmds.ls("motionTrail*")
    cmds.delete(trails)


def update_value():
    cmds.setAttr(pc[0] + ".target[0].targetOffsetTranslateX",
                 cmds.floatSliderGrp('x_offset_slider', q=True, v=True) * unit_adjust)
    cmds.setAttr(pc[0] + ".target[0].targetOffsetTranslateY",
                 cmds.floatSliderGrp('y_offset_slider', q=True, v=True) * unit_adjust)
    cmds.setAttr(pc[0] + ".target[0].targetOffsetTranslateZ",
                 cmds.floatSliderGrp('z_offset_slider', q=True, v=True) * unit_adjust)
    cmds.parentConstraint(pc, edit=True, mo=True)
    update_frames()


def update_size():
    size_val = cmds.floatSliderGrp('sizeSlider', q=True, v=True)
    size_attr = t_guide[0] + ".scaleX"
    cmds.setAttr(size_attr, size_val * unit_adjust)
    size_attr = t_guide[0] + ".scaleY"
    cmds.setAttr(size_attr, size_val * unit_adjust)
    size_attr = t_guide[0] + ".scaleZ"
    cmds.setAttr(size_attr, size_val * unit_adjust)


def update_frames():
    orig_selection = cmds.ls(selection=True)
    frames_val = cmds.intSliderGrp('framesSlider', q=True, v=True)
    if cmds.getAttr("TrajectoryGuideShape.ghosting") == 1:
        select_guide()
        cmds.setAttr("TrajectoryGuideShape.ghosting", 0)
        maya.mel.eval(
            'doGhost "3" { "1", "0", "2", %s, %s, "1", " 3 1 10 20", "1", "120", "0", "1", "1", "0", "0"};' % (
                frames_val, frames_val))
        cmds.select(orig_selection)
    else:
        cmds.setAttr("motionTrail1HandleShape.fadeInoutFrames", frames_val)
        cmds.setAttr("motionTrail1HandleShape.preFrame", frames_val)
        cmds.setAttr("motionTrail1HandleShape.postFrame", frames_val)


def get_current_camera():
    pan = cmds.getPanel(wf=True)
    cam = cmds.modelPanel(pan, q=True, camera=True)
    return cam


def select_guide():
    global t_guide
    cmds.select(t_guide)


def delete_guides():
    guides = cmds.ls("TrajectoryGuide*")
    cmds.delete(guides)


def get_unit_adjust(x):
    return {
        'm': 1,
        'cm': 100,
        'mm': 1000
    }.get(x, 1)


def update_constraint_offset():
    global pc
    pc = cmds.parentConstraint(owner, t_guide, edit=True, mo=True)


def tg_menu():
    global t_guide, t_guide_group, owner, pc, motion_trail,  unit_adjust
    selection = cmds.ls(selection=True)
    if len(selection) == 0:
        delete_guides()
        for window in cmds.lsUI(windows=True):
            if "TrajectoryGuideWindow" in window:
                cmds.deleteUI(window, window=True)
    else:
        unit_adjust = get_unit_adjust(cmds.currentUnit(query=True, linear=True)) * 0.1
        owner = selection[0]
        t_guide = cmds.spaceLocator(n="TrajectoryGuide")
        cmds.setKeyframe(t_guide, v=1, at="v")
        t_guide_group = cmds.group(n="TrajectoryGuideGroup")
        pc = cmds.parentConstraint(owner, t_guide)
        menu_win = cmds.window("TrajectoryGuideWindow", title="Trajectory Guide", iconName='TrajectoryGuide',
                               resizeToFitChildren=True, te=100, le=1200)
        cmds.columnLayout(adjustableColumn=True)
        cmds.separator(bgc=(0.75, 0, 0))
        cmds.floatSliderGrp('x_offset_slider', field=True, width=300, min=-100, max=100, value=0,
                            changeCommand='update_value()', dragCommand='update_value()')
        cmds.separator(bgc=(0, 0.75, 0))
        cmds.floatSliderGrp('y_offset_slider', field=True, width=300, min=-100, max=100, value=0,
                            changeCommand='update_value()', dragCommand='update_value()')
        cmds.separator(bgc=(0, 0, 0.75))
        cmds.floatSliderGrp('z_offset_slider', field=True, width=300, min=-100, max=100, value=0,
                            changeCommand='update_value()', dragCommand='update_value()')
        cmds.radioButtonGrp(numberOfRadioButtons=2, label='Type:', cal=(1, "left"), cw3=(25, 75, 25),
                            labelArray2=['MotionTrail', 'Ghosting'], sl=1, on1='set_to_motion_trail()',
                            on2='set_to_ghosting()')
        set_to_motion_trail()
        cmds.intSliderGrp('framesSlider', label='Frames:', width=200, min=1, max=35, value=5,
                          dragCommand='update_frames()')
        cmds.floatSliderGrp('sizeSlider', label='Size:', field=True, width=200, min=0.15, max=5, value=1,
                            dragCommand='update_size()')
        cmds.button(label='Update Constraint', command='update_constraint_offset()')
        cmds.button(label='Select Guide', command='select_guide()')
        cmds.setParent('..')
        cmds.showWindow(menu_win)
        cmds.select(owner)
        update_size()
