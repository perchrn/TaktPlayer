'''
Created on 20. des. 2011

@author: pcn
'''
from midi import MidiUtilities

class NoteState(object):
    def __init__(self):
        self._noteOn = False
        self._note = -1
        self._octav = -1
        self._noteLetter = ' '
        self._velocity = -1
        self._noteOnSPP = -1.0
        self._noteOffSPP = -1.0
        self._noteOnQuantizedSPP = -1
        self._noteOffQuantizedSPP = -1
        self._noteOnInSync = False
        self._noteOffInSync = False
        self._quantizeValue = 0

    def getNote(self):
        return self._note

    def getVelocity(self):
        return self._velocity

    def getStartPosition(self):
        return self._noteOnQuantizedSPP

    def getStopPosition(self):
        return self._noteOffQuantizedSPP

    def isActive(self, spp):
        if(self._note == -1):
            return False
        if(self._noteOnQuantizedSPP == -1):
            return False
        if(self._noteOnQuantizedSPP < spp):
            return True
        else:
            return False

    def isUnquantized(self):
        if(self._note == -1):
            return False
        if(self._noteOnQuantizedSPP == -1):
            return True

    def isOn(self, note):
        if(note != -1):
            if(self._note == note):
                return  True
        return False

    def printState(self, midiChannel):
        if(self._note > -1):
            if(self._noteOn):
                print "State: Note on: " + self._noteLetter + str(self._octav) + " vel: " + str(self._velocity) + " channel: " + str(midiChannel) + " OnSPP: " + str(self._noteOnSPP) + " OffSPP: " + str(self._noteOffSPP)
            else:
                print "State: Note off: " + self._noteLetter + str(self._octav) + " vel: " + str(self._velocity) + " channel: " + str(midiChannel) + " OnSPP: " + str(self._noteOnSPP) + " OffSPP: " + str(self._noteOffSPP)

    def noteOn(self, note, velocity, songPosition, spp, midiSync):
        self._noteOn = True
        self._noteOnSPP = spp
        self._noteOnInSync = midiSync
        self._note = note
        (octav, noteLetter) = MidiUtilities.noteToOctavAndLetter(note)
        self._octav = octav
        self._noteLetter = noteLetter
        self._velocity = velocity

    def noteOff(self, note, velocity, songPosition, spp, midiSync):
        self._noteOn = False
        self._noteOffSPP = spp
        self._noteOffInSync = midiSync
        self._noteOffQuantizedSPP = self._quantize(spp, self._quantizeValue)
        self._note = note
        (octav, noteLetter) = MidiUtilities.noteToOctavAndLetter(note)
        self._octav = octav
        self._noteLetter = noteLetter
        self._velocity = velocity

    def _quantize(self, spp, quantizeValue):
        if(quantizeValue < 1):
            return spp
        else:
            intSPP = int(spp)
            rest = intSPP % quantizeValue
            quantizedSPP = int(intSPP / quantizeValue) * quantizeValue
            factor = float(rest) / quantizeValue
            if(factor > 0.15):
                quantizedSPP += quantizeValue
            print "Quantizing Note: " + str(self._note) + " SPP: " + str(spp) + " (" + str(int(spp/24)) + ") quantizedSPP: " + str(quantizedSPP) + " (" + str(int(spp/24)) + ") diff: " + str(spp - quantizedSPP) + " quantizeStep: " + str(quantizeValue) + " (" + str(int(quantizeValue/24)) + ")"
            return quantizedSPP

    def quantize(self, quantizeValue):
        self._quantizeValue = quantizeValue
        if((self._noteOnSPP >= 0.0) and (self._noteOnQuantizedSPP < 0)):
            self._noteOnQuantizedSPP = self._quantize(self._noteOnSPP, quantizeValue)
        if((self._noteOffSPP >= 0.0) and (self._noteOffQuantizedSPP < 0)):
            self._noteOffQuantizedSPP = self._quantize(self._noteOffSPP, quantizeValue)

class MidiChannelStateHolder(object):
    def __init__(self, channelId):
        self._midiChannel = channelId

        self._activeNote = NoteState()
        self._nextNote = NoteState()

    def noteEvent(self, noteOn, note, velocity, songPosition):
        (midiSync, spp) = songPosition
        if(noteOn == False):
            if(self._activeNote.isOn(note)):
                self._activeNote.noteOff(note, velocity, songPosition, spp, midiSync)
            elif(self._nextNote.isOn(note)):
                self._nextNote.noteOff(note, velocity, songPosition, spp, midiSync)
        else:
            if(velocity > 0):
                self._nextNote = NoteState()#reset note
                self._nextNote.noteOn(note, velocity, songPosition, spp, midiSync)
            else:
                #Velocity 0 is the same as note off.
                if(self._activeNote.isOn(note)):
                    self._activeNote.noteOff(note, velocity, songPosition, spp, midiSync)
                elif(self._nextNote.isOn(note)):
                    self._nextNote.noteOff(note, velocity, songPosition, spp, midiSync)

    def getActiveNote(self, spp):
        if(self._nextNote.isActive(spp)):
            self._activateNextNote()
        return self._activeNote

    def getNextNote(self):
        return self._nextNote

    def _activateNextNote(self):
        self._activeNote = self._nextNote
        self._nextNote = NoteState()#reset note

    def quantizeNextNote(self, note, quantizeValue):
        if(self._nextNote.getNote() == note):
            self._nextNote.quantize(quantizeValue)

    def checkNextNoteQuantize(self):
        if(self._nextNote.isUnquantized()):
            return self._nextNote.getNote()
        return -1

    def printState(self, midiChannel):
        self._activeNote.printState(self._midiChannel)

class MidiStateHolder(object):
    def __init__(self):
        self._midiChannelStateHolder = []
        for i in range(16):
            self._midiChannelStateHolder.append(MidiChannelStateHolder(i+1))

    def noteOn(self, midiChannel, data1, data2, songPosition):
        self._midiChannelStateHolder[midiChannel].noteEvent(True, data1, data2, songPosition)

    def noteOff(self, midiChannel, data1, data2, songPosition):
        self._midiChannelStateHolder[midiChannel].noteEvent(False, data1, data2, songPosition)

    def polyPreasure(self, midiChannel, data1, data2, songPosition):
        pass

    def controller(self, midiChannel, data1, data2, songPosition):
        pass

    def programChange(self, midiChannel, data1, data2, songPosition):
        pass

    def aftertouch(self, midiChannel, data1, data2, songPosition):
        pass

    def pitchBend(self, midiChannel, data1, data2, songPosition):
        pass

    def getActiveNote(self, midiChannel, spp):
        return self._midiChannelStateHolder[midiChannel].getActiveNote(spp)

    def checkForWaitingNote(self, midiChannel):
        return self._midiChannelStateHolder[midiChannel].checkNextNoteQuantize()

    def quantizeWaitingNote(self, midiChannel, note, quantizeValue):
        self._midiChannelStateHolder[midiChannel].quantizeNextNote(note, quantizeValue)

    def printState(self):
        for i in range(16):
            self._midiChannelStateHolder[i].printState()

