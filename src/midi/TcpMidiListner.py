'''
Created on 12. des. 2011

@author: pcn
'''

import socket
import time
from multiprocessing import Process, Queue
from Queue import Empty
import traceback
from midi.MidiStateHolder import quantizePosition
from midi.MidiUtilities import noteToOctavAndLetter
import os

def networkDaemon(host, port, useBroadcast, outputQueue, commandQueue, logQueue):
    midiSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    if(useBroadcast == True):
        midiSocket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        host = ''
#    else:
#        processLogger.error("DEBUG pcn: Setting up multicast for: %s:%d" % (host, port))
#        midiSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
#        mcastAddress = host
#        host = ''
    try:
        midiSocket.bind((host, port))
    except:
        logQueue.put_nowait("Address already in use: %s:%d" % (host, port))
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
            logQueue.put_nowait("Address already in use and won't shut down: %s:%d" % (host, port))
            return
#    if(useBroadcast == False):
#        mreq = struct.pack("4sl", socket.inet_aton(mcastAddress), socket.INADDR_ANY)        
#        midiSocket.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
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
                logQueue.put_nowait("Got shutdown message from client!")
        except:
            pass
        try:
            command, arguments = commandQueue.get_nowait()
            if(command == "QUIT"):
                logQueue.put_nowait("got command QUIT")
                run = False
            elif(command == "BIND"):
                host, port = arguments
                logQueue.put_nowait("got command BIND: %s:%d" % (host, port))
        except Empty:
            pass


class TcpMidiListner(object):
    def __init__(self, midiTimingClass, midiStateHolderClass, configLoadCallback = None, eventLogSaveQueue = None):
        #Logging etc.
        self._configLoadCallback = configLoadCallback
        self._eventLogSaveQueue = eventLogSaveQueue

        #Daemon variables:
        self._midiListnerProcess = None
        self._midiQueue = Queue(1024)
        self._midiListnerCommandQueue = Queue(-1)
        self._midiListnerPrintQueue = Queue(1024)
        self._conectedAddress = None

        self._midiInsideSysExMessage = False

        self._midiTiming = midiTimingClass
        self._midiStateHolder = midiStateHolderClass

    def startDaemon(self, host, port, useBroadcast):
        print "Starting TcpMidiListner daemon"
        self._midiListnerProcess = Process(target=networkDaemon, args=(host, port, useBroadcast, self._midiQueue, self._midiListnerCommandQueue, self._midiListnerPrintQueue))
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

    def _addEventToSaveLog(self, string):
        if(self._eventLogSaveQueue != None):
            try:
                self._eventLogSaveQueue.put_nowait(string + "\n")
            except:
                pass

    def _decodeMidiEvent(self, dataTimeStamp, command, data1, data2, data3 = 0x00):
        isMidiNote = False
        sysexEvent = False
        if(self._midiInsideSysExMessage):
            print "inside sysex"
            sysexEvent = True
            for midiData in command, data1, data2, data3:
                if((midiData & 0x80) and (midiData < 0xf7)):
                    self._midiInsideSysExMessage = False
                    print "SysEx message ended by a new command."
                elif(midiData == 0xf7):
                    self._midiInsideSysExMessage = False
                    print "SysEx message ended by a SysEx end command."
            if(command & 0x80):
                sysexEvent = False
        if(sysexEvent):
            #Skip non commands
            return isMidiNote
        #Realtime Messages
        elif(command == 0xf0):
            if(data1 & 0x80 or data2 & 0x80 or data3 & 0x80):
                self._midiInsideSysExMessage = False;
            else:
                self._midiInsideSysExMessage = True;
            print "SysEx message start!"
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
                isMidiNote = True
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
        return isMidiNote

    def getData(self, clockOnly):
        try:
            printString = self._midiListnerPrintQueue.get_nowait()
            print printString
        except:
            pass
        gotMidiNote = False
        while(True):
            try:
                dataTimeStamp, self._conectedAddress, data = self._midiQueue.get_nowait()
#                data, self._conectedAddress = self._socket.recvfrom(1024)
            except:
                return gotMidiNote
            if data:
                dataLen = len(data)
