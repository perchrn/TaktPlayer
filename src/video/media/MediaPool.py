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

        self._emptyImage = getEmptyImage(self._internalResolutionX, self._internalResolutionY)

        self._defaultQuantize = midiTiming.getTicksPerQuarteNote() * 4

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
            print "mediaPool config is updated..."
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
        mediaPoolState = []
        for i in range(128):
            mediaPoolState.append(False)
        for xmlConfig in self._configurationTree.findXmlChildrenList("MediaFile"):
            midiNote = self.addXmlMedia(xmlConfig)
            mediaPoolState[midiNote] = True
        for i in range(128):
            mediaState = mediaPoolState[i]
            if(mediaState == False):
                noteLetter = MidiUtilities.noteToNoteString(i)
                self.addMedia("", noteLetter)

    def addXmlMedia(self, xmlConfig):
        fileName = xmlConfig.get("filename")
        noteLetter = xmlConfig.get("note")
        mediaType = xmlConfig.get("type")
        print "addXmlMedia: " + fileName + " note: " + noteLetter + " type: " + mediaType
        print "DEBUG xml: " + self._configurationTree.getConfigurationXMLString()
        return self.addMedia(fileName, noteLetter, None, mediaType)

    def addMedia(self, fileName, noteLetter, midiLength = None, mediaType = None):
        midiNote = MidiUtilities.noteStringToNoteNumber(noteLetter)

        oldMedia = self._mediaPool[midiNote]

        if(len(fileName) <= 0):
            if(oldMedia != None):
                print "Removing old media. " + noteLetter + " filename: " + oldMedia.getFileName()
                if(self._configurationTree.removeChildUniqueId("MediaFile", "Note", noteLetter) == False):
                    print "Config child NOT removed -!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!"
                else:
                    print "Config child removed OK"
                oldMedia.close()
            mediaFile = None
        else:
            if(mediaType == None):
                print "Non XML media add!!! !!! !!! !!! !!! !!! !!! ;-)"
                if(self._isFileNameAnImageName(fileName)):
                    mediaType = "Image"
                elif(self._isFileNameAnImageSequenceName(fileName)):
                    mediaType = "ImageSequence"
                else:
                    mediaType = "VideoLoop"
            keepOld = False
            if(oldMedia != None):
                if(oldMedia.equalFileName(fileName)):
                    if(oldMedia.getType() == mediaType):
                        keepOld= True
                        print "Keeping old media in this slot: " + str(midiNote) + " fileName: " + str(fileName)
                        if(midiLength != None):
                            oldMedia.setMidiLengthInBeats(midiLength)
                        oldMedia.checkAndUpdateFromConfiguration()
                        mediaFile = oldMedia
            if(keepOld == False):
                if(oldMedia != None):
                    print "Removing old media. " + noteLetter + " filename: " + oldMedia.getFileName()
                    if(self._configurationTree.removeChildUniqueId("MediaFile", "Note", noteLetter) == False):
                        print "Config child NOT removed -!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!"
                        print "DEBUG xml: " + self._configurationTree.getConfigurationXMLString()
                    else:
                        print "Config child removed OK"
                    oldMedia.close()
                if(mediaType == "Image"):
                    clipConf = self._configurationTree.addChildUniqueId("MediaFile", "Note", noteLetter, midiNote)
                    mediaFile = ImageFile(fileName, self._midiTiming, clipConf)
                    mediaFile.openFile(midiLength)
                elif(mediaType == "ImageSequence"):
                    clipConf = self._configurationTree.addChildUniqueId("MediaFile", "Note", noteLetter, midiNote)
                    mediaFile = ImageSequenceFile(fileName, self._midiTiming, clipConf)
                    mediaFile.openFile(midiLength)
                else:
                    clipConf = self._configurationTree.addChildUniqueId("MediaFile", "Note", noteLetter, midiNote)
                    mediaFile = VideoLoopFile(fileName, self._midiTiming, clipConf)
                    mediaFile.openFile(midiLength)

        self._mediaPool[midiNote] = mediaFile
        return midiNote
        
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


