#=================================================================================================================================================
#=================================================================================================================================================
#	bufferToolsLib - a part of cgmTools
#=================================================================================================================================================
#=================================================================================================================================================
#
# DESCRIPTION:
#   Library of functions for the cgmRiggingTools tool
#
# ARGUMENTS:
#   Maya
#
#
# AUTHOR:
# 	Josh Burton (under the supervision of python guru (and good friend) David Bokser) - jjburton@gmail.com
#	http://www.cgmonks.com
# 	Copyright 2011 CG Monks - All Rights Reserved.
#
# CHANGELOG:
#	0.1.12072011 - First version
#	0.1.12132011 - master control maker implemented, snap move tools added
#	0.1.12272011 - split out library from tool
#
#=================================================================================================================================================
__version__ = '0.1.12032011'

import maya.cmds as mc
import maya.mel as mel
import subprocess

from cgm.lib.cgmBaseMelUI import *
from cgm.lib.classes.SetFactory import *
from cgm.lib.classes.OptionVarFactory import *
from cgm.lib.classes.ObjectFactory import *
from cgm.lib.classes import NameFactory

from cgm.lib import (search,guiFactory,lists)
reload(search)
reload(guiFactory)

"""

"""
def printReport(self):
    guiFactory.doPrintReportStart()
    print self.refSetsDict
    print "# Object Sets found: "
    for o in self.objectSetsRaw:
        print "#    '%s'"%o
    
    print "# Loaded Sets: "  
    for o in self.objectSets:
        print "#    '%s'"%o  
        
    if self.ActiveObjectSetsOptionVar.value:
        print "# Active Sets: "
        for o in self.ActiveObjectSetsOptionVar.value:
            if o:
                print "#    '%s'"%o 
    if self.refSetsDict:
        print "# Refs and sets: "
        for o in self.refSetsDict.keys():
            print "#     '%s':'%s'"%(o,"','".join(self.refSetsDict.get(o)))            
    
    print "# Active Refs: "
    if self.ActiveRefsOptionVar.value:   
        for o in self.ActiveRefsOptionVar.value:
            if o:
                print "#    '%s'"%o
    else:
        print "#    None"
        
        
                
    print "# Active Types: "
    if self.ActiveTypesOptionVar.value:    
        for o in self.ActiveTypesOptionVar.value:
            if o:
                print "#    '%s'"%o 
    else:
        print "#    None"
                
    guiFactory.doPrintReportEnd()


def updateObjectSets(self):
    self.objectSetsRaw = search.returnObjectSets()
    self.refPrefixes = []
    self.refSetsDict = {'From Scene':[]}
    self.setTypesDict = {}
    for t in self.setTypes:
        self.setTypesDict[t] = []
    self.sortedSets = []
    self.objectSets = []
    self.setGroupName = False
    self.setGroups = []
    
    if self.objectSetsRaw:
        for o in self.objectSetsRaw:
            sInstance = SetFactory(o)
            
            # Get our reference prefixes and sets sorted out
            if sInstance.refState:
                if sInstance.refPrefix in self.refSetsDict.keys():
                    self.refSetsDict[sInstance.refPrefix].append(o)
                else:
                    self.refSetsDict[sInstance.refPrefix] = [o]
            else:
                self.refSetsDict['From Scene'].append(o)
                # See if we have a scene set group and if so, initialize
                if sInstance.setType == 'objectSetGroup':
                    self.setsGroup = SetFactory(o)
                    self.setGroupName = self.setsGroup.nameShort
                    self.setGroups.append(self.setsGroup.nameShort)
                
            # Get our type tags, if none assign 'NONE'
            if sInstance.setType:
                if sInstance.setType in self.setTypesDict.keys():
                    self.setTypesDict[sInstance.setType].append(o)
                else:
                    self.setTypesDict['NONE'].append(o)     
            else:
                self.setTypesDict['NONE'].append(o)

        print self.setTypesDict
        
        if self.refSetsDict.keys():
            self.refPrefixes.extend( self.refSetsDict.keys() )
        
        
        self.sortedSets = []
        
        #Sort for activeRefs
        tmpActiveRefSets = []
        if self.refSetsDict.keys() and self.ActiveRefsOptionVar.value:
            for r in self.refSetsDict.keys():
                #If value, let's add or subtract based on if our set refs are found
                if r in self.ActiveRefsOptionVar.value and self.refSetsDict.get(r):
                    tmpActiveRefSets.extend(self.refSetsDict.get(r))
                      
                    
        #Sort for active types  
        tmpActiveTypeSets = []
        if self.setTypesDict.keys() and self.ActiveTypesOptionVar.value:
            for t in self.setTypesDict.keys():
                if t in self.ActiveTypesOptionVar.value and self.setTypesDict.get(t):
                    tmpActiveTypeSets.extend(self.setTypesDict.get(t))
        
        if tmpActiveTypeSets and tmpActiveRefSets:
            self.sortedSets = lists.returnMatchList(tmpActiveTypeSets,tmpActiveRefSets)
        elif tmpActiveTypeSets:
            self.sortedSets = tmpActiveTypeSets
        else:
            self.sortedSets = tmpActiveRefSets
                   
    if self.sortedSets:
        self.objectSets = self.sortedSets
    else:
        self.objectSets = self.objectSetsRaw
        

    # Set Group creation if they don't have em
    if mc.optionVar( q='cgmVar_MaintainLocalSetGroup' ) and not self.setGroupName:
        initializeSetGroup(self)
        
    if mc.optionVar( q='cgmVar_MaintainLocalSetGroup' ):
        doGroupLocal(self)
            
    # Hide Set groups
    if mc.optionVar( q='cgmVar_HideSetGroups' ):
        for s in self.setGroups:
            if s in self.objectSets:
                self.objectSets.remove(s)
        
    #Get our sets ref info
    print ("Prefixes are: '%s'"%self.refPrefixes)
        
    
