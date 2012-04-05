#=================================================================================================================================================
#=================================================================================================================================================
#	attrTools - a part of cgmTools
#=================================================================================================================================================
#=================================================================================================================================================
#
# DESCRIPTION:
#   Gui Tool for attribute tools
#
# REQUIRES:
#   Maya
#
# AUTHOR:
# 	Josh Burton (under the supervision of python guru (and good friend) David Bokser) - jjburton@gmail.com
#	http://www.cgmonks.com
# 	Copyright 2011 CG Monks - All Rights Reserved.
#
#
#=================================================================================================================================================
__version__ = '0.1.03292012'


import maya.mel as mel
import maya.cmds as mc

from cgm.lib.zoo.zooPyMaya.baseMelUI import *

from cgm.lib import (guiFactory,
                     dictionary,
                     search)

from cgm.tools.lib import (tdToolsLib,
                           locinatorLib,
                           attrToolsLib)

reload(tdToolsLib)
reload(attrToolsLib)

def run():
	attrToolsClass()

class attrToolsClass(BaseMelWindow):
	WINDOW_NAME = 'attrTools'
	WINDOW_TITLE = 'cgm.attrTools'
	DEFAULT_SIZE = 350, 400
	DEFAULT_MENU = None
	RETAIN = True
	MIN_BUTTON = True
	MAX_BUTTON = False
	FORCE_DEFAULT_SIZE = True  #always resets the size of the window when its re-created
	guiFactory.initializeTemplates()

	def __init__( self):
		# Maya version check
		if mayaVer >= 2011:
			self.currentGen = True
		else:
			self.currentGen = False
		# Basic variables
		self.window = ''
		self.activeTab = ''
		self.toolName = 'attrTools'
		self.module = 'tdTools'
		self.winName = 'attrToolsWin'

		self.showHelp = False
		self.helpBlurbs = []
		self.oldGenBlurbs = []

		self.showTimeSubMenu = False
		self.timeSubMenu = []

		# About Window
		self.description = 'Tools for working with attributes'
		self.author = 'Josh Burton'
		self.owner = 'CG Monks'
		self.website = 'www.cgmonks.com'
		self.version = __version__

		# About Window

		#>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
		# Build
		#>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

		#Menu
		self.UI_HelpMenu = MelMenu( l='Help', pmc=self.buildHelpMenu)

		MainColumn = MelColumnLayout(self)

		self.buildAttributeTool(MainColumn)
		
		self.show()




	#>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
	# Menus
	#>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
	def buildHelpMenu(self, *a ):
		self.UI_HelpMenu.clear()
		ShowHelpOption = mc.optionVar( q='cgmVarTDToolsShowHelp' )
		MelMenuItem( self.UI_HelpMenu, l="Show Help",
				     cb=ShowHelpOption,
				     c= lambda *a: self.do_showHelpToggle())
		MelMenuItem( self.UI_HelpMenu, l="Print Tools Help",
				     c=lambda *a: self.printHelp() )

		MelMenuItemDiv( self.UI_HelpMenu )
		MelMenuItem( self.UI_HelpMenu, l="About",
				     c=lambda *a: self.showAbout() )

	def do_showHelpToggle(self):
		ShowHelpOption = mc.optionVar( q='cgmVarTDToolsShowHelp' )
		guiFactory.toggleMenuShowState(ShowHelpOption,self.helpBlurbs)
		mc.optionVar( iv=('cgmVarTDToolsShowHelp', not ShowHelpOption))


	def showAbout(self):
		window = mc.window( title="About", iconName='About', ut = 'cgmUITemplate',resizeToFitChildren=True )
		mc.columnLayout( adjustableColumn=True )
		guiFactory.header(self.toolName,overrideUpper = True)
		mc.text(label='>>>A Part of the cgmTools Collection<<<', ut = 'cgmUIInstructionsTemplate')
		guiFactory.headerBreak()
		guiFactory.lineBreak()
		descriptionBlock = guiFactory.textBlock(self.description)

		guiFactory.lineBreak()
		mc.text(label=('%s%s' %('Written by: ',self.author)))
		mc.text(label=('%s%s%s' %('Copyright ',self.owner,', 2011')))
		guiFactory.lineBreak()
		mc.text(label='Version: %s' % self.version)
		mc.text(label='')
		guiFactory.doButton('Visit Website', 'import webbrowser;webbrowser.open("http://www.cgmonks.com")')
		guiFactory.doButton('Close', 'import maya.cmds as mc;mc.deleteUI(\"' + window + '\", window=True)')
		mc.setParent( '..' )
		mc.showWindow( window )

	def printHelp(self):
		import tdToolsLib
		help(tdToolsLib)

	
	#>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
	# Tools
	#>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
	def buildAttributeTool(self,parent,vis=True):
		OptionList = ['Tools','Manager','Utilities']
		cgmVarName = 'cgmAttributeMode'
		RadioCollectionName ='AttributeMode'
		RadioOptionList = 'AttributeModeSelectionChoicesList'

		ShowHelpOption = mc.optionVar( q='cgmVarTDToolsShowHelp' )
		
		if not mc.optionVar( ex=cgmVarName ):
			mc.optionVar( sv=(cgmVarName, OptionList[0]) )
		
		MelSeparator(parent,ut = 'cgmUIHeaderTemplate',h=5)
		
		#Mode Change row 
		ModeSetRow = MelHLayout(parent,ut='cgmUISubTemplate',padding = 5)
		MelLabel(ModeSetRow, label = 'Choose Mode: ',align='right')
		self.RadioCollectionName = MelRadioCollection()
		self.RadioOptionList = []		

		#build our sub section options
		self.ContainerList = []

		self.ContainerList.append( self.buildAttributeEditingTool(parent,vis=False) )
		self.ContainerList.append( self.buildAttributeManagerTool( parent,vis=False) )
		self.ContainerList.append( self.buildAttributeUtilitiesTool( parent,vis=False) )
		
		for item in OptionList:
			self.RadioOptionList.append(self.RadioCollectionName.createButton(ModeSetRow,label=item,
						                                                      onCommand = Callback(guiFactory.toggleModeState,item,OptionList,cgmVarName,self.ContainerList)))
		ModeSetRow.layout()


		mc.radioCollection(self.RadioCollectionName,edit=True, sl=self.RadioOptionList[OptionList.index(mc.optionVar(q=cgmVarName))])

		
		
	def buildAttributeEditingTool(self,parent, vis=True):
		#Container
		containerName = 'Attributes Constainer'
		self.containerName = MelColumn(parent,vis=vis)
		
		###Create
		mc.setParent(self.containerName)
		guiFactory.header('Create')
		guiFactory.lineSubBreak()
		
		#>>>Create Row
		attrCreateRow = MelHSingleStretchLayout(self.containerName,ut='cgmUISubTemplate',padding = 5)
		MelSpacer(attrCreateRow)

		MelLabel(attrCreateRow,l='Names:',align='right')
		self.AttrNamesTextField = MelTextField(attrCreateRow,backgroundColor = [1,1,1],
		                                       annotation = "Names for the attributes. Create multiple with a ';'. \n Message nodes try to connect to the last object in a selection \n For example: 'Test1;Test2;Test3'")
		guiFactory.doButton2(attrCreateRow,'Add',
		                     lambda *a: attrToolsLib.doAddAttributesToSelected(self),
		                     "Add the attribute names from the text field")
		MelSpacer(attrCreateRow,w=2)

		attrCreateRow.setStretchWidget(self.AttrNamesTextField)
		attrCreateRow.layout()
		
		
		#>>> asf
		self.buildAttrTypeRow(self.containerName)
		MelSeparator(self.containerName,ut = 'cgmUIHeaderTemplate',h=3)
		MelSeparator(self.containerName,ut = 'cgmUITemplate',h=10)
		
		###Modify
		mc.setParent(self.containerName)
		guiFactory.header('Modify')
		guiFactory.lineSubBreak()
		
		#>>> Load To Field
		#clear our variables
		if not mc.optionVar( ex='cgmVarAttributeSourceObject' ):
			mc.optionVar( sv=('cgmVarAttributeSourceObject', '') )
	
		LoadAttributeObjectRow = MelHSingleStretchLayout(self.containerName ,ut='cgmUISubTemplate',padding = 5)
	
		MelSpacer(LoadAttributeObjectRow,w=5)
		
		guiFactory.doButton2(LoadAttributeObjectRow,'>>',
	                        lambda *a:attrToolsLib.uiLoadSourceObject(self),
	                         'Load to field')
		
		self.SourceObjectField = MelTextField(LoadAttributeObjectRow, w= 125, ut = 'cgmUIReservedTemplate', editable = False)
	
		LoadAttributeObjectRow.setStretchWidget(self.SourceObjectField  )
		
		MelLabel(LoadAttributeObjectRow, l=' . ')
		self.ObjectAttributesOptionMenu = MelOptionMenu(LoadAttributeObjectRow)
	
		guiFactory.doButton2(LoadAttributeObjectRow,'X',
	                        lambda *a:attrToolsLib.uiDeleteAttr(self,self.ObjectAttributesOptionMenu),
		                    'Delete attribute',
		                    w = 25)
	
		MelSpacer(LoadAttributeObjectRow,w=5)
	
		LoadAttributeObjectRow.layout()
	
	
		mc.setParent(self.containerName)
		guiFactory.lineSubBreak()


		#>>> Standard Flags
		BasicAttrFlagsRow = MelHLayout(self.containerName ,ut='cgmUISubTemplate',padding = 2)
		MelSpacer(BasicAttrFlagsRow,w=5)
		self.KeyableAttrCB = MelCheckBox(BasicAttrFlagsRow,label = 'Keyable')
		MelSpacer(BasicAttrFlagsRow,w=5)
		self.HiddenAttrCB = MelCheckBox(BasicAttrFlagsRow,label = 'Hidden')
		MelSpacer(BasicAttrFlagsRow,w=5)
		self.LockedAttrCB = MelCheckBox(BasicAttrFlagsRow,label = 'Locked')
		MelSpacer(BasicAttrFlagsRow,w=5)
		BasicAttrFlagsRow.layout()
		
		#>>> Int Row
		EditDigitSettingsRow = MelHLayout(self.containerName,ut='cgmUISubTemplate',padding = 5)
		MelLabel(EditDigitSettingsRow,label = 'Settings: ')
		self.MinField = MelTextField(EditDigitSettingsRow,
		                             enable = False,
		                             text = 'Min',
		                             bgc = dictionary.returnStateColor('normal'),
		                             ec = lambda *a: tdToolsLib.uiUpdateAutoNameTag(self,'cgmPosition'),
		                             w = 50)
		self.MaxField = MelTextField(EditDigitSettingsRow,
		                             enable = False,
		                             text = 'Max',
		                             bgc = dictionary.returnStateColor('normal'),
		                             ec = lambda *a: tdToolsLib.uiUpdateAutoNameTag(self,'cgmDirection'),
		                             w = 50)
		self.DefaultField = MelTextField(EditDigitSettingsRow,
		                                 enable = False,
		                                 text = 'Default',
		                                 bgc = dictionary.returnStateColor('normal'),
		                                 ec = lambda *a: tdToolsLib.uiUpdateAutoNameTag(self,'cgmName'),
		                                 w = 50)
		MelSpacer(EditDigitSettingsRow,w=5)
		EditDigitSettingsRow.layout()
		
		#>>> Enum
		MelSeparator(self.containerName,ut='cgmUISubTemplate',h=5)
		EditEnumRow = MelHSingleStretchLayout(self.containerName,ut='cgmUISubTemplate',padding = 5)
		MelSpacer(EditEnumRow,w=10)
		MelLabel(EditEnumRow,label = 'Enum: ')
		self.EnumField = MelTextField(EditEnumRow,
		                                enable = False,
		                                bgc = dictionary.returnStateColor('normal'),
		                                ec = lambda *a: tdToolsLib.uiUpdateAutoNameTag(self,'cgmPosition'),
		                                w = 75)
		MelSpacer(EditEnumRow,w=10)
		EditEnumRow.setStretchWidget(self.EnumField)
		
		EditEnumRow.layout()
		
		#>>> String
		MelSeparator(self.containerName,ut='cgmUISubTemplate',h=5)
		EditStringRow = MelHSingleStretchLayout(self.containerName,ut='cgmUISubTemplate',padding = 5)
		MelSpacer(EditStringRow,w=10)
		MelLabel(EditStringRow,label = 'String: ')
		self.StringField = MelTextField(EditStringRow,
		                                enable = False,
		                                bgc = dictionary.returnStateColor('normal'),
		                                ec = lambda *a: tdToolsLib.uiUpdateAutoNameTag(self,'cgmPosition'),
		                                w = 75)
		MelSpacer(EditStringRow,w=10)
		EditStringRow.setStretchWidget(self.StringField)
		
		EditStringRow.layout()
		
		#>>> Message
		MelSeparator(self.containerName,ut='cgmUISubTemplate',h=5)
		EditMessageRow = MelHSingleStretchLayout(self.containerName,ut='cgmUISubTemplate',padding = 5)
		MelSpacer(EditMessageRow,w=10)
		MelLabel(EditMessageRow,label = 'Message: ')
		self.MessageField = MelTextField(EditMessageRow,
		                                enable = False,
		                                bgc = dictionary.returnStateColor('normal'),
		                                ec = lambda *a: tdToolsLib.uiUpdateAutoNameTag(self,'cgmPosition'),
		                                w = 75)
		guiFactory.doButton2(EditMessageRow,'<<',
	                        lambda *a:attrToolsLib.uiLoadSourceObject(self),
	                         'Load to field')
		MelSpacer(EditMessageRow,w=10)
		EditMessageRow.setStretchWidget(self.MessageField)

		EditMessageRow.layout()
		
		
		mc.setParent(self.containerName )
		guiFactory.lineSubBreak()
		guiFactory.lineBreak()

		
		#>>> Basic
		mc.setParent(self.containerName )
		guiFactory.header('Connect')
		guiFactory.doButton2(self.containerName,'Select an attr',
	                        lambda *a: attrToolsLib.uiSelectAttrMenu(self,'test'),
		                    'Delete attribute')		
		guiFactory.lineSubBreak()

			
		return self.containerName
	
	def buildAttrTypeRow(self,parent):	
		#>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
		# Attr type row
		#>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
		attrTypes = ['string','float','int','vector','bool','enum','message']
		attrShortTypes = ['str','float','int','[000]','bool','enum','msg']

		self.CreateAttrTypeRadioCollection = MelRadioCollection()
		self.CreateAttrTypeRadioCollectionChoices = []		
		if not mc.optionVar( ex='cgmAttrCreateType' ):
			mc.optionVar( sv=('cgmAttrCreateType', 'string') )
			
		#build our sub section options
		AttrTypeRow = MelHLayout(self.containerName,ut='cgmUISubTemplate',padding = 5)
		for item in attrTypes:
			cnt = attrTypes.index(item)
			self.CreateAttrTypeRadioCollectionChoices.append(self.CreateAttrTypeRadioCollection.createButton(AttrTypeRow,label=attrShortTypes[cnt],
			                                                                                                 onCommand = ('%s%s%s' %("mc.optionVar( sv=('cgmAttrCreateType','",item,"'))"))))
			MelSpacer(AttrTypeRow,w=2)

		mc.radioCollection(self.CreateAttrTypeRadioCollection ,edit=True,sl= (self.CreateAttrTypeRadioCollectionChoices[ attrTypes.index(mc.optionVar(q='cgmAttrCreateType')) ]))
		
		AttrTypeRow.layout()
		"""
		AttrLabelRow = MelHLayout(self.containerName,ut='cgmUISubTemplate')
		for item in attrTypes:
			MelLabel(AttrLabelRow,label=item)
		AttrLabelRow.layout()
		"""

		
	def buildAttributeManagerTool(self,parent, vis=True):
		containerName = 'Attributes Constainer'
		self.containerName = MelColumn(parent,vis=vis)

		#>>> Tag Labels
		TagLabelsRow = MelHLayout(self.containerName ,ut='cgmUISubTemplate',padding = 2)
		MelLabel(TagLabelsRow,label = 'Not done yet...')
		TagLabelsRow.layout()
		
		if mc.optionVar( q = 'cgmVarAttributeSourceObject'):
			self.SourceObjectField(edit=True,text = mc.optionVar( q = 'cgmVarAttributeSourceObject'))
			attrToolsLib.uiUpdateObjectAttrMenu(self,self.ObjectAttributesOptionMenu)

		return self.containerName
	
	
	def buildAttributeUtilitiesTool(self,parent, vis=True):
		containerName = 'Utilities Container'
		self.containerName = MelColumn(parent,vis=vis)

		#>>> Tag Labels
		mc.setParent(self.containerName)
		guiFactory.header('Short cuts')
		guiFactory.lineSubBreak()
		
		AttributeUtilityRow1 = MelHLayout(self.containerName,ut='cgmUISubTemplate',padding = 2)
	
		guiFactory.doButton2(AttributeUtilityRow1,'cgmName to Float',
			                 lambda *a:tdToolsLib.doCGMNameToFloat(),
			                 'Makes an animatalbe float attribute using the cgmName tag')
	
	
		mc.setParent(self.containerName)
		guiFactory.lineSubBreak()
	
		AttributeUtilityRow1.layout()
	
		#>>> SDK tools
		mc.setParent(self.containerName)
		guiFactory.lineBreak()
		guiFactory.header('SDK Tools')
		guiFactory.lineSubBreak()
	
	
		sdkRow = MelHLayout(self.containerName ,ut='cgmUISubTemplate',padding = 2)
		guiFactory.doButton2(sdkRow,'Select Driven Joints',
			                 lambda *a:tdToolsLib.doSelectDrivenJoints(self),
			                 "Selects driven joints from an sdk attribute")
	
	
		sdkRow.layout()
		mc.setParent(self.containerName)
		guiFactory.lineSubBreak()
		

		return self.containerName
	


