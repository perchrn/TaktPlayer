'''
Created on 21. mars 2012

@author: pcn
'''
import pygame.midi
import socket
import ctypes
import time
import logging
from multiprocessing import Process, Queue
from Queue import Empty

class MidiOverNetSender(object):
    def __init__(self):
        self._log = logging.getLogger('%s.%s' % (__name__, self.__class__.__name__))
        self._midiInputList = None
        self._midiOverNetProcess = None

    def scanInputs(self):
        pygame.midi.init()
        self._midiInputList = []
        midiDevices = pygame.midi.get_count()
        for i in range(midiDevices):
            midiSys, midiName, midiInput, midiOutput, midiOpen = pygame.midi.get_device_info(i) #@UnusedVariable
            if(midiInput == 1):
                if(midiOpen == 1):
                    midiState = "Already in use."
                else:
                    midiState = "Available."
                self._log.info("input id: %d \"%s\" %s" % (i, midiName, midiState))
                self._midiInputList.append((midiName, midiOpen, i))
            if(midiOutput == 1):
                if(midiOpen == 1):
                    midiState = "Already in use."
                else:
                    midiState = "Available."
                self._log.info("output id: %d \"%s\" %s" % (i, midiName, midiState))
        return self._midiInputList

#        self._host = "10.242.10.145"
#        self._port = 2020
    def startMidiOverNetProcess(self, inputId, host, port, guiHost, guiPort, useBroadcast, filterClock):
        if((inputId < len(self._midiInputList)) and (inputId >= 0)):
            midiName, midiOpen, pygameMidiId = self._midiInputList[inputId] #@UnusedVariable
            if(useBroadcast == True):
                host = '<broadcast>'
            clockInfo = "Sending MIDI clock."
            if(filterClock == True):
                clockInfo = "Filtering MIDI clock!"
            print "Starting MidiOverNetPorcess. From MIDI input: \"%s\" to host: %s:%d %s" %(midiName, host, port, clockInfo)
            self._midiOverNetQueue = Queue(32)
            self._statusQueue = Queue(1024)
            self._debugPrintQueue = Queue(1024)
            self._midiOverNetProcess = Process(target=midiOverNetProcess, args=(host, port, guiHost, guiPort, useBroadcast, filterClock, pygameMidiId, self._midiOverNetQueue, self._statusQueue, self._debugPrintQueue))
            self._midiOverNetProcess.name = "midiUdpSender"
            self._midiOverNetProcess.start()

    def getMidiName(self, inputId):
        if((inputId < len(self._midiInputList)) and (inputId >= 0)):
            midiName, midiOpen, pygameMidiId = self._midiInputList[inputId] #@UnusedVariable
            return midiName
        return ""

    def stopMidiOverNetProcess(self):
        if(self._midiOverNetProcess != None):
            print "Stopping midiUdpSender"
            self._midiOverNetQueue.put("QUIT")
            self._midiOverNetProcess.join(20.0)
            if(self._midiOverNetProcess.is_alive()):
                print "midiUdpSender did not respond to quit command. Terminating."
                self._midiOverNetProcess.terminate()
        self._midiOverNetProcess = None

    def getMidiStatus(self):
        run = True
        clocks = 0
        midis = 0
        daemon = 0
        if(self._midiOverNetProcess != None):
            while(run):
                try:
                    status = self._statusQueue.get_nowait()
                    if(status == 1):
                        clocks += 1
                    elif(status == 2):
                        midis += 1
                    daemon += 1
                except Empty:
                    run = False
            try:
                for i in range(512): #@UnusedVariable
                    message = self._debugPrintQueue.get_nowait()
                    print "midiOverNetProcess: " + message
            except Empty:
                pass
        return (daemon, clocks, midis)