#>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
# Individual Set Stuff
#>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def doSelectSetObjects(self,nameIndex):
    setName = self.objectSetsDict.get(nameIndex)
    if mc.objExists(setName):
        s = SetFactory(setName)
        s.select()
    else:
        guiFactory.warning("'%s' doesn't exist.Reloading Gui"%setName)
        self.reset()
        

def doAddSelected(self,nameIndex):
    setName = self.objectSetsDict.get(nameIndex)
    if mc.objExists(setName):
        s = SetFactory(setName)
        s.doStoreSelected()
    else:
        guiFactory.warning("'%s' doesn't exist.Reloading Gui"%setName)
        self.reset()


def doRemoveSelected(self,nameIndex):
    setName = self.objectSetsDict.get(nameIndex)
    if mc.objExists(setName):
        s = SetFactory(setName)
        s.doRemoveSelected()
    else:
        guiFactory.warning("'%s' doesn't exist.Reloading Gui"%setName)
        self.reset()
        

def doKeySet(self,nameIndex):
    setName = self.objectSetsDict.get(nameIndex)
    if mc.objExists(setName):
        s = SetFactory(setName)
        s.key()
    else:
        guiFactory.warning("'%s' doesn't exist.Reloading Gui"%setName)
        self.reset()
    
    
def doDeleteCurrentSetKey(self,nameIndex):
    setName = self.objectSetsDict.get(nameIndex)
    if mc.objExists(setName):
        s = SetFactory(setName)
        s.deleteCurrentKey()
    else:
        guiFactory.warning("'%s' doesn't exist.Reloading Gui"%setName)
        self.reset()
    

def doPurgeSet(self,nameIndex):
    setName = self.objectSetsDict.get(nameIndex)
    if mc.objExists(setName):
        s = SetFactory(setName)
        s.purge()
    else:
        guiFactory.warning("'%s' doesn't exist.Reloading Gui"%setName)
        self.reset()

def doCreateSet(self):
    b = SetFactory('Set')
    b.doStoreSelected()
    self.reset()
    
def doDeleteSet(self,nameIndex):
    setName = self.objectSetsDict.get(nameIndex) 
    if mc.objExists(setName):
        mc.delete(setName)
        self.reset()
    else:
        guiFactory.warning("'%s' doesn't exist.Reloading Gui"%setName)
        self.reset()
    
def doCopySet(self,nameIndex):
    setName = self.objectSetsDict.get(nameIndex) 
    if mc.objExists(setName):
        s = SetFactory(self.objectSetsDict.get(nameIndex))
        s.copy()
        self.reset()
    else:
        guiFactory.warning("'%s' doesn't exist.Reloading Gui"%setName)
        self.reset()
    
