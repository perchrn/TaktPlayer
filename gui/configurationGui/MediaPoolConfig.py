'''
Created on 6. feb. 2012

@author: pcn
'''
from midi.MidiUtilities import noteToNoteString, noteStringToNoteNumber
import wx
from widgets.PcnImageButton import PcnKeyboardButton, PcnImageButton,\
    addTrackButtonFrame, EVT_DRAG_DONE_EVENT, EVT_DOUBLE_CLICK_EVENT,\
    PcnPopupMenu
import os
from video.media.MediaFileModes import VideoLoopMode, ImageSequenceMode,\
    MediaTypes, MixMode, getMixModeFromName, forceUnixPath
from video.EffectModes import getEffectId, EffectTypes
from midi.MidiModulation import MidiModulation
from midi.MidiTiming import MidiTiming
import sys
from utilities.FloatListText import textToFloatValues, floatValuesToString
from configurationGui.MediaDialogs import MediaFontDialog

class MediaPoolConfig(object):
    def __init__(self, configParent, noteModulation):
        self._configurationTree = configParent.addChildUnique("MediaPool")
        self._noteModulation = noteModulation

        self._mediaPool = []
        for i in range(128): #@UnusedVariable
            self._mediaPool.append(None)

        self.loadMediaFromConfiguration()

    def _getConfiguration(self):
        self.loadMediaFromConfiguration()
        self.setupSpecialNoteModulations()

    def checkAndUpdateFromConfiguration(self):
        if(self._configurationTree.isConfigurationUpdated()):
            print "mediaPool config is updated..."
            self._getConfiguration()
            self._configurationTree.resetConfigurationUpdated()

    def loadMediaFromConfiguration(self):
        mediaPoolState = []
        for i in range(128):
            mediaPoolState.append(False)
        mediaFileChildren = self._configurationTree.findXmlChildrenList("MediaFile")
        if(mediaFileChildren != None):
            for xmlConfig in mediaFileChildren:
                midiNote = self.addXmlMedia(xmlConfig)
                mediaPoolState[midiNote] = True
        for i in range(128):
            mediaState = mediaPoolState[i]
            if(mediaState == False):
                noteLetter = noteToNoteString(i)
                self.addMedia("", noteLetter)

    def addXmlMedia(self, xmlConfig):
        fileName = forceUnixPath(xmlConfig.get("filename"))
        noteLetter = xmlConfig.get("note")
        print "Adding " + fileName.encode("utf-8") + " - " + str(noteLetter)
        return self.addMedia(fileName, noteLetter, xmlConfig)

    def addMedia(self, fileName, noteLetter, xmlConfig = None):
        midiNote = noteStringToNoteNumber(noteLetter)
        midiNote = min(max(midiNote, 0), 127)

        #remove old:
        if(self._mediaPool[midiNote] != None):
            if(self._configurationTree.removeChildUniqueId("MediaFile", "Note", noteLetter) == False):
                print "Config child NOT removed -!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!"
#            else:
#                print "Config child removed OK"

        if(len(fileName) <= 0):
            self._mediaPool[midiNote] = None
        else:
            self._mediaPool[midiNote] = MediaFile(self._configurationTree, fileName, noteLetter, midiNote, xmlConfig)
        return midiNote

    def getNoteConfiguration(self, noteId):
        noteId = min(max(noteId, 0), 127)
        return self._mediaPool[noteId]

    def getNoteList(self):
        return self._mediaPool

    def setupSpecialNoteModulations(self):
        for note in self._mediaPool:
#            if(note == None):
#                print "n",
#            else:
#                print note.getType(),
            if((note != None) and (note.getType() == "Modulation")):
                noteName = note.getName()
                descSum = "Modulation;" + noteName + ";Any;Sum"
                desc1st = "Modulation;" + noteName + ";Any;1st"
                desc2nd = "Modulation;" + noteName + ";Any;2nd"
                desc3rd = "Modulation;" + noteName + ";Any;3rd"
                self._noteModulation.addModulation(descSum)
                self._noteModulation.addModulation(desc1st)
                self._noteModulation.addModulation(desc2nd)
                self._noteModulation.addModulation(desc3rd)
                for midiChannel in range(16):
                    descSum = "Modulation;" + noteName + ";" + str(midiChannel + 1) + ";Sum"
                    desc1st = "Modulation;" + noteName + ";" + str(midiChannel + 1) + ";1st"
                    desc2nd = "Modulation;" + noteName + ";" + str(midiChannel + 1) + ";2nd"
                    desc3rd = "Modulation;" + noteName + ";" + str(midiChannel + 1) + ";3rd"
                    self._noteModulation.addModulation(descSum)
                    self._noteModulation.addModulation(desc1st)
                    self._noteModulation.addModulation(desc2nd)
                    self._noteModulation.addModulation(desc3rd)

    def makeNoteConfig(self, fileName, noteLetter, midiNote):
        if((midiNote >= 0) and (midiNote < 128)):
#            print "Making note: %d !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!" % midiNote
            newMediaFile = MediaFile(self._configurationTree, fileName, noteLetter, midiNote, None)
            self._mediaPool[midiNote] = newMediaFile
            #print self._configurationTree.getConfigurationXMLString()
            return newMediaFile
        return None

    def deleteNoteConfig(self, midiNote, noteLetter):
        if((midiNote >= 0) and (midiNote < 128)):
#            print "Deleting note: %d !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!" % midiNote
            if(self._configurationTree.removeChildUniqueId("MediaFile", "Note", noteLetter) == False):
                print "Config child NOT removed -!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!"
            else:
#                print "Config child removed OK"
                self._mediaPool[midiNote] = None

    def countNumberOfTimeTimeModulationTemplateUsed(self, effectConfigName):
        returnNumer = 0
        for noteConfig in self._mediaPool:
            if(noteConfig != None):
                returnNumer += noteConfig.countNumberOfTimeTimeModulationTemplateUsed(effectConfigName)
        return returnNumer

    def countNumberOfTimeEffectTemplateUsed(self, effectConfigName):
        returnNumer = 0
        for noteConfig in self._mediaPool:
            if(noteConfig != None):
                returnNumer += noteConfig.countNumberOfTimeEffectTemplateUsed(effectConfigName)
        return returnNumer

    def countNumberOfTimeFadeTemplateUsed(self, fadeConfigName):
        returnNumer = 0
        for noteConfig in self._mediaPool:
            if(noteConfig != None):
                returnNumer += noteConfig.countNumberOfTimeFadeTemplateUsed(fadeConfigName)
        return returnNumer

    def renameTimeModulationTemplateUsed(self, oldName, newName):
        for noteConfig in self._mediaPool:
            if(noteConfig != None):
                noteConfig.renameTimeModulationTemplateUsed(oldName, newName)

    def renameEffectTemplateUsed(self, oldName, newName):
        for noteConfig in self._mediaPool:
            if(noteConfig != None):
                noteConfig.renameEffectTemplateUsed(oldName, newName)

    def renameFadeTemplateUsed(self, oldName, newName):
        for noteConfig in self._mediaPool:
            if(noteConfig != None):
                noteConfig.renameFadeTemplateUsed(oldName, newName)

    def verifyTimeModulationTemplateUsed(self, fadeConfigNameList):
        for noteConfig in self._mediaPool:
            if(noteConfig != None):
                noteConfig.verifyTimeModulationTemplateUsed(fadeConfigNameList)

    def verifyEffectTemplateUsed(self, effectConfigNameList):
        for noteConfig in self._mediaPool:
            if(noteConfig != None):
                noteConfig.verifyEffectTemplateUsed(effectConfigNameList)

    def verifyFadeTemplateUsed(self, fadeConfigNameList):
        for noteConfig in self._mediaPool:
            if(noteConfig != None):
                noteConfig.verifyFadeTemplateUsed(fadeConfigNameList)

class MediaFile(object):
    def __init__(self, configParent, fileName, noteLetter, midiNote, xmlConfig):
        mediaType = None
        if(xmlConfig != None):
            mediaType = xmlConfig.get("type")
        if(mediaType == None):
            mediaType = "VideoLoop"
        self._configurationTree = configParent.addChildUniqueId("MediaFile", "Note", noteLetter, midiNote)
        self._configurationTree.addTextParameter("FileName", "")
        self._configurationTree.setValue("FileName", fileName)
        self._configurationTree.addTextParameter("Type", mediaType)
        self._configurationTree.addFloatParameter("SyncLength", 4.0) #Default one bar (re calculated on load)
        self._configurationTree.addFloatParameter("QuantizeLength", 1.0)#Default one beat
        if(mediaType != "Modulation"):
            self._configurationTree.addTextParameter("MixMode", "Add")#Default Add
            self._defaultTimeModulationSettingsName = "Default"
            self._configurationTree.addTextParameter("TimeModulationConfig", self._defaultTimeModulationSettingsName)#Default Default
            self._defaultEffect1SettingsName = "MediaDefault1"
            self._configurationTree.addTextParameter("Effect1Config", self._defaultEffect1SettingsName)#Default MediaDefault1
            self._defaultEffect2SettingsName = "MediaDefault2"
            self._configurationTree.addTextParameter("Effect2Config", self._defaultEffect2SettingsName)#Default MediaDefault2
            self._defaultFadeSettingsName = "Default"
            self._configurationTree.addTextParameter("FadeConfig", self._defaultFadeSettingsName)#Default Default
        self._configurationTree.addTextParameter("ModulationValuesMode", "KeepOld")#Default KeepOld
        if(mediaType == "VideoLoop"):
            self._configurationTree.addTextParameter("LoopMode", "Normal")
        elif(mediaType == "Image"):
            self._configurationTree.addTextParameter("StartValues", "0.0|0.0|0.0")
            self._configurationTree.addTextParameter("EndValues", "0.0|0.0|0.0")
            self._configurationTree.addTextParameter("DisplayMode", "Crop")
        elif(mediaType == "ScrollImage"):
            self._configurationTree.addTextParameter("ScrollModulation", "None")
            self._configurationTree.addBoolParameter("HorizontalMode", True)
            self._configurationTree.addBoolParameter("ReverseMode", False)
        elif(mediaType == "Sprite"):
            self._configurationTree.addTextParameter("StartPosition", "0.5|0.5")
            self._configurationTree.addTextParameter("EndPosition", "0.5|0.5")
            self._configurationTree.addTextParameter("XModulation", "None")
            self._configurationTree.addTextParameter("YModulation", "None")
            self._configurationTree.addBoolParameter("InvertFirstFrameMask", False)
        elif(mediaType == "Text"):
            self._configurationTree.addTextParameter("StartPosition", "0.5|0.5")
            self._configurationTree.addTextParameter("EndPosition", "0.5|0.5")
            self._configurationTree.addTextParameter("XModulation", "None")
            self._configurationTree.addTextParameter("YModulation", "None")
            self._configurationTree.addTextParameter("Font", "Arial;32;#FFFFFF")
        elif(mediaType == "ImageSequence"):
            self._configurationTree.addTextParameter("SequenceMode", "Time")
            self._configurationTree.addTextParameter("PlaybackModulation", "None")
        elif(mediaType == "Camera"):
            self._configurationTree.addTextParameter("DisplayMode", "Crop")
        elif(mediaType == "KinectCamera"):
#            self._configurationTree.addTextParameter("DisplayModeModulation", "None")
            self._configurationTree.addTextParameter("FilterValues", "0.0|0.0|0.0|0.0")
            self._configurationTree.addTextParameter("ZoomValues", "0.5|0.5|0.5|0.5")
        elif(mediaType == "Modulation"):
            self._configurationTree.addTextParameter("FirstModulation", "None")
            self._configurationTree.addTextParameter("ModulationCombiner1", "Add")
            self._configurationTree.addTextParameter("SecondModulation", "None")
            self._configurationTree.addTextParameter("ModulationCombiner2", "Add")
            self._configurationTree.addTextParameter("ThirdModulation", "None")
            self._configurationTree.addFloatParameter("MinValue", 0.0)
            self._configurationTree.addFloatParameter("MaxValue", 1.0)
            self._configurationTree.addTextParameter("Smoother", "Off")

        if(xmlConfig != None):
            self._configurationTree._updateFromXml(xmlConfig)

    def getConfig(self):
        return self._configurationTree

    def updateFileName(self, fileName, isVideoFile):
        self._configurationTree.setValue("FileName", fileName)
        if(isVideoFile == False):
            #Image file
            oldType = self._configurationTree.getValue("Type")
            if((oldType == "Image") or (oldType == "ScrollImage") or (oldType == "Sprite")):
                changedToImage = False
            else:
                changedToImage = True
                self._configurationTree.setValue("Type", "Image")
            if(oldType == "VideoLoop"):
                self._configurationTree.removeParameter("LoopMode")
            elif(oldType == "Camera"):
                self._configurationTree.removeParameter("DisplayMode")
            elif(oldType == "KinectCamera"):
#                self._configurationTree.removeParameter("DisplayModeModulation")
                self._configurationTree.removeParameter("FilterValues")
                self._configurationTree.removeParameter("ZoomValues")
            elif(oldType == "ImageSequence"):
                self._configurationTree.removeParameter("SequenceMode")
                self._configurationTree.removeParameter("PlaybackModulation")
            elif(oldType == "Group"):
                pass
            elif(oldType == "Text"):
                self._configurationTree.removeParameter("StartPosition")
                self._configurationTree.removeParameter("EndPosition")
                self._configurationTree.removeParameter("XModulation")
                self._configurationTree.removeParameter("YModulation")
                self._configurationTree.removeParameter("Font")
            elif(oldType == "Modulation"):
                self._configurationTree.removeParameter("FirstModulation")
                self._configurationTree.removeParameter("ModulationCombiner1")
                self._configurationTree.removeParameter("SecondModulation")
                self._configurationTree.removeParameter("ModulationCombiner2")
                self._configurationTree.removeParameter("ThirdModulation")
                self._configurationTree.removeParameter("MinValue")
                self._configurationTree.removeParameter("MaxValue")
                self._configurationTree.removeParameter("Smoother")

                self._configurationTree.addTextParameter("MixMode", "Add")#Default Add
                self._configurationTree.addTextParameter("TimeModulationConfig", self._defaultTimeModulationSettingsName)#Default Default
                self._configurationTree.addTextParameter("Effect1Config", self._defaultEffect1SettingsName)#Default MediaDefault1
                self._configurationTree.addTextParameter("Effect2Config", self._defaultEffect2SettingsName)#Default MediaDefault2
                self._configurationTree.addTextParameter("FadeConfig", self._defaultFadeSettingsName)#Default Default

            if(changedToImage == True):
                self._configurationTree.addTextParameter("StartValues", "0.0|0.0|0.0")
                self._configurationTree.addTextParameter("EndValues", "0.0|0.0|0.0")
                self._configurationTree.addBoolParameter("DisplayMode", "Crop")
        else:
            #Video file
            oldType = self._configurationTree.getValue("Type")
            if((oldType == "Image") or (oldType == "ScrollImage") or (oldType == "Sprite") or (oldType == "Camera") or (oldType == "KinectCamera") or (oldType == "Modulation")):
                self._configurationTree.setValue("Type", "VideoLoop")
                oldloopMode = self._configurationTree.getValue("LoopMode")
                if(oldloopMode == None):
                    self._configurationTree.setValue("LoopMode", "Normal")
                if(oldType == "KinectCamera"):
#                    self._configurationTree.removeParameter("DisplayModeModulation")
                    self._configurationTree.removeParameter("FilterValues")
                    self._configurationTree.removeParameter("ZoomValues")
                elif(oldType == "Camera"):
                    self._configurationTree.removeParameter("DisplayMode")
                elif(oldType == "ImageSequence"):
                    self._configurationTree.removeParameter("SequenceMode")
                    self._configurationTree.removeParameter("PlaybackModulation")
                elif(oldType == "Image"):
                    self._configurationTree.removeParameter("StartValues")
                    self._configurationTree.removeParameter("EndValues")
                    self._configurationTree.removeParameter("DisplayMode")
                elif(oldType == "ScrollImage"):
                    self._configurationTree.removeParameter("ScrollModulation")
                    self._configurationTree.removeParameter("HorizontalMode")
                    self._configurationTree.removeParameter("ReverseMode")
                elif(oldType == "Sprite"):
                    self._configurationTree.removeParameter("StartPosition")
                    self._configurationTree.removeParameter("EndPosition")
                    self._configurationTree.removeParameter("XModulation")
                    self._configurationTree.removeParameter("YModulation")
                    self._configurationTree.removeParameter("InvertFirstFrameMask")
                elif(oldType == "Text"):
                    self._configurationTree.removeParameter("StartPosition")
                    self._configurationTree.removeParameter("EndPosition")
                    self._configurationTree.removeParameter("XModulation")
                    self._configurationTree.removeParameter("YModulation")
                    self._configurationTree.removeParameter("Font")
                elif(oldType == "Group"):
                    pass
                elif(oldType == "Modulation"):
                    self._configurationTree.removeParameter("FirstModulation")
                    self._configurationTree.removeParameter("ModulationCombiner1")
                    self._configurationTree.removeParameter("SecondModulation")
                    self._configurationTree.removeParameter("ModulationCombiner2")
                    self._configurationTree.removeParameter("ThirdModulation")
                    self._configurationTree.removeParameter("MinValue")
                    self._configurationTree.removeParameter("MaxValue")
                    self._configurationTree.removeParameter("Smoother")

                    self._configurationTree.addTextParameter("MixMode", "Add")#Default Add
                    self._configurationTree.addTextParameter("TimeModulationConfig", self._defaultTimeModulationSettingsName)#Default Default
                    self._configurationTree.addTextParameter("Effect1Config", self._defaultEffect1SettingsName)#Default MediaDefault1
                    self._configurationTree.addTextParameter("Effect2Config", self._defaultEffect2SettingsName)#Default MediaDefault2
                    self._configurationTree.addTextParameter("FadeConfig", self._defaultFadeSettingsName)#Default Default

    def getName(self):
        return self._configurationTree.getValue("FileName")

    def getType(self):
        return self._configurationTree.getValue("Type")

    def getMixMode(self):
        retValue = "None"
        mediaType = self._configurationTree.getValue("Type")
        if((mediaType != None) and (mediaType != "Modulation")):
            retValue = self._configurationTree.getValue("MixMode")
        return retValue

    def getFadeConfigName(self):
        retValue = "None"
        mediaType = self._configurationTree.getValue("Type")
        if((mediaType != None) and (mediaType != "Modulation")):
            retValue = self._configurationTree.getValue("FadeConfig")
        return retValue

    def updateFrom(self, sourceMediaFile, dontChangeNote = True):
        sourceConfigTree = sourceMediaFile.getConfig()
        self._configurationTree.setValue("FileName", sourceConfigTree.getValue("FileName"))
        mediaType = sourceConfigTree.getValue("Type")
        self._configurationTree.setValue("Type", mediaType)
        self._configurationTree.setValue("SyncLength", sourceConfigTree.getValue("SyncLength"))
        self._configurationTree.setValue("QuantizeLength", sourceConfigTree.getValue("QuantizeLength"))
        if(mediaType == "Modulation"):
            self._configurationTree.removeParameter("MixMode")
            self._configurationTree.removeParameter("TimeModulationConfig")
            self._configurationTree.removeParameter("Effect1Config")
            self._configurationTree.removeParameter("Effect2Config")
            self._configurationTree.removeParameter("FadeConfig")
            self._configurationTree.removeParameter("MinValue")
            self._configurationTree.removeParameter("MaxValue")
            self._configurationTree.removeParameter("Smoother")
        else:
            self._configurationTree.addTextParameter("MixMode", "Add")#Default Add
            self._configurationTree.addTextParameter("TimeModulationConfig", self._defaultTimeModulationSettingsName)#Default Default
            self._configurationTree.addTextParameter("Effect1Config", self._defaultEffect1SettingsName)#Default MediaDefault1
            self._configurationTree.addTextParameter("Effect2Config", self._defaultEffect2SettingsName)#Default MediaDefault2
            self._configurationTree.addTextParameter("FadeConfig", self._defaultFadeSettingsName)#Default Default
            self._configurationTree.addFloatParameter("MinValue", 0.0)
            self._configurationTree.addFloatParameter("MaxValue", 1.0)
            self._configurationTree.addTextParameter("Smoother", "Off")
            self._configurationTree.setValue("MixMode", sourceConfigTree.getValue("MixMode"))
            self._configurationTree.setValue("TimeModulationConfig", sourceConfigTree.getValue("TimeModulationConfig"))
            self._configurationTree.setValue("Effect1Config", sourceConfigTree.getValue("Effect1Config"))
            self._configurationTree.setValue("Effect2Config", sourceConfigTree.getValue("Effect2Config"))
            self._configurationTree.setValue("FadeConfig", sourceConfigTree.getValue("FadeConfig"))
        self._configurationTree.setValue("ModulationValuesMode", sourceConfigTree.getValue("ModulationValuesMode"))

        if(mediaType == "VideoLoop"):
            self._configurationTree.addTextParameter("LoopMode", "Normal")
            loopMode = sourceConfigTree.getValue("LoopMode")
            if(loopMode != None):
                self._configurationTree.setValue("LoopMode", loopMode)
        else:
            self._configurationTree.removeParameter("LoopMode")

        if(mediaType == "Image"):
            self._configurationTree.addTextParameter("StartValues", "0.0|0.0|0.0")
            self._configurationTree.addTextParameter("EndValues", "0.0|0.0|0.0")
            startVal = sourceConfigTree.getValue("StartValues")
            if(startVal != None):
                self._configurationTree.setValue("StartValues", startVal)
            endVal = sourceConfigTree.getValue("EndValues")
            if(endVal != None):
                self._configurationTree.setValue("EndValues", endVal)
        else:
            self._configurationTree.removeParameter("StartValues")
            self._configurationTree.removeParameter("EndValues")

        if((mediaType == "Image") or (mediaType == "Camera")):
            self._configurationTree.addTextParameter("DisplayMode", "Crop")
            cropMode = sourceConfigTree.getValue("DisplayMode")
            if(cropMode != None):
                self._configurationTree.setValue("DisplayMode", cropMode)
        else:
            self._configurationTree.removeParameter("DisplayMode")

        if(mediaType == "ScrollImage"):
            self._configurationTree.addTextParameter("ScrollModulation", "None")
            self._configurationTree.addBoolParameter("HorizontalMode", True)
            self._configurationTree.addBoolParameter("ReverseMode", False)
            scrollVal = sourceConfigTree.getValue("ScrollModulation")
            if(scrollVal != None):
                self._configurationTree.setValue("ScrollModulation", scrollVal)
            horVal = sourceConfigTree.getValue("HorizontalMode")
            if(horVal != None):
                self._configurationTree.setValue("HorizontalMode", horVal)
            revMode = sourceConfigTree.getValue("ReverseMode")
            if(revMode != None):
                self._configurationTree.setValue("ReverseMode", revMode)
        else:
            self._configurationTree.removeParameter("ScrollModulation")
            self._configurationTree.removeParameter("HorizontalMode")
            self._configurationTree.removeParameter("ReverseMode")
            
        if((mediaType == "Sprite") or (mediaType == "Text")):
            self._configurationTree.addTextParameter("StartPosition", "0.5|0.5")
            self._configurationTree.addTextParameter("EndPosition", "0.5|0.5")
            self._configurationTree.addTextParameter("XModulation", "None")
            self._configurationTree.addTextParameter("YModulation", "None")
            startVal = sourceConfigTree.getValue("StartPosition")
            if(startVal != None):
                self._configurationTree.setValue("StartPosition", startVal)
            endVal = sourceConfigTree.getValue("EndPosition")
            if(endVal != None):
                self._configurationTree.setValue("EndPosition", endVal)
            xVal = sourceConfigTree.getValue("XModulation")
            if(xVal != None):
                self._configurationTree.setValue("XModulation", xVal)
            yVal = sourceConfigTree.getValue("YModulation")
            if(yVal != None):
                self._configurationTree.setValue("YModulation", yVal)
        else:
            self._configurationTree.removeParameter("StartPosition")
            self._configurationTree.removeParameter("EndPosition")
            self._configurationTree.removeParameter("XModulation")
            self._configurationTree.removeParameter("YModulation")

        if(mediaType == "Sprite"):
            self._configurationTree.addBoolParameter("InvertFirstFrameMask", False)
            invMode = sourceConfigTree.getValue("InvertFirstFrameMask")
            if(invMode != None):
                self._configurationTree.setValue("InvertFirstFrameMask", invMode)
        else:
            self._configurationTree.removeParameter("InvertFirstFrameMask")

        if(mediaType == "Text"):
            self._configurationTree.addTextParameter("Font", "Arial;32;#FFFFFF")
            font = sourceConfigTree.getValue("Font")
            if(font != None):
                self._configurationTree.setValue("Font", font)
        else:
            self._configurationTree.removeParameter("Font")

        if(mediaType == "ImageSequence"):
            self._configurationTree.addTextParameter("SequenceMode", "Time")
            self._configurationTree.addTextParameter("PlaybackModulation", "None")
            sequenceMode = sourceConfigTree.getValue("SequenceMode")
            if(sequenceMode != None):
                self._configurationTree.setValue("SequenceMode", sequenceMode)
            playBackMod = sourceConfigTree.getValue("PlaybackModulation")
            if(playBackMod != None):
                self._configurationTree.setValue("PlaybackModulation", playBackMod)
        else:
            self._configurationTree.removeParameter("SequenceMode")
            self._configurationTree.removeParameter("PlaybackModulation")

        if(mediaType == "KinectCamera"):
#            self._configurationTree.addTextParameter("DisplayModeModulation", "None")
            self._configurationTree.addTextParameter("FilterValues", "0.0|0.0|0.0|0.0")
            self._configurationTree.addTextParameter("ZoomValues", "0.5|0.5|0.5|0.5")
