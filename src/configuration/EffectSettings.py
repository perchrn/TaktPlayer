'''
Created on 25. jan. 2012

@author: pcn
'''
from midi.MidiModulation import MidiModulation
from video.media.MediaFileModes import FadeMode, forceUnixPath
import os

class ConfigurationTemplates(object):
    def __init__(self, configurationTree, midiTiming, name, templateName = "Template", templateId = "Name"):
        self._configurationTree = configurationTree
        self._midiTiming = midiTiming
        self._templateConfig = self._configurationTree.addChildUnique(name)
        self._configurationTemplates = []
        self._templateName = templateName
        self._templateId = templateId
        self._templateTypeName = "Unknown template type"
        self._setupConfiguration()
        self._getConfiguration()

    def _setupConfiguration(self):
        pass

    def _getConfiguration(self):
        self.loadChildrenFromConfiguration()
        self._validateDefault()

    def checkAndUpdateFromConfiguration(self):
        if(self._configurationTree.isConfigurationUpdated()):
            print self._templateTypeName + " config is updated..."
            self._getConfiguration()

    def getMidiTiming(self):
        return self._midiTiming

    def getTemplate(self, name):
        lowername = name.lower()
        for template in self._configurationTemplates:
            if(template.getName().lower() == lowername):
                return template
        return None

    def getTemplateByIndex(self, index):
        if((index >= 0) and (index < len(self._configurationTemplates))):
            return self._configurationTemplates[index]
        else:
            return None

    def getList(self):
        return self._configurationTemplates

    def getTemplateNamesList(self):
        returnList = []
        for template in self._configurationTemplates:
            returnList.append(template.getName())
        return returnList

    def _findTemplateIx(self, name):
        lowername = name.lower()
        for templateIx in range(len(self._configurationTemplates)):
            template = self._configurationTemplates[templateIx]
#            print "template.getName().lower() ( " + template.getName() + " ) == lowername ( " + lowername + " )"
            if(template.getName().lower() == lowername):
                return templateIx
        return -1
                
    def loadChildrenFromConfiguration(self):
        effectTemplatesToKeep = []
        xmlChildren = self._templateConfig.findXmlChildrenList(self._templateName)
        if(xmlChildren == None):
            return
        lowerId = self._templateId.lower()
        for xmlConfig in xmlChildren:
            newTemplateName = xmlConfig.get(lowerId)
            oldTemplateIndex = self._findTemplateIx(newTemplateName)
            if(oldTemplateIndex < 0):
                newTemplate = self.createTemplateFromXml(newTemplateName, xmlConfig)
                self._configurationTemplates.append(newTemplate)
            else:
                newTemplate = self.createTemplateFromXml(newTemplateName, xmlConfig)
                self._configurationTemplates[oldTemplateIndex] = newTemplate
            effectTemplatesToKeep.append(newTemplateName)
        arrayLength = len(self._configurationTemplates)
        for i in range(arrayLength):
            ix = arrayLength - 1 - i
            template = self._configurationTemplates[ix]
            templateName = template.getName()
            templateLowerName = templateName.lower()
            keepTemplate = False
            for keepName in effectTemplatesToKeep:
                if(templateLowerName == keepName.lower()):
                    keepTemplate = True
                    break
                elif(templateName == forceUnixPath(keepName)):
                    keepTemplate = True
                    break
            if(keepTemplate == False):
                if(self._templateConfig.removeChildUniqueId(self._templateName, self._templateId, templateName) == False):
                    print "Config child NOT removed -!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!"
                else:
                    print "Config child removed OK"
                self._configurationTemplates.pop(ix)

    def getChoices(self):
        choiceList = []
        for template in self._configurationTemplates:
            choiceList.append(template.getName())
        return choiceList

    def _validateDefault(self):
        pass

    def createTemplateFromXml(self, name, xmlConfig):
        pass

    def duplicateTemplate(self, configName):
        oldTemplate = self.getTemplate(configName)
        if(oldTemplate != None):
            newTemplateName = configName + "_dup"
            testTemplate = self.getTemplate(newTemplateName)
            if(testTemplate == None):
                newTemplate = oldTemplate.getCopy(newTemplateName)
                if(newTemplate != None):
                    self._configurationTemplates.append(newTemplate)
                else:
                    print "Ii" * 100
                    print "Error! getCopy not implemented for template. Cannot duplicate!!!"
                    print "Ii" * 100
                return newTemplateName
        return None

    def deleteTemplate(self, configName):
        template = self.getTemplate(configName)
        if(template != None):
            self._configurationTemplates.remove(template)
        if(self._templateConfig.removeChildUniqueId(self._templateName, self._templateId, configName) == False):
            print "Config child NOT removed -!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!"
        else:
            print "Config child removed OK"

