'''
Created on 21. des. 2011

@author: pcn
'''
import logging

from video.media.MediaFile import MediaFile, getEmptyImage
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

    def addMedia(self, fileName, noteLetter, midiLength):
        midiNote = MidiUtilities.noteStringToNoteNumber(noteLetter)
        self._log.info("Adding media \"%s\" to note number %d with length %f" %(fileName, midiNote, midiLength))

        if(len(fileName) > 0):
            mediaFile = MediaFile(fileName, self._midiTiming, self._currentWindowSize)
            mediaFile.openFile()
            mediaFile.setMidiLengthInBeats(midiLength)
        else:
            mediaFile = None

        print "Adding NOTE: " + str(midiNote)
        self._mediaPool[midiNote] = mediaFile

    def updateVideo(self, timeStamp):
        midiSync, midiTime = self._midiTiming.getSongPosition(timeStamp) #@UnusedVariable
        for midiChannel in range(16):
            activeMedia = None
            quantizeValue = self._defaultQuantize
            note = self._midiStateHolder.checkForWaitingNote(midiChannel)
            if(note > -1):
                noteMedia = self._mediaPool[note]
                if(noteMedia != None):
                    quantizeValue = noteMedia.getQuantize()
                self._midiStateHolder.quantizeWaitingNote(midiChannel, note, quantizeValue)
            newNote = self._midiStateHolder.getActiveNote(midiChannel, midiTime)
            if(newNote.isActive(midiTime)):
                newMedia = self._mediaPool[newNote.getNote()]
                if(newMedia):
                    newMedia.setStartPosition(newNote.getStartPosition())
                    activeMedia = newMedia
            if(activeMedia != None):
                activeMedia.skipFrames(midiTime)
                self._mediaMixer.gueueImage(activeMedia, midiChannel)
            else:
                self._mediaMixer.gueueImage(None, midiChannel)
        #TODO: Make sure we only use the same MediaFile instance once.
        self._mediaMixer.mixImages()