#            tmpModulation = sourceConfigTree.getValue("DisplayModeModulation")
#            if(tmpModulation != None):
#                self._configurationTree.setValue("DisplayModeModulation", tmpModulation)
            filterVal = sourceConfigTree.getValue("FilterValues")
            if(filterVal != None):
                self._configurationTree.setValue("FilterValues", filterVal)
            filterVal = sourceConfigTree.getValue("ZoomValues")
            if(filterVal != None):
                self._configurationTree.setValue("ZoomValues", filterVal)
        else:
            self._configurationTree.removeParameter("DisplayModeModulation")
            self._configurationTree.removeParameter("FilterValues")

        if(mediaType == "Modulation"):
            self._configurationTree.addTextParameter("FirstModulation", "None")
            tmpModulation = sourceConfigTree.getValue("FirstModulation")
            if(tmpModulation != None):
                self._configurationTree.setValue("FirstModulation", tmpModulation)
            self._configurationTree.addTextParameter("ModulationCombiner1", "Add")
            tmpMod = sourceConfigTree.getValue("ModulationCombiner1")
            if(tmpModulation != None):
                self._configurationTree.setValue("ModulationCombiner1", tmpMod)
            self._configurationTree.addTextParameter("SecondModulation", "None")
            tmpModulation = sourceConfigTree.getValue("SecondModulation")
            if(tmpModulation != None):
                self._configurationTree.setValue("SecondModulation", tmpModulation)
            self._configurationTree.addTextParameter("ModulationCombiner2", "Add")
            tmpMod = sourceConfigTree.getValue("ModulationCombiner2")
            if(tmpModulation != None):
                self._configurationTree.setValue("ModulationCombiner2", tmpMod)
            self._configurationTree.addTextParameter("ThirdModulation", "None")
            tmpModulation = sourceConfigTree.getValue("ThirdModulation")
            if(tmpModulation != None):
                self._configurationTree.setValue("ThirdModulation", tmpModulation)
            self._configurationTree.addFloatParameter("MinValue", 0.0)
            tmpValue = sourceConfigTree.getValue("MinValue")
            if(tmpValue != None):
                self._configurationTree.setValue("MinValue", tmpValue)
            self._configurationTree.addFloatParameter("MaxValue", 1.0)
            tmpValue = sourceConfigTree.getValue("MaxValue")
            if(tmpValue != None):
                self._configurationTree.setValue("MaxValue", tmpValue)
            self._configurationTree.addTextParameter("Smoother", "Off")
            tmpValue = sourceConfigTree.getValue("Smoother")
            if(tmpValue != None):
                self._configurationTree.setValue("Smoother", tmpValue)
        else:
            self._configurationTree.removeParameter("FirstModulation")
            self._configurationTree.removeParameter("ModulationCombiner1")
            self._configurationTree.removeParameter("SecondModulation")
            self._configurationTree.removeParameter("ModulationCombiner2")
            self._configurationTree.removeParameter("ThirdModulation")
            self._configurationTree.removeParameter("MinValue")
            self._configurationTree.removeParameter("MaxValue")
            self._configurationTree.removeParameter("Smoother")

    def countNumberOfTimeEffectTemplateUsed(self, effectsConfigName):
        returnNumber = 0
        for configName in ["Effect1Config", "Effect2Config"]:
            usedConfigName = self._configurationTree.getValue(configName)
            if(usedConfigName == effectsConfigName):
                returnNumber += 1
        return returnNumber

    def countNumberOfTimeTimeModulationTemplateUsed(self, effectsConfigName):
        returnNumber = 0
        for configName in ["TimeModulationConfig"]:
            usedConfigName = self._configurationTree.getValue(configName)
            if(usedConfigName == effectsConfigName):
                returnNumber += 1
        return returnNumber

    def countNumberOfTimeFadeTemplateUsed(self, fadeConfigName):
        returnNumber = 0
        for configName in ["FadeConfig"]:
            usedConfigName = self._configurationTree.getValue(configName)
            if(usedConfigName == fadeConfigName):
                returnNumber += 1
        return returnNumber

    def renameTimeModulationTemplateUsed(self, oldName, newName):
        for configName in ["TimeModulationConfig"]:
            usedConfigName = self._configurationTree.getValue(configName)
            if(usedConfigName == oldName):
                self._configurationTree.setValue(configName, newName)

    def renameEffectTemplateUsed(self, oldName, newName):
        for configName in ["Effect1Config", "Effect2Config"]:
            usedConfigName = self._configurationTree.getValue(configName)
            if(usedConfigName == oldName):
                self._configurationTree.setValue(configName, newName)

    def renameFadeTemplateUsed(self, oldName, newName):
        for configName in ["FadeConfig"]:
            usedConfigName = self._configurationTree.getValue(configName)
            if(usedConfigName == oldName):
                self._configurationTree.setValue(configName, newName)

    def verifyTimeModulationTemplateUsed(self, timeModulationConfigNameList):
        usedConfigName = self._configurationTree.getValue("TimeModulationConfig")
        nameOk = False
        for configName in timeModulationConfigNameList:
            if(usedConfigName == configName):
                nameOk = True
                break
        if(nameOk == False):
            self._configurationTree.setValue("TimeModulationConfig", "Default")

    def verifyEffectTemplateUsed(self, effectConfigNameList):
        usedConfigName = self._configurationTree.getValue("Effect1Config")
        nameOk = False
        for configName in effectConfigNameList:
            if(usedConfigName == configName):
                nameOk = True
                break
        if(nameOk == False):
            self._configurationTree.setValue("Effect1Config", self._defaultEffect1SettingsName)
        usedConfigName = self._configurationTree.getValue("Effect2Config")
        nameOk = False
        for configName in effectConfigNameList:
            if(usedConfigName == configName):
                nameOk = True
                break
        if(nameOk == False):
            self._configurationTree.setValue("Effect2Config", self._defaultEffect2SettingsName)

    def verifyFadeTemplateUsed(self, fadeConfigNameList):
        usedConfigName = self._configurationTree.getValue("FadeConfig")
        nameOk = False
        for configName in fadeConfigNameList:
            if(usedConfigName == configName):
                nameOk = True
                break
        if(nameOk == False):
            self._configurationTree.setValue("FadeConfig", self._defaultFadeSettingsName)

