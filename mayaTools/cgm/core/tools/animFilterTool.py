"""
------------------------------------------
baseTool: cgm.core.tools
Author: David Bokser
email: dbokser@cgmonks.com

Website : http://www.cgmonastery.com
------------------------------------------
Collection of anim post filters to help with animation
================================================================
"""
# From Python =============================================================
import copy
import re
import time
import pprint
import os
import logging
import json

logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)

import maya.cmds as mc

import cgm.core.classes.GuiFactory as cgmUI
from cgm.core import cgm_RigMeta as cgmRigMeta
mUI = cgmUI.mUI

from cgm.core.lib import shared_data as SHARED
from cgm.core.cgmPy import validateArgs as VALID
from cgm.core import cgm_General as cgmGEN
from cgm.core import cgm_Meta as cgmMeta
import cgm.core.lib.transform_utils as TRANS
from cgm.core.cgmPy import path_Utils as CGMPATH
import cgm.core.lib.math_utils as MATH
from cgm.lib import lists

from cgm.core.tools import dragger as DRAGGER
from cgm.core.tools import trajectoryAim as TRAJECTORYAIM
from cgm.core.tools import keyframeToMotionCurve as K2MC
from cgm.core.tools import spring as SPRING

#>>> Root settings =============================================================
__version__ = cgmGEN.__RELEASE
__toolname__ ='postFilter'

_padding = 5

class ui(cgmUI.cgmGUI):
    USE_Template = 'cgmUITemplate'
    WINDOW_NAME = '{0}_ui'.format(__toolname__)    
    WINDOW_TITLE = '{1} - {0}'.format(__version__,__toolname__)
    DEFAULT_MENU = None
    RETAIN = True
    MIN_BUTTON = True
    MAX_BUTTON = False
    FORCE_DEFAULT_SIZE = True  #always resets the size of the window when its re-created  
    DEFAULT_SIZE = 425,350
    TOOLNAME = '{0}.ui'.format(__toolname__)
    
    def insert_init(self,*args,**kws):
        _str_func = '__init__[{0}]'.format(self.__class__.TOOLNAME)            
        log.info("|{0}| >>...".format(_str_func))

        if kws:log.debug("kws: %s"%str(kws))
        if args:log.debug("args: %s"%str(args))
        log.info(self.__call__(q=True, title=True))

        self.__version__ = __version__
        self.__toolName__ = self.__class__.WINDOW_NAME	

        #self.l_allowedDockAreas = []
        self.WINDOW_TITLE = self.__class__.WINDOW_TITLE
        self.DEFAULT_SIZE = self.__class__.DEFAULT_SIZE

        self._optionDict = {
            'aimFwd' : 'z+',
            'aimUp' : 'y+',
            'translate' : True,
            'rotate' : True
        }
        
        self._actionList = []
        self._loadedFile = ""

 
    def build_menus(self):
        self.uiMenu_FileMenu = mUI.MelMenu(l='File', pmc = cgmGEN.Callback(self.buildMenu_file))
        self.uiMenu_SetupMenu = mUI.MelMenu(l='Setup', pmc = cgmGEN.Callback(self.buildMenu_setup))

    def buildMenu_file(self):
        self.uiMenu_FileMenu.clear()                      

        mUI.MelMenuItem( self.uiMenu_FileMenu, l="Save",
                         c = lambda *a:mc.evalDeferred(cgmGEN.Callback(uiFunc_save_actions,self)))

        mUI.MelMenuItem( self.uiMenu_FileMenu, l="Save As",
                         c = lambda *a:mc.evalDeferred(cgmGEN.Callback(uiFunc_save_as_actions,self)))
        
        mUI.MelMenuItem( self.uiMenu_FileMenu, l="Load",
                         c = lambda *a:mc.evalDeferred(cgmGEN.Callback(uiFunc_load_actions,self)))

    def buildMenu_setup(self):
        self.uiMenu_SetupMenu.clear()
        #>>> Reset Options		                     

        mUI.MelMenuItemDiv( self.uiMenu_SetupMenu )

        mUI.MelMenuItem( self.uiMenu_SetupMenu, l="Reload",
                         c = lambda *a:mc.evalDeferred(self.reload,lp=True))

        mUI.MelMenuItem( self.uiMenu_SetupMenu, l="Reset",
                         c = lambda *a:mc.evalDeferred(self.reload,lp=True))
        
    def build_layoutWrapper(self,parent):
        _str_func = 'build_layoutWrapper'
        #self._d_uiCheckBoxes = {}
    
        #_MainForm = mUI.MelFormLayout(parent,ut='cgmUISubTemplate')
        _MainForm = mUI.MelFormLayout(self,ut='cgmUITemplate')
        _column = buildColumn_main(self,_MainForm,True)

    
        _row_cgm = cgmUI.add_cgmFooter(_MainForm)            
        _MainForm(edit = True,
                  af = [(_column,"top",0),
                        (_column,"left",0),
                        (_column,"right",0),                        
                        (_row_cgm,"left",0),
                        (_row_cgm,"right",0),                        
                        (_row_cgm,"bottom",0),
    
                        ],
                  ac = [(_column,"bottom",2,_row_cgm),
                        ],
                  attachNone = [(_row_cgm,"top")])          
        

def buildColumn_main(self,parent, asScroll = False):
    """
    Trying to put all this in here so it's insertable in other uis
    
    """   
    if asScroll:
        _inside = mUI.MelScrollLayout(parent,useTemplate = 'cgmUISubTemplate') 
    else:
        _inside = mUI.MelColumnLayout(parent,useTemplate = 'cgmUISubTemplate') 
    
    #>>>Objects Load Row ---------------------------------------------------------------------------------------
    uiFunc_build_post_process_column(self,_inside)
    
    return _inside
    
def uiFunc_clear_loaded(self):
    _str_func = 'uiFunc_clear_loaded'

    self._mTransformTarget = False
    #self._mGroup = False
    self.uiTF_objLoad(edit=True, l='',en=False)      
    #self.uiField_report(edit=True, l='...')
    #self.uiReport_objects()
    #self.uiScrollList_parents.clear()
    
    #for o in self._l_toEnable:
        #o(e=True, en=False)  
     
def uiFunc_updateTargetDisplay(self):
    _str_func = 'uiFunc_updateTargetDisplay'  
    #self.uiScrollList_parents.clear()

    if not self._mTransformTarget:
        log.info("|{0}| >> No target.".format(_str_func))                        
        #No obj
        self.uiTF_objLoad(edit=True, l='',en=False)
        self._mGroup = False

        #for o in self._l_toEnable:
            #o(e=True, en=False)
        return
    
    _short = self._mTransformTarget.p_nameBase
    self.uiTF_objLoad(edit=True, ann=_short)
    
    if len(_short)>20:
        _short = _short[:20]+"..."
    self.uiTF_objLoad(edit=True, l=_short)   
    
    self.uiTF_objLoad(edit=True, en=True)
    
    return

