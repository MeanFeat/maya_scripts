import collections

import maya.cmds as cmds
from maya.api import OpenMaya
from maya.api.OpenMaya import MVector, MMatrix, MEulerRotation, MAngle

from core.basis import build_plane_normal, build_matrix

ProgressTuple = collections.namedtuple('ProgressWindow', ['window', 'control'])

file_name = "D:\\gamedev\\python\\output\\example.txt"
point_count = 68


def create_progress_window(size):
    win = cmds.window(title='Importing Facial Data', toolbox=True)
    cmds.columnLayout()
    progress = ProgressTuple(win, cmds.progressBar(maxValue=size, width=400))
    cmds.showWindow(progress.window)
    return progress


input_file = open(file_name, "r")
input_lines = input_file.readlines()

progress_window = create_progress_window(len(input_lines))

locators = []
for i in range(point_count):
    locators.append(cmds.spaceLocator())

#cmds.select("capture_points")
#locators = cmds.ls(selection=True)


def get_static_vectors(vector_list):
    average_left = (vector_list[0] + vector_list[1] + vector_list[2] + vector_list[3]) / 4
    average_right = (vector_list[16] + vector_list[15] + vector_list[14] + vector_list[13]) / 4
    average_front = (vector_list[27] + vector_list[28] + vector_list[29] + vector_list[30]) / 4
    return average_left, average_right, average_front


def rotate_vectors(vector_list):
    average_left, average_right, average_front = get_static_vectors(vector_list)
    average_length = (average_left.length() + average_right.length() + average_front.length()) / 3
    normalized_vectors = [v / average_length for v in vector_list]
    triangulation_vectors = [average_right, average_left, average_front]
    plane_normal = build_plane_normal(triangulation_vectors[0], triangulation_vectors[1], triangulation_vectors[2])
    rotation_matrix = build_matrix((plane_normal ^ triangulation_vectors[-1]).normal(), plane_normal.normal(), triangulation_vectors[-1].normal())
    result = []
    for nv in normalized_vectors:
        result.append((rotation_matrix * nv))
    return result, rotation_matrix

#rotation_root = cmds.spaceLocator(name='rotation_root')

current_frame = 0
for line in input_lines:
    keys = line.split(']')[0].split('[')[-1].split(',')
    current_frame += 1

    i = 0
    raw_vectors = []
    while i < len(keys):
        x = float(keys[i + 0])
        y = -float(keys[i + 1])
        z = float(keys[i + 2])
        vector = MVector(x, y, z)
        raw_vectors.append(vector)
        i += 3

    left, right, front = get_static_vectors(raw_vectors)
    average_vector = (left + right + front)/3

    centered_vectors = []
    for rv in raw_vectors:
        centered_vectors.append(rv - average_vector)

    rotated_vectors, matrix = rotate_vectors(centered_vectors)
    euler_rotation = MEulerRotation.decompose(matrix, MEulerRotation.kXYZ)
    for index, value in enumerate(rotated_vectors):
        cmds.setKeyframe(locators[index], attribute='translateX', t=[current_frame, current_frame], v=value.x)
        cmds.setKeyframe(locators[index], attribute='translateY', t=[current_frame, current_frame], v=value.y)
        cmds.setKeyframe(locators[index], attribute='translateZ', t=[current_frame, current_frame], v=value.z)
    #for e, a in zip((euler_rotation.x, euler_rotation.y, euler_rotation.z), ("rotateX", "rotateY", "rotateZ")):
    #    cmds.setKeyframe(rotation_root, minimizeRotation=False, v=OpenMaya.MAngle(e).asDegrees(), at=a, time=current_frame)

    cmds.progressBar(progress_window.control, edit=True, step=1)
cmds.deleteUI(progress_window.window)
