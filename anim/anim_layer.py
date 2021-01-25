import maya.cmds as cmds

print("anim.anim_layer loaded")


class anim_layer:

    def __init__(self, name):
        if cmds.animLayer(name, query=True, exists=True):
            print(name + ' already exists')
            self.scene_name = name
        else:
            self.scene_name = cmds.animLayer(name)