def uiFunc_build_post_process_column(self, parentColumn):   
    _str_func = 'uiFunc_build_post_process_column[{0}]'.format(self.__class__.TOOLNAME)            
    log.info("|{0}| >>...".format(_str_func)) 

    mc.setParent(parentColumn)
    cgmUI.add_LineSubBreak()

    # Post Process Action
    #
    _row = mUI.MelHSingleStretchLayout(parentColumn,ut='cgmUISubTemplate',padding = 5)
    self._post_row_aimDirection = _row

    mUI.MelSpacer(_row,w=_padding)                          
    mUI.MelLabel(_row,l='Action:')

    _row.setStretchWidget( mUI.MelSeparator(_row) )

    actions = ['Dragger', 'Spring', 'Trajectory Aim', 'Keyframe to Motion Curve']

    self.post_actionMenu = mUI.MelOptionMenu(_row,useTemplate = 'cgmUITemplate') #, changeCommand=cgmGEN.Callback(uiFunc_setPostAction,self)
    for dir in actions:
        self.post_actionMenu.append(dir)
    
    self.post_actionMenu.setValue(actions[0])

    mUI.MelSpacer(_row,w=_padding)

    _row.layout()
    #
    # End Post Process Action


    # Add Action Button
    #
    _row = mUI.MelHSingleStretchLayout(parentColumn,ut='cgmUISubTemplate',padding = 5)

    mUI.MelSpacer(_row,w=_padding)
    
    _row.setStretchWidget( cgmUI.add_Button(_row,'Add Action',
        cgmGEN.Callback(uiFunc_add_action,self),                         
        #lambda *a: attrToolsLib.doAddAttributesToSelected(self),
        'Add Action',h=30) )
    
    mUI.MelSpacer(_row,w=_padding)

    _row.layout()       
    #
    # End Add Action Button

    # Post Process Options Frame
    #
    self._postProcessOptionsColumn = mUI.MelColumnLayout(parentColumn,useTemplate = 'cgmUISubTemplate') 
    #
    # Post Process Options Frame
    
    # Actions Frame
    #
    _row = mUI.MelHSingleStretchLayout(parentColumn,ut='cgmUISubTemplate',padding = _padding)        

    mUI.MelSpacer(_row,w=_padding)

    _subColumn = mUI.MelColumnLayout(_row,useTemplate = 'cgmUIHeaderTemplate') 

    self._actionsFrame = mUI.MelFrameLayout(_subColumn, label='Actions', collapsable=False, collapse=True,useTemplate = 'cgmUIHeaderTemplate')
    
    self._actionsColumn = mUI.MelColumnLayout(self._actionsFrame,useTemplate = 'cgmUIHeaderTemplate') 
    
    uiFunc_buildActionsColumn(self)
    
    _row.setStretchWidget(_subColumn)

    mUI.MelSpacer(_row,w=_padding)

    _row.layout()
    #
    # End Actions Frame
    
    #uiFunc_setPostAction(self)

def uiFunc_buildActionsColumn(self):
    _str_func = 'uiFunc_buildActionsColumn[{0}]'.format(self.__class__.TOOLNAME)            
    log.info("|{0}| >>...".format(_str_func)) 

    self._actionsColumn.clear()
    self._actionFrames = []

    for i,action in enumerate(self._actionList):
        mc.setParent(self._actionsColumn)
        cgmUI.add_LineSubBreak()
        
        _row = mUI.MelHSingleStretchLayout(self._actionsColumn,ut='cgmUISubTemplate',padding = _padding)        
    
        mUI.MelSpacer(_row,w=_padding)
    
        _subColumn = mUI.MelColumnLayout(_row,useTemplate = 'cgmUIHeaderTemplate') 
    
        _frame = mUI.MelFrameLayout(_subColumn, label=action.filterType if action.name == None else "{0} - {1}".format(action.name, action.filterType), collapsable=True, collapse=True,useTemplate = 'cgmUIHeaderTemplate')
        
        pum = mUI.MelPopupMenu(_frame)
        mUI.MelMenuItem(pum, label="Rename", command=cgmGEN.Callback(uiFunc_rename_action,self,i) )
        mUI.MelMenuItem(pum, label="Copy", command=cgmGEN.Callback(uiFunc_copy_action,self,i) )
        mUI.MelMenuItem(pum, label="Paste", command=cgmGEN.Callback(uiFunc_paste_action,self,i) )
        mUI.MelMenuItem(pum, label="Duplicate", command=cgmGEN.Callback(uiFunc_duplicate_action,self,i) )
        mUI.MelMenuItem(pum, divider=True )
        mUI.MelMenuItem(pum, label="Move Up", command=cgmGEN.Callback(uiFunc_move_action,self,i,'up') )
        mUI.MelMenuItem(pum, label="Move Down", command=cgmGEN.Callback(uiFunc_move_action,self,i,'down') )
        mUI.MelMenuItem(pum, label="Move to Top", command=cgmGEN.Callback(uiFunc_move_action,self,i,'top') )
        mUI.MelMenuItem(pum, label="Move to Bottom", command=cgmGEN.Callback(uiFunc_move_action,self,i,'bottom') )
        mUI.MelMenuItem(pum, divider=True )
        mUI.MelMenuItem(pum, label="Delete", command=cgmGEN.Callback(uiFunc_remove_action,self,i) )
        mUI.MelMenuItem(pum, divider=True )
        mUI.MelMenuItem(pum, label="Run", command=cgmGEN.Callback(uiFunc_run_action,self,i) )

        _dataColumn = mUI.MelColumnLayout(_frame,useTemplate = 'cgmUIHeaderTemplate') 
        
        self._actionFrames.append(_frame)

        mc.evalDeferred( cgmGEN.Callback(action.build_column,_dataColumn) )
        
        _row.setStretchWidget(_subColumn)
        
        mUI.MelSpacer(_row,w=_padding)
    
        _row.layout()         
    
    mc.setParent(self._actionsColumn)
    cgmUI.add_LineSubBreak()      
    
    _row = mUI.MelHSingleStretchLayout(self._actionsColumn,ut='cgmUISubTemplate',padding = 5)
    
    mUI.MelSpacer(_row,w=_padding)
    
    _row.setStretchWidget( cgmUI.add_Button(_row,'Run',
        cgmGEN.Callback(uiFunc_run,self),                         
        #lambda *a: attrToolsLib.doAddAttributesToSelected(self),
        'Run',h=30) ) 
    
    mUI.MelSpacer(_row,w=_padding)

    _row.layout()    
    
    mc.setParent(self._actionsColumn)
    cgmUI.add_LineSubBreak()  

def uiFunc_run(self):
    _str_func = 'uiFunc_run[{0}]'.format(self.__class__.TOOLNAME)            
    log.info("|{0}| >>...".format(_str_func)) 

    uiFunc_updateActionDicts(self)

    for action in self._actionList:
        mc.select(action._optionDict['objs'])
        
        animLayerName = mc.animLayer(action.name)
        mc.setAttr( '{0}.rotationAccumulationMode'.format(animLayerName), 0)
        mc.setAttr( '{0}.scaleAccumulationMode'.format(animLayerName), 1)
        mc.animLayer( animLayerName, e=True, addSelectedObjects=True)

        for layer in mc.ls(type='animLayer'):
            mc.animLayer(layer, e=True, selected=(layer == animLayerName))

        action.run()

