#=================================================================================================================================================
#=================================================================================================================================================
#	RigFactory - a part of cgmTools
#=================================================================================================================================================
#=================================================================================================================================================
#
# DESCRIPTION:
#	Series of tools for finding stuff
#
# AUTHOR:
# 	Josh Burton (under the supervision of python guru (and good friend) David Bokser) - jjburton@gmail.com
#	http://www.cgmonks.com
# 	Copyright 2012 CG Monks - All Rights Reserved.
#
#=================================================================================================================================================
import maya.cmds as mc
from cgm.lib.classes import NameFactory
from cgm.lib.classes.AttrFactory import *
from cgm.lib.classes.BufferFactory import *
from cgm.lib.classes.ObjectFactory import *

from cgm.rigger.lib.Limb import module
reload(module)
from cgm.rigger import ModuleFactory
reload(ModuleFactory)

from cgm.rigger.ModuleFactory import *
from cgm.rigger.lib.Limb import *


import random
import re
import copy

from cgm.lib import (search,
                     distance,
                     names,
                     logic,
                     attributes,
                     names,
                     rigging,
                     constraints,
                     curves,
                     dictionary,
                     settings,
                     lists,
                     modules,
                     position,
                     cgmMath,
                     controlBuilder)


reload(search)
reload(distance)
reload(names)
reload(attributes)
reload(names)
reload(rigging)
reload(constraints)
reload(curves)
reload(dictionary)
reload(settings)
reload(lists)
reload(modules)
reload(cgmMath)
reload(controlBuilder)
reload(logic)

typesDictionary = dictionary.initializeDictionary(settings.getTypesDictionaryFile())
namesDictionary = dictionary.initializeDictionary( settings.getNamesDictionaryFile())
settingsDictionary = dictionary.initializeDictionary( settings.getSettingsDictionaryFile())

axisDirectionsByString = ['x+','y+','z+','x-','y-','z-']
geoTypes = 'nurbsSurface','mesh','poly','subdiv'
CharacterTypes = 'Bio','Mech','Prop'

moduleTypeToFunctionDict = {'None':ModuleFactory,
                            'segment':Limb.module.Segment}

moduleTypeToMasterClassDict = {'None':['none','None',False],
                               'Limb':['segment']}

#Make our class bridge
#guiFactory.classBridge_Puppet()   

#These are our init variables
initLists = ['geo','modules','rootModules','orderedModules','orderedParentModules']
initDicts = ['templateSizeObjects','Module','moduleParents','moduleChildren']
initStores = ['PuppetNull','refState',]
 