def doToggleQssState(self,nameIndex):
    setName = self.objectSetsDict.get(nameIndex)
    if mc.objExists(setName):
        s = SetFactory(setName)
        s.isQss(not s.qssState)
    else:
        guiFactory.warning("'%s' doesn't exist.Reloading Gui"%setName)
        self.reset()

def doSetType(self,setName,typeName):
    if mc.objExists(setName):
        s = SetFactory(setName)
        if typeName == 'NONE':
            s.doSetType()            
        else:
            s.doSetType(typeName)
    else:
        guiFactory.warning("'%s' doesn't exist.Reloading Gui"%setName)
        self.reset()
        
    
def doUpdateSetName(self,setTextField,nameIndex):
    # get the field
    setName = self.objectSetsDict.get(nameIndex)
    print ">>>>>>>>>>>>>>"
    print setName
    if not mc.objExists(setName):
        guiFactory.warning("'%s' doesn't exist.Reloading Gui"%setName)
        self.reset()
        return

    newName = mc.textField(setTextField,q=True,text = True)

    if setName and newName:
        #Name it
        attributes.storeInfo(setName,'cgmName',newName)
        buffer = NameFactory.doNameObject(setName)
        #Update...field
        mc.textField(setTextField,e = True,text = buffer)
        #...dict...
        self.objectSetsDict[nameIndex] = buffer
        #...optionVar...
        
        tmp = OptionVarFactory('cgmVar_activeObjectSets','string')
        if setName in tmp.value:
            guiFactory.report("Set was an active set. Setting new name '%s' as active"%buffer)
            tmp.remove(setName)
            tmp.append(buffer) 
        

    else:
        guiFactory.warning("There's a problem with the name input.")
        
#>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
# Gui stuff
#>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def doSetSetAsActive(self,nameIndex):
    setName = self.objectSetsDict.get(nameIndex)
    if mc.objExists(setName):
        if '' in self.ActiveObjectSetsOptionVar.value:
            self.ActiveObjectSetsOptionVar.remove('')
        self.ActiveObjectSetsOptionVar.append(setName) 
    else:
        guiFactory.warning("'%s' doesn't exist.Reloading Gui"%setName)
        self.reset()

def doSetSetAsInactive(self,nameIndex):
    setName = self.objectSetsDict.get(nameIndex)
    if mc.objExists(setName): 
        self.ActiveObjectSetsOptionVar.remove(setName) 
            
    else:
        guiFactory.warning("'%s' doesn't exist.Reloading Gui"%setName)
        self.reset()

def doSetRefState(self,refIndex,value,reset = True):
    refName = self.refPrefixDict.get(refIndex)
    if refName in self.refPrefixes:
        if value:
            self.ActiveRefsOptionVar.append(refName)
        else:
            self.ActiveRefsOptionVar.remove(refName)
        if reset:
            self.reset()
    else:
        guiFactory.warning("'%s' doesn't exist.Reloading Gui"%refName)
        self.reset()
        
def doSetTypeState(self,typeIndex,value,reset = True):
    typeName = self.typeDict.get(typeIndex)
    if typeName in self.setTypes:
        if value:
            self.ActiveTypesOptionVar.append(typeName)
        else:
            self.ActiveTypesOptionVar.remove(typeName)
        if reset:
            self.reset()
    else:
        guiFactory.warning("'%s' doesn't exist.Reloading Gui"%typeName)
        self.reset()
        
def guiDoSetType(self,nameIndex,typeName):
    """ Function for the gui call, root function is above """
    setName = self.objectSetsDict.get(nameIndex)
    doSetType(self,setName,typeName)
    self.reset()
    
#>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
# Set Group Stuff
#>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>  
def initializeSetGroup(self):
    # Set Group creation if they don't have em
    if not self.setGroupName:
        self.setsGroup = SetFactory('Scene','objectSetGroup')
        self.setGroupName = self.setsGroup.nameShort
        if not mc.optionVar( q='cgmVar_HideSetGroups' ):
            self.objectSets.append(self.setsGroup.nameShort)    

def doSetMaintainLocalSetGroup(self):
    optionVar = OptionVarFactory('cgmVar_MaintainLocalSetGroup')
    optionVar.toggle()
    if optionVar.value:
        if not self.setGroupName:
            initializeSetGroup(self)
        buffer = self.refSetsDict.get('From Scene')
        for s in buffer:
            sInstance = SetFactory(s)
            if not sInstance.parents:
                self.setsGroup.store(s)
        
        self.reset()
        
