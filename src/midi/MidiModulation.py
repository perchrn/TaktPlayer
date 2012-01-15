'''
Created on 9. jan. 2012

@author: pcn
'''
import random
import math
from midi.MidiStateHolder import MidiChannelStateHolder, NoteState

# Modulation examples:
#MidiModulation.connectModulation("PlayBack", "MidiChannel.Controller.ModWheel")
#MidiModulation.connectModulation("PlayBack", "MidiChannel.Controller.Volume")
#MidiModulation.connectModulation("PlayBack", "MidiChannel.Controller.Pan")
#MidiModulation.connectModulation("PlayBack", "MidiChannel.PitchBend")
#MidiModulation.connectModulation("PlayBack", "MidiChannel.Aftertouch")
#MidiModulation.connectModulation("PlayBack", "MidiNote.Velocity")
#MidiModulation.connectModulation("PlayBack", "MidiNote.ReleaseVelocity")
#MidiModulation.connectModulation("PlayBack", "MidiNote.NotePreasure")
#MidiModulation.connectModulation("PlayBack", "LFO.Triangle.4.0|0.0")
#MidiModulation.connectModulation("PlayBack", "ADSR.ADSR.4.0|0.0|1.0|4.0")
#MidiModulation.connectModulation("PlayBack", "ADSR.AR.4.0|4.0")
#MidiModulation.connectModulation("PlayBack", "None")#Always 0.0

#MidiModulation.connectModulation("PlayBack", "Value.1.0")

class LowFrequencyOscilator(object):
    class Shape():
        Triangle, SawTooth, Ramp, Sine, Random = range(5)

    def __init__(self, midiTimingClass, mode, midiLength = 4.0, startSPP = 0.0):
        print "iiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiii"
        print "LowFrequencyOscilator: Len: %f, Start: %f S: %f R: %f" % (midiLength, startSPP)
        print "iiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiii"
        self._midiTiming = midiTimingClass
        self._startSongPosition = startSPP
        self._midiLength = midiLength
        self._syncLength = midiLength * self._midiTiming.getTicksPerQuarteNote()
        self._shape = mode
        random.seed(self._midiTiming.getTime())
        self._radians360 = math.radians(360)

    def getValue(self, songPosition, argument):
        if(self._shape == LowFrequencyOscilator.Shape.Random):
            return random.random()
        else:
            phase = ((songPosition - self._startSongPosition) / self._syncLength) % 1.0
            if(self._shape == LowFrequencyOscilator.Shape.Triangle):
                return abs((phase * 2) - 1.0)
            elif(self._shape == LowFrequencyOscilator.Shape.SawTooth):
                return phase
            elif(self._shape == LowFrequencyOscilator.Shape.Ramp):
                return 1.0 - phase
            elif(self._shape == LowFrequencyOscilator.Shape.Sine):
                return math.sin(self._radians360 * phase)

    def isEqual(self, mode, midiLength, startSPP):
        if(self._shape == mode):
            if(self._midiLength == midiLength):
                if(self._startSongPosition == startSPP):
                    return True
        return False

def getLfoShapeId(shapeName):
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

