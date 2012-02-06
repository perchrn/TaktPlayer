'''
Created on 6. feb. 2012

@author: pcn
'''
from midi.MidiUtilities import noteToNoteString, noteStringToNoteNumber

class MediaPoolConfig(object):
    def __init__(self, configParent):
        self._configurationTree = configParent.addChildUnique("MediaPool")

        self._mediaPool = []
        for i in range(128): #@UnusedVariable
            self._mediaPool.append(None)

        self.loadMediaFromConfiguration()

    def _getConfiguration(self):
        print "DEBUG: MediaPoolConfig._getConfiguration"
        self.loadMediaFromConfiguration()

    def checkAndUpdateFromConfiguration(self):
        if(self._configurationTree.isConfigurationUpdated()):
            print "mediaPool config is updated..."
            self._getConfiguration()
            self._configurationTree.resetConfigurationUpdated()
        else:
            print "DEBUG: MediaPoolConfig.checkAndUpdateFromConfiguration NOT updated..."

    def loadMediaFromConfiguration(self):
        mediaPoolState = []
        for i in range(128):
            mediaPoolState.append(False)
        mediaFileChildren = self._configurationTree.findXmlChildrenList("MediaFile")
        if(mediaFileChildren != None):
            print "self._configurationTree.findXmlChildrenList(\"MediaFile\") != None"
            for xmlConfig in mediaFileChildren:
                print "adding one..."
                midiNote = self.addXmlMedia(xmlConfig)
                mediaPoolState[midiNote] = True
        else:
            print "self._configurationTree.findXmlChildrenList(\"MediaFile\") == None"
        for i in range(128):
            mediaState = mediaPoolState[i]
            if(mediaState == False):
                noteLetter = noteToNoteString(i)
                self.addMedia("", noteLetter)

    def addXmlMedia(self, xmlConfig):
        fileName = xmlConfig.get("filename")
        noteLetter = xmlConfig.get("note")
        print "Adding " + str(fileName) + " - " + str(noteLetter)
        return self.addMedia(fileName, noteLetter, xmlConfig)

    def addMedia(self, fileName, noteLetter, xmlConfig = None):
        midiNote = noteStringToNoteNumber(noteLetter)
        midiNote = min(max(midiNote, 0), 127)

        #remove old:
        if(self._mediaPool[midiNote] != None):
            if(self._configurationTree.removeChildUniqueId("MediaFile", "Note", noteLetter) == False):
                print "Config child NOT removed -!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!"
            else:
                print "Config child removed OK"

        if(len(fileName) <= 0):
            self._mediaPool[midiNote] = None
        else:
            print "DEBUG media added to pool pos: " + str(midiNote)
            self._mediaPool[midiNote] = MediaFile(self._configurationTree, fileName, noteLetter, midiNote, xmlConfig)
        return midiNote

    def getNoteConfig(self, noteId):
        noteId = min(max(noteId, 0), 127)
        print "DEBUG media requested from pos: " + str(noteId)
        return self._mediaPool[noteId]

class MediaFile(object):
    def __init__(self, configParent, fileName, noteLetter, midiNote, xmlConfig):
        mediaType = xmlConfig.get("type")
        if(mediaType != None):
            mediaType = "VideoLoop"
        self._configurationTree = configParent.addChildUniqueId("MediaFile", "Note", noteLetter, midiNote)
        self._configurationTree.addTextParameter("FileName", "")
        self._configurationTree.addTextParameter("Type", mediaType)
        self._configurationTree.addFloatParameter("SyncLength", 4.0) #Default one bar (re calculated on load)
        self._configurationTree.addFloatParameter("QuantizeLength", 4.0)#Default one bar
        self._configurationTree.addTextParameter("MixMode", "Add")#Default Add
        self._defaultEffect1SettingsName = "MediaDefault1"
        self._configurationTree.addTextParameter("Effect1Config", self._defaultEffect1SettingsName)#Default MediaDefault1
        self._defaultEffect2SettingsName = "MediaDefault2"
        self._configurationTree.addTextParameter("Effect2Config", self._defaultEffect2SettingsName)#Default MediaDefault2
        self._defaultFadeSettingsName = "Default"
        self._configurationTree.addTextParameter("FadeConfig", self._defaultFadeSettingsName)#Default Default
        if(mediaType == "VideoLoop"):
            self._configurationTree.addTextParameter("LoopMode", "Normal")
        elif(mediaType == "VideoLoop"):
            self._configurationTree.addTextParameter("SequenceMode", "Time")
            self._configurationTree.addTextParameter("PlayBackModulation", "None")
        self._configurationTree._updateFromXml(xmlConfig)

    def getFileName(self):
        return self._configurationTree.getValue("FileName")

