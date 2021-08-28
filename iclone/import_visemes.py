from maya import cmds, mel
from maya.api import OpenMaya

file_name = 'D:/Temp/RADIANT_TEMP/input/visemes.arcvis'

attribute_list = ['Open',
                  'Explosive',
                  'Dental_Lip',
                  'Tight_O',
                  'Tight',
                  'Wide',
                  'Affricate',
                  'Lip_Open']


def key_rotation(bone_name):
    x = arcvis_file.readline().split(']')[0].split('[')[-1].split(',')
    y = arcvis_file.readline().split(']')[0].split('[')[-1].split(',')
    z = arcvis_file.readline().split(']')[0].split('[')[-1].split(',')
    w = arcvis_file.readline().split(']')[0].split('[')[-1].split(',')
    for frame in range(0, len(x)):
        quat = OpenMaya.MQuaternion(float(x[frame]), float(y[frame]), float(z[frame]), float(w[frame]))
        if quat == OpenMaya.MQuaternion(0.0, 0.0, 0.0, 0.0):
            rotation = OpenMaya.MEulerRotation(0.0, 0.0, 0.0)
        else:
            rotation = quat.asEulerRotation()
        cmds.setKeyframe(bone_name, attribute="rotateX", t=[frame, frame], v=float(OpenMaya.MAngle(float(rotation.x)).asDegrees()))
        cmds.setKeyframe(bone_name, attribute="rotateY", t=[frame, frame], v=float(OpenMaya.MAngle(float(rotation.y)).asDegrees()))
        cmds.setKeyframe(bone_name, attribute="rotateZ", t=[frame, frame], v=float(OpenMaya.MAngle(float(rotation.z)).asDegrees()))


with open(file_name, "r") as arcvis_file:
    wave_file_name = arcvis_file.readline()
    string = 'doSoundImportArgList ("1", {"' + wave_file_name.rstrip() + '","0"});'
    print(string)
    mel.eval(string)

    arcvis_file.readline()  # none

    for a in attribute_list:
        keys = arcvis_file.readline().split(']')[0].split('[')[-1].split(',')
        for i, k in enumerate(keys):
            cmds.setKeyframe('Morpher_CC_Base_Body', attribute=a, t=[i, i], v=float(k))

    # unknown blendshapes
    arcvis_file.readline()
    arcvis_file.readline()
    arcvis_file.readline()
    arcvis_file.readline()
    arcvis_file.readline()
    arcvis_file.readline()
    arcvis_file.readline()

    key_rotation('CC_Base_JawRoot')
    key_rotation('CC_Base_Tongue01')
