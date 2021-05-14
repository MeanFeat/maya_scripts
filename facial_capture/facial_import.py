import maya.cmds as cmds

locators = []
f = open("D:\\gamedev\\python\\output\\example.txt", "r")
#data = f.read().split(',')

for item in range(68):
    loc = cmds.spaceLocator()
    for coord in ['translateX', 'translateY', 'translateZ']:
        keys = f.readline().split(']')[0].split('[')[-1].split(',')
        for i, k in enumerate(keys):
            if coord is 'translateY':
                k = -float(k)
            cmds.setKeyframe(loc, attribute=coord, t=[i, i], v=float(k))
