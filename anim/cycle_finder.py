import collections
import maya.cmds as cmds

ProgressTuple = collections.namedtuple('ProgressWindow', ['window', 'control'])


def create_progress_window(size):
    win = cmds.window(title='Squared Error', toolbox=True)
    cmds.columnLayout()
    progress_window = ProgressTuple(win, cmds.progressBar(maxValue=size, width=400))
    cmds.showWindow(progress_window.window)
    return progress_window


sel = cmds.ls(selection=True)
selected_time = int(cmds.currentTime(q=True))
start_time = int(cmds.playbackOptions(minTime=True, query=True))
end_time = int(cmds.playbackOptions(maxTime=True, query=True))

attributes_to_sample = ['rx', 'ry', 'rz']
selected_items = cmds.ls(selection=True)
prog = create_progress_window(len(selected_items) * len(attributes_to_sample))
error_per_frame = [0.] * (end_time-start_time+1)
delta_per_frame = [0.] * (end_time-start_time+1)

for sel in selected_items:
    for att in attributes_to_sample:
        if cmds.keyframe(sel, at=att, q=True):
            previous_frame_value = 0.
            selected_frame_value = cmds.keyframe(sel, at=att, t=(selected_time, selected_time), q=True, eval=True)[0]
            for i, v in enumerate(cmds.keyframe(sel, at=att, t=(start_time, end_time), q=True, valueChange=True)):
                error_per_frame[i] += (v - selected_frame_value)**2
                delta_per_frame[i] += (v - previous_frame_value)**2
                previous_frame_value = v
    cmds.progressBar(prog.control, edit=True, step=1)

for frame, error in enumerate(error_per_frame):
    cmds.setKeyframe('root', t=[frame], at='Error', v=error)

for frame, delta in enumerate(delta_per_frame):
    cmds.setKeyframe('root', t=[frame], at='Delta', v=delta)

cmds.deleteUI(prog.window)