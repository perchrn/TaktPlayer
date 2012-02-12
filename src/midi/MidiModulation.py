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
#MidiModulation.connectModulation("PlayBack", "LFO.Triangle.4.0|0.0|0.25|0.75")
#MidiModulation.connectModulation("PlayBack", "ADSR.ADSR.4.0|0.0|1.0|4.0")
#MidiModulation.connectModulation("PlayBack", "ADSR.AR.4.0|4.0")
#MidiModulation.connectModulation("PlayBack", "None")#Always 0.0
#MidiModulation.connectModulation("PlayBack", "Value.1.0")

#MidiModulation.connectModulation("FadeInOut", "OtherMidiChannel.16.Contoller.ModWheel")
#MidiModulation.connectModulation("FadeInOut", "OtherMidiChannel.16.Note.1C.ADSR")

class LowFrequencyOscilator(object):
    def __init__(self, midiTimingClass, mode, midiLength = 4.0, startSPP = 0.0, minVal = 0.0, maxVal = 1.0):
        self._midiTiming = midiTimingClass
        self._startSongPosition = startSPP
        self._midiLength = midiLength
        self._syncLength = midiLength * self._midiTiming.getTicksPerQuarteNote()
        self._shape = mode
        self._minVal = minVal
        self._maxVal = maxVal
        self._valRange = maxVal - minVal
        random.seed(self._midiTiming.getTime())
        self._radians360 = math.radians(360)

    def getValue(self, songPosition, argument):
        if(self._shape == LfoShapes.Random):
            return self._minVal + (random.random() * self._valRange)
        else:
            phase = ((songPosition - self._startSongPosition) / self._syncLength) % 1.0
            if(self._shape == LfoShapes.Triangle):
                return self._minVal + (abs((phase * 2) - 1.0) * self._valRange)
            elif(self._shape == LfoShapes.SawTooth):
                return self._minVal + (phase * self._valRange)
            elif(self._shape == LfoShapes.Ramp):
                return self._minVal + (1.0 - phase * self._valRange)
            elif(self._shape == LfoShapes.Sine):
                return self._minVal + ((1.0 + math.sin(self._radians360 * phase)) / 2 * self._valRange)

    def isEqual(self, mode, midiLength, startSPP, minVal, maxVal):
        if(self._shape == mode):
            if(self._midiLength == midiLength):
                if(self._startSongPosition == startSPP):
                    if(self._minVal == minVal):
                        if(self._maxVal == maxVal):
                            return True
        return False

class LfoShapes():
    Triangle, SawTooth, Ramp, Sine, Random = range(5)

    def getChoices(self):
        return ["Triangle", "SawTooth", "Ramp", "Sine", "Random"]

    def getNames(self, typeId):
        for i in range(len(self.getChoices())):
            if(typeId == i):
                return self.getChoices()[i]
        return self.getChoices()[0]

def getLfoShapeId(shapeName):
    if(shapeName == "Triangle"):
        return LfoShapes.Triangle
    elif(shapeName == "SawTooth"):
        return LfoShapes.SawTooth
    elif(shapeName == "Ramp"):
        return LfoShapes.Ramp
    elif(shapeName == "Sine"):
        return LfoShapes.Sine
    elif(shapeName == "Random"):
        return LfoShapes.Random
    else:
        return None

class AdsrShapes():
    ADSR, AR = range(2)

    def getChoices(self):
        return ["ADSR", "AR"]

    def getNames(self, typeId):
        for i in range(len(self.getChoices())):
            if(typeId == i):
                return self.getChoices()[i]
        return self.getChoices()[0]

def getAdsrShapeId(shapeName):
    if(shapeName == "ADSR"):
        return AdsrShapes.ADSR
    elif(shapeName == "AR"):
        return AdsrShapes.AR
    else:
        return None


