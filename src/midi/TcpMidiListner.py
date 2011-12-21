'''
Created on 12. des. 2011

@author: pcn
'''
#@ReservedAssignment

import socket
import time
import logging
from utilities import MultiprocessLogger
from multiprocessing import Process, Queue
from Queue import Empty
from midi.MidiStateHolder import MidiStateHolder

def networkDaemon(host, port, outputQueue, commandQueue, logQueue):
#        while(True):
#            if(midiSocket)
    processLogger = logging.getLogger('networkDaemon')
    processLogger.setLevel(logging.DEBUG)
    MultiprocessLogger.configureProcessLogger(processLogger, logQueue)
    midiSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        midiSocket.bind((host, port))
    except:
        processLogger.warning("Address already in use: %s:%d" % (host, port))
        #Ask process hogging port to shut down
        import ctypes
        udpClientSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        buffer = ctypes.create_string_buffer(6)
        for i in range(6): #fa-fa-fa (*2) like in Allo Allo:-P
            buffer[i] = chr(0xfa)
        udpClientSocket.sendto(buffer, ("127.0.0.1", port))
        time.sleep(2)
        try:
            midiSocket.bind((host, port))
        except:
            processLogger.error("Address already in use and won't shut down: %s:%d" % (host, port))
            return
    midiSocket.settimeout(1.0)
    run = True
    while(run):
        try:
            data, remoteAddress = midiSocket.recvfrom(1024)
            if(len(data) == 6):
                run = False
                for i in range(6):
                    if(ord(data[i]) != 0xfa):
                        run = True
            if(run == True):
                timeStamp = time.time()
                outputQueue.put_nowait((timeStamp, remoteAddress, data))#we loose data here if program is to slow
            else:
                processLogger.warning("Got shutdown message from client!")
        except:
            pass
        try:
            command, arguments = commandQueue.get_nowait()
            if(command == "QUIT"):
                processLogger.debug("got command QUIT")
                run = False
            elif(command == "BIND"):
                host, port = arguments
                processLogger.info("got command BIND: %s:%d" % (host, port))
        except Empty:
            pass


class TcpMidiListner(object):

    def __init__(self, multiprocessLogger):
        #Daemon variables:
        self._log = logging.getLogger('%s.%s' % (__name__, self.__class__.__name__))
        self._multiprocessLogger = multiprocessLogger
        self._midiQueue = Queue(1024)
        self._midiListnerCommandQueue = Queue(-1)
        self.startDaemon('', 2020)
        self._conectedAddress = None

        #MIDI timing variables:
        self._midiOurSongPosition = 0;
        self._midiLastTimeEventWasSPP = False
#        self._midiTimeing = (4,4);
        self._midiTicksPerQuarteNote = 24
        self._midiTicksPerBar = self._midiTicksPerQuarteNote * 4
        self._midiInsideSysExMessage = False
        self._midiTicksTimestamps = [-1.0, -1.0, -1.0, -1.0, -1.0, -1.0, -1.0, -1.0, -1.0, -1.0, -1.0, -1.0, -1.0, -1.0, -1.0, -1.0,
                                     -1.0, -1.0, -1.0, -1.0, -1.0, -1.0, -1.0, -1.0, -1.0, -1.0, -1.0, -1.0, -1.0, -1.0, -1.0, -1.0,
                                     -1.0, -1.0, -1.0, -1.0, -1.0, -1.0, -1.0, -1.0, -1.0, -1.0, -1.0, -1.0, -1.0, -1.0, -1.0, -1.0,
                                     -1.0, -1.0, -1.0, -1.0, -1.0, -1.0, -1.0, -1.0, -1.0, -1.0, -1.0, -1.0, -1.0, -1.0, -1.0, -1.0,
                                     -1.0, -1.0, -1.0, -1.0, -1.0, -1.0, -1.0, -1.0, -1.0, -1.0, -1.0, -1.0, -1.0, -1.0, -1.0, -1.0,
                                     -1.0, -1.0, -1.0, -1.0, -1.0, -1.0, -1.0, -1.0, -1.0, -1.0, -1.0, -1.0, -1.0, -1.0, -1.0, -1.0]
        self._midiTicksTimestampsPos = -1
        self._midiTicksTimestampsLength = 96
        self._midiInitTime = time.time()
        self._midiBpm = 120.0
        self._midiMaxSyncBarsMissed = 16 * self._midiTicksPerQuarteNote

        self._midiStateHolder = MidiStateHolder()
        self._debug = 0

