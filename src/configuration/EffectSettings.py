'''
Created on 25. jan. 2012

@author: pcn
'''
from midi.MidiModulation import MidiModulation
from video.media.MediaFileModes import FadeMode
import copy

class ConfigurationTemplates(object):
    def __init__(self, configurationTree, midiTiming, name):
        self._configurationTree = configurationTree
        self._midiTiming = midiTiming
        self._templateConfig = self._configurationTree.addChildUnique(name)
        self._configurationTemplates = []
        self._setupConfiguration()
        self._getConfiguration()

    def _setupConfiguration(self):
        pass

    def _getConfiguration(self):
        self.loadChildrenFromConfiguration()
        self._validateDefault()

    def checkAndUpdateFromConfiguration(self):
        pass

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
            print "DEBUG getTemplateByIndex() bad index: " + str(index) + " (len=" + str(len(self._configurationTemplates)) + ")"
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
        xmlChildren = self._templateConfig.findXmlChildrenList("Template")
        if(xmlChildren == None):
            return
        for xmlConfig in xmlChildren:
            newTemplateName = xmlConfig.get("name")
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
            if(keepTemplate == False):
                if(self._templateConfig.removeChildUniqueId("Template", "Name", templateName) == False):
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
                newTemplate = copy.deepcopy(oldTemplate)
                newTemplate.setName(newTemplateName)
                self._configurationTemplates.append(newTemplate)
                return newTemplateName
        return None

    def deleteTemplate(self, configName):
        template = self.getTemplate(configName)
        if(template != None):
            self._configurationTemplates.remove(template)

class EffectTemplates(ConfigurationTemplates):
    def __init__(self, configurationTree, midiTiming, internalResolutionX, internalResolutionY):
        self._internalResolutionX = internalResolutionX
        self._internalResolutionY = internalResolutionY
        ConfigurationTemplates.__init__(self, configurationTree, midiTiming, "EffectModulation")

    def getInternalResolution(self):
        return (self._internalResolutionX, self._internalResolutionY)

    def _validateDefault(self):
        for name in "MediaDefault1", "MediaDefault2", "MixPreDefault", "MixPostDefault":
            foundConfig = self._templateConfig.findChildUniqueId("Template", "Name", name)
            if(foundConfig == None):
                effectConfigTree = self._templateConfig.addChildUniqueId("Template", "Name", name, name)
                self._defaultModulationConfig = EffectSettings(name, self, effectConfigTree)
                self._configurationTemplates.append(self._defaultModulationConfig)

    def createTemplateFromXml(self, name, xmlConfig):
        effectConfigTree = self._templateConfig.addChildUniqueId("Template", "Name", name, name)
        newTemplate = EffectSettings(name, self, effectConfigTree)
        newTemplate.updateFromXml(xmlConfig)
        return newTemplate

    def createTemplate(self, saveName, effectName, ammountMod, arg1Mod, arg2Mod, arg3Mod, arg4Mod):
        effectConfigTree = self._templateConfig.addChildUniqueId("Template", "Name", saveName, saveName)
        newTemplate = EffectSettings(saveName, self, effectConfigTree)
        newTemplate.update(effectName, ammountMod, arg1Mod, arg2Mod, arg3Mod, arg4Mod)
        self._configurationTemplates.append(newTemplate)
        return newTemplate

    def checkIfNameIsDefaultName(self, configName):
        for name in "MediaDefault1", "MediaDefault2", "MixPreDefault", "MixPostDefault":
            if(configName == name):
                return True
        return False
        