class AttackDecaySustainRelease(object):
    class Shape():
        ADSR, AR = range(2)

    def __init__(self, midiTimingClass, mode, attack, decay, sustain, release):
        self._midiTiming = midiTimingClass

        print "iiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiii"
        print "AttackDecaySustainRelease: A: %f, D: %f S: %f R: %f" % (attack, decay, sustain, release)
        print "iiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiii"
        self._attackLength = attack
        self._decayLength = decay
        self._sustainValue = sustain
        self._releaseLength = release
        self._attackLengthCalc = attack * self._midiTiming.getTicksPerQuarteNote()
        self._decayLengthCalc = decay * self._midiTiming.getTicksPerQuarteNote()
        self._releaseLengthCalc = release * self._midiTiming.getTicksPerQuarteNote()

        self._shape = mode

    def getValue(self, songPosition, argument):
        noteOnSPP, noteOffSPP, originalLength = argument
        if((noteOffSPP <= noteOnSPP) and (originalLength > 0.0)):
            if(songPosition < noteOnSPP):
                return 0.0
            elif((songPosition - noteOnSPP) < self._attackLengthCalc):
                return 1.0 - ((float(songPosition) - noteOnSPP) / self._attackLengthCalc)
            else:
                if(self._sustainValue >= 0.99):
                    return 0.0
                else:
                    if((songPosition - noteOnSPP - self._attackLengthCalc) <= self._decayLengthCalc):
                        return (((float(songPosition) - noteOnSPP - self._attackLengthCalc) / self._decayLengthCalc) * (1.0 - self._sustainValue))
                    else:
                        return 1.0 - self._sustainValue
        else:
            if((songPosition - noteOffSPP) <= self._releaseLengthCalc):
                return ((float(songPosition) - noteOffSPP) / self._releaseLengthCalc)
            else:
                return 1.0

    def isEqual(self, mode, attack, decay, sustain, release):
        if(self._shape == mode):
            if(self._attackLength == attack):
                if(self._decayLength == decay):
                    if(self._sustainValue == sustain):
                        if(self._releaseLength == release):
                            return True
        return False


def getAdsrShapeId(shapeName):
    if(shapeName == "ADSR"):
        return AttackDecaySustainRelease.Shape.ADSR
    elif(shapeName == "AR"):
        return AttackDecaySustainRelease.Shape.AR
    else:
        return None

class ModulationSources():
    MidiChannel, MidiNote, Lfo, ADSR = range(4)

class ModulatiobReceiver(object):
    def __init__(self, modId, name):
        self._modId = modId
        self._name = name

    def getName(self):
        return self._name

