'''
Created on 21. des. 2011

@author: pcn
'''
import logging

from video.media.MediaFile import VideoLoopFile, ImageFile, ImageSequenceFile,\
    CameraInput, MediaError, KinectCameraInput, ScrollImageFile, SpriteImageFile,\
    MediaGroup, TextMedia, ModulationMedia
from midi import MidiUtilities
from video.Effects import getEmptyImage
from video.media.MediaFileModes import forceUnixPath
from midi.MidiStateHolder import GenericModulationHolder

class MediaPool(object):
    def __init__(self, midiTiming, midiStateHolder, specialModulationHolder, mediaMixer, timeModulationConfiguration, effectsConfiguration, effectImagesConfiguration, fadeConfiguration, configurationTree, internalResolutionX, internalResolutionY, videoDir):
        self._configurationTree = configurationTree
        self._timeModulationConfiguration = timeModulationConfiguration
        self._effectsConfigurationTemplates = effectsConfiguration
        self._effectImagesConfigurationTemplates = effectImagesConfiguration
        self._mediaFadeConfigurationTemplates = fadeConfiguration
        #Logging etc.
        self._log = logging.getLogger('%s.%s' % (__name__, self.__class__.__name__))

        self._internalResolutionX =  internalResolutionX
        self._internalResolutionY =  internalResolutionY
        self._videoDirectory = videoDir

        self._emptyImage = getEmptyImage(self._internalResolutionX, self._internalResolutionY)

        self._defaultQuantize = midiTiming.getTicksPerQuarteNote() * 1

        self._midiTiming = midiTiming
        self._midiStateHolder = midiStateHolder
        self._specialModulationHolder = specialModulationHolder
        self._noteModulation = GenericModulationHolder("Note", self._specialModulationHolder)
        self._effectsModulation = GenericModulationHolder("Effect", self._specialModulationHolder)
        self._mediaMixer = mediaMixer
        self._mediaMixer.gueueImage(self._emptyImage, None, 1)
        self._mediaPool = []
        for i in range(128): #@UnusedVariable
            self._mediaPool.append(None)
        self._mediaTracks = []
        self._mediaTrackIds = []
        self._mediaTrackStateHolders = []
        self._modulationMediaList = []
        for i in range(16): #@UnusedVariable
            self._mediaTracks.append(None)
            self._mediaTrackIds.append(-1)
            self._mediaTrackStateHolders.append(None)
        self.loadMediaFromConfiguration()

    def _getConfiguration(self):
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
        xmlChildren = self._configurationTree.findXmlChildrenList("MediaFile")
        if(xmlChildren != None):
            for xmlConfig in xmlChildren:
                midiNote = self.addXmlMedia(xmlConfig)
                mediaPoolState[midiNote] = True
        for i in range(128):
            mediaState = mediaPoolState[i]
            if(mediaState == False):
                noteLetter = MidiUtilities.noteToNoteString(i)
                self.addMedia("", noteLetter)
        self._effectsConfigurationTemplates.setupEffectModulations(self._effectsModulation)
        self.setupSpecialNoteModulations()
        self.mediaPostConfigurations()
        self._mediaMixer.doPostConfigurations()

    def setupSpecialNoteModulations(self):
        for note in self._mediaPool:
