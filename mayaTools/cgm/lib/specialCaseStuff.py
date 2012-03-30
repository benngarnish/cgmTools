#=================================================================================================================================================
#=================================================================================================================================================
#	rigging - a part of cgmTools
#=================================================================================================================================================
#=================================================================================================================================================
#
# DESCRIPTION:
#	Series of tools for the widgety magic of rigging
#
# REQUIRES:
# 	Maya
#   distance
#
# AUTHOR:
# 	Josh Burton (under the supervision of python guru (and good friend) David Bokser) - jjburton@gmail.com
#	http://www.cgmonks.com
# 	Copyright 2011 CG Monks - All Rights Reserved.
#
# CHANGELOG:
#	0.1 - 02/09/2011 - added documenation
#
# FUNCTION KEY:
#   1) locMe - creates locators at the pivots of every object selected - matching translation, rotation and rotation order
#   2) locMeObject (obj) - return name of locator created
#   3) setRotationOrderObj (obj, ro)
#   4) doSetLockHideKeyableAttr (obj,lock,visible,keyable,channels) - Pass an oject, True/False for locking it,
#       True/False for visible in channel box, and which channels you want locked in ('tx','ty',etc) form
#   5) groupMe() - Pass selection into it and return locators placed at the pivots of each object - matching translation, rotation and rotation order
#   6) groupMeObject(obj) - Pass object into it and return locators placed at the pivots of each object - matching translation, rotation and rotation order
#
# 3/4/2011 - added point, orient, parent snap functions as well as the list to heirarchy one
#=================================================================================================================================================
import maya.cmds as mc
import maya.mel as mel

from cgm.lib import guiFactory
from cgm.lib import distance
from cgm.lib import attributes
from cgm.lib import autoname
from cgm.lib import constraints
from cgm.lib import rigging


# Maya version check
mayaVersion = int( mel.eval( 'getApplicationVersionAsFloat' ) )

#>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
# Special case tools
#>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def plasticConstraintsAndScaleFromObjectToTransform():
    selection = mc.ls(sl=True, flatten=True)
    for obj in selection:
	#Make a transform
	group = rigging.groupMeObject(obj,maintainParent = True)

	#Get scale connections
	objScaleConnections = []
	for s in 'sx','sy','sz':
	    buffer =  attributes.returnDriverAttribute(obj+'.'+s)
	    attributes.breakConnection(obj+'.'+s)
	    attributes.doConnectAttr(buffer,(group+'.'+s))

	# Get constraint info from obj
	objConstraints = constraints.returnObjectConstraints(obj)

	for const in objConstraints:
	    constraintTargets = constraints.returnConstraintTargets(const)
	    mc.delete(const)

	    mc.parentConstraint(constraintTargets,group, maintainOffset = True)
	    



def troubleShootingClientPathStuff():
    import inspect
    import os
    import sys
    import maya
    maya.mel.eval( 'getenv PYTHONPATH' )
    maya.mel.eval( 'getenv MAYA_MODULE_PATH' )
    maya.mel.eval( 'getenv MAYA_SCRIPT_PATH' )
    maya.mel.eval( 'getenv SYS' )



def doConnectScaleToCGMTagOnObject(objectList, cgmTag, storageObject):
    attributeList = []

    for obj in objectList:
	userAttrsData = attributes.returnUserAttrsToDict(obj)
	success = False
	for key in userAttrsData.keys():
	    if key == cgmTag:
		success = True
		buffer = attributes.addFloatAttributeToObject (storageObject, userAttrsData.get(key), dv = 1 )

	if success:
	    attributes.doConnectAttr(buffer,(obj+'.scaleX'))
	    attributes.doConnectAttr(buffer,(obj+'.scaleY'))
	    attributes.doConnectAttr(buffer,(obj+'.scaleZ'))

	attributeList.append(buffer)



def attachQSSSkinJointsToRigJoints (qssSkinJoints,qssRigJoints):
    """
    >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    DESCRIPTION:
    Created for N project. It will constrain one skeleton to the other
    by looking for the closest joint in a qss set of bind joints

    REQUIRES:
    qssSet(set) - must exist in scene. Set of the rig joints
    rigStartJoint - the first joint of a unifed  deformation skeleton

    RETURNS:
    Nothing
    >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    """
    mc.select(cl=True)
    mc.select(qssSkinJoints)
    skinnedHeirarchy = mc.ls(sl=True)
    mc.select(cl=True)
    mc.select(qssRigJoints)
    rigHeirarchy = mc.ls(sl=True)
    constraintsList = []
    for obj in rigHeirarchy:
	print ('On '+obj)
	attachJoint = distance.returnClosestObject(obj,skinnedHeirarchy)
	pntConstBuffer = mc.pointConstraint(obj,attachJoint,maintainOffset=True,weight=1)
	orConstBuffer = mc.orientConstraint(obj,attachJoint,maintainOffset=True,weight=1)
	pntConst = mc.rename(pntConstBuffer,(obj+('_pntConst')))
	orConst = mc.rename(orConstBuffer,(obj+('_orConst')))
	constraintsList.append(pntConst)
	constraintsList.append(orConst)
    #make our attribute Holder object
    """ need to make our master scale connector"""
    dataHolderGrp= ('rigJointsConstraintHolder_grp')
    if mc.objExists (dataHolderGrp):
	pass
    else:
	mc.group (n= dataHolderGrp, w=True, empty=True)
    #stores the constraints
    attributes.storeObjListNameToMessage (constraintsList, dataHolderGrp)
#>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>