#                if(dataLen > 8): # Midi over Ethernet header
#                    headerOk = False
#                    if(ord(data[0:1]) == 0x00):
#                        if(ord(data[1:2]) == 0x00):
#                            if(ord(data[2:3]) == 0x00):
#                                if(ord(data[3:4]) == 0x00):
#                                    if(ord(data[4:5]) == 0x03):
#                                        if(ord(data[5:6]) == 0x00):
#                                            if(ord(data[6:7]) == 0x00):
#                                                if(ord(data[7:8]) == 0x00):
#                                                    headerOk = True
#                                    else:
#                                        if(ord(data[4:5]) == 0x00):
#                                            if(ord(data[5:6]) == 0x00):
#                                                if(ord(data[6:7]) == 0x00):
#                                                    if(ord(data[7:8]) == 0x00):
#                                                        self._decodeMidiEvent(0xf8, 0x00, 0x00)
#                    if(headerOk == True):
#                        command = ord(data[8:9])
#                        data1 = ord(data[9:10])
#                        data2 = ord(data[10:11])
#                        self._decodeMidiEvent(dataTimeStamp, command, data1, data2)
                if(dataLen > 8): # VST timing or programName over net!
                    if(str(data).startswith("vstTime|")):
                        vstTimeSplit = str(data).split("|")
                        if(len(vstTimeSplit) == 3):
                            posVal = float(vstTimeSplit[1])
#                            print "t," + str(posVal*24),
                            tempoVal = float(vstTimeSplit[2])
                            returnValue = self._midiTiming._updateFromVstTiming(dataTimeStamp, posVal, tempoVal);
                            if(returnValue != None):
                                stopedState, oldSpp, newSpp = returnValue
                                if(stopedState == True): # Clear all on restart
                                    self._midiStateHolder.cleanupFutureNotes(0.0, oldSpp, self._midiTiming.getTicksPerQuarteNote())
                                else:
                                    if(newSpp < oldSpp): # Looping back (else it is just a jump and we do nothing.)
                                        self._midiStateHolder.fixLoopingNotes(oldSpp, newSpp, self._midiTiming.getTicksPerQuarteNote())
                            self._addEventToSaveLog(str(dataTimeStamp) + "|" + str(data))
                    if(str(data).startswith("loadProgram|")):
                        programSplit = str(data).split("|")
                        if(len(programSplit) == 2):
                            programName = programSplit[1]
                            self._addEventToSaveLog(str(dataTimeStamp) + "|" + str(data))
                            if(self._configLoadCallback != None):
                                xmlString = self._configLoadCallback(programName)
                                self._addEventToSaveLog(xmlString)
                            self._addEventToSaveLog(str(dataTimeStamp) + "|" + str(data) + "|Done")
                else:
                    if(dataLen > 3): # MVP MIDI over net
                        command = ord(data[0:1])
                        data1 = ord(data[1:2])
                        data2 = ord(data[2:3])
                        data3 = ord(data[3:4])
                        isMidiNote = self._decodeMidiEvent(dataTimeStamp, command, data1, data2, data3)
                        if(isMidiNote == True):
                            gotMidiNote = True
                        self._addEventToSaveLog(str(dataTimeStamp) + "|MIDI|%02x|%02x|%02x|%02x"%(command, data1, data2, data3))
                    else:
                        print "Short: " + str(len(data))
            else:
                return gotMidiNote