class EffectTemplates(ConfigurationTemplates):
    def __init__(self, configurationTree, midiTiming, internalResolutionX, internalResolutionY):
        self._internalResolutionX = internalResolutionX
        self._internalResolutionY = internalResolutionY
        ConfigurationTemplates.__init__(self, configurationTree, midiTiming, "EffectModulation")
        self._templateTypeName = "Effect templates"


    def getInternalResolution(self):
        return (self._internalResolutionX, self._internalResolutionY)

    def _validateDefault(self):
        for name in "MediaDefault1", "MediaDefault2", "MixPreDefault", "MixPostDefault":
            foundConfig = self._templateConfig.findChildUniqueId(self._templateName, self._templateId, name)
            if(foundConfig == None):
                effectConfigTree = self._templateConfig.addChildUniqueId(self._templateName, self._templateId, name, name)
                self._defaultModulationConfig = EffectSettings(name, self, effectConfigTree, self._templateConfig, self._templateId)
                self._configurationTemplates.append(self._defaultModulationConfig)

    def createTemplateFromXml(self, name, xmlConfig):
        effectConfigTree = self._templateConfig.addChildUniqueId(self._templateName, self._templateId, name, name)
        newTemplate = EffectSettings(name, self, effectConfigTree, self._templateConfig, self._templateId)
        newTemplate.updateFromXml(xmlConfig)
        return newTemplate

    def createTemplate(self, saveName, effectName, ammountMod, arg1Mod, arg2Mod, arg3Mod, arg4Mod, startValuesString):
        effectConfigTree = self._templateConfig.addChildUniqueId(self._templateName, self._templateId, saveName, saveName)
        newTemplate = EffectSettings(saveName, self, effectConfigTree, self._templateConfig, self._templateId)
        newTemplate.update(effectName, ammountMod, arg1Mod, arg2Mod, arg3Mod, arg4Mod, startValuesString)
        self._configurationTemplates.append(newTemplate)
        return newTemplate

    def checkIfNameIsDefaultName(self, configName):
        for name in "MediaDefault1", "MediaDefault2", "MixPreDefault", "MixPostDefault":
            if(configName == name):
                return True
        return False
        
