'''
Created on 9. jan. 2012

@author: pcn
'''
import random
import math
from midi.MidiStateHolder import MidiChannelStateHolder, NoteState

class LowFrequencyOscilator(object):
    class Shape():
        Triangle, SawTooth, Ramp, Sine, Random = range(5)

    def __init__(self, midiTimingClass, mode, midiLength = 4.0, startSPP = 0.0):
        self._midiTiming = midiTimingClass
        self._startSongPosition = startSPP
        self._syncLength = midiLength * self._midiTiming.getTicksPerQuarteNote()
        self._Shape = mode
        random.seed(self._midiTiming.getTime())
        self._radians360 = math.radians(360)

    def getValue(self, songPosition, argument):
        if(self._Shape == LowFrequencyOscilator.Shape.Random):
            return random.random()
        else:
            phase = ((songPosition - self._startSongPosition) / self._syncLength) % 1.0
            if(self._Shape == LowFrequencyOscilator.Shape.Triangle):
                return abs((phase * 2) - 1.0)
            elif(self._Shape == LowFrequencyOscilator.Shape.SawTooth):
                return phase
            elif(self._Shape == LowFrequencyOscilator.Shape.Ramp):
                return 1.0 - phase
            elif(self._Shape == LowFrequencyOscilator.Shape.Sine):
                return math.sin(self._radians360 * phase)

def getShapeId(shapeName):
    if(shapeName == "Triangle"):
        return LowFrequencyOscilator.Shape.Triangle
    elif(shapeName == "SawTooth"):
        return LowFrequencyOscilator.Shape.SawTooth
    elif(shapeName == "Ramp"):
        return LowFrequencyOscilator.Shape.Ramp
    elif(shapeName == "Sine"):
        return LowFrequencyOscilator.Shape.Sine
    elif(shapeName == "Random"):
        return LowFrequencyOscilator.Shape.Random
    else:
        return None

class ModulationSources():
    MidiChannel, MidiNote, Lfo = range(3)

class ModulatiobReceiver(object):
    def __init__(self, modId, name):
        self._modId = modId
        self._name = name

    def getName(self):
        return self._name

class MidiModulation(object):
    def __init__(self, configurationTree):
        self._tmpMidiChClass = MidiChannelStateHolder(0)
        self._tmpMidiNoteClass = NoteState()

        self._configurationTree = configurationTree

        self._modulationReceivers = []
        self._activeLfos = []

    def setModulationReceiver(self, name, defaultValue):
        if(self.findReceiver(name) == None):
            modId = len(self._modulationReceivers)
            self._modulationReceivers.append(ModulatiobReceiver(modId, name))
        else:
            print "Duplicate receiver configured... Ignored."
        self._configurationTree.addTextParameter(name, defaultValue)

    def findReceiver(self, receiverName):
        for regReceiver in self._modulationReceivers:
            if(regReceiver.getName() == receiverName):
                return regReceiver
        return None

    def connectModulation(self, receiverName):
        receiver = self.findReceiver(receiverName)
        if(receiver == None):
            print "Unregistered receiver \"%s\"" % receiverName
            return None
        sourceDescription = self._configurationTree.getValue(receiverName)
        sourceSplit = sourceDescription.split('.', 6)
        if( sourceSplit[0] == "MidiChannel" ):
            if(len(sourceSplit) > 1):
                modId = self._tmpMidiChClass.getModulationId(sourceSplit[1])
                if(modId != None):
                    if(len(sourceSplit) > 2):
                        subId = self._tmpMidiChClass.getModulationSubId(modId, sourceSplit[2])
                        if(subId != None):
                            modId = (modId, subId)
                    return (ModulationSources.MidiChannel, modId)
        elif( sourceSplit[0] == "MidiNote" ):
            modId = self._tmpMidiNoteClass.getModulationId(sourceSplit[1])
            if(modId != None):
                return (ModulationSources.MidiNote, modId)
        elif( sourceSplit[0] == "Lfo" ):
            if(len(sourceSplit) > 1):
                mode = getShapeId(sourceSplit[1])
                if(mode != None):
                    midiLength = 4.0
                    startSPP = 0.0
                    if(len(sourceSplit) > 2):
                        tmpLength = float(sourceSplit[2])
                        if(tmpLength > 0.0):
                            midiLength = tmpLength
                        if(len(sourceSplit) > 3):
                            tmpSPP = float(sourceSplit[2])
                            if(tmpSPP >= 0.0):
                                startSPP = tmpSPP
                    return (ModulationSources.Lfo, self.getLfoId(mode, midiLength, startSPP))
        if(sourceDescription != "None"):
            print "Invalid modulation description: \"%s\"" % sourceDescription
        return None

    def _getLfo(self, lfoConfig):
        mode, startSPP, midiLength = lfoConfig
        foundLfo = self.findLfo(mode, midiLength, startSPP)
        if(foundLfo == None):
            return LowFrequencyOscilator(mode, midiLength, startSPP)
        else:
            return foundLfo

    def getLfoId(self, mode, midiLength = 4.0 , startSPP = 0.0):
        return (mode, midiLength, startSPP)

    def getModlulationValue(self, combinedId, midiChannelStateHolder, midiNoteStateHolder, songPosition, argument = 0.0, plussMinus = False):
        if(combinedId != None):
            sourceId, subId = combinedId
            if(sourceId == ModulationSources.MidiChannel):
                return midiChannelStateHolder.getModulationValue(subId, argument)
            elif(sourceId == ModulationSources.MidiNote):
                return midiNoteStateHolder.getModulationValue(subId, argument)
            elif(sourceId == ModulationSources.Lfo):
                return self._getLfo(subId).getValue(songPosition, argument)
        #Return "0.0", if we don't find it.
        if(plussMinus == True):
            return 0.5
        else:
            return 0.0

    def getModlulationValueAsPlussMinus(self, combinedId, midiChannelStateHolder, midiNoteStateHolder, songPosition, argument = 0.0):
        value = self.getModlulationValue(combinedId, midiChannelStateHolder, midiNoteStateHolder, songPosition, argument, True)
        return (value * 2) - 1.0