class EffectSettings(object):
    def __init__(self, templateName, effectTemplates, effectConfigTree):
        self._effectTemplates = effectTemplates
        self._templateName = templateName
        self._midiTiming = self._effectTemplates.getMidiTiming()
        self._configurationTree = effectConfigTree
        self._internalResolutionX, self._internalResolutionY = self._effectTemplates.getInternalResolution()
        self._midiModulation = MidiModulation(self._configurationTree, self._midiTiming)
        self._setupConfiguration()
        self._getConfiguration()

    def getName(self):
        return self._templateName

    def setName(self, name):
        self._templateName = name
        self._configurationTree.setValue("Name", name)

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

    def getConfigHolder(self):
        return self._configurationTree

    def _getConfiguration(self):
        self._effectAmountModulationId = self._midiModulation.connectModulation("Amount")
        self._effectArg1ModulationId = self._midiModulation.connectModulation("Arg1")
        self._effectArg2ModulationId = self._midiModulation.connectModulation("Arg2")
        self._effectArg3ModulationId = self._midiModulation.connectModulation("Arg3")
        self._effectArg4ModulationId = self._midiModulation.connectModulation("Arg4")
        self._effectName = self._configurationTree.getValue("Effect")
#        self._actualEffect = getEffectByName(effectName, self._configurationTree, self._internalResolutionX, self._internalResolutionY)

    def getEffectName(self):
        return self._effectName

    def update(self, effectName, ammountMod, arg1Mod, arg2Mod, arg3Mod, arg4Mod):
        self._configurationTree.setValue("Effect", effectName)
        self._midiModulation.setValue("Amount", ammountMod)
        self._midiModulation.setValue("Arg1", arg1Mod)
        self._midiModulation.setValue("Arg2", arg2Mod)
        self._midiModulation.setValue("Arg3", arg3Mod)
        self._midiModulation.setValue("Arg4", arg4Mod)
        
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


class FadeTemplates(ConfigurationTemplates):
    def __init__(self, configurationTree, midiTiming):
        ConfigurationTemplates.__init__(self, configurationTree, midiTiming, "FadeAndLevelTemplates")

    def _validateDefault(self):
        name = "Default"
        foundConfig = self._templateConfig.findChildUniqueId("Template", "Name", name)
        if(foundConfig == None):
            effectConfigTree = self._templateConfig.addChildUniqueId("Template", "Name", name, name)
            self._defaultModulationConfig = FadeSettings(name, self, effectConfigTree)
            self._configurationTemplates.append(self._defaultModulationConfig)

    def createTemplateFromXml(self, name, xmlConfig):
        effectConfigTree = self._templateConfig.addChildUniqueId("Template", "Name", name, name)
        newTemplate = FadeSettings(name, self, effectConfigTree)
        newTemplate.updateFromXml(xmlConfig)
        return newTemplate

    def createTemplate(self, saveName, fadeMode, fadeMod, levelMod):
        effectConfigTree = self._templateConfig.addChildUniqueId("Template", "Name", saveName, saveName)
        newTemplate = FadeSettings(saveName, self, effectConfigTree)
        newTemplate.update(fadeMode, fadeMod, levelMod)
        self._configurationTemplates.append(newTemplate)
        return newTemplate

    def checkIfNameIsDefaultName(self, configName):
        for name in "Default":
            if(configName == name):
                return True
        return False
        
class FadeSettings(object):
    def __init__(self, templateName, effectTemplates, effectConfigTree):
        self._fadeTemplates = effectTemplates
        self._templateName = templateName
        self._midiTiming = self._fadeTemplates.getMidiTiming()
        self._configurationTree = effectConfigTree
        self._midiModulation = MidiModulation(self._configurationTree, self._midiTiming)
        self._setupConfiguration()
        self._getConfiguration()

    def getName(self):
        return self._templateName

    def setName(self, name):
        self._templateName = name
        self._configurationTree.setValue("Name", name)

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
            print "EffectSettings config is updated..."
            self._getConfiguration()
            self._midiModulation.checkAndUpdateFromConfiguration()
            self._configurationTree.resetConfigurationUpdated()

    def updateFromXml(self, xmlFile):
        self._configurationTree._updateFromXml(xmlFile)

    def getValues(self, songPosition, midiChannelStateHolder, midiNoteStateHolder):
        fadeVal =  self._midiModulation.getModlulationValue(self._fadeModulationId, midiChannelStateHolder, midiNoteStateHolder, songPosition, 0.0)
        levelVal =  self._midiModulation.getModlulationValue(self._levelModulationId, midiChannelStateHolder, midiNoteStateHolder, songPosition, 0.0)
        return (self._fadeMode, fadeVal, levelVal)

