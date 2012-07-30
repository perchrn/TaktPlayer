'''
Created on 20. des. 2011

@author: pcn
'''
from midi import MidiUtilities
import logging
from midi.MidiController import MidiControllers
import time

def quantizePosition(spp, quantizeValue):
    if(quantizeValue < 0.125):
        return spp
    else:
        intSPP = int(spp)
        rest = intSPP % quantizeValue
        quantizedSPP = int(intSPP / quantizeValue) * quantizeValue
        factor = float(rest) / quantizeValue
        if(factor > 0.15):
            quantizedSPP += quantizeValue
#            print "Quantizing Note: " + str(self._note) + " SPP: " + str(spp) + " (" + str(int(spp/24)) + ") quantizedSPP: " + str(quantizedSPP) + " (" + str(int(spp/24)) + ") diff: " + str(spp - quantizedSPP) + " quantizeStep: " + str(quantizeValue) + " (" + str(int(quantizeValue/24)) + ")"
        return quantizedSPP

class NoteModulationSources():
    Velocity, ReleaseVelocity, NotePreasure = range(3)

    def getChoices(self):
        return ["Velocity", "ReleaseVelocity", "NotePreasure"]

    def getNames(self, typeId):
        for i in range(len(self.getChoices())):
            if(typeId == i):
                return self.getChoices()[i]
        return self.getChoices()[0]

    def getId(self, typeName):
        choices = self.getChoices()
        for i in range(len(choices)):
            name = choices[i]
            if(name == typeName):
                return i
        if(typeName == "Preasure"):
            return NoteModulationSources.NotePreasure
        return -1

class NoteState(object):
    def __init__(self):
        self._noteOn = False
        self._note = -1
        self._octav = -1
        self._noteLetter = ' '
        self._velocity = -1
        self._releaseVelocity = 0
        self._preasure = 0
        self._noteOnSPP = -1.0
        self._noteOffSPP = -1.0
        self._noteLegth = 0.0
        self._noteOnQuantizedSPP = -1
        self._noteOffQuantizedSPP = -1
        self._noteOnInSync = False
        self._noteOffInSync = False
        self._quantizeValue = 0
        self._isNew = False

    def getModulationId(self, modName):
        if(modName == "Velocity"):
            return NoteModulationSources.Velocity
        elif(modName == "ReleaseVelocity"):
            return NoteModulationSources.ReleaseVelocity
        elif(modName == "NotePreasure"):
            return NoteModulationSources.NotePreasure
        elif(modName == "Preasure"):
            return NoteModulationSources.NotePreasure
        else:
            return None

    def getModulationValue(self, modId, argument):
        isInt = isinstance(modId, int)
        if(isInt == True):
            if(modId == NoteModulationSources.Velocity):
                velMod = float(self._velocity) / 128
                return velMod
            elif(modId == NoteModulationSources.ReleaseVelocity):
                velMod = float(self._releaseVelocity) / 128
                return velMod
            elif(modId == NoteModulationSources.NotePreasure):
                preasureMod = float(self._preasure) / 128
                return preasureMod
        elif(len(modId) == 1):
            if(modId[0] == NoteModulationSources.Velocity):
                velMod = float(self._velocity) / 128
                return velMod
            elif(modId[0] == NoteModulationSources.ReleaseVelocity):
                velMod = float(self._releaseVelocity) / 128
                return velMod
            elif(modId[0] == NoteModulationSources.NotePreasure):
                preasureMod = float(self._preasure) / 128
                return preasureMod
        return 0.0

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

    def getNoteLength(self):
        return self._noteLegth

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

    def isFarAway(self, songPosition, timeLimit):
        if(self._note == -1):
            return False
        if(abs(self._noteOnSPP - songPosition) > timeLimit):
            return True
        return False

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

    def setPreasure(self, preasure):
        self._preasure = preasure

    def setNewState(self, state = True):
        self._isNew = state

    def isNew(self):
        return self._isNew

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
        self._noteOffQuantizedSPP = quantizePosition(spp, self._quantizeValue)
        self._noteLegth = self._noteOffQuantizedSPP - self._noteOnQuantizedSPP
        if(self._noteLegth == 0.0):
            self._noteLegth = self._quantizeValue / 4.0
        if(self._noteLegth == 0.0):
            self._noteLegth = 6.0
        self._note = note
        (octav, noteLetter) = MidiUtilities.noteToOctavAndLetter(note)
        self._octav = octav
        self._noteLetter = noteLetter
        self._releaseVelocity = velocity

    def quantize(self, quantizeValue):
        self._quantizeValue = quantizeValue
        if((self._noteOnSPP >= 0.0) and (self._noteOnQuantizedSPP < 0)):
            self._noteOnQuantizedSPP = quantizePosition(self._noteOnSPP, quantizeValue)
        if((self._noteOffSPP >= 0.0) and (self._noteOffQuantizedSPP < 0)):
            self._noteOffQuantizedSPP = quantizePosition(self._noteOffSPP, quantizeValue)

    def moveStartPos(self, moveValue):
        self._noteOnSPP += moveValue
        if(self._noteOnSPP < 0.0):
            self._noteOnSPP = 0.0
        if(self._noteOnQuantizedSPP > -1.0):
            self._noteOnQuantizedSPP += moveValue
            if(self._noteOnQuantizedSPP < 0.0):
                self._noteOnQuantizedSPP = 0.0
        if(self._noteOffSPP > -1.0):
            self._noteOffSPP += moveValue
            if(self._noteOffSPP < 0.0):
                self._noteOffSPP = 0.0
        if(self._noteOffQuantizedSPP > -1.0):
            self._noteOffQuantizedSPP += moveValue
            if(self._noteOffQuantizedSPP < 0.0):
                self._noteOffQuantizedSPP = 0.0

        