def uiFunc_run_action(self, idx):
    _str_func = 'uiFunc_run_action[{0}]'.format(self.__class__.TOOLNAME)            
    log.info("|{0}| >>...".format(_str_func)) 

    action = self._actionList[idx]

    mc.select(action._optionDict['objs'])
    
    animLayerName = mc.animLayer(action.name)
    mc.setAttr( '{0}.rotationAccumulationMode'.format(animLayerName), 0)
    mc.setAttr( '{0}.scaleAccumulationMode'.format(animLayerName), 1)
    mc.animLayer( animLayerName, e=True, addSelectedObjects=True)

    for layer in mc.ls(type='animLayer'):
        mc.animLayer(layer, e=True, selected=(layer == animLayerName))

    action.run()

def uiFunc_copy_action(self, idx):
    _str_func = 'uiFunc_copy_action[{0}]'.format(self.__class__.TOOLNAME)            
    log.info("|{0}| >>...".format(_str_func))

    self.clipboard = cgmMeta.cgmOptionVar("cgmVar_animFilter_clipboard", varType = "string")
    self.clipboard.setValue( json.dumps(self._actionList[idx]._optionDict) )

def uiFunc_paste_action(self, idx):
    _str_func = 'uiFunc_paste_action[{0}]'.format(self.__class__.TOOLNAME)            
    log.info("|{0}| >>...".format(_str_func)) 

    ignoreList = ['name', 'filterType']

    action = self._actionList[idx]

    self.clipboard = cgmMeta.cgmOptionVar("cgmVar_animFilter_clipboard", varType = "string")

    clipboard = self.clipboard.getValue()
    if clipboard:
        optionDict = json.loads(clipboard)

        for key in optionDict:
            if key in action._optionDict and key not in ignoreList:
                action._optionDict[key] = optionDict[key]

        mc.evalDeferred( cgmGEN.Callback(action.build_column,action._parentColumn) )


def uiFunc_duplicate_action(self, idx):
    _str_func = 'uiFunc_duplicate_action[{0}]'.format(self.__class__.TOOLNAME)            
    log.info("|{0}| >>...".format(_str_func)) 

    uiFunc_updateActionDicts(self)

    action = self._actionList[idx]   

    self._actionList.append( action_class[action._optionDict['filterType']](action._optionDict) )

    mc.evalDeferred( cgmGEN.Callback(uiFunc_buildActionsColumn,self) )

def uiFunc_save_actions(self):
    _str_func = 'uiFunc_save_actions[{0}]'.format(self.__class__.TOOLNAME)            
    log.info("|{0}| >>...".format(_str_func)) 

    if os.path.exists(self._loadedFile):
        uiFunc_updateActionDicts(self)

        f = open(self._loadedFile, 'w')
        f.write(json.dumps( [copy.copy(action._optionDict) for action in self._actionList] ))
        f.close()
    else:
        uiFunc_save_as_actions(self)

def uiFunc_save_as_actions(self):
    _str_func = 'uiFunc_save_actions[{0}]'.format(self.__class__.TOOLNAME)            
    log.info("|{0}| >>...".format(_str_func)) 

    uiFunc_updateActionDicts(self)

    basicFilter = "*.afs"
    filename = mc.fileDialog2(fileFilter=basicFilter, dialogStyle=2, fileMode=0)

    f = open(filename[0], 'w')
    f.write(json.dumps( [copy.copy(action._optionDict) for action in self._actionList] ))
    f.close()

    self._loadedFile = filename[0]

    mc.window(self, e=True, title="{0} - {1}".format(self.__class__.WINDOW_TITLE, filename[0]))

def uiFunc_load_actions(self):
    _str_func = 'uiFunc_load_actions[{0}]'.format(self.__class__.TOOLNAME)            
    log.info("|{0}| >>...".format(_str_func)) 

    basicFilter = "*.afs"
    filename = mc.fileDialog2(fileFilter=basicFilter, dialogStyle=2, fileMode=1)

    f = open(filename[0], 'r')
    actionDicts = json.loads(f.read())
    f.close()

    self._loadedFile = filename[0]

    mc.window(self, e=True, title="{0} - {1}".format(self.__class__.WINDOW_TITLE, filename[0]))

    self._actionList = []

    for data in actionDicts:
        if data['filterType'] in action_class:
            self._actionList.append( action_class[data['filterType']](data) )

    mc.evalDeferred( cgmGEN.Callback(uiFunc_buildActionsColumn,self) )

def uiFunc_rename_action(self, idx):
    _str_func = 'uiFunc_rename_action[{0}]'.format(self.__class__.TOOLNAME)            
    log.info("|{0}| >>...".format(_str_func)) 

    result = mc.promptDialog(
            title='Rename Action',
            message='Enter Name:',
            button=['OK', 'Cancel'],
            defaultButton='OK',
            cancelButton='Cancel',
            dismissString='Cancel')

    if result == 'OK':
        text = mc.promptDialog(query=True, text=True)
        self._actionList[idx].name = text
        self._actionFrames[idx](edit=True, label="{0} - {1}".format(text, self._actionList[idx].filterType)) 

def uiFunc_move_action(self, idx, direction):
    _str_func = 'uiFunc_move_action[{0}]'.format(self.__class__.TOOLNAME)            
    log.info("|{0}| >>...".format(_str_func)) 

    uiFunc_updateActionDicts(self)

    action = self._actionList.pop(idx)

    if direction == 'up':
        self._actionList.insert( max(idx-1,0), action )
    elif direction == 'down':
        self._actionList.insert( min(idx+1, len(self._actionList)), action )
    elif direction == 'top':
        self._actionList.insert(0, action)
    elif direction == 'bottom':
        self._actionList.append(action)

    mc.evalDeferred( cgmGEN.Callback(uiFunc_buildActionsColumn,self) )

def uiFunc_remove_action(self, idx):
    _str_func = 'uiFunc_remove_action[{0}]'.format(self.__class__.TOOLNAME)            
    log.info("|{0}| >>...".format(_str_func)) 

    self._actionList.pop(idx)

    mc.evalDeferred( cgmGEN.Callback(uiFunc_buildActionsColumn,self) )

def uiFunc_add_action(self):
    _str_func = 'uiFunc_add_action[{0}]'.format(self.__class__.TOOLNAME)            
    log.info("|{0}| >>...".format(_str_func)) 

    postAction = self.post_actionMenu.getValue().lower()

    action = action_class[postAction]()
    # if postAction == 'dragger':
    #     action = ui_post_dragger_column(self._optionDict)
    # elif postAction == 'spring':
    #     action = ui_post_spring_column(self._optionDict)
    # elif postAction == 'trajectory aim':
    #     action = ui_post_trajectory_aim_column(self._optionDict)
    # elif postAction == 'keyframe to motion curve':
    #     action = ui_post_keyframe_to_motion_curve_column(self._optionDict)

    self._actionList.append(action)

    uiFunc_updateActionDicts(self)
    mc.evalDeferred( cgmGEN.Callback(uiFunc_buildActionsColumn,self) )