#    def __del__(self):
#        if(self._connection != None):
#            self._connection.close()
    def startDaemon(self, host, port):
        self._log.debug("Starting TcpMidiListner daemon")
        self._midiListnerProcess = Process(target=networkDaemon, args=(host, port, self._midiQueue, self._midiListnerCommandQueue, self._multiprocessLogger.getLogQueue()))
        self._midiListnerProcess.name = "midiUdpListner"
#        self._midiListnerProcess.daemon = True
        self._midiListnerProcess.start()

    def stopDaemon(self):
        self._log.debug("Stopping TcpMidiListner daemon")
        self._midiListnerCommandQueue.put(("QUIT", None))
        self._midiListnerProcess.join(10.0)

    def _calculateSubSubPos(self, timeStamp):
        midiSync = True
        subsubPos = 0.0
        if(self._midiTicksTimestampsPos > -1):
            lastTimestamp = self._midiTicksTimestamps[self._midiTicksTimestampsPos]
            deltaTime = timeStamp - lastTimestamp
            subsubPos = (self._midiTicksPerQuarteNote * deltaTime * self._midiBpm) / 60
#            print "TimeStamp: " + str(timeStamp) + "Delta: " + str(deltaTime) + " SubSubPos: " + str(subsubPos)
            if(subsubPos > self._midiTicksPerBar * self._midiMaxSyncBarsMissed):
                midiSync = False;
        else:
            midiSync = False;
            deltaTime = timeStamp - self._midiInitTime
            subsubPos = (self._midiTicksPerQuarteNote * deltaTime * self._midiBpm) / 60
        return (midiSync, subsubPos)

    def getSongPosition(self, timeStamp):
        midiSync, subsubPos = self._calculateSubSubPos(timeStamp)
        ourSongPosition = self._midiOurSongPosition + subsubPos
        return (midiSync, ourSongPosition)

    def convertToMidiPosition(self, midiSync, ourSongPosition):
        bar = int(ourSongPosition / self._midiTicksPerBar) + 1
        beat = int((ourSongPosition % self._midiTicksPerBar) / self._midiTicksPerQuarteNote) + 1
        subbeat = int(ourSongPosition % self._midiTicksPerQuarteNote) + 1
        subBeatFraction = ourSongPosition % 1.0
        return (midiSync, bar, beat, subbeat, subBeatFraction)
        
    def getMidiPosition(self, timeStamp):
        midiSync, ourSongPosition = self.getSongPosition(timeStamp)
        return self.convertToMidiPosition(midiSync, ourSongPosition)
        
    def printMidiPosition(self):
        currentTimestamp = time.time()
        midiSync, bar, beat, subbeat, subsubpos = self.getMidiPosition(currentTimestamp)
        if(midiSync):
            syncIndicator = "S "
        else:
            syncIndicator = ""
        print "%s%3d:%d:%02d.%04d BPM: %d" % (syncIndicator, bar, beat, subbeat, int(subsubpos * 10000), int(self._midiBpm))