class MidiControllerLatestModified(object):
    def __init__(self):
        self._numberToSave = 10
        self._latestControllers = []

    def controllerUpdated(self, controllerId):
        oldestIndex = None
        currentTime = time.time()
        oldestTime = currentTime
        for i in range(len(self._latestControllers)):
            oldControllerId, oldControllerTime = self._latestControllers[i]
            if(oldControllerId == controllerId):
                self._latestControllers[i] = (controllerId, currentTime)
                return
            if(oldControllerTime < oldestTime):
                oldestTime = oldControllerTime
                oldestIndex = i
        if(len(self._latestControllers) < self._numberToSave):
            self._latestControllers.append((controllerId, currentTime))
        elif(oldestIndex != None):
            self._latestControllers[oldestIndex] = (controllerId, currentTime)

    def getLatestControllers(self):
        self._latestControllers = sorted(self._latestControllers, key=lambda controller: controller[1], reverse=True)
        return self._latestControllers

    def getLatestControllersString(self):
        returnString = ""
        for controllerInfo in self.getLatestControllers():
            if(returnString != ""):
                returnString += ","
            returnString += str(controllerInfo[0])
        return returnString

class MidiChannelModulationSources():
    Controller, PitchBend, Aftertouch = range(3)

    def getChoices(self):
        return ("Controller", "PitchBend", "Aftertouch")

    def getNames(self, typeId):
        for i in range(len(self.getChoices())):
            if(typeId == i):
                return self.getChoices()[i]
        return self.getChoices()[0]

class MidiChannelStateHolder(object):
    def __init__(self, channelId, midiControllerLatestModified):
        self._log = logging.getLogger('%s.%s' % (__name__, self.__class__.__name__))
        self._midiChannel = channelId

        self._activeNotes = []
        for i in range(128): #@UnusedVariable
            self._activeNotes.append(NoteState())
        self._numberOfWaitingActiveNotes = 0
        self._nextNotes = []
        for i in range(128): #@UnusedVariable
            self._nextNotes.append(NoteState())
        self._numberOfWaitingNextNotes = 0
        self._activeNote = self._activeNotes[0]

        self._controllerValues = []
        for i in range(128): #@UnusedVariable
            self._controllerValues.append(0.0)

        self._pitchBendValue = 0.5 #No pitch bend
        self._aftertouch = 0.0 #No aftertouch

        self._midiControllers = MidiControllers()
        self._midiControllerLatestModified = midiControllerLatestModified

    def getModulationId(self, modName):
        if(modName == "Controller"):
            return MidiChannelModulationSources.Controller
        elif(modName == "PitchBend"):
            return MidiChannelModulationSources.PitchBend
        elif(modName == "Aftertouch"):
            return MidiChannelModulationSources.Aftertouch
        else:
            return None

    def getModulationSubId(self, modId, subModName):
        if(modId == MidiChannelModulationSources.Controller):
            return self._midiControllers.getId(subModName)
        else:
            return None

    def getModulationValue(self, modId, argument):
        isInt = isinstance(modId, int)
        if((isInt == False) and (len(modId) == 2)):
            if(modId[0] == MidiChannelModulationSources.Controller):
                return self._controllerValues[modId[1]]
        elif(isInt == True):
            if(modId == MidiChannelModulationSources.PitchBend):
                return self._pitchBendValue
            if(modId == MidiChannelModulationSources.Aftertouch):
                return self._aftertouch
        elif(len(modId) == 1):
            if(modId[0] == MidiChannelModulationSources.PitchBend):
                return self._pitchBendValue
            if(modId[0] == MidiChannelModulationSources.Aftertouch):
                return self._aftertouch
        return 0.0

    def noteEvent(self, noteOn, note, velocity, songPosition):
        (midiSync, spp) = songPosition
        nextNote = self._nextNotes[note]
        if(noteOn == False):
            if(self._activeNote.isOn(note)):
                self._activeNote.noteOff(note, velocity, songPosition, spp, midiSync)
            if(nextNote.isOn(note)):
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
                if(nextNote.isOn(note)):
                    nextNote.noteOff(note, velocity, songPosition, spp, midiSync)

    def polyPreasure(self, note, preasure, songPosition):
        self._nextNotes[note].setPreasure(preasure)
        self._activeNotes[note].setPreasure(preasure)

    def controllerChange(self, controllerId, value, songPosition):