class MediaFileGui(object): #@UndefinedVariable
    def __init__(self, parentPlane, mainConfig, trackGui, noteRequestCallback, parentClass, cursorWidgetList, fxWidgetList):
        self._parentPlane = parentPlane
        self._mainConfig = mainConfig
        self._specialModulationHolder = self._mainConfig.getSpecialModulationHolder()
        self._videoDirectory = self._mainConfig.getGuiVideoDir()
        self._lastDialogDir = self._videoDirectory
        self._trackGui = trackGui
        self._requestThumbCallback = noteRequestCallback
        self._clearDragCursorCallback = parentClass.clearDragCursor
        self.setDragCursorCallback = parentClass.setDragCursor
        self.trackEffectFieldUpdateCallback = self._trackGui.updateEffectField
        self._trackUnselectEditor = self._trackGui.unselectButton
        self._midiTiming = MidiTiming()
        self._midiModulation = MidiModulation(None, self._midiTiming, self._specialModulationHolder)
        self._mediaFileGuiPanel = wx.Panel(self._parentPlane, wx.ID_ANY) #@UndefinedVariable

        self._config = None
        self._mixModes = MixMode()
        self._loopModes = VideoLoopMode()
        self._sequenceModes = ImageSequenceMode()
        self._typeModes = MediaTypes()

        self._trackThumbnailBitmap = wx.EmptyBitmap (42, 32, depth=3) #@UndefinedVariable

        self._doubbleBitmap = wx.Bitmap("graphics/timingDoubble.png") #@UndefinedVariable
        self._halfBitmap = wx.Bitmap("graphics/timingHalf.png") #@UndefinedVariable

        self._blankModeBitmap = wx.Bitmap("graphics/modeEmpty.png") #@UndefinedVariable
        self._modeBitmapCamera = wx.Bitmap("graphics/modeCamera.png") #@UndefinedVariable
        self._modeBitmapImage = wx.Bitmap("graphics/modeImage.png") #@UndefinedVariable
        self._modeBitmapImageScroll = wx.Bitmap("graphics/modeImageScroll.png") #@UndefinedVariable
        self._modeBitmapSprite = wx.Bitmap("graphics/modeImageSprite.png") #@UndefinedVariable
        self._modeBitmapText = wx.Bitmap("graphics/modeText.png") #@UndefinedVariable
        self._modeBitmapImageSeqModulation = wx.Bitmap("graphics/modeImageSeqModulation.png") #@UndefinedVariable
        self._modeBitmapImageSeqReTrigger = wx.Bitmap("graphics/modeImageSeqReTrigger.png") #@UndefinedVariable
        self._modeBitmapImageSeqTime = wx.Bitmap("graphics/modeImageSeqTime.png") #@UndefinedVariable
        self._modeBitmapLoop = wx.Bitmap("graphics/modeLoop.png") #@UndefinedVariable
        self._modeBitmapLoopReverse = wx.Bitmap("graphics/modeLoopReverse.png") #@UndefinedVariable
        self._modeBitmapPingPong = wx.Bitmap("graphics/modePingPong.png") #@UndefinedVariable
        self._modeBitmapPingPongReverse = wx.Bitmap("graphics/modePingPongReverse.png") #@UndefinedVariable
        self._modeBitmapPlayOnce = wx.Bitmap("graphics/modePlayOnce.png") #@UndefinedVariable
        self._modeBitmapPlayOnceReverse = wx.Bitmap("graphics/modePlayOnceReverse.png") #@UndefinedVariable
        self._modeBitmapGroup = wx.Bitmap("graphics/modeGroup.png") #@UndefinedVariable
        self._modeBitmapModulation = wx.Bitmap("graphics/modeModulation.png") #@UndefinedVariable

        self._modeImages = [self._modeBitmapLoop, self._modeBitmapLoopReverse, self._modeBitmapPingPong, self._modeBitmapPingPongReverse,
                            self._modeBitmapPlayOnce, self._modeBitmapPlayOnceReverse, self._modeBitmapCamera, self._modeBitmapImage,
                            self._modeBitmapImageScroll, self._modeBitmapSprite, self._modeBitmapText, self._modeBitmapImageSeqTime, self._modeBitmapImageSeqReTrigger,
                            self._modeBitmapImageSeqModulation, self._modeBitmapGroup, self._modeBitmapModulation]
        self._modeLabels = ["VideoLoop", "VideoLoopReverse", "VideoPingPong", "VideoPingPongReverse",
                           "VideoPlayOnce", "VideoPlayOnceReverse", "Camera", "Image",
                           "ScrollingImage", "Sprite", "Text", "ImageSeqTime", "ImageSeqReTrigger",
                           "ImageSeqModulation", "Group", "Modulation"]

        self._blankMixBitmap = wx.Bitmap("graphics/mixEmpty.png") #@UndefinedVariable
        self._emptyBitMap = wx.EmptyBitmap (40, 30, depth=3) #@UndefinedVariable
        self._mixBitmapAdd = wx.Bitmap("graphics/mixAdd.png") #@UndefinedVariable
        self._mixBitmapAlpha = wx.Bitmap("graphics/mixAlpha.png") #@UndefinedVariable
        self._mixBitmapDefault = wx.Bitmap("graphics/mixDefault.png") #@UndefinedVariable
        self._mixBitmapLumaKey = wx.Bitmap("graphics/mixLumaKey.png") #@UndefinedVariable
        self._mixBitmapWhiteLumaKey = wx.Bitmap("graphics/mixWhiteLumaKey.png") #@UndefinedVariable
        self._mixBitmapMultiply = wx.Bitmap("graphics/mixMultiply.png") #@UndefinedVariable
        self._mixBitmapReplace = wx.Bitmap("graphics/mixReplace.png") #@UndefinedVariable
        self._mixBitmapSubtract = wx.Bitmap("graphics/mixSubtract.png") #@UndefinedVariable

        self._mixImages = [self._mixBitmapDefault, self._mixBitmapAdd, self._mixBitmapSubtract, self._mixBitmapMultiply,
                            self._mixBitmapLumaKey, self._mixBitmapWhiteLumaKey, self._mixBitmapAlpha, self._mixBitmapReplace]
        self._mixLabels = self._mixModes.getChoices()

        self._wipeModeImages, self._wipeModeLabels = self._mainConfig.getFadeModeLists()
        self._wipeModeLabelsLong = ["Default", "FadeOut", "PushOut", "NoizeDisolve", "ZoomOut", "Flip"]

        self._blankFxBitmap = wx.Bitmap("graphics/fxEmpty.png") #@UndefinedVariable
        self._fxBitmapBlobDetect = wx.Bitmap("graphics/fxBlobDetect.png") #@UndefinedVariable
        self._fxBitmapBlur = wx.Bitmap("graphics/fxBlur.png") #@UndefinedVariable
        self._fxBitmapBlurMul = wx.Bitmap("graphics/fxBlurMultiply.png") #@UndefinedVariable
        self._fxBitmapFeedback = wx.Bitmap("graphics/fxFeedback.png") #@UndefinedVariable
        self._fxBitmapDelay = wx.Bitmap("graphics/fxDelay.png") #@UndefinedVariable
        self._fxBitmapColorize = wx.Bitmap("graphics/fxColorize.png") #@UndefinedVariable
        self._fxBitmapContrast = wx.Bitmap("graphics/fxContrast.png") #@UndefinedVariable
        self._fxBitmapDeSat = wx.Bitmap("graphics/fxDeSat.png") #@UndefinedVariable
        self._fxBitmapDist = wx.Bitmap("graphics/fxDist.png") #@UndefinedVariable
        self._fxBitmapEdge = wx.Bitmap("graphics/fxEdge.png") #@UndefinedVariable
        self._fxBitmapFlip = wx.Bitmap("graphics/fxFlip.png") #@UndefinedVariable
        self._fxBitmapHueSat = wx.Bitmap("graphics/fxHueSat.png") #@UndefinedVariable
        self._fxBitmapImageAdd = wx.Bitmap("graphics/fxImageAdd.png") #@UndefinedVariable
        self._fxBitmapInverse = wx.Bitmap("graphics/fxInverse.png") #@UndefinedVariable
        self._fxBitmapMirror = wx.Bitmap("graphics/fxMirror.png") #@UndefinedVariable
        self._fxBitmapPixelate = wx.Bitmap("graphics/fxPixelate.png") #@UndefinedVariable
        self._fxBitmapRays = wx.Bitmap("graphics/fxRays.png") #@UndefinedVariable
        self._fxBitmapRotate = wx.Bitmap("graphics/fxRotate.png") #@UndefinedVariable
        self._fxBitmapScroll = wx.Bitmap("graphics/fxScroll.png") #@UndefinedVariable
        self._fxBitmapSelfDiff = wx.Bitmap("graphics/fxSelfDiff.png") #@UndefinedVariable
        self._fxBitmapSlitScan = wx.Bitmap("graphics/fxSlitScan.png") #@UndefinedVariable
        self._fxBitmapThreshold = wx.Bitmap("graphics/fxThreshold.png") #@UndefinedVariable
        self._fxBitmapTVNoize = wx.Bitmap("graphics/fxTVNoize.png") #@UndefinedVariable
        self._fxBitmapVal2Hue = wx.Bitmap("graphics/fxVal2Hue.png") #@UndefinedVariable
        self._fxBitmapZoom = wx.Bitmap("graphics/fxZoom.png") #@UndefinedVariable

        self._helpBitmap = wx.Bitmap("graphics/helpButton.png") #@UndefinedVariable
        self._helpPressedBitmap = wx.Bitmap("graphics/helpButtonPressed.png") #@UndefinedVariable
        self._editBitmap = wx.Bitmap("graphics/editButton.png") #@UndefinedVariable
        self._editPressedBitmap = wx.Bitmap("graphics/editButtonPressed.png") #@UndefinedVariable
        self._editSelectedBitmap = wx.Bitmap("graphics/editButtonSelected.png") #@UndefinedVariable

        self._editBigBitmap = wx.Bitmap("graphics/editButtonBig.png") #@UndefinedVariable
        self._editBigPressedBitmap = wx.Bitmap("graphics/editButtonBigPressed.png") #@UndefinedVariable
        self._closeButtonBitmap = wx.Bitmap("graphics/closeButton.png") #@UndefinedVariable
        self._closeButtonPressedBitmap = wx.Bitmap("graphics/closeButtonPressed.png") #@UndefinedVariable
        self._newThumbButtonBitmap = wx.Bitmap("graphics/newThumbButton.png") #@UndefinedVariable
        self._newThumbButtonPressedBitmap = wx.Bitmap("graphics/newThumbButtonPressed.png") #@UndefinedVariable
        self._removeButtonBitmap = wx.Bitmap("graphics/removeButton.png") #@UndefinedVariable
        self._removeButtonPressedBitmap = wx.Bitmap("graphics/removeButtonPressed.png") #@UndefinedVariable
        self._saveBigBitmap = wx.Bitmap("graphics/saveButtonBig.png") #@UndefinedVariable
        self._saveBigPressedBitmap = wx.Bitmap("graphics/saveButtonBigPressed.png") #@UndefinedVariable
        self._saveBigGreyBitmap = wx.Bitmap("graphics/saveButtonBigGrey.png") #@UndefinedVariable

        self._configSizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable |||
        self._subPanelsList = []
        self._clipOverviewGuiPlane = wx.Panel(self._parentPlane, wx.ID_ANY, size=(88,288)) #@UndefinedVariable
        self._subPanelsList.append(self._clipOverviewGuiPlane)
        self._trackGuiPlane = wx.Panel(self._parentPlane, wx.ID_ANY, size=(300,-1)) #@UndefinedVariable
        self._subPanelsList.append(self._trackGuiPlane)
        self._noteConfigPanel = wx.Panel(self._parentPlane, wx.ID_ANY, size=(300,-1)) #@UndefinedVariable
        self._subPanelsList.append(self._noteConfigPanel)
        self._noteSlidersPanel = wx.Panel(self._parentPlane, wx.ID_ANY, size=(300,-1)) #@UndefinedVariable
        self._subPanelsList.append(self._noteSlidersPanel)
        self._timeModulationListPanel = wx.Panel(self._parentPlane, wx.ID_ANY, size=(500,-1)) #@UndefinedVariable
        self._subPanelsList.append(self._timeModulationListPanel)
        self._timeModulationConfigPanel = wx.Panel(self._parentPlane, wx.ID_ANY, size=(300,-1)) #@UndefinedVariable
        self._subPanelsList.append(self._timeModulationConfigPanel)
        self._effectListPanel = wx.Panel(self._parentPlane, wx.ID_ANY, size=(500,-1)) #@UndefinedVariable
        self._subPanelsList.append(self._effectListPanel)
        self._effectConfigPanel = wx.Panel(self._parentPlane, wx.ID_ANY, size=(300,-1)) #@UndefinedVariable
        self._subPanelsList.append(self._effectConfigPanel)
        self._effectImageListPanel = wx.Panel(self._parentPlane, wx.ID_ANY, size=(280,-1)) #@UndefinedVariable
        self._subPanelsList.append(self._effectImageListPanel)
        self._fadeListPanel = wx.Panel(self._parentPlane, wx.ID_ANY, size=(500,-1)) #@UndefinedVariable
        self._subPanelsList.append(self._fadeListPanel)
        self._fadeConfigPanel = wx.Panel(self._parentPlane, wx.ID_ANY, size=(300,-1)) #@UndefinedVariable
        self._subPanelsList.append(self._fadeConfigPanel)
        self._moulationConfigPanel = wx.Panel(self._parentPlane, wx.ID_ANY, size=(300,-1)) #@UndefinedVariable
        self._subPanelsList.append(self._moulationConfigPanel)
        self._slidersPanel = wx.Panel(self._parentPlane, wx.ID_ANY, size=(300,-1)) #@UndefinedVariable
        self._subPanelsList.append(self._slidersPanel)

        isFirst = True
        for panels in self._subPanelsList:
            panels.Bind(wx.EVT_LEFT_UP, self._onMouseRelease) #@UndefinedVariable
            self._configSizer.Add(panels)
            if(isFirst == True):
                isFirst = False
            else:
                self._configSizer.Hide(panels)

        self._parentPlane.Bind(wx.EVT_LEFT_UP, self._onMouseRelease) #@UndefinedVariable
        self._parentPlane.SetSizer(self._configSizer)

        self._clipOverviewGuiPlane.SetBackgroundColour((160,160,160))
        self.setupClipOverviewGui(self._clipOverviewGuiPlane, cursorWidgetList, fxWidgetList)

        self._trackGuiPlane.SetBackgroundColour((170,170,170))
        self._trackGuiSizer = wx.BoxSizer(wx.VERTICAL) #@UndefinedVariable ---
        self._trackGuiPlane.SetSizer(self._trackGuiSizer)
        self._trackGui.setupTrackGui(self._trackGuiPlane, self._trackGuiSizer, self._configSizer, self)

        self._noteConfigPanel.SetBackgroundColour((180,180,180))
        self._noteConfigSizer = wx.BoxSizer(wx.VERTICAL) #@UndefinedVariable ---
        self._noteConfigPanel.SetSizer(self._noteConfigSizer)

        self._noteSlidersPanel.SetBackgroundColour((170,170,170))
        self._noteSlidersSizer = wx.BoxSizer(wx.VERTICAL) #@UndefinedVariable ---
        self._noteSlidersPanel.SetSizer(self._noteSlidersSizer)
        self._setupNoteSlidersGui(self._noteSlidersPanel, self._noteSlidersSizer)

        self._timeModulationListPanel.SetBackgroundColour((160,160,160))
        self._timeModulationListSizer = wx.BoxSizer(wx.VERTICAL) #@UndefinedVariable ---
        self._timeModulationListPanel.SetSizer(self._timeModulationListSizer)
        self._mainConfig.setupTimeModulationsListGui(self._timeModulationListPanel, self._timeModulationListSizer, self._configSizer, self)

        self._timeModulationConfigPanel.SetBackgroundColour((170,170,170))
        self._timeModulationConfigSizer = wx.BoxSizer(wx.VERTICAL) #@UndefinedVariable ---
        self._timeModulationConfigPanel.SetSizer(self._timeModulationConfigSizer)
        self._mainConfig.setupTimeModulationsGui(self._timeModulationConfigPanel, self._timeModulationConfigSizer, self._configSizer, self)

        self._effectListPanel.SetBackgroundColour((160,160,160))
        self._effectListSizer = wx.BoxSizer(wx.VERTICAL) #@UndefinedVariable ---
        self._effectListPanel.SetSizer(self._effectListSizer)
        self._mainConfig.setupEffectsListGui(self._effectListPanel, self._effectListSizer, self._configSizer, self)

        self._effectConfigPanel.SetBackgroundColour((170,170,170))
        self._effectConfigSizer = wx.BoxSizer(wx.VERTICAL) #@UndefinedVariable ---
        self._effectConfigPanel.SetSizer(self._effectConfigSizer)
        self._mainConfig.setupEffectsGui(self._effectConfigPanel, self._effectConfigSizer, self._configSizer, self)

        self._effectImageListPanel.SetBackgroundColour((180,180,180))
        self._effectImageListSizer = wx.BoxSizer(wx.VERTICAL) #@UndefinedVariable ---
        self._effectImageListPanel.SetSizer(self._effectImageListSizer)
        self._mainConfig.setupEffectImageListGui(self._effectImageListPanel, self._effectImageListSizer, self._configSizer, self)

        self._fadeListPanel.SetBackgroundColour((160,160,160))
        self._fadeListSizer = wx.BoxSizer(wx.VERTICAL) #@UndefinedVariable ---
        self._fadeListPanel.SetSizer(self._fadeListSizer)
        self._mainConfig.setupFadeListGui(self._fadeListPanel, self._fadeListSizer, self._configSizer, self)

        self._fadeConfigPanel.SetBackgroundColour((170,170,170))
        self._fadeConfigSizer = wx.BoxSizer(wx.VERTICAL) #@UndefinedVariable ---
        self._fadeConfigPanel.SetSizer(self._fadeConfigSizer)
        self._mainConfig.setupFadeGui(self._fadeConfigPanel, self._fadeConfigSizer, self._configSizer, self)

        self._moulationConfigPanel.SetBackgroundColour((160,160,160))
        self._moulationConfigSizer = wx.BoxSizer(wx.VERTICAL) #@UndefinedVariable ---
        self._moulationConfigPanel.SetSizer(self._moulationConfigSizer)
        self._mainConfig.setupModulationGui(self._moulationConfigPanel, self._moulationConfigSizer, self._configSizer, self)

        self._slidersPanel.SetBackgroundColour((180,180,180))
        self._slidersSizer = wx.BoxSizer(wx.VERTICAL) #@UndefinedVariable ---
        self._slidersPanel.SetSizer(self._slidersSizer)
        self._mainConfig.setupEffectsSlidersGui(self._slidersPanel, self._slidersSizer, self._configSizer, self)

        self._parentPlane.Bind(wx.EVT_SIZE, self._onResize) #@UndefinedVariable

        headerLabel = wx.StaticText(self._noteConfigPanel, wx.ID_ANY, "Note configuration:") #@UndefinedVariable
        headerFont = headerLabel.GetFont()
        headerFont.SetWeight(wx.BOLD) #@UndefinedVariable
        if(sys.platform == "darwin"):
            headerFont.SetPointSize(12)
        headerLabel.SetFont(headerFont)
        self._noteConfigSizer.Add(headerLabel, proportion=0, flag=wx.EXPAND) #@UndefinedVariable

        self._fileName = ""
        self._cameraId = 0
        fileNameSizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable |||
        self._fileNameLabel = wx.StaticText(self._noteConfigPanel, wx.ID_ANY, "File name:") #@UndefinedVariable
        self._fileNameField = wx.TextCtrl(self._noteConfigPanel, wx.ID_ANY, self._fileName, size=(200, -1)) #@UndefinedVariable
        self._fileNameField.SetEditable(False)
        self._fileNameField.SetBackgroundColour((232,232,232))
        self._fileNameField.Bind(wx.EVT_TEXT, self._onUpdate) #@UndefinedVariable
        self._fileNameField.Bind(wx.EVT_LEFT_UP, self._onFileLeftRelease) #@UndefinedVariable
        fileOpenButton = PcnImageButton(self._noteConfigPanel, self._editBitmap, self._editPressedBitmap, (-1, -1), wx.ID_ANY, size=(17, 17)) #@UndefinedVariable
        fileOpenButton.Bind(wx.EVT_BUTTON, self._onOpenFile) #@UndefinedVariable
        fileNameSizer.Add(self._fileNameLabel, 1, wx.ALL, 5) #@UndefinedVariable
        fileNameSizer.Add(self._fileNameField, 1, wx.ALL, 5) #@UndefinedVariable
        fileNameSizer.Add(fileOpenButton, 0, wx.ALL, 5) #@UndefinedVariable
        self._noteConfigSizer.Add(fileNameSizer, proportion=1, flag=wx.EXPAND) #@UndefinedVariable

        self._fontSizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable |||
        self._fontLabel = wx.StaticText(self._noteConfigPanel, wx.ID_ANY, "Font:") #@UndefinedVariable
        self._fontField = wx.TextCtrl(self._noteConfigPanel, wx.ID_ANY, "Arial;32;#FFFFFF", size=(200, -1)) #@UndefinedVariable
        self._fontField.SetEditable(True)
        self._fontField.SetBackgroundColour((255,255,255))
        self._fontField.Bind(wx.EVT_TEXT, self._onUpdate) #@UndefinedVariable
        fileOpenButton = PcnImageButton(self._noteConfigPanel, self._editBitmap, self._editPressedBitmap, (-1, -1), wx.ID_ANY, size=(17, 17)) #@UndefinedVariable
        fileOpenButton.Bind(wx.EVT_BUTTON, self._onFontDialog) #@UndefinedVariable
        self._fontSizer.Add(self._fontLabel, 1, wx.ALL, 5) #@UndefinedVariable
        self._fontSizer.Add(self._fontField, 1, wx.ALL, 5) #@UndefinedVariable
        self._fontSizer.Add(fileOpenButton, 0, wx.ALL, 5) #@UndefinedVariable
        self._noteConfigSizer.Add(self._fontSizer, proportion=1, flag=wx.EXPAND) #@UndefinedVariable

        typeSizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable |||
        tmpText2 = wx.StaticText(self._noteConfigPanel, wx.ID_ANY, "Type:") #@UndefinedVariable
        self._typeField = wx.ComboBox(self._noteConfigPanel, wx.ID_ANY, size=(200, -1), choices=["VideoLoop"], style=wx.CB_READONLY) #@UndefinedVariable
        self._updateTypeChoices(self._typeField, "VideoLoop", "VideoLoop")
        typeHelpButton = PcnImageButton(self._noteConfigPanel, self._helpBitmap, self._helpPressedBitmap, (-1, -1), wx.ID_ANY, size=(17, 17)) #@UndefinedVariable
        typeHelpButton.Bind(wx.EVT_BUTTON, self._onTypeHelp) #@UndefinedVariable
        typeSizer.Add(tmpText2, 1, wx.ALL, 5) #@UndefinedVariable
        typeSizer.Add(self._typeField, 1, wx.ALL, 5) #@UndefinedVariable
        typeSizer.Add(typeHelpButton, 0, wx.ALL, 5) #@UndefinedVariable
        self._noteConfigSizer.Add(typeSizer, proportion=1, flag=wx.EXPAND) #@UndefinedVariable
        self._noteConfigPanel.Bind(wx.EVT_COMBOBOX, self._onTypeChosen, id=self._typeField.GetId()) #@UndefinedVariable

        self._subModeSizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable |||
        self._subModeLabel = wx.StaticText(self._noteConfigPanel, wx.ID_ANY, "Loop mode:") #@UndefinedVariable
        self._subModeField = wx.ComboBox(self._noteConfigPanel, wx.ID_ANY, size=(200, -1), choices=["Normal"], style=wx.CB_READONLY) #@UndefinedVariable
        self._updateLoopModeChoices(self._subModeField, "Normal", "Normal")
        subModeHelpButton = PcnImageButton(self._noteConfigPanel, self._helpBitmap, self._helpPressedBitmap, (-1, -1), wx.ID_ANY, size=(17, 17)) #@UndefinedVariable
        subModeHelpButton.Bind(wx.EVT_BUTTON, self._onSubModeHelp) #@UndefinedVariable
        self._subModeSizer.Add(self._subModeLabel, 1, wx.ALL, 5) #@UndefinedVariable
        self._subModeSizer.Add(self._subModeField, 1, wx.ALL, 5) #@UndefinedVariable
        self._subModeSizer.Add(subModeHelpButton, 0, wx.ALL, 5) #@UndefinedVariable
        self._noteConfigSizer.Add(self._subModeSizer, proportion=1, flag=wx.EXPAND) #@UndefinedVariable
        self._noteConfigPanel.Bind(wx.EVT_COMBOBOX, self._onSubModeChosen, id=self._subModeField.GetId()) #@UndefinedVariable

        self._subMode2Sizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable |||
        self._subMode2Label = wx.StaticText(self._noteConfigPanel, wx.ID_ANY, "Reverse scrolling:") #@UndefinedVariable
        self._subMode2Field = wx.ComboBox(self._noteConfigPanel, wx.ID_ANY, size=(200, -1), choices=["Off"], style=wx.CB_READONLY) #@UndefinedVariable
        self._updateReverseModeChoices(self._subMode2Field, "Off", "Off")
        subMode2HelpButton = PcnImageButton(self._noteConfigPanel, self._helpBitmap, self._helpPressedBitmap, (-1, -1), wx.ID_ANY, size=(17, 17)) #@UndefinedVariable
        subMode2HelpButton.Bind(wx.EVT_BUTTON, self._onSubMode2Help) #@UndefinedVariable
        self._subMode2Sizer.Add(self._subMode2Label, 1, wx.ALL, 5) #@UndefinedVariable
        self._subMode2Sizer.Add(self._subMode2Field, 1, wx.ALL, 5) #@UndefinedVariable
        self._subMode2Sizer.Add(subMode2HelpButton, 0, wx.ALL, 5) #@UndefinedVariable
        self._noteConfigSizer.Add(self._subMode2Sizer, proportion=1, flag=wx.EXPAND) #@UndefinedVariable
        self._noteConfigPanel.Bind(wx.EVT_COMBOBOX, self._onSubMode2Chosen, id=self._subMode2Field.GetId()) #@UndefinedVariable

        self._subModulationSizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable |||
        self._subModulationLabel = wx.StaticText(self._noteConfigPanel, wx.ID_ANY, "Playback modulation:") #@UndefinedVariable
        self._subModulationField = wx.TextCtrl(self._noteConfigPanel, wx.ID_ANY, "None", size=(200, -1)) #@UndefinedVariable
        self._subModulationField.SetInsertionPoint(0)
        self._subModulationField.Bind(wx.EVT_TEXT, self._onUpdate) #@UndefinedVariable
        self._subModulationEditButton = PcnImageButton(self._noteConfigPanel, self._editBitmap, self._editPressedBitmap, (-1, -1), wx.ID_ANY, size=(17, 17)) #@UndefinedVariable
        self._subModulationEditButton.Bind(wx.EVT_BUTTON, self._onSubmodulationEdit) #@UndefinedVariable
        self._subModulationSizer.Add(self._subModulationLabel, 1, wx.ALL, 5) #@UndefinedVariable
        self._subModulationSizer.Add(self._subModulationField, 1, wx.ALL, 5) #@UndefinedVariable
        self._subModulationSizer.Add(self._subModulationEditButton, 0, wx.ALL, 5) #@UndefinedVariable
        self._noteConfigSizer.Add(self._subModulationSizer, proportion=1, flag=wx.EXPAND) #@UndefinedVariable

        self._subModulationMode1Sizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable |||
        self._subModulationMode1Label = wx.StaticText(self._noteConfigPanel, wx.ID_ANY, "Combine 1 and 2:") #@UndefinedVariable
        self._subModulationMode1Field = wx.ComboBox(self._noteConfigPanel, wx.ID_ANY, size=(200, -1), choices=["Add"], style=wx.CB_READONLY) #@UndefinedVariable
        self._updateSubModulationMode1Choices(self._subModulationMode1Field, "Add", "Add")
        subModulationMode1HelpButton = PcnImageButton(self._noteConfigPanel, self._helpBitmap, self._helpPressedBitmap, (-1, -1), wx.ID_ANY, size=(17, 17)) #@UndefinedVariable
        subModulationMode1HelpButton.Bind(wx.EVT_BUTTON, self._onsubModulationMode1Help) #@UndefinedVariable
        self._subModulationMode1Sizer.Add(self._subModulationMode1Label, 1, wx.ALL, 5) #@UndefinedVariable
        self._subModulationMode1Sizer.Add(self._subModulationMode1Field, 1, wx.ALL, 5) #@UndefinedVariable
        self._subModulationMode1Sizer.Add(subModulationMode1HelpButton, 0, wx.ALL, 5) #@UndefinedVariable
        self._noteConfigSizer.Add(self._subModulationMode1Sizer, proportion=1, flag=wx.EXPAND) #@UndefinedVariable
        self._noteConfigPanel.Bind(wx.EVT_COMBOBOX, self._onsubModulationMode1Chosen, id=self._subModulationMode1Field.GetId()) #@UndefinedVariable

        self._subModulation2Sizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable |||
        self._subModulation2Label = wx.StaticText(self._noteConfigPanel, wx.ID_ANY, "Y position modulation:") #@UndefinedVariable
        self._subModulation2Field = wx.TextCtrl(self._noteConfigPanel, wx.ID_ANY, "None", size=(200, -1)) #@UndefinedVariable
        self._subModulation2Field.SetInsertionPoint(0)
        self._subModulation2Field.Bind(wx.EVT_TEXT, self._onUpdate) #@UndefinedVariable
        self._subModulation2EditButton = PcnImageButton(self._noteConfigPanel, self._editBitmap, self._editPressedBitmap, (-1, -1), wx.ID_ANY, size=(17, 17)) #@UndefinedVariable
        self._subModulation2EditButton.Bind(wx.EVT_BUTTON, self._onSubmodulation2Edit) #@UndefinedVariable
        self._subModulation2Sizer.Add(self._subModulation2Label, 1, wx.ALL, 5) #@UndefinedVariable
        self._subModulation2Sizer.Add(self._subModulation2Field, 1, wx.ALL, 5) #@UndefinedVariable
        self._subModulation2Sizer.Add(self._subModulation2EditButton, 0, wx.ALL, 5) #@UndefinedVariable
        self._noteConfigSizer.Add(self._subModulation2Sizer, proportion=1, flag=wx.EXPAND) #@UndefinedVariable

        self._subModulationMode2Sizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable |||
        self._subModulationMode2Label = wx.StaticText(self._noteConfigPanel, wx.ID_ANY, "Combine 2 and 3:") #@UndefinedVariable
        self._subModulationMode2Field = wx.ComboBox(self._noteConfigPanel, wx.ID_ANY, size=(200, -1), choices=["Add"], style=wx.CB_READONLY) #@UndefinedVariable
        self._updateSubModulationMode2Choices(self._subModulationMode2Field, "Add", "Add")
        subModulationMode2HelpButton = PcnImageButton(self._noteConfigPanel, self._helpBitmap, self._helpPressedBitmap, (-1, -1), wx.ID_ANY, size=(17, 17)) #@UndefinedVariable
        subModulationMode2HelpButton.Bind(wx.EVT_BUTTON, self._onsubModulationMode2Help) #@UndefinedVariable
        self._subModulationMode2Sizer.Add(self._subModulationMode2Label, 1, wx.ALL, 5) #@UndefinedVariable
        self._subModulationMode2Sizer.Add(self._subModulationMode2Field, 1, wx.ALL, 5) #@UndefinedVariable
        self._subModulationMode2Sizer.Add(subModulationMode2HelpButton, 0, wx.ALL, 5) #@UndefinedVariable
        self._noteConfigSizer.Add(self._subModulationMode2Sizer, proportion=1, flag=wx.EXPAND) #@UndefinedVariable
        self._subModulationMode2Field.Bind(wx.EVT_COMBOBOX, self._onUpdate) #@UndefinedVariable

        self._subModulation3Sizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable |||
        self._subModulation3Label = wx.StaticText(self._noteConfigPanel, wx.ID_ANY, "ThirdModulation:") #@UndefinedVariable
        self._subModulation3Field = wx.TextCtrl(self._noteConfigPanel, wx.ID_ANY, "None", size=(200, -1)) #@UndefinedVariable
        self._subModulation3Field.SetInsertionPoint(0)
        self._subModulation3Field.Bind(wx.EVT_TEXT, self._onUpdate) #@UndefinedVariable
        self._subModulation3EditButton = PcnImageButton(self._noteConfigPanel, self._editBitmap, self._editPressedBitmap, (-1, -1), wx.ID_ANY, size=(17, 17)) #@UndefinedVariable
        self._subModulation3EditButton.Bind(wx.EVT_BUTTON, self._onSubmodulation3Edit) #@UndefinedVariable
        self._subModulation3Sizer.Add(self._subModulation3Label, 1, wx.ALL, 5) #@UndefinedVariable
        self._subModulation3Sizer.Add(self._subModulation3Field, 1, wx.ALL, 5) #@UndefinedVariable
        self._subModulation3Sizer.Add(self._subModulation3EditButton, 0, wx.ALL, 5) #@UndefinedVariable
        self._noteConfigSizer.Add(self._subModulation3Sizer, proportion=1, flag=wx.EXPAND) #@UndefinedVariable

        self._values1Sizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable |||
        self._values1Label = wx.StaticText(self._noteConfigPanel, wx.ID_ANY, "Values 1:") #@UndefinedVariable
        self._values1Field = wx.TextCtrl(self._noteConfigPanel, wx.ID_ANY, "0.0|0.0|0.0", size=(200, -1)) #@UndefinedVariable
        self._values1Field.SetInsertionPoint(0)
        self._values1Field.Bind(wx.EVT_TEXT, self._onUpdate) #@UndefinedVariable
        self._values1EditButton = PcnImageButton(self._noteConfigPanel, self._editBitmap, self._editPressedBitmap, (-1, -1), wx.ID_ANY, size=(17, 17)) #@UndefinedVariable
        self._values1EditButton.Bind(wx.EVT_BUTTON, self._onValues1Edit) #@UndefinedVariable
        self._values1Sizer.Add(self._values1Label, 1, wx.ALL, 5) #@UndefinedVariable
        self._values1Sizer.Add(self._values1Field, 1, wx.ALL, 5) #@UndefinedVariable
        self._values1Sizer.Add(self._values1EditButton, 0, wx.ALL, 5) #@UndefinedVariable
        self._noteConfigSizer.Add(self._values1Sizer, proportion=1, flag=wx.EXPAND) #@UndefinedVariable

        self._values2Sizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable |||
        self._values2Label = wx.StaticText(self._noteConfigPanel, wx.ID_ANY, "Values 2:") #@UndefinedVariable
        self._values2Field = wx.TextCtrl(self._noteConfigPanel, wx.ID_ANY, "0.0|0.0|0.0", size=(200, -1)) #@UndefinedVariable
        self._values2Field.SetInsertionPoint(0)
        self._values2Field.Bind(wx.EVT_TEXT, self._onUpdate) #@UndefinedVariable
        self._values2EditButton = PcnImageButton(self._noteConfigPanel, self._editBitmap, self._editPressedBitmap, (-1, -1), wx.ID_ANY, size=(17, 17)) #@UndefinedVariable
        self._values2EditButton.Bind(wx.EVT_BUTTON, self._onValues2Edit) #@UndefinedVariable
        self._values2Sizer.Add(self._values2Label, 1, wx.ALL, 5) #@UndefinedVariable
        self._values2Sizer.Add(self._values2Field, 1, wx.ALL, 5) #@UndefinedVariable
        self._values2Sizer.Add(self._values2EditButton, 0, wx.ALL, 5) #@UndefinedVariable
        self._noteConfigSizer.Add(self._values2Sizer, proportion=1, flag=wx.EXPAND) #@UndefinedVariable

        self._subModulationSmootherSizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable |||
        self._subModulationSmootherLabel = wx.StaticText(self._noteConfigPanel, wx.ID_ANY, "Smooth sum:") #@UndefinedVariable
        self._subModulationSmootherField = wx.ComboBox(self._noteConfigPanel, wx.ID_ANY, size=(200, -1), choices=["Off"], style=wx.CB_READONLY) #@UndefinedVariable
        self._updateSubModulationSmootherChoices(self._subModulationSmootherField, "Off", "Off")
        subModulationSmootherHelpButton = PcnImageButton(self._noteConfigPanel, self._helpBitmap, self._helpPressedBitmap, (-1, -1), wx.ID_ANY, size=(17, 17)) #@UndefinedVariable
        subModulationSmootherHelpButton.Bind(wx.EVT_BUTTON, self._onsubModulationSmootherHelp) #@UndefinedVariable
        self._subModulationSmootherSizer.Add(self._subModulationSmootherLabel, 1, wx.ALL, 5) #@UndefinedVariable
        self._subModulationSmootherSizer.Add(self._subModulationSmootherField, 1, wx.ALL, 5) #@UndefinedVariable
        self._subModulationSmootherSizer.Add(subModulationSmootherHelpButton, 0, wx.ALL, 5) #@UndefinedVariable
        self._noteConfigSizer.Add(self._subModulationSmootherSizer, proportion=1, flag=wx.EXPAND) #@UndefinedVariable
        self._subModulationSmootherField.Bind(wx.EVT_COMBOBOX, self._onUpdate) #@UndefinedVariable

        self._midiNote = 24
        noteSizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable |||
        tmpText3 = wx.StaticText(self._noteConfigPanel, wx.ID_ANY, "Note:") #@UndefinedVariable
        self._noteField = wx.TextCtrl(self._noteConfigPanel, wx.ID_ANY, noteToNoteString(self._midiNote), size=(200, -1)) #@UndefinedVariable
        self._noteField.SetEditable(False)
        self._noteField.SetBackgroundColour((232,232,232))
        self._noteField.Bind(wx.EVT_TEXT, self._onUpdate) #@UndefinedVariable
        noteHelpButton = PcnImageButton(self._noteConfigPanel, self._helpBitmap, self._helpPressedBitmap, (-1, -1), wx.ID_ANY, size=(17, 17)) #@UndefinedVariable
        noteHelpButton.Bind(wx.EVT_BUTTON, self._onNoteHelp) #@UndefinedVariable
        noteSizer.Add(tmpText3, 1, wx.ALL, 5) #@UndefinedVariable
        noteSizer.Add(self._noteField, 1, wx.ALL, 5) #@UndefinedVariable
        noteSizer.Add(noteHelpButton, 0, wx.ALL, 5) #@UndefinedVariable
        self._noteConfigSizer.Add(noteSizer, proportion=1, flag=wx.EXPAND) #@UndefinedVariable

        self._syncSizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable |||
        self._syncFieldLabel = wx.StaticText(self._noteConfigPanel, wx.ID_ANY, "Synchronization length:") #@UndefinedVariable
        self._syncField = wx.TextCtrl(self._noteConfigPanel, wx.ID_ANY, "4.0", size=(200, -1)) #@UndefinedVariable
        self._syncField.SetInsertionPoint(0)
        self._syncField.Bind(wx.EVT_TEXT, self._onUpdate) #@UndefinedVariable
        syncHelpButton = PcnImageButton(self._noteConfigPanel, self._helpBitmap, self._helpPressedBitmap, (-1, -1), wx.ID_ANY, size=(17, 17)) #@UndefinedVariable
        syncHelpButton.Bind(wx.EVT_BUTTON, self._onSyncHelp) #@UndefinedVariable
        self._syncSizer.Add(self._syncFieldLabel, 1, wx.ALL, 5) #@UndefinedVariable
        self._syncSizer.Add(self._syncField, 1, wx.ALL, 5) #@UndefinedVariable
        self._syncSizer.Add(syncHelpButton, 0, wx.ALL, 5) #@UndefinedVariable
        self._noteConfigSizer.Add(self._syncSizer, proportion=1, flag=wx.EXPAND) #@UndefinedVariable

        quantizeSizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable |||
        tmpText5 = wx.StaticText(self._noteConfigPanel, wx.ID_ANY, "Quantization:") #@UndefinedVariable
        self._quantizeField = wx.TextCtrl(self._noteConfigPanel, wx.ID_ANY, "1.0", size=(200, -1)) #@UndefinedVariable
        self._quantizeField.SetInsertionPoint(0)
        self._quantizeField.Bind(wx.EVT_TEXT, self._onUpdate) #@UndefinedVariable
        quantizeHelpButton = PcnImageButton(self._noteConfigPanel, self._helpBitmap, self._helpPressedBitmap, (-1, -1), wx.ID_ANY, size=(17, 17)) #@UndefinedVariable
        quantizeHelpButton.Bind(wx.EVT_BUTTON, self._onQuantizeHelp) #@UndefinedVariable
        quantizeSizer.Add(tmpText5, 1, wx.ALL, 5) #@UndefinedVariable
        quantizeSizer.Add(self._quantizeField, 1, wx.ALL, 5) #@UndefinedVariable
        quantizeSizer.Add(quantizeHelpButton, 0, wx.ALL, 5) #@UndefinedVariable
        self._noteConfigSizer.Add(quantizeSizer, proportion=1, flag=wx.EXPAND) #@UndefinedVariable

        self._mixSizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable |||
        tmpText6 = wx.StaticText(self._noteConfigPanel, wx.ID_ANY, "Mix mode:") #@UndefinedVariable
        self._mixField = wx.ComboBox(self._noteConfigPanel, wx.ID_ANY, size=(200, -1), choices=["Add"], style=wx.CB_READONLY) #@UndefinedVariable
        self._updateMixModeChoices(self._mixField, "Add", "Add")
        self._mixField.Bind(wx.EVT_COMBOBOX, self._onUpdate) #@UndefinedVariable
        mixHelpButton = PcnImageButton(self._noteConfigPanel, self._helpBitmap, self._helpPressedBitmap, (-1, -1), wx.ID_ANY, size=(17, 17)) #@UndefinedVariable
        mixHelpButton.Bind(wx.EVT_BUTTON, self._onMixHelp) #@UndefinedVariable
        self._mixSizer.Add(tmpText6, 1, wx.ALL, 5) #@UndefinedVariable
        self._mixSizer.Add(self._mixField, 1, wx.ALL, 5) #@UndefinedVariable
        self._mixSizer.Add(mixHelpButton, 0, wx.ALL, 5) #@UndefinedVariable
        self._noteConfigSizer.Add(self._mixSizer, proportion=1, flag=wx.EXPAND) #@UndefinedVariable

        self._timeModulationSizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable |||
        tmpText7 = wx.StaticText(self._noteConfigPanel, wx.ID_ANY, "Time modulation template:") #@UndefinedVariable
        self._timeModulationField = wx.ComboBox(self._noteConfigPanel, wx.ID_ANY, size=(200, -1), choices=["Default"], style=wx.CB_READONLY) #@UndefinedVariable
        self._updateTimeModulationChoices(self._timeModulationField, "Default", "Default")
        self._timeModulationField.Bind(wx.EVT_COMBOBOX, self._onUpdate) #@UndefinedVariable
        self._timeModulationButton = PcnImageButton(self._noteConfigPanel, self._editBitmap, self._editPressedBitmap, (-1, -1), wx.ID_ANY, size=(17, 17)) #@UndefinedVariable
        self._timeModulationButton.Bind(wx.EVT_BUTTON, self._onTimeModulationEdit) #@UndefinedVariable
        self._timeModulationSizer.Add(tmpText7, 1, wx.ALL, 5) #@UndefinedVariable
        self._timeModulationSizer.Add(self._timeModulationField, 1, wx.ALL, 5) #@UndefinedVariable
        self._timeModulationSizer.Add(self._timeModulationButton, 0, wx.ALL, 5) #@UndefinedVariable
        self._noteConfigSizer.Add(self._timeModulationSizer, proportion=1, flag=wx.EXPAND) #@UndefinedVariable

        self._effect1Sizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable |||
        tmpText7 = wx.StaticText(self._noteConfigPanel, wx.ID_ANY, "Effect 1 template:") #@UndefinedVariable
        self._effect1Field = wx.ComboBox(self._noteConfigPanel, wx.ID_ANY, size=(200, -1), choices=["MediaDefault1"], style=wx.CB_READONLY) #@UndefinedVariable
        self._updateEffecChoices(self._effect1Field, "MediaDefault1", "MediaDefault1")
        self._effect1Field.Bind(wx.EVT_COMBOBOX, self._onUpdate) #@UndefinedVariable
        self._effect1Button = PcnImageButton(self._noteConfigPanel, self._editBitmap, self._editPressedBitmap, (-1, -1), wx.ID_ANY, size=(17, 17)) #@UndefinedVariable
        self._effect1Button.Bind(wx.EVT_BUTTON, self._onEffect1Edit) #@UndefinedVariable
        self._effect1Sizer.Add(tmpText7, 1, wx.ALL, 5) #@UndefinedVariable
        self._effect1Sizer.Add(self._effect1Field, 1, wx.ALL, 5) #@UndefinedVariable
        self._effect1Sizer.Add(self._effect1Button, 0, wx.ALL, 5) #@UndefinedVariable
        self._noteConfigSizer.Add(self._effect1Sizer, proportion=1, flag=wx.EXPAND) #@UndefinedVariable

        self._effect2Sizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable |||
        tmpText7 = wx.StaticText(self._noteConfigPanel, wx.ID_ANY, "Effect 2 template:") #@UndefinedVariable
        self._effect2Field = wx.ComboBox(self._noteConfigPanel, wx.ID_ANY, size=(200, -1), choices=["MediaDefault2"], style=wx.CB_READONLY) #@UndefinedVariable
        self._updateEffecChoices(self._effect2Field, "MediaDefault2", "MediaDefault2")
        self._effect2Field.Bind(wx.EVT_COMBOBOX, self._onUpdate) #@UndefinedVariable
        self._effect2Button = PcnImageButton(self._noteConfigPanel, self._editBitmap, self._editPressedBitmap, (-1, -1), wx.ID_ANY, size=(17, 17)) #@UndefinedVariable
        self._effect2Button.Bind(wx.EVT_BUTTON, self._onEffect2Edit) #@UndefinedVariable
        self._effect2Sizer.Add(tmpText7, 1, wx.ALL, 5) #@UndefinedVariable
        self._effect2Sizer.Add(self._effect2Field, 1, wx.ALL, 5) #@UndefinedVariable
        self._effect2Sizer.Add(self._effect2Button, 0, wx.ALL, 5) #@UndefinedVariable
        self._noteConfigSizer.Add(self._effect2Sizer, proportion=1, flag=wx.EXPAND) #@UndefinedVariable

        self._fadeSizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable |||
        tmpText7 = wx.StaticText(self._noteConfigPanel, wx.ID_ANY, "Fade template:") #@UndefinedVariable
        self._fadeField = wx.ComboBox(self._noteConfigPanel, wx.ID_ANY, size=(200, -1), choices=["Default"], style=wx.CB_READONLY) #@UndefinedVariable
        self._updateFadeChoices(self._fadeField, "Default", "Default")
        self._fadeField.Bind(wx.EVT_COMBOBOX, self._onUpdate) #@UndefinedVariable
        self._fadeButton = PcnImageButton(self._noteConfigPanel, self._editBitmap, self._editPressedBitmap, (-1, -1), wx.ID_ANY, size=(17, 17)) #@UndefinedVariable
        self._fadeButton.Bind(wx.EVT_BUTTON, self._onFadeEdit) #@UndefinedVariable
        self._fadeSizer.Add(tmpText7, 1, wx.ALL, 5) #@UndefinedVariable
        self._fadeSizer.Add(self._fadeField, 1, wx.ALL, 5) #@UndefinedVariable
        self._fadeSizer.Add(self._fadeButton, 0, wx.ALL, 5) #@UndefinedVariable
        self._noteConfigSizer.Add(self._fadeSizer, proportion=1, flag=wx.EXPAND) #@UndefinedVariable

        self._buttonsSizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable |||
        closeButton = PcnImageButton(self._noteConfigPanel, self._closeButtonBitmap, self._closeButtonPressedBitmap, (-1, -1), wx.ID_ANY, size=(55, 17)) #@UndefinedVariable
        closeButton.Bind(wx.EVT_BUTTON, self._onCloseButton) #@UndefinedVariable
        thumbButton = PcnImageButton(self._noteConfigPanel, self._newThumbButtonBitmap, self._newThumbButtonPressedBitmap, (-1, -1), wx.ID_ANY, size=(90, 17)) #@UndefinedVariable
        thumbButton.Bind(wx.EVT_BUTTON, self._onThumbButton) #@UndefinedVariable
        deleteButton = PcnImageButton(self._noteConfigPanel, self._removeButtonBitmap, self._removeButtonPressedBitmap, (-1, -1), wx.ID_ANY, size=(67, 17)) #@UndefinedVariable
        deleteButton.Bind(wx.EVT_BUTTON, self._onDeleteButton) #@UndefinedVariable
        self._saveButton = PcnImageButton(self._noteConfigPanel, self._saveBigGreyBitmap, self._saveBigGreyBitmap, (-1, -1), wx.ID_ANY, size=(52, 17)) #@UndefinedVariable
        self._saveButton.Bind(wx.EVT_BUTTON, self._onSaveButton) #@UndefinedVariable
        self._buttonsSizer.Add(closeButton, 0, wx.ALL, 5) #@UndefinedVariable
        self._buttonsSizer.Add(thumbButton, 0, wx.ALL, 5) #@UndefinedVariable
        self._buttonsSizer.Add(deleteButton, 0, wx.ALL, 5) #@UndefinedVariable
        self._buttonsSizer.Add(self._saveButton, 0, wx.ALL, 5) #@UndefinedVariable
        self._noteConfigSizer.Add(self._buttonsSizer, proportion=1, flag=wx.EXPAND) #@UndefinedVariable

        self._mainSelection = self.MainSelection.Unselected
        self._selectedEditor = self.EditSelection.Unselected
        self._noteGuiOpen = False
        self._isEffectImageListOpen = False
        self._activeTrackClipNoteId = -1
        self._type = "VideoLoop"
        self._setupSubConfig(self._config)

    def setupClipOverviewGui(self, overviewPanel, cursorWidgetList, fxWidgetList):
        self._mainClipOverviewPlane = overviewPanel

        isMac = False
        if(sys.platform == "darwin"):
            isMac = True
            font = wx.SystemSettings_GetFont(wx.SYS_SYSTEM_FONT) #@UndefinedVariable
            font.SetPointSize(10)

        txt = wx.StaticText(self._mainClipOverviewPlane, wx.ID_ANY, "NOTE CLIP:", pos=(4, 2)) #@UndefinedVariable
        if(isMac == True):
            txt.SetFont(font)
        self._overviewClipButton = PcnKeyboardButton(self._mainClipOverviewPlane, self._trackThumbnailBitmap, (6, 18), wx.ID_ANY, size=(42, 32), isBlack=False) #@UndefinedVariable
        cursorWidgetList.append(self._overviewClipButton)
        self._overviewClipButton.setFrqameAddingFunction(addTrackButtonFrame)
        self._overviewClipButton.Bind(wx.EVT_BUTTON, self._onOverviewClipEditButton) #@UndefinedVariable
        self._overviewClipButton.setBitmap(self._emptyBitMap)

        txt = wx.StaticText(self._mainClipOverviewPlane, wx.ID_ANY, "Type:", pos=(51, 18)) #@UndefinedVariable
        if(isMac == True):
            txt.SetFont(font)
        self._overviewClipModeButton = PcnImageButton(self._mainClipOverviewPlane, self._blankModeBitmap, self._blankModeBitmap, (52, 32), wx.ID_ANY, size=(25, 16)) #@UndefinedVariable
        cursorWidgetList.append(self._overviewClipModeButton)
        self._overviewClipModeButtonPopup = PcnPopupMenu(self, self._modeImages, self._modeLabels, self._onClipModeChosen)

        txt = wx.StaticText(self._mainClipOverviewPlane, wx.ID_ANY, "Length:", pos=(12, 54)) #@UndefinedVariable
        if(isMac == True):
            txt.SetFont(font)
        self._overviewClipLengthLabel = wx.StaticText(self._mainClipOverviewPlane, wx.ID_ANY, "N/A", pos=(16, 68)) #@UndefinedVariable
        if(isMac == True):
            self._overviewClipLengthLabel.SetFont(font)
        lengthDoubbleButton = PcnImageButton(self._mainClipOverviewPlane, self._doubbleBitmap, self._doubbleBitmap, (48, 69), wx.ID_ANY, size=(16, 12)) #@UndefinedVariable
        cursorWidgetList.append(lengthDoubbleButton)
        lengthHalfButton = PcnImageButton(self._mainClipOverviewPlane, self._halfBitmap, self._halfBitmap, (65, 69), wx.ID_ANY, size=(16, 12)) #@UndefinedVariable
        cursorWidgetList.append(lengthHalfButton)
        lengthDoubbleButton.Bind(wx.EVT_BUTTON, self._onLengthDoubbleButton) #@UndefinedVariable
        lengthHalfButton.Bind(wx.EVT_BUTTON, self._onLengthHalfButton) #@UndefinedVariable
        txt = wx.StaticText(self._mainClipOverviewPlane, wx.ID_ANY, "Quantize:", pos=(12, 82)) #@UndefinedVariable
        if(isMac == True):
            txt.SetFont(font)
        self._overviewClipQuantizeLabel = wx.StaticText(self._mainClipOverviewPlane, wx.ID_ANY, "N/A", pos=(16, 98)) #@UndefinedVariable
        if(isMac == True):
            self._overviewClipQuantizeLabel.SetFont(font)
        syncDoubbleButton = PcnImageButton(self._mainClipOverviewPlane, self._doubbleBitmap, self._doubbleBitmap, (48, 99), wx.ID_ANY, size=(16, 12)) #@UndefinedVariable
        cursorWidgetList.append(syncDoubbleButton)
        syncHalfButton = PcnImageButton(self._mainClipOverviewPlane, self._halfBitmap, self._halfBitmap, (65, 99), wx.ID_ANY, size=(16, 12)) #@UndefinedVariable
        cursorWidgetList.append(syncHalfButton)
        syncDoubbleButton.Bind(wx.EVT_BUTTON, self._onSyncDoubbleButton) #@UndefinedVariable
        syncHalfButton.Bind(wx.EVT_BUTTON, self._onSyncHalfButton) #@UndefinedVariable

        txt = wx.StaticText(self._mainClipOverviewPlane, wx.ID_ANY, "FX1:", pos=(8, 118)) #@UndefinedVariable
        if(isMac == True):
            txt.SetFont(font)
        txt = wx.StaticText(self._mainClipOverviewPlane, wx.ID_ANY, "FX2:", pos=(42, 118)) #@UndefinedVariable
        if(isMac == True):
            txt.SetFont(font)
        self._overviewFx1Button = PcnImageButton(self._mainClipOverviewPlane, self._blankFxBitmap, self._blankFxBitmap, (10, 132), wx.ID_ANY, size=(32, 22)) #@UndefinedVariable
        fxWidgetList.append(self._overviewFx1Button)
        self._overviewFx2Button = PcnImageButton(self._mainClipOverviewPlane, self._blankFxBitmap, self._blankFxBitmap, (44, 132), wx.ID_ANY, size=(32, 22)) #@UndefinedVariable
        fxWidgetList.append(self._overviewFx2Button)
        self._overviewFx1Button.enableDoubleClick()
        self._overviewFx2Button.enableDoubleClick()
        self._overviewClipModeButton.Bind(wx.EVT_BUTTON, self._onClipModeButton) #@UndefinedVariable
        self._overviewFx1Button.Bind(EVT_DRAG_DONE_EVENT, self._onDragFx1Done)
        self._overviewFx2Button.Bind(EVT_DRAG_DONE_EVENT, self._onDragFx2Done)
        self._overviewFx1Button.Bind(wx.EVT_BUTTON, self._onFxButton) #@UndefinedVariable
        self._overviewFx2Button.Bind(wx.EVT_BUTTON, self._onFxButton) #@UndefinedVariable
        self._overviewFx1Button.Bind(EVT_DOUBLE_CLICK_EVENT, self._onFxButtonDouble)
        self._overviewFx2Button.Bind(EVT_DOUBLE_CLICK_EVENT, self._onFxButtonDouble)

        txt = wx.StaticText(self._mainClipOverviewPlane, wx.ID_ANY, "Mix:", pos=(8, 164)) #@UndefinedVariable
        if(isMac == True):
            txt.SetFont(font)
        txt = wx.StaticText(self._mainClipOverviewPlane, wx.ID_ANY, "Mode:", pos=(12, 178)) #@UndefinedVariable
        if(isMac == True):
            txt.SetFont(font)
        self._overviewClipMixButton = PcnImageButton(self._mainClipOverviewPlane, self._blankMixBitmap, self._blankMixBitmap, (50, 178), wx.ID_ANY, size=(25, 16)) #@UndefinedVariable
        cursorWidgetList.append(self._overviewClipMixButton)
        self._overviewClipMixButtonPopup = PcnPopupMenu(self, self._mixImages, self._mixLabels, self._onClipMixChosen)
        self._overviewClipMixButton.Bind(wx.EVT_BUTTON, self._onClipMixButton) #@UndefinedVariable

        txt = wx.StaticText(self._mainClipOverviewPlane, wx.ID_ANY, "Fade/Wipe:", pos=(8, 200)) #@UndefinedVariable
        if(isMac == True):
            txt.SetFont(font)
        txt = wx.StaticText(self._mainClipOverviewPlane, wx.ID_ANY, "Mode:", pos=(12, 217)) #@UndefinedVariable
        if(isMac == True):
            txt.SetFont(font)
        self._overviewClipFadeModeButton = PcnImageButton(self._mainClipOverviewPlane, self._blankModeBitmap, self._blankModeBitmap, (50, 217), wx.ID_ANY, size=(25, 16)) #@UndefinedVariable
        cursorWidgetList.append(self._overviewClipFadeModeButton)
        self._overviewClipFadeModeButton.enableDoubleClick()
        self._overviewClipFadeModeButton.Bind(wx.EVT_BUTTON, self._onClipFadeButton) #@UndefinedVariable
        self._overviewClipFadeModeButton.Bind(EVT_DOUBLE_CLICK_EVENT, self._onClipFadeButtonDouble)

        txt = wx.StaticText(self._mainClipOverviewPlane, wx.ID_ANY, "Modulation:", pos=(12, 236)) #@UndefinedVariable
        if(isMac == True):
            txt.SetFont(font)
        self._overviewClipFadeModulationButton = PcnImageButton(self._mainClipOverviewPlane, self._blankModeBitmap, self._blankModeBitmap, (18, 252), wx.ID_ANY, size=(25, 16)) #@UndefinedVariable
        cursorWidgetList.append(self._overviewClipFadeModulationButton)
        self._overviewClipFadeLevelButton = PcnImageButton(self._mainClipOverviewPlane, self._blankModeBitmap, self._blankModeBitmap, (46, 252), wx.ID_ANY, size=(25, 16)) #@UndefinedVariable
        cursorWidgetList.append(self._overviewClipFadeLevelButton)
        self._overviewClipFadeModulationButton.enableDoubleClick()
        self._overviewClipFadeModulationButton.Bind(wx.EVT_BUTTON, self._onClipFadeModulationButton) #@UndefinedVariable
        self._overviewClipFadeModulationButton.Bind(EVT_DOUBLE_CLICK_EVENT, self._onClipFadeButtonDouble)
        self._overviewClipFadeLevelButton.enableDoubleClick()
        self._overviewClipFadeLevelButton.Bind(wx.EVT_BUTTON, self._onClipFadeLevelButton) #@UndefinedVariable
        self._overviewClipFadeLevelButton.Bind(EVT_DOUBLE_CLICK_EVENT, self._onClipFadeButtonDouble)

        self._overviewClipNoteLabel = wx.StaticText(self._mainClipOverviewPlane, wx.ID_ANY, "NOTE: N/A", pos=(8, 278)) #@UndefinedVariable
        if(isMac == True):
            boldfont = wx.SystemSettings_GetFont(wx.SYS_SYSTEM_FONT) #@UndefinedVariable
            boldfont.SetPointSize(12)
            boldfont.SetWeight(wx.FONTWEIGHT_BOLD) #@UndefinedVariable
            self._overviewClipNoteLabel.SetFont(boldfont)

        self._overviewClipSaveButtonDissabled = True
        self._overviewClipEditButton = PcnImageButton(self._mainClipOverviewPlane, self._editBigBitmap, self._editBigPressedBitmap, (20, 300), wx.ID_ANY, size=(48, 17)) #@UndefinedVariable
        cursorWidgetList.append(self._overviewClipEditButton)
        self._overviewClipEditButton.Bind(wx.EVT_BUTTON, self._onOverviewClipEditButton) #@UndefinedVariable
        self._overviewClipSaveButton = PcnImageButton(self._mainClipOverviewPlane, self._saveBigGreyBitmap, self._saveBigGreyBitmap, (18, 320), wx.ID_ANY, size=(52, 17)) #@UndefinedVariable
        cursorWidgetList.append(self._overviewClipSaveButton)
        self._overviewClipSaveButton.Bind(wx.EVT_BUTTON, self._onOverviewClipSaveButton) #@UndefinedVariable

        sizeText = wx.StaticText(self._mainClipOverviewPlane, wx.ID_ANY, ".", pos=(78, 435)) #@UndefinedVariable
        if(isMac == True):
            sizeText.SetFont(font)

    def _setupNoteSlidersGui(self, plane, sizer):
        self._mainSliderSizer = sizer

        headerLabel = wx.StaticText(plane, wx.ID_ANY, "Note sliders:") #@UndefinedVariable
        headerFont = headerLabel.GetFont()
        headerFont.SetWeight(wx.BOLD) #@UndefinedVariable
        headerLabel.SetFont(headerFont)
        self._mainSliderSizer.Add(headerLabel, proportion=0, flag=wx.EXPAND) #@UndefinedVariable

        self._slidersInfoLabel = wx.StaticText(plane, wx.ID_ANY, "N/A") #@UndefinedVariable
        self._mainSliderSizer.Add(self._slidersInfoLabel, proportion=0, flag=wx.EXPAND) #@UndefinedVariable

        self._noteSlider1Sizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable |||
        self._noteSlider1Label = wx.StaticText(plane, wx.ID_ANY, "Slider 1:") #@UndefinedVariable
        self._noteSlider1 = wx.Slider(plane, wx.ID_ANY, minValue=0, maxValue=127, size=(200, -1)) #@UndefinedVariable
        self._noteSlider1ValueLabel = wx.StaticText(plane, wx.ID_ANY, "0.0", size=(30,-1)) #@UndefinedVariable
        self._noteSlider1Sizer.Add(self._noteSlider1Label, 1, wx.ALL, 5) #@UndefinedVariable
        self._noteSlider1Sizer.Add(self._noteSlider1, 2, wx.ALL, 5) #@UndefinedVariable
        self._noteSlider1Sizer.Add(self._noteSlider1ValueLabel, 0, wx.ALL, 5) #@UndefinedVariable
        self._mainSliderSizer.Add(self._noteSlider1Sizer, proportion=1, flag=wx.EXPAND) #@UndefinedVariable
        self._noteSlider1Id = self._noteSlider1.GetId()

        self._noteSlider2Sizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable |||
        self._noteSlider2Label = wx.StaticText(plane, wx.ID_ANY, "Slider 2:") #@UndefinedVariable
        self._noteSlider2 = wx.Slider(plane, wx.ID_ANY, minValue=0, maxValue=127, size=(200, -1)) #@UndefinedVariable
        self._noteSlider2ValueLabel = wx.StaticText(plane, wx.ID_ANY, "0.0", size=(30,-1)) #@UndefinedVariable
        self._noteSlider2Sizer.Add(self._noteSlider2Label, 1, wx.ALL, 5) #@UndefinedVariable
        self._noteSlider2Sizer.Add(self._noteSlider2, 2, wx.ALL, 5) #@UndefinedVariable
        self._noteSlider2Sizer.Add(self._noteSlider2ValueLabel, 0, wx.ALL, 5) #@UndefinedVariable
        self._mainSliderSizer.Add(self._noteSlider2Sizer, proportion=1, flag=wx.EXPAND) #@UndefinedVariable
        self._noteSlider2Id = self._noteSlider2.GetId()

        self._noteSlider3Sizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable |||
        self._noteSlider3Label = wx.StaticText(plane, wx.ID_ANY, "Slider 3:") #@UndefinedVariable
        self._noteSlider3 = wx.Slider(plane, wx.ID_ANY, minValue=0, maxValue=127, size=(200, -1)) #@UndefinedVariable
        self._noteSlider3ValueLabel = wx.StaticText(plane, wx.ID_ANY, "0.0", size=(30,-1)) #@UndefinedVariable
        self._noteSlider3Sizer.Add(self._noteSlider3Label, 1, wx.ALL, 5) #@UndefinedVariable
        self._noteSlider3Sizer.Add(self._noteSlider3, 2, wx.ALL, 5) #@UndefinedVariable
        self._noteSlider3Sizer.Add(self._noteSlider3ValueLabel, 0, wx.ALL, 5) #@UndefinedVariable
        self._mainSliderSizer.Add(self._noteSlider3Sizer, proportion=1, flag=wx.EXPAND) #@UndefinedVariable
        self._noteSlider3Id = self._noteSlider3.GetId()

        self._noteSlider4Sizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable |||
        self._noteSlider4Label = wx.StaticText(plane, wx.ID_ANY, "Slider 4:") #@UndefinedVariable
        self._noteSlider4 = wx.Slider(plane, wx.ID_ANY, minValue=0, maxValue=127, size=(200, -1)) #@UndefinedVariable
        self._noteSlider4ValueLabel = wx.StaticText(plane, wx.ID_ANY, "0.0", size=(30,-1)) #@UndefinedVariable
        self._noteSlider4Sizer.Add(self._noteSlider4Label, 1, wx.ALL, 5) #@UndefinedVariable
        self._noteSlider4Sizer.Add(self._noteSlider4, 2, wx.ALL, 5) #@UndefinedVariable
        self._noteSlider4Sizer.Add(self._noteSlider4ValueLabel, 0, wx.ALL, 5) #@UndefinedVariable
        self._mainSliderSizer.Add(self._noteSlider4Sizer, proportion=1, flag=wx.EXPAND) #@UndefinedVariable
        self._noteSlider4Id = self._noteSlider4.GetId()

        self._noteSlider5Sizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable |||
        self._noteSlider5Label = wx.StaticText(plane, wx.ID_ANY, "Slider 5:") #@UndefinedVariable
        self._noteSlider5 = wx.Slider(plane, wx.ID_ANY, minValue=0, maxValue=127, size=(200, -1)) #@UndefinedVariable
        self._noteSlider5ValueLabel = wx.StaticText(plane, wx.ID_ANY, "0.0", size=(30,-1)) #@UndefinedVariable
        self._noteSlider5Sizer.Add(self._noteSlider5Label, 1, wx.ALL, 5) #@UndefinedVariable
        self._noteSlider5Sizer.Add(self._noteSlider5, 2, wx.ALL, 5) #@UndefinedVariable
        self._noteSlider5Sizer.Add(self._noteSlider5ValueLabel, 0, wx.ALL, 5) #@UndefinedVariable
        self._mainSliderSizer.Add(self._noteSlider5Sizer, proportion=1, flag=wx.EXPAND) #@UndefinedVariable
        self._noteSlider5Id = self._noteSlider5.GetId()

        self._resetButtonBitmap = wx.Bitmap("graphics/releaseSlidersButton.png") #@UndefinedVariable
        self._resetButtonPressedBitmap = wx.Bitmap("graphics/releaseSlidersButtonPressed.png") #@UndefinedVariable
        self._updateButtonBitmap = wx.Bitmap("graphics/updateButton.png") #@UndefinedVariable
        self._updateButtonPressedBitmap = wx.Bitmap("graphics/updateButtonPressed.png") #@UndefinedVariable
        self._updateRedButtonBitmap = wx.Bitmap("graphics/updateButtonRed.png") #@UndefinedVariable
        self._updateRedButtonPressedBitmap = wx.Bitmap("graphics/updateButtonRedPressed.png") #@UndefinedVariable

        self._sliderButtonsSizer = wx.BoxSizer(wx.HORIZONTAL) #@UndefinedVariable |||
        closeButton = PcnImageButton(plane, self._closeButtonBitmap, self._closeButtonPressedBitmap, (-1, -1), wx.ID_ANY, size=(55, 17)) #@UndefinedVariable
        closeButton.Bind(wx.EVT_BUTTON, self._onSliderCloseButton) #@UndefinedVariable
        self._updateButton = PcnImageButton(plane, self._updateButtonBitmap, self._updateButtonPressedBitmap, (-1, -1), wx.ID_ANY, size=(67, 17)) #@UndefinedVariable
        self._updateButton.Bind(wx.EVT_BUTTON, self._onSliderUpdateButton) #@UndefinedVariable
        #TODO: Make this a test button for image zoom...
        self._resetButton = PcnImageButton(plane, self._resetButtonBitmap, self._resetButtonPressedBitmap, (-1, -1), wx.ID_ANY, size=(67, 17)) #@UndefinedVariable
        self._resetButton.Bind(wx.EVT_BUTTON, self._onResetButton) #@UndefinedVariable
        self._sliderButtonsSizer.Add(closeButton, 0, wx.ALL, 5) #@UndefinedVariable
        self._sliderButtonsSizer.Add(self._updateButton, 0, wx.ALL, 5) #@UndefinedVariable
        self._sliderButtonsSizer.Add(self._resetButton, 0, wx.ALL, 5) #@UndefinedVariable
        self._mainSliderSizer.Add(self._sliderButtonsSizer, proportion=1, flag=wx.EXPAND) #@UndefinedVariable

        self._noteValuesWidget = None
        self._noteValuesNumValues = 0

        plane.Bind(wx.EVT_SLIDER, self._onSlide) #@UndefinedVariable

    def _updateNoteSliders(self, valueString, labelList, valueField, numValues, infoText):
        self._valuesString = valueString
        self._labelList = labelList
        self._noteValuesWidget = valueField
        self._noteValuesNumValues = numValues
        self._infoText = infoText

        self._slidersInfoLabel.SetLabel(infoText)
        values = textToFloatValues(valueString, numValues)
        if(numValues > 0):
            calcValue = int(127.0 * values[0])
            self._noteSlider1.SetValue(calcValue)
            self._mainSliderSizer.Show(self._noteSlider1Sizer)
            self._noteSlider1Label.SetLabel(labelList[0])
        else:
            self._mainSliderSizer.Hide(self._noteSlider1Sizer)
        if(numValues > 1):
            calcValue = int(127.0 * values[1])
            self._noteSlider2.SetValue(calcValue)
            self._mainSliderSizer.Show(self._noteSlider2Sizer)
            self._noteSlider2Label.SetLabel(labelList[1])
        else:
            self._mainSliderSizer.Hide(self._noteSlider2Sizer)
        if(numValues > 2):
            calcValue = int(127.0 * values[2])
            self._noteSlider3.SetValue(calcValue)
            self._mainSliderSizer.Show(self._noteSlider3Sizer)
            self._noteSlider3Label.SetLabel(labelList[2])
        else:
            self._mainSliderSizer.Hide(self._noteSlider3Sizer)
        if(numValues > 3):
            calcValue = int(127.0 * values[3])
            self._noteSlider4.SetValue(calcValue)
            self._mainSliderSizer.Show(self._noteSlider4Sizer)
            self._noteSlider4Label.SetLabel(labelList[3])
        else:
            self._mainSliderSizer.Hide(self._noteSlider4Sizer)
        if(numValues > 4):
            calcValue = int(127.0 * values[4])
            self._noteSlider5.SetValue(calcValue)
            self._mainSliderSizer.Show(self._noteSlider5Sizer)
            self._noteSlider5Label.SetLabel(labelList[4])
        else:
            self._mainSliderSizer.Hide(self._noteSlider5Sizer)
        self._noteSlidersPanel.Layout()
        self.refreshLayout()
        self._updateValueLabels()

    def setSliderValue(self, sliderId, value):
        baseId = 10
        calcValue = int(127.0 * value)
        if(sliderId == 1):
            self.sendGuiController(self._midiNote, baseId, calcValue)
        elif(sliderId == 2):
            self.sendGuiController(self._midiNote, baseId+1, calcValue)
        elif(sliderId == 3):
            self.sendGuiController(self._midiNote, baseId+2, calcValue)
        elif(sliderId == 4):
            self.sendGuiController(self._midiNote, baseId+3, calcValue)
        elif(sliderId == 5):
            self.sendGuiController(self._midiNote, baseId+4, calcValue)

    def _onSliderCloseButton(self, event):
        self._configSizer.Hide(self._noteSlidersPanel)
        self._selectedEditor = self.EditSelection.Unselected
        self._highlightButton(self._selectedEditor)
        baseId = 10
        self.sendGuiRelease(self._midiNote, baseId)

    def _onSliderUpdateButton(self, event):
        if(self._noteValuesWidget != None):
            values = []
            if(self._noteValuesNumValues > 0):
                values.append(round(float(self._noteSlider1.GetValue()) / 127.0, 2))
            if(self._noteValuesNumValues > 1):
                values.append(round(float(self._noteSlider2.GetValue()) / 127.0, 2))
            if(self._noteValuesNumValues > 2):
                values.append(round(float(self._noteSlider3.GetValue()) / 127.0, 2))
            if(self._noteValuesNumValues > 3):
                values.append(round(float(self._noteSlider4.GetValue()) / 127.0, 2))
            if(self._noteValuesNumValues > 4):
                values.append(round(float(self._noteSlider5.GetValue()) / 127.0, 2))
            self._valuesString = floatValuesToString(values)
            self._noteValuesWidget.SetValue(self._valuesString)
            self._updateNoteSliders(self._valuesString, self._labelList, self._noteValuesWidget, self._noteValuesNumValues, self._infoText)

    def _onResetButton(self, event):
        baseId = 10
        self.sendGuiRelease(self._midiNote, baseId)
        self._updateNoteSliders(self._valuesString, self._labelList, self._noteValuesWidget, self._noteValuesNumValues, self._infoText)

    def _onSlide(self, event):
        sliderId = event.GetEventObject().GetId()
        baseId = 10
        if((self._midiNote == None) or (self._midiNote < 0) or (self._midiNote >= 128)):
            print "No note selected for note controller message!"
        else:
            if(sliderId == self._noteSlider1Id):
                self.sendGuiController(self._midiNote, baseId, self._noteSlider1.GetValue())
            elif(sliderId == self._noteSlider2Id):
                self.sendGuiController(self._midiNote, baseId+1, self._noteSlider2.GetValue())
            elif(sliderId == self._noteSlider3Id):
                self.sendGuiController(self._midiNote, baseId+2, self._noteSlider3.GetValue())
            elif(sliderId == self._noteSlider4Id):
                self.sendGuiController(self._midiNote, baseId+3, self._noteSlider4.GetValue())
            elif(sliderId == self._noteSlider5Id):
                self.sendGuiController(self._midiNote, baseId+4, self._noteSlider5.GetValue())
        self._updateValueLabels()

    def _updateValueLabels(self):
        valueString = "%.2f" % (float(self._noteSlider1.GetValue()) / 127.0)
        self._noteSlider1ValueLabel.SetLabel(valueString)
        valueString = "%.2f" % (float(self._noteSlider2.GetValue()) / 127.0)
        self._noteSlider2ValueLabel.SetLabel(valueString)
        valueString = "%.2f" % (float(self._noteSlider3.GetValue()) / 127.0)
        self._noteSlider3ValueLabel.SetLabel(valueString)
        valueString = "%.2f" % (float(self._noteSlider4.GetValue()) / 127.0)
        self._noteSlider4ValueLabel.SetLabel(valueString)
        valueString = "%.2f" % (float(self._noteSlider5.GetValue()) / 127.0)
        self._noteSlider5ValueLabel.SetLabel(valueString)

    def sendGuiRelease(self, note, guiControllerId):
        if((note == None) or (note < 0) or (note >= 128)):
            print "No note selected for note controller message!"
        else:
            channel = 0
            guiControllerId = (guiControllerId & 0x0f)
            command = 0xd0
            command += guiControllerId
            midiSender = self._mainConfig.getMidiSender()
            midiSender.sendGuiRelease(channel, note, command)

    def sendGuiController(self, note, guiControllerId, value):
        midiChannel = self._mainConfig.getSelectedMidiChannel()
        guiControllerId = (guiControllerId & 0x0f)
        command = 0xf0
        command += guiControllerId
        midiSender = self._mainConfig.getMidiSender()
        midiSender.sendGuiController(midiChannel, note, command, value)

    def getPlane(self):
        return self._mediaFileGuiPanel

    def _onResize(self, event):
        currentWidth, currentHeight = self._parentPlane.GetSize() #@UnusedVariable
        self._mainConfig.updateEffectListHeight(currentHeight - 50)

    def refreshLayout(self):
        self._onResize(None)
        self._parentPlane.Layout()
        self._parentPlane.SendSizeEvent()

    def showNoteGui(self):
        self._updateEditButton(True)
        self._configSizer.Show(self._noteConfigPanel)
        if(self._mainSelection == self.MainSelection.Track):
            self._trackGui.closeTackGui()
        self._mainSelection = self.MainSelection.Note
        self.refreshLayout()

    def showTimeModulationListGui(self):
        self._configSizer.Show(self._timeModulationListPanel)
        self.refreshLayout()

    def hideTimeModulationListGui(self):
        self._configSizer.Hide(self._timeModulationListPanel)
        self.refreshLayout()

    def showEffectList(self):
        self._configSizer.Show(self._effectListPanel)
        self.refreshLayout()

    def hideEffectsListGui(self):
        self._configSizer.Hide(self._effectListPanel)
        self.refreshLayout()

    def showEffectImageListGui(self):
        if(self._isEffectImageListOpen == False):
            self._isEffectImageListOpen = True
            self._configSizer.Show(self._effectImageListPanel)
            self.refreshLayout()
        else:
            self.hideEffectImageListGui()

    def hideEffectImageListGui(self):
        self._isEffectImageListOpen = False
        self._configSizer.Hide(self._effectImageListPanel)
        self.refreshLayout()

    def showFadeListGui(self):
        self._configSizer.Show(self._fadeListPanel)
        self.refreshLayout()

    def hideFadeListGui(self):
        self._configSizer.Hide(self._fadeListPanel)
        self.refreshLayout()

    def hideNoteGui(self):
        self._updateEditButton(False)
        self._configSizer.Hide(self._noteConfigPanel)
        self._mainSelection = self.MainSelection.Unselected
        self.refreshLayout()

    def isTrackEditorOpen(self):
        return self._mainSelection == self.MainSelection.Track

    def showTrackGui(self):
        self._configSizer.Show(self._trackGuiPlane)
        if(self._mainSelection == self.MainSelection.Note):
            self._onCloseButton(None)
        self._mainSelection = self.MainSelection.Track
        self.refreshLayout()

    def hideTrackGui(self):
        self._configSizer.Hide(self._trackGuiPlane)
        self._mainSelection = self.MainSelection.Unselected
        self.refreshLayout()

    class MainSelection():
        Unselected, Track, Note = range(3)

    class EditSelection():
        Unselected, TimeModulation, Effect1, Effect2, Fade, SubModulation1, SubModulation2, SubModulation3, Values1, Values2 = range(10)

    def _onOpenFile(self, event):
        if(self._type == "Camera" or self._type == "KinectCamera"):
            dlg = wx.NumberEntryDialog(self._mediaFileGuiPanel, "Choose camera input ID:", "ID:", "Camera input", self._cameraId, 0, 32) #@UndefinedVariable
            if dlg.ShowModal() == wx.ID_OK: #@UndefinedVariable
                self._cameraId = dlg.GetValue()
                self._fileNameField.SetValue(str(self._cameraId))
            dlg.Destroy()
        elif(self._type == "Group"):
            pass # TODO: Fix group GUI
        elif(self._type == "Text"):
            pass # TODO: Fix Text GUI
        elif(self._type == "Modulation"):
            pass # TODO: Fix Text GUI
        else:
            dlg = wx.FileDialog(self._mediaFileGuiPanel, "Choose a file", self._lastDialogDir, "", "*.*", wx.OPEN) #@UndefinedVariable
            if dlg.ShowModal() == wx.ID_OK: #@UndefinedVariable
                self._fileName = forceUnixPath(dlg.GetPath())
