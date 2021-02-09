from maya import cmds
from core import scene_util


def frame_selected_timeline():
    rng = cmds.timeControl(scene_util.get_playback_slider(), q=True, rangeArray=True)
    cmds.playbackOptions(min=rng[0], max=rng[1])


def key_range(sel):
    time_range = scene_util.get_timeline_selection()
    original_time = cmds.currentTime(query=True)
    for i in range(int(time_range[0]), int(time_range[1])):
        cmds.currentTime(i, update=True)
        cmds.setKeyframe(sel)
    cmds.currentTime(original_time)