class AttackDecaySustainRelease(object):
    def __init__(self, midiTimingClass, mode, attack, decay, sustain, release):
        self._midiTiming = midiTimingClass

        self._attackLength = attack
        self._decayLength = decay
        self._sustainValue = sustain
        self._releaseLength = release
        self._attackLengthCalc = attack * self._midiTiming.getTicksPerQuarteNote()
        self._decayLengthCalc = decay * self._midiTiming.getTicksPerQuarteNote()
        self._sustainStartCalc = self._attackLengthCalc + self._decayLengthCalc
        self._releaseLengthCalc = release * self._midiTiming.getTicksPerQuarteNote()

        self._shape = mode

    def getValue(self, songPosition, argument):
        noteOnSPP, noteOffSPP, originalLength = argument
        if((originalLength < 0.001)):
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
            if((self._releaseLengthCalc > 0.0)):
                if((noteOffSPP - noteOnSPP) < self._sustainStartCalc):
                    releaseStartValue = self.getValue(noteOffSPP, (noteOnSPP, 0.0, 0.0))
                else:
                    releaseStartValue = self._sustainValue
                if((songPosition - noteOffSPP) <= self._releaseLengthCalc):
                    return (((float(songPosition) - noteOffSPP) / self._releaseLengthCalc) * releaseStartValue) + (1.0 - releaseStartValue)
            return 1.0

    def getAttackLength(self):
        return self._attackLengthCalc

    def getDecayLength(self):
        return self._decayLengthCalc

    def calculateHoldLength(self, holdLength):
        return holdLength * self._midiTiming.getTicksPerQuarteNote()

    def getReleaseLength(self):
        return self._releaseLengthCalc

    def isEqual(self, mode, attack, decay, sustain, release):
        if(self._shape == mode):
            if(self._attackLength == attack):
                if(self._decayLength == decay):
                    if(self._sustainValue == sustain):
                        if(self._releaseLength == release):
                            return True
        return False

class ModulationSources():
    NoModulation, MidiChannel, MidiNote, LFO, ADSR, Value = range(6)

    def getChoices(self):
        return ["None", "MidiChannel", "MidiNote", "LFO", "ADSR", "Value"]

    def getNames(self, typeId):
        for i in range(len(self.getChoices())):
            if(typeId == i):
                return self.getChoices()[i]
        return self.getChoices()[0]


class ModulatiobReceiver(object):
    def __init__(self, modId, name):
        self._modId = modId
        self._name = name

    def getName(self):
        return self._name