#                print "DEBUG new file: original path: " + str(dlg.GetPath()) + " unix path: " + str(self._fileName)
                basename = os.path.basename(self._fileName)
                self._lastDialogDir = os.path.dirname(self._fileName)
                self._fileNameField.SetValue(basename)
                lowerName = basename.lower()
                if(lowerName.endswith(".jpg") or lowerName.endswith(".jpeg") or lowerName.endswith(".gif") or lowerName.endswith(".png")):
                    selectedTypeId = self._typeField.GetSelection()
                    oldType = self._typeModes.getNames(selectedTypeId)
                    if((oldType == "Image") or (oldType == "ScrollImage") or (oldType == "Sprite")):
                        self._type = oldType
                    else:
                        self._type = "Image"
                        self._selectedSubMode = "Crop"
                    self._updateTypeChoices(self._typeField, self._type, "VideoLoop")
                    self._setupSubConfig(self._config)
                    self._showOrHideSaveButton()
            dlg.Destroy()

    def _onFileLeftRelease(self, event):
        noteName = self._mainConfig.getDraggedNoteName()
        if(noteName != ""):
            self._mainConfig.setDraggedNoteName("")
            if(self._type == "Group"):
                if(self._fileName != ""):
                    self._fileName += ","
                self._fileName += noteName
                selectedTypeId = self._typeField.GetSelection()
                self._type = self._typeModes.getNames(selectedTypeId)
                self._fileNameField.SetValue(self._fileName)
        self._clearDragCursorCallback()
        event.Skip(True)

    def _onFontDialog(self, event):
        dlg = MediaFontDialog(self._mediaFileGuiPanel, "Media Font:", self._fontField, self._fileNameField.GetValue())
        dlg.ShowModal()
        try:
            dlg.Destroy()
        except wx._core.PyDeadObjectError: #@UndefinedVariable
            pass

    def _onTypeChosen(self, event):
        selectedTypeId = self._typeField.GetSelection()
        self._type = self._typeModes.getNames(selectedTypeId)
        if(self._type == "Camera" or self._type == "KinectCamera"):
            self._fileNameField.SetValue(str(self._cameraId))
        else:
            self._fileNameField.SetValue(os.path.basename(self._fileName))
        self._setupSubConfig(self._config)
        self._showOrHideSaveButton()

    def _onTypeHelp(self, event):
        text = """
Decides what kind of input this is.

VideoLoop:\tOur normal video file playing in loop.
Image:\t\tA single static image.
ScrollImage:\tAn image that scrolls horizontally or vertically.
Sprite:\t\tAn small image (or GIF anim) that can be moved.
ImageSequence:\tA sequence of images.
Camera:\t\tCamera or capture input.
Group:\t\tGroups together a set of inputs.
"""
        dlg = wx.MessageDialog(self._mediaFileGuiPanel, text, 'Type help', wx.OK|wx.ICON_INFORMATION) #@UndefinedVariable
        dlg.ShowModal()
        dlg.Destroy()

    def _onSubModeChosen(self, event):
        if(self._type == "ImageSequence"):
            selectedSubModeId = self._subModeField.GetSelection()
            self._selectedSubMode = self._sequenceModes.getNames(selectedSubModeId)
            self._showOrHideSubModeModulation()
        self._showOrHideSaveButton()

    def _onSubModeHelp(self, event):
        if(self._type == "VideoLoop"):
            text = """
Decides how we loop this video file.

Normal:\tLoops forward.
Reverse:\tLoops in reverse.
PingPong:\tLoops alternating between forward and reverse.
PingPongReverse:\tLoops alternating between reverse and forward.
DontLoop:\tPlay video once.
DontLoopReverse:\tPlay video onve in reverse.
"""
            dlg = wx.MessageDialog(self._mediaFileGuiPanel, text, 'Loop mode help', wx.OK|wx.ICON_INFORMATION) #@UndefinedVariable
        elif(self._type == "Image"):
            text = """
Decides fit the image to screen.

Crop:\tCuts away what does not fit.
Stretch:\tStretches the image to fit.
Scale:\tAdds black borders to keep aspect ratio.
"""
            dlg = wx.MessageDialog(self._mediaFileGuiPanel, text, 'Sequence mode help', wx.OK|wx.ICON_INFORMATION) #@UndefinedVariable
        elif(self._type == "ImageSequence"):
            text = """
Decides how we decide which image to show.

Time:\tShows each image synchronization length before skipping.
ReTrigger:\tShows a new image every time the note is pressed.
Modulation:\tUses modulation source to select image.

ReTrigger Will be restarted when another note is activated on the same track.
"""
            dlg = wx.MessageDialog(self._mediaFileGuiPanel, text, 'Sequence mode help', wx.OK|wx.ICON_INFORMATION) #@UndefinedVariable
        elif(self._type == "ScrollImage"):
            text = """
Decides which direction the image scrolls when not modulated.
"""
            dlg = wx.MessageDialog(self._mediaFileGuiPanel, text, 'Scroll direction help', wx.OK|wx.ICON_INFORMATION) #@UndefinedVariable
        elif(self._type == "Sprite"):
            text = """
Sometimes you may need to invert the mask on the first image.
"""
            dlg = wx.MessageDialog(self._mediaFileGuiPanel, text, 'Mask invertion help', wx.OK|wx.ICON_INFORMATION) #@UndefinedVariable
        else:
            text = "\nMissing help text for \"" + str(self._type) + "\" (subMode1)"
            dlg = wx.MessageDialog(self._mediaFileGuiPanel, text, 'Unknown help', wx.OK|wx.ICON_INFORMATION) #@UndefinedVariable
        dlg.ShowModal()
        dlg.Destroy()

    def _onSubMode2Chosen(self, event):
        if(self._type == "ImageSequence"):
            selectedSubMode = self._subMode2Field.GetValue()
            self._selectedSubMode = selectedSubMode
        self._showOrHideSaveButton()

    def _onsubModulationMode1Chosen(self, event):
        if(self._subModulationMode1Field.GetValue().startswith("If")):
            self._updateSubModulationMode2Choices(self._subModulationMode2Field, "", "", True)
        else:
            self._updateSubModulationMode2Choices(self._subModulationMode2Field, self._subModulationMode2Field.GetValue(), "Add", False)
        self._showOrHideSaveButton()

    def _onSubMode2Help(self, event):
        if(self._type == "ScrollImage"):
            text = """
Reverses the scroll direction when not modulated.
"""
            dlg = wx.MessageDialog(self._mediaFileGuiPanel, text, 'Scroll direction help', wx.OK|wx.ICON_INFORMATION) #@UndefinedVariable
        else:
            text = "\nMissing help text for " + str(self._type) + " (subMode2)"
            dlg = wx.MessageDialog(self._mediaFileGuiPanel, text, 'Unknown help', wx.OK|wx.ICON_INFORMATION) #@UndefinedVariable
        dlg.ShowModal()
        dlg.Destroy()

    def _onSubmodulationEdit(self, event, showEffectGui = True):
        if(showEffectGui == True):
            if(self._selectedEditor != self.EditSelection.SubModulation1):
                self._configSizer.Show(self._moulationConfigPanel)
                self._selectedEditor = self.EditSelection.SubModulation1
            else:
                self._configSizer.Hide(self._moulationConfigPanel)
                self._selectedEditor = self.EditSelection.Unselected
            self._configSizer.Hide(self._timeModulationConfigPanel)
            self.hideEffectsGui()
            self._configSizer.Hide(self._fadeConfigPanel)
            self._configSizer.Hide(self._noteSlidersPanel)
            self.refreshLayout()
        self._mainConfig.updateModulationGui(self._subModulationField.GetValue(), self._subModulationField, None, None)
        self._highlightButton(self._selectedEditor)

    def _onsubModulationMode1Help(self, event):
        text = """
Decides how we add the second value.
"""
        dlg = wx.MessageDialog(self._mediaFileGuiPanel, text, 'Modulation combine help', wx.OK|wx.ICON_INFORMATION) #@UndefinedVariable
        dlg.ShowModal()
        dlg.Destroy()
        
    def _onSubmodulation2Edit(self, event, showEffectGui = True):
        if(showEffectGui == True):
            if(self._selectedEditor != self.EditSelection.SubModulation2):
                self._configSizer.Show(self._moulationConfigPanel)
                self._selectedEditor = self.EditSelection.SubModulation2
            else:
                self._configSizer.Hide(self._moulationConfigPanel)
                self._selectedEditor = self.EditSelection.Unselected
            self._configSizer.Hide(self._timeModulationConfigPanel)
            self.hideEffectsGui()
            self._configSizer.Hide(self._fadeConfigPanel)
            self._configSizer.Hide(self._noteSlidersPanel)
            self.refreshLayout()
        self._mainConfig.updateModulationGui(self._subModulation2Field.GetValue(), self._subModulation2Field, None, None)
        self._highlightButton(self._selectedEditor)

    def _onsubModulationMode2Help(self, event):
        text = """
Decides how we add the third value.
"""
        dlg = wx.MessageDialog(self._mediaFileGuiPanel, text, 'Modulation combine help', wx.OK|wx.ICON_INFORMATION) #@UndefinedVariable
        dlg.ShowModal()
        dlg.Destroy()

    def _onsubModulationSmootherHelp(self, event):
        text = """
Averages the sum value over the last n values.

Smoothish\t-> n = 4
Smooth\t-> n = 16
Smoother\t-> n = 48
Smoothest\t-> n = 128
"""
        dlg = wx.MessageDialog(self._mediaFileGuiPanel, text, 'Modulation combine help', wx.OK|wx.ICON_INFORMATION) #@UndefinedVariable
        dlg.ShowModal()
        dlg.Destroy()

    def _onSubmodulation3Edit(self, event, showEffectGui = True):
        if(showEffectGui == True):
            if(self._selectedEditor != self.EditSelection.SubModulation3):
                self._configSizer.Show(self._moulationConfigPanel)
                self._selectedEditor = self.EditSelection.SubModulation3
            else:
                self._configSizer.Hide(self._moulationConfigPanel)
                self._selectedEditor = self.EditSelection.Unselected
            self._configSizer.Hide(self._timeModulationConfigPanel)
            self.hideEffectsGui()
            self._configSizer.Hide(self._fadeConfigPanel)
            self._configSizer.Hide(self._noteSlidersPanel)
            self.refreshLayout()
        self._mainConfig.updateModulationGui(self._subModulation3Field.GetValue(), self._subModulation3Field, None, None)
        self._highlightButton(self._selectedEditor)

    def _onValues1Edit(self, event, showEffectGui = True):
        if(showEffectGui == True):
            if(self._selectedEditor != self.EditSelection.Values1):
                self._configSizer.Show(self._noteSlidersPanel)
                self._selectedEditor = self.EditSelection.Values1
            else:
                self._configSizer.Hide(self._noteSlidersPanel)
                self._selectedEditor = self.EditSelection.Unselected
            self._configSizer.Hide(self._timeModulationConfigPanel)
            self.hideEffectsGui()
            self._configSizer.Hide(self._fadeConfigPanel)
            self._configSizer.Hide(self._moulationConfigPanel)
            self.refreshLayout()
        if(self._type == "Image"):
            self._updateNoteSliders(self._values1Field.GetValue(), ("Start zoom:", "Start move:", "Start angle:"), self._values1Field, 3, "Start zoom:")
        elif(self._type == "VideoLoop"):
            self._updateNoteSliders(self._values1Field.GetValue(), ("Pitch bend:", "Hmm1:", "Hmm2:"), self._values1Field, 3, "Video loop test:")
        elif((self._type == "Sprite") or (self._type == "Text")):
            self._updateNoteSliders(self._values1Field.GetValue(), ("Start X position:", "Start Y position:"), self._values1Field, 2, "Start position:")
        elif(self._type == "Modulation"):
            self._updateNoteSliders(self._values1Field.GetValue(), ("Minimum value:"), self._values1Field, 1, "Minimum value:")
        else: #KinectInput
            self.setSliderValue(5, 0.0)
            self._updateNoteSliders(self._values1Field.GetValue(), ("Display mode:", "Black filter:", "Diff filter:", "Erode filter:"), self._values1Field, 4, "Kinect filters:")
        self._highlightButton(self._selectedEditor)

    def _onValues2Edit(self, event, showEffectGui = True):
        if(showEffectGui == True):
            if(self._selectedEditor != self.EditSelection.Values2):
                self._configSizer.Show(self._noteSlidersPanel)
                self._selectedEditor = self.EditSelection.Values2
            else:
                self._configSizer.Hide(self._noteSlidersPanel)
                self._selectedEditor = self.EditSelection.Unselected
            self._configSizer.Hide(self._timeModulationConfigPanel)
            self.hideEffectsGui()
            self._configSizer.Hide(self._fadeConfigPanel)
            self._configSizer.Hide(self._moulationConfigPanel)
            self.refreshLayout()
        if(self._type == "Image"):
            self._updateNoteSliders(self._values2Field.GetValue(), ("End zoom:", "End move:", "End angle:"), self._values2Field, 3, "End zoom:")
        elif((self._type == "Sprite") or (self._type == "Text")):
            self._updateNoteSliders(self._values2Field.GetValue(), ("End X position:", "End Y position:"), self._values2Field, 2, "End position:")
        elif(self._type == "Modulation"):
            self._updateNoteSliders(self._values2Field.GetValue(), ("Maximum value:"), self._values2Field, 1, "Maximum value:")
        else: #KinectInput
            self.setSliderValue(5, 1.0)
            self._updateNoteSliders(self._values2Field.GetValue(), ("Zoom amount:", "X/Y ratio:", "X center:", "Y center:"), self._values2Field, 4, "Kinect zoom:")
        self._highlightButton(self._selectedEditor)

    def _onMixHelp(self, event):
        text = """
Decides how this image is mixed with images on lower MIDI channels.
\t(This only gets used if track mix mode is set to Default.)

Add:\t\tSums the images together.
Multiply:\t\tMultiplies the images together.
Lumakey:\t\tReplaces source everywhere the image is black.
WhiteLumakey:\tReplaces source everywhere the image is white.
AlphaMask:\tIf source has alpha channel it will use this as mask.
Replace:\t\tNo mixing. Just use this image.
"""
        dlg = wx.MessageDialog(self._mediaFileGuiPanel, text, 'Mix help', wx.OK|wx.ICON_INFORMATION) #@UndefinedVariable
        dlg.ShowModal()
        dlg.Destroy()

    def _onNoteHelp(self, event):
        text = """
This is the note assigned to this configuration.
\t(Note \"""" + noteToNoteString(self._midiNote) + "\" has id " + str(self._midiNote) + """.)
"""
        dlg = wx.MessageDialog(self._mediaFileGuiPanel, text, 'Note help', wx.OK|wx.ICON_INFORMATION) #@UndefinedVariable
        dlg.ShowModal()
        dlg.Destroy()

    def _onSyncValidate(self, event):
        valueString = self._syncField.GetValue()
        valueError = False
        try:
            valueFloat = float(valueString)
        except ValueError:
            valueFloat = 4.0
            valueError = True
        if(valueFloat < 0.0):
            valueFloat = 0.0
            valueError = True
        if(valueFloat > 1280.0):
            valueFloat = 1280.0
            valueError = True
        if(valueError):
            dlg = wx.MessageDialog(self._mediaFileGuiPanel, "Value must be a float between 0.0 and 1280.0", 'Synchronization length value error', wx.OK|wx.ICON_INFORMATION) #@UndefinedVariable
            dlg.ShowModal()
            dlg.Destroy()
        valueString = str(valueFloat)
        self._syncField.SetValue(valueString)

    def _onSyncHelp(self, event):
        if(self._type == "Group"):
            text = """
Decides how fast the clips in this groups should play.

\t0.5 -> is double speed.
\t2.0 -> is half speed.
"""
        else:
            text = """
Decides how long the video takes to loop
or how long the images are displayed.

\tGiven in beats (4:4)
"""
        dlg = wx.MessageDialog(self._mediaFileGuiPanel, text, 'Synchronization help', wx.OK|wx.ICON_INFORMATION) #@UndefinedVariable
        dlg.ShowModal()
        dlg.Destroy()

    def _onQuantizeValidate(self, event):
        valueString = self._quantizeField.GetValue()
        valueError = False
        try:
            valueFloat = float(valueString)
        except ValueError:
            valueFloat = 1.0
            valueError = True
        if(valueFloat < 0.0):
            valueFloat = 0.0
            valueError = True
        if(valueFloat > 1280.0):
            valueFloat = 1280.0
            valueError = True
        if(valueError):
            dlg = wx.MessageDialog(self._mediaFileGuiPanel, "Value must be a float between 0.0 and 1280.0", 'Quantize value error', wx.OK|wx.ICON_INFORMATION) #@UndefinedVariable
            dlg.ShowModal()
            dlg.Destroy()
        valueString = str(valueFloat)
        self._quantizeField.SetValue(valueString)

    def _onQuantizeHelp(self, event):
        text = """
Decides when the video or image starts.
All notes on events are quantized to this.

\tGiven in beats (4:4)
"""
        dlg = wx.MessageDialog(self._mediaFileGuiPanel, text, 'Quantize help', wx.OK|wx.ICON_INFORMATION) #@UndefinedVariable
        dlg.ShowModal()
        dlg.Destroy()

    def _highlightButton(self, selected):
        if(selected == self.EditSelection.SubModulation1):
            self._subModulationEditButton.setBitmaps(self._editSelectedBitmap, self._editSelectedBitmap)
        else:
            self._subModulationEditButton.setBitmaps(self._editBitmap, self._editPressedBitmap)
        if(selected == self.EditSelection.SubModulation2):
            self._subModulation2EditButton.setBitmaps(self._editSelectedBitmap, self._editSelectedBitmap)
        else:
            self._subModulation2EditButton.setBitmaps(self._editBitmap, self._editPressedBitmap)
        if(selected == self.EditSelection.SubModulation3):
            self._subModulation3EditButton.setBitmaps(self._editSelectedBitmap, self._editSelectedBitmap)
        else:
            self._subModulation3EditButton.setBitmaps(self._editBitmap, self._editPressedBitmap)
        if(selected == self.EditSelection.Values1):
            self._values1EditButton.setBitmaps(self._editSelectedBitmap, self._editSelectedBitmap)
        else:
            self._values1EditButton.setBitmaps(self._editBitmap, self._editPressedBitmap)
        if(selected == self.EditSelection.Values2):
            self._values2EditButton.setBitmaps(self._editSelectedBitmap, self._editSelectedBitmap)
        else:
            self._values2EditButton.setBitmaps(self._editBitmap, self._editPressedBitmap)
        if(selected == self.EditSelection.TimeModulation):
            self._timeModulationButton.setBitmaps(self._editSelectedBitmap, self._editSelectedBitmap)
        else:
            self._timeModulationButton.setBitmaps(self._editBitmap, self._editPressedBitmap)
        if(selected == self.EditSelection.Effect1):
            self._effect1Button.setBitmaps(self._editSelectedBitmap, self._editSelectedBitmap)
        else:
            self._effect1Button.setBitmaps(self._editBitmap, self._editPressedBitmap)
        if(selected == self.EditSelection.Effect2):
            self._effect2Button.setBitmaps(self._editSelectedBitmap, self._editSelectedBitmap)
        else:
            self._effect2Button.setBitmaps(self._editBitmap, self._editPressedBitmap)
        if(selected == self.EditSelection.Fade):
            self._fadeButton.setBitmaps(self._editSelectedBitmap, self._editSelectedBitmap)
        else:
            self._fadeButton.setBitmaps(self._editBitmap, self._editPressedBitmap)

    def _onTimeModulationEdit(self, event, showEffectGui = True):
        if(showEffectGui == True):
            if(self._selectedEditor != self.EditSelection.TimeModulation):
                self._selectedEditor = self.EditSelection.TimeModulation
                self._configSizer.Show(self._timeModulationConfigPanel)
            else:
                self._selectedEditor = self.EditSelection.Unselected
                self._configSizer.Hide(self._timeModulationConfigPanel)
            self.hideEffectsGui()
            self._configSizer.Hide(self._fadeConfigPanel)
            self._configSizer.Hide(self._moulationConfigPanel)
            self._configSizer.Hide(self._noteSlidersPanel)
            self.refreshLayout()
        selectedConfig = self._timeModulationField.GetValue()
        self._mainConfig.updateTimeModulationGui(selectedConfig, self._midiNote, self._timeModulationField)
        self._highlightButton(self._selectedEditor)

    def _onEffect1Edit(self, event, showEffectGui = True):
        if(showEffectGui == True):
            if(self._selectedEditor != self.EditSelection.Effect1):
                self.showEffectsGui(self.EditSelection.Effect1)
            else:
                self.hideEffectsGui()
            self._configSizer.Hide(self._timeModulationConfigPanel)
            self._configSizer.Hide(self._fadeConfigPanel)
            self._configSizer.Hide(self._moulationConfigPanel)
            self._configSizer.Hide(self._noteSlidersPanel)
            self.refreshLayout()
        selectedEffectConfig = self._effect1Field.GetValue()
        self._mainConfig.updateEffectsGui(selectedEffectConfig, self._midiNote, "Effect1", self._effect1Field)
        self._highlightButton(self._selectedEditor)

    def _onEffect2Edit(self, event, showEffectGui = True):
        if(showEffectGui == True):
            if(self._selectedEditor != self.EditSelection.Effect2):
                self.showEffectsGui(self.EditSelection.Effect2)
            else:
                self.hideEffectsGui()
            self._configSizer.Hide(self._timeModulationConfigPanel)
            self._configSizer.Hide(self._fadeConfigPanel)
            self._configSizer.Hide(self._moulationConfigPanel)
            self._configSizer.Hide(self._noteSlidersPanel)
            self.refreshLayout()
        selectedEffectConfig = self._effect2Field.GetValue()
        self._mainConfig.updateEffectsGui(selectedEffectConfig, self._midiNote, "Effect2", self._effect2Field)
        self._highlightButton(self._selectedEditor)

    def showTimeModulationGui(self):
        self._configSizer.Show(self._timeModulationConfigPanel)
        self._highlightButton(self._selectedEditor)
        self.refreshLayout()

    def hideTimeModulationGui(self):
        self._configSizer.Hide(self._timeModulationConfigPanel)
        self._selectedEditor = self.EditSelection.Unselected
        self._highlightButton(self._selectedEditor)
        self.refreshLayout()

    def fixTimeModulationGuiLayout(self):
        self.refreshLayout()

    def showEffectsGui(self, selectedId):
        self._selectedEditor = selectedId
        self._configSizer.Show(self._effectConfigPanel)
        self._highlightButton(self._selectedEditor)
        self.refreshLayout()

    def hideEffectsGui(self):
        self.hideSlidersGui()
        self._configSizer.Hide(self._effectConfigPanel)
        self._trackUnselectEditor()
        self._selectedEditor = self.EditSelection.Unselected
        self._highlightButton(self._selectedEditor)
        self.refreshLayout()

    def fixEffectsGuiLayout(self):
        self.refreshLayout()

    def showFadeGui(self):
        self._configSizer.Show(self._fadeConfigPanel)
        self._highlightButton(self._selectedEditor)
        self.refreshLayout()

    def hideFadeGui(self):
        self._configSizer.Hide(self._fadeConfigPanel)
        self._trackUnselectEditor()
        self._selectedEditor = self.EditSelection.Unselected
        self._highlightButton(self._selectedEditor)
        self.refreshLayout()

    def showModulationGui(self):
        self._configSizer.Show(self._moulationConfigPanel)
        self.refreshLayout()

    def fixModulationGuiLayout(self):
        self.refreshLayout()

    def hideModulationGui(self):
        self._configSizer.Hide(self._moulationConfigPanel)
        if((self._selectedEditor == self.EditSelection.SubModulation1)
           or (self._selectedEditor == self.EditSelection.SubModulation2)
           or (self._selectedEditor == self.EditSelection.SubModulation3)):
            self._selectedEditor = self.EditSelection.Unselected
            self._highlightButton(self._selectedEditor)
        self.refreshLayout()
        self._mainConfig.stopModulationGui()

    def setDragCursor(self, cursor):
        self._parentPlane.SetCursor(cursor) #@UndefinedVariable
        for panels in self._subPanelsList:
            panels.SetCursor(cursor)

    def clearDragCursor(self, cursor):
        self._parentPlane.SetCursor(cursor) #@UndefinedVariable
        for panels in self._subPanelsList:
            panels.SetCursor(cursor)

    def showSlidersGui(self):
        self._configSizer.Show(self._slidersPanel)
        self.refreshLayout()
        self._mainConfig.startSlidersUpdate()

    def hideSlidersGui(self):
        self._configSizer.Hide(self._slidersPanel)
        self.refreshLayout()
        self._mainConfig.stopSlidersUpdate()

    def _onFadeEdit(self, event, showFadeGui=True):
        if(showFadeGui == True):
            if(self._selectedEditor != self.EditSelection.Fade):
                self._configSizer.Hide(self._moulationConfigPanel)
                self._configSizer.Show(self._fadeConfigPanel)
                self._selectedEditor = self.EditSelection.Fade
            else:
                self._configSizer.Hide(self._fadeConfigPanel)
                self._selectedEditor = self.EditSelection.Unselected
            self._configSizer.Hide(self._timeModulationConfigPanel)
            self.hideEffectsGui()
            self._configSizer.Hide(self._noteSlidersPanel)
            self.refreshLayout()
        selectedFadeConfig = self._fadeField.GetValue()
        self._mainConfig.updateFadeGui(selectedFadeConfig, "Media", self._fadeField)
        self._highlightButton(self._selectedEditor)

    def _onCloseButton(self, event):
        self.hideNoteGui()
        self._configSizer.Hide(self._timeModulationConfigPanel)
        self.hideEffectsGui()
        self._configSizer.Hide(self._moulationConfigPanel)
        self._configSizer.Hide(self._fadeConfigPanel)
        self._configSizer.Hide(self._noteSlidersPanel)
        self._selectedEditor = self.EditSelection.Unselected
        self._highlightButton(self._selectedEditor)
        self.refreshLayout()

    def _onThumbButton(self, event):
        if((self._midiNote > 0) and (self._midiNote < 128)):
            self._requestThumbCallback(self._midiNote, -1.0, True)

    def _onDeleteButton(self, event):
        if(self._config == None):
            return
        noteLetter = noteToNoteString(self._midiNote)
        self._mainConfig.deleteNoteConfig(self._midiNote, noteLetter)
        self.clearGui(self._midiNote)
        self._mainConfig.clearNoteThumb(self._midiNote)

    def _onSaveButton(self, event):
        if(self._type == "Camera" or self._type == "KinectCamera"):
            noteFileName = str(self._cameraId)
        elif(self._type == "Text"):
            noteFileName = self._fileNameField.GetValue()
            self._fileName = noteFileName
        elif(self._type == "Modulation"):
            noteFileName = self._fileNameField.GetValue()
            self._fileName = noteFileName
        elif(self._type == "Group"):
            validatedGroupString = ""
            groupString = self._fileNameField.GetValue()
            groupNoteStrings = groupString.split(",")
            for noteString in groupNoteStrings:
                noteId = noteStringToNoteNumber(noteString)
                if((noteId >= 0) and (noteId < 128)):
                    if(validatedGroupString != ""):
                        validatedGroupString += ","
                    validatedGroupString += noteToNoteString(noteId)
            noteFileName = validatedGroupString
            self._fileName = noteFileName
            self._fileNameField.SetValue(noteFileName)
        else:
            noteFileName = self._fileName
            if((self._videoDirectory != "") and (self._fileName != "")):
                if(os.path.isabs(self._fileName)):
                    try:
                        noteFileName = forceUnixPath(os.path.relpath(self._fileName, self._videoDirectory))
                    except:
                        noteFileName = self._fileName
                    else:
                        if(noteFileName.startswith("..") == True):
                            noteFileName = self._fileName
                    self._fileName = noteFileName
        if(noteFileName == ""):
            self._onDeleteButton(None)
        else:
            noteLetter = noteToNoteString(self._midiNote)
            if(self._config == None):
                newConfig = self._mainConfig.makeNoteConfig(noteFileName, noteLetter, self._midiNote)
                if(noteFileName != ""):
                    self._mainConfig.setNewNoteThumb(self._midiNote)
                if(newConfig != None):
                    self._config = newConfig.getConfig()
            else:
                if(self._config.getValue("FileName") != noteFileName):
                    self._mainConfig.setNewNoteThumb(self._midiNote)
                self._config.setValue("FileName", noteFileName)
            if(self._config != None):
                self._config.setValue("Type", self._type)
                if(self._type == "VideoLoop"):
                    loopMode = self._subModeField.GetValue()
                    self._config.addTextParameter("LoopMode", "Normal")
                    self._config.setValue("LoopMode", loopMode)
                else:
                    self._config.removeParameter("LoopMode")

                if(self._type == "Image"):
                    fieldValString = self._values1Field.GetValue()
                    startVal = textToFloatValues(fieldValString, 3)
                    startValString = floatValuesToString(startVal)
                    if(fieldValString != startValString):
                        startValString = "0.0|0.0|0.0"
                    self._values1Field.SetValue(startValString)
                    self._config.addTextParameter("StartValues", "0.0|0.0|0.0")
                    self._config.setValue("StartValues", startValString)
                    fieldValString = self._values2Field.GetValue()
                    endVal = textToFloatValues(fieldValString, 3)
                    endValString = floatValuesToString(endVal)
                    if(fieldValString != endValString):
                        endValString = "0.0|0.0|0.0"
                    self._values2Field.SetValue(endValString)
                    self._config.addTextParameter("EndValues", "0.0|0.0|0.0")
                    self._config.setValue("EndValues", endValString)
                else:
                    self._config.removeParameter("StartValues")
                    self._config.removeParameter("EndValues")

                if((self._type == "Image") or (self._type == "Camera")):
                    resizeMode = self._subModeField.GetValue()
                    self._config.addBoolParameter("DisplayMode", "Crop")
                    self._config.setValue("DisplayMode", resizeMode)
                else:
                    self._config.removeParameter("DisplayMode")

                if(self._type == "ImageSequence"):
                    sequenceMode = self._subModeField.GetValue()
                    self._config.addTextParameter("SequenceMode", "Time")
                    self._config.setValue("SequenceMode", sequenceMode)
                    sequenceModulation = self._midiModulation.validateModulationString(self._subModulationField.GetValue())
                    self._subModulationField.SetValue(sequenceModulation)
                    self._config.addTextParameter("PlaybackModulation", "None")
                    self._config.setValue("PlaybackModulation", sequenceModulation)
                else:
                    self._config.removeParameter("SequenceMode")
                    self._config.removeParameter("PlaybackModulation")

                if(self._type == "ScrollImage"):
                    scrollMode = self._subModeField.GetValue()
                    if(scrollMode == "Horizontal"):
                        scrollMode = True
                    else:
                        scrollMode = False
                    self._config.addBoolParameter("HorizontalMode", True)
                    self._config.setValue("HorizontalMode", scrollMode)
                    revMode = self._subMode2Field.GetValue()
                    if(revMode == "On"):
                        revMode = True
                    else:
                        revMode = False
                    self._config.addBoolParameter("ReverseMode", False)
                    self._config.setValue("ReverseMode", revMode)
                    sequenceModulation = self._midiModulation.validateModulationString(self._subModulationField.GetValue())
                    self._subModulationField.SetValue(sequenceModulation)
                    self._config.addTextParameter("ScrollModulation", "None")
                    self._config.setValue("ScrollModulation", sequenceModulation)
                else:
                    self._config.removeParameter("HorizontalMode")
                    self._config.removeParameter("ReverseMode")
                    self._config.removeParameter("ScrollModulation")

                if((self._type == "Sprite") or (self._type == "Text")):
                    fieldValString = self._values1Field.GetValue()
                    startVal = textToFloatValues(fieldValString, 2)
                    startValString = floatValuesToString(startVal)
                    if(fieldValString != startValString):
                        startValString = "0.5|0.5"
                    self._values1Field.SetValue(startValString)
                    self._config.addTextParameter("StartPosition", "0.5|0.5")
                    self._config.setValue("StartPosition", startValString)
                    fieldValString = self._values2Field.GetValue()
                    endVal = textToFloatValues(fieldValString, 2)
                    endValString = floatValuesToString(endVal)
                    if(fieldValString != endValString):
                        endValString = "0.5|0.5"
                    self._values2Field.SetValue(endValString)
                    self._config.addTextParameter("EndPosition", "0.5|0.5")
                    self._config.setValue("EndPosition", endValString)
                    xModulation = self._midiModulation.validateModulationString(self._subModulationField.GetValue())
                    self._subModulationField.SetValue(xModulation)
                    self._config.addTextParameter("XModulation", "None")
                    self._config.setValue("XModulation", xModulation)
                    yModulation = self._midiModulation.validateModulationString(self._subModulation2Field.GetValue())
                    self._subModulation2Field.SetValue(yModulation)
                    self._config.addTextParameter("YModulation", "None")
                    self._config.setValue("YModulation", yModulation)
                else:
                    self._config.removeParameter("StartPosition")
                    self._config.removeParameter("EndPosition")
                    self._config.removeParameter("XModulation")
                    self._config.removeParameter("YModulation")

                if(self._type == "Sprite"):
                    self._config.addBoolParameter("InvertFirstFrameMask", False)
                    subMode = self._subModeField.GetValue()
                    if(subMode == "Normal"):
                        invMode = False
                    else:
                        invMode = True
                    self._config.setValue("InvertFirstFrameMask", invMode)
                else:
                    self._config.removeParameter("InvertFirstFrameMask")

                if(self._type == "Text"):
                    self._config.addTextParameter("Font", "Arial;32;#FFFFFF")
                    fontString = self._fontField.GetValue()
                    self._config.setValue("Font", fontString)
                else:
                    self._config.removeParameter("Font")

                if(self._type == "KinectCamera"):