class RenderFileReader(TcpMidiListner):
    def __init__(self, midiTimingClass, midiStateHolderClass, configLoadCallback):
        TcpMidiListner.__init__(self, midiTimingClass, midiStateHolderClass, configLoadCallback, eventLogSaveQueue=None)
        self._eventLogFileHandle = None
        self._renderFileOutputName = None
        self._loadConfigFileName = None
        self._quantizeValue = 1.0 * self._midiTiming.getTicksPerQuarteNote()
        self._nextLine = None
        self._nextTimeStamp = 0.0
        self._startRecordingTime = -1.0
        self._eventLogFileHandle = None
        self._slowStop = False

    def openFile(self, renderFileName):
        try:
            self._eventLogFileHandle = open(renderFileName, 'r')
            self._findStartLine()
        except:
            print "Error opening render file with file name: " + str(renderFileName)
            traceback.print_exc()
            self._eventLogFileHandle = None

    def startDaemon(self, host, port, useBroadcast):
        pass

    def requestTcpMidiListnerProcessToStop(self):
        self._nextLine = None

    def hasTcpMidiListnerProcessToShutdownNicely(self):
        if(self._slowStop == True):
            return False
        return True

    def forceTcpMidiListnerProcessToStop(self):
        self._nextLine = None

    def endIsReached(self):
        if(self._nextLine == None):
            return True
        return False

    def getStartTime(self):
        return self._startRecordingTime

    def getOutputFileName(self):
        return self._renderFileOutputName

    def _findStartLine(self):
        stop = False
        startFound = False
        while(stop == False):
            try:
                currentLine = self._eventLogFileHandle.readline()
                if not currentLine:
                    break
            except:
                break
            currentLineSplit = currentLine.split('|')
            if(len(currentLineSplit) > 1):
                self._loadConfig(currentLineSplit)
                if(currentLineSplit[1].lower() == "startrecording"):
                    if(len(currentLineSplit) > 2):
                        self._renderFileOutputName = currentLineSplit[2].split('\n')[0]
                    currentTimeStamp = float(currentLineSplit[0])
                    self._startRecordingTime = currentTimeStamp
                    startFound = True
                    stop = True
                    print "StartRecording tag found at: " + str(currentLineSplit[0])
        if(startFound == False):
            self._eventLogFileHandle.seek(0)
            print "Warning no StartRecording tag found!!!"
            stop = False
            configIsLoaded = False
            vstBlockSeekPos = -1
            vstBlockTimeStamp = 0.0
            tmpBlockPos = -1
            tmpBlockTimeStamp = 0.0
            while(stop == False):
                try:
                    currentPos = self._eventLogFileHandle.tell()
                    currentLine = self._eventLogFileHandle.readline()
                    if not currentLine:
                        break
                except:
                    break
                currentLineSplit = currentLine.split('|')
                if(len(currentLineSplit) > 1):
                    loadedConfig = self._loadConfig(currentLineSplit)
                    if(loadedConfig == True):
                        configIsLoaded = True
                    if(configIsLoaded):
                        currentTimeStamp = float(currentLineSplit[0])
                        if(currentTimeStamp > tmpBlockTimeStamp):
                            tmpBlockPos = currentPos
                            tmpBlockTimeStamp = currentTimeStamp
                        if(currentLineSplit[1].lower() == "vsttime"):
                            if(len(currentLineSplit) > 2):
                                vstTimeStamp = float(currentLineSplit[2])
                                if((vstTimeStamp % 1.0) == 0.0):
                                    vstBlockSeekPos = tmpBlockPos
                                    vstBlockTimeStamp = tmpBlockTimeStamp
                                else:
                                    if(vstBlockSeekPos > -1):
                                        self._eventLogFileHandle.seek(vstBlockSeekPos)
                                        self._startRecordingTime = vstBlockTimeStamp
                                        startFound = True
                                        stop = True
            if(startFound == True):
                baseLoadName = os.path.basename(self._loadConfigFileName)
                if(baseLoadName.endswith(".cfg")):
                    self._renderFileOutputName = baseLoadName[0:(len(baseLoadName)-4)]
                else:
                    self._renderFileOutputName = baseLoadName
            else:
                self._nextLine = None
        if(startFound == True):
            self._nextLine = self._eventLogFileHandle.readline()
            print "S"*120
            print "Starting on line: " + self._nextLine.split('\n')[0]
            print "S"*120
            if not self._nextLine:
                self._nextLine = None
            else:
                if(len(currentLineSplit) > 1):
                    currentTimeStamp = float(currentLineSplit[0])
                    _, currentMidiTimeStamp = self._midiTiming.getSongPosition(currentTimeStamp)
                    if(currentLineSplit[1].lower() == "midi"):
                        currentMidiTimeStamp = quantizePosition(currentMidiTimeStamp, self._quantizeValue)
                    self._nextTimeStamp = currentMidiTimeStamp
                else:
                    self._nextLine = None

    def _loadConfig(self, currentLineSplit):
        loadStartOk = False
        if(currentLineSplit[1].lower() == "loadprogram"):
            if(len(currentLineSplit) > 2):
                if(currentLineSplit[2] != "Done"):
                    loadStartOk = True
                    self._loadConfigFileName = currentLineSplit[2].split('\n')[0]
        configString = ""
        if(loadStartOk == True):
            stop = False
            while(stop == False):
                try:
                    currentLine = self._eventLogFileHandle.readline()
                    if not currentLine:
                        break
                except:
                    break
                currentLineSplit = currentLine.split('|')
                if(len(currentLineSplit) > 1):
                    if(currentLineSplit[1].lower() == "loadprogram"):
                        if(len(currentLineSplit) > 3):
                            if(currentLineSplit[3] == "Done\n"):
                                stop = True
                    if(currentLineSplit[1].lower() == "vsttime"):
                        self._updateVstTime(currentLineSplit)
                if(stop == False):
                    configString += currentLine
            if(stop == True):
                print "C"*120
                print "Loading config: " + str(self._loadConfigFileName)
                print "C"*120
                self._configLoadCallback(self._loadConfigFileName, configString)
                print "C"*120
                return True
        return False

    def _updateVstTime(self, currentLineSplit):
        if(len(currentLineSplit) == 4):
            posVal = float(currentLineSplit[2])