class MidiModulation(object):
    def __init__(self, configurationTree, midiTiming):
        self._tmpMidiChClass = MidiChannelStateHolder(0)
        self._tmpMidiNoteClass = NoteState()

        self._configurationTree = configurationTree
        self._midiTiming = midiTiming

        self._modulationReceivers = []
        self._activeLfos = []
        self._activeAdsrs = []

    def _getConfiguration(self):
        pass

    def checkAndUpdateFromConfiguration(self):
        if(self._configurationTree.isConfigurationUpdated()):
            print "mediaMod config is updated..."
            self._getConfiguration()
            self._configurationTree.resetConfigurationUpdated()

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
        elif( sourceSplit[0] == "LFO" ):
            if(len(sourceSplit) > 1):
                mode = getLfoShapeId(sourceSplit[1])
                if(mode != None):
                    midiLength = 4.0
                    startSPP = 0.0
                    if(len(sourceSplit) > 2):
                        newSplit = sourceDescription.split('.', 2)
                        valuesSplit = newSplit[2].split('|', 5)
                        tmpLength = float(valuesSplit[0])
                        if(tmpLength > 0.0):
                            midiLength = tmpLength
                        if(len(valuesSplit) > 1):
                            tmpSPP = float(valuesSplit[1])
                            if(tmpSPP >= 0.0):
                                startSPP = tmpSPP
                    return (ModulationSources.Lfo, self._getLfoId(mode, midiLength, startSPP))
        elif( sourceSplit[0] == "ADSR" ):
            if(len(sourceSplit) > 1):
                mode = getAdsrShapeId(sourceSplit[1])
                if(mode != None):
                    attack = 4.0
                    decay = 0.0
                    sustain = 1.0
                    release = 4.0
                    if(len(sourceSplit) > 2):
                        newSplit = sourceDescription.split('.', 2)
                        print "DEBUG " + newSplit[2]
                        valuesSplit = newSplit[2].split('|', 5)
                        print "DEBUG " + valuesSplit[0]
                        tmpAttack = float(valuesSplit[0])
                        if(tmpAttack >= 0.0):
                            attack = tmpAttack
                        if(len(valuesSplit) > 1):
                            if(mode == AttackDecaySustainRelease.Shape.AR):
                                tmpRelease = float(valuesSplit[1])
                                if(tmpRelease >= 0.0):
                                    release = tmpRelease
                            else:
                                tmpDecay = float(valuesSplit[1])
                                if(tmpDecay >= 0.0):
                                    decay = tmpDecay
                                if(len(valuesSplit) > 2):
                                    tmpSustain = float(valuesSplit[2])
                                    if(tmpSustain >= 0.0):
                                        sustain = tmpSustain
                                    if(len(valuesSplit) > 3):
                                        tmpRelease = float(valuesSplit[3])
                                        if(tmpRelease >= 0.0):
                                            release = tmpRelease
                    print "ADSR id: " + str(self._getAdsrId(mode, attack, decay, sustain, release))
                    return (ModulationSources.ADSR, self._getAdsrId(mode, attack, decay, sustain, release))
        if(sourceDescription != "None"):
            print "Invalid modulation description: \"%s\"" % sourceDescription
        return None

    def _findLfo(self, mode, midiLength, startSPP):
        for lfo in self._activeLfos:
            if(lfo.isEqual(mode, midiLength, startSPP)):
                return lfo
        return None

    def _getLfo(self, lfoConfig):
        mode, startSPP, midiLength = lfoConfig
        foundLfo = self._findLfo(mode, midiLength, startSPP)
        if(foundLfo == None):
            newLfo = LowFrequencyOscilator(self._midiTiming, mode, midiLength, startSPP)
            self._activeLfos.append(newLfo)
            return newLfo
        else:
            return foundLfo

    def _getLfoId(self, mode, midiLength = 4.0 , startSPP = 0.0):
        return (mode, midiLength, startSPP)

    def _findAdsr(self, mode, attack, decay, sustain, release):
        for adsr in self._activeAdsrs:
            if(adsr.isEqual(mode, attack, decay, sustain, release)):
                return adsr
        return None

    def _getAdsr(self, adsrConfig):
        mode, attack, decay, sustain, release = adsrConfig
        foundAdsr = self._findAdsr(mode, attack, decay, sustain, release)
        if(foundAdsr == None):
            newAdsr = AttackDecaySustainRelease(self._midiTiming, mode, attack, decay, sustain, release)
            self._activeAdsrs.append(newAdsr)
            return newAdsr
        else:
            return foundAdsr

    def _getAdsrId(self, mode, attack, decay, sustain, release):
        return (mode, attack, decay, sustain, release)

    def getModlulationValue(self, combinedId, midiChannelStateHolder, midiNoteStateHolder, songPosition, argument = 0.0, plussMinus = False):
        if(combinedId != None):
            sourceId, subId = combinedId
            if(sourceId == ModulationSources.MidiChannel):
                return midiChannelStateHolder.getModulationValue(subId, argument)
            elif(sourceId == ModulationSources.MidiNote):
                return midiNoteStateHolder.getModulationValue(subId, argument)
            elif(sourceId == ModulationSources.Lfo):
                return self._getLfo(subId).getValue(songPosition, argument)
            elif(sourceId == ModulationSources.ADSR):
                return self._getAdsr(subId).getValue(songPosition, (midiNoteStateHolder.getStartPosition(), midiNoteStateHolder.getStopPosition(), midiNoteStateHolder.getNoteLength()))
        #Return "0.0", if we don't find it.
        if(plussMinus == True):
            return 0.5
        else:
            return 0.0

    def getModlulationValueAsPlussMinus(self, combinedId, midiChannelStateHolder, midiNoteStateHolder, songPosition, argument = 0.0):
        value = self.getModlulationValue(combinedId, midiChannelStateHolder, midiNoteStateHolder, songPosition, argument, True)
        return (value * 2) - 1.0