# def uiFunc_setPostAction(self):
#     _str_func = 'uiFunc_setPostAction[{0}]'.format(self.__class__.TOOLNAME)            
#     log.info("|{0}| >>...".format(_str_func)) 

#     postAction = self.post_actionMenu.getValue()

#     if postAction == 'Dragger':
#         uiFunc_build_post_dragger_column(self)
#     elif postAction == 'Spring':
#         uiFunc_build_post_spring_column(self)
#     elif postAction == 'Trajectory Aim':
#         uiFunc_build_post_trajectory_aim_column(self)
#     elif postAction == 'Keys to Motion Curve':
#         uiFunc_build_post_keyframe_to_motion_curve_column(self)

def uiFunc_updateActionDicts(self):
    _str_func = 'uiFunc_updateActionDicts[{0}]'.format(self.__class__.TOOLNAME)            
    log.info("|{0}| >>...".format(_str_func))

    for action in self._actionList:
        action.update_dict()

class ui_post_filter(object):
    filterType = 'undefined'

    def __init__(self, optionDict = {
            'aimFwd' : 'z+',
            'aimUp' : 'y+',
            'translate' : True,
            'rotate' : True
        }):

        self._optionDict = copy.copy(optionDict)
        self.name = self._optionDict.get('name', None)

    def build_column(self, parentColumn):
        pass

    def run(self):
        pass

    def get_data(self):
        return None

    def update_dict(self):
        pass

    def uiFunc_set_translate(self):
        self._optionDict['translate'] = self.uiFF_translate.getValue()
        self.uiCL_translate(e=True, vis=self._optionDict['translate'])

    def uiFunc_set_rotate(self):
        self._optionDict['rotate'] = self.uiFF_rotate.getValue()
        self.uiCL_rotate(e=True, vis=self._optionDict['rotate'])

    def uiFunc_setPostAim(self):
        aimFwd = self.post_fwdMenu.getValue()
        aimUp = self.post_upMenu.getValue()

        if aimFwd[0] == aimUp[0]:
            log.error('Fwd and Up axis should be different or you may get unexpected results')
            self.post_fwdMenu(edit=True, bgc=[1,.35,.35])
            self.post_upMenu(edit=True, bgc=[1,.35,.35])
        else:
            self.post_fwdMenu(edit=True, bgc=[.35,.35,.35])
            self.post_upMenu(edit=True, bgc=[.35,.35,.35])

    def uiFunc_setObjects(self):
        if not hasattr(self, 'uiTF_objects'):
            return

        self._optionDict['objs'] = mc.ls(sl=True)
        self.uiTF_objects(edit=True, label=', '.join(mc.ls(sl=True)))