class PuppetFactory():
    """ 
    Character
    
    """    
    def __init__(self,characterName = '',*a,**kw):
        """ 
        Intializes an optionVar class handler
        
        Keyword arguments:
        varName(string) -- name for the optionVar
        
        ObjectFactories:
        self.PuppetNull - main null
        self.NoTransformGroup        
        >>> self.GeoGroup - group where geo is stored to
        self.PuppetInfoNull - master puppet info null under which the other nulls live        
        >>> self.GeoInfoNull
        >>> self.ModuleInfoNull
        >>> self.ModulesGroup
        
        BufferFactories:
        self.ModulesBuffer - buffer for modules. Instanced from self.ModuleInfoNull
        
        """    
        #>>>Keyword args        
        characterType = kw.pop('characterType','')
        initializeOnly = kw.pop('initializeOnly',False)
        
        
        #Default to creation of a var as an int value of 0
        ### input check         
        self.masterNulls = modules.returnPuppetObjects()
        self.nameBase = characterName
        
        for l in initLists:
            self.__dict__[l] = []
        for d in initDicts:
            self.__dict__[d] = {}
        for o in initStores:
            self.__dict__[o] = False

        guiFactory.doPrintReportStart()
        
        if mc.objExists(characterName):
            #Make a name dict to check
            if search.findRawTagInfo(characterName,'cgmModuleType') == 'master':
                self.nameBase = characterName
                self.PuppetNull = ObjectFactory(characterName)
                self.refState = self.PuppetNull.refState
                guiFactory.report("'%s' exists. Checking..."%characterName)

            else:
                guiFactory.warning("'%s' isn't a puppet module. Can't initialize"%characterName)
                return
        else:
            if self.nameBase == '':
                randomOptions = ['ReallyNameMe','SolarSystem_isADumbName','David','Josh','Ryan','NameMe','Homer','Georgie','PleaseNameMe','NAMEThis','PleaseNameThisPuppet']
                buffer = random.choice(randomOptions)
                cnt = 0
                while mc.objExists(buffer) and cnt<10:
                    cnt +=1
                    buffer = random.choice(randomOptions)
                self.nameBase = buffer            
                       

        if self.refState or initializeOnly:
            guiFactory.report("'%s' Initializing..."%characterName)
            if not self.initialize():
                guiFactory.warning("'%s' failed to initialize. Please go back to the non referenced file to repair!"%moduleName)
                return     
            
        else:
            if not self.verify():
                guiFactory.warning("'%s' failed to verify!"%characterName)
                return         
        
        self.checkGeo()
        self.verifyTemplateSizeObject(False)
        self.getModules(initializeOnly=initializeOnly,*a,**kw)
        guiFactory.report("'%s' checks out"%self.nameBase)
        guiFactory.doPrintReportEnd()
                
    def verify(self):
        """ 
        Verifies the various components a masterNull for a character/asset. If a piece is missing it replaces it.
        
        RETURNS:
        success(bool)
        """            
        #Puppet null
        try:
            if not mc.objExists(self.nameBase):
                buffer = mc.group(empty=True)
                self.PuppetNull = ObjectFactory(buffer)
            else:
                self.PuppetNull = ObjectFactory(self.nameBase)
            
            self.PuppetNull.store('cgmName',self.nameBase,True)   
            self.PuppetNull.store('cgmType','ignore')
            self.PuppetNull.store('cgmModuleType','master')
                 
            if self.PuppetNull.nameShort != self.nameBase:
                self.PuppetNull.doName(False)
            
            attributes.doSetLockHideKeyableAttr(self.PuppetNull.nameShort,channels=['tx','ty','tz','rx','ry','rz','sx','sy','sz'])
        except:
            guiFactory.warning("Puppet null failed!")
            
        #Checks our modules container null
        created = False
        #Initialize message attr
        self.afModulesGroup = AttrFactory(self.PuppetNull,'modulesGroup','message')
        if not self.afModulesGroup.value:
            self.ModulesGroup = ObjectFactory(mc.group(empty=True))            
            self.afModulesGroup.doStore(self.ModulesGroup.nameShort)
            created = True
        else:
            self.ModulesGroup = ObjectFactory(self.afModulesGroup.value)
            
        self.ModulesGroup.store('cgmName','modules')   
        self.ModulesGroup.store('cgmType','group')
        
        self.ModulesGroup.doParent(self.PuppetNull.nameShort)
        
        if created:
            self.ModulesGroup.doName(False)
            
        self.afModulesGroup.updateData()   
            
        attributes.doSetLockHideKeyableAttr(self.ModulesGroup.nameShort)

            
        #Checks our noTransform container null
        created = False        
        self.afNoTransformGroup = AttrFactory(self.PuppetNull,'noTransformGroup','message')
        if not self.afNoTransformGroup.value:
            self.NoTransformGroup = ObjectFactory(mc.group(empty=True))
            self.afNoTransformGroup.doStore(self.NoTransformGroup.nameShort)
            created = True
        else:
            self.NoTransformGroup = ObjectFactory(self.afNoTransformGroup.value)
            
        self.NoTransformGroup.store('cgmName','noTransform')   
        self.NoTransformGroup.store('cgmType','group')
        
        self.NoTransformGroup.doParent(self.PuppetNull.nameShort)
        
        if created:
            self.NoTransformGroup.doName(False)
            
        self.afNoTransformGroup.updateData()   
            
        attributes.doSetLockHideKeyableAttr(self.NoTransformGroup.nameShort)
         
            
        #Checks our geo container null
        created = False        
        self.afGeoGroup = AttrFactory(self.PuppetNull,'geoGroup','message')
        if not self.afGeoGroup.value:
            self.GeoGroup = ObjectFactory(mc.group(empty=True))
            self.afGeoGroup.doStore(self.GeoGroup.nameShort)            
            created = True
        else:
            self.GeoGroup = ObjectFactory(self.afGeoGroup.value)
            
        self.GeoGroup.store('cgmName','geo')   
        self.GeoGroup.store('cgmType','group')
        
        self.GeoGroup.doParent(self.afNoTransformGroup.value)
        
        if created:
            self.GeoGroup.doName(False)
            
        self.afGeoGroup.updateData()   
            
        attributes.doSetLockHideKeyableAttr(self.GeoGroup.nameShort)
        
            
        #Checks master info null
        created = False        
        self.afPuppetInfo = AttrFactory(self.PuppetNull,'info','message')
        if not self.afPuppetInfo.value:
            self.PuppetInfoNull = ObjectFactory(mc.group(empty=True))
            self.afPuppetInfo.doStore(self.PuppetInfoNull.nameShort)               
            created = True
        else:
            self.PuppetInfoNull = ObjectFactory(self.afPuppetInfo.value)
            
            
        self.PuppetInfoNull.store('cgmName','master')   
        self.PuppetInfoNull.store('cgmType','info')
        
        self.PuppetInfoNull.doParent(self.PuppetNull.nameShort)
        
        if created:
            self.PuppetInfoNull.doName(False)
            
        self.afPuppetInfo.updateData()   
            
        attributes.doSetLockHideKeyableAttr(self.PuppetInfoNull.nameShort)
        
            
        #Checks modules info null
        created = False        
        self.afModuleInfo = AttrFactory(self.afPuppetInfo.value,'modules','message')
        if not self.afModuleInfo.value:
            self.ModuleInfoNull = ObjectFactory(mc.group(empty=True))
            self.afModuleInfo.doStore(self.ModuleInfoNull.nameShort)     
            created = True
        else:
            self.ModuleInfoNull = ObjectFactory(self.afModuleInfo.value)
            
        self.ModuleInfoNull.store('cgmName','modules')   
        self.ModuleInfoNull.store('cgmType','info')
        
        self.ModuleInfoNull.doParent(self.PuppetInfoNull.nameShort)
        
        if created:
            self.ModuleInfoNull.doName(False)
            
        self.afModuleInfo.updateData()   
            
        attributes.doSetLockHideKeyableAttr(self.ModuleInfoNull.nameShort)
        
        #Initialize our modules null as a buffer
        self.ModulesBuffer = BufferFactory(self.ModuleInfoNull.nameShort)
        
        #Checks geo info null
        created = False        
        self.afGeoInfo = AttrFactory(self.afPuppetInfo.value,'geo','message')
        if not self.afGeoInfo.value:
            self.GeoInfoNull = ObjectFactory(mc.group(empty=True))
            self.afGeoInfo.doStore(self.GeoInfoNull.nameShort)              
            created = True
        else:
            self.GeoInfoNull = ObjectFactory(self.afGeoInfo.value)
            
        self.GeoInfoNull.store('cgmName','geo')   
        self.GeoInfoNull.store('cgmType','info')
        
        self.GeoInfoNull.doParent(self.afPuppetInfo.value)
        
        if created:
            self.GeoInfoNull.doName(False)
            
        self.afGeoInfo.updateData()   
            
        attributes.doSetLockHideKeyableAttr(self.GeoInfoNull.nameShort) 
        
            
        #Checks settings info null
        created = False        
        self.afSettingsInfo = AttrFactory(self.afPuppetInfo.value,'settings','message')
        if not self.afSettingsInfo.value:
            self.SettingsInfoNull = ObjectFactory(mc.group(empty=True))
            self.afSettingsInfo.doStore(self.SettingsInfoNull.nameShort)   
            created = True
        else:
            self.SettingsInfoNull = ObjectFactory(self.afSettingsInfo.value)
            
        self.SettingsInfoNull.store('cgmName','settings')   
        self.SettingsInfoNull.store('cgmType','info')
        defaultFont = modules.returnSettingsData('defaultTextFont')
        self.SettingsInfoNull.store('font',defaultFont)
        
        self.SettingsInfoNull.doParent(self.afPuppetInfo.value)
        
        if created:
            self.SettingsInfoNull.doName(False)
            
        self.afSettingsInfo.updateData()   
        
        
        self.optionPuppetMode = AttrFactory(self.SettingsInfoNull,'optionPuppetTemplateMode','int',initialValue = 0)      
        
        self.optionAimAxis= AttrFactory(self.SettingsInfoNull,'axisAim','enum',enum = 'x+:y+:z+:x-:y-:z-',initialValue=2) 
        self.optionUpAxis= AttrFactory(self.SettingsInfoNull,'axisUp','enum',enum = 'x+:y+:z+:x-:y-:z-',initialValue=1) 
        self.optionOutAxis= AttrFactory(self.SettingsInfoNull,'axisOut','enum',enum = 'x+:y+:z+:x-:y-:z-',initialValue=0)         
            
        attributes.doSetLockHideKeyableAttr(self.SettingsInfoNull.nameShort) 
        
        return True
     
    def initialize(self):
        """ 
        Verifies the various components a masterNull for a character/asset. If a piece is missing it replaces it.
        
        RETURNS:
        success(bool)
        """            
        #Puppet null       
        if not attributes.doGetAttr(self.PuppetNull.nameShort,'cgmName'):
            return False
        if attributes.doGetAttr(self.PuppetNull.nameShort,'cgmType') != 'ignore':
            return False
        if attributes.doGetAttr(self.PuppetNull.nameShort,'cgmModuleType') != 'master':
            return False        
        
        self.afModulesGroup = AttrFactory(self.PuppetNull,'modulesGroup')
        if not self.afModulesGroup.value:
            guiFactory.warning("'%s' looks to be missing. Go back to unreferenced file"%self.afModulesGroup.attr)
            return False
        else:
            self.ModulesGroup = ObjectFactory(self.afModulesGroup.value)

        self.afNoTransformGroup = AttrFactory(self.PuppetNull,'noTransformGroup')
        if not self.afNoTransformGroup.value:
            guiFactory.warning("'%s' looks to be missing. Go back to unreferenced file"%self.afNoTransformGroup.attr)
            return False
        else:
            self.NoTransformGroup = ObjectFactory(self.afNoTransformGroup.value)        
            
        self.afGeoGroup = AttrFactory(self.PuppetNull,'geoGroup')
        if not self.afGeoGroup.value:
            guiFactory.warning("'%s' looks to be missing. Go back to unreferenced file"%self.afGeoGroup.attr)
            return False
        else:
            self.GeoGroup = ObjectFactory(self.afGeoGroup.value)        
         
        self.afPuppetInfo = AttrFactory(self.PuppetNull,'info')
        if not self.afPuppetInfo.value:
            guiFactory.warning("'%s' looks to be missing. Go back to unreferenced file"%self.afPuppetInfo.attr)
            return False
        
        else:
            self.PuppetInfoNull = ObjectFactory(self.afPuppetInfo.value)                    
            self.afModuleInfo = AttrFactory(self.PuppetInfoNull,'modules')
            if not self.afModuleInfo.value:
                guiFactory.warning("'%s' looks to be missing. Go back to unreferenced file"%self.afModuleInfo.attr)
                return False  
            else:
                #Initialize our modules null as a buffer
                self.ModuleInfoNull = ObjectFactory(self.afModuleInfo.value)
                self.ModulesBuffer = BufferFactory(self.afModuleInfo.value)                
            
            self.afGeoInfo = AttrFactory(self.PuppetInfoNull,'geo')
            if not self.afGeoInfo.value:
                guiFactory.warning("'%s' looks to be missing. Go back to unreferenced file"%self.afGeoInfo.attr)
                return False
            else:
                self.GeoInfoNull = ObjectFactory(self.afGeoInfo.value)             
            
            self.afSettingsInfo = AttrFactory(self.PuppetInfoNull,'settings')
            if not self.afSettingsInfo.value:
                guiFactory.warning("'%s' looks to be missing. Go back to unreferenced file"%self.afSettingsInfo.attr)
                return False 
            else:
                self.SettingsInfoNull = ObjectFactory(self.afSettingsInfo.value,)
                
                self.optionPuppetMode = AttrFactory(self.SettingsInfoNull,'optionPuppetTemplateMode')
                self.optionAimAxis= AttrFactory(self.SettingsInfoNull,'axisAim') 
                self.optionUpAxis= AttrFactory(self.SettingsInfoNull,'axisUp') 
                self.optionOutAxis= AttrFactory(self.SettingsInfoNull,'axisOut')
                
        return True
            
    def delete(self):
        mc.delete(self.PuppetNull.nameLong)
        
    #>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    # Modules
    #>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    def changeModuleCGMTag(self,moduleName,tag,newInfo,*a,**kw):
        """
        Function to change a cgm tag on a module and push a rename through that moudule's instance
        
        moduleName(string)
        tag(string) which tag to use. For a list
        ###
        from cgm.lib.classes import NameFactory
        NameFactory.cgmNameTags   
        ###
        newInfo(*a,**kw) - info to pass into the attributes.storeInfo() function
        """
        if moduleName in self.ModulesBuffer.bufferList:
            #Clear our instanced module
            index = self.ModulesBuffer.bufferList.index(moduleName)
            modType = search.returnTagInfo(self.Module[index].ModuleNull.nameShort,'moduleType') or False
            if index is not False:
                if modType in moduleTypeToFunctionDict.keys():
                    if self.Module[index].changeCGMTag(tag,newInfo,*a,**kw):
                        self.Module[index] = moduleTypeToFunctionDict[modType](self.Module[index].ModuleNull.nameShort)                   
                    self.ModulesBuffer.updateData()
                else:
                    guiFactory.warning("'%s' is not a module type found in the moduleTypeToFunctionDict. Cannot initialize"%modType)
                    return False  
            else:
                guiFactory.warning("%s is not a valid index. Cannot continue"%index)
                return False                  
        else:
            guiFactory.warning("'%s' doesn't seem to be a connected module. Cannot change tag"%moduleName)        
            return False
        
    def getModules(self,*a,**kw):
        """
        Intializes all connected modules of a puppet
        """           
        self.Module = {}
        self.moduleIndexDict = {}
        self.moduleParents = {}
        self.ModulesBuffer.updateData()
        if self.ModulesBuffer.bufferList:
            for i,m in enumerate(self.ModulesBuffer.bufferList):
                modType = search.returnTagInfo(m,'moduleType') or False
                if modType in moduleTypeToFunctionDict.keys():
                    self.Module[i] = moduleTypeToFunctionDict[modType](m,*a,**kw)
                    self.Module[i].ModuleNull.doParent(self.ModulesGroup.nameLong)
                    self.moduleIndexDict[m] = i
                else:
                    guiFactory.warning("'%s' is not a module type found in the moduleTypeToFunctionDict. Cannot initialize"%modType)
    
    def createModule(self,moduleType,*a,**kw):
        """
        Create and connect a new module
        
        moduleType(string) - type of module to create
        """   
        if moduleType in moduleTypeToFunctionDict.keys():
            tmpModule = moduleTypeToFunctionDict[moduleType](forceNew=True,*a,**kw)
            self.ModulesBuffer.store(tmpModule.ModuleNull.nameShort)
            tmpModule.ModuleNull.doParent(self.ModulesGroup.nameShort)             
            self.Module[ self.ModulesBuffer.bufferList.index(tmpModule.ModuleNull.nameShort) ] = tmpModule
        else:
            guiFactory.warning("'%s' is not a module type found in the moduleTypeToFunctionDict. Cannot initialize"%moduleType)

        
    def addModule(self,module,*a,**kw):
        """
        Adds a module to a puppet
        
        module(string)
        """
        if module in self.ModulesBuffer.bufferList:
            return guiFactory.warning("'%s' already connnected to '%s'"%(module,self.nameBase))

        elif mc.objExists(module):
            # If it exists, check type to initialize and add
            modType = search.returnTagInfo(module,'moduleType') or False
            if modType in moduleTypeToFunctionDict.keys():
                self.ModulesBuffer.store(module)
                moduleNullBuffer = rigging.doParentReturnName(module,self.afModulesGroup.value)
                self.Module[ self.ModulesBuffer.bufferList.index(module) ] = moduleTypeToFunctionDict[modType](moduleNullBuffer)
                
            else:
                guiFactory.warning("'%s' is not a module type found in the moduleTypeToFunctionDict. Cannot initialize")
            
        else:
            guiFactory.warning("'%s' is not a module type found in the moduleTypeToFunctionDict. Cannot initialize"%module)
    
    def removeModule(self,moduleName):
        """
        Removes a module from a puppet
        
        module(string)
        """        
        if moduleName in self.ModulesBuffer.bufferList:
            #Clear our instanced module
            index = self.ModulesBuffer.bufferList.index(moduleName)
            if index is not False:
                self.Module[index] = False
            self.ModulesBuffer.remove(moduleName)
            buffer = rigging.doParentToWorld(moduleName)
            self.getModules()
        else:
            guiFactory.warning("'%s' doesn't seem to be a connected module. Cannot remove"%moduleName)
    
    def deleteModule(self,moduleName,*a,**kw):
        """
        Removes a module from a puppet
        
        module(string)
        """          
        if moduleName in self.ModulesBuffer.bufferList:
            #Clear our instanced module            
            index = self.ModulesBuffer.bufferList.index(moduleName)
            if index:
                self.Module[index] = False
                
            self.ModulesBuffer.remove(moduleName)
            buffer = rigging.doParentToWorld(moduleName)
            mc.delete(buffer)
            self.getModules()
        else:
            guiFactory.warning("'%s' doesn't seem to be a connected module. Cannot delete"%moduleName)
            
    def getOrderedModules(self):
        """ 
        Returns ordered modules of a character
        
        Stores:
        self.orderedModules(list)       
        
        Returns:
        self.orderedModules(list)
        """            
        assert self.ModulesBuffer.bufferList,"'%s' has no modules"%self.nameBase
        self.orderedModules = []
        self.rootModules = []
        moduleParents = {}
        
        for i,m in enumerate(self.ModulesBuffer.bufferList):
            if self.Module[i].moduleParent:
                moduleParents[m] = self.Module[i].moduleParent
            else:
                self.orderedModules.append(m)
                self.rootModules.append(m)                
                
        while len(moduleParents):
            for module in self.orderedModules:
                for k in moduleParents.keys():
                    if moduleParents.get(k) == module:
                        self.orderedModules.append(k)
                        moduleParents.pop(k)
            
                
        return self.orderedModules
                
    def getOrderedParentModules(self):
        """ 
        Returns ordered list of parent modules of a character
        
        Stores:
        self.moduleChildren(dict)
        self.orderedParentModules(list)       
        self.rootModules(list)
        
        Returns:
        self.orderedParentModules(list)
        """    
        moduleParents ={}
        self.orderedParentModules = []
        self.moduleChildren = {}
        
        #First get our module children stored tothe instance as a dict
        for i,m in enumerate(self.ModulesBuffer.bufferList):
            if not self.Module[i].moduleParent:
                self.orderedParentModules.append(m) 
            else:
                moduleParents[m] = self.Module[i].moduleParent                
                
            childrenBuffer = []
            for iCheck,mCheck in enumerate(self.ModulesBuffer.bufferList):
                if self.Module[iCheck].moduleParent == m:
                    childrenBuffer.append(mCheck)
            if childrenBuffer:
                self.moduleChildren[m] = childrenBuffer
    
        moduleChildrenD = copy.copy(self.moduleChildren)
        
        # Pop the 
        if self.orderedParentModules:
            for p in self.orderedParentModules:
                try:
                    moduleChildrenD.pop(p)
                except:pass
            
        cnt = 0
        #Process the childdren looking for parents as children and so on and so forth, appending them as it finds them
        while len(moduleChildrenD)>0 and cnt < 100:
            for module in self.orderedParentModules:
                print module
                for child in moduleChildrenD.keys():
                    cnt +=1
                    if child in moduleParents.keys() and moduleParents[child] == module:
                        self.orderedParentModules.append(child)
                        moduleChildrenD.pop(child)
     
        guiFactory.report("Children dict is - '%s'"%self.moduleChildren)
        guiFactory.report("Module Parents dict is - '%s'"%moduleParents)
        guiFactory.report("Ordered Parents dict is - '%s'"%self.orderedParentModules)
     
        return self.orderedParentModules
        
        

    #>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    # Size objects
    #>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    def verifyTemplateSizeObject(self,create = False):
        """ 
        >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
        DESCRIPTION:
        Returns an existing template size object or makes one and returns it
        
        ARGUMENTS:
        masterNull(list)
        
        RETURNS:
        returnList(list) - size object controls
        >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
        """
        templateSizeObject = attributes.returnMessageObject(self.PuppetNull.nameShort,'templateSizeObject')
        if not mc.objExists(templateSizeObject) and create:
            self.createSizeTemplateControl()
            guiFactory.report("'%s' has template object '%s'"%(self.PuppetNull.nameShort,templateSizeObject))
            return True
        elif templateSizeObject:
            self.templateSizeObjects['root'] = templateSizeObject
            self.templateSizeObjects['start'] = attributes.returnMessageObject(templateSizeObject,'controlStart')
            self.templateSizeObjects['end'] = attributes.returnMessageObject(templateSizeObject,'controlEnd')
            for key in self.templateSizeObjects.keys():
                if not self.templateSizeObjects[key]:
                    #self.templateSizeObjects = {}
                    guiFactory.warning("'%s' didn't check out. Rebuildling..."%(key))
                    try:
                        mc.delete(templateSizeObject)
                        self.createSizeTemplateControl()
                    except:
                        guiFactory.warning("Rebuild failed")                        
                    return False
            guiFactory.report("'%s' has template object '%s'"%(self.PuppetNull.nameShort,templateSizeObject))
            return True
            
        guiFactory.warning("Size template failed to verify")
        return False
    
    def isRef(self):
        """
        Basic ref check. Stores to self
        """
        if mc.referenceQuery(self.PuppetNull.nameShort, isNodeReferenced=True):
            self.refState = True
            self.refPrefix = search.returnReferencePrefix(self.PuppetNull.nameShort)
            return
        self.refState = False
        self.refPrefix = None
        
    def createSizeTemplateControl(self):
        """ 
        >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>   
        DESCRIPTION:
        Generates a sizeTemplateObject. It's been deleted, it recreates it. Guess the size based off of there
        being a mesh there. If there is no mesh, it sets sets an intial size of a 
        [155,170,29] unit character.
        
        ARGUMENTS:
        self.PuppetNull.nameShort(string)
        
        RETURNS:
        returnList(list) = [startCrv(string),EndCrv(list)]
        >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
        """
        #>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
        # Get info
        #>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
        startColors = modules.returnSettingsData('colorStart')
        endColors = modules.returnSettingsData('colorEnd')
        
        font = mc.getAttr((self.afSettingsInfo.value+'.font'))
        
        """ checks for there being anything in our geo group """
        if not self.geo:
            return guiFactory.warning('Need some geo defined to make this tool worthwhile')
            boundingBoxSize =  modules.returnSettingsDataAsFloat('meshlessSizeTemplate')
        else:
            boundingBoxSize = distance.returnBoundingBoxSize (self.afGeoGroup.value)
            boundingBox = mc.exactWorldBoundingBox(self.afGeoGroup.value)
            
        
        """determine orienation """
        maxSize = max(boundingBoxSize)
        matchIndex = boundingBoxSize.index(maxSize)
        
        """Find the pivot of the bounding box """
        pivotPosition = distance.returnCenterPivotPosition(self.afGeoGroup.value)
        
        #>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
        # Get our positions
        #>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
        if self.optionPuppetMode.value == 0:
            #If bio...
            if matchIndex == 1 or matchIndex == 0:
                #Vertical
                posBuffers = [[0,.5,0],[0,.75,0]]
                width = (boundingBoxSize[0]/2)
                height = (boundingBoxSize[1])
                depth = boundingBoxSize[2]
                
                for cnt,pos in enumerate(posBuffers):
                    posBuffer = posBuffers[cnt]
                    posBuffer[0] = 0
                    posBuffer[1] = (posBuffer[1] * height)
                    posBuffer[2] = 0
                    
            elif matchIndex == 2:
                #Horizontal
                posBuffers = [[0,0,-.33],[0,0,.66]]
                width = boundingBoxSize[1]
                height = boundingBoxSize[2]/2
                depth = (boundingBoxSize[0])
                
                for cnt,pos in enumerate(posBuffers):
                    posBuffer = posBuffers[cnt]
                    posBuffer[0] = 0
                    posBuffer[1] = boundingBoxSize[1] * .75
                    posBuffer[2] = (posBuffer[2] * height)
                          
        else:
            #Otherwise 
            if matchIndex == 1 or matchIndex == 0:
                #Vertical
                width = (boundingBoxSize[0]/2)
                height = (boundingBoxSize[1])
                depth = boundingBoxSize[2]                
                posBuffers = [[0,boundingBox[1],0],[0,boundingBox[4],0]]

            elif matchIndex == 2:
                #Horizontal
                width = boundingBoxSize[0]
                height = boundingBoxSize[2]/2
                depth = (boundingBoxSize[1])
                startHeight = max([boundingBox[4],boundingBox[1]]) - depth/2
                print startHeight
                posBuffers = [[0,startHeight,boundingBox[2]],[0,startHeight,boundingBox[5]]]
        # Simple reverse of start pos buffers if the object is pointing negative        
        if self.optionAimAxis < 2:        
            posBuffers.reverse()
            
        #>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
        # Making the controls
        #>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>       
        """ make our control object """
        startCurves = []
        startCurve = curves.createControlCurve('circle',depth*.8)
        mc.xform(startCurve,t=posBuffers[0],ws=True)
        attributes.doSetAttr(startCurve,'rotateOrder',5)
        curves.setCurveColorByName(startCurve,startColors[1])
        startCurves.append(startCurve)
        
        startText = curves.createTextCurve('start',size=depth*.75,font=font)
        mc.xform(startText,t=posBuffers[0],ws=True)
        curves.setCurveColorByName(startText,startColors[0])
        startCurves.append(startText)
        
        endCurves = []
        endCurve = curves.createControlCurve('circle',depth*.8)
        mc.xform(endCurve,t=posBuffers[1],ws=True)
        curves.setCurveColorByName(endCurve,endColors[1])
        attributes.doSetAttr(endCurve,'rotateOrder',5)        
        endCurves.append(endCurve)
        
        endText = curves.createTextCurve('end',size=depth*.6,font=font)
        mc.xform(endText,t=posBuffers[1],ws=True)
        curves.setCurveColorByName(endText,endColors[0])
        endCurves.append(endText)
        
        """ aiming """
        position.aimSnap(startCurve,endCurve,[0,0,1],[0,1,0])
        position.aimSnap(startText,endCurve,[0,0,1],[0,1,0])
        
        position.aimSnap(endCurve,startCurve,[0,0,-1],[0,1,0])
        position.aimSnap(endText,startCurve,[0,0,-1],[0,1,0])
            
        sizeCurveControlStart = curves.combineCurves(startCurves)
        sizeCurveControlEnd = curves.combineCurves(endCurves)
        """ store our info to name our objects"""
        attributes.storeInfo(sizeCurveControlStart,'cgmName',(self.PuppetNull.nameShort+'.cgmName'))
        attributes.storeInfo(sizeCurveControlStart,'cgmDirection','start')
        attributes.storeInfo(sizeCurveControlStart,'cgmType','templateSizeObject')
        sizeCurveControlStart = NameFactory.doNameObject(sizeCurveControlStart)
        mc.makeIdentity(sizeCurveControlStart, apply = True, t=True,s=True,r=True)
    
        attributes.storeInfo(sizeCurveControlEnd,'cgmName',(self.PuppetNull.nameShort+'.cgmName'))
        attributes.storeInfo(sizeCurveControlEnd,'cgmDirection','end')
        attributes.storeInfo(sizeCurveControlEnd,'cgmType','templateSizeObject')
        sizeCurveControlEnd  = NameFactory.doNameObject(sizeCurveControlEnd)
        
        endGroup = rigging.groupMeObject(sizeCurveControlEnd)
        mc.makeIdentity(sizeCurveControlEnd, apply = True, t=True,s=True,r=True)
        
        mc.parentConstraint(sizeCurveControlStart,endGroup,maintainOffset = True)
        
        """ make control group """
        controlGroup = rigging.groupMeObject(sizeCurveControlStart)
        attributes.storeInfo(controlGroup,'cgmName',(self.PuppetNull.nameShort+'.cgmName'))
        attributes.storeInfo(controlGroup,'cgmType','templateSizeObjectGroup')
        controlGroup = NameFactory.doNameObject(controlGroup)

        
        endGroup = rigging.doParentReturnName(endGroup,controlGroup)
        #>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
        # Getting data ready
        #>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>    
        attributes.storeInfo(controlGroup,'controlStart',sizeCurveControlStart)
        attributes.storeInfo(controlGroup,'controlEnd',sizeCurveControlEnd)        
        attributes.storeInfo(self.PuppetNull.nameShort,'templateSizeObject',controlGroup)
        
        self.templateSizeObjects['root'] = controlGroup
        self.templateSizeObjects['start'] = sizeCurveControlStart
        self.templateSizeObjects['end'] = sizeCurveControlEnd  
       
        returnList=[]
        returnList.append(sizeCurveControlStart)
        returnList.append(sizeCurveControlEnd)
        return returnList

    #>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    # Geo Stuff
    #>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>  
    def addGeo(self):
        """ 
        Add geo to a puppet
        """
        assert self.afGeoGroup.value is not False,"No geo group found!"
        
        selection = mc.ls(sl=True,flatten=True,long=True) or []
        
        if not selection:
            guiFactory.warning("No selection found to add to '%s'"%self.nameBase)
        
        returnList = []    
        for o in selection:
            if search.returnObjectType(o) in geoTypes:
                if self.afGeoGroup.value not in search.returnAllParents(o,True):
                    o = rigging.doParentReturnName(o,self.afGeoGroup.value)
                    self.geo.append(o)
                else:
                    guiFactory.warning("'%s' already a part of '%s'"%(o,self.nameBase))
            else:
                guiFactory.warning("'%s' doesn't seem to be geo. Not added to '%s'"%(o,self.nameBase))
    
    def checkGeo(self):
        """
        Check a puppet's geo that it is actually geo
        """
        assert self.afGeoGroup.value is not False,"No geo group found!"
        
        children = search.returnAllChildrenObjects(self.afGeoGroup.value)
        if not children:
            return False
    
        for o in children:
            if search.returnObjectType(o) in geoTypes:
                buff = mc.ls(o,long=True)
                self.geo.append(buff[0])
            else:
                rigging.doParentToWorld(o)
                guiFactory.warning("'%s' isn't geo, removing from group."%o)
        return True
    
    #>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    # Data setting stuff
    #>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>  
    def doSetMode(self,i):
        assert i <(len(CharacterTypes)),"%i isn't a viable base pupppet type"%i
        self.optionPuppetMode.set(i)
        
    def doSetAimAxis(self,i):
        """
        Set the aim axis. if up or out have that axis. They will be changed. Aim is the priority.
        Then Up, and Out is last.
        
        """
        assert i < 6,"%i isn't a viable aim axis integer"%i
        
        self.optionAimAxis.set(i)
        if self.optionUpAxis.value == self.optionAimAxis.value:
            self.doSetUpAxis(i)
        if self.optionOutAxis.value == self.optionAimAxis.value:
            self.doSetOutAxis(i)
            
        return True
        
    def doSetUpAxis(self,i):
        """
        Set the aim axis. if up or out have that axis. They will be changed. Aim is the priority.
        Then Up, and Out is last.
        
        """        
        assert i < 6,"%i isn't a viable up axis integer"%i
        axisBuffer = range(6)
        axisBuffer.remove(self.optionAimAxis.value)
        
        if i != self.optionAimAxis.value:
            self.optionUpAxis.set(i)  
        else:
            self.optionUpAxis.set(axisBuffer[0]) 
            guiFactory.warning("Aim axis has '%s'. Changed up axis to '%s'. Change aim setting if you want this seeting"%(axisDirectionsByString[self.optionAimAxis.value],axisDirectionsByString[self.optionUpAxis.value]))                  
            axisBuffer.remove(axisBuffer[0])
            
        if self.optionOutAxis.value in [self.optionAimAxis.value,self.optionUpAxis.value]:
            for i in axisBuffer:
                if i not in [self.optionAimAxis.value,self.optionUpAxis.value]:
                    self.doSetOutAxis(i)
                    guiFactory.warning("Setting conflict. Changed out axis to '%s'"%axisDirectionsByString[i])                    
                    break
        return True        
        
        
    def doSetOutAxis(self,i):
        assert i < 6,"%i isn't a viable aim axis integer"%i
        
        if i not in [self.optionAimAxis.value,self.optionUpAxis.value]:
            self.optionOutAxis.set(i)
        else:
            axisBuffer = range(6)
            axisBuffer.remove(self.optionAimAxis.value)
            axisBuffer.remove(self.optionUpAxis.value)
            self.optionOutAxis.set(axisBuffer[0]) 
            guiFactory.warning("Setting conflict. Changed out axis to '%s'"%axisDirectionsByString[ axisBuffer[0] ])                    


        
    def doRenamePuppet(self,newName):
        """
        Rename Puppet null
        """
        if newName == self.PuppetNull.cgm['cgmName']:
            return guiFactory.warning("Already named '%s'"%newName)
        
        self.PuppetNull.store('cgmName ',newName)   
        self.nameBase = newName
        self.PuppetNull.doName()
        self.initializePuppet()
        self.getModules()
        guiFactory.warning("Puppet renamed as '%s'"%newName)
        
        
   #>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
   #>> Sizing
   #>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    def doSize(self):
        """ 
        Function to size a puppet
    
        """
        #>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
        # Get Info
        #>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
        ### TemplateSizeObject Check ###
        if not self.ModulesBuffer.bufferList:
            raise StandardError,"'%s' has no modules"%self.PuppetNull.nameLong            
        
        if not self.templateSizeObjects:
            raise StandardError,"'%s' has no size template"%self.PuppetNull.nameLong
        
        basicOrientation = logic.returnHorizontalOrVertical([self.templateSizeObjects['start'],self.templateSizeObjects['end']])
        print basicOrientation
        
        # Get module info
        if not self.getOrderedModules() and self.getOrderedParentModules():
            guiFactory.warning("Failed to get ordered module info, here's what we got...")
            guiFactory.report("Ordered modules - %s"%self.orderedModules)
            guiFactory.report("Ordered parent modules - %s"%self.orderedParentModules)
            guiFactory.report("Module children- %s"%self.moduleChildren)
        
        ##Delete this later
        guiFactory.report("Ordered modules - %s"%self.orderedModules)
        guiFactory.report("Ordered parent modules - %s"%self.orderedParentModules)
        guiFactory.report("Module children- %s"%self.moduleChildren)        
        
        #>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
        # Starter locs and positions
        #>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>        
        coreModulePositionList = {}
        locInfo = {}
        checkList = {}
        orderedListCopy = copy.copy(self.orderedModules)
        
        for m in self.orderedModules:
            checkList[m] = False
         
        # first do the root modules """        
        for m in self.rootModules:
            #Size each module and store it
            buffer = self.Module[ self.moduleIndexDict[m] ].doInitialSize(self) or False
            if not buffer:
                guiFactory.warning("Failed to get a size return on '%s'"%m)
                return False
            coreModulePositionList[m] = buffer['positions']
            locInfo[m] = buffer['locator']
            checkList.pop(m)
            orderedListCopy.remove(m)
            
        """   
        #>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
        # Delete the locs 
        #>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>            
        for key in locInfo.keys():
            buffer = locInfo.get(key)
            parentBuffer = search.returnAllParents(buffer)
            if mc.objExists(parentBuffer[-1]):
                mc.delete(parentBuffer[-1])
                    
        
        #>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
        # Store everything
        #>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
        for module in orderedModules:
            ### module null data ###
            moduleData = attributes.returnUserAttrsToDict(module)
            infoNulls = modules.returnInfoNullsFromModule(module)
        
            ### part name ###
            partName = NameFactory.returnUniqueGeneratedName(module, ignore = 'cgmType')
            partType = moduleData.get('cgmModuleType')
            direction = moduleData.get('cgmDirection')
            
            ### template null ###
            templateNull = moduleData.get('templateNull')
            templateNullData = attributes.returnUserAttrsToDict(templateNull)
            curveDegree = templateNullData.get('curveDegree')
            handles = templateNullData.get('handles')
            stiffIndex = templateNullData.get('stiffIndex') 
        
            ### template object nulls ###
            templatePosObjectsInfoNull = infoNulls.get('templatePosObjects')
            templateControlObjectsNull = infoNulls.get('templateControlObjects')
            starterObjectsInfoNull = infoNulls.get('templateStarterData')
            templateControlObjectsDataNull = infoNulls.get('templateControlObjectsData')
            rotateOrderInfoNull = infoNulls.get('rotateOrderInfo')
            coreNamesInfoNull = infoNulls.get('coreNames')
            
            ### rig null ###
            rigNull = moduleData.get('rigNull')
            
            #>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
            # Positional
            #>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>   
            corePositionList = characterCorePositionList.get(module)
            
            modules.doPurgeNull(starterObjectsInfoNull)
            ### store our positional data ###
            for i in range(len(corePositionList)):
                buffer = ('%s%s' % ('pos_',i))
                mc.addAttr (starterObjectsInfoNull, ln=buffer, at= 'double3')
                mc.addAttr (starterObjectsInfoNull, ln=(buffer+'X'),p=buffer , at= 'double')
                mc.addAttr (starterObjectsInfoNull, ln=(buffer+'Y'),p=buffer , at= 'double')
                mc.addAttr (starterObjectsInfoNull, ln=(buffer+'Z'),p=buffer , at= 'double')
                xBuffer = (starterObjectsInfoNull+'.'+buffer+'X')
                yBuffer = (starterObjectsInfoNull+'.'+buffer+'Y')
                zBuffer = (starterObjectsInfoNull+'.'+buffer+'Z')
                set = corePositionList[i]
                mc.setAttr (xBuffer, set[0])
                mc.setAttr (yBuffer, set[1])
                mc.setAttr (zBuffer, set[2])
                
            ### make a place to store rotational data ###
            for i in range(len(corePositionList)+1):
                buffer = ('%s%s' % ('rot_',i))
                mc.addAttr (starterObjectsInfoNull, ln=buffer, at= 'double3')
                mc.addAttr (starterObjectsInfoNull, ln=(buffer+'X'),p=buffer , at= 'double')
                mc.addAttr (starterObjectsInfoNull, ln=(buffer+'Y'),p=buffer , at= 'double')
                mc.addAttr (starterObjectsInfoNull, ln=(buffer+'Z'),p=buffer , at= 'double')
    
            modules.doPurgeNull(templateControlObjectsDataNull)
            ### store our positional data ###
            for i in range(len(corePositionList)):
                buffer = ('%s%s' % ('pos_',i))
                mc.addAttr (templateControlObjectsDataNull, ln=buffer, at= 'double3')
                mc.addAttr (templateControlObjectsDataNull, ln=(buffer+'X'),p=buffer , at= 'double')
                mc.addAttr (templateControlObjectsDataNull, ln=(buffer+'Y'),p=buffer , at= 'double')
                mc.addAttr (templateControlObjectsDataNull, ln=(buffer+'Z'),p=buffer , at= 'double')
                
                ### make a place to store rotational data ###
                buffer = ('%s%s' % ('rot_',i))
                mc.addAttr (templateControlObjectsDataNull, ln=buffer, at= 'double3')
                mc.addAttr (templateControlObjectsDataNull, ln=(buffer+'X'),p=buffer , at= 'double')
                mc.addAttr (templateControlObjectsDataNull, ln=(buffer+'Y'),p=buffer , at= 'double')
                mc.addAttr (templateControlObjectsDataNull, ln=(buffer+'Z'),p=buffer , at= 'double')
                          
                
                ### make a place for scale data ###
                buffer = ('%s%s' % ('scale_',i))
                mc.addAttr (templateControlObjectsDataNull, ln=buffer, at= 'double3')
                mc.addAttr (templateControlObjectsDataNull, ln=(buffer+'X'),p=buffer , at= 'double')
                mc.addAttr (templateControlObjectsDataNull, ln=(buffer+'Y'),p=buffer , at= 'double')
                mc.addAttr (templateControlObjectsDataNull, ln=(buffer+'Z'),p=buffer , at= 'double')
        
            #>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
            # Need to generate names
            #>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>    
            ### check the settings first ###
            settingsCoreNames = modules.returncgmTemplateCoreNames(partType)
            
            ### if there are no names settings, genearate them from name of the limb module###
            generatedNames = []
            if settingsCoreNames == False:   
                cnt = 1
                for handle in range(handles):
                    generatedNames.append('%s%s%i' % (partName,'_',cnt))
                    cnt+=1
            
            elif (len(corePositionList)) > (len(settingsCoreNames)):
                ### Otherwise we need to make sure that there are enough core names for handles ###       
                cntNeeded = (len(corePositionList) - len(settingsCoreNames) +1)
                nonSplitEnd = settingsCoreNames[len(settingsCoreNames)-2:]
                toIterate = settingsCoreNames[1]
                iterated = []
                for i in range(cntNeeded):
                    iterated.append('%s%s%i' % (toIterate,'_',(i+1)))
                generatedNames.append(settingsCoreNames[0])
                for name in iterated:
                    generatedNames.append(name)
                for name in nonSplitEnd:
                    generatedNames.append(name) 
                    
            else:
                generatedNames = settingsCoreNames
                
            
            modules.doPurgeNull(coreNamesInfoNull)
            ### store our name data###
            n = 0
            for name in generatedNames:
                attrBuffer = (coreNamesInfoNull + '.' + ('%s%s' % ('name_',n)))
                attributes.addStringAttributeToObj(coreNamesInfoNull,('%s%s' % ('name_',n)))
                n+=1
                mc.setAttr(attrBuffer, name, type='string')
    
            #>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
            # Rotation orders
            #>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> 
            modules.doPurgeNull(rotateOrderInfoNull)
            ### store our rotation order data ###
            for i in range(len(corePositionList)):
                atrrNamebuffer = ('%s%s' % ('rotateOrder_',i))
                attributes.addRotateOrderAttr(rotateOrderInfoNull,atrrNamebuffer)
                
            print ('%s%s' % (module,' sized and stored!')) """
            
            
            
            
            
             
        """                  
        for module in parentModules:
            childrenModules = modules.returnOrderedChildrenModules(module)
            for moduleType in childrenModules.keys():
                typeModuleDict = childrenModules.get(moduleType)
                for directionKey in typeModuleDict.keys():
                    directionModuleSet = typeModuleDict.get(directionKey)
                    locInfoBuffer = {}
                    #>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
                    # Starter locs
                    #>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
                    for m in directionModuleSet:
                        rawModuleName = NameFactory.returnUniqueGeneratedName(m,ignore='cgmType')
                        ### make our initial sub groups ###
                        if moduleType == 'arm' or moduleType == 'wing' or moduleType == 'tail':
                            locInfoBuffer[m] = createStartingPositionLoc(m,modeDict.get(moduleType),typeWorkingCurveDict.get(moduleType),typeAimingCurveDict.get(moduleType),cvDict.get(directionKey))
                            orderedModules.remove(m) 
                            checkList.pop(m)
                        elif moduleType == 'clavicle':
                            locInfoBuffer[m] = createStartingPositionLoc(m,modeDict.get(moduleType),templateSizeObjects[1],templateSizeObjects[0],cvDict.get(directionKey))
                            orderedModules.remove(m) 
                            checkList.pop(m)
                        elif moduleType == 'finger':
                            moduleParent = attributes.returnMessageObject(m,'moduleParent')
                            parentLoc = locInfo.get(moduleParent)
                            locInfoBuffer[m] = createStartingPositionLoc(m,modeDict.get(moduleType),parentLoc)
                            orderedModules.remove(m) 
                        elif moduleType == 'foot':
                            moduleParent = attributes.returnMessageObject(m,'moduleParent')
                            parentLoc = locInfo.get(moduleParent)
                            locInfoBuffer[m] = createStartingPositionLoc(m,modeDict.get(moduleType),parentLoc)
                            orderedModules.remove(m) 
                            checkList.pop(m)
                        elif moduleType == 'head':
                            locInfoBuffer[m] = createStartingPositionLoc(m,modeDict.get(moduleType),templateSizeObjects[1],templateSizeObjects[0],cvDict.get(directionKey))
                            orderedModules.remove(m) 
                            checkList.pop(m)
                        elif moduleType == 'leg':
                            if basicOrientation == 'vertical':
                                locInfoBuffer[m] = createStartingPositionLoc(m,modeDict.get(moduleType),typeWorkingCurveDict.get(moduleType),typeAimingCurveDict.get(moduleType),cvDict.get(directionKey))
                            else:
                                horizontalLegInfoBuffer = horiztonalLegDict.get(directionKey)
                                locInfoBuffer[m] = createStartingPositionLoc(m,modeDict.get(moduleType),horizontalLegInfoBuffer[1],horizontalLegInfoBuffer[2],horizontalLegInfoBuffer[0])
                            orderedModules.remove(m) 
                            checkList.pop(m)
                        ### do we need to spread them? ###
                    numberOfLocs = len(directionModuleSet)
                    if numberOfLocs > 1:        
                        if moduleType in aimSpreads:
                            #>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
                            # Aim spread
                            #>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
                            print 'aim spread!'
                            ### do an aim spread ###
                            sizeObjectLength = distance.returnDistanceBetweenObjects(templateSizeObjects[0],templateSizeObjects[1])
                            moveDistance = (sizeObjectLength/1.25)/len(directionModuleSet)
                                
                            ### let's move stuff ###
                            cnt = 0
                            for m in directionModuleSet:
                                mLocInfo = locInfoBuffer.get(m)
                                mc.xform(mLocInfo[1],t=[0,0,moveDistance*cnt],r=True,os=True)
                                cnt += 1
                        else:
                            #>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
                            # Split spread
                            #>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
                            print 'split spread!'
                            ### if we're not going to do an aim spread...do a split spread ###
                            if moduleType == 'finger':
                                print 'yes!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!'
                                ### get the parent module###
                                moduleParent = attributes.returnMessageObject(directionModuleSet[0],'moduleParent')
                                print 
                                ### get it's positional data###
                                parentPositions = characterCorePositionList.get(moduleParent)
                                parentLastSegmentDistance = distance.returnDistanceBetweenPoints(parentPositions[-2],parentPositions[-1])
                                curveWidth = parentLastSegmentDistance / 5
                            else:
                                absCurveSize = distance.returnAbsoluteSizeCurve(typeWorkingCurveDict.get(moduleType))
                                curveWidth = max(absCurveSize)
                                curveWidth = (curveWidth*.9)/2
                                
                            mLocInfo = locInfoBuffer.get(directionModuleSet[0])
                            
                            ### gonna make a curve to split###
                            locs=[]
                            locToDup = mLocInfo[0]
                            curveStartBuffer = mc.duplicate(locToDup,rc=True)
                            curveEndBuffer = mc.duplicate(locToDup,rc=True)
                            curveStartBuffer = rigging.doParentToWorld(curveStartBuffer[0])
                            curveEndBuffer = rigging.doParentToWorld(curveEndBuffer[0])
                            locs.append(curveStartBuffer)
                            locs.append(curveEndBuffer)
                            mc.xform(locs[0],t=[curveWidth,0,0],r=True,os=True)
                            mc.xform(locs[1],t=[-curveWidth,0,0],r=True,os=True)
                            
                            if numberOfLocs == 2:
                                cnt = 0
                                for m in directionModuleSet:
                                    mLocInfo = locInfoBuffer.get(m)
                                    position.movePointSnap(mLocInfo[1],locs[cnt])
                                    cnt +=1
                                for loc in locs:
                                    mc.delete(loc)
                            elif numberOfLocs == 3:
                                midM = directionModuleSet[0]
                                cnt = 0
                                for m in directionModuleSet:
                                    if m != midM:
                                        mLocInfo = locInfoBuffer.get(m)
                                        position.movePointSnap(mLocInfo[1],locs[cnt])
                                        cnt +=1
                                for loc in locs:
                                    mc.delete(loc)
                            else:
                                crvName = curves.curveFromObjList(locs)          
                                crvName = mc.rebuildCurve (crvName, ch=0, rpo=1, rt=0, end=1, kr=0, kcp=0, kep=1, kt=0, s=len(directionModuleSet)-1, d=1, tol=0.001)
                                curveLocs = locators.locMeCVsOnCurve(crvName[0])
                                cnt = 0
                                for m in directionModuleSet:
                                    mLocInfo = locInfoBuffer.get(m)
                                    position.movePointSnap(mLocInfo[1],curveLocs[cnt])
                                    cnt+=1
                                
                                for loc in curveLocs,locs:
                                    mc.delete(loc)
                                mc.delete(crvName[0])
                    #>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
                    # Generate initial positional data
                    #>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
                    for module in directionModuleSet:
                        #characterCorePositionListBuffer = doGenerateInitialPositionData(m,masterNull,locInfoBuffer,templateSizeObjects)      
                        characterCorePositionList[module] = 'data goes here!'
                        currentLocInfo = locInfoBuffer.get(module)
                        locInfo[module] = currentLocInfo
                        if moduleType == 'arm':
                            if modules.returnOrderedChildrenModules(module) != False:
                                baseDistance = (doGeneratePartBaseDistance(currentLocInfo[0],meshGroup)) * .7
                            else: baseDistance = doGeneratePartBaseDistance(currentLocInfo[0],meshGroup)
                        elif moduleType == 'leg':
                            if modules.returnOrderedChildrenModules(module) != False:
                                baseDistance = (doGeneratePartBaseDistance(currentLocInfo[0],meshGroup)) * .9
                            else: baseDistance = doGeneratePartBaseDistance(currentLocInfo[0],meshGroup)
                        elif moduleType == 'foot' or moduleType == 'hoof':
                            ### get the parent module###
                            moduleParent = attributes.returnMessageObject(m,'moduleParent')
                            ### get it's positional data###
                            parentPositions = characterCorePositionList.get(moduleParent)
                            parentLastSegmentDistance = distance.returnDistanceBetweenPoints(parentPositions[-2],parentPositions[-1])
                            baseDistance = parentLastSegmentDistance / 2.5
                        else:
                            baseDistance = doGeneratePartBaseDistance(currentLocInfo[0],meshGroup)
                        characterCorePositionListBuffer = doGenerateInitialPositionData(module,masterNull,currentLocInfo,templateSizeObjects,baseDistance)      
                        characterCorePositionList[module] = characterCorePositionListBuffer[0]
                        locInfo[module] = characterCorePositionListBuffer[1]
                            
        
        for key in locInfo.keys():
            infoBuffer = locInfo.get(key)
            parentBuffer = search.returnAllParents(infoBuffer)
            if mc.objExists(parentBuffer[-1]) == True:
                mc.delete(parentBuffer[-1])
                
                
        
        orderedModules = modules.returnOrderedModules(masterNull)
        #>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
        # Store everything
        #>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
        for module in orderedModules:
            ### module null data ###
            moduleData = attributes.returnUserAttrsToDict(module)
            infoNulls = modules.returnInfoNullsFromModule(module)
        
            ### part name ###
            partName = NameFactory.returnUniqueGeneratedName(module, ignore = 'cgmType')
            partType = moduleData.get('cgmModuleType')
            direction = moduleData.get('cgmDirection')
            
            ### template null ###
            templateNull = moduleData.get('templateNull')
            templateNullData = attributes.returnUserAttrsToDict(templateNull)
            curveDegree = templateNullData.get('curveDegree')
            handles = templateNullData.get('handles')
            stiffIndex = templateNullData.get('stiffIndex') 
        
            ### template object nulls ###
            templatePosObjectsInfoNull = infoNulls.get('templatePosObjects')
            templateControlObjectsNull = infoNulls.get('templateControlObjects')
            starterObjectsInfoNull = infoNulls.get('templateStarterData')
            templateControlObjectsDataNull = infoNulls.get('templateControlObjectsData')
            rotateOrderInfoNull = infoNulls.get('rotateOrderInfo')
            coreNamesInfoNull = infoNulls.get('coreNames')
            
            ### rig null ###
            rigNull = moduleData.get('rigNull')
            
            #>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
            # Positional
            #>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>   
            corePositionList = characterCorePositionList.get(module)
            
            modules.doPurgeNull(starterObjectsInfoNull)
            ### store our positional data ###
            for i in range(len(corePositionList)):
                buffer = ('%s%s' % ('pos_',i))
                mc.addAttr (starterObjectsInfoNull, ln=buffer, at= 'double3')
                mc.addAttr (starterObjectsInfoNull, ln=(buffer+'X'),p=buffer , at= 'double')
                mc.addAttr (starterObjectsInfoNull, ln=(buffer+'Y'),p=buffer , at= 'double')
                mc.addAttr (starterObjectsInfoNull, ln=(buffer+'Z'),p=buffer , at= 'double')
                xBuffer = (starterObjectsInfoNull+'.'+buffer+'X')
                yBuffer = (starterObjectsInfoNull+'.'+buffer+'Y')
                zBuffer = (starterObjectsInfoNull+'.'+buffer+'Z')
                set = corePositionList[i]
                mc.setAttr (xBuffer, set[0])
                mc.setAttr (yBuffer, set[1])
                mc.setAttr (zBuffer, set[2])
                
            ### make a place to store rotational data ###
            for i in range(len(corePositionList)+1):
                buffer = ('%s%s' % ('rot_',i))
                mc.addAttr (starterObjectsInfoNull, ln=buffer, at= 'double3')
                mc.addAttr (starterObjectsInfoNull, ln=(buffer+'X'),p=buffer , at= 'double')
                mc.addAttr (starterObjectsInfoNull, ln=(buffer+'Y'),p=buffer , at= 'double')
                mc.addAttr (starterObjectsInfoNull, ln=(buffer+'Z'),p=buffer , at= 'double')
    
            modules.doPurgeNull(templateControlObjectsDataNull)
            ### store our positional data ###
            for i in range(len(corePositionList)):
                buffer = ('%s%s' % ('pos_',i))
                mc.addAttr (templateControlObjectsDataNull, ln=buffer, at= 'double3')
                mc.addAttr (templateControlObjectsDataNull, ln=(buffer+'X'),p=buffer , at= 'double')
                mc.addAttr (templateControlObjectsDataNull, ln=(buffer+'Y'),p=buffer , at= 'double')
                mc.addAttr (templateControlObjectsDataNull, ln=(buffer+'Z'),p=buffer , at= 'double')
                
                ### make a place to store rotational data ###
                buffer = ('%s%s' % ('rot_',i))
                mc.addAttr (templateControlObjectsDataNull, ln=buffer, at= 'double3')
                mc.addAttr (templateControlObjectsDataNull, ln=(buffer+'X'),p=buffer , at= 'double')
                mc.addAttr (templateControlObjectsDataNull, ln=(buffer+'Y'),p=buffer , at= 'double')
                mc.addAttr (templateControlObjectsDataNull, ln=(buffer+'Z'),p=buffer , at= 'double')
                          
                
                ### make a place for scale data ###
                buffer = ('%s%s' % ('scale_',i))
                mc.addAttr (templateControlObjectsDataNull, ln=buffer, at= 'double3')
                mc.addAttr (templateControlObjectsDataNull, ln=(buffer+'X'),p=buffer , at= 'double')
                mc.addAttr (templateControlObjectsDataNull, ln=(buffer+'Y'),p=buffer , at= 'double')
                mc.addAttr (templateControlObjectsDataNull, ln=(buffer+'Z'),p=buffer , at= 'double')
        
            #>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
            # Need to generate names
            #>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>    
            ### check the settings first ###
            settingsCoreNames = modules.returncgmTemplateCoreNames(partType)
            
            ### if there are no names settings, genearate them from name of the limb module###
            generatedNames = []
            if settingsCoreNames == False:   
                cnt = 1
                for handle in range(handles):
                    generatedNames.append('%s%s%i' % (partName,'_',cnt))
                    cnt+=1
            
            elif (len(corePositionList)) > (len(settingsCoreNames)):
                ### Otherwise we need to make sure that there are enough core names for handles ###       
                cntNeeded = (len(corePositionList) - len(settingsCoreNames) +1)
                nonSplitEnd = settingsCoreNames[len(settingsCoreNames)-2:]
                toIterate = settingsCoreNames[1]
                iterated = []
                for i in range(cntNeeded):
                    iterated.append('%s%s%i' % (toIterate,'_',(i+1)))
                generatedNames.append(settingsCoreNames[0])
                for name in iterated:
                    generatedNames.append(name)
                for name in nonSplitEnd:
                    generatedNames.append(name) 
                    
            else:
                generatedNames = settingsCoreNames
                
            
            modules.doPurgeNull(coreNamesInfoNull)
            ### store our name data###
            n = 0
            for name in generatedNames:
                attrBuffer = (coreNamesInfoNull + '.' + ('%s%s' % ('name_',n)))
                attributes.addStringAttributeToObj(coreNamesInfoNull,('%s%s' % ('name_',n)))
                n+=1
                mc.setAttr(attrBuffer, name, type='string')
    
            #>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
            # Rotation orders
            #>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> 
            modules.doPurgeNull(rotateOrderInfoNull)
            ### store our rotation order data ###
            for i in range(len(corePositionList)):
                atrrNamebuffer = ('%s%s' % ('rotateOrder_',i))
                attributes.addRotateOrderAttr(rotateOrderInfoNull,atrrNamebuffer)
                
            print ('%s%s' % (module,' sized and stored!'))"""

    
    