'''
Created on 9. jan. 2012

@author: pcn
'''
import random
import math
from midi.MidiStateHolder import MidiChannelStateHolder, NoteState,\
    MidiChannelModulationSources, NoteModulationSources
from midi.MidiController import MidiControllers

# Modulation ideas:
#MidiModulation.connectModulation("FadeInOut", "OtherMidiChannel.16.Contoller.ModWheel")
#MidiModulation.connectModulation("FadeInOut", "OtherMidiChannel.16.Note.1C.ADSR")

class LowFrequencyOscilator(object):
    def __init__(self, midiTimingClass, mode, midiLength = 4.0, startBeat = 0.0, minVal = 0.0, maxVal = 1.0):
        self._midiTiming = midiTimingClass
        self._startSongPosition = startBeat * self._midiTiming.getTicksPerQuarteNote()
        self._midiLength = midiLength
        self._syncLength = midiLength * self._midiTiming.getTicksPerQuarteNote()
        if(self._syncLength < 0.001):
            self._syncLength = 0.001
        self._shape = mode
        self._minVal = minVal
        self._maxVal = maxVal
        self._valRange = maxVal - minVal
        random.seed(self._midiTiming.getTime())
        self._radians360 = math.radians(360)
        self._lastRandomId = -1
        self._lastRandomValue = 0.0

    def getValue(self, songPosition, argument):
        if(self._shape == LfoShapes.Random):
            randomId = int((songPosition - self._startSongPosition) / self._syncLength)
            if(randomId != self._lastRandomId):
                self._lastRandomId = randomId
                self._lastRandomValue = self._minVal + (random.random() * self._valRange)
            return self._lastRandomValue
        else:
            phase = ((songPosition - self._startSongPosition) / self._syncLength) % 1.0
            if(self._shape == LfoShapes.Triangle):
                return self._minVal + (abs((phase * 2) - 1.0) * self._valRange)
            elif(self._shape == LfoShapes.SawTooth):
                return self._minVal + (phase * self._valRange)
            elif(self._shape == LfoShapes.Ramp):
                return self._minVal + ((1.0 - phase) * self._valRange)
            elif(self._shape == LfoShapes.Sine):
                return self._minVal + ((1.0 + math.sin(self._radians360 * phase)) / 2 * self._valRange)
            elif(self._shape == LfoShapes.Square):
                if(phase < 0.5):
                    return self._maxVal
                else:
                    return self._minVal

    def isEqual(self, mode, midiLength, startSPP, minVal, maxVal):
        if(self._shape == mode):
            if(self._midiLength == midiLength):
                if(self._startSongPosition == startSPP):
                    if(self._minVal == minVal):
                        if(self._maxVal == maxVal):
                            return True
        return False

    def calculateLength(self, length):
        return length * self._midiTiming.getTicksPerQuarteNote()


class LfoShapes():
    Triangle, SawTooth, Ramp, Sine, Square, Random = range(6)

    def getChoices(self):
        return ["Triangle", "SawTooth", "Ramp", "Sine", "Square", "Random"]

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
    elif(shapeName == "Square"):
        return LfoShapes.Square
    elif(shapeName == "Random"):
        return LfoShapes.Random
    else:
        return None

class DmxTypes():
    Direct, Channel = range(2)

    def getChoices(self):
        return ["Direct", "Channel"]

    def getNames(self, typeId):
        for i in range(len(self.getChoices())):
            if(typeId == i):
                return self.getChoices()[i]
        return self.getChoices()[0]

def getDmxTypeId(typeName):
    if(typeName == "Direct"):
        return DmxTypes.Direct
    elif(typeName == "Channel"):
        return DmxTypes.Channel
    else:
        return None

