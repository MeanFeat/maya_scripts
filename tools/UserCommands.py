import maya.cmds as cmds
import maya.mel


def FrameSelectedTimeline():
    aPlayBackSliderPython = maya.mel.eval('$tmpVar=$gPlayBackSlider')
    rng = cmds.timeControl(aPlayBackSliderPython, q=True, rangeArray=True)
    cmds.playbackOptions(min=rng[0], max=rng[1])


def KeyRange(sel=cmds.ls(selection=True)):
    playbackSlider = maya.mel.eval('$tmpVar=$gPlayBackSlider')
    timeRange = cmds.timeControl(playbackSlider, query=True, rangeArray=True)

    for i in range(int(timeRange[0]), int(timeRange[1])):
        cmds.currentTime(i, update=True)
        cmds.setKeyframe(sel)