#        print "DEBUG got controller: " + self._midiControllers.getName(controllerId) + " (id: " + str(controllerId) + ") value: " + str(value)
        if(controllerId == self._midiControllers.ResetAllControllers):
            self._log.info("Resetting all controller values for MIDI channel %d at %f" %(self._midiChannel, songPosition))
            for i in range(128):
                self._controllerValues[i] = 0.0
        else:
            self._controllerValues[controllerId] = (float(value) / 127)
            self._midiControllerLatestModified.controllerUpdated(controllerId)

    def pitchBendChange(self, data1, data2, songPosition):
        self._pitchBendValue = (float(data2) / 128) + (float(data1) / 16256)#(127*128)

    def aftertouchChange(self, data1, data2, songPosition):
        self._aftertouch = (float(data1) / 128) + (float(data2) / 16256)#(127*128)

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
                self._activeNote.setNewState(True)
        if(self._numberOfWaitingActiveNotes > 0):
            if(self._activeNote.isNoteReleased(spp)):
                testNote = self._findWaitingActiveNote(spp)
                if(testNote != None):
                    print "Re activating downpressed note: " + str(testNote.getNote())
                    self._activeNote = testNote
        return self._activeNote

    def removeDoneActiveNote(self):
        noteId = self._activeNote.getNote()
        if(noteId != -1):
            self._activeNotes[noteId] = NoteState()#reset note
            self._activeNote = self._activeNotes[noteId]

    def removeAllNotes(self):
        for i in range(128):
            self._activeNotes[i] = NoteState()
            self._nextNotes[i] = NoteState()
        self._activeNote = self._activeNotes[0]

    def _activateNextNote(self, nextNote):
        noteId = nextNote.getNote()
        self._activeNote = nextNote
        self._activeNotes[noteId] = nextNote
        self._nextNotes[noteId] = NoteState()#reset note
        self._numberOfWaitingNextNotes -= 1
        self._numberOfWaitingActiveNotes += 1

    def quantizeWaitingNote(self, note, quantizeValue):
        testNote = self._nextNotes[note]
        if(testNote.getNote() == note):
            testNote.quantize(quantizeValue)

    def checkIfNextNoteIsQuantized(self):
        unquantizedNote = self._findUnquantizedNexNote()
        if(unquantizedNote != None):
            return unquantizedNote.getNote()
        return -1

    def cleanupFutureNotes(self, songPositionTuplet, oldSongPosition, timeLimit):
        midiSync, songPosition = songPositionTuplet #@UnusedVariable
        for note in range(128):
            testNote = self._nextNotes[note]
            if(testNote.isFarAway(songPosition, timeLimit)):
                self._nextNotes[note] = NoteState()#reset note
            testNote = self._activeNotes[note]
            if(testNote.isFarAway(songPosition, timeLimit)):
                self._activeNotes[note] = NoteState()#reset note
        noteId = self._activeNote.getNote()
        if(noteId != -1):
            self._activeNote = self._activeNotes[noteId]

    def fixLoopingNotes(self, oldSongPosition, newSongPosition, ticksPerQuarteNote):
        if(newSongPosition > oldSongPosition):
            return
        newPosQuantized = quantizePosition(newSongPosition, ticksPerQuarteNote)
        jumpLength = oldSongPosition - newSongPosition
        jumpLengthQuantized = quantizePosition(jumpLength, ticksPerQuarteNote)
        for note in range(128):
            testNote = self._activeNotes[note]
            noteStart = testNote.getUnquantizedStartPosition()
            if(noteStart > newPosQuantized):
                testNote.moveStartPos(-jumpLengthQuantized)