#                    modeModulation = self._midiModulation.validateModulationString(self._subModulationField.GetValue())
#                    self._subModulationField.SetValue(modeModulation)
#                    self._config.addTextParameter("DisplayModeModulation", "None")
#                    self._config.setValue("DisplayModeModulation", modeModulation)
                    filterVal = textToFloatValues(self._values1Field.GetValue(), 4)
                    filterValString = floatValuesToString(filterVal)
                    self._values1Field.SetValue(filterValString)
                    self._config.addTextParameter("FilterValues", "0.0|0.0|0.0|0.0")
                    self._config.setValue("FilterValues", filterValString)
                    zoomVal = textToFloatValues(self._values2Field.GetValue(), 4)
                    zoomValString = floatValuesToString(zoomVal)
                    self._values1Field.SetValue(zoomValString)
                    self._config.addTextParameter("ZoomValues", "0.5|0.5|0.5|0.5")
                    self._config.setValue("ZoomValues", zoomValString)
                else:
#                    self._config.removeParameter("DisplayModeModulation")
                    self._config.removeParameter("FilterValues")
                    self._config.removeParameter("ZoomValues")

                if(self._type == "Modulation"):
                    firstModulation = self._midiModulation.validateModulationString(self._subModulationField.GetValue())
                    self._subModulationField.SetValue(firstModulation)
                    modulationCombiner1 = self._subModulationMode1Field.GetValue()
                    secondModulation = self._midiModulation.validateModulationString(self._subModulation2Field.GetValue())
                    self._subModulation2Field.SetValue(secondModulation)
                    modulationCombiner2 = self._subModulationMode2Field.GetValue()
                    thirdModulation = self._midiModulation.validateModulationString(self._subModulation3Field.GetValue())
                    self._subModulation3Field.SetValue(thirdModulation)
                    fieldValString = self._values1Field.GetValue()
                    minVal = textToFloatValues(fieldValString, 1)
                    minValString = floatValuesToString(minVal)
                    if(fieldValString != minValString):
                        minValString = "0.0"
                    self._values1Field.SetValue(minValString)
                    fieldValString = self._values2Field.GetValue()
                    maxVal = textToFloatValues(fieldValString, 1)
                    maxValString = floatValuesToString(maxVal)
                    if(fieldValString != maxValString):
                        maxValString = "1.0"
                    self._values2Field.SetValue(maxValString)
                    smoothMode = self._subModulationSmootherField.GetValue()

                    self._config.addTextParameter("FirstModulation", "None")
                    self._config.setValue("FirstModulation", firstModulation)
                    self._config.addTextParameter("ModulationCombiner1", "Add")
                    self._config.setValue("ModulationCombiner1", modulationCombiner1)
                    self._config.addTextParameter("SecondModulation", "None")
                    self._config.setValue("SecondModulation", secondModulation)
                    self._config.addTextParameter("ModulationCombiner2", "Add")
                    self._config.setValue("ModulationCombiner2", modulationCombiner2)
                    self._config.addTextParameter("ThirdModulation", "None")
                    self._config.setValue("ThirdModulation", thirdModulation)
                    self._config.addFloatParameter("MinValue", 0.0)
                    self._config.setValue("MinValue", minValString)
                    self._config.addFloatParameter("MaxValue", 1.0)
                    self._config.setValue("MaxValue", maxValString)
                    self._config.addTextParameter("Smoother", "Off")
                    self._config.setValue("Smoother", smoothMode)
                    self._config.removeParameter("MixMode")
                    self._config.removeParameter("TimeModulationConfig")
                    self._config.removeParameter("Effect1Config")
                    self._config.removeParameter("Effect2Config")
                    self._config.removeParameter("FadeConfig")
                else:
                    self._config.removeParameter("FirstModulation")
                    self._config.removeParameter("ModulationCombiner1")
                    self._config.removeParameter("SecondModulation")
                    self._config.removeParameter("ModulationCombiner2")
                    self._config.removeParameter("ThirdModulation")
                    self._config.removeParameter("MinValue")
                    self._config.removeParameter("MaxValue")
                    self._config.removeParameter("Smoother")

                    self._config.addTextParameter("MixMode", "Add")#Default Add
                    self._config.addTextParameter("TimeModulationConfig", "Default")#Default Default
                    self._config.addTextParameter("Effect1Config", "MediaDefault1")#Default MediaDefault1
                    self._config.addTextParameter("Effect2Config", "MediaDefault2")#Default MediaDefault2
                    self._config.addTextParameter("FadeConfig", "Default")#Default Default
                    mixMode = self._mixField.GetValue()
                    self._config.setValue("MixMode", mixMode)
                    timeModulation = self._timeModulationField.GetValue()
                    self._config.setValue("TimeModulationConfig", timeModulation)
                    effect1Config = self._effect1Field.GetValue()
                    self._config.setValue("Effect1Config", effect1Config)
                    effect2Config = self._effect2Field.GetValue()
                    self._config.setValue("Effect2Config", effect2Config)
                    fadeConfig = self._fadeField.GetValue()
                    self._config.setValue("FadeConfig", fadeConfig)

                self._onSyncValidate(event)
                syncLength = float(self._syncField.GetValue())
                self._config.setValue("SyncLength", syncLength)
                self._onQuantizeValidate(event)
                quantizeLength = float(self._quantizeField.GetValue())
                self._config.setValue("QuantizeLength", quantizeLength)
                self.updateGui(None, None)

    def _showOrHideSubModeModulation(self):
        if(self._selectedSubMode == "Modulation"):
            self._noteConfigSizer.Show(self._subModulationSizer)
        else:
            self._noteConfigSizer.Hide(self._subModulationSizer)
            if(self._selectedEditor == self.EditSelection.SubModulation1):
                self._onSubmodulationEdit(None, True)
        self.refreshLayout()

    def _setupSubConfig(self, config):
        if(self._type == "VideoLoop"):
            self._subModeLabel.SetLabel("Loop mode:")
            if(config != None):
                self._updateLoopModeChoices(self._subModeField, config.getValue("LoopMode"), "Normal")
            else:
                self._updateLoopModeChoices(self._subModeField, self._subModeField.GetValue(), "Normal")
        elif(self._type == "ImageSequence"):
            self._subModeLabel.SetLabel("Sequence mode:")
            if(config != None):
                self._selectedSubMode = config.getValue("SequenceMode")
                self._updateSequenceModeChoices(self._subModeField, self._selectedSubMode, "Time")
                playbackMod = config.getValue("PlaybackModulation")
                self._subModulationField.SetValue(str(playbackMod))
            else:
                self._selectedSubMode = self._subModeField.GetValue()
                self._updateSequenceModeChoices(self._subModeField, self._selectedSubMode, "Time")
                self._subModulationField.SetValue("None")
        elif(self._type == "Image"):
            self._subModeLabel.SetLabel("Resize mode:")
            if(config != None):
                cropMode = config.getValue("DisplayMode")
                if(cropMode == None):
                    self._selectedSubMode = "Crop"
                else:
                    self._selectedSubMode = cropMode
                self._updateCropModeChoices(self._subModeField, self._selectedSubMode, "Crop")
                confString = self._config.getValue("StartValues")
                confVal = textToFloatValues(confString, 3)
                confValString = floatValuesToString(confVal)
                self._values1Field.SetValue(confValString)
                confString = self._config.getValue("EndValues")
                confVal = textToFloatValues(confString, 3)
                confValString = floatValuesToString(confVal)
                self._values2Field.SetValue(confValString)
            else:
                self._selectedSubMode = self._subModeField.GetValue()
                self._updateCropModeChoices(self._subModeField, self._selectedSubMode, "Crop")
                self._values1Field.SetValue("0.0|0.0|0.0")
                self._values2Field.SetValue("0.0|0.0|0.0")
        elif(self._type == "ScrollImage"):
            self._subModeLabel.SetLabel("Scroll direction:")
            if(config != None):
                horMode = config.getValue("HorizontalMode")
                if((horMode == None) or (horMode == True)):
                    self._selectedSubMode = "Horizontal"
                else:
                    self._selectedSubMode = "Vertical"
                self._updateScrollModeChoices(self._subModeField, self._selectedSubMode, "Horizontal")
                revMode = config.getValue("ReverseMode")
                if(revMode == True):
                    selectedSub2Mode = "On"
                else:
                    selectedSub2Mode = "Off"
                self._updateReverseModeChoices(self._subMode2Field, selectedSub2Mode, "Off")
                scrMod = config.getValue("ScrollModulation")
                self._subModulationField.SetValue(str(scrMod))
            else:
                oldSubMode = self._subModeField.GetValue()
                self._updateScrollModeChoices(self._subModeField, oldSubMode, "Horizontal")
                self._selectedSubMode = self._subModeField.GetValue()
                oldSub2Mode = self._subMode2Field.GetValue()
                self._updateReverseModeChoices(self._subMode2Field, oldSub2Mode, "Off")
                self._subModulationField.SetValue("None")
        elif((self._type == "Sprite") or (self._type == "Text")):
            self._subModeLabel.SetLabel("First frame mask mode:")
            if(config != None):
                if(self._type == "Sprite"):
                    invMode = config.getValue("InvertFirstFrameMask")
                    if(invMode == True):
                        self._selectedSubMode = "Invert mask"
                    else:
                        self._selectedSubMode = "Normal"
                    self._updateInvertModeChoices(self._subModeField, self._selectedSubMode, "Normal")
                else:
                    font = config.getValue("Font")
                    if(font == None):
                        self._fontField.SetValue("Arial;32;#FFFFFF")
                    else:
                        self._fontField.SetValue(font)
                confString = self._config.getValue("StartPosition")
                if(confString == None):
                    confValString = "0.5|0.5"
                else:
                    confVal = textToFloatValues(confString, 2)
                    confValString = floatValuesToString(confVal)
                self._values1Field.SetValue(confValString)
                confString = self._config.getValue("EndPosition")
                if(confString == None):
                    confValString = "0.5|0.5"
                else:
                    confVal = textToFloatValues(confString, 2)
                    confValString = floatValuesToString(confVal)
                self._values2Field.SetValue(confValString)
                xMod = config.getValue("XModulation")
                self._subModulationField.SetValue(str(xMod))
                yMod = config.getValue("YModulation")
                self._subModulation2Field.SetValue(str(yMod))
            else:
                if(self._type == "Sprite"):
                    self._selectedSubMode = self._subModeField.GetValue()
                    self._updateInvertModeChoices(self._subModeField, self._selectedSubMode, "Normal")
                else:
                    self._fontField.SetValue("Arial;32;#FFFFFF")
                self._values1Field.SetValue("0.5|0.5")
                self._values2Field.SetValue("0.5|0.5")
                self._subModulationField.SetValue("None")
                self._subModulation2Field.SetValue("None")
        elif(self._type == "Camera"):
            self._subModeLabel.SetLabel("Resize mode:")
            if(config != None):
                cropMode = config.getValue("DisplayMode")
                if(cropMode == None):
                    self._selectedSubMode = "Crop"
                else:
                    self._selectedSubMode = cropMode
                self._updateCropModeChoices(self._subModeField, self._selectedSubMode, "Crop")
            else:
                self._selectedSubMode = self._subModeField.GetValue()
                self._updateCropModeChoices(self._subModeField, self._selectedSubMode, "Crop")
        elif(self._type == "KinectCamera"):
            if(config != None):
