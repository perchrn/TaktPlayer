'''
Created on 20. des. 2011

@author: pcn
'''
from midi import MidiUtilities

class MidiChannelStateHolder(object):
    def __init__(self, channelId):
        self._midiChannel = channelId

        #Note data:
        self._noteOn = False
        self._note = -1
        self._octav = -1
        self._noteLetter = ' '
        self._velocity = -1
        self._noteOnSPP = 0.0
        self._noteOffSPP = 0.0
        self._noteOnInSync = False
        self._noteOffInSync = False

    def noteEvent(self, noteOn, note, velocity, songPosition):
        (midiSync, spp) = songPosition
        if(noteOn == False):
            self._noteOn = False
            self._noteOffSPP = spp
            self._noteOffInSync = midiSync
        else:
            if(velocity > 0):
                self._noteOn = True
                self._noteOnSPP = spp
                self._noteOnInSync = midiSync
            else:
                #Velocity 0 is the same as note off.
                self._noteOn = False
                self._noteOffSPP = spp
                self._noteOffInSync = midiSync
        self._note = note
        (octav, noteLetter) = MidiUtilities.noteToOctavAndLetter(note)
        self._octav = octav
        self._noteLetter = noteLetter
        self._velocity = velocity
#        if(noteOn == True):
#            print "Note on: " + self._noteLetter + str(self._octav) + " vel: " + str(self._velocity) + " channel: " + str(self._midiChannel)
#        else:
#            print "Note off: " + self._noteLetter + str(self._octav) + " vel: " + str(self._velocity) + " channel: " + str(self._midiChannel)

    def printState(self):
        if(self._note > -1):
            if(self._noteOn):
                print "State: Note on: " + self._noteLetter + str(self._octav) + " vel: " + str(self._velocity) + " channel: " + str(self._midiChannel) + " OnSPP: " + str(self._noteOnSPP) + " OffSPP: " + str(self._noteOffSPP)
            else:
                print "State: Note off: " + self._noteLetter + str(self._octav) + " vel: " + str(self._velocity) + " channel: " + str(self._midiChannel) + " OnSPP: " + str(self._noteOnSPP) + " OffSPP: " + str(self._noteOffSPP)


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

    def getNoteState(self, midiChannel):
        return self._midiChannelStateHolder[midiChannel].getNoteState()

    def printState(self):
        for i in range(16):
            self._midiChannelStateHolder[i].printState()