#                print "DEBUG fixLoopingNotes() for note: " + str(testNote.getNote()) + " with old start: " + str(noteStart) + " new start: " + str(testNote.getUnquantizedStartPosition())

    def printState(self, midiChannel):
        self._activeNote.printState(self._midiChannel)


class GuiControllerValues(object):
    def __init__(self, myId):
        self._id = myId
        self._lastMidiChannel = -1
        self._controllerStates = []
        for i in range(16): #@UnusedVariable
            self._controllerStates.append(None)

    def controllerChange(self, midiChannel, value, command):
        self._lastMidiChannel = midiChannel
        controllerNr = int(command & 0x0f)
        self._controllerStates[controllerNr] = (float(value) / 127)
        #print "DEBUG setting gui value: " + str(self._controllerStates[controllerNr]) + " for ID: " + str(self._id) + " contoller: " + str(controllerNr)

    def resetState(self, command = None):
        if(command == None):
            for i in range(16):
                self._controllerStates[i] = None
        else:
            baseController = int(command & 0x0f)
            for i in range(5):
                self._controllerStates[baseController + i] = None

    def getGuiContollerState(self, guiCtrlStateStartId):
        return (self._controllerStates[guiCtrlStateStartId], self._controllerStates[guiCtrlStateStartId+1], self._controllerStates[guiCtrlStateStartId+2], self._controllerStates[guiCtrlStateStartId+3], self._controllerStates[guiCtrlStateStartId+4])

    def updateWithGuiSettings(self, guiCtrlStateStartId, effectsValues):
        effectAmount, effectArg1, effectArg2, effectArg3, effectArg4 = effectsValues
        if(self._controllerStates[guiCtrlStateStartId] != None):
            effectAmount = self._controllerStates[guiCtrlStateStartId]
        if(self._controllerStates[guiCtrlStateStartId+1] != None):
            effectArg1 = self._controllerStates[guiCtrlStateStartId+1]
        if(self._controllerStates[guiCtrlStateStartId+2] != None):
            effectArg2 = self._controllerStates[guiCtrlStateStartId+2]
        if(self._controllerStates[guiCtrlStateStartId+3] != None):
            effectArg3 = self._controllerStates[guiCtrlStateStartId+3]
        if(self._controllerStates[guiCtrlStateStartId+4] != None):
            effectArg4 = self._controllerStates[guiCtrlStateStartId+4]
        return (effectAmount, effectArg1, effectArg2, effectArg3, effectArg4)
        
class MidiStateHolder(object):
    def __init__(self):
        self._midiChannelStateHolder = []
        self._midiControllerLatestModified = MidiControllerLatestModified()
        for i in range(16):
            self._midiChannelStateHolder.append(MidiChannelStateHolder(i+1, self._midiControllerLatestModified))
        self._guiControllerNoteValues = []
        for i in range(128):
            self._guiControllerNoteValues.append(GuiControllerValues(i))
        self._guiControllerChannelValues = []
        for i in range(16):
            self._guiControllerChannelValues.append(GuiControllerValues(i))

    def noteOn(self, midiChannel, data1, data2, songPosition):