class ui_post_dragger_column(ui_post_filter):
    filterType = 'dragger'

    def build_column(self, parentColumn):
        self._parentColumn = parentColumn

        parentColumn.clear()

        mc.setParent(parentColumn)
        cgmUI.add_LineSubBreak()  

        # Objects
        #
        _row = mUI.MelHSingleStretchLayout(parentColumn,ut='cgmUISubTemplate',padding = 5)

        mUI.MelSpacer(_row,w=_padding)
        mUI.MelLabel(_row,l='Objects:')

        self.uiTF_objects = mUI.MelLabel(_row, ut='cgmUIInstructionsTemplate', l=', '.join(self._optionDict.get('objs', mc.ls(sl=True)))  )

        _row.setStretchWidget( self.uiTF_objects )

        cgmUI.add_Button(_row,'Set',
            cgmGEN.Callback(self.uiFunc_setObjects),
            'Set Objects')

        mUI.MelSpacer(_row,w=_padding)

        _row.layout()
        
        #
        # End Objects

        # Translate
        #
        _row = mUI.MelHSingleStretchLayout(parentColumn,ut='cgmUISubTemplate',padding = 5)

        mUI.MelSpacer(_row,w=_padding)
        mUI.MelLabel(_row,l='Translate:')

        _row.setStretchWidget( mUI.MelSeparator(_row) )

        self.uiFF_translate = mUI.MelCheckBox(_row, ut='cgmUISubTemplate', v=self._optionDict.get('translate', True), changeCommand=cgmGEN.Callback(self.uiFunc_set_translate))

        mUI.MelSpacer(_row,w=_padding)

        _row.layout()
        
        #
        # End Translate

        self.uiCL_translate = mUI.MelColumnLayout(parentColumn,useTemplate = 'cgmUISubTemplate') 
        
        # Post Damp
        #
        _row = mUI.MelHSingleStretchLayout(self.uiCL_translate,ut='cgmUISubTemplate',padding = 5)

        mUI.MelSpacer(_row,w=_padding)
        mUI.MelLabel(_row,l='Damp:')

        _row.setStretchWidget( mUI.MelSeparator(_row) )

        self.uiFF_post_damp = mUI.MelFloatField(_row, ut='cgmUISubTemplate', w= 50, v=self._optionDict.get('damp', 7.0))

        mUI.MelSpacer(_row,w=_padding)

        _row.layout()
        
        #
        # End Damp

        self.uiCL_translate(e=True, vis=self._optionDict['translate'])

        mc.setParent(parentColumn)
        cgmUI.add_LineSubBreak()  

        # Rotate
        #
        _row = mUI.MelHSingleStretchLayout(parentColumn,ut='cgmUISubTemplate',padding = 5)

        mUI.MelSpacer(_row,w=_padding)
        mUI.MelLabel(_row,l='Rotate:')

        _row.setStretchWidget( mUI.MelSeparator(_row) )

        self.uiFF_rotate = mUI.MelCheckBox(_row, ut='cgmUISubTemplate', v=self._optionDict.get('rotate', True), changeCommand=cgmGEN.Callback(self.uiFunc_set_rotate))

        mUI.MelSpacer(_row,w=_padding)

        _row.layout()
        
        #
        # End Rotate

        self.uiCL_rotate = mUI.MelColumnLayout(parentColumn,useTemplate = 'cgmUISubTemplate') 

        # Aim
        #
        _row = mUI.MelHSingleStretchLayout(self.uiCL_rotate,ut='cgmUISubTemplate',padding = 5)
        self._post_row_aimDirection = _row

        mUI.MelSpacer(_row,w=_padding)                          
        mUI.MelLabel(_row,l='Aim:')  

        _row.setStretchWidget( mUI.MelSeparator(_row) )

        directions = ['x+', 'x-', 'y+', 'y-', 'z+', 'z-']

        mUI.MelLabel(_row,l='Fwd:') 

        self.post_fwdMenu = mUI.MelOptionMenu(_row,useTemplate = 'cgmUITemplate', changeCommand=cgmGEN.Callback(self.uiFunc_setPostAim))
        for dir in directions:
            self.post_fwdMenu.append(dir)
        
        self.post_fwdMenu.setValue(self._optionDict.get('aimFwd', 'z+'))

        mUI.MelSpacer(_row,w=_padding)
        
        mUI.MelLabel(_row,l='Up:')

        self.post_upMenu = mUI.MelOptionMenu(_row,useTemplate = 'cgmUITemplate', changeCommand=cgmGEN.Callback(self.uiFunc_setPostAim))
        for dir in directions:
            self.post_upMenu.append(dir)

        self.post_upMenu.setValue(self._optionDict.get('aimUp', 'y+'))

        mUI.MelSpacer(_row,w=_padding)

        _row.layout()
        #
        # End Aim

        # Post Angular Damp
        #
        _row = mUI.MelHSingleStretchLayout(self.uiCL_rotate,ut='cgmUISubTemplate',padding = 5)

        mUI.MelSpacer(_row,w=_padding)
        mUI.MelLabel(_row,l='Angular Damp:')

        _row.setStretchWidget( mUI.MelSeparator(_row) )

        self.uiFF_post_angular_damp = mUI.MelFloatField(_row, ut='cgmUISubTemplate', w= 50, v=self._optionDict.get('angularDamp', 7.0))

        mUI.MelSpacer(_row,w=_padding)

        _row.layout()
        #
        # End Angular Damp

        mc.setParent(self.uiCL_rotate)
        cgmUI.add_LineSubBreak()  

        # Post Object Scale
        #
        _row = mUI.MelHSingleStretchLayout(self.uiCL_rotate,ut='cgmUISubTemplate',padding = 5)

        mUI.MelSpacer(_row,w=_padding)
        mUI.MelLabel(_row,l='Object Scale:')

        _row.setStretchWidget( mUI.MelSeparator(_row) )

        self.uiFF_post_object_scale = mUI.MelFloatField(_row, ut='cgmUISubTemplate', w= 50, v=self._optionDict.get('objectScale', 10.0))

        mUI.MelSpacer(_row,w=_padding)

        _row.layout()
        #
        # End Object Scale

        self.uiCL_rotate(e=True, vis=self._optionDict['rotate'])

        mc.setParent(parentColumn)
        cgmUI.add_LineSubBreak()  

        # Debug
        #
        _row = mUI.MelHSingleStretchLayout(parentColumn,ut='cgmUISubTemplate',padding = 5)

        mUI.MelSpacer(_row,w=_padding)

        mUI.MelLabel(_row,l='Additional Options:')

        _row.setStretchWidget( mUI.MelSeparator(_row) )

        mUI.MelLabel(_row,l='Debug:')

        self.uiCB_post_debug = mUI.MelCheckBox(_row,en=True,
                                   v = self._optionDict.get('debug', False),
                                   label = '',
                                   ann='Debug locators will not be deleted so you could see what happened')


        mUI.MelLabel(_row,l='Show Bake:')

        self.uiCB_post_show_bake = mUI.MelCheckBox(_row,en=True,
                                   v = self._optionDict.get('showBake', False),
                                   label = '',
                                   ann='Show the bake process')


        mUI.MelSpacer(_row,w=_padding)

        _row.layout()
        #
        # End Debug

        mc.setParent(parentColumn)
        cgmUI.add_LineSubBreak()  

    def get_data(self):
        self.update_dict()

        order = ['name',
            'filterType',
            'objs',
            'aimFwd',
            'aimUp',
            'damp',
            'angularDamp',
            'translate',
            'rotate',
            'objectScale',
            'debug',
            'showBake']

        data = [self._optionDict[x] for x in order]
        
        return data

    def update_dict(self):
        self._optionDict['name'] = self.name
        self._optionDict['filterType'] = self.filterType
        self._optionDict['objs'] = [x.strip() for x in self.uiTF_objects.getValue().split(',')] if hasattr(self, 'uiTF_objects') else []
        self._optionDict['aimFwd'] = self.post_fwdMenu.getValue() if hasattr(self, 'post_fwdMenu') else 'z+'
        self._optionDict['aimUp'] = self.post_upMenu.getValue() if hasattr(self, 'post_upMenu') else 'y+'
        self._optionDict['damp'] = self.uiFF_post_damp.getValue() if hasattr(self, 'uiFF_post_damp') else 7.0
        self._optionDict['angularDamp'] = self.uiFF_post_angular_damp.getValue() if hasattr(self, 'uiFF_post_angular_damp') else 7.0
        self._optionDict['translate'] = self.uiFF_translate.getValue() if hasattr(self, 'uiFF_translate') else True
        self._optionDict['rotate'] = self.uiFF_rotate.getValue() if hasattr(self, 'uiFF_rotate') else True
        self._optionDict['objectScale'] = self.uiFF_post_object_scale.getValue() if hasattr(self, 'uiFF_post_object_scale') else 10.0
        self._optionDict['debug'] = self.uiCB_post_debug.getValue() if hasattr(self, 'uiCB_post_debug') else False
        self._optionDict['showBake'] = self.uiCB_post_show_bake.getValue() if hasattr(self, 'uiCB_post_show_bake') else False

    def run(self):
        self.update_dict()

        for obj in self._optionDict['objs']:
            mc.select(obj)
            postInstance = DRAGGER.Dragger(aimFwd = self._optionDict['aimFwd'], aimUp = self._optionDict['aimUp'], damp = self._optionDict['damp'], angularDamp = self._optionDict['angularDamp'], translate=self._optionDict['translate'], rotate=self._optionDict['rotate'], objectScale=self._optionDict['objectScale'], debug=self._optionDict['debug'], showBake=self._optionDict['showBake'])
            postInstance.bake()


