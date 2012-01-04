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
            mediaFile.setMidiLength(midiLength)
        else:
            mediaFile = None

        print "Adding NOTE: " + str(midiNote)
        self._mediaPool[midiNote] = mediaFile

    def updateVideo(self, timeStamp):
        midiSync, midiTime = self._midiTiming.getSongPosition(timeStamp) #@UnusedVariable
        mediaFile = self._mediaPool[36]
        mediaFile.skipFrames(midiTime)
        self._mediaMixer.gueueImage(mediaFile.getImage(), 1)
        pass


