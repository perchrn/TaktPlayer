'''
Created on 21. des. 2011

@author: pcn
'''
import logging

from video.media.MediaFile import VideoLoopFile, ImageFile, ImageSequenceFile, getEmptyImage
from midi import MidiUtilities

class MediaPool(object):
    def __init__(self, midiTiming, midiStateHolder, mediaMixer, multiprocessLogger, windowSize):
        #Logging etc.
        self._log = logging.getLogger('%s.%s' % (__name__, self.__class__.__name__))
        self._multiprocessLogger = multiprocessLogger

        self._currentWindowSize = windowSize

        self._emptyImage = getEmptyImage(self._currentWindowSize[0], self._currentWindowSize[1])

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

    def addMedia(self, fileName, noteLetter, midiLength):
        midiNote = MidiUtilities.noteStringToNoteNumber(noteLetter)
        self._log.info("Adding media \"%s\" to note number %d with length %f" %(fileName, midiNote, midiLength))

        if(len(fileName) <= 0):
            mediaFile = None
        elif(self._isFileNameAnImageName(fileName)):
            mediaFile = ImageFile(fileName, self._midiTiming, self._currentWindowSize)
            mediaFile.openFile(midiLength)
        elif(self._isFileNameAnImageSequenceName(fileName)):
            mediaFile = ImageSequenceFile(fileName, self._midiTiming, self._currentWindowSize)
            mediaFile.openFile(midiLength)
        else:
            mediaFile = VideoLoopFile(fileName, self._midiTiming, self._currentWindowSize)
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


