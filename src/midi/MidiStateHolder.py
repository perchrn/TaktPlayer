'''
Created on 20. des. 2011

@author: pcn
'''
from midi import MidiUtilities
import logging
from midi.MidiController import MidiControllers
import time

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
        self._noteOffQuantizedSPP = self._quantize(spp, self._quantizeValue)
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
#            print "Quantizing Note: " + str(self._note) + " SPP: " + str(spp) + " (" + str(int(spp/24)) + ") quantizedSPP: " + str(quantizedSPP) + " (" + str(int(spp/24)) + ") diff: " + str(spp - quantizedSPP) + " quantizeStep: " + str(quantizeValue) + " (" + str(int(quantizeValue/24)) + ")"
            return quantizedSPP

    def quantize(self, quantizeValue):
        self._quantizeValue = quantizeValue
        if((self._noteOnSPP >= 0.0) and (self._noteOnQuantizedSPP < 0)):
            self._noteOnQuantizedSPP = self._quantize(self._noteOnSPP, quantizeValue)
        if((self._noteOffSPP >= 0.0) and (self._noteOffQuantizedSPP < 0)):
            self._noteOffQuantizedSPP = self._quantize(self._noteOffSPP, quantizeValue)

class MidiControllerLatestModified(object):
    def __init__(self):
        self._numberToSave = 10
        self._latestControllers = []

    def controllerUpdated(self, controllerId):
        print "DEBUG controllerUpdated()"
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
#        print "DEBUG got controller: " + getControllerName(controllerId) + " (id: " + str(controllerId) + ")"
        if(controllerId == self._midiControllers.ResetAllControllers):
            self._log.info("Resetting all controller values for MIDI channel %d at %f" %(self._midiChannel, songPosition))
            for i in range(128):
                self._controllerValues[i] = 0.0
        else:
            print "DEBUG controllerChange()"
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

    def cleanupFutureNotes(self, songPosition, timeLimit):
        for note in range(128):
            testNote = self._nextNotes[note]
            if(testNote.isFarAway(songPosition, timeLimit)):
                self._nextNotes[note] = NoteState()#reset note

    def printState(self, midiChannel):
        self._activeNote.printState(self._midiChannel)

class MidiStateHolder(object):
    def __init__(self):
        self._midiChannelStateHolder = []
        self._midiControllerLatestModified = MidiControllerLatestModified()
        for i in range(16):
            self._midiChannelStateHolder.append(MidiChannelStateHolder(i+1, self._midiControllerLatestModified))

    def noteOn(self, midiChannel, data1, data2, songPosition):
        self._midiChannelStateHolder[midiChannel].noteEvent(True, data1, data2, songPosition)

    def noteOff(self, midiChannel, data1, data2, songPosition):
        self._midiChannelStateHolder[midiChannel].noteEvent(False, data1, data2, songPosition)

    def polyPreasure(self, midiChannel, data1, data2, songPosition):
        self._midiChannelStateHolder[midiChannel].polyPreasure(data1, data2, songPosition)

    def controller(self, midiChannel, data1, data2, songPosition):
        self._midiChannelStateHolder[midiChannel].controllerChange(data1, data2, songPosition)

    def programChange(self, midiChannel, data1, data2, songPosition):
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

    def cleanupFutureNotes(self, songPosition, timeLimit):
        for i in range(16):
            self._midiChannelStateHolder[i].cleanupFutureNotes(songPosition, timeLimit)
        
    def printState(self):
        for i in range(16):
            self._midiChannelStateHolder[i].printState()

    def getMidiChannelState(self, midiChannel):
        return self._midiChannelStateHolder[midiChannel]

    def getLatestMidiControllersString(self):
        return self._midiControllerLatestModified.getLatestControllersString()

