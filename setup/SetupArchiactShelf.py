import maya.cmds as cmds
import tools.MergeDecals as decals
import os

# A null function to get around errors passing None to some functions.
def _null(*args):
    pass

# Functions to create a maya shelf.
class _shelf():
    
    def __init__(self, name="customShelf", iconPath=""):
        self.name = name
        self.iconPath = iconPath
        self.labelBackground = (0, 0, 0, 0)
        self.labelColour = (0.9, 0.9, 0.9)
        self._cleanOldShelf()
        cmds.setParent(self.name)
        self.build()

    def build(self):
        '''This method should be overwritten in derived classes to actually build the shelf
        elements. Otherwise, nothing is added to the shelf.'''
        pass
    
    def _cleanOldShelf(self):
        if cmds.shelfLayout(self.name, ex=1):
            if cmds.shelfLayout(self.name, q=1, ca=1):
                for each in cmds.shelfLayout(self.name, q=1, ca=1):
                    cmds.deleteUI(each)
        else:
            cmds.shelfLayout(self.name, p="ShelfLayout")

    def AddButton(self, label, icon="commandButton.png", command=_null, doubleCommand=_null):
        cmds.setParent(self.name)
        if icon:
            icon = self.iconPath + icon
        print (icon)
        cmds.shelfButton(width=37, height=37, image=icon, l=label, command=command, dcc=doubleCommand, imageOverlayLabel="", olb=self.labelBackground, olc=self.labelColour)
    
    def AddMenuItem(self, parent, label, command=_null, icon=""):
        if icon:
            icon = self.iconPath + icon
        return cmds.menuItem(p=parent, l=label, c=command, i="")

    def AddSubMenu(self, parent, label, icon=None):
        if icon:
            icon = self.iconPath + icon
        return cmds.menuItem(p=parent, l=label, i=icon, subMenu=1)

# Creates the archiact shelf.
class archiactShelf(_shelf):
    def build(self):
        d = decals.decals()
        self.AddButton("Merge Decals", command=d.MergeDecalAndBase, icon="MergeDecals.png")
        

radPath = os.environ['RADIANT_BASE_PATH'].split(';')[0]
archiactShelf(name="Archiact", iconPath=(radPath + "/Tools/Maya/scripts/ui/"))