#        print syncIndicator + str(bar) + ":" + str(beat) + ":" + str(subbeat) + ":" + str(subsubpos) + " BPM: " + str(int(self._midiBpm)) + " SPP: " + str(self._midiOurSongPosition)
        
    def _resetTimingTable(self):
        self._log.warning("Resetting timing table!")
        for i in range(96):
            self._midiTicksTimestamps[i] = -1.0
        self._midiTicksTimestampsPos = -1
        self._midiInitTime = time.time()

    def _updateSongPostiton(self, dataTimeStamp, data1 = None, data2 = None):
        if(data1 == None):
            midiSync, subsubPos = self._calculateSubSubPos(dataTimeStamp)
            if(midiSync == False and self._midiTicksTimestampsPos != -1):
                #We have missed MIDI sync and can't use our timing table anymore.
                self._resetTimingTable()
            if(self._midiLastTimeEventWasSPP == True):
                #Don't increase or calculate new position when we just got a SPP from MIDI host
                self._midiLastTimeEventWasSPP = False
            else:
                if(subsubPos > 10.0):
                    #We have skipped MIDI ticks and add calculated ticks.
                    self._log.info("Adding internal time to Song Position Pointer due to lost MIDI sync. " + str(subsubPos))
                    self._midiOurSongPosition += int(subsubPos)
                else:
                    self._midiOurSongPosition += 1
            self._midiTicksTimestampsPos = (self._midiTicksTimestampsPos + 1) % self._midiTicksTimestampsLength
            startPosTimeStamp = self._midiTicksTimestamps[self._midiTicksTimestampsPos]
            self._midiTicksTimestamps[self._midiTicksTimestampsPos] = dataTimeStamp
            if(startPosTimeStamp < 0):
                firstTimeStamp = self._midiTicksTimestamps[0]
                if(dataTimeStamp - firstTimeStamp > 0):
                    self._midiBpm = 60 * self._midiTicksTimestampsPos / (self._midiTicksPerQuarteNote * (dataTimeStamp - firstTimeStamp))
            else:
                self._midiBpm = 60 * self._midiTicksTimestampsLength / (self._midiTicksPerQuarteNote * (dataTimeStamp - startPosTimeStamp))
        else:
            sppValue = int(data1)+(int(data2 << 7))
            self._midiOurSongPosition = sppValue
            self._midiLastTimeEventWasSPP = True
            self._log.info("Got Song Position Pointer from host. SPP %d" %(self._midiOurSongPosition))
#        if((self._midiOurSongPosition % self._midiTicksPerQuarteNote) == 0):
#            self.printMidiPosition()

    def _decodeMidiEvent(self, dataTimeStamp, command, data1, data2, data3 = 0x00):
        sysexEvent = False
        if(self._midiInsideSysExMessage):
            print "inside sysex"
            sysexEvent = True
            for midiData in command, data1, data2, data3:
                if((midiData & 0x80) and (midiData < 0xf7)):
                    self._midiInsideSysExMessage = False
                    self._log.debug("SysEx message ended by a new command.")
                elif(midiData == 0xf7):
                    self._midiInsideSysExMessage = False
                    self._log.debug("SysEx message ended by a SysEx end command.")
            if(command & 0x80):
                sysexEvent = False
        if(sysexEvent):
            #Skip non commands
            return
        #Realtime Messages
        elif(command == 0xf0):
            if(data1 & 0x80 or data2 & 0x80 or data3 & 0x80):
                self._midiInsideSysExMessage = False;
            else:
                self._midiInsideSysExMessage = True;
            self._log.debug("SysEx message start!")
        elif(command == 0xf1):
            print "Time Code!"
        elif(command == 0xf2):
            self._updateSongPostiton(dataTimeStamp, data1, data2);
        elif(command == 0xf3):
            print "Song Select!"
        elif(command == 0xf4):
            print "Unknown!"
        elif(command == 0xf5):
            print "Unknown!"
        elif(command == 0xf6):
            print "Tune Request!"
        elif(command == 0xf7):
            self._midiInsideSysExMessage = False
            print "!!! SysEx end :-D"
        elif(command == 0xf8):
            self._updateSongPostiton(dataTimeStamp);
        elif(command == 0xf9):
            print "Unknown!"
        elif(command == 0xfa):
            print "Start!"
        elif(command == 0xfb):
            print "Continue!"
        elif(command == 0xfc):
            print "Stop!"
        elif(command == 0xfd):
            print "Unknown!"
        elif(command == 0xfe):
            print "Active sensing!"
        elif(command == 0xff):
            print "System reset!"
        else:
            decodeOk = False
            if((command > 0x7f) and (command < 0x90)):
                midiChannel = int(command & 0x0f)
                decodeOk = True
                self._midiStateHolder.noteOff(midiChannel, data1, data2, self.getSongPosition(dataTimeStamp))
                #print "Note off: " + noteLetter + str(octav) + " vel: " + str(velocity) + " channel: " + str(midiChannel)
            if((command > 0x8f) and (command < 0xa0)):
                midiChannel = int(command & 0x0f)
                decodeOk = True
                self._midiStateHolder.noteOn(midiChannel, data1, data2, self.getSongPosition(dataTimeStamp))
            if((command > 0x9f) and (command < 0xb0)):
                midiChannel = int(command & 0x0f)
                decodeOk = True
                self._midiStateHolder.polyPreasure(midiChannel, data1, data2, self.getSongPosition(dataTimeStamp))
                #print "Poly preasure: " + str(data1) + " value: " + str(data2) + " channel: " + str(midiChannel)
            if((command > 0xaf) and (command < 0xc0)):
                midiChannel = int(command & 0x0f)
                decodeOk = True
                self._midiStateHolder.controller(midiChannel, data1, data2, self.getSongPosition(dataTimeStamp))
                #print "Controller: " + str(data1) + " value: " + str(data2) + " channel: " + str(midiChannel)
            if((command > 0xbf) and (command < 0xd0)):
                midiChannel = int(command & 0x0f)
                decodeOk = True
                self._midiStateHolder.programChange(midiChannel, data1, data2, self.getSongPosition(dataTimeStamp))
                #print "Program change: " + str(data1) + " value: " + str(data2) + " channel: " + str(midiChannel)
            if((command > 0xcf) and (command < 0xe0)):
                midiChannel = int(command & 0x0f)
                decodeOk = True
                self._midiStateHolder.aftertouch(midiChannel, data1, data2, self.getSongPosition(dataTimeStamp))
                #print "Channel pressure (aftertouch): " + str(data1) + " value: " + str(data2) + " channel: " + str(midiChannel)
            if((command > 0xdf) and (command < 0xf0)):
                midiChannel = int(command & 0x0f)
                decodeOk = True
                self._midiStateHolder.pitchBend(midiChannel, data1, data2, self.getSongPosition(dataTimeStamp))
                #print "Pitch bend: " + str(data1) + " value: " + str(data2) + " channel: " + str(midiChannel)
            if(decodeOk != True):
                print "Unknown message: %02x %02x %02x %02x" % (command, data1, data2, data3)

    def getData(self):