#        print "DEBUG pcn: Note on: " + str(data1) + " spp: " + str(songPosition)
        self._midiChannelStateHolder[midiChannel].noteEvent(True, data1, data2, songPosition)

    def noteOff(self, midiChannel, data1, data2, songPosition):
        self._midiChannelStateHolder[midiChannel].noteEvent(False, data1, data2, songPosition)

    def polyPreasure(self, midiChannel, data1, data2, songPosition):
        self._midiChannelStateHolder[midiChannel].polyPreasure(data1, data2, songPosition)

    def controller(self, midiChannel, data1, data2, songPosition):
        self._midiChannelStateHolder[midiChannel].controllerChange(data1, data2, songPosition)

    def guiController(self, midiChannel, data1, data2, data3):
        if((data3 & 0xf0) == 0xf0):
            note = min(max(0, data1), 127)
            self._guiControllerNoteValues[note].controllerChange(midiChannel, data2, data3)
        if((data3 & 0xf0) == 0xe0):
            self._guiControllerChannelValues[midiChannel].controllerChange(midiChannel, data2, data3)
        if((data3 & 0xf0) == 0xd0):
            note = min(max(0, data1), 127)
            self._guiControllerNoteValues[note].resetState(data3)
        if((data3 & 0xf0) == 0xc0):
            self._guiControllerChannelValues[midiChannel].resetState(data3)

        if((data3 & 0xf0) == 0x80):
            self._midiChannelStateHolder[midiChannel].removeAllNotes()

    def programChange(self, midiChannel, data1, data2, data3, songPosition):
        print "programChange............ " + str(data1) + " : " + str(data2)
        pass

    def aftertouch(self, midiChannel, data1, data2, songPosition):
        self._midiChannelStateHolder[midiChannel].aftertouchChange(data1, data2, songPosition)

    def pitchBend(self, midiChannel, data1, data2, songPosition):
        self._midiChannelStateHolder[midiChannel].pitchBendChange(data1, data2, songPosition)

    def getActiveNote(self, midiChannel, spp):
        return self._midiChannelStateHolder[midiChannel].getActiveNote(spp)

    def checkForWaitingNote(self, midiChannel):
        return self._midiChannelStateHolder[midiChannel].checkIfNextNoteIsQuantized()

    def quantizeWaitingNote(self, midiChannel, note, quantizeValue):
        self._midiChannelStateHolder[midiChannel].quantizeWaitingNote(note, quantizeValue)

    def cleanupFutureNotes(self, songPosition, oldSongPosition, timeLimit):
        for i in range(16):
            self._midiChannelStateHolder[i].cleanupFutureNotes(songPosition, oldSongPosition, timeLimit)

    def fixLoopingNotes(self, oldSongPosition, newSongPosition, ticksPerQuarteNote):
        for i in range(16):
            self._midiChannelStateHolder[i].fixLoopingNotes(oldSongPosition, newSongPosition, ticksPerQuarteNote)

    def printState(self):
        for i in range(16):
            self._midiChannelStateHolder[i].printState()

    def getMidiChannelState(self, midiChannel):
        return self._midiChannelStateHolder[midiChannel]

    def getLatestMidiControllersString(self):
        return self._midiControllerLatestModified.getLatestControllersString()

    def getGuiNoteControllerStareHolder(self, midiNote):
        note = min(max(0, midiNote), 127)
        return self._guiControllerNoteValues[note]

    def getMidiChannelControllerStateHolder(self, midiChannel):
        channel = min(max(0, midiChannel), 15)
        return self._guiControllerChannelValues[channel]

class DummyMidiStateHolder(object):
    def __init__(self):
        self._lastMidiEventTime = -1

    def noteOn(self, midiChannel, data1, data2, songPosition):
        self._lastMidiEventTime = time.time()
#        print "Got note! " + str(self._lastMidiEventTime)

    def noteOff(self, midiChannel, data1, data2, songPosition):
        self._lastMidiEventTime = time.time()
#        print "Got note off! " + str(self._lastMidiEventTime)

    def polyPreasure(self, midiChannel, data1, data2, songPosition):
        self._lastMidiEventTime = time.time()
#        print "Got PP! " + str(self._lastMidiEventTime)

    def controller(self, midiChannel, data1, data2, songPosition):
        self._lastMidiEventTime = time.time()
#        print "Got ctrl! " + str(self._lastMidiEventTime)

    def guiController(self, midiChannel, data1, data2, data3):
        self._lastMidiEventTime = time.time()
#        print "Got gui?!?! " + str(self._lastMidiEventTime)

    def programChange(self, midiChannel, data1, data2, data3, songPosition):
        self._lastMidiEventTime = time.time()
#        print "Got prg! " + str(self._lastMidiEventTime)()

    def aftertouch(self, midiChannel, data1, data2, songPosition):
        self._lastMidiEventTime = time.time()
#        print "Got aft! " + str(self._lastMidiEventTime)

    def pitchBend(self, midiChannel, data1, data2, songPosition):
        self._lastMidiEventTime = time.time()
#        print "Got bnd! " + str(self._lastMidiEventTime)

    def cleanupFutureNotes(self, songPosition, oldSongPosition, timeLimit):
        self._lastMidiEventTime = time.time()
#        print "Got clr! " + str(self._lastMidiEventTime)

    def getLastMidiEventTime(self):
        return self._lastMidiEventTime