#            if(note == None):
#                print "n",
#            else:
#                print note.getType(),
            if((note != None) and (note.getType() == "Modulation")):
                noteName = note.getFileName()
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

    def addXmlMedia(self, xmlConfig):
        fileName = xmlConfig.get("filename")
        noteLetter = xmlConfig.get("note")
        mediaType = xmlConfig.get("type")
        if(mediaType != "Text"):
            fileName = forceUnixPath(fileName)
            xmlConfig.set("filename", fileName)
        return self.addMedia(fileName, noteLetter, None, mediaType)

    def addMedia(self, fileName, noteLetter, midiLength = None, mediaType = None):
        midiNote = MidiUtilities.noteStringToNoteNumber(noteLetter)
        midiNote = min(max(midiNote, 0), 127)

        oldMedia = self._mediaPool[midiNote]
        guiCtrlStateHolder = self._midiStateHolder.getGuiNoteControllerStareHolder(midiNote)

        if(len(fileName) <= 0):
            if(oldMedia != None):
                print "New file is empty: Removing old media. " + noteLetter + " filename: " + str(oldMedia.getFileName().encode("utf-8"))
                if(self._configurationTree.removeChildUniqueId("MediaFile", "Note", noteLetter) == False):
                    print "Config child NOT removed -!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!"
                else:
                    print "Config child removed OK"
                oldMedia.close()
            mediaFile = None
        else:
            if(mediaType == None):
                if(self._isFileNameAnImageName(fileName)):
                    mediaType = "Image"
                elif(self._isFileNameAnImageSequenceName(fileName)):
                    mediaType = "ImageSequence"
                else:
                    mediaType = "VideoLoop"
            keepOld = False
            if(oldMedia != None):
                if(oldMedia.equalFileName(fileName)):
                    print "FileName OK"
                    if((oldMedia.getType() == mediaType)):
                        print "MediaType OK"
                        keepOld= True
                        print "Keeping old media in this slot: " + str(midiNote) + " fileName: " + str(fileName.encode("utf-8"))
                        if(midiLength != None):
                            oldMedia.setMidiLengthInBeats(midiLength)
                        oldMedia.checkAndUpdateFromConfiguration()
                        mediaFile = oldMedia
            if(keepOld == False):
                if(oldMedia != None):
                    print "Removing old media. " + noteLetter + " filename: " + str(oldMedia.getFileName().encode("utf-8"))
                    if(self._configurationTree.removeChildUniqueId("MediaFile", "Note", noteLetter) == False):
                        print "Config child NOT removed -!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!-!"
                    else:
                        print "Config child removed OK"
                    oldMedia.close()
                    if((oldMedia.getType() == "Modulation")):
                        try:
                            self._modulationMediaList.remove(oldMedia)
                        except:
                            pass
                try:
                    if(mediaType == "Image"):
                        clipConf = self._configurationTree.addChildUniqueId("MediaFile", "Note", noteLetter, midiNote)
                        mediaFile = ImageFile(fileName, self._midiTiming,  self._timeModulationConfiguration, self._specialModulationHolder, self._effectsConfigurationTemplates, self._effectImagesConfigurationTemplates, guiCtrlStateHolder, self._mediaFadeConfigurationTemplates, clipConf, self._internalResolutionX, self._internalResolutionY, self._videoDirectory)
                        mediaFile.openFile(midiLength)
                    elif(mediaType == "ImageSequence"):
                        clipConf = self._configurationTree.addChildUniqueId("MediaFile", "Note", noteLetter, midiNote)
                        mediaFile = ImageSequenceFile(fileName, self._midiTiming,  self._timeModulationConfiguration, self._specialModulationHolder, self._effectsConfigurationTemplates, self._effectImagesConfigurationTemplates, guiCtrlStateHolder, self._mediaFadeConfigurationTemplates, clipConf, self._internalResolutionX, self._internalResolutionY, self._videoDirectory)
                        mediaFile.openFile(midiLength)
                    elif(mediaType == "ScrollImage"):
                        clipConf = self._configurationTree.addChildUniqueId("MediaFile", "Note", noteLetter, midiNote)
                        mediaFile = ScrollImageFile(fileName, self._midiTiming,  self._timeModulationConfiguration, self._specialModulationHolder, self._effectsConfigurationTemplates, self._effectImagesConfigurationTemplates, guiCtrlStateHolder, self._mediaFadeConfigurationTemplates, clipConf, self._internalResolutionX, self._internalResolutionY, self._videoDirectory)
                        mediaFile.openFile(midiLength)
                    elif(mediaType == "Sprite"):
                        clipConf = self._configurationTree.addChildUniqueId("MediaFile", "Note", noteLetter, midiNote)
                        mediaFile = SpriteImageFile(fileName, self._midiTiming,  self._timeModulationConfiguration, self._specialModulationHolder, self._effectsConfigurationTemplates, self._effectImagesConfigurationTemplates, guiCtrlStateHolder, self._mediaFadeConfigurationTemplates, clipConf, self._internalResolutionX, self._internalResolutionY, self._videoDirectory)
                        mediaFile.openFile(midiLength)
                    elif(mediaType == "Text"):
                        clipConf = self._configurationTree.addChildUniqueId("MediaFile", "Note", noteLetter, midiNote)
                        mediaFile = TextMedia(fileName, self._midiTiming,  self._timeModulationConfiguration, self._specialModulationHolder, self._effectsConfigurationTemplates, self._effectImagesConfigurationTemplates, guiCtrlStateHolder, self._mediaFadeConfigurationTemplates, clipConf, self._internalResolutionX, self._internalResolutionY, self._videoDirectory)
                        mediaFile.openFile(midiLength)
                    elif(mediaType == "Camera"):
                        clipConf = self._configurationTree.addChildUniqueId("MediaFile", "Note", noteLetter, midiNote)
                        mediaFile = CameraInput(fileName, self._midiTiming,  self._timeModulationConfiguration, self._specialModulationHolder, self._effectsConfigurationTemplates, self._effectImagesConfigurationTemplates, guiCtrlStateHolder, self._mediaFadeConfigurationTemplates, clipConf, self._internalResolutionX, self._internalResolutionY, self._videoDirectory)
                        mediaFile.openFile(midiLength)
                    elif(mediaType == "KinectCamera"):
                        clipConf = self._configurationTree.addChildUniqueId("MediaFile", "Note", noteLetter, midiNote)
                        mediaFile = KinectCameraInput(fileName, self._midiTiming,  self._timeModulationConfiguration, self._specialModulationHolder, self._effectsConfigurationTemplates, self._effectImagesConfigurationTemplates, guiCtrlStateHolder, self._mediaFadeConfigurationTemplates, clipConf, self._internalResolutionX, self._internalResolutionY, self._videoDirectory)
                        mediaFile.openFile(midiLength)
                    elif(mediaType == "Group"):
                        clipConf = self._configurationTree.addChildUniqueId("MediaFile", "Note", noteLetter, midiNote)
                        mediaFile = MediaGroup(fileName, self._midiTiming,  self._timeModulationConfiguration, self._specialModulationHolder, self._effectsConfigurationTemplates, self._effectImagesConfigurationTemplates, guiCtrlStateHolder, self._mediaFadeConfigurationTemplates, clipConf, self._internalResolutionX, self._internalResolutionY, self._videoDirectory)
                        mediaFile.setGetMediaCallback(self.getMedia)
                        mediaFile.openFile(midiLength)
                    elif(mediaType == "Modulation"):
                        clipConf = self._configurationTree.addChildUniqueId("MediaFile", "Note", noteLetter, midiNote)
                        mediaFile = ModulationMedia(fileName, self._midiTiming,  self._timeModulationConfiguration, self._specialModulationHolder, self._effectsConfigurationTemplates, self._effectImagesConfigurationTemplates, guiCtrlStateHolder, self._mediaFadeConfigurationTemplates, clipConf, self._internalResolutionX, self._internalResolutionY, self._videoDirectory)
                        mediaFile.openFile(midiLength)
                        self._modulationMediaList.append(mediaFile)
                    else:
                        clipConf = self._configurationTree.addChildUniqueId("MediaFile", "Note", noteLetter, midiNote)
                        mediaFile = VideoLoopFile(fileName, self._midiTiming,  self._timeModulationConfiguration, self._specialModulationHolder, self._effectsConfigurationTemplates, self._effectImagesConfigurationTemplates, guiCtrlStateHolder, self._mediaFadeConfigurationTemplates, clipConf, self._internalResolutionX, self._internalResolutionY, self._videoDirectory)
                        mediaFile.openFile(midiLength)
                except MediaError, mediaError:
                    print "Error opening media file: %s Message: %s" % (fileName.encode("utf-8"), str(mediaError))
                    mediaFile = None

        self._mediaPool[midiNote] = mediaFile
        return midiNote

    def mediaPostConfigurations(self):
        for media in self._mediaPool:
            if(media != None):
