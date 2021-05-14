from maya import cmds
from core import scene_util


def frame_selected_timeline():
    time_range = scene_util.get_timeline_selection()
    cmds.playbackOptions(min=time_range[0], max=(time_range[1]-1))


def frame_past_timeline():
    time_range = scene_util.get_timeline_selection()
    cmds.playbackOptions(min=time_range[0])


def frame_future_timeline():
    time_range = scene_util.get_timeline_selection()
    cmds.playbackOptions(max=(time_range[1]-1))


def trim_past_timeline():
    time_range = scene_util.get_timeline_selection()
    sel = cmds.ls(selection=True)
    start_time = int(cmds.playbackOptions(minTime=True, query=True))
    cmds.cutKey(sel, clear=True, time=(start_time, time_range[0]-1))


def trim_future_timeline():
    time_range = scene_util.get_timeline_selection()
    sel = cmds.ls(selection=True)
    end_time = int(cmds.playbackOptions(maxTime=True, query=True))
    cmds.cutKey(sel, clear=True, time=(time_range[1], end_time))


def key_range(sel):
    time_range = scene_util.get_timeline_selection()
    original_time = cmds.currentTime(query=True)
    for i in range(int(time_range[0]), int(time_range[1])):
        cmds.currentTime(i, update=True)
        cmds.setKeyframe(sel)
    cmds.currentTime(original_time)


def share_keys(sel):
    next_frame, end_frame = scene_util.get_timeline_selection()
    while next_frame < end_frame:
        cmds.currentTime(next_frame, update=True)
        cmds.setKeyframe(sel)
        prev_frame = next_frame
        next_frame = int(cmds.findKeyframe(timeSlider=True, which='next'))
        if prev_frame > next_frame or next_frame == prev_frame:
            break