#                dispMod = config.getValue("DisplayModeModulation")
#                self._subModulationField.SetValue(str(dispMod))
                confString = self._config.getValue("FilterValues")
                if(confString == None):
                    confValString = "0.0|0.0|0.0|0.0"
                else:
                    confVal = textToFloatValues(confString, 4)
                    confValString = floatValuesToString(confVal)
                self._values1Field.SetValue(confValString)
                confString = self._config.getValue("ZoomValues")
                if(confString == None):
                    confValString = "0.5|0.5|0.5|0.5"
                else:
                    confVal = textToFloatValues(confString, 4)
                    confValString = floatValuesToString(confVal)
                self._values2Field.SetValue(confValString)
            else:
#                self._subModulationField.SetValue("None")
                self._values1Field.SetValue("0.0|0.0|0.0|0.0")
                self._values2Field.SetValue("0.5|0.5|0.5|0.5")
        elif(self._type == "Modulation"):
            if(config != None):
                confMod = config.getValue("FirstModulation")
                self._subModulationField.SetValue(str(confMod))
                firstConfMode = config.getValue("ModulationCombiner1")
                self._updateSubModulationMode1Choices(self._subModulationMode1Field, firstConfMode, "Add")
                confMod = config.getValue("SecondModulation")
                self._subModulation2Field.SetValue(str(confMod))
                confMode = config.getValue("ModulationCombiner2")
                if(firstConfMode.startswith("If")):
                    self._updateSubModulationMode2Choices(self._subModulationMode2Field, confMode, "Else", True)
                else:
                    self._updateSubModulationMode2Choices(self._subModulationMode2Field, confMode, "Add", False)
                confMod = config.getValue("ThirdModulation")
                self._subModulation3Field.SetValue(str(confMod))
                confVal = self._config.getValue("MinValue")
                if(confVal == None):
                    confVal = 0.0
                self._values1Field.SetValue(str(confVal))
                confVal = self._config.getValue("MaxValue")
                if(confVal == None):
                    confVal = 1.0
                self._values2Field.SetValue(str(confVal))
                firstConfMode = config.getValue("Smoother")
                self._updateSubModulationSmootherChoices(self._subModulationSmootherField, firstConfMode, "Off")
            else:
                self._subModulationField.SetValue("None")
                self._subModulation2Field.SetValue("None")
                self._subModulation3Field.SetValue("None")
                self._values1Field.SetValue("0.0")
                self._values2Field.SetValue("1.0")
                self._subModulationSmootherField.SetValue("Off")

        if(self._type == "Text"):
            self._noteConfigSizer.Show(self._fontSizer)
        else:
            self._noteConfigSizer.Hide(self._fontSizer)
            