#                print "DEBUG pcn: mediaPostConfigurations() mediaType: " + str(media.getType()) + " name: " + str(media.getFileName())
                media.doPostConfigurations()

    def getMedia(self, noteId):
        if((noteId >= 0) and (noteId < 128)):
            return self._mediaPool[noteId]
        else:
            return None

    def requestNoteList(self):
        noteListString = ""
        for i in range(128):
            media = self._mediaPool[i]
            if(media != None):
                if(noteListString != ""):
                    noteListString += ","
                noteListString += str(i)
        return noteListString

    def requestTrackState(self, timeStamp):
        noteListString = ""
        for i in range(16):
            noteId = self._mediaTrackIds[i]
            if(noteListString != ""):
                noteListString += ","
            noteListString += str(noteId)
        return noteListString

    def requestEffectState(self, midiChannel, midiNote):
        if(midiChannel != None):
            if(midiChannel < 0 or midiChannel >= 16):
                print "Channel effect state request: Bad channel: " + str(midiChannel)
            else:
#                print "Channel effect state request!"
                return self._mediaMixer.getEffectState(midiChannel)
        else:
            if(midiNote != None):
                if(midiNote < 0 or midiNote >= 128):
                    print "Note effect state request: Bad note: " + str(midiNote)
                else:
#                    print "Note effect state request!"
                    midiNoteObject = self._mediaPool[midiNote]
                    if(midiNoteObject != None):
                        return midiNoteObject.getEffectState()
            else:
                print "Error: Empty request!"
        return None, None

    def requestVideoThumbnail(self, noteId, videoPosition, forceUpdate):
        noteMedia = self._mediaPool[noteId]
        if(noteMedia != None):
            return noteMedia.getThumbnailId(videoPosition, forceUpdate)
        else:
            return None

    def updateVideo(self, timeStamp):
        midiSync, midiTime = self._midiTiming.getSongPosition(timeStamp) #@UnusedVariable