class AdsrShapes():
    ADSR, AR = range(2)#TODO: Add curved attack release... (for fades)

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
    def __init__(self, midiTimingClass, mode, attack, decay, sustain, release, minVal, maxVal):
        self._midiTiming = midiTimingClass
        self._shape = mode

        self._attackLength = attack
        if(self._shape == AdsrShapes.ADSR):
            self._decayLength = decay
            self._sustainValue = sustain
        else:
            self._decayLength = 0.0
            self._sustainValue = 1.0
        self._releaseLength = release
        self._minVal = minVal
        self._maxVal = maxVal
        self._valRange = maxVal - minVal

        self._attackLengthCalc = attack * self._midiTiming.getTicksPerQuarteNote()
        self._decayLengthCalc = decay * self._midiTiming.getTicksPerQuarteNote()
        self._sustainStartCalc = self._attackLengthCalc + self._decayLengthCalc
        self._releaseLengthCalc = release * self._midiTiming.getTicksPerQuarteNote()
        self._postReleaseLengthCalc = self._releaseLengthCalc + (16.0 * self._midiTiming.getTicksPerQuarteNote())

    def getValue(self, songPosition, argument):
        noteOnSPP, noteOffSPP, originalLength = argument
        if((originalLength < 0.0001)):
            if(songPosition < noteOnSPP):
                returnValue = 0.0
            elif((songPosition - noteOnSPP) < self._attackLengthCalc):
                returnValue = 1.0 - ((float(songPosition) - noteOnSPP) / self._attackLengthCalc)
            else:
                if(self._sustainValue >= 0.99):
                    returnValue = 0.0
                else:
                    if((songPosition - noteOnSPP - self._attackLengthCalc) < self._decayLengthCalc):
                        returnValue = (((float(songPosition) - noteOnSPP - self._attackLengthCalc) / self._decayLengthCalc) * (1.0 - self._sustainValue))
                    else:
                        returnValue = 1.0 - self._sustainValue
        else:
            #print "ADSR: originalLength " + str(originalLength)+ " self._releaseLengthCalc " + str(self._releaseLengthCalc)
            if((self._releaseLengthCalc > 0.0)):
                if((noteOffSPP - noteOnSPP) < self._sustainStartCalc):
                    releaseStartValue = self.getValue(noteOffSPP, (noteOnSPP, 0.0, 0.0))
                else:
                    releaseStartValue = self._sustainValue
                if((songPosition - noteOffSPP) <= self._releaseLengthCalc):
                    returnValue = (((float(songPosition) - noteOffSPP) / self._releaseLengthCalc) * releaseStartValue) + (1.0 - releaseStartValue)
                    if((returnValue == 0.0) and (songPosition - noteOffSPP) <= self._postReleaseLengthCalc):
                        returnValue = 0.00001
                else:
                    returnValue = 1.0
            else:
                returnValue = 1.0
        if(self._minVal > 0.001 or self._maxVal < 0.999):
            returnValue = self._minVal + (returnValue * self._valRange)
        return returnValue

    def getAttackLength(self):
        return self._attackLengthCalc

    def getDecayLength(self):
        return self._decayLengthCalc

    def calculateHoldLength(self, holdLength):
        return holdLength * self._midiTiming.getTicksPerQuarteNote()

    def getReleaseLength(self):
        return self._releaseLengthCalc

    def isEqual(self, mode, attack, decay, sustain, release, minValue, maxValue):
        if(self._shape == mode):
            if(self._attackLength == attack):
                if(self._decayLength == decay):
                    if(self._sustainValue == sustain):
                        if(self._releaseLength == release):
                            if(self._minVal == minValue):
                                if(self._maxVal == maxValue):
                                    return True
        return False