class ui_post_spring_column(ui_post_filter):
    filterType = 'spring'

    def build_column(self, parentColumn):
        self._parentColumn = parentColumn

        parentColumn.clear()

        mc.setParent(parentColumn)
        cgmUI.add_LineSubBreak()  

        # Objects
        #
        _row = mUI.MelHSingleStretchLayout(parentColumn,ut='cgmUISubTemplate',padding = 5)

        mUI.MelSpacer(_row,w=_padding)
        mUI.MelLabel(_row,l='Objects:')

        self.uiTF_objects = mUI.MelLabel(_row, ut='cgmUIInstructionsTemplate', l=', '.join(self._optionDict.get('objs', mc.ls(sl=True)))  )

        _row.setStretchWidget( self.uiTF_objects )

        cgmUI.add_Button(_row,'Set',
            cgmGEN.Callback(self.uiFunc_setObjects),
            'Set Objects')

        mUI.MelSpacer(_row,w=_padding)

        _row.layout()
        
        #
        # End Objects

        # Translate
        #
        _row = mUI.MelHSingleStretchLayout(parentColumn,ut='cgmUISubTemplate',padding = 5)

        mUI.MelSpacer(_row,w=_padding)
        mUI.MelLabel(_row,l='Translate:')

        _row.setStretchWidget( mUI.MelSeparator(_row) )

        self.uiFF_translate = mUI.MelCheckBox(_row, ut='cgmUISubTemplate', v=self._optionDict.get('translate', True), changeCommand=cgmGEN.Callback(self.uiFunc_set_translate))

        mUI.MelSpacer(_row,w=_padding)

        _row.layout()
        
        #
        # End Translate

        self.uiCL_translate = mUI.MelColumnLayout(parentColumn,useTemplate = 'cgmUISubTemplate') 

        # Spring
        #
        _row = mUI.MelHSingleStretchLayout(self.uiCL_translate,ut='cgmUISubTemplate',padding = 5)

        mUI.MelSpacer(_row,w=_padding)
        mUI.MelLabel(_row,l='Spring Force:')

        _row.setStretchWidget( mUI.MelSeparator(_row) )

        self.uiFF_post_spring = mUI.MelFloatField(_row, ut='cgmUISubTemplate', w= 50, v=self._optionDict.get('springForce', 1.0))

        mUI.MelSpacer(_row,w=_padding)

        _row.layout()
        #
        # End Spring

        mc.setParent(self.uiCL_translate)
        cgmUI.add_LineSubBreak()  

        # Post Damp
        #
        _row = mUI.MelHSingleStretchLayout(self.uiCL_translate,ut='cgmUISubTemplate',padding = 5)

        mUI.MelSpacer(_row,w=_padding)
        mUI.MelLabel(_row,l='Damp:')

        _row.setStretchWidget( mUI.MelSeparator(_row) )

        self.uiFF_post_damp = mUI.MelFloatField(_row, ut='cgmUISubTemplate', w= 50, v=self._optionDict.get('damp', .1))

        mUI.MelSpacer(_row,w=_padding)

        _row.layout()
        #
        # End Damp

        mc.setParent(parentColumn)
        cgmUI.add_LineSubBreak()  

        # Rotate
        #
        _row = mUI.MelHSingleStretchLayout(parentColumn,ut='cgmUISubTemplate',padding = 5)

        mUI.MelSpacer(_row,w=_padding)
        mUI.MelLabel(_row,l='Rotate:')

        _row.setStretchWidget( mUI.MelSeparator(_row) )

        self.uiFF_rotate = mUI.MelCheckBox(_row, ut='cgmUISubTemplate', v=self._optionDict.get('rotate', True), changeCommand=cgmGEN.Callback(self.uiFunc_set_rotate))

        mUI.MelSpacer(_row,w=_padding)

        _row.layout()
        
        #
        # End Rotate

        self.uiCL_rotate = mUI.MelColumnLayout(parentColumn,useTemplate = 'cgmUISubTemplate') 

        # Aim
        #
        _row = mUI.MelHSingleStretchLayout(self.uiCL_rotate,ut='cgmUISubTemplate',padding = 5)
        self._post_row_aimDirection = _row

        mUI.MelSpacer(_row,w=_padding)                          
        mUI.MelLabel(_row,l='Aim:')  

        _row.setStretchWidget( mUI.MelSeparator(_row) )

        directions = ['x+', 'x-', 'y+', 'y-', 'z+', 'z-']

        mUI.MelLabel(_row,l='Fwd:') 

        self.post_fwdMenu = mUI.MelOptionMenu(_row,useTemplate = 'cgmUITemplate', changeCommand=cgmGEN.Callback(self.uiFunc_setPostAim))
        for dir in directions:
            self.post_fwdMenu.append(dir)
        
        self.post_fwdMenu.setValue(self._optionDict.get('aimFwd', 'z+'))

        mUI.MelSpacer(_row,w=_padding)
        
        mUI.MelLabel(_row,l='Up:')

        self.post_upMenu = mUI.MelOptionMenu(_row,useTemplate = 'cgmUITemplate', changeCommand=cgmGEN.Callback(self.uiFunc_setPostAim))
        for dir in directions:
            self.post_upMenu.append(dir)

        self.post_upMenu.setValue(self._optionDict.get('aimUp', 'y+'))

        mUI.MelSpacer(_row,w=_padding)

        _row.layout()
        #
        # End Aim

        # Angular Spring
        #
        _row = mUI.MelHSingleStretchLayout(self.uiCL_rotate,ut='cgmUISubTemplate',padding = 5)

        mUI.MelSpacer(_row,w=_padding)
        mUI.MelLabel(_row,l='Angular Spring Force:')

        _row.setStretchWidget( mUI.MelSeparator(_row) )

        self.uiFF_post_angular_spring = mUI.MelFloatField(_row, ut='cgmUISubTemplate', w= 50, v=self._optionDict.get('angularSpringForce', 1.0))

        mUI.MelSpacer(_row,w=_padding)

        _row.layout()
        #
        # End Angular Spring

        mc.setParent(self.uiCL_rotate)
        cgmUI.add_LineSubBreak()  

        # Post Angular Damp
        #
        _row = mUI.MelHSingleStretchLayout(self.uiCL_rotate,ut='cgmUISubTemplate',padding = 5)

        mUI.MelSpacer(_row,w=_padding)
        mUI.MelLabel(_row,l='Angular Damp:')

        _row.setStretchWidget( mUI.MelSeparator(_row) )

        self.uiFF_post_angular_damp = mUI.MelFloatField(_row, ut='cgmUISubTemplate', w= 50, v=self._optionDict.get('angularDamp', .1))

        mUI.MelSpacer(_row,w=_padding)

        _row.layout()
        #
        # End Angular Damp

        # Angular Up Spring
        #
        _row = mUI.MelHSingleStretchLayout(self.uiCL_rotate,ut='cgmUISubTemplate',padding = 5)

        mUI.MelSpacer(_row,w=_padding)
        mUI.MelLabel(_row,l='Angular Up Spring Force:')

        _row.setStretchWidget( mUI.MelSeparator(_row) )

        self.uiFF_post_angular_up_spring = mUI.MelFloatField(_row, ut='cgmUISubTemplate', w= 50, v=self._optionDict.get('angularUpSpringForce', 1.0))

        mUI.MelSpacer(_row,w=_padding)

        _row.layout()
        #
        # Angular Up Spring

        mc.setParent(self.uiCL_rotate)
        cgmUI.add_LineSubBreak()  

        # Post Angular Up Damp
        #
        _row = mUI.MelHSingleStretchLayout(self.uiCL_rotate,ut='cgmUISubTemplate',padding = 5)

        mUI.MelSpacer(_row,w=_padding)
        mUI.MelLabel(_row,l='Angular Up Damp:')

        _row.setStretchWidget( mUI.MelSeparator(_row) )

        self.uiFF_post_angular_up_damp = mUI.MelFloatField(_row, ut='cgmUISubTemplate', w= 50, v=self._optionDict.get('angularUpDamp', .1))

        mUI.MelSpacer(_row,w=_padding)

        _row.layout()
        #
        # End Post Angular Up Damp

        mc.setParent(self.uiCL_rotate)
        cgmUI.add_LineSubBreak()  

        # Post Object Scale
        #
        _row = mUI.MelHSingleStretchLayout(self.uiCL_rotate,ut='cgmUISubTemplate',padding = 5)

        mUI.MelSpacer(_row,w=_padding)
        mUI.MelLabel(_row,l='Object Scale:')

        _row.setStretchWidget( mUI.MelSeparator(_row) )

        self.uiFF_post_object_scale = mUI.MelFloatField(_row, ut='cgmUISubTemplate', w= 50, v=self._optionDict.get('objectScale', 10.0))

        mUI.MelSpacer(_row,w=_padding)

        _row.layout()
        #
        # End Object Scale

        mc.setParent(parentColumn)
        cgmUI.add_LineSubBreak()  

        # Debug
        #
        _row = mUI.MelHSingleStretchLayout(parentColumn,ut='cgmUISubTemplate',padding = 5)

        mUI.MelSpacer(_row,w=_padding)

        mUI.MelLabel(_row,l='Additional Options:')

        _row.setStretchWidget( mUI.MelSeparator(_row) )

        mUI.MelLabel(_row,l='Debug:')

        self.uiCB_post_debug = mUI.MelCheckBox(_row,en=True,
                                   v = self._optionDict.get('debug', False),
                                   label = '',
                                   ann='Debug locators will not be deleted so you could see what happened')


        mUI.MelLabel(_row,l='Show Bake:')

        self.uiCB_post_show_bake = mUI.MelCheckBox(_row,en=True,
                                   v = self._optionDict.get('showBake', False),
                                   label = '',
                                   ann='Show the bake process')


        mUI.MelSpacer(_row,w=_padding)

        _row.layout()
        #
        # End Debug

        mc.setParent(parentColumn)
        cgmUI.add_LineSubBreak()  

        self.uiCL_translate(e=True, vis=self._optionDict['translate'])
        self.uiCL_rotate(e=True, vis=self._optionDict['rotate'])


    def get_data(self):
        self.update_dict()

        order = ['name',
                'filterType',
                'objs',
                'aimFwd',
                'aimUp',
                'damp',
                'springForce',
                'angularDamp',
                'angularSpringForce',
                'angularUpDamp',
                'angularUpSpringForce',
                'objectScale',
                'translate',
                'rotate',
                'debug',
                'showBake']

        data = [self._optionDict[x] for x in order]
        
        return data

    def update_dict(self):
        self._optionDict['name'] = self.name
        self._optionDict['filterType'] = self.filterType
        self._optionDict['objs'] = [x.strip() for x in self.uiTF_objects.getValue().split(',')] if hasattr(self, 'uiTF_objects') else []
        self._optionDict['aimFwd'] = self.post_fwdMenu.getValue() if hasattr(self, 'post_fwdMenu') else 'z+'
        self._optionDict['aimUp'] = self.post_upMenu.getValue() if hasattr(self, 'post_upMenu') else 'y+'
        self._optionDict['damp'] = self.uiFF_post_damp.getValue() if hasattr(self, 'uiFF_post_damp') else .3
        self._optionDict['springForce'] = self.uiFF_post_spring.getValue() if hasattr(self, 'uiFF_post_spring') else 12.0
        self._optionDict['angularDamp'] = self.uiFF_post_angular_damp.getValue() if hasattr(self, 'uiFF_post_angular_damp') else .3
        self._optionDict['angularSpringForce'] = self.uiFF_post_angular_spring.getValue() if hasattr(self, 'uiFF_post_angular_spring') else 12.0
        self._optionDict['angularUpDamp'] = self.uiFF_post_angular_up_damp.getValue() if hasattr(self, 'uiFF_post_angular_up_damp') else .3
        self._optionDict['angularUpSpringForce'] = self.uiFF_post_angular_up_spring.getValue() if hasattr(self, 'uiFF_post_angular_up_spring') else 12.0
        self._optionDict['translate'] = self.uiFF_translate.getValue() if hasattr(self, 'uiFF_translate') else True
        self._optionDict['rotate'] = self.uiFF_rotate.getValue() if hasattr(self, 'uiFF_rotate') else True
        self._optionDict['objectScale'] = self.uiFF_post_object_scale.getValue() if hasattr(self, 'uiFF_post_object_scale') else 10.0
        self._optionDict['debug'] = self.uiCB_post_debug.getValue() if hasattr(self, 'uiCB_post_debug') else False
        self._optionDict['showBake'] = self.uiCB_post_show_bake.getValue() if hasattr(self, 'uiCB_post_show_bake') else False


    def run(self):
        self.update_dict()

        for obj in self._optionDict['objs']:
            mc.select(obj)
            postInstance = SPRING.Spring(aimFwd = self._optionDict['aimFwd'], aimUp = self._optionDict['aimUp'], damp = self._optionDict['damp'], springForce=self._optionDict['springForce'], angularDamp = self._optionDict['angularDamp'], angularSpringForce = self._optionDict['angularSpringForce'], angularUpDamp = self._optionDict['angularUpDamp'], angularUpSpringForce = self._optionDict['angularUpSpringForce'],objectScale=self._optionDict['objectScale'], translate=self._optionDict['translate'], rotate=self._optionDict['rotate'],debug=self._optionDict['debug'], showBake=self._optionDict['showBake'])
            postInstance.bake()