#        if(self._connection == None):
#            self._connection, self._conectedAddress = self._socket.accept()
#        data = self._connection.recv(1024)
        self._debug += 1
        if(self._debug > 120):
            self._debug = 0
            self.printMidiPosition()
            self._midiStateHolder.printState()
        while(True):
            try:
                dataTimeStamp, self._conectedAddress, data = self._midiQueue.get_nowait()
#                data, self._conectedAddress = self._socket.recvfrom(1024)
            except:
                return
            if data:
                dataLen = len(data)
                if(dataLen > 8): # Midi over Ethernet header
                    headerOk = False
                    if(ord(data[0:1]) == 0x00):
                        if(ord(data[1:2]) == 0x00):
                            if(ord(data[2:3]) == 0x00):
                                if(ord(data[3:4]) == 0x00):
                                    if(ord(data[4:5]) == 0x03):
                                        if(ord(data[5:6]) == 0x00):
                                            if(ord(data[6:7]) == 0x00):
                                                if(ord(data[7:8]) == 0x00):
                                                    headerOk = True
                                    else:
                                        if(ord(data[4:5]) == 0x00):
                                            if(ord(data[5:6]) == 0x00):
                                                if(ord(data[6:7]) == 0x00):
                                                    if(ord(data[7:8]) == 0x00):
                                                        self._decodeMidiEvent(0xf8, 0x00, 0x00)
                    if(headerOk == True):
                        command = ord(data[8:9])
                        data1 = ord(data[9:10])
                        data2 = ord(data[10:11])
                        self._decodeMidiEvent(dataTimeStamp, command, data1, data2)
                else:
                    if(dataLen > 3): # MVP MIDI over net
                        command = ord(data[0:1])
                        data1 = ord(data[1:2])
                        data2 = ord(data[2:3])
                        data3 = ord(data[3:4])
                        self._decodeMidiEvent(dataTimeStamp, command, data1, data2, data3)
                    else:
                        print "Short: " + str(len(data))
            else:
                return
