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
    
    def sendNoteOn(self, midiChannel, note):
        command = 0x80 + midiChannel
        data1 = note
        data2 = 0x40 # Velocity
        data3 = 0x00
        self._midiCommandBuffer[0] = chr(command)
        self._midiCommandBuffer[1] = chr(data1)
        self._midiCommandBuffer[2] = chr(data2)
        self._midiCommandBuffer[3] = chr(data3)
        self._udpClientSocket.sendto(self._midiCommandBuffer, (self._host, self._port))

    def sendNoteOff(self, midiChannel, note):
        command = 0x90 + midiChannel
        data1 = note
        data2 = 0x40 # Velocity
        data3 = 0x00
        self._midiCommandBuffer[0] = chr(command)
        self._midiCommandBuffer[1] = chr(data1)
        self._midiCommandBuffer[2] = chr(data2)
        self._midiCommandBuffer[3] = chr(data3)
        self._udpClientSocket.sendto(self._midiCommandBuffer, (self._host, self._port))

    def sendNoteOnOff(self, midiChannel, note):
        self.sendNoteOn(midiChannel, note)
        self.sendNoteOff(midiChannel, note)