class EffectSettings(object):
    def __init__(self, templateName, effectTemplates, effectConfigTree, parentConfigurationTree, templateId):
        self._effectTemplates = effectTemplates
        self._templateName = templateName
        self._midiTiming = self._effectTemplates.getMidiTiming()
        self._configurationTree = effectConfigTree
        self._parentConfigurationTree = parentConfigurationTree
        self._templateId = templateId
        self._internalResolutionX, self._internalResolutionY = self._effectTemplates.getInternalResolution()
        self._midiModulation = MidiModulation(self._configurationTree, self._midiTiming)
        self._setupConfiguration()
        self._getConfiguration()

    def getCopy(self, newName):
        effectConfigTree = self._parentConfigurationTree.addChildUniqueId(self._templateName, self._templateId, newName, newName)
        copyTemplate = EffectSettings(newName, self._effectTemplates, effectConfigTree, self._parentConfigurationTree, self._templateId)
        effectName = self._configurationTree.getValue("Effect")
        ammountMod = self._configurationTree.getValue("Amount")
        arg1Mod = self._configurationTree.getValue("Arg1")
        arg2Mod = self._configurationTree.getValue("Arg2")
        arg3Mod = self._configurationTree.getValue("Arg3")
        arg4Mod = self._configurationTree.getValue("Arg4")
        startValuesString = self.getStartValuesString()
        copyTemplate.update(effectName, ammountMod, arg1Mod, arg2Mod, arg3Mod, arg4Mod, startValuesString)
        return copyTemplate


    def getName(self):
        return self._templateName

    def setName(self, name):
        self._templateName = name
        self._configurationTree.setValue(self._templateId, name)

    def _setupConfiguration(self):
        self._midiModulation.setModulationReceiver("Amount", "MidiChannel.Controller.ModWheel")
        self._midiModulation.setModulationReceiver("Arg1", "None")
        self._midiModulation.setModulationReceiver("Arg2", "None")
        self._midiModulation.setModulationReceiver("Arg3", "None")
        self._midiModulation.setModulationReceiver("Arg4", "None")
        self._effectAmountModulationId = -1
        self._effectArg1ModulationId = -1
        self._effectArg2ModulationId = -1
        self._effectArg3ModulationId = -1
        self._effectArg4ModulationId = -1

        self._configurationTree.addTextParameter("Effect", "None")
        self._effectName = "None"

        self._configurationTree.addTextParameter("StartValues", "0.0|0.0|0.0|0.0|0.0")
        self._effectAmountStartValue = 0.0
        self._effectArg1StartValue = 0.0
        self._effectArg2StartValue = 0.0
        self._effectArg3StartValue = 0.0
        self._effectArg4StartValue = 0.0

    def getConfigHolder(self):
        return self._configurationTree

    def _getConfiguration(self):
        self._effectAmountModulationId = self._midiModulation.connectModulation("Amount")
        self._effectArg1ModulationId = self._midiModulation.connectModulation("Arg1")
        self._effectArg2ModulationId = self._midiModulation.connectModulation("Arg2")
        self._effectArg3ModulationId = self._midiModulation.connectModulation("Arg3")
        self._effectArg4ModulationId = self._midiModulation.connectModulation("Arg4")
        self._effectName = self._configurationTree.getValue("Effect")
        startValues = self._configurationTree.getValue("StartValues")
        self._setStartValuesString(startValues)
#        self._actualEffect = getEffectByName(effectName, self._configurationTree, self._internalResolutionX, self._internalResolutionY)

    def getEffectName(self):
        return self._effectName

    def update(self, effectName, ammountMod, arg1Mod, arg2Mod, arg3Mod, arg4Mod, startValuesString):
        self._configurationTree.setValue("Effect", effectName)
        self._midiModulation.setValue("Amount", ammountMod)
        self._midiModulation.setValue("Arg1", arg1Mod)
        self._midiModulation.setValue("Arg2", arg2Mod)
        self._midiModulation.setValue("Arg3", arg3Mod)
        self._midiModulation.setValue("Arg4", arg4Mod)
        #Validate and set:
        self._setStartValuesString(startValuesString)
        self._configurationTree.setValue("StartValues", self.getStartValuesString())
        
    def checkAndUpdateFromConfiguration(self):
        if(self._configurationTree.isConfigurationUpdated()):
            print "EffectSettings config is updated..."
            self._getConfiguration()
            self._midiModulation.checkAndUpdateFromConfiguration()
            self._configurationTree.resetConfigurationUpdated()

    def updateFromXml(self, xmlFile):
        self._configurationTree._updateFromXml(xmlFile)

    def getValues(self, songPosition, midiChannelStateHolder, midiNoteStateHolder):
        amount =  self._midiModulation.getModlulationValue(self._effectAmountModulationId, midiChannelStateHolder, midiNoteStateHolder, songPosition, 0.0)
        arg1 =  self._midiModulation.getModlulationValue(self._effectArg1ModulationId, midiChannelStateHolder, midiNoteStateHolder, songPosition, 0.0)
        arg2 =  self._midiModulation.getModlulationValue(self._effectArg2ModulationId, midiChannelStateHolder, midiNoteStateHolder, songPosition, 0.0)
        arg3 =  self._midiModulation.getModlulationValue(self._effectArg3ModulationId, midiChannelStateHolder, midiNoteStateHolder, songPosition, 0.0)
        arg4 =  self._midiModulation.getModlulationValue(self._effectArg4ModulationId, midiChannelStateHolder, midiNoteStateHolder, songPosition, 0.0)
        return (amount, arg1, arg2, arg3, arg4)

    def getStartValues(self):
        return (self._effectAmountStartValue, self._effectArg1StartValue, self._effectArg2StartValue, self._effectArg3StartValue, self._effectArg4StartValue)

    def _setStartValuesString(self, startValues):
        if(startValues != None):
            startValuesSplit = startValues.split('|', 6)
            if(len(startValuesSplit) == 5):
                self._effectAmountStartValue = min(max(0.0, float(startValuesSplit[0])), 1.0)
                self._effectArg1StartValue = min(max(0.0, float(startValuesSplit[1])), 1.0)
                self._effectArg2StartValue = min(max(0.0, float(startValuesSplit[2])), 1.0)
                self._effectArg3StartValue = min(max(0.0, float(startValuesSplit[3])), 1.0)
                self._effectArg4StartValue = min(max(0.0, float(startValuesSplit[4])), 1.0)

    def getStartValuesString(self):
        valueString = str(self._effectAmountStartValue)
        valueString += "|" + str(self._effectArg1StartValue)
        valueString += "|" + str(self._effectArg2StartValue)
        valueString += "|" + str(self._effectArg3StartValue)
        valueString += "|" + str(self._effectArg4StartValue)
        return valueString

