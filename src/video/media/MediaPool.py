'''
Created on 21. des. 2011

@author: pcn
'''
import logging
import time

from video.media.MediaFile import MediaFile, getEmptyImage
from midi import MidiUtilities

class MediaPool(object):
    def __init__(self, midiTiming, mediaMixer, multiprocessLogger):
        #Logging etc.
        self._log = logging.getLogger('%s.%s' % (__name__, self.__class__.__name__))
        self._multiprocessLogger = multiprocessLogger

        self._emptyImage = getEmptyImage(800, 600)

        self._midiTiming = midiTiming
        self._mediaMixer = mediaMixer
#        self._mediaMixer.gueueImage(self._emptyImage, 1)
        self._mediaPool = []
        for i in range(128): #@UnusedVariable
            self._mediaPool.append(None)

    def addMedia(self, fileName, noteLetter, midiLength):
        midiNote = MidiUtilities.noteStringToNoteNumber(noteLetter)
        self._log.info("Adding media \"%s\" to note number %d with length %f" %(fileName, midiNote, midiLength))

        if(len(fileName) > 0):
            mediaFile = MediaFile(fileName, self._midiTiming)
            mediaFile.openFile()
            mediaFile.setMidiLength(midiLength)
        else:
            mediaFile = None

        self._mediaPool[midiNote] = mediaFile

    def updateVideo(self, timeStamp):
        midiSync, midiTime = self._midiTiming.getSongPosition(timeStamp) #@UnusedVariable
        pass


