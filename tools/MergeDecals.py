import maya.cmds as cmds
import maya.mel as mm

class decals():
    def __init__(self):
        self.version=1.0
        self.verbose=False

    def VertPaintAlpha(self, node, value):
        cmds.select(node)
        cmds.polyColorPerVertex( alpha=value )
        return True

    # Transfer the UV's & Vertex colors from the main mesh to a second UV on the Decals.
    def TransferUV(self, nodes):
        if len(nodes) > 1:
            cmds.transferAttributes(nodes[0], nodes[1], transferUVs=2, transferColors=2)

            # Decals are now the base UV set. This is incorrect, so we need to fix it.
            n = nodes[0]
            indices = cmds.polyUVSet(n, query=True, allUVSetsIndices=True)
            baseUVName = cmds.getAttr(n + ".uvSet[0].uvSetName")
            if self.verbose: print ("Base UV Name: " + baseUVName)
            return baseUVName
        return ""

    def GetUniqueName(self, wantedName):
        if cmds.objExists(wantedName):
            for num in range(1000):    
                newName = wantedName + str(num)
                if not cmds.objExists(newName):
                    return newName
            return (wantedName + "xxx999")
        else:
            return wantedName

    # Merges the decals with the base mesh and cleans up the mess.
    def MergeBaseAndDecal(self, nodes):
        newName = self.GetUniqueName(nodes[0])
        nodeList = cmds.polyUnite(nodes[1], nodes[0], op=True, muv=1, n=newName)
        if self.verbose: print ("NodeList: " + str(nodeList))
        if self.verbose: print ("Deleting history on " + nodeList[0])
        cmds.delete(nodeList[0], constructionHistory=True) # Delete the history
    
        # Sometimes empty nodes remain. Delete them if they have.
        for n in nodes:
            if cmds.objExists(n):
                if self.verbose: print ("Deleting empty node " + n)
                cmds.delete(n) # Delete the empty nodes now that they're no longer used
        
        if self.verbose: print ("Renaming " + newName + " back to " + nodes[0])    
        cmds.rename(newName, nodes[0]) # Rename the base object back to its original name now that the unused nodes are gone.
        return True

    # Takes what is the current base uv and which one is wanted as the base UV and swaps them.
    def ForceBaseUV(self, node, baseUVName):
        if baseUVName is "": return False
    
        indices = cmds.polyUVSet(node, query=True, allUVSetsIndices=True)
        currentBaseUV = cmds.getAttr(node + ".uvSet[0].uvSetName")
        cmds.polyUVSet(node, reorder=True, uvSet=baseUVName, nuv=currentBaseUV)   
        return True
    
    def ApplyMaterials(self, nodes):
        shd = cmds.shadingNode('lambert', name="Mat_Decal", asShader=True)

        for node in nodes:
            if cmds.objExists(node):
                shdSG = cmds.sets(name='%s%sSG' % (shd, node), empty=True, renderable=True, noSurfaceShader=True)
                cmds.connectAttr('%s.outColor' % shd, '%s.surfaceShader' % shdSG)
                cmds.sets(node, e=True, forceElement=shdSG)

    # Applies materials to the two meshes now that they've been split into two separate objects.
    def ReapplyMaterials(self, *args):
        sceneMaterials = cmds.ls(materials=True)
        print(sceneMaterials)
        print("TODO: Store the material name in the Extra Attributes")
        print("TODO: Look for the material name, if it's not found create it")
        print("TODO: Assign the color and map nodes to the material")
    
        return False
        
    # Names the UV Set on a node to the specified name
    def NameUVSet(self, node, setName):
        cmds.select(node)
        cmds.polyUVSet(rename=True, newUVSet=setName )
        return True

    def DeleteVertsWithAlpha(self, node, alphaValue):
        cmds.select(node)
        print ("")
        cmds.ConvertSelectionToVertices()
        result = cmds.polyColorPerVertex( query=True, a=True )
        
        # Loop through all of the vertices based on their vertex colour alpha
        for i, v in enumerate(result):
            if v == alphaValue:
                cmds.select("{0}.vtx[{1}]".format(node, i), d=True)
        cmds.ConvertSelectionToFaces()
        cmds.delete()
                
    def testVertexColors(self, *args):
        return True
    
    def GetMaterialFilename(self, node):
        result = []
        shapes = cmds.ls(node, o=True, dag=True, s=True)
        shadingEngines = cmds.listConnections(shapes, type="shadingEngine")
        materials = cmds.ls(cmds.listConnections(shadingEngines), materials=True)
        
        result.append(materials[0])
        
        # Grab the color filename
        colorFileNode = cmds.listConnections('%s.color' % (materials[0]), type='file')
        colorFile = None
        if colorFileNode != None:
            colorFile = cmds.getAttr(colorFileNode[0] + '.fileTextureName')
        
        result.append("color")
        result.append(colorFile)
        
        # Grab any bumpmap
        bump = cmds.listConnections('%s' % materials[0], type='bump2d')
        if bump != None:
            for x in bump:
                # value = cmds.getAttr(x + '.bumpValue')
                bumpTextureFileNode = cmds.listConnections(x, type = 'file')
                bumpTexture = cmds.getAttr(bumpTextureFileNode[0] + '.fileTextureName')
                result.append(materials[0]) # Duplicate this so the code doesn't get confused.
                result.append("bump")
                result.append(bumpTexture)
            
        # grab all texture filenames    
        #for x in textures:
        #    print cmds.getAttr(x + '.fileTextureName')

        return result
    
    def SaveInfo(self, node, base, data):
        if self.verbose: print ("Saving info %s" % base)
        snFilename = "arch_" + base 
        lngFilename = "arch_" + base 
        d = iter(data)
        attributes = cmds.attributeInfo(node, all=True)
        for m, n, v in zip(d, d, d): # Blinn: blinn1, color, None
            mtl = snFilename + "Mtl"
            # mtlL = snFilename + "Material"
            mtlColor = mtl + "_" + n
            # mtlColorL = mtlL + n

            # If this material has been added previously, skip this value.
            if mtl not in attributes:
                cmds.addAttr(node, shortName=mtl, dataType="string")
                cmds.setAttr("{0}.{1}".format(node, mtl), m, type="string")
                attributes = cmds.attributeInfo(node, all=True)

            # If this colour/bump texture has been stored before, skip this value.
            if mtlColor not in attributes:
                cmds.addAttr(node, shortName=mtlColor, dataType="string")
                attributes = cmds.attributeInfo(node, all=True)
            cmds.setAttr("{0}.{1}".format(node, mtlColor), str(v), type="string")
        return ""
        
    def LoadInfo(self, node):
        print ("Loading the info from " + str(node))

        attributes = cmds.attributeInfo(node, all=True)
        archAttributes = [x for x in attributes if x.startswith("Arch_")]
        result = []
        for attrib in archAttributes:
            pieces = attrib.split("_")
            value = cmds.getAttr(node + "." + attrib)
            tmpResult = []
            tmpResult.append(pieces[1])
            tmpResult.append(pieces[2])
            tmpResult.append(value)
            result.append(tmpResult)
        return result
        
    def MergeDecalAndBase(self, *args):        
        sel = cmds.ls(os=True)
        last = len(sel)
        if last > 1:
            baseMatInfo = self.GetMaterialFilename(sel[0])
            decalMatInfo = self.GetMaterialFilename(sel[1])

            # Make sure that the UV sets are named properly before we start.
            self.NameUVSet(sel[0], "Base")
            self.NameUVSet(sel[1], "Decal")
            cmds.select(sel)
    
            baseUV = self.TransferUV(sel)
            self.VertPaintAlpha(sel[0], 0.0) # No alpha on the base
            self.VertPaintAlpha(sel[1], 1.0) # Full alpha on the decals
            self.ApplyMaterials(sel)
            self.MergeBaseAndDecal(sel)
            
            # Create a lightmap UV and force it to the front, so that it will
            # become the second set when base is bumped up.
            lightmapUV = 'LightmapUV'
            cmds.polyUVSet(create=True, uvSet=lightmapUV)
            cmds.polyAutoProjection( sel[0] + '.f[*]', uvSetName=lightmapUV )
            self.ForceBaseUV(sel[0], lightmapUV)
            
            self.ForceBaseUV(sel[0], baseUV)
            cmds.delete(sel[0], ch=True)
            #cmds.select(sel[0])
            self.SaveInfo(sel[0], "Base", baseMatInfo)
            self.SaveInfo(sel[0], "Decal", decalMatInfo)
        else:
            print ("Please select the base and decal meshes in that order and try again.")

    def SplitDecalAndBase(self, *args):
        sel = cmds.ls(os=True)
        if len(sel) == 1:

            node = cmds.ls(sl=True, o=True)[0]
            matInfo = self.LoadInfo(node)
            decalNode = cmds.duplicate(node, name="decal", rr=True)[0]
            self.DeleteVertsWithAlpha(node, 0.0)
            self.DeleteVertsWithAlpha(decalNode, 1.0)
            # Re-assign the materials. Look for two that already exist.
            self.ReapplyMaterials(matInfo)
        else:
            print ("Please select one mesh to extract the decals from.")
        return True
        
    print ("[Completed]")

#d = decals()
# d.testVertexColors()
#d.MergeDecalAndBase()
#d.SplitDecalAndBase()
################################# Use this for testing tomorrow
#d.ReapplyMaterials([['Base', 'color', 'D:/radiantart/Source/TechArt/Decal/BaseTexture01.tga'], ['Decal', 'color', 'None'], ['Decal', 'bump', 'D:/radiantart/Source/TechArt/Decal/MarcoStamp.tga']])