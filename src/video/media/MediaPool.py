'''
Created on 21. des. 2011

@author: pcn
'''
import logging

from video.media.MediaFile import VideoLoopFile, ImageFile, ImageSequenceFile, getEmptyImage
from midi import MidiUtilities

class MediaPool(object):
    def __init__(self, midiTiming, midiStateHolder, mediaMixer, configurationTree, multiprocessLogger):
        self._configurationTree = configurationTree
        #Logging etc.
        self._log = logging.getLogger('%s.%s' % (__name__, self.__class__.__name__))
        self._multiprocessLogger = multiprocessLogger

        self._internalResolutionX =  self._configurationTree.getValueFromPath("Global.ResolutionX")
        self._internalResolutionY =  self._configurationTree.getValueFromPath("Global.ResolutionY")

        print "DEBUG: " + str(type(self._internalResolutionX)) + " : " + str(self._internalResolutionX)
        self._emptyImage = getEmptyImage(self._internalResolutionX, self._internalResolutionY)


        self._defaultQuantize = 24 * 4

        self._midiTiming = midiTiming
        self._midiStateHolder = midiStateHolder
        self._mediaMixer = mediaMixer
        self._mediaMixer.gueueImage(self._emptyImage, 1)
        self._mediaPool = []
        for i in range(128): #@UnusedVariable
            self._mediaPool.append(None)
        self._mediaTracks = []
        for i in range(16): #@UnusedVariable
            self._mediaTracks.append(None)
        self.loadMediaFromConfiguration()

    def _getConfiguration(self):
        #TODO load new, free old and update existing media files
        self.loadMediaFromConfiguration()

    def checkAndUpdateFromConfiguration(self):
        if(self._configurationTree.isConfigurationUpdated()):
            self._getConfiguration()
            for mediaFile in self._mediaPool:
                if(mediaFile != None):
                    mediaFile.checkAndUpdateFromConfiguration()
            self._configurationTree.resetConfigurationUpdated()

    def _isFileNameAnImageName(self, filename):
        if(filename.endswith(".png")):
            return True
        if(filename.endswith(".jpg")):
            return True
        return False

    def _isFileNameAnImageSequenceName(self, filename):
        if(filename.endswith("_sequence.avi")):
            return True
        return False

    def loadMediaFromConfiguration(self):
        for xmlConfig in self._configurationTree.findXmlChildrenList("MediaFile"):
            self.addXmlMedia(xmlConfig)

    def addXmlMedia(self, xmlConfig):
#        fileName = self._configurationTree.getValueFromXml(xmlConfig, "FileName")
#        noteLetter = self._configurationTree.getValueFromXml(xmlConfig, "Note")
#        midiLength = self._configurationTree.getValueFromXml(xmlConfig, "SyncLengt")
        fileName = xmlConfig.get("filename")
        noteLetter = xmlConfig.get("note")
        print "Debug: " + str(noteLetter) + " " + str(fileName)
        self.addMedia(fileName, noteLetter, None)

    def addMedia(self, fileName, noteLetter, midiLength = None):
        midiNote = MidiUtilities.noteStringToNoteNumber(noteLetter)

        if(len(fileName) <= 0):
            mediaFile = None
        elif(self._isFileNameAnImageName(fileName)):
            clipConf = self._configurationTree.addChildUniqueId("MediaFile", "Note", noteLetter, midiNote)
            mediaFile = ImageFile(fileName, self._midiTiming, clipConf)
            mediaFile.openFile(midiLength)
        elif(self._isFileNameAnImageSequenceName(fileName)):
            clipConf = self._configurationTree.addChildUniqueId("MediaFile", "Note", noteLetter, midiNote)
            mediaFile = ImageSequenceFile(fileName, self._midiTiming, clipConf)
            mediaFile.openFile(midiLength)
        else:
            clipConf = self._configurationTree.addChildUniqueId("MediaFile", "Note", noteLetter, midiNote)
            mediaFile = VideoLoopFile(fileName, self._midiTiming, clipConf)
            mediaFile.openFile(midiLength)

        print "Adding NOTE: " + str(midiNote)
        self._mediaPool[midiNote] = mediaFile
        
    def updateVideo(self, timeStamp):
        midiSync, midiTime = self._midiTiming.getSongPosition(timeStamp) #@UnusedVariable
        for midiChannel in range(16):
            activeMedia = None
            quantizeValue = self._defaultQuantize
            midiChannelState = self._midiStateHolder.getMidiChannelState(midiChannel)
            note = midiChannelState.checkIfNextNoteIsQuantized()
            if(note > -1):
                noteMedia = self._mediaPool[note]
                if(noteMedia != None):
                    quantizeValue = noteMedia.getQuantize()
                midiChannelState.quantizeWaitingNote(note, quantizeValue)
            midiNoteState = midiChannelState.getActiveNote(midiTime)
            if(midiNoteState.isActive(midiTime)):
                newMedia = self._mediaPool[midiNoteState.getNote()]
                oldMedia = self._mediaTracks[midiChannel]
                if(oldMedia == None):
                    self._mediaTracks[midiChannel] = newMedia
                elif(oldMedia != newMedia):
                    oldMedia.restartSequence()
                    self._mediaTracks[midiChannel] = newMedia
                if(newMedia):
                    newMedia.setStartPosition(midiNoteState.getStartPosition())
                    activeMedia = newMedia
            if(activeMedia != None):
                activeMedia.skipFrames(midiTime, midiNoteState, midiChannelState)
                self._mediaMixer.gueueImage(activeMedia, midiChannel)
            else:
                self._mediaMixer.gueueImage(None, midiChannel)
        #TODO: Make sure we only use the same VideoLoopFile instance once.
        self._mediaMixer.mixImages()


