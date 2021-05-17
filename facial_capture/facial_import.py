import collections

import maya.cmds as cmds
from maya.api.OpenMaya import MVector

ProgressTuple = collections.namedtuple('ProgressWindow', ['window', 'control'])

file_name = "D:\\gamedev\\python\\output\\example.txt"


def create_progress_window(size):
    win = cmds.window(title='Squared Error', toolbox=True)
    cmds.columnLayout()
    progress_window = ProgressTuple(win, cmds.progressBar(maxValue=size, width=400))
    cmds.showWindow(progress_window.window)
    return progress_window


input_file = open(file_name, "r")
input_lines = input_file.readlines()

prog = create_progress_window(len(input_lines))

locators = []
for i in range(68):
    locators.append(cmds.spaceLocator())

current_frame = 0
for line in input_lines:
    keys = line.split(']')[0].split('[')[-1].split(',')
    current_frame += 1
    average_x = 0
    average_y = 0
    average_z = 0
    average_length = 0
    i = 0
    average_vector = MVector()
    raw_vectors = []
    while i < len(keys):
        x = float(keys[i + 0])
        y = -float(keys[i + 1])
        z = float(keys[i + 2])
        average_vector += MVector(x,y,z)
        vector = MVector(x, y, z)
        raw_vectors.append(vector)
        i += 3
    average_vector /= 68
    centered_vectors = []
    for rv in raw_vectors:
        vector = rv - average_vector
        centered_vectors.append(vector)
        average_length += vector.length()
    average_length /= 68
    normalized_vectors = [v / average_length for v in centered_vectors]
    for i, v in enumerate(normalized_vectors):
        cmds.setKeyframe(locators[i], attribute='translateX', t=[current_frame, current_frame], v=v.x)
        cmds.setKeyframe(locators[i], attribute='translateY', t=[current_frame, current_frame], v=v.y)
        cmds.setKeyframe(locators[i], attribute='translateZ', t=[current_frame, current_frame], v=v.z)
    cmds.progressBar(prog.control, edit=True, step=1)
cmds.deleteUI(prog.window)
