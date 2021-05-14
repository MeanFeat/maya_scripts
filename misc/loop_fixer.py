import collections

import maya.cmds as cmds

# fix dense loop animation. Match last frame with first.
from core import scene_util

ProgressTuple = collections.namedtuple('ProgressWindow', ['window', 'control'])


def create_progress_window(size):
    win = cmds.window(title='Loop Fixer', toolbox=True)
    cmds.columnLayout()
    progress_window = ProgressTuple(win, cmds.progressBar(maxValue=size, width=400))
    cmds.showWindow(progress_window.window)
    return progress_window


sel = cmds.ls(selection=True)
prog = create_progress_window(len(sel)*6)

current_values = []
'''
for sel in cmds.ls(selection=True, type='joint'):
    for att in ['tx', 'ty', 'tz', 'rx', 'ry', 'rz']:
        if cmds.keyframe(sel, at=att, q=True):
            end_frame_index = cmds.keyframe(sel, at=att, query=True, keyframeCount=True)
            current_values = cmds.keyframe(sel, at=att, t=(0, end_frame_index), q=True, valueChange=True)
            diff = current_values[end_frame_index-1] - current_values[0]
            start, end = scene_util.get_timeline_selection()
            for i in range(0, end_frame_index):
                result = current_values[i] - (diff * (i / end_frame_index))
                cmds.setKeyframe(sel, t=[i], at=att, v=result)
        cmds.progressBar(prog.control, edit=True, step=1)

'''

start_frame_index = int(cmds.currentTime(q=True))
for sel in cmds.ls(selection=True, type='joint'):
    for att in ['tx', 'ty', 'tz', 'rx', 'ry', 'rz']:
        if cmds.keyframe(sel, at=att, q=True):
            end_frame_index = cmds.keyframe(sel, at=att, query=True, keyframeCount=True)
            current_values = cmds.keyframe(sel, at=att, t=(0, end_frame_index), q=True, valueChange=True)
            diff = current_values[-1] - current_values[0]
            for i in range(start_frame_index, end_frame_index):
                result = current_values[i] - (diff * ((i-start_frame_index) / (end_frame_index-start_frame_index)))
                cmds.setKeyframe(sel, t=[i], at=att, v=result)
        cmds.progressBar(prog.control, edit=True, step=1)

cmds.deleteUI(prog.window)
