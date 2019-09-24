import maya.cmds as mc
import os

def BakeAndPrep():
    bakeSetName = "bakeSet"
    deleteSetName = "deleteSet"
    exportSetName = "exportSet"
    
    if(mc.optionVar(exists='cgm_bake_set')):
        bakeSetName = mc.optionVar(q='cgm_bake_set')
    if(mc.optionVar(exists='cgm_delete_set')):
        deleteSetName = mc.optionVar(q='cgm_delete_set')
    if(mc.optionVar(exists='cgm_export_set')):
        exportSetName = mc.optionVar(q='cgm_export_set')
    
    # Bake Animation For Export
    
    try:
        topNode = mc.ls(sl=True)[0]
    except:
        print "Select top node and try again."
        return
    
    currentTime = mc.currentTime(q=True)
    
    topNodeSN = topNode.split(':')[-1]
    
    # save
    loc = mc.file(q=True, loc=True)
    base, ext = os.path.splitext(loc)
    bakedLoc = "%s_baked%s" % (base, ext)

    mc.file(rn=bakedLoc)

    # gather data
    
    namespaces = topNode.split(':')[:-1]

    if len(namespaces) > 0:
        ns = ':'.join( topNode.split(':')[:-1] ) + ':'
    else:
        ns = "%s_" % topNode.split('|')[-1]

    # set tangent options to spline
    currentTangent = mc.keyTangent( q=True, g=True, ott=True )[0]
    mc.keyTangent( g=True, ott="spline" )
    
    # bake
    bakeSet = "%s%s" % (ns, bakeSetName)
    if(mc.objExists(bakeSet)):
        mc.bakeResults( mc.sets( bakeSet, q=True ), 
                        simulation=True, 
                        t=( mc.playbackOptions(q=True, min=True), mc.playbackOptions(q=True, max=True) ), 
                        sampleBy=1, 
                        disableImplicitControl=True,
                        preserveOutsideKeys = False, 
                        sparseAnimCurveBake = False,
                        removeBakedAttributeFromLayer = False, 
                        removeBakedAnimFromLayer = True, 
                        bakeOnOverrideLayer = False, 
                        minimizeRotation = True, 
                        controlPoints = False, 
                        shape = False )

        mc.setInfinity(mc.sets( bakeSet, q=True ), pri='constant', poi='constant')
    else:
        print "No bake set found."

    mc.keyTangent( g=True, ott=currentTangent )
    
    # import reference
    if( mc.referenceQuery(topNode, isNodeReferenced=True) ):
        refFile = mc.referenceQuery( topNode ,filename=True )
        topRefNode = mc.referenceQuery( topNode, referenceNode=True, topReference=True)
        topRefFile = mc.referenceQuery(topRefNode, filename=True)

        while refFile != topRefFile:
            mc.file(topRefFile, ir=True)
            topRefNode = mc.referenceQuery( topNode, referenceNode=True, topReference=True)
            topRefFile = mc.referenceQuery(topRefNode, filename=True)

        mc.file(topRefFile, ir=True)

    if len(namespaces) > 0:
        for space in namespaces[:-1]:
            mc.namespace( removeNamespace = space, mergeNamespaceWithRoot = True)

        ns = '%s:' % namespaces[-1]
    else:
        ns = "%s_" % topNode

    # delete garbage
    deleteSet = "%s%s" % (ns, deleteSetName)
    if(mc.objExists(deleteSet)):
        mc.delete( mc.sets( deleteSet, q=True ) )  
    else:
        print "No delete set found."  

    # export
    newTopNode = '%s%s' % (ns, topNodeSN)
    if not mc.objExists(newTopNode):
        if mc.objExists(topNode):
            newTopNode = topNode
    
    # revert to old name
    #for i, tempObj in enumerate(namespaceTransforms):
    #    tempObj.name = origNames[i]

    # revert to previous settings
    mc.currentTime(currentTime)

    exportSet = "%s%s" % (ns, exportSetName)
    if(mc.objExists(exportSet)):
        mc.select( mc.sets( exportSet, q=True ) ) 
    else:
        print "No export set found. Selecting top node."
        mc.select( topNode )

    mc.refresh()