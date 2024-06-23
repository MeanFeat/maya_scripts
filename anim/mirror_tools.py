import maya.cmds as cmds
import maya.mel as mel
import core.scene_util as scene_utils
from anim.anim_layer import *
import maya


left = None
right = None
single = None
current_time = None


class CopyOption:
    keys = 0
    curve = 1

    def __init__(self, option_type):
        self.value = option_type

    def __str__(self):
        if self.value == CopyOption.keys:
            return 'keys'
        if self.value == CopyOption.curve:
            return 'curve'

    def __eq__(self, y):
        return self.value == y.value


def select_controls():
    scene_utils.select_layer_objects("*:Controls")


def swap_animation(a, b, option_type=CopyOption(CopyOption.curve)):
    null = cmds.spaceLocator(name="tempCopyNull")
    cmds.select(null, r=True)
    if cmds.selectKey(a) > 0:
        send_animation(a, null, option_type)
    if cmds.selectKey(b) > 0:
        send_animation(b, a, option_type)
    if cmds.selectKey(null) > 0:
        send_animation(null, b, option_type)
    cmds.delete(null)


def send_animation(a, b, option_type=CopyOption(CopyOption.curve)):
    if cmds.selectKey(a) > 0:
        if option_type == CopyOption(CopyOption.keys):
            cmds.cutKey(a, time=(current_time, current_time), option=option_type.__str__())
        else:
            cmds.copyKey(a, option=option_type.__str__())
        cmds.pasteKey(b, option='replaceCompletely')


def populate_lists():
    ctrls = cmds.ls(selection=True)
    result_single = []
    result_left = []
    result_right = []

    temp_left = []
    temp_right = []
    for c in ctrls:
        ctrl_name = c.split(':')  # ignore Namespace
        ctrl_name = ctrl_name[len(ctrl_name) - 1]
        if "_L" in ctrl_name:
            temp_left.append(c)
        elif "_R" in ctrl_name:
            temp_right.append(c)
        else:
            result_single.append(c)
    temp_right.sort()
    temp_left.sort()
    if len(temp_left) != len(temp_right):
        for le in temp_left:
            l_token = le.split('_')[0]
            for ri in temp_right:
                r_token = ri.split('_')[0]
                if (r_token == l_token) and ("_L" in le) and ("_R" in ri):
                    if le not in result_left:
                        result_left.append(le)
                    if ri not in result_right:
                        result_right.append(ri)
    else:
        for l in temp_left:
            result_left.append(l)
        for r in temp_right:
            result_right.append(r)
    return result_left, result_right, result_single


def mirror_animation(item, option_type, scale_matrix):
    attr = ["translateX", "translateY", "translateZ", "rotateX", "rotateY", "rotateZ"]
    for idx, a in enumerate(attr):
        if not cmds.getAttr(item + '.' + a, lock=True):
            cmds.select(cl=True)
            key = cmds.selectKey(item, attribute=a)
            if key > 0:
                if option_type == CopyOption(CopyOption.keys):
                    cmds.selectKey(item, time=(current_time, current_time), attribute=a)
                else:  # "curve"
                    cmds.selectKey(item, attribute=a)
                cmds.scaleKey(valueScale=scale_matrix[idx], valuePivot=0.0)
    cmds.select(item)


def mirror_all():
    select_controls()
    mirror_selection()


def mirror_selection(option_type=CopyOption(CopyOption.curve)):
    global current_time, left, right, single
    current_time = int(cmds.currentTime(query=True))
    left, right, single = populate_lists()
    main_progress_bar = maya.mel.eval('$tmp = $gMainProgressBar;')
    cmds.progressBar(main_progress_bar,
                     edit=True,
                     beginProgress=True,
                     isInterruptable=True,
                     status='Mirroring Controls ...',
                     minValue=0,
                     maxValue=len(single) + len(left) + len(right))
    for s in single:
        mirror_animation(s, option_type, [-1, 1, 1, 1, -1, -1])
        cmds.progressBar(main_progress_bar, edit=True, step=1, status='Mirroring... ' + s)
    for ind in range(0, len(left)):
        swap_animation(left[ind], right[ind], option_type)
        cmds.progressBar(main_progress_bar, edit=True, step=2, status='Mirroring... ' + left[ind])
    cmds.progressBar(main_progress_bar, edit=True, endProgress=True)


def send_across():
    original_selection = cmds.ls(selection=True)
    global current_time, left, right, single
    current_time = int(cmds.currentTime(query=True))
    select_controls()
    left, right, single = populate_lists()

    for item in original_selection:
        if item in left:
            index = left.index(item)
            send_animation(left[index], right[index])
        elif item in right:
            index = right.index(item)
            send_animation(right[index], left[index])
    cmds.select(original_selection)


def swap_across():
    original_selection = cmds.ls(selection=True)
    global current_time, left, right, single
    current_time = int(cmds.currentTime(query=True))
    select_controls()
    left, right, single = populate_lists()

    for item in original_selection:
        if item in left:
            index = left.index(item)
            swap_animation(left[index], right[index])
        elif item in right:
            index = right.index(item)
            swap_animation(right[index], left[index])
    cmds.select(original_selection)