class ui_post_trajectory_aim_column(ui_post_filter):
    filterType = 'trajectory aim'

    def build_column(self, parentColumn):
        self._parentColumn = parentColumn

        parentColumn.clear()

        mc.setParent(parentColumn)
        cgmUI.add_LineSubBreak()  

        # Objects
        #
        _row = mUI.MelHSingleStretchLayout(parentColumn,ut='cgmUISubTemplate',padding = 5)

        mUI.MelSpacer(_row,w=_padding)
        mUI.MelLabel(_row,l='Objects:')

        self.uiTF_objects = mUI.MelLabel(_row, ut='cgmUIInstructionsTemplate', l=', '.join(self._optionDict.get('objs', mc.ls(sl=True)))  )

        _row.setStretchWidget( self.uiTF_objects )

        cgmUI.add_Button(_row,'Set',
            cgmGEN.Callback(self.uiFunc_setObjects),
            'Set Objects')

        mUI.MelSpacer(_row,w=_padding)

        _row.layout()
        
        #
        # End Objects

        # Aim
        #
        _row = mUI.MelHSingleStretchLayout(parentColumn,ut='cgmUISubTemplate',padding = 5)
        self._post_row_aimDirection = _row

        mUI.MelSpacer(_row,w=_padding)                          
        mUI.MelLabel(_row,l='Aim:')  

        _row.setStretchWidget( mUI.MelSeparator(_row) )

        directions = ['x+', 'x-', 'y+', 'y-', 'z+', 'z-']

        mUI.MelLabel(_row,l='Fwd:') 

        self.post_fwdMenu = mUI.MelOptionMenu(_row,useTemplate = 'cgmUITemplate', changeCommand=cgmGEN.Callback(self.uiFunc_setPostAim))
        for dir in directions:
            self.post_fwdMenu.append(dir)
        
        self.post_fwdMenu.setValue(self._optionDict.get('aimFwd', 'z+'))

        mUI.MelSpacer(_row,w=_padding)
        
        mUI.MelLabel(_row,l='Up:')

        self.post_upMenu = mUI.MelOptionMenu(_row,useTemplate = 'cgmUITemplate', changeCommand=cgmGEN.Callback(self.uiFunc_setPostAim))
        for dir in directions:
            self.post_upMenu.append(dir)

        self.post_upMenu.setValue(self._optionDict.get('aimUp', 'y+'))

        mUI.MelSpacer(_row,w=_padding)

        _row.layout()
        #
        # End Aim

        # Post Damp
        #
        _row = mUI.MelHSingleStretchLayout(parentColumn,ut='cgmUISubTemplate',padding = 5)

        mUI.MelSpacer(_row,w=_padding)
        mUI.MelLabel(_row,l='Damp:')

        _row.setStretchWidget( mUI.MelSeparator(_row) )

        self.uiFF_post_damp = mUI.MelFloatField(_row, ut='cgmUISubTemplate', w= 50, v=self._optionDict.get('damp', 10.0))

        mUI.MelSpacer(_row,w=_padding)

        _row.layout()
        #
        # End Damp

        mc.setParent(parentColumn)
        cgmUI.add_LineSubBreak()  

        # Debug
        #
        _row = mUI.MelHSingleStretchLayout(parentColumn,ut='cgmUISubTemplate',padding = 5)

        mUI.MelSpacer(_row,w=_padding)
        mUI.MelLabel(_row,l='Show Bake:')

        _row.setStretchWidget( mUI.MelSeparator(_row) )   

        self.uiCB_post_show_bake = mUI.MelCheckBox(_row,en=True,
                                   v = self._optionDict.get('debug', False),
                                   label = '',
                                   ann='Show the bake process')


        mUI.MelSpacer(_row,w=_padding)

        _row.layout()
        #
        # End Debug

        mc.setParent(parentColumn)
        cgmUI.add_LineSubBreak()  

    def get_data(self):
        self.update_dict()

        order = ['name',
                'filterType',
                'objs',
                'aimFwd',
                'aimUp',
                'damp',
                'showBake']

        data = [self._optionDict[x] for x in order]
        
        return data

    def update_dict(self):
        self._optionDict['name'] = self.name
        self._optionDict['filterType'] = self.filterType
        self._optionDict['objs'] = [x.strip() for x in self.uiTF_objects.getValue().split(',')] if hasattr(self, 'uiTF_objects') else []
        self._optionDict['aimFwd'] = self.post_fwdMenu.getValue() if hasattr(self, 'post_fwdMenu') else 'z+'
        self._optionDict['aimUp'] = self.post_upMenu.getValue() if hasattr(self, 'post_upMenu') else 'y+'
        self._optionDict['damp'] = self.uiFF_post_damp.getValue() if hasattr(self, 'uiFF_post_damp') else .3
        self._optionDict['showBake'] = self.uiCB_post_show_bake.getValue() if hasattr(self, 'uiCB_post_show_bake') else False

    def run(self):
        self.update_dict()

        for obj in self._optionDict['objs']:
            mc.select(obj)
            postInstance = TRAJECTORYAIM.TrajectoryAim(aimFwd = self._optionDict['aimFwd'], aimUp = self._optionDict['aimUp'], damp = self._optionDict['damp'], showBake=self._optionDict['showBake'])
            postInstance.bake()