def midiOverNetProcess(host, port, guiHost, guiPort, useBroadcast, filterClock, pygameMidiId, commandQueue, statusQueue, debugPrintQueue):
    pygame.midi.init()
    midiDevice = pygame.midi.Input(pygameMidiId)
    if(midiDevice == None):
        return
    udpClientSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    guiUdpClientSocket = None
    if(guiHost != None):
        guiUdpClientSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    if(useBroadcast == True):
        udpClientSocket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        host = '<broadcast>'
        if(guiUdpClientSocket != None):
            guiUdpClientSocket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            guiHost = '<broadcast>'
    buffer = ctypes.create_string_buffer(4) #@ReservedAssignment
    midiClicksSentSinceLastSPP = 9999
    sppValue = 0
    lastTimeEventWasSPP = True
    run = True
    while(run):
        result = midiDevice.read(1)
        if(len(result) > 0):
            midiData, timestamp = result[0] #@UnusedVariable
            command, data1, data2, data3 = midiData
            #bufferStruct.pack_into(buffer, 0, midiData)
            if(command == 0xf2):
                if(filterClock == False):
                    sppValue = (int(data1)+int(data2 << 7)) * 6
                    lastTimeEventWasSPP = True
                    statusQueue.put_nowait(1)#MIDI Time.
                    buffer[0] = chr(command)
                    buffer[1] = chr(data1)
                    buffer[2] = chr(data2)
                    buffer[3] = chr(data3)
                    udpClientSocket.sendto(buffer, (host, port))
                    if(guiUdpClientSocket != None):
                        guiUdpClientSocket.sendto(buffer, (guiHost, guiPort))
            elif(command == 0xf8):
                if(filterClock == False):
                    if(lastTimeEventWasSPP == True):
                        #Don't increase or calculate new position when we just got a SPP from MIDI host
                        lastTimeEventWasSPP = False
                        midiClicksSentSinceLastSPP = 0
                    else:
                        sppValue += 1
                        if((midiClicksSentSinceLastSPP > 95) and ((sppValue % 6) == 0)):
                            calcSpp = sppValue / 6
                            sppLsb = calcSpp & 0x7f
                            sppMsb = (calcSpp >> 7) & 0x7f
                            sppExtraBits = (calcSpp >> 14) & 0x7f
    #                        debugPrintQueue.put_nowait("Sending extra SPP: " + str(sppValue) + " calcSPP " + str(calcSpp) + " MSB: " + str(sppExtraBits) + " msb: " + str(sppMsb) + " lsb: " + str(sppLsb))
                            midiClicksSentSinceLastSPP = 0
                            buffer[0] = chr(0xf2)
                            buffer[1] = chr(sppLsb)
                            buffer[2] = chr(sppMsb)
                            buffer[3] = chr(sppExtraBits)
                            udpClientSocket.sendto(buffer, (host, port))
                            if(guiUdpClientSocket != None):
                                guiUdpClientSocket.sendto(buffer, (guiHost, guiPort))
                        else:
                            midiClicksSentSinceLastSPP += 1
                    buffer[0] = chr(command)
                    buffer[1] = chr(data1)
                    buffer[2] = chr(data2)
                    buffer[3] = chr(data3)
                    udpClientSocket.sendto(buffer, (host, port))
                    if(guiUdpClientSocket != None):
                        guiUdpClientSocket.sendto(buffer, (guiHost, guiPort))
                    statusQueue.put_nowait(1)#MIDI Time.
            else:
                buffer[0] = chr(command)
                buffer[1] = chr(data1)
                buffer[2] = chr(data2)
                buffer[3] = chr(data3)
                udpClientSocket.sendto(buffer, (host, port))
                if(guiUdpClientSocket != None):
                    guiUdpClientSocket.sendto(buffer, (guiHost, guiPort))
                if(command != 0xf8):
#                    debugPrintQueue.put_nowait("%02x %02x %02x %02x - %f - %f" % (command, data1, data2, data3, time.time(), timestamp / 1000.0))
                    statusQueue.put_nowait(2)#Other MIDI
            try:
                command = commandQueue.get_nowait()
                if(command == "QUIT"):
                    run = False
            except Empty:
                pass
        else:
            try:
                command = commandQueue.get_nowait()
                if(command == "QUIT"):
                    run = False
            except Empty:
                pass
            statusQueue.put_nowait(0)#No MIDI
            time.sleep(0.005)