class MidiModulation(object):
    def __init__(self, configurationTree, midiTiming):
        self._tmpMidiChClass = MidiChannelStateHolder(0, None)
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
        return  self.findModulationId(sourceDescription)

    def findModulationId(self, sourceDescription):
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
                    minVal = 0.0
                    maxVal = 1.0
                    if(len(sourceSplit) > 2):
                        newSplit = sourceDescription.split('.', 2)
                        valuesSplit = newSplit[2].split('|', 5)
                        try:
                            tmpLength = float(valuesSplit[0])
                            if(tmpLength > 0.0):
                                midiLength = tmpLength
                        except:
                            pass #Keep default
                        if(len(valuesSplit) > 1):
                            try:
                                tmpSPP = float(valuesSplit[1])
                                if(tmpSPP >= 0.0):
                                    startSPP = tmpSPP * self._midiTiming.getTicksPerQuarteNote()
                            except:
                                pass #Keep default
                            if(len(valuesSplit) > 2):
                                try:
                                    tmpMin = float(valuesSplit[2])
                                    if(tmpMin >= 0.0):
                                        minVal = tmpMin
                                except:
                                    pass #Keep default
                                if(len(valuesSplit) > 3):
                                    try:
                                        tmpMax = float(valuesSplit[3])
                                        if(tmpMax >= 0.0):
                                            maxVal = tmpMax
                                    except:
                                        pass #Keep default
                    return (ModulationSources.LFO, self._getLfoId(mode, midiLength, startSPP, minVal, maxVal))
        elif( sourceSplit[0] == "Value" ):
            if(len(sourceSplit) > 1):
                newSplit = sourceDescription.split('.', 1)
                try:
                    value = float(newSplit[1])
                except:
                    value = 0.0
                value = min(max(value, 0.0), 1.0)
                return (ModulationSources.Value, value)
        elif( sourceSplit[0] == "ADSR" ):
            if(len(sourceSplit) > 1):
                mode = getAdsrShapeId(sourceSplit[1])
                if(mode != None):
                    attack = 0.0
                    decay = 0.0
                    sustain = 1.0
                    release = 0.0
                    if(len(sourceSplit) > 2):
                        newSplit = sourceDescription.split('.', 2)
                        valuesSplit = newSplit[2].split('|', 5)
                        try:
                            tmpAttack = float(valuesSplit[0])
                            if(tmpAttack >= 0.0):
                                attack = tmpAttack
                        except:
                            pass #Keep default
                        if(len(valuesSplit) > 1):
                            if(mode == AdsrShapes.AR):
                                try:
                                    tmpRelease = float(valuesSplit[1])
                                    if(tmpRelease >= 0.0):
                                        release = tmpRelease
                                except:
                                    pass #Keep default
                            else:
                                try:
                                    tmpDecay = float(valuesSplit[1])
                                    if(tmpDecay >= 0.0):
                                        decay = tmpDecay
                                except:
                                    pass #Keep default
                                if(len(valuesSplit) > 2):
                                    try:
                                        tmpSustain = float(valuesSplit[2])
                                        if(tmpSustain >= 0.0):
                                            sustain = tmpSustain
                                    except:
                                        pass #Keep default
                                if(len(valuesSplit) > 3):
                                    try:
                                        tmpRelease = float(valuesSplit[3])
                                        if(tmpRelease >= 0.0):
                                            release = tmpRelease
                                    except:
                                        pass #Keep default
                    print "ADSR id: " + str(self._getAdsrId(mode, attack, decay, sustain, release))
                    return (ModulationSources.ADSR, self._getAdsrId(mode, attack, decay, sustain, release))
        if(sourceDescription != "None"):
            print "Invalid modulation description: \"%s\"" % sourceDescription
        return None

    def _findLfo(self, mode, midiLength, startSPP, minVal, maxVal):
        for lfo in self._activeLfos:
            if(lfo.isEqual(mode, midiLength, startSPP, minVal, maxVal)):
                return lfo
        return None

    def _getLfo(self, lfoConfig):
        mode, midiLength, startSPP, minVal, maxVal = lfoConfig
        foundLfo = self._findLfo(mode, midiLength, startSPP, minVal, maxVal)
        if(foundLfo == None):
            newLfo = LowFrequencyOscilator(self._midiTiming, mode, midiLength, startSPP, minVal, maxVal)
            self._activeLfos.append(newLfo)
            return newLfo
        else:
            return foundLfo

    def _getLfoId(self, mode, midiLength = 4.0 , startSPP = 0.0, minVal = 0.0, maxVal = 1.0):
        return (mode, midiLength, startSPP, minVal, maxVal)

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
            elif(sourceId == ModulationSources.LFO):
                return self._getLfo(subId).getValue(songPosition, argument)
            elif(sourceId == ModulationSources.ADSR):
                return self._getAdsr(subId).getValue(songPosition, (midiNoteStateHolder.getStartPosition(), midiNoteStateHolder.getStopPosition(), midiNoteStateHolder.getNoteLength()))
            elif(sourceId == ModulationSources.Value):
                return subId
        #Return "0.0", if we don't find it.
        if(plussMinus == True):
            return 0.5
        else:
            return 0.0

    def getModlulationValueAsPlussMinus(self, combinedId, midiChannelStateHolder, midiNoteStateHolder, songPosition, argument = 0.0):
        value = self.getModlulationValue(combinedId, midiChannelStateHolder, midiNoteStateHolder, songPosition, argument, True)
        return (value * 2) - 1.0

    def convertToPlussMinus(self, value):
        return (value * 2) - 1.0
