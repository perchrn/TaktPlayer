'''
Created on 4. feb. 2012

@author: pcn
'''
import ctypes
import socket

class SendMidiOverNet(object):
    def __init__(self, host, port):
        self._host = host
        self._port = port
        self._midiCommandBuffer = ctypes.create_string_buffer(4) #@ReservedAssignment
        self._udpClientSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def _sendMidiData(self, command, data1, data2, data3):
        if((command > 0x7f) and (command <= 0xff)):
            data1 = min(max(0, data1), 127)
            data2 = min(max(0, data2), 127)
            data3 = min(max(0, data3), 127)
#            print "command: 0x%2x 0x%2x 0x%2x 0x%2x" % (command, data1, data2, data3)
            self._midiCommandBuffer[0] = chr(command)
            self._midiCommandBuffer[1] = chr(data1)
            self._midiCommandBuffer[2] = chr(data2)
            self._midiCommandBuffer[3] = chr(data3)
            self._udpClientSocket.sendto(self._midiCommandBuffer, (self._host, self._port))
        else:
            print "Bad command..."

    def sendNoteOn(self, midiChannel, note):
        if((midiChannel > -1) and (midiChannel < 16)):
            command = 0x90 + midiChannel
            self._sendMidiData(command, note, 0x40, 0) # Setting velocity to 0x40

    def sendNoteOff(self, midiChannel, note):
        if((midiChannel > -1) and (midiChannel < 16)):
            command = 0x80 + midiChannel
            self._sendMidiData(command, note, 0x00, 0) # Setting velocity to 0x00

    def sendNoteOnOff(self, midiChannel, note):
        if((midiChannel > -1) and (midiChannel < 16)):
            self.sendNoteOn(midiChannel, note)
            self.sendNoteOff(midiChannel, note)
        else:
            print "Bad MIDI channel: " + str(midiChannel)

    def sendMidiController(self, midiChannel, controllerId, value):
        if((midiChannel > -1) and (midiChannel < 16)):
            if((controllerId > -1) and (controllerId < 128)):
                command = 0xb0 + midiChannel
                self._sendMidiData(command, controllerId, value, 0) # Setting velocity to 0x40
            else:
                print "Bad controller id: " + str(controllerId)
        else:
            print "Bad MIDI channel: " + str(midiChannel)

    def sendPitchbend(self, midiChannel, value, subValue = 0):
        if((midiChannel > -1) and (midiChannel < 16)):
            command = 0xe0 + midiChannel
            self._sendMidiData(command, subValue, value, 0) # Setting velocity to 0x40
        else:
            print "Bad MIDI channel: " + str(midiChannel)

    def sendAftertouch(self, midiChannel, value, subValue = 0):
        if((midiChannel > -1) and (midiChannel < 16)):
            command = 0xd0 + midiChannel
            self._sendMidiData(command, value, subValue, 0) # Setting velocity to 0x40
        else:
            print "Bad MIDI channel: " + str(midiChannel)

    def sendPolyPreasure(self, midiChannel, note, value):
        if((midiChannel > -1) and (midiChannel < 16)):
            command = 0xa0 + midiChannel
            self._sendMidiData(command, note, value, 0) # Setting velocity to 0x40
        else:
            print "Bad MIDI channel: " + str(midiChannel)