#        if(self._type == "KinectCamera"):
#            self._subModulationLabel.SetLabel("Display mode:")
        if((self._type == "Sprite") or (self._type == "Text")):
            self._subModulationLabel.SetLabel("X position modulation:")
        elif(self._type == "Modulation"):
            self._subModulationLabel.SetLabel("1st modulation:")
        else:
            self._subModulationLabel.SetLabel("Playback modulation:")

        if(self._type == "VideoLoop"):
            self._noteConfigSizer.Show(self._subModeSizer)
        elif(self._type == "Image"):
            self._noteConfigSizer.Show(self._subModeSizer)
        elif(self._type == "ScrollImage"):
            self._noteConfigSizer.Show(self._subModeSizer)
        elif(self._type == "Sprite"):
            self._noteConfigSizer.Show(self._subModeSizer)
        elif(self._type == "ImageSequence"):
            self._noteConfigSizer.Show(self._subModeSizer)
        elif(self._type == "Camera"):
            self._noteConfigSizer.Show(self._subModeSizer)
        else:
            self._noteConfigSizer.Hide(self._subModeSizer)

        if(self._type == "ScrollImage"):
            self._noteConfigSizer.Show(self._subMode2Sizer)
        else:
            self._noteConfigSizer.Hide(self._subMode2Sizer)

        if(self._type == "ScrollImage"):
            self._noteConfigSizer.Show(self._subModulationSizer)
        elif(self._type == "Sprite"):
            self._noteConfigSizer.Show(self._subModulationSizer)
        elif(self._type == "Text"):
            self._noteConfigSizer.Show(self._subModulationSizer)
        elif(self._type == "ImageSequence"):
            self._showOrHideSubModeModulation()
#        elif(self._type == "KinectCamera"):
#            self._noteConfigSizer.Show(self._subModulationSizer)
        elif(self._type == "Modulation"):
            self._noteConfigSizer.Show(self._subModulationSizer)
        else:
            self._noteConfigSizer.Hide(self._subModulationSizer)
            if(self._selectedEditor == self.EditSelection.SubModulation1):
                self._onSubmodulationEdit(None, True)

        if(self._type == "Sprite"):
            self._subModulation2Label.SetLabel("Y position modulation:")
            self._noteConfigSizer.Show(self._subModulation2Sizer)
        elif(self._type == "Text"):
            self._subModulation2Label.SetLabel("Y position modulation:")
            self._noteConfigSizer.Show(self._subModulation2Sizer)
        elif(self._type == "Modulation"):
            self._subModulation2Label.SetLabel("2nd modulation:")
            self._noteConfigSizer.Show(self._subModulation2Sizer)
        else:
            self._noteConfigSizer.Hide(self._subModulation2Sizer)
            if(self._selectedEditor == self.EditSelection.SubModulation2):
                self._onSubmodulation2Edit(None, True)

        if(self._type == "Modulation"):
            self._subModulation3Label.SetLabel("3rd modulation:")
            self._noteConfigSizer.Show(self._subModulation3Sizer)
            self._noteConfigSizer.Show(self._subModulationMode1Sizer)
            self._noteConfigSizer.Show(self._subModulationMode2Sizer)
            self._noteConfigSizer.Show(self._subModulationSmootherSizer)
            self._noteConfigSizer.Hide(self._mixSizer)
            self._noteConfigSizer.Hide(self._effect1Sizer)
            self._noteConfigSizer.Hide(self._effect2Sizer)
            self._noteConfigSizer.Hide(self._fadeSizer)
        else:
            self._noteConfigSizer.Hide(self._subModulation3Sizer)
            self._noteConfigSizer.Hide(self._subModulationMode1Sizer)
            self._noteConfigSizer.Hide(self._subModulationMode2Sizer)
            self._noteConfigSizer.Hide(self._subModulationSmootherSizer)
            self._noteConfigSizer.Show(self._mixSizer)
            self._noteConfigSizer.Show(self._effect1Sizer)
            self._noteConfigSizer.Show(self._effect2Sizer)
            self._noteConfigSizer.Show(self._fadeSizer)

        if(self._type == "KinectCamera"):
            self._values1Label.SetLabel("Filter values:")
            self._noteConfigSizer.Show(self._values1Sizer)
        elif(self._type == "Image"):
            self._values1Label.SetLabel("Start zoom:")
            self._noteConfigSizer.Show(self._values1Sizer)
        elif(self._type == "Sprite"):
            self._values1Label.SetLabel("Start position:")
            self._noteConfigSizer.Show(self._values1Sizer)
        elif(self._type == "Text"):
            self._values1Label.SetLabel("Start position:")
            self._noteConfigSizer.Show(self._values1Sizer)
        elif(self._type == "Modulation"):
            self._values1Label.SetLabel("Minimum value:")
            self._noteConfigSizer.Show(self._values1Sizer)
        else:
            self._noteConfigSizer.Hide(self._values1Sizer)
            if(self._selectedEditor == self.EditSelection.Values1):
                self._onValues1Edit(None, True)


        if(self._type == "Image"):
            self._values2Label.SetLabel("End zoom:")
            self._noteConfigSizer.Show(self._values2Sizer)
        elif(self._type == "Sprite"):
            self._values2Label.SetLabel("End position:")
            self._noteConfigSizer.Show(self._values2Sizer)
        elif(self._type == "Text"):
            self._values2Label.SetLabel("End position:")
            self._noteConfigSizer.Show(self._values2Sizer)
        elif(self._type == "KinectCamera"):
            self._values2Label.SetLabel("Zoom settings:")
            self._noteConfigSizer.Show(self._values2Sizer)
        elif(self._type == "Modulation"):
            self._values2Label.SetLabel("Maximum value:")
            self._noteConfigSizer.Show(self._values2Sizer)
        else:
            self._noteConfigSizer.Hide(self._values2Sizer)
            if(self._selectedEditor == self.EditSelection.Values2):
                self._onValues2Edit(None, True)

        if((self._type == "Camera") or (self._type == "KinectCamera")):
            self._noteConfigSizer.Hide(self._timeModulationSizer)
            if(self._selectedEditor == self.EditSelection.TimeModulation):
                self._onTimeModulationEdit(None, False)
        elif(self._type == "Modulation"):
            self._noteConfigSizer.Hide(self._timeModulationSizer)
            if(self._selectedEditor == self.EditSelection.TimeModulation):
                self._onTimeModulationEdit(None, False)
        else:
            if(config != None):
                timeModulationTemplate = config.getValue("TimeModulationConfig")
                self._updateTimeModulationChoices(self._timeModulationField, timeModulationTemplate, "Default")
            else:
                oldTimeModulationTemplate = self._timeModulationField.GetValue()
                self._updateTimeModulationChoices(self._timeModulationField, oldTimeModulationTemplate, "Default")
            self._noteConfigSizer.Show(self._timeModulationSizer)

        if(self._type == "Group"):
            self._syncFieldLabel.SetLabel("Time multiplyer:")
        else:
            self._syncFieldLabel.SetLabel("Synchronization length:")
            

        if(self._type == "Camera"):
            self._fileNameLabel.SetLabel("Camera ID:")
            self._fileNameField.SetEditable(False)
            self._fileNameField.SetBackgroundColour((232,232,232))
            self._noteConfigSizer.Hide(self._syncSizer)
        elif(self._type == "KinectCamera"):
            self._fileNameLabel.SetLabel("Camera ID:")
            self._fileNameField.SetEditable(False)
            self._fileNameField.SetBackgroundColour((232,232,232))
            self._noteConfigSizer.Hide(self._syncSizer)
        elif(self._type == "Group"):
            self._fileNameLabel.SetLabel("Group notes:")
            self._fileNameField.SetEditable(True)
            self._fileNameField.SetBackgroundColour((255,255,255))
            self._noteConfigSizer.Show(self._syncSizer)
        elif(self._type == "Text"):
            self._fileNameLabel.SetLabel("Text:")
            self._fileNameField.SetEditable(True)
            self._fileNameField.SetBackgroundColour((255,255,255))
            self._noteConfigSizer.Show(self._syncSizer)
        elif(self._type == "Modulation"):
            self._fileNameLabel.SetLabel("Name:")
            self._fileNameField.SetEditable(True)
            self._fileNameField.SetBackgroundColour((255,255,255))
            self._noteConfigSizer.Hide(self._syncSizer)
        else:
            self._fileNameLabel.SetLabel("File name:")
            self._fileNameField.SetEditable(False)
            self._fileNameField.SetBackgroundColour((232,232,232))
            self._noteConfigSizer.Show(self._syncSizer)
        self._noteConfigPanel.Layout()
        self.refreshLayout()

    def updateTimeModulationField(self, widget, value, saveValue):
        self._updateTimeModulationChoices(widget, value, value, False)
        if(saveValue == True):
            timeModulation = self._timeModulationField.GetValue()
            self._config.setValue("TimeModulationConfig", timeModulation)
        self._showOrHideSaveButton()

    def _updateTimeModulationChoices(self, widget, value, defaultValue, updateSaveButton = False):
        if(self._mainConfig == None):
            self._updateChoices(widget, None, value, defaultValue, updateSaveButton)
        else:
            self._updateChoices(widget, self._mainConfig.getTimeModulationChoices, value, defaultValue, updateSaveButton)

    def updateEffectField(self, widget, value, saveValue, fieldName):
        self._updateEffecChoices(widget, value, value, False)
        if(saveValue == True):
            if(fieldName == "Effect1"):
                effect1Config = self._effect1Field.GetValue()
                self._config.setValue("Effect1Config", effect1Config)
            elif(fieldName == "Effect2"):
                effect2Config = self._effect2Field.GetValue()
                self._config.setValue("Effect2Config", effect2Config)
        self._showOrHideSaveButton()

    def _updateEffecChoices(self, widget, value, defaultValue, updateSaveButton = False):
        if(self._mainConfig == None):
            self._updateChoices(widget, None, value, defaultValue, updateSaveButton)
        else:
            self._updateChoices(widget, self._mainConfig.getEffectChoices, value, defaultValue, updateSaveButton)

    def updateFadeField(self, widget, value, saveValue):
        self._updateFadeChoices(widget, value, value, False)
        if(saveValue == True):
            fadeConfig = self._fadeField.GetValue()
            self._config.setValue("FadeConfig", fadeConfig)
        self._showOrHideSaveButton()

    def _updateFadeChoices(self, widget, value, defaultValue, updateSaveButton = False):
        if(self._mainConfig == None):
            self._updateChoices(widget, None, value, defaultValue, updateSaveButton)
        else:
            self._updateChoices(widget, self._mainConfig.getFadeChoices, value, defaultValue, updateSaveButton)

    def _getMediaMixModes(self):
        fullList = self._mixModes.getChoices()
        noDefaultList = []
        for entry in fullList:
            if(entry != "Default"):
                noDefaultList.append(entry)
        return noDefaultList

    def _updateMixModeChoices(self, widget, value, defaultValue):
        self._updateChoices(widget, self._getMediaMixModes, value, defaultValue)

    def _updateLoopModeChoices(self, widget, value, defaultValue):
        self._updateChoices(widget, self._loopModes.getChoices, value, defaultValue)

    def _updateSequenceModeChoices(self, widget, value, defaultValue):
        self._updateChoices(widget, self._sequenceModes.getChoices, value, defaultValue)

    def _getCropChoises(self):
        return ["Crop", "Stretch", "Scale"]

    def _updateCropModeChoices(self, widget, value, defaultValue):
        self._updateChoices(widget, self._getCropChoises, value, defaultValue)

    def _getScrollChoises(self):
        return ["Horizontal", "Vertical"]

    def _updateScrollModeChoices(self, widget, value, defaultValue):
        self._updateChoices(widget, self._getScrollChoises, value, defaultValue)

    def _getReverseChoises(self):
        return ["Off", "On"]

    def _updateReverseModeChoices(self, widget, value, defaultValue):
        self._updateChoices(widget, self._getReverseChoises, value, defaultValue)

    def _getInvertChoises(self):
        return ["Normal", "Invert mask"]

    def _updateInvertModeChoices(self, widget, value, defaultValue):
        self._updateChoices(widget, self._getInvertChoises, value, defaultValue)

    def _updateTypeChoices(self, widget, value, defaultValue):
        self._updateChoices(widget, self._typeModes.getChoices, value, defaultValue)

    def _getCombineModulation1Choises(self):
        return ["Add", "Subtract", "Mutiply", "Mask", "If (1st > 0.5) Then:"]

    def _updateSubModulationMode1Choices(self, widget, value, defaultValue):
        self._updateChoices(widget, self._getCombineModulation1Choises, value, defaultValue)

    def _getCombineModulation2Choises(self):
        return ["Add", "Subtract", "Mutiply", "Mask"]

    def _getCombineModulation2Choises2(self):
        return ["Else"]

    def _updateSubModulationMode2Choices(self, widget, value, defaultValue, ifMode=False):
        if(ifMode == True):
            self._updateChoices(widget, self._getCombineModulation2Choises2, "Else", "Else")
        else:
            self._updateChoices(widget, self._getCombineModulation2Choises, value, defaultValue)

    def _getModulationSmootherChoises(self):
        return ["Off", "Smoothish", "Smooth", "Smoother","Smoothest"]

    def _updateSubModulationSmootherChoices(self, widget, value, defaultValue):
            self._updateChoices(widget, self._getModulationSmootherChoises, value, defaultValue)

    def _updateChoices(self, widget, choicesFunction, value, defaultValue, updateSaveButton = False):
        if(choicesFunction == None):
            choiceList = [value]
        else:
            choiceList = choicesFunction()
        widget.Clear()
        valueOk = False
        for choice in choiceList:
            widget.Append(choice)
            if(choice == value):
                valueOk = True
        if(valueOk == True):
            widget.SetStringSelection(value)
        else:
            widget.SetStringSelection(defaultValue)
        if(updateSaveButton == True):
            self._showOrHideSaveButton()

    def updateMixmodeThumb(self, widget, mixMode, noteMixMode, showDefault = False):
        if(mixMode == "Default"):
            if(noteMixMode == "None"):
                widget.setBitmaps(self._mixBitmapDefault, self._mixBitmapDefault)
                return
            mixMode = noteMixMode
        mixModeId = getMixModeFromName(mixMode)
        if(mixModeId == self._mixModes.Add):
            widget.setBitmaps(self._mixBitmapAdd, self._mixBitmapAdd)
        if(mixModeId == self._mixModes.AlphaMask):
            widget.setBitmaps(self._mixBitmapAlpha, self._mixBitmapAlpha)
        elif(mixModeId == self._mixModes.Default):
            if(showDefault == True):
                widget.setBitmaps(self._mixBitmapDefault, self._mixBitmapDefault)#Default is Add!
            else:
                widget.setBitmaps(self._mixBitmapAdd, self._mixBitmapAdd)#Default is Add!
        elif(mixModeId == self._mixModes.LumaKey):
            widget.setBitmaps(self._mixBitmapLumaKey, self._mixBitmapLumaKey)
        elif(mixModeId == self._mixModes.WhiteLumaKey):
            widget.setBitmaps(self._mixBitmapWhiteLumaKey, self._mixBitmapWhiteLumaKey)
        elif(mixModeId == self._mixModes.Multiply):
            widget.setBitmaps(self._mixBitmapMultiply, self._mixBitmapMultiply)
        elif(mixModeId == self._mixModes.Replace):
            widget.setBitmaps(self._mixBitmapReplace, self._mixBitmapReplace)
        elif(mixModeId == self._mixModes.Subtract):
            widget.setBitmaps(self._mixBitmapSubtract, self._mixBitmapSubtract)

    def updateEffectThumb(self, widget, effectConfigName):
        effectTemplate = self._mainConfig.getEffectTemplate(effectConfigName)
        effectTemplate.checkAndUpdateFromConfiguration()
        effectName = effectTemplate.getEffectName()
        effectId = getEffectId(effectName)
        if(effectId == None):
            widget.setBitmaps(self._blankFxBitmap, self._blankFxBitmap)
        elif(effectId == EffectTypes.BlobDetect):
            widget.setBitmaps(self._fxBitmapBlobDetect, self._fxBitmapBlobDetect)
        elif(effectId == EffectTypes.Blur):
            widget.setBitmaps(self._fxBitmapBlur, self._fxBitmapBlur)
        elif(effectId == EffectTypes.BlurContrast):
            widget.setBitmaps(self._fxBitmapBlurMul, self._fxBitmapBlurMul)
        elif(effectId == EffectTypes.Feedback):
            widget.setBitmaps(self._fxBitmapFeedback, self._fxBitmapFeedback)
        elif(effectId == EffectTypes.Delay):
            widget.setBitmaps(self._fxBitmapDelay, self._fxBitmapDelay)
        elif(effectId == EffectTypes.SelfDifference):
            widget.setBitmaps(self._fxBitmapSelfDiff, self._fxBitmapSelfDiff)
        elif(effectId == EffectTypes.Colorize):
            widget.setBitmaps(self._fxBitmapColorize, self._fxBitmapColorize)
        elif(effectId == EffectTypes.Contrast):
            widget.setBitmaps(self._fxBitmapContrast, self._fxBitmapContrast)
        elif(effectId == EffectTypes.Desaturate):
            widget.setBitmaps(self._fxBitmapDeSat, self._fxBitmapDeSat)
        elif(effectId == EffectTypes.Distortion):
            widget.setBitmaps(self._fxBitmapDist, self._fxBitmapDist)
        elif(effectId == EffectTypes.Edge):
            widget.setBitmaps(self._fxBitmapEdge, self._fxBitmapEdge)
        elif(effectId == EffectTypes.Flip):
            widget.setBitmaps(self._fxBitmapFlip, self._fxBitmapFlip)
        elif(effectId == EffectTypes.HueSaturation):
            widget.setBitmaps(self._fxBitmapHueSat, self._fxBitmapHueSat)
        elif(effectId == EffectTypes.ImageAdd):
            widget.setBitmaps(self._fxBitmapImageAdd, self._fxBitmapImageAdd)
        elif(effectId == EffectTypes.Invert):
            widget.setBitmaps(self._fxBitmapInverse, self._fxBitmapInverse)
        elif(effectId == EffectTypes.Mirror):
            widget.setBitmaps(self._fxBitmapMirror, self._fxBitmapMirror)
        elif(effectId == EffectTypes.Pixelate):
            widget.setBitmaps(self._fxBitmapPixelate, self._fxBitmapPixelate)
        elif(effectId == EffectTypes.Rays):
            widget.setBitmaps(self._fxBitmapRays, self._fxBitmapRays)
        elif(effectId == EffectTypes.SlitScan):
            widget.setBitmaps(self._fxBitmapSlitScan, self._fxBitmapSlitScan)
        elif(effectId == EffectTypes.Rotate):
            widget.setBitmaps(self._fxBitmapRotate, self._fxBitmapRotate)
        elif(effectId == EffectTypes.Scroll):
            widget.setBitmaps(self._fxBitmapScroll, self._fxBitmapScroll)
        elif(effectId == EffectTypes.Threshold):
            widget.setBitmaps(self._fxBitmapThreshold, self._fxBitmapThreshold)
        elif(effectId == EffectTypes.TVNoize):
            widget.setBitmaps(self._fxBitmapTVNoize, self._fxBitmapTVNoize)
        elif(effectId == EffectTypes.ValueToHue):
            widget.setBitmaps(self._fxBitmapVal2Hue, self._fxBitmapVal2Hue)
        elif(effectId == EffectTypes.Zoom):
            widget.setBitmaps(self._fxBitmapZoom, self._fxBitmapZoom)
        else:
            print "Warning! Missing FX bitmap for effect: " + str(effectConfigName) + " with id: " + str(effectId)
            widget.setBitmaps(self._blankFxBitmap, self._blankFxBitmap)

    def updateMediaTypeThumb(self, widget, configHolder):
        if(configHolder != None):
            mediaType = configHolder.getValue("Type")
        else:
            mediaType = self._type
        if(mediaType == "Camera" or self._type == "KinectCamera"):
            widget.setBitmaps(self._modeBitmapCamera, self._modeBitmapCamera)
        elif(mediaType == "Image"):
            widget.setBitmaps(self._modeBitmapImage, self._modeBitmapImage)
        elif(mediaType == "ScrollImage"):
            widget.setBitmaps(self._modeBitmapImageScroll, self._modeBitmapImageScroll)
        elif(mediaType == "Sprite"):
            widget.setBitmaps(self._modeBitmapSprite, self._modeBitmapSprite)
        elif(mediaType == "Text"):
            widget.setBitmaps(self._modeBitmapText, self._modeBitmapText)
        elif(mediaType == "Group"):
            widget.setBitmaps(self._modeBitmapGroup, self._modeBitmapGroup)
        elif(mediaType == "Modulation"):
            widget.setBitmaps(self._modeBitmapModulation, self._modeBitmapModulation)
        elif(mediaType == "VideoLoop"):
            if(configHolder != None):
                loopMode = configHolder.getValue("LoopMode")
            else:
                loopMode = self._subModeField.GetValue()
            if(loopMode == "Normal"):
                widget.setBitmaps(self._modeBitmapLoop, self._modeBitmapLoop)
            elif(loopMode == "Reverse"):
                widget.setBitmaps(self._modeBitmapLoopReverse, self._modeBitmapLoopReverse)
            elif(loopMode == "PingPong"):
                widget.setBitmaps(self._modeBitmapPingPong, self._modeBitmapPingPong)
            elif(loopMode == "PingPongReverse"):
                widget.setBitmaps(self._modeBitmapPingPongReverse, self._modeBitmapPingPongReverse)
            elif(loopMode == "DontLoop"):
                widget.setBitmaps(self._modeBitmapPlayOnce, self._modeBitmapPlayOnce)
            elif(loopMode == "DontLoopReverse"):
                widget.setBitmaps(self._modeBitmapPlayOnceReverse, self._modeBitmapPlayOnceReverse)
        elif(mediaType == "ImageSequence"):
            if(configHolder != None):
                seqMode = configHolder.getValue("SequenceMode")
            else:
                seqMode = self._subModeField.GetValue()
            if(seqMode == "Time"):
                widget.setBitmaps(self._modeBitmapImageSeqTime, self._modeBitmapImageSeqTime)
            elif(seqMode == "ReTrigger"):
                widget.setBitmaps(self._modeBitmapImageSeqReTrigger, self._modeBitmapImageSeqReTrigger)
            elif(seqMode == "Modulation"):
                widget.setBitmaps(self._modeBitmapImageSeqModulation, self._modeBitmapImageSeqModulation)

    def _onOverviewClipEditButton(self, event):
        if(self._noteGuiOpen == False):
            self.showNoteGui()
        else:
            self.hideNoteGui()

    def _updateEditButton(self, isOpen):
        self._noteGuiOpen = isOpen
        if(isOpen == True):
            self._overviewClipEditButton.setBitmaps(self._editBigBitmap, self._editBigPressedBitmap)
        else:
            self._overviewClipEditButton.setBitmaps(self._editBigBitmap, self._editBigPressedBitmap)

    def _onOverviewClipSaveButton(self, event):
        if(self._overviewClipSaveButtonDissabled == False):
            self._onSaveButton(event)

    def _onMouseRelease(self, event):
        print "DEBUG mouse RELEASE " * 5
        self._mainConfig.getDraggedFxName()
        self._clearDragCursorCallback()

    def _onClipMixButton(self, event):
        self._clipOverviewGuiPlane.PopupMenu(self._overviewClipMixButtonPopup, (77,30))

    def _onClipMixChosen(self, index):
        if((index >= 0) and (index < len(self._mixLabels))):
            modeText = self._mixLabels[index]
            self._updateMixModeChoices(self._mixField, modeText, "Add")
            self.updateMixmodeThumb(self._overviewClipMixButton, modeText, modeText)
            self._showOrHideSaveButton()

    def _onClipModeButton(self, event):
        self._clipOverviewGuiPlane.PopupMenu(self._overviewClipModeButtonPopup, (77,13))

    def _onClipModeChosen(self, index):
        if((index >= 0) and (index < len(self._modeLabels))):
            modeText = self._modeLabels[index]
            loopMode = None
            if(modeText == "VideoLoop"):
                self._type = "VideoLoop"
                loopMode = "Normal"
                self._updateLoopModeChoices(self._subModeField, loopMode, "Normal")
            elif(modeText == "VideoLoopReverse"):
                self._type = "VideoLoop"
                loopMode = "Reverse"
                self._updateLoopModeChoices(self._subModeField, loopMode, "Normal")
            elif(modeText == "VideoPingPong"):
                self._type = "VideoLoop"
                loopMode = "PingPong"
                self._updateLoopModeChoices(self._subModeField, loopMode, "Normal")
            elif(modeText == "VideoPingPongReverse"):
                self._type = "VideoLoop"
                loopMode = "PingPongReverse"
                self._updateLoopModeChoices(self._subModeField, loopMode, "Normal")
            elif(modeText == "VideoPlayOnce"):
                self._type = "VideoLoop"
                loopMode = "DontLoop"
                self._updateLoopModeChoices(self._subModeField, loopMode, "Normal")
            elif(modeText == "VideoPlayOnceReverse"):
                self._type = "VideoLoop"
                loopMode = "DontLoopReverse"
                self._updateLoopModeChoices(self._subModeField, loopMode, "Normal")
            elif(modeText == "Camera"):
                self._type = "Camera"
            elif(modeText == "KinectCamera"):
                self._type = "KinectCamera"
            elif(modeText == "Image"):
                self._type = "Image"
            elif(modeText == "ScrollImage"):
                self._type = "ScrollImage"
            elif(modeText == "Sprite"):
                self._type = "Sprite"
            elif(modeText == "Text"):
                self._type = "Text"
            elif(modeText == "Group"):
                self._type = "Group"
            elif(modeText == "Modulation"):
                self._type = "Modulation"
            elif(modeText == "ImageSeqTime"):
                self._type = "ImageSequence"
                self._updateSequenceModeChoices(self._subModeField, "Time", "Time")
            elif(modeText == "ImageSeqReTrigger"):
                self._type = "ImageSequence"
                self._updateSequenceModeChoices(self._subModeField, "ReTrigger", "Time")
            elif(modeText == "ImageSeqModulation"):
                self._type = "ImageSequence"
                self._updateSequenceModeChoices(self._subModeField, "Modulation", "Time")

            self._updateTypeChoices(self._typeField, self._type, "VideoLoop")
            self._setupSubConfig(None)
            self.updateMediaTypeThumb(self._overviewClipModeButton, None)
            self._showOrHideSaveButton()

    def _onClipFadeModeChosen(self, index):
        if((index >= 0) and (index < len(self._wipeModeLabels))):
            if(self._midiNote != None):
                wipeMode = self._wipeModeLabels[index]
                if(self._config != None):
                    fadeConfigName = self._config.getValue("FadeConfig")
                    fadeConfig = self._mainConfig.getFadeTemplate(fadeConfigName)
                    if(fadeConfig != None):
                        if(fadeConfig.getFadeMode() != wipeMode):
                            makeNew = False
                            if(fadeConfigName == "Default"):
                                makeNew = True
                            else:
                                inUseNumber = self._mainConfig.countNumberOfTimeFadeTemplateUsed(fadeConfigName)
                                if(inUseNumber < 2):
                                    fadeConfig.update(wipeMode, None, None)
                                else:
                                    makeNew = True
                            if(makeNew == True):
                                newFadeConfigName = "NoteFade_" + noteToNoteString(self._midiNote)
                                oldConfig = self._mainConfig.getFadeTemplate(newFadeConfigName)
                                if(oldConfig == None):
                                    text = "Do you want to make a new configuration: \"%s\"" % (newFadeConfigName)
                                else:
                                    text = "Do you want to update configuration: \"%s\"" % (newFadeConfigName)
                                dlg = wx.MessageDialog(self._mediaFileGuiPanel, text, 'Move?', wx.YES_NO | wx.ICON_QUESTION) #@UndefinedVariable
                                result = dlg.ShowModal() == wx.ID_YES #@UndefinedVariable
                                dlg.Destroy()
                                if(result == True):
                                    if(oldConfig == None):
                                        self._mainConfig.makeFadeTemplate(newFadeConfigName, wipeMode, False, 0.0, "None", "None")
                                        if(self._config != None):
                                            self._config.setValue("FadeConfig", newFadeConfigName)
                                    else:
                                        oldConfig.update(wipeMode, None, None, None, None)
                                    self._updateFadeChoices(self._fadeField, newFadeConfigName, "Default")
                                    self._mainConfig.updateFadeGuiButtons(newFadeConfigName, None, self._overviewClipFadeModeButton, self._overviewClipFadeModulationButton, self._overviewClipFadeLevelButton)
                                    self._showOrHideSaveButton()

    def _onClipFadeButton(self, event):
        self._onFadeEdit(event)

    def _onClipFadeModulationButton(self, event):
        self._onFadeEdit(event)

    def _onClipFadeLevelButton(self, event):
        self._onFadeEdit(event)

    def _onLengthDoubbleButton(self, event):
        if(self._config != None):
            oldLength = float(self._syncField.GetValue())
            newLength = oldLength * 2
            self._syncField.SetValue(str(newLength))
            if(newLength >= 1000):
                newLength = int(newLength)
            self._overviewClipLengthLabel.SetLabel(str(newLength))
            self._showOrHideSaveButton()

    def _onLengthHalfButton(self, event):
        if(self._config != None):
            oldLength = float(self._syncField.GetValue())
            newLength = oldLength / 2
            self._syncField.SetValue(str(newLength))
            if(newLength >= 1000):
                newLength = int(newLength)
            self._overviewClipLengthLabel.SetLabel(str(newLength))
            self._showOrHideSaveButton()

    def _onSyncDoubbleButton(self, event):
        if(self._config != None):
            oldLength = float(self._quantizeField.GetValue())
            newLength = oldLength * 2
            self._quantizeField.SetValue(str(newLength))
            if(newLength >= 1000):
                newLength = int(newLength)
            self._overviewClipQuantizeLabel.SetLabel(str(newLength))
            self._showOrHideSaveButton()

    def _onSyncHalfButton(self, event):
        if(self._config != None):
            oldLength = float(self._quantizeField.GetValue())
            newLength = oldLength / 2
            self._quantizeField.SetValue(str(newLength))
            if(newLength >= 1000):
                newLength = int(newLength)
            self._overviewClipQuantizeLabel.SetLabel(str(newLength))
            self._showOrHideSaveButton()

    def _onDragFx1Done(self, event):
        fxName = self._mainConfig.getDraggedFxName()
        if(fxName != None):
            if(self._midiNote != None):
                self._updateEffecChoices(self._effect1Field, fxName, "MediaDefault1")
                self.updateEffectThumb(self._overviewFx1Button, fxName)
                self._showOrHideSaveButton()
        self._clearDragCursorCallback()

    def _onDragFx2Done(self, event):
        fxName = self._mainConfig.getDraggedFxName()
        if(fxName != None):
            if(self._midiNote != None):
                self._updateEffecChoices(self._effect2Field, fxName, "MediaDefault2")
                self.updateEffectThumb(self._overviewFx2Button, fxName)
                self._showOrHideSaveButton()
        self._clearDragCursorCallback()

    def _onFxButton(self, event):
        buttonId = event.GetEventObject().GetId()
        effectConfigName = None
        effectId = None
        midiNote = None
        if(self._config != None):
            if(buttonId == self._overviewFx1Button.GetId()):
                effectConfigName = self._config.getValue("Effect1Config")
                effectId = "Effect1"
                midiNote = self._midiNote
                if((self._selectedEditor == self.EditSelection.Effect1) or (self._selectedEditor == self.EditSelection.Effect2)):
                    self._selectedEditor = self.EditSelection.Effect1
                else:
                    self._selectedEditor = self.EditSelection.Unselected
            if(buttonId == self._overviewFx2Button.GetId()):
                effectConfigName = self._config.getValue("Effect2Config")
                effectId = "Effect2"
                midiNote = self._midiNote
                if((self._selectedEditor == self.EditSelection.Effect1) or (self._selectedEditor == self.EditSelection.Effect2)):
                    self._selectedEditor = self.EditSelection.Effect2
                else:
                    self._selectedEditor = self.EditSelection.Unselected
        if(effectConfigName != None):
            self._mainConfig.updateEffectsGui(effectConfigName, midiNote, effectId, None)
            self._mainConfig.showSliderGuiEditButton()
            self.showSlidersGui()
        self._highlightButton(self._selectedEditor)

    def _onFxButtonDouble(self, event):
        buttonId = event.GetEventObject().GetId()
        effectConfigName = None
        if(self._config != None):
            if(buttonId == self._overviewFx1Button.GetId()):
                effectConfigName = self._config.getValue("Effect1Config")
            if(buttonId == self._overviewFx2Button.GetId()):
                effectConfigName = self._config.getValue("Effect2Config")
        self._mainConfig.updateEffectList(effectConfigName)
        self.showEffectList()

    def _onClipFadeButtonDouble(self, event):
        fadeConfigName = None
        if(self._config != None):
            fadeConfigName = self._config.getValue("FadeConfig")
        self._mainConfig.updateFadeList(fadeConfigName)
        self.showFadeListGui()

    def updateOverviewClipBitmap(self, clipBitmap):
        if(clipBitmap != None):
            self._overviewClipButton.setBitmap(clipBitmap)
        else:
            self._overviewClipButton.setBitmap(self._emptyBitMap)

    def _checkIfUpdated(self):
        guiFileName = self._fileNameField.GetValue()
        if(self._config == None):
            if(guiFileName != ""):
                return True
            else:
                return False
        configFileName = os.path.basename(self._config.getValue("FileName"))
        if((guiFileName == "") and (configFileName == "")):
            return False
        if(guiFileName != configFileName):
            return True
        guiType = self._typeField.GetValue()
        configType = self._config.getValue("Type")
        if(guiType != configType):
            return True
        if(configType == "VideoLoop"):
            guiMode = self._subModeField.GetValue()
            configMode = self._config.getValue("LoopMode")
            if(guiMode != configMode):
                return True
        if(self._type == "Image"):
            guiSubMode = self._values1Field.GetValue()
            configSubMode = self._config.getValue("StartValues")
            if(guiSubMode != configSubMode):
                return True
            guiSubMode = self._values2Field.GetValue()
            configSubMode = self._config.getValue("EndValues")
            if(guiSubMode != configSubMode):
                return True
            guiSubMode = self._subModeField.GetValue()
            configSubMode = self._config.getValue("DisplayMode")
            if(guiSubMode != configSubMode):
                return True
        if(self._type == "ScrollImage"):
            guiSubMode = self._subModulationField.GetValue()
            configSubMode = self._config.getValue("ScrollModulation")
            if(guiSubMode != configSubMode):
                return True
            guiSubMode = self._subModeField.GetValue()
            if(guiSubMode == "Horizontal"):
                guiSubModeVal = True
            else:
                guiSubModeVal = False
            configSubMode = self._config.getValue("HorizontalMode")
            if(guiSubModeVal != configSubMode):
                return True
            guiSubMode = self._subMode2Field.GetValue()
            if(guiSubMode == "On"):
                guiSubModeVal = True
            else:
                guiSubModeVal = False
            configSubMode = self._config.getValue("ReverseMode")
            if(guiSubModeVal != configSubMode):
                return True
        if((self._type == "Sprite") or (self._type == "Text")):
            guiSubMode = self._subModulationField.GetValue()
            configSubMode = self._config.getValue("XModulation")
            if(guiSubMode != configSubMode):
                return True
            guiSubMode = self._subModulation2Field.GetValue()
            configSubMode = self._config.getValue("YModulation")
            if(guiSubMode != configSubMode):
                return True
            guiSubMode = self._values1Field.GetValue()
            configSubMode = self._config.getValue("StartPosition")
            if(guiSubMode != configSubMode):
                return True
            guiSubMode = self._values2Field.GetValue()
            configSubMode = self._config.getValue("EndPosition")
            if(guiSubMode != configSubMode):
                return True
        if(self._type == "Sprite"):
            guiSubMode = self._subModeField.GetValue()
            if(guiSubMode == "Normal"):
                guiSubModeVal = False
            else:
                guiSubModeVal = True
            configSubMode = self._config.getValue("InvertFirstFrameMask")
            if(guiSubModeVal != configSubMode):
                return True
        if(self._type == "Text"):
            guiFont = self._fontField.GetValue()
            configFont = self._config.getValue("Font")
            if(guiFont != configFont):
                return True
        if(self._type == "ImageSequence"):
            guiMode = self._subModeField.GetValue()
            configMode = self._config.getValue("SequenceMode")
            if(guiMode != configMode):
                return True
            guiSubMode = self._subModulationField.GetValue()
            configSubMode = self._config.getValue("PlaybackModulation")
            if(guiSubMode != configSubMode):
                return True
        if(self._type == "Camera"):
            guiSubMode = self._subModeField.GetValue()
            configSubMode = self._config.getValue("DisplayMode")
            if(guiSubMode != configSubMode):
                return True
        if(self._type == "KinectCamera"):
            guiSubMode = self._values1Field.GetValue()
            configSubMode = self._config.getValue("FilterValues")
            if(guiSubMode != configSubMode):
                return True
            guiSubMode = self._values2Field.GetValue()
            configSubMode = self._config.getValue("ZoomValues")
            if(guiSubMode != configSubMode):
                return True
        if(self._type == "Modulation"):
            guiSubMode = self._subModulationField.GetValue()
            configSubMode = self._config.getValue("FirstModulation")
            if(guiSubMode != configSubMode):
                return True
            guiSubMode = self._subModulationMode1Field.GetValue()
            configSubMode = self._config.getValue("ModulationCombiner1")
            if(guiSubMode != configSubMode):
                return True
            guiSubMode = self._subModulation2Field.GetValue()
            configSubMode = self._config.getValue("SecondModulation")
            if(guiSubMode != configSubMode):
                return True
            guiSubMode = self._subModulationMode2Field.GetValue()
            configSubMode = self._config.getValue("ModulationCombiner2")
            if(guiSubMode != configSubMode):
                return True
            guiSubMode = self._subModulation3Field.GetValue()
            configSubMode = self._config.getValue("ThirdModulation")
            if(guiSubMode != configSubMode):
                return True
            guiValue = self._values1Field.GetValue()
            configValue = self._config.getValue("MinValue")
            if(guiValue != configValue):
                return True
            guiValue = self._values2Field.GetValue()
            configValue = self._config.getValue("MaxValue")
            if(guiValue != configValue):
                return True
            guiValue = self._subModulationSmootherField.GetValue()
            configValue = self._config.getValue("Smoother")
            if(guiValue != configValue):
                return True
        else:
            guiMix = self._mixField.GetValue()
            configMix = self._config.getValue("MixMode")