def doSetHideSetGroups(self):
    optionVar = OptionVarFactory('cgmVar_HideSetGroups')
    optionVar.toggle()
    self.reset()
    
def doGroupLocal(self):
    if not self.setGroupName:
        initializeSetGroup(self)
    buffer = self.refSetsDict.get('From Scene')
    for s in buffer:
        sInstance = SetFactory(s)
        if not sInstance.parents:
            self.setsGroup.store(s)
    
        
#>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
# Multi Set Stuff
#>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> 
def doMultiSetType(self,typeName):
    if self.setMode:
        if self.ActiveObjectSetsOptionVar.value:
            for s in self.ActiveObjectSetsOptionVar.value:
                if s in self.objectSets and s in self.refSetsDict.get('From Scene'):
                    doSetType(self,s,typeName)
            self.reset()
            
        else:
            guiFactory.warning("No active sets found")
            return
            
    else:
        for s in self.objectSets:
            if s in self.refSetsDict.get('From Scene'):
                doSetType(self,s,typeName)      
        self.reset()
                
            

def doSetAllSetsAsActive(self):
    if self.activeSetsCBDict:
        for i,s in enumerate(self.activeSetsCBDict.keys()):
            if self.objectSetsDict.get(i) in self.objectSets:
                tmp = self.activeSetsCBDict.get(s)          
                mc.checkBox(tmp, edit = True,
                            value = True)
                doSetSetAsActive(self,i)

def doSetAllSetsAsInactive(self):
    if self.activeSetsCBDict:
        for i,s in enumerate(self.activeSetsCBDict.keys()):
            if self.objectSetsDict.get(i) in self.objectSets:
                tmp = self.activeSetsCBDict.get(s)                        
                mc.checkBox(tmp, edit = True,
                            value = False)
                doSetSetAsInactive(self,i)

def doSelectMultiSets(self):
    allObjectsList = []            
    if self.setMode:
        if self.ActiveObjectSetsOptionVar.value:
            for o in self.ActiveObjectSetsOptionVar.value:
                if o in self.objectSets:
                    s = SetFactory(o)
                    allObjectsList.extend(s.setList)     
        else:
            guiFactory.warning("No active sets found")
            return
            
    else:
        for s in self.objectSets:
            sInstance = SetFactory(s)
            allObjectsList.extend(sInstance.setList) 

    if allObjectsList:
        mc.select(allObjectsList)
            
def doKeyMultiSets(self):
    allObjectsList = []   
    
    if self.setMode:
        if self.ActiveObjectSetsOptionVar.value:    
            for o in self.ActiveObjectSetsOptionVar.value:
                if o in self.objectSets:
                    s = SetFactory(o)
                    s.key()
                    allObjectsList.extend(s.setList)                 
        else:
            guiFactory.warning("No active sets found")
            return  
    else:
        for s in self.objectSets:
            sInstance = SetFactory(s)
            sInstance.key()
            allObjectsList.extend(sInstance.setList)             

    if allObjectsList:
        mc.select(allObjectsList)
    
def doDeleteMultiCurrentKeys(self):
    allObjectsList = []      
    
    if self.setMode:
        if self.ActiveObjectSetsOptionVar.value:    
            for o in self.ActiveObjectSetsOptionVar.value:
                if o in self.objectSets:
                    s = SetFactory(o)
                    s.deleteCurrentKey()
                    allObjectsList.extend(s.setList)                
        else:
            guiFactory.warning("No active sets found")
            return  
    else:
        for s in self.objectSets:
            sInstance = SetFactory(s)
            sInstance.deleteCurrentKey()
            allObjectsList.extend(sInstance.setList) 
            
    if allObjectsList:
        mc.select(allObjectsList)    
            
def doSetAllRefState(self,value):
    if self.activeRefsCBDict:
        for i in self.activeRefsCBDict.keys():
            tmp = self.activeRefsCBDict.get(i)
            mc.menuItem(tmp,edit = True,cb=value)
            doSetRefState(self,i,value,False)
        self.reset()
        
def doSetAllTypeState(self,value):
    if self.activeTypesCBDict:
        for i in self.activeTypesCBDict.keys():
            tmp = self.activeTypesCBDict.get(i)
            mc.menuItem(tmp,edit = True,cb=value)
            doSetTypeState(self,i,value,False)
        self.reset()
        
            