class ModulationSources():
    NoModulation, MidiChannel, MidiNote, DMX512, LFO, ADSR, Value, Special = range(8)

    def getChoices(self, dmxEnabled = True):
        if(dmxEnabled == True):
            return ["None", "MidiChannel", "MidiNote", "DMX", "LFO", "ADSR", "Value", "Special"]
        else:
            return ["None", "MidiChannel", "MidiNote", "LFO", "ADSR", "Value", "Special"]

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
    def __init__(self, configurationTree, midiTiming, specialHolder):
        self._tmpMidiChClass = MidiChannelStateHolder(0, None)
        self._tmpMidiNoteClass = NoteState(0)

        self._configurationTree = configurationTree
        self._midiTiming = midiTiming
        self._specialModulationHolder = specialHolder

        self._modulationReceivers = []
        self._activeLfos = []
        self._activeAdsrs = []

    def _getConfiguration(self):
        pass

    def checkAndUpdateFromConfiguration(self):
        if(self._configurationTree.isConfigurationUpdated()):
            #print "mediaMod config is updated..."
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

    def setValue(self, name, value):
        self._configurationTree.setValue(name, value)

    def connectModulation(self, receiverName):
        receiver = self.findReceiver(receiverName)
        if(receiver == None):
            print "Unregistered receiver \"%s\"" % receiverName
            return None
        sourceDescription = self._configurationTree.getValue(receiverName)
        return self.findModulationId(sourceDescription)

    def findModulationId(self, sourceDescription):
        if(sourceDescription == None):
            sourceDescription = "None"
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
        elif( sourceSplit[0] == "DMX" ):
            if(len(sourceSplit) > 1):
                mode = getDmxTypeId(sourceSplit[1])
            else:
                mode = None
            if(mode != None):
                if(len(sourceSplit) > 2):
                    value = int(sourceSplit[2])
                else:
                    value = 0
                return (ModulationSources.DMX512, (mode, value))
        elif( sourceSplit[0] == "LFO" ):
            if(len(sourceSplit) > 1):
                mode = getLfoShapeId(sourceSplit[1])
                if(mode != None):
                    midiLength = 4.0
                    if(mode == LfoShapes.Random):
                        midiLength = 0.0
                    startBeat = 0.0
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
                                tmpStartBeat = float(valuesSplit[1])
                                if(tmpStartBeat >= 0.0):
                                    startBeat = tmpStartBeat
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
                    return (ModulationSources.LFO, self._getLfoId(mode, midiLength, startBeat, minVal, maxVal))
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
                    minValue = 0.0
                    maxValue = 1.0
                    if(len(sourceSplit) > 2):
                        newSplit = sourceDescription.split('.', 2)
                        valuesSplit = newSplit[2].split('|', 7)
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
                                if(len(valuesSplit) > 4):
                                    try:
                                        tmpMin = float(valuesSplit[4])
                                        if(tmpMin >= 0.0):
                                            minValue = tmpMin
                                    except:
                                        pass #Keep default
                                if(len(valuesSplit) > 5):
                                    try:
                                        tmpMax = float(valuesSplit[5])
                                        if(tmpMax >= 0.0):
                                            maxValue = tmpMax
                                    except:
                                        pass #Keep default
                    #print "ADSR id: " + str(self._getAdsrId(mode, attack, decay, sustain, release))
                    return (ModulationSources.ADSR, self._getAdsrId(mode, attack, decay, sustain, release, minValue, maxValue))
        elif( sourceSplit[0] == "Special" ):
            restId = sourceDescription.split("Special.")[1]
            return (ModulationSources.Special, self._specialModulationHolder.getModulationId(restId))
        if(sourceDescription != "None"):
            print "Invalid modulation description: \"%s\"" % sourceDescription
        return None

    def getStringFromId(self, modulationId):
        modulationSource, subModId = modulationId
        if(modulationSource == ModulationSources.MidiChannel):
            returnString = "MidiChannel"
            isInt = isinstance(subModId, int)
            if((isInt == False) and (len(subModId) == 2)):
                if(subModId[0] == MidiChannelModulationSources.Controller):
                    midiControllers = MidiControllers()
                    controllerName = midiControllers.getName(subModId[1])
                    returnString += ".Controller." + controllerName
            else:
                if(subModId == MidiChannelModulationSources.Controller):
                    returnString += ".Controller.ModWheel"
                else:
                    midiChannelModulationSources = MidiChannelModulationSources()
                    channelSourceName = midiChannelModulationSources.getNames(subModId)
                    returnString += "." + channelSourceName
        elif(modulationSource == ModulationSources.MidiNote):
            returnString = "MidiNote"
            isInt = isinstance(subModId, int)
            if(isInt == False):
                subModId = subModId[0]
            noteModulationSources = NoteModulationSources()
            subModeName = noteModulationSources.getNames(subModId)
            returnString += "." + subModeName
        elif(modulationSource == ModulationSources.DMX512):
            returnString = "DMX"
            isInt = isinstance(subModId, int)
            if(isInt == True):
                subModId = [subModId]
            dmxTypes = DmxTypes()
            subModeName = dmxTypes.getNames(subModId[0])
            returnString += "." + subModeName
            if(len(subModId) > 1):
                value = int(subModId[1])
            else:
                value = 0
            returnString += "." + str(value)
        elif(modulationSource == ModulationSources.LFO):
            returnString = "LFO"
            isInt = isinstance(subModId, int)
            if(isInt == True):
                subModId = [subModId]
            lfoTypes = LfoShapes()
            subModName = lfoTypes.getNames(subModId[0])
            returnString += "." + subModName
            if(len(subModId) > 1):
                returnString += "." + str(subModId[1])
            else:
                returnString += ".4.0"
            if(len(subModId) > 2):
                returnString += "|" + str(subModId[2])
            else:
                returnString += "|0.0"
            if(len(subModId) > 3):
                returnString += "|" + str(subModId[3])
            else:
                returnString += "|0.0"
            if(len(subModId) > 4):
                returnString += "|" + str(subModId[4])
            else:
                returnString += "|1.0"
        elif(modulationSource == ModulationSources.ADSR):
            returnString = "ADSR"
            isInt = isinstance(subModId, int)
            if(isInt == True):
                subModId = [subModId]
            adsrType = AdsrShapes()
            subModName = adsrType.getNames(subModId[0])
            returnString += "." + subModName
            if(len(subModId) > 1):
                returnString += "." + str(subModId[1])
            else:
                returnString += ".0.0"
            if(subModId[0] == adsrType.AR):
                if(len(subModId) > 4):
                    returnString += "|" + str(subModId[4])
                else:
                    returnString += "|0.0"
            else:
                if(len(subModId) > 2):
                    returnString += "|" + str(subModId[2])
                else:
                    returnString += "|0.0"
                if(len(subModId) > 3):
                    returnString += "|" + str(subModId[3])
                else:
                    returnString += "|1.0"
                if(len(subModId) > 4):
                    returnString += "|" + str(subModId[4])
                else:
                    returnString += "|0.0"
                if(len(subModId) > 5):
                    returnString += "|" + str(subModId[5])
                else:
                    returnString += "|0.0"
                if(len(subModId) > 6):
                    returnString += "|" + str(subModId[6])
                else:
                    returnString += "|1.0"
        elif(modulationSource == ModulationSources.Value):
            returnString = "Value"
            isFloat = isinstance(subModId, float)
            if(isFloat != True):
                subModId = subModId[0]
            returnString += "." + str(subModId)
        elif(modulationSource == ModulationSources.Special):
            returnString = "Special"
            returnString += "." + self._specialModulationHolder.getSubModString(subModId)
        else:
            returnString = "None"
        return returnString

    def validateModulationString(self, string):
        modulationId = self.findModulationId(string)
        if(modulationId == None):
            return "None"
        else:
            newString = self.getStringFromId(modulationId)
            return newString

    def _findLfo(self, mode, midiLength, startBeat, minVal, maxVal):
        for lfo in self._activeLfos:
            if(lfo.isEqual(mode, midiLength, startBeat, minVal, maxVal)):
                return lfo
        return None

    def _getLfo(self, lfoConfig):
        mode, midiLength, startBeat, minVal, maxVal = lfoConfig
        foundLfo = self._findLfo(mode, midiLength, startBeat, minVal, maxVal)
        if(foundLfo == None):
            newLfo = LowFrequencyOscilator(self._midiTiming, mode, midiLength, startBeat, minVal, maxVal)
            self._activeLfos.append(newLfo)
            return newLfo
        else:
            return foundLfo

    def _getLfoId(self, mode, midiLength = 4.0 , startSPP = 0.0, minVal = 0.0, maxVal = 1.0):
        return (mode, midiLength, startSPP, minVal, maxVal)

    def _findAdsr(self, mode, attack, decay, sustain, release, minValue, maxValue):
        for adsr in self._activeAdsrs:
            if(adsr.isEqual(mode, attack, decay, sustain, release, minValue, maxValue)):
                return adsr
        return None

    def _getAdsr(self, adsrConfig):
        mode, attack, decay, sustain, release, minValue, maxValue = adsrConfig
        foundAdsr = self._findAdsr(mode, attack, decay, sustain, release, minValue, maxValue)
        if(foundAdsr == None):
            newAdsr = AttackDecaySustainRelease(self._midiTiming, mode, attack, decay, sustain, release, minValue, maxValue)
            self._activeAdsrs.append(newAdsr)
            return newAdsr
        else:
            return foundAdsr

    def _getAdsrId(self, mode, attack, decay, sustain, release, minValue, maxValue):
        return (mode, attack, decay, sustain, release, minValue, maxValue)

    def getModlulationValue(self, combinedId, midiChannelStateHolder, midiNoteStateHolder, dmxStateHolder, songPosition, specialModulationHolder, argument = 0.0, plussMinus = False):
        if(combinedId != None):
            sourceId, subId = combinedId
            if(sourceId == ModulationSources.MidiChannel):
                return midiChannelStateHolder.getModulationValue(subId, argument)
            elif(sourceId == ModulationSources.MidiNote):
                return midiNoteStateHolder.getModulationValue(subId, argument)
            elif(sourceId == ModulationSources.DMX512):
                if(dmxStateHolder == None):
                    return 0.0
                midiChannel = None
                if(subId[0] == DmxTypes.Channel):
                    midiChannel = midiChannelStateHolder.getMidiChannel() - 1
                return dmxStateHolder.getValue(subId[1], midiChannel)
            elif(sourceId == ModulationSources.LFO):
                return self._getLfo(subId).getValue(songPosition, argument)
            elif(sourceId == ModulationSources.ADSR):
                return self._getAdsr(subId).getValue(songPosition, (midiNoteStateHolder.getStartPosition(), midiNoteStateHolder.getStopPosition(), midiNoteStateHolder.getNoteLength()))
            elif(sourceId == ModulationSources.Value):
                return subId
            elif(sourceId == ModulationSources.Special):
                #print "DEBUG pcn: getModulationValue(Special, " + str(subId) + ") " + str(specialModulationHolder.getValue(subId))
                return specialModulationHolder.getValue(subId)
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