class FadeTemplates(ConfigurationTemplates):
    def __init__(self, configurationTree, midiTiming):
        ConfigurationTemplates.__init__(self, configurationTree, midiTiming, "FadeAndLevelTemplates")
        self._templateTypeName = "Effect templates"

    def _validateDefault(self):
        name = "Default"
        foundConfig = self._templateConfig.findChildUniqueId(self._templateName, self._templateId, name)
        if(foundConfig == None):
            fadeConfigTree = self._templateConfig.addChildUniqueId(self._templateName, self._templateId, name, name)
            self._defaultModulationConfig = FadeSettings(name, self, fadeConfigTree, self._templateConfig, self._templateId)
            self._configurationTemplates.append(self._defaultModulationConfig)

    def createTemplateFromXml(self, name, xmlConfig):
        fadeConfigTree = self._templateConfig.addChildUniqueId(self._templateName, self._templateId, name, name)
        newTemplate = FadeSettings(name, self, fadeConfigTree, self._templateConfig, self._templateId)
        newTemplate.updateFromXml(xmlConfig)
        return newTemplate

    def createTemplate(self, saveName, fadeMode, fadeMod, levelMod):
        fadeConfigTree = self._templateConfig.addChildUniqueId(self._templateName, self._templateId, saveName, saveName)
        newTemplate = FadeSettings(saveName, self, fadeConfigTree, self._templateConfig, self._templateId)
        newTemplate.update(fadeMode, fadeMod, levelMod)
        self._configurationTemplates.append(newTemplate)
        return newTemplate

    def checkIfNameIsDefaultName(self, configName):
        for name in "Default":
            if(configName == name):
                return True
        return False
        