#            print "DEBUG test mixmode GUI: " + str(guiMix) + " cfg: " + str(configMix)
            if(guiMix != configMix):
#                print "DEBUG MixMode differs!"
                return True
            guiFx1 = self._effect1Field.GetValue()
            configFx1 = self._config.getValue("Effect1Config")
            if(guiFx1 != configFx1):
                return True
            guiFx2 = self._effect2Field.GetValue()
            configFx2 = self._config.getValue("Effect2Config")
            if(guiFx2 != configFx2):
                return True
            guiFade = self._fadeField.GetValue()
            configFade = self._config.getValue("FadeConfig")
            if(guiFade != configFade):
                return True
        if((self._type != "Modulation") and (self._type != "Camera") and (self._type != "KinectCamera")):
            guiTime = self._timeModulationField.GetValue()
            configTime = self._config.getValue("TimeModulationConfig")
            if(guiTime != configTime):
                return True
        guiSyncLength = float(self._syncField.GetValue())
        configSyncLength = float(self._config.getValue("SyncLength"))
        if(guiSyncLength != configSyncLength):
            return True
        guiQLength = float(self._quantizeField.GetValue())
        configQLength = float(self._config.getValue("QuantizeLength"))
        if(guiQLength != configQLength):
            return True
        return False

    def _onUpdate(self, event):
        self._showOrHideSaveButton()

    def _showOrHideSaveButton(self):
        updated = self._checkIfUpdated()
        if(updated == False):
            self._overviewClipSaveButton.setBitmaps(self._saveBigGreyBitmap, self._saveBigGreyBitmap)
            self._saveButton.setBitmaps(self._saveBigGreyBitmap, self._saveBigGreyBitmap)
            self._overviewClipSaveButtonDissabled = True
        if(updated == True):
            self._overviewClipSaveButton.setBitmaps(self._saveBigBitmap, self._saveBigPressedBitmap)
            self._saveButton.setBitmaps(self._saveBigBitmap, self._saveBigPressedBitmap)
            self._overviewClipSaveButtonDissabled = False
        
    def updateGui(self, noteConfig, midiNote):
        if(noteConfig != None):
            config = noteConfig.getConfig()
            self._config = config
            self._midiNote = midiNote
        if(self._config == None):
            return
        self._type = self._config.getValue("Type")
        if(self._type == "Camera" or self._type == "KinectCamera"):
            fileNameFieldValue = self._config.getValue("FileName")
            try:
                self._cameraId = int(fileNameFieldValue)
            except:
                self._cameraId = 0
            self._fileName = ""
            self._fileNameField.SetValue(str(self._cameraId))
        else:
            self._cameraId = 0
            self._fileName = self._config.getValue("FileName")
            if((self._type == "Group") or (self._type == "Modulation") or (self._type == "Text")):
                self._fileNameField.SetValue(self._fileName)
            else:
                self._fileNameField.SetValue(os.path.basename(self._fileName))
        self._updateTypeChoices(self._typeField, self._type, "VideoLoop")
        self._setupSubConfig(self._config)
        self.updateMediaTypeThumb(self._overviewClipModeButton, self._config)
        noteText = self._config.getValue("Note")
        self._noteField.SetValue(noteText)
        self._overviewClipNoteLabel.SetLabel("NOTE: " + noteText)
        length = self._config.getValue("SyncLength")
        self._syncField.SetValue(str(length))
        if(length >= 1000):
            length = int(float(length))
        else:
            length = float(length)
        self._overviewClipLengthLabel.SetLabel(str(length))
        qLength = self._config.getValue("QuantizeLength")
        self._quantizeField.SetValue(str(qLength))
        if(qLength >= 1000):
            qLength = int(float(qLength))
        else:
            qLength = float(qLength)
        self._overviewClipQuantizeLabel.SetLabel(str(qLength))
        if(self._type == "Modulation"):
            self._overviewClipMixButton.setBitmaps(self._blankMixBitmap, self._blankMixBitmap)
            self._overviewFx1Button.setBitmaps(self._blankFxBitmap, self._blankFxBitmap)
            self._overviewFx2Button.setBitmaps(self._blankFxBitmap, self._blankFxBitmap)
            self._mainConfig.updateFadeGuiButtons("Clear\nThe\Buttons\nV0tt", None, self._overviewClipFadeModeButton, self._overviewClipFadeModulationButton, self._overviewClipFadeLevelButton)
        else:
            mixMode = self._config.getValue("MixMode")
            self._updateMixModeChoices(self._mixField, mixMode, "Add")
            self.updateMixmodeThumb(self._overviewClipMixButton, mixMode, mixMode)
            effect1Config = self._config.getValue("Effect1Config")
            self._updateEffecChoices(self._effect1Field, effect1Config, "MediaDefault1")
            self.updateEffectThumb(self._overviewFx1Button, effect1Config)
            effect2Config = self._config.getValue("Effect2Config")
            self._updateEffecChoices(self._effect2Field, effect2Config, "MediaDefault2")
            self.updateEffectThumb(self._overviewFx2Button, effect2Config)
            fadeConfigName = self._config.getValue("FadeConfig")
            self._updateFadeChoices(self._fadeField, fadeConfigName, "Default")
            self._mainConfig.updateFadeGuiButtons(fadeConfigName, None, self._overviewClipFadeModeButton, self._overviewClipFadeModulationButton, self._overviewClipFadeLevelButton)

        if(self._selectedEditor != None):
            if(self._selectedEditor == self.EditSelection.TimeModulation):
                self._onTimeModulationEdit(None, False)
            elif(self._selectedEditor == self.EditSelection.Effect1):
                self._onEffect1Edit(None, False)
            elif(self._selectedEditor == self.EditSelection.Effect2):
                self._onEffect2Edit(None, False)
            elif(self._selectedEditor == self.EditSelection.Fade):
                self._onFadeEdit(None, False)
            elif(self._selectedEditor == self.EditSelection.SubModulation1):
                self._onSubmodulationEdit(None, False)
            elif(self._selectedEditor == self.EditSelection.SubModulation2):
                self._onSubmodulation2Edit(None, False)
            elif(self._selectedEditor == self.EditSelection.SubModulation3):
                self._onSubmodulation3Edit(None, False)
            elif(self._selectedEditor == self.EditSelection.Values1):
                self._onValues1Edit(None, False)
            elif(self._selectedEditor == self.EditSelection.Values2):
                self._onValues2Edit(None, False)

        self._showOrHideSaveButton()

    def clearGui(self, midiNote):
        self._config = None
        self._midiNote = midiNote
        midiNoteString = noteToNoteString(self._midiNote)
        self._cameraId = 0
        self._fileName = ""
        self._fileNameField.SetValue("")
        self._type = "VideoLoop"
        self._updateTypeChoices(self._typeField, self._type, "VideoLoop")
        self._updateLoopModeChoices(self._subModeField, "Normal", "Normal")
        self._setupSubConfig(self._config)
        self._noteField.SetValue(midiNoteString)
        self._syncField.SetValue("4.0")
        self._quantizeField.SetValue("1.0")
        self._updateMixModeChoices(self._mixField, "Add", "Add")
        self._updateEffecChoices(self._effect1Field, "MediaDefault1", "MediaDefault1")
        self._updateEffecChoices(self._effect2Field, "MediaDefault2", "MediaDefault2")
        self._updateFadeChoices(self._fadeField, "Default", "Default")

        if(self._selectedEditor != None):
            if(self._selectedEditor == self.EditSelection.TimeModulation):
                self._onTimeModulationEdit(None, False)
            elif(self._selectedEditor == self.EditSelection.Effect1):
                self._onEffect1Edit(None, False)
            elif(self._selectedEditor == self.EditSelection.Effect2):
                self._onEffect2Edit(None, False)
            elif(self._selectedEditor == self.EditSelection.Fade):
                self._onFadeEdit(None, False)
            elif(self._selectedEditor == self.EditSelection.SubModulation1):
                self._onSubmodulationEdit(None, False)
            elif(self._selectedEditor == self.EditSelection.SubModulation2):
                self._onSubmodulation2Edit(None, False)
            elif(self._selectedEditor == self.EditSelection.SubModulation3):
                self._onSubmodulation3Edit(None, False)
            elif(self._selectedEditor == self.EditSelection.Values1):
                self._onValues1Edit(None, False)
            elif(self._selectedEditor == self.EditSelection.Values2):
                self._onValues2Edit(None, False)

        self._overviewClipButton.setBitmap(self._emptyBitMap)
        self._overviewClipModeButton.setBitmaps(self._blankModeBitmap, self._blankModeBitmap)
        self._overviewClipMixButton.setBitmaps(self._blankMixBitmap, self._blankMixBitmap)
        self._overviewClipLengthLabel.SetLabel("N/A")
        self._overviewClipQuantizeLabel.SetLabel("N/A")
        self._overviewFx1Button.setBitmaps(self._blankFxBitmap, self._blankFxBitmap)
        self._overviewFx2Button.setBitmaps(self._blankFxBitmap, self._blankFxBitmap)
        self._overviewClipNoteLabel.SetLabel("NOTE: " + midiNoteString)
        self._mainConfig.updateFadeGuiButtons("Clear\nThe\Buttons\nV0tt", None, self._overviewClipFadeModeButton, self._overviewClipFadeModulationButton, self._overviewClipFadeLevelButton)

        self._showOrHideSaveButton()


