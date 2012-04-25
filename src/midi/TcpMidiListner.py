'''
Created on 12. des. 2011

@author: pcn
'''

import socket
import time
import logging
from utilities import MultiprocessLogger
from multiprocessing import Process, Queue
from Queue import Empty

def networkDaemon(host, port, useBroadcast, outputQueue, commandQueue, logQueue):
    processLogger = logging.getLogger('networkDaemon')
    processLogger.setLevel(logging.DEBUG)
    MultiprocessLogger.configureProcessLogger(processLogger, logQueue)
    midiSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    if(useBroadcast == True):
        midiSocket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        host = ''
    try:
        midiSocket.bind((host, port))
    except:
        processLogger.warning("Address already in use: %s:%d" % (host, port))
        #Ask process hogging port to shut down
        import ctypes
        udpClientSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        if(useBroadcast == True):
            udpClientSocket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        buffer = ctypes.create_string_buffer(6) #@ReservedAssignment
        for i in range(6): #fa-fa-fa (*2) like in Allo Allo:-P
            buffer[i] = chr(0xfa)
        if(useBroadcast == True):
            udpClientSocket.sendto(buffer, ('<broadcast>', port))
        else:
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
    def __init__(self, midiTimingClass, midiStateHolderClass, multiprocessLogger):
        #Logging etc.
        self._log = logging.getLogger('%s.%s' % (__name__, self.__class__.__name__))
        self._multiprocessLogger = multiprocessLogger

        #Daemon variables:
        self._midiListnerProcess = None
        self._midiQueue = Queue(1024)
        self._midiListnerCommandQueue = Queue(-1)
        self._conectedAddress = None

        self._midiInsideSysExMessage = False

        self._midiTiming = midiTimingClass
        self._midiStateHolder = midiStateHolderClass

    def startDaemon(self, host, port, useBroadcast):
        self._log.debug("Starting TcpMidiListner daemon")
        self._midiListnerProcess = Process(target=networkDaemon, args=(host, port, useBroadcast, self._midiQueue, self._midiListnerCommandQueue, self._multiprocessLogger.getLogQueue()))
        self._midiListnerProcess.name = "midiUdpListner"
#        self._midiListnerProcess.daemon = True
        self._midiListnerProcess.start()

    def stopDaemon(self):
        if(self._midiListnerProcess != None):
            self._midiListnerProcess.join(20.0)
            if(self._midiListnerProcess.is_alive()):
                print "TcpMidiListner did not respond to quit command. Terminating."
                self._midiListnerProcess.terminate()
            self._midiListnerProcess = None

    def requestTcpMidiListnerProcessToStop(self):
        if(self._midiListnerProcess != None):
            print "Stopping TcpMidiListner daemon"
            self._midiListnerCommandQueue.put(("QUIT", None))

    def hasTcpMidiListnerProcessToShutdownNicely(self):
        if(self._midiListnerProcess == None):
            return True
        else:
            if(self._midiListnerProcess.is_alive() == False):
                self._midiListnerProcess = None
                return True
            return False

    def forceTcpMidiListnerProcessToStop(self):
        if(self._midiListnerProcess != None):
            if(self._midiListnerProcess.is_alive()):
                print "TcpMidiListner daemon did not respond to quit command. Terminating."
                self._midiListnerProcess.terminate()
        self._midiListnerProcess = None

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
            oldSpp = self._midiTiming._updateSongPostiton(dataTimeStamp, data1, data2, data3)
            if(oldSpp != None):
                self._midiStateHolder.cleanupFutureNotes(self._midiTiming.getSongPosition(dataTimeStamp), oldSpp, self._midiTiming.getTicksPerQuarteNote())
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
            self._midiTiming._updateSongPostiton(dataTimeStamp);
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
                self._midiStateHolder.noteOff(midiChannel, data1, data2, self._midiTiming.getSongPosition(dataTimeStamp))
                #print "Note off: " + noteLetter + str(octav) + " vel: " + str(velocity) + " channel: " + str(midiChannel)
            if((command > 0x8f) and (command < 0xa0)):
                midiChannel = int(command & 0x0f)
                decodeOk = True
                self._midiStateHolder.noteOn(midiChannel, data1, data2, self._midiTiming.getSongPosition(dataTimeStamp))
            if((command > 0x9f) and (command < 0xb0)):
                midiChannel = int(command & 0x0f)
                decodeOk = True
                self._midiStateHolder.polyPreasure(midiChannel, data1, data2, self._midiTiming.getSongPosition(dataTimeStamp))
                #print "Poly preasure: " + str(data1) + " value: " + str(data2) + " channel: " + str(midiChannel)
            if((command > 0xaf) and (command < 0xc0)):
                midiChannel = int(command & 0x0f)
                decodeOk = True
                if(data3 == 0x00):
                    self._midiStateHolder.controller(midiChannel, data1, data2, self._midiTiming.getSongPosition(dataTimeStamp))
                    #print "MIDI controller: " + str(data1) + " value: " + str(data2) + " channel: " + str(midiChannel)
                else:
                    self._midiStateHolder.guiController(midiChannel, data1, data2, data3)
                    #print "GUI controller note: " + str(data1) + " value: " + str(data2) + " command: 0x%02x" % (data3)
            if((command > 0xbf) and (command < 0xd0)):
                midiChannel = int(command & 0x0f)
                decodeOk = True
                self._midiStateHolder.programChange(midiChannel, data1, data2, data3, self._midiTiming.getSongPosition(dataTimeStamp))
                #print "Program change: " + str(data1) + " value: " + str(data2) + " channel: " + str(midiChannel)
            if((command > 0xcf) and (command < 0xe0)):
                midiChannel = int(command & 0x0f)
                decodeOk = True
                self._midiStateHolder.aftertouch(midiChannel, data1, data2, self._midiTiming.getSongPosition(dataTimeStamp))
                #print "Channel pressure (aftertouch): " + str(data1) + " value: " + str(data2) + " channel: " + str(midiChannel)
            if((command > 0xdf) and (command < 0xf0)):
                midiChannel = int(command & 0x0f)
                decodeOk = True
                self._midiStateHolder.pitchBend(midiChannel, data1, data2, self._midiTiming.getSongPosition(dataTimeStamp))
                #print "Pitch bend: " + str(data1) + " value: " + str(data2) + " channel: " + str(midiChannel)
            if(decodeOk != True):
                print "Unknown message: %02x %02x %02x %02x" % (command, data1, data2, data3)

    def getData(self, clockOnly):
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
