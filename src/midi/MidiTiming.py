'''
Created on 21. des. 2011

@author: pcn
'''
import time
import logging

class MidiTiming(object):
    def __init__(self):
        #Logging etc.
        self._log = logging.getLogger('%s.%s' % (__name__, self.__class__.__name__))
        #MIDI timing variables:
        self._midiOurSongPosition = 0;
        self._midiLastTimeEventWasSPP = False
#        self._midiTimeing = (4,4);
        self._midiTicksPerQuarteNote = 24
        self._midiTicksPerBar = self._midiTicksPerQuarteNote * 4
        self._midiTicksTimestamps = [-1.0, -1.0, -1.0, -1.0, -1.0, -1.0, -1.0, -1.0, -1.0, -1.0, -1.0, -1.0, -1.0, -1.0, -1.0, -1.0,
                                     -1.0, -1.0, -1.0, -1.0, -1.0, -1.0, -1.0, -1.0, -1.0, -1.0, -1.0, -1.0, -1.0, -1.0, -1.0, -1.0,
                                     -1.0, -1.0, -1.0, -1.0, -1.0, -1.0, -1.0, -1.0, -1.0, -1.0, -1.0, -1.0, -1.0, -1.0, -1.0, -1.0,
                                     -1.0, -1.0, -1.0, -1.0, -1.0, -1.0, -1.0, -1.0, -1.0, -1.0, -1.0, -1.0, -1.0, -1.0, -1.0, -1.0,
                                     -1.0, -1.0, -1.0, -1.0, -1.0, -1.0, -1.0, -1.0, -1.0, -1.0, -1.0, -1.0, -1.0, -1.0, -1.0, -1.0,
                                     -1.0, -1.0, -1.0, -1.0, -1.0, -1.0, -1.0, -1.0, -1.0, -1.0, -1.0, -1.0, -1.0, -1.0, -1.0, -1.0]
        self._midiTicksTimestampsPos = -1
        self._midiTicksTimestampsLength = 96
        self._midiInitTime = time.time()
        self._midiBpm = 120.0
        self._midiMaxSyncBarsMissed = 16 * self._midiTicksPerQuarteNote

    def getTicksPerQuarteNote(self):
        return self._midiTicksPerQuarteNote

    def _calculateSubSubPos(self, timeStamp):
        midiSync = True
        subsubPos = 0.0
        if(self._midiTicksTimestampsPos > -1):
            lastTimestamp = self._midiTicksTimestamps[self._midiTicksTimestampsPos]
            deltaTime = timeStamp - lastTimestamp
            subsubPos = (self._midiTicksPerQuarteNote * deltaTime * self._midiBpm) / 60
#            print "TimeStamp: " + str(timeStamp) + "Delta: " + str(deltaTime) + " SubSubPos: " + str(subsubPos)
            if(subsubPos > self._midiTicksPerBar * self._midiMaxSyncBarsMissed):
                midiSync = False;
        else:
            midiSync = False;
            deltaTime = timeStamp - self._midiInitTime
            subsubPos = (self._midiTicksPerQuarteNote * deltaTime * self._midiBpm) / 60
        return (midiSync, subsubPos)

    def getSongPosition(self, timeStamp):
        midiSync, subsubPos = self._calculateSubSubPos(timeStamp)
        ourSongPosition = self._midiOurSongPosition + subsubPos
        return (midiSync, ourSongPosition)

    def convertToMidiPosition(self, midiSync, ourSongPosition):
        bar = int(ourSongPosition / self._midiTicksPerBar) + 1
        beat = int((ourSongPosition % self._midiTicksPerBar) / self._midiTicksPerQuarteNote) + 1
        subbeat = int(ourSongPosition % self._midiTicksPerQuarteNote) + 1
        subBeatFraction = ourSongPosition % 1.0
        return (midiSync, bar, beat, subbeat, subBeatFraction)
        
    def getMidiPosition(self, timeStamp):
        midiSync, ourSongPosition = self.getSongPosition(timeStamp)
        return self.convertToMidiPosition(midiSync, ourSongPosition)
        
    def printMidiPosition(self):
        currentTimestamp = time.time()
        midiSync, bar, beat, subbeat, subsubpos = self.getMidiPosition(currentTimestamp)
        if(midiSync):
            syncIndicator = "S "
        else:
            syncIndicator = ""
        print "%s%3d:%d:%02d.%04d BPM: %d" % (syncIndicator, bar, beat, subbeat, int(subsubpos * 10000), int(self._midiBpm))
#        print syncIndicator + str(bar) + ":" + str(beat) + ":" + str(subbeat) + ":" + str(subsubpos) + " BPM: " + str(int(self._midiBpm)) + " SPP: " + str(self._midiOurSongPosition)
        
    def _resetTimingTable(self):
        self._log.warning("Resetting timing table!")
        for i in range(96):
            self._midiTicksTimestamps[i] = -1.0
        self._midiTicksTimestampsPos = -1
        self._midiInitTime = time.time()

    def _updateSongPostiton(self, dataTimeStamp, data1 = None, data2 = None):
        if(data1 == None):
            midiSync, subsubPos = self._calculateSubSubPos(dataTimeStamp)
            if(midiSync == False and self._midiTicksTimestampsPos != -1):
                #We have missed MIDI sync and can't use our timing table anymore.
                self._resetTimingTable()
            if(self._midiLastTimeEventWasSPP == True):
                #Don't increase or calculate new position when we just got a SPP from MIDI host
                self._midiLastTimeEventWasSPP = False
            else:
                if(subsubPos > 10.0):
                    #We have skipped MIDI ticks and add calculated ticks.
                    self._log.info("Adding internal time to Song Position Pointer due to lost MIDI sync. " + str(subsubPos))
                    self._midiOurSongPosition += int(subsubPos)
                else:
                    self._midiOurSongPosition += 1
            self._midiTicksTimestampsPos = (self._midiTicksTimestampsPos + 1) % self._midiTicksTimestampsLength
            startPosTimeStamp = self._midiTicksTimestamps[self._midiTicksTimestampsPos]
            self._midiTicksTimestamps[self._midiTicksTimestampsPos] = dataTimeStamp
            if(startPosTimeStamp < 0):
                firstTimeStamp = self._midiTicksTimestamps[0]
                if(dataTimeStamp - firstTimeStamp > 0):
                    self._midiBpm = 60 * self._midiTicksTimestampsPos / (self._midiTicksPerQuarteNote * (dataTimeStamp - firstTimeStamp))
            else:
                self._midiBpm = 60 * self._midiTicksTimestampsLength / (self._midiTicksPerQuarteNote * (dataTimeStamp - startPosTimeStamp))
        else:
            sppValue = int(data1)+(int(data2 << 7))
            self._midiOurSongPosition = sppValue
            self._midiLastTimeEventWasSPP = True
            self._log.info("Got Song Position Pointer from host. SPP %d" %(self._midiOurSongPosition))
#        if((self._midiOurSongPosition % self._midiTicksPerQuarteNote) == 0):
#            self.printMidiPosition()

    def guessMidiLength(self, originalLength):
        barLength = 240 / self._midiBpm # 240 = 60sec * 4beats
        bars = originalLength / barLength
        #Use editor for more detailed timing options
        if(bars > 0.875):
            bars = int(bars + 0.5)
            return self._midiTicksPerBar * bars
        elif(bars > .625):
            return 3 * self._midiTicksPerQuarteNote
        elif(bars > .375):
            return 2 * self._midiTicksPerQuarteNote
        else:
            return self._midiTicksPerQuarteNote
            