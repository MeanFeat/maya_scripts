import maya.OpenMaya as om
import maya.OpenMayaAnim as oma
import maya.OpenMayaMPx as ompx

kPluginCmdName = "averageVertexSkinWeight"

kIndexFlag = "-i"
kIndexLongFlag = "-index"
kValueFlag = "-v"
kValueLongFlag = "-value"


class AverageVertexSkinWeightCmd(ompx.MPxCommand):
    def __init__(self):
        ompx.MPxCommand.__init__(self)

        # parse by frags
        self.index = None
        self.pressure = None

        # skinCluster related
        self.fnSkin = None
        self.maintainMaxInfluences = True
        self.maxInfluences = 5

        # origMesh related
        # self.fnOrigMesh = None

        # for undo
        self.component = None
        self.infIndices = None
        self.dagPath = om.MDagPath()
        self.oldWeights = om.MDoubleArray()

    def isUndoable(self):
        return True

    def doIt(self, args):
        # get the skinCluster for the component
        # selected skinned geo
        selection = om.MSelectionList()
        om.MGlobal.getActiveSelectionList(selection)

        # get dag path for selection
        component = om.MObject()
        try:
            selection.getDagPath(0, self.dagPath, component)
            self.dagPath.extendToShape()
        except:
            return

        # get skincluster from shape
        itSkin = om.MItDependencyGraph(self.dagPath.node(),
                                       om.MFn.kSkinClusterFilter,
                                       om.MItDependencyGraph.kUpstream,
                                       om.MItDependencyGraph.kBreadthFirst,
                                       om.MItDependencyGraph.kPlugLevel)

        skcMObj = None
        while not itSkin.isDone():
            # current MObject in the iteration
            skcMObj = itSkin.currentItem()

            # here's our skinCluster node
            self.fnSkin = oma.MFnSkinCluster(skcMObj)

            # cast current MObj to MFnDependencyNode to get attribute value
            mFnDependSkinCluster = om.MFnDependencyNode(skcMObj)

            # get if maintain max influences is checked
            maintainMaxInfMPlug = mFnDependSkinCluster.findPlug('maintainMaxInfluences')
            self.maintainMaxInfluences = maintainMaxInfMPlug.asBool()

            # get number of max influences to maintain
            maxInfMPlug = mFnDependSkinCluster.findPlug('maxInfluences')
            self.maxInfluences = maxInfMPlug.asInt()

            # done, break out
            break

        # check for skinCluster
        if not self.fnSkin:
            om.MGlobal.displayError('Cannot find skinCluster node connected to component.')
            return

        # check if max influenc
        if self.maintainMaxInfluences == True and self.maxInfluences < 1:
            om.MGlobal.displayWarning('Maintain max influences is ON and Max influences is set to 0. No weight will be set.')
            return

        # # find tweak node
        # itMesh = om.MItDependencyGraph(skcMObj,
        # 	om.MFn.kMesh,
        # 	om.MItDependencyGraph.kUpstream,
        # 	om.MItDependencyGraph.kBreadthFirst,
        # 	om.MItDependencyGraph.kPlugLevel)

        # # iterate thru tweak connections looking for mesh
        # while not itMesh.isDone():
        # 	meshMObj = itMesh.currentItem()

        # 	# check if current item is an intermediate object
        # 	if om.MFnDagNode(meshMObj).isIntermediateObject() == True:
        # 		self.fnOrigMesh = om.MFnMesh(meshMObj)
        # 		break

        # 	itMesh.next()

        # # check for origMesh
        # if not self.fnOrigMesh:
        # 	om.MGlobal.displayError('Cannot find orig mesh of the deformation chain.')
        # 	return

        # parse flags
        argData = om.MArgDatabase(self.syntax(), args)
        # -index
        if argData.isFlagSet(kIndexFlag):
            self.index = argData.flagArgumentInt(kIndexFlag, 0)
        # -value
        if argData.isFlagSet(kValueFlag):
            self.pressure = argData.flagArgumentDouble(kValueFlag, 0)

        # do the actual work
        self.redoIt()

    def undoIt(self):
        # to undo just set the weight back to oldWeights
        self.fnSkin.setWeights(self.dagPath,
                               self.component,
                               self.infIndices,
                               self.oldWeights,
                               False)

    def redoIt(self):
        # get the vertex to operating on
        self.component = om.MFnSingleIndexedComponent().create(om.MFn.kMeshVertComponent)
        om.MFnSingleIndexedComponent(self.component).addElement(self.index)

        # get surrounding vertices
        surrWeights = om.MDoubleArray()  # storing weights of surrounding vertices
        msInf = om.MScriptUtil()  # script util for int pointer
        infCountPtr = msInf.asUintPtr()  # unsigned int pointer sotring number of influences on the vertex
        surrVtxArray = om.MIntArray()  # storing sorrounding vertex indices

        # create iterator
        mitVtx = om.MItMeshVertex(self.dagPath, self.component)
        mitVtx.getConnectedVertices(surrVtxArray)
        surrComponents = om.MFnSingleIndexedComponent().create(om.MFn.kMeshVertComponent)
        om.MFnSingleIndexedComponent(surrComponents).addElements(surrVtxArray)

        # read weight from single vertex, store to oldWeights
        self.fnSkin.getWeights(self.dagPath, self.component, self.oldWeights, infCountPtr)

        # read weight fromthe surrounding vertices, store to surrWeights
        self.fnSkin.getWeights(self.dagPath, surrComponents, surrWeights, infCountPtr)

        # number of influences affecting the operating vertex
        influenceCount = om.MScriptUtil.getUint(infCountPtr)

        # reset variable infIndices
        infIndices_util = om.MScriptUtil()
        infIndices_util.createFromList(range(0, influenceCount), influenceCount)
        infIndices_iPtr = infIndices_util.asIntPtr()
        self.infIndices = om.MIntArray(infIndices_iPtr, influenceCount)

        # calculate multiplier for each surrounding vertices base on distance
        # distances = []
        # dist_append = distances.append
        # mPt = om.MPoint
        # mSpaceKObj = om.MSpace.kObject
        # fnOrigMesh_getPoint = self.fnOrigMesh.getPoint

        # get operating vertex point position on the orig mesh
        # compPt = mPt()
        # cPt_distTo = compPt.distanceTo
        # fnOrigMesh_getPoint(self.index, compPt, mSpaceKObj)

        # loop over each surrounding vertices to get distance to the operating vertex
        # for sIndx in sorted(surrVtxArray):
        # sPoint = mPt()
        # fnOrigMesh_getPoint(sIndx, sPoint, mSpaceKObj)
        # dist = cPt_distTo(sPoint)
        # dist_append(dist)

        # average all the surrounding vertex weights, multiply with the brush value and blend it over the origWeight
        oldWeight = self.oldWeights

        values = []
        values_append = values.append

        # pre-calculate what we can before entering the loop
        surrVtxCount = surrVtxArray.length()
        pressure = self.pressure
        pressure_sqr = pressure * pressure
        pre_mult = (1.0 / surrVtxCount) * (1.0 - pressure)

        # normalize and invert the distances, make closer distance has more value than the further ones
        # mults = [(sum(distances)/d)*pressure_sqr for d in distances]

        # the main weight value calculation loop
        for i in range(0, influenceCount):
            v = oldWeight[i] * pre_mult
            for w in range(0, surrVtxCount):
                # v += surrWeights[i + (w*influenceCount)] * mults[w]
                v += surrWeights[i + (w * influenceCount)] * pressure_sqr
            values_append(v)

        # do maintain max influences if maintainMaxInfluences is checked on the skinCluster node
        if self.maintainMaxInfluences:
            # get indices of the top N values
            maxIndexs = sorted(range(influenceCount), key=lambda v: values[v], reverse=True)[:self.maxInfluences]
            maxVals = [0] * influenceCount
            for i in maxIndexs:
                maxVals[i] = values[i]
        else:  # else, just use the calculated list
            maxVals = values

        # normalize
        normList = [w / sum(maxVals) for w in maxVals]

        # cast python list to MDoubleArray
        # newWeights
        newWeight_util = om.MScriptUtil()
        newWeight_util.createFromList(normList, influenceCount)
        newWeight_dPtr = newWeight_util.asDoublePtr()
        newWeights = om.MDoubleArray(newWeight_dPtr, influenceCount)

        # set the final weights throught the skinCluster
        self.fnSkin.setWeights(self.dagPath,
                               self.component,
                               self.infIndices,
                               newWeights,
                               False,
                               self.oldWeights)


# Creator
def cmdCreator():
    # Create the command
    return ompx.asMPxPtr(AverageVertexSkinWeightCmd())


# Syntax creator
def syntaxCreator():
    syntax = om.MSyntax()
    syntax.addFlag(kIndexFlag, kIndexLongFlag, om.MSyntax.kLong)
    syntax.addFlag(kValueFlag, kValueLongFlag, om.MSyntax.kDouble)
    return syntax


# Initialize the script plug-in
def initializePlugin(mobject):
    mplugin = ompx.MFnPlugin(mobject, "Nuternativ", "1.0", "Any")
    try:
        mplugin.registerCommand(kPluginCmdName, cmdCreator, syntaxCreator)
    except:
        om.MGlobal.displayError('Failed to register command:  %s\n%s' % (kPluginCmdName, e))


# Uninitialize the script plug-in
def uninitializePlugin(mobject):
    mplugin = ompx.MFnPlugin(mobject)
    try:
        mplugin.deregisterCommand(kPluginCmdName)
    except:
        om.MGlobal.displayError('Failed to de-register command:  %s\n%s' % (kPluginCmdName, e))