class ui_post_keyframe_to_motion_curve_column(ui_post_filter):
    filterType = 'keyframe to motion curve'

    def build_column(self, parentColumn):
        self._parentColumn = parentColumn

        parentColumn.clear()

        mc.setParent(parentColumn)
        cgmUI.add_LineSubBreak()  

        # Objects
        #
        _row = mUI.MelHSingleStretchLayout(parentColumn,ut='cgmUISubTemplate',padding = 5)

        mUI.MelSpacer(_row,w=_padding)
        mUI.MelLabel(_row,l='Objects:')

        self.uiTF_objects = mUI.MelLabel(_row, ut='cgmUIInstructionsTemplate', l=', '.join(self._optionDict.get('objs', mc.ls(sl=True)))  )

        _row.setStretchWidget( self.uiTF_objects )

        cgmUI.add_Button(_row,'Set',
            cgmGEN.Callback(self.uiFunc_setObjects),
            'Set Objects')

        mUI.MelSpacer(_row,w=_padding)

        _row.layout()
        
        #
        # End Objects

        # Debug
        #
        _row = mUI.MelHSingleStretchLayout(parentColumn,ut='cgmUISubTemplate',padding = 5)

        mUI.MelSpacer(_row,w=_padding)

        mUI.MelLabel(_row,l='Additional Options:')

        _row.setStretchWidget( mUI.MelSeparator(_row) )

        mUI.MelLabel(_row,l='Debug:')

        self.uiCB_post_debug = mUI.MelCheckBox(_row,en=True,
                                   v = self._optionDict.get('debug', False),
                                   label = '',
                                   ann='Debug locators will not be deleted so you could see what happened')


        mUI.MelLabel(_row,l='Show Bake:')

        self.uiCB_post_show_bake = mUI.MelCheckBox(_row,en=True,
                                   v = self._optionDict.get('showBake', False),
                                   label = '',
                                   ann='Show the bake process')


        mUI.MelSpacer(_row,w=_padding)

        _row.layout()
        #
        # End Debug

        mc.setParent(parentColumn)
        cgmUI.add_LineSubBreak()  

    def get_data(self):
        self.update_dict()

        order = ['name',
                'filterType',
                'objs',
                'debug',
                'showBake']

        data = [self._optionDict[x] for x in order]
        
        return data

    def update_dict(self):
        self._optionDict['name'] = self.name
        self._optionDict['filterType'] = self.filterType
        self._optionDict['objs'] = [x.strip() for x in self.uiTF_objects.getValue().split(',')] if hasattr(self, 'uiTF_objects') else []
        self._optionDict['debug'] = self.uiCB_post_debug.getValue() if hasattr(self, 'uiCB_post_debug') else False
        self._optionDict['showBake'] = self.uiCB_post_show_bake.getValue() if hasattr(self, 'uiCB_post_show_bake') else False


    def run(self):
        self.update_dict()

        for obj in self._optionDict['objs']:
            mc.select(obj)
            postInstance = K2MC.KeyframeToMotionCurve(debug=self._optionDict['debug'], showBake=self._optionDict['showBake'])
            postInstance.bake()

# def uiFunc_add_dragger_action(self):
#     self._actionList.append( uiFunc_get_dragger_data(self) )
#     uiFunc_buildActionsColumn(self)

# def uiFunc_add_spring_action(self):
#     self._actionList.append( uiFunc_get_spring_data(self) )
#     uiFunc_buildActionsColumn(self)

# def uiFunc_add_trajectory_aim_action(self):
#     self._actionList.append( uiFunc_get_trajectory_aim_data(self) )
#     uiFunc_buildActionsColumn(self)

# def uiFunc_add_keyframe_to_motion_curve_action(self):
#     self._actionList.append( uiFunc_get_keyframe_to_motion_curve_data(self) )
#     uiFunc_buildActionsColumn(self)

action_class = {
    'dragger':ui_post_dragger_column,
    'spring':ui_post_spring_column,
    'trajectory aim':ui_post_trajectory_aim_column,
    'keyframe to motion curve':ui_post_keyframe_to_motion_curve_column
}