#                            print "t," + str(posVal*24),
            tempoVal = float(currentLineSplit[3])
            dataTimeStamp = float(currentLineSplit[0])
            returnValue = self._midiTiming._updateFromVstTiming(dataTimeStamp, posVal, tempoVal);
            if(returnValue != None):
                stopedState, oldSpp, newSpp = returnValue
                if(stopedState == True): # Clear all on restart
                    self._midiStateHolder.cleanupFutureNotes(0.0, oldSpp, self._midiTiming.getTicksPerQuarteNote())
                else:
                    if(newSpp < oldSpp): # Looping back (else it is just a jump and we do nothing.)
                        self._midiStateHolder.fixLoopingNotes(oldSpp, newSpp, self._midiTiming.getTicksPerQuarteNote())

    def getData(self, calcTime):
        currentLineSplit = self._nextLine.split('|')
        currentMidiTimeStamp = self._nextTimeStamp
        _, calcMidiTime = self._midiTiming.getSongPosition(calcTime)
        while(currentMidiTimeStamp <= calcMidiTime):
            print ".",
            self._slowStop = True
            if(len(currentLineSplit) > 1):
                self._loadConfig(currentLineSplit)
                if(currentLineSplit[1].lower() == "stoprecording"):
                    print "Buu"*120
                    self._nextLine = None
                    break
                if(currentLineSplit[1].lower() == "vsttime"):
                    print "v",
                    self._updateVstTime(currentLineSplit)
                    _, calcMidiTime = self._midiTiming.getSongPosition(calcTime)
                if(currentLineSplit[1].lower() == "midi"):
                    if(len(currentLineSplit) == 6):
                        command = int(currentLineSplit[2], 16)
                        data1 = int(currentLineSplit[3], 16)
                        data2 = int(currentLineSplit[4], 16)
                        data3 = int(currentLineSplit[5], 16)
                        self._decodeMidiEvent(float(currentLineSplit[0]), command, data1, data2, data3)
                        status = "(other)"
                        mtype = command & 0xf0
                        if(mtype == 0x80):
                            status = "(off)"
                        if(mtype == 0x90):
                            (octav, noteLetter) = noteToOctavAndLetter(data1)
                            status = "(" + str(octav) + str(noteLetter) + ")"
                        if(mtype == 0xb0):
                            if(data3 == 0x00):
                                status = "(ctrl)"
                            else:
                                status = "(gui)"
                        print "m|%d|%d|%d|%s" % ((command & 0x0f), data1, data2, status),
            currentLine = self._eventLogFileHandle.readline()
            if not currentLine:
                self._nextLine = None
                break
            currentLineSplit = currentLine.split('|')
            if(len(currentLineSplit) > 1):
                currentTimeStamp = float(currentLineSplit[0])
                _, currentMidiTimeStamp = self._midiTiming.getSongPosition(currentTimeStamp)
                if(currentLineSplit[1].lower() == "midi"):
                    noteTimeStamp = quantizePosition(currentMidiTimeStamp, self._quantizeValue)
                    if(noteTimeStamp < currentMidiTimeStamp):
                        currentMidiTimeStamp = noteTimeStamp
            self._nextLine = currentLine
            self._nextTimeStamp = currentMidiTimeStamp