class FadeSettings(object):
    def __init__(self, templateName, fadeTemplates, fadeConfigTree, parentConfigurationTree, templateId):
        self._fadeTemplates = fadeTemplates
        self._templateName = templateName
        self._midiTiming = self._fadeTemplates.getMidiTiming()
        self._configurationTree = fadeConfigTree
        self._parentConfigurationTree = parentConfigurationTree
        self._templateId = templateId
        self._midiModulation = MidiModulation(self._configurationTree, self._midiTiming)
        self._setupConfiguration()
        self._getConfiguration()

    def getCopy(self, newName):
        fadeConfigTree = self._parentConfigurationTree.addChildUniqueId(self._templateName, self._templateId, newName, newName)
        copyTemplate = FadeSettings(newName, self._fadeTemplates, fadeConfigTree, self._parentConfigurationTree, self._templateId)
        fadeModeString = self._configurationTree.getValue("Mode")
        fadeModulationString = self._configurationTree.getValue("Modulation")
        levelModulationString = self._configurationTree.getValue("Level")
        copyTemplate.update(fadeModeString, fadeModulationString, levelModulationString)
        return copyTemplate

    def getName(self):
        return self._templateName

    def setName(self, name):
        self._templateName = name
        self._configurationTree.setValue(self._templateId, name)

    def getFadeMode(self):
        return self._configurationTree.getValue("Mode")

    def _setupConfiguration(self):
        self._midiModulation.setModulationReceiver("Modulation", "None")
        self._midiModulation.setModulationReceiver("Level", "None")
        self._configurationTree.addTextParameter("Mode", "Black")
        self._fadeModulationId = -1
        self._levelModulationId = -1
        self._fadeMode = FadeMode.Black

    def getConfigHolder(self):
        return self._configurationTree

    def _getConfiguration(self):
        self._fadeModulationId = self._midiModulation.connectModulation("Modulation")
        self._levelModulationId = self._midiModulation.connectModulation("Level")
        fadeMode = self._configurationTree.getValue("Mode")
        if(fadeMode == "Black"):
            self._fadeMode = FadeMode.Black
        elif(fadeMode == "White"):
            self._fadeMode = FadeMode.White
        else:
            self._fadeMode = FadeMode.Black #Defaults to black

    def update(self, fadeMode, fadeMod, levelMod):
        if(fadeMod != None):
            self._midiModulation.setValue("Modulation", fadeMod)
        if(levelMod != None):
            self._midiModulation.setValue("Level", levelMod)
        self._configurationTree.setValue("Mode", fadeMode)
        
    def checkAndUpdateFromConfiguration(self):
        if(self._configurationTree.isConfigurationUpdated()):
            print "FadeSettings config is updated..."
            self._getConfiguration()
            self._midiModulation.checkAndUpdateFromConfiguration()
            self._configurationTree.resetConfigurationUpdated()

    def updateFromXml(self, xmlFile):
        self._configurationTree._updateFromXml(xmlFile)

    def getValues(self, songPosition, midiChannelStateHolder, midiNoteStateHolder):
        fadeVal =  self._midiModulation.getModlulationValue(self._fadeModulationId, midiChannelStateHolder, midiNoteStateHolder, songPosition, 0.0)
        levelVal =  self._midiModulation.getModlulationValue(self._levelModulationId, midiChannelStateHolder, midiNoteStateHolder, songPosition, 0.0)
        return (self._fadeMode, fadeVal, levelVal)

class EffectImageList(ConfigurationTemplates):
    def __init__(self, configurationTree, midiTiming, videoDir = None):
        ConfigurationTemplates.__init__(self, configurationTree, midiTiming, "EffectImageList", "Image", "FileName")
        self._templateTypeName = "Effect images"
        self._videoDir = videoDir

    def getVideoDir(self):
        return self._videoDir

    def getFileListString(self):
        returnList = ""
        for template in self._configurationTemplates:
            if(returnList == ""):
                returnList += os.path.basename(template.getFileName())
            else:
                returnList += "," + os.path.basename(template.getFileName())
        return returnList

    def createTemplateFromXml(self, fileName, xmlConfig):
        fileName = forceUnixPath(fileName)
        xmlConfig.set("filename", fileName)
        #print "DEBUG createTemplateFromXml creating new with fileName: " + str(fileName) 
        effectImageConfigTree = self._templateConfig.addChildUniqueId(self._templateName, self._templateId, fileName, fileName)
        newTemplate = ImageSettings(fileName, self, effectImageConfigTree)
        newTemplate.updateFromXml(xmlConfig)
        return newTemplate

    def createTemplate(self, saveName):
        if(len(self._configurationTemplates) < 62):
            effectImageConfigTree = self._templateConfig.addChildUniqueId(self._templateName, self._templateId, saveName, saveName)
            newTemplate = ImageSettings(saveName, self, effectImageConfigTree)
            self._configurationTemplates.append(newTemplate)
            return newTemplate
        return None

class ImageSettings(object):
    def __init__(self, fileName, effectImageTemplates, imageConfigTree):
        self._effectImageTemplates = effectImageTemplates
        self._fileName = fileName
        self._configurationTree = imageConfigTree
        self._setupConfiguration()
        self._getConfiguration()

    def getFileName(self):
        return self._fileName

    def getName(self):
        return self.getFileName()

    def setFileName(self, fileame):
        self._fileName = fileame
        self._configurationTree.setValue(self._templateId, fileame)

    def _setupConfiguration(self):
        pass

    def getConfigHolder(self):
        return self._configurationTree

    def _getConfiguration(self):
        pass

    def checkAndUpdateFromConfiguration(self):
        if(self._configurationTree.isConfigurationUpdated()):
            print "EffectImageList config is updated..."
            self._getConfiguration()
            self._configurationTree.resetConfigurationUpdated()

    def updateFromXml(self, xmlFile):
        self._configurationTree._updateFromXml(xmlFile)
