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

    def getUnquantizedStartPosition(self):
        return self._noteOnSPP

    def getStopPosition(self):
        return self._noteOffQuantizedSPP

    def isActive(self, spp):
        if(self._note == -1):
            return False
        if(self._noteOnQuantizedSPP == -1):
            return False
        if((spp < 0.0) or (self._noteOnQuantizedSPP <= spp)):
            return True
        else:
            return False

    def isNoteUneleased(self, spp):
        if(self._note == -1):
            return False
        if(self._noteOffQuantizedSPP == -1):
            return True
        if(self._noteOffQuantizedSPP > spp):
            return True
        else:
            return False

    def isNoteReleased(self, spp):
        if(self._note == -1):
            return False
        if(self._noteOffQuantizedSPP == -1):
            return False
        if(self._noteOffQuantizedSPP <= spp):
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
                print "State: Note on: " + self._noteLetter + str(self._octav) + " vel: " + str(self._velocity) + " channel: " + str(midiChannel) + " OnSPP: " + str(self._noteOnSPP) + " OffSPP: " + str(self._noteOffSPP) + " OnSPP: " + str(self._noteOnQuantizedSPP) + " OffSPP: " + str(self._noteOffQuantizedSPP)
            else:
                print "State: Note off: " + self._noteLetter + str(self._octav) + " vel: " + str(self._velocity) + " channel: " + str(midiChannel) + " OnSPP: " + str(self._noteOnSPP) + " OffSPP: " + str(self._noteOffSPP) + " OnSPP: " + str(self._noteOnQuantizedSPP) + " OffSPP: " + str(self._noteOffQuantizedSPP)

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

#        self._nextNote = NoteState()
        self._activeNotes = []
        for i in range(128): #@UnusedVariable
            self._activeNotes.append(NoteState())
        self._numberOfWaitingActiveNotes = 0
        self._nextNotes = []
        for i in range(128): #@UnusedVariable
            self._nextNotes.append(NoteState())
        self._numberOfWaitingNextNotes = 0
        self._activeNote = self._activeNotes[0]


    def noteEvent(self, noteOn, note, velocity, songPosition):
        (midiSync, spp) = songPosition
        if(noteOn == False):
            nextNote = self._nextNotes[note]
            if(self._activeNote.isOn(note)):
                self._activeNote.noteOff(note, velocity, songPosition, spp, midiSync)
            elif(nextNote.isOn(note)):
                nextNote.noteOff(note, velocity, songPosition, spp, midiSync)
        else:
            if(velocity > 0): #NOTE ON!!!
                nextNote = NoteState()#reset note
                nextNote.noteOn(note, velocity, songPosition, spp, midiSync)
                self._nextNotes[note] = nextNote
                self._numberOfWaitingNextNotes += 1
            else:
                #Velocity 0 is the same as note off.
                if(self._activeNote.isOn(note)):
                    self._activeNote.noteOff(note, velocity, songPosition, spp, midiSync)
                elif(nextNote.isOn(note)):
                    nextNote.noteOff(note, velocity, songPosition, spp, midiSync)

    def _findWaitingActiveNote(self, spp):
        returnNote = None
        noteCount = 0
        for note in range(128):
            testNote = self._activeNotes[note]
            if(testNote.isActive(spp)):
                if(testNote.isNoteUneleased(spp)):
                    if(returnNote == None):
                        returnNote = testNote
                    else:
                        if(testNote.getStartPosition() < returnNote.getStartPosition()):
                            returnNote = testNote
                    noteCount += 1
        self._numberOfWaitingActiveNotes = noteCount
        return returnNote

    def _findWaitingNextNote(self):
        returnNote = None
        noteCount = 0
        for note in range(128):
            testNote = self._nextNotes[note]
            if(testNote.isActive(-1.0)):
                if(returnNote == None):
                    returnNote = testNote
                else:
                    if(testNote.getStartPosition() < returnNote.getStartPosition()):
                        returnNote = testNote
                noteCount += 1
        self._numberOfWaitingNextNotes = noteCount
        return returnNote

    def _findUnquantizedNexNote(self):
        returnNote = None
        for note in range(128):
            testNote = self._nextNotes[note]
            if(testNote.isUnquantized()):
                if(returnNote == None):
                    returnNote = testNote
                else:
                    if(testNote.getUnquantizedStartPosition() < returnNote.getUnquantizedStartPosition()):
                        returnNote = testNote
        return returnNote

    def getActiveNote(self, spp):
        if(self._numberOfWaitingNextNotes > 0):
            nextNote = self._findWaitingNextNote()
            if((nextNote != None) and (nextNote.isActive(spp))):
                self._activateNextNote(nextNote)
        if(self._numberOfWaitingActiveNotes > 0):
            if(self._activeNote.isNoteReleased(spp)):
                testNote = self._findWaitingActiveNote(spp)
                if(testNote != None):
                    print "Re activating downpressed note: " + str(testNote.getNote())
                    self._activeNote = testNote
        return self._activeNote

#    def getNextNote(self):
#        return self._nextNote

    def _activateNextNote(self, nextNote):
        noteId = nextNote.getNote()
        print "Activate NextNote! " + str(noteId)
        self._activeNote = nextNote
        self._activeNotes[noteId] = nextNote
        self._nextNotes[noteId] = NoteState()#reset note
        self._numberOfWaitingNextNotes -= 1
        self._numberOfWaitingActiveNotes += 1

    def quantizeNextNote(self, note, quantizeValue):
        testNote = self._nextNotes[note]
        if(testNote.getNote() == note):
            testNote.quantize(quantizeValue)

    def checkNextNoteQuantize(self):
        unquantizedNote = self._findUnquantizedNexNote()
        if(unquantizedNote != None):
            return unquantizedNote.getNote()
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