#        print "DEBUG pcn: Updating modulation medias.........................................."
        for modulationMedia in self._modulationMediaList:
            modulationMedia.updateModulationValues(None, midiTime)
#        print "DEBUG pcn: Updating modulation medias..................................... done"
        for midiChannel in range(16):
            activeMedia = None
            noteMediaIsModulationType = False
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
                newNoteId = midiNoteState.getNote()
                newMedia = self._mediaPool[newNoteId]
                if(midiNoteState.isNew() == True):
                    if(newMedia != None):
                        midiNoteState.setNewState(False)
                oldMedia = self._mediaTracks[midiChannel]
                oldMediaState = self._mediaTrackStateHolders[midiChannel]
                if((newMedia != None) and (newMedia.getType() == "Modulation")):
                    newMedia.setStartPosition(midiNoteState.getStartPosition(), None, midiTime, midiNoteState, midiChannelState)
                    newMedia = oldMedia
                    noteMediaIsModulationType = True
                activeMediaState = None
                if(oldMedia == None):
                    self._mediaTracks[midiChannel] = newMedia
                    if(newMedia != None):
                        activeMediaState = newMedia.getMediaStateHolder()
                        self._mediaTrackIds[midiChannel] = newNoteId
                    else:
                        self._mediaTrackIds[midiChannel] = -1
                    self._mediaTrackStateHolders[midiChannel] = activeMediaState
                elif(oldMedia != newMedia):
                    oldMedia.releaseMedia(oldMediaState)
                    self._mediaTracks[midiChannel] = newMedia
                    if(newMedia != None):
                        activeMediaState = newMedia.getMediaStateHolder()
                        self._mediaTrackIds[midiChannel] = newNoteId
                    else:
                        self._mediaTrackIds[midiChannel] = -1
                    self._mediaTrackStateHolders[midiChannel] = activeMediaState
                else:
                    activeMediaState = oldMediaState
                if(newMedia != None):
                    activeMedia = newMedia
                    if(noteMediaIsModulationType == False):
                        newMedia.setStartPosition(midiNoteState.getStartPosition(), activeMediaState, midiTime, midiNoteState, midiChannelState)
                else:
                    self._mediaTrackStateHolders[midiChannel] = None
            if(activeMedia != None):
                activeMediaState = self._mediaTrackStateHolders[midiChannel]
                noteIsDone = activeMedia.skipFrames(activeMediaState, midiTime, midiNoteState, midiChannelState)
                if(noteIsDone == True):
                    midiChannelState.removeDoneActiveNote()
                self._mediaMixer.gueueImage(activeMedia, activeMediaState, midiChannel)
            else:
                self._mediaMixer.gueueImage(None, None, midiChannel)
                if(self._mediaTracks[midiChannel] != None):
                    self._mediaTracks[midiChannel].releaseMedia(self._mediaTrackStateHolders[midiChannel])
                self._mediaTracks[midiChannel] = None
                self._mediaTrackStateHolders[midiChannel] = None
                self._mediaTrackIds[midiChannel] = -1
        #TODO: Make sure we only use the same VideoLoopFile instance once.
        self._mediaMixer.mixImages(midiTime)


