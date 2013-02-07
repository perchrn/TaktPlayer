'''
Created on 12. des. 2011

@author: pcn
'''

import time
from multiprocessing import Process, Queue
import traceback

try:
    from ola.ClientWrapper import ClientWrapper
    olaOk = True
except:
    olaOk = False

outputQueue = None

def NewDataCallback(data):
    outputQueue.put_nowait((time.time(), data))

def dmxDaemon(universe, dmxOutputQueue, logQueue):
    global outputQueue
    outputQueue = dmxOutputQueue
    try:
        wrapper = ClientWrapper()
        client = wrapper.Client()
        client.RegisterUniverse(universe, client.REGISTER, NewDataCallback)
        wrapper.Run()
    except:
        logQueue.put_nowait("Error setting up DMX in uiniverse: %d" % (universe))
        logQueue.put_nowait(traceback.format_exc())
        logQueue.put_nowait("Error setting up DMX in uiniverse: %d" % (universe))

class DmxListner(object):
    def __init__(self, configLoadCallback = None, eventLogSaveQueue = None):
        #Logging etc.
        self._configLoadCallback = configLoadCallback
        self._eventLogSaveQueue = eventLogSaveQueue

        #Daemon variables:
        self._dmxListnerProcess = None
        self._dmxQueue = Queue(1024)
        self._dmxListnerPrintQueue = Queue(1024)
        self._conectedAddress = None

    def startDaemon(self, universe):
        if(olaOk):
            print "Starting DmxListner daemon in universe: " + str(universe)
            self._dmxListnerProcess = Process(target=dmxDaemon, args=(universe, self._dmxQueue, self._dmxListnerPrintQueue))
            self._dmxListnerProcess.name = "dmxListner"
            self._dmxListnerProcess.start()

    def requestDmxListnerProcessToStop(self):
        if(self._dmxListnerProcess != None):
            print "Stopping DmxListner daemon"
            self._dmxListnerProcess.terminate()

    def hasDmxListnerProcessToShutdownNicely(self):
        if(self._dmxListnerProcess == None):
            return True
        else:
            if(self._dmxListnerProcess.is_alive() == False):
                self._dmxListnerProcess = None
                return True
            return False

    def forceDmxListnerProcessToStop(self):
        if(self._dmxListnerProcess != None):
            if(self._dmxListnerProcess.is_alive()):
                print "DmxListner daemon did not respond to quit command. Terminating."
                self._dmxListnerProcess.terminate()
        self._dmxListnerProcess = None

    def _addEventToSaveLog(self, string):
        if(self._eventLogSaveQueue != None):
            try:
                self._eventLogSaveQueue.put_nowait(string + "\n")
            except:
                pass

    def getData(self):
        try:
            printString = self._dmxListnerPrintQueue.get_nowait()
            print printString
        except:
            pass
        gotDmxNote = False
        while(True):
            try:
                dataTimeStamp, data = self._dmxQueue.get_nowait()
            except:
                return gotDmxNote
            if data:
                dataLen = len(data)
                if(dataLen > 1):
                    dataString = ""
                    for i in range(len(data)):
                        dataString += "|%02x" % (data[i])
                    self._addEventToSaveLog(str(dataTimeStamp) + "|DMX" + dataString)
                    print str(dataTimeStamp) + "|DMX" + dataString
                else:
                    print "Bad DMX length: data: " + str(len(data))
            else:
                return gotDmxNote

#class RenderFileReader(DmxListner):
#    def __init__(self, midiTimingClass, midiStateHolderClass, configLoadCallback):
#        DmxListner.__init__(self, midiTimingClass, midiStateHolderClass, configLoadCallback, eventLogSaveQueue=None)
#        self._eventLogFileHandle = None
#        self._renderFileOutputName = None
#        self._loadConfigFileName = None
#        self._quantizeValue = 1.0 * self._midiTiming.getTicksPerQuarteNote()
#        self._nextLine = None
#        self._nextTimeStamp = 0.0
#        self._startRecordingTime = -1.0
#        self._eventLogFileHandle = None
#        self._slowStop = False
#
#    def openFile(self, renderFileName):
#        try:
#            self._eventLogFileHandle = open(renderFileName, 'r')
#            self._findStartLine()
#        except:
#            print "Error opening render file with file name: " + str(renderFileName)
#            traceback.print_exc()
#            self._eventLogFileHandle = None
#
#    def startDaemon(self, host, port, useBroadcast):
#        pass
#
#    def requestDmxListnerProcessToStop(self):
#        self._nextLine = None
#
#    def hasDmxListnerProcessToShutdownNicely(self):
#        if(self._slowStop == True):
#            return False
#        return True
#
#    def forceDmxListnerProcessToStop(self):
#        self._nextLine = None
#
#    def endIsReached(self):
#        if(self._nextLine == None):
#            return True
#        return False
#
#    def getStartTime(self):
#        return self._startRecordingTime
#
#    def getOutputFileName(self):
#        return self._renderFileOutputName
#
#    def _findStartLine(self):
#        stop = False
#        startFound = False
#        while(stop == False):
#            try:
#                currentLine = self._eventLogFileHandle.readline()
#                if not currentLine:
#                    break
#            except:
#                break
#            currentLineSplit = currentLine.split('|')
#            if(len(currentLineSplit) > 1):
#                self._loadConfig(currentLineSplit)
#                if(currentLineSplit[1].lower() == "startrecording"):
#                    if(len(currentLineSplit) > 2):
#                        self._renderFileOutputName = currentLineSplit[2].split('\n')[0]
#                    currentTimeStamp = float(currentLineSplit[0])
#                    self._startRecordingTime = currentTimeStamp
#                    startFound = True
#                    stop = True
#                    print "StartRecording tag found at: " + str(currentLineSplit[0])
#        if(startFound == False):
#            self._eventLogFileHandle.seek(0)
#            print "Warning no StartRecording tag found!!!"
#            stop = False
#            configIsLoaded = False
#            vstBlockSeekPos = -1
#            vstBlockTimeStamp = 0.0
#            tmpBlockPos = -1
#            tmpBlockTimeStamp = 0.0
#            while(stop == False):
#                try:
#                    currentPos = self._eventLogFileHandle.tell()
#                    currentLine = self._eventLogFileHandle.readline()
#                    if not currentLine:
#                        break
#                except:
#                    break
#                currentLineSplit = currentLine.split('|')
#                if(len(currentLineSplit) > 1):
#                    loadedConfig = self._loadConfig(currentLineSplit)
#                    if(loadedConfig == True):
#                        configIsLoaded = True
#                    if(configIsLoaded):
#                        currentTimeStamp = float(currentLineSplit[0])
#                        if(currentTimeStamp > tmpBlockTimeStamp):
#                            tmpBlockPos = currentPos
#                            tmpBlockTimeStamp = currentTimeStamp
#                        if(currentLineSplit[1].lower() == "vsttime"):
#                            if(len(currentLineSplit) > 2):
#                                vstTimeStamp = float(currentLineSplit[2])
#                                if((vstTimeStamp % 1.0) == 0.0):
#                                    vstBlockSeekPos = tmpBlockPos
#                                    vstBlockTimeStamp = tmpBlockTimeStamp
#                                else:
#                                    if(vstBlockSeekPos > -1):
#                                        self._eventLogFileHandle.seek(vstBlockSeekPos)
#                                        self._startRecordingTime = vstBlockTimeStamp
#                                        startFound = True
#                                        stop = True
#            if(startFound == True):
#                baseLoadName = os.path.basename(self._loadConfigFileName)
#                if(baseLoadName.endswith(".cfg")):
#                    self._renderFileOutputName = baseLoadName[0:(len(baseLoadName)-4)]
#                else:
#                    self._renderFileOutputName = baseLoadName
#            else:
#                self._nextLine = None
#        if(startFound == True):
#            self._nextLine = self._eventLogFileHandle.readline()
#            print "S"*120
#            print "Starting on line: " + self._nextLine.split('\n')[0]
#            print "S"*120
#            if not self._nextLine:
#                self._nextLine = None
#            else:
#                if(len(currentLineSplit) > 1):
#                    currentTimeStamp = float(currentLineSplit[0])
#                    _, currentMidiTimeStamp = self._midiTiming.getSongPosition(currentTimeStamp)
#                    if(currentLineSplit[1].lower() == "midi"):
#                        currentMidiTimeStamp = quantizePosition(currentMidiTimeStamp, self._quantizeValue)
#                    self._nextTimeStamp = currentMidiTimeStamp
#                else:
#                    self._nextLine = None
#
#    def _loadConfig(self, currentLineSplit):
#        loadStartOk = False
#        if(currentLineSplit[1].lower() == "loadprogram"):
#            if(len(currentLineSplit) > 2):
#                if(currentLineSplit[2] != "Done"):
#                    loadStartOk = True
#                    self._loadConfigFileName = currentLineSplit[2].split('\n')[0]
#        configString = ""
#        if(loadStartOk == True):
#            stop = False
#            while(stop == False):
#                try:
#                    currentLine = self._eventLogFileHandle.readline()
#                    if not currentLine:
#                        break
#                except:
#                    break
#                currentLineSplit = currentLine.split('|')
#                if(len(currentLineSplit) > 1):
#                    if(currentLineSplit[1].lower() == "loadprogram"):
#                        if(len(currentLineSplit) > 3):
#                            if(currentLineSplit[3] == "Done\n"):
#                                stop = True
#                    if(currentLineSplit[1].lower() == "vsttime"):
#                        self._updateVstTime(currentLineSplit)
#                if(stop == False):
#                    configString += currentLine
#            if(stop == True):
#                print "C"*120
#                print "Loading config: " + str(self._loadConfigFileName)
#                print "C"*120
#                self._configLoadCallback(self._loadConfigFileName, configString)
#                print "C"*120
#                return True
#        return False
#
#    def _updateVstTime(self, currentLineSplit):
#        if(len(currentLineSplit) == 4):
#            posVal = float(currentLineSplit[2])
##                            print "t," + str(posVal*24),
#            tempoVal = float(currentLineSplit[3])
#            dataTimeStamp = float(currentLineSplit[0])
#            returnValue = self._midiTiming._updateFromVstTiming(dataTimeStamp, posVal, tempoVal);
#            if(returnValue != None):
#                stopedState, oldSpp, newSpp = returnValue
#                if(stopedState == True): # Clear all on restart
#                    self._midiStateHolder.cleanupFutureNotes(0.0, oldSpp, self._midiTiming.getTicksPerQuarteNote())
#                else:
#                    if(newSpp < oldSpp): # Looping back (else it is just a jump and we do nothing.)
#                        self._midiStateHolder.fixLoopingNotes(oldSpp, newSpp, self._midiTiming.getTicksPerQuarteNote())
#
#    def getData(self, calcTime):
#        currentLineSplit = self._nextLine.split('|')
#        currentMidiTimeStamp = self._nextTimeStamp
#        _, calcMidiTime = self._midiTiming.getSongPosition(calcTime)
#        while(currentMidiTimeStamp <= calcMidiTime):
#            print ".",
#            self._slowStop = True
#            if(len(currentLineSplit) > 1):
#                self._loadConfig(currentLineSplit)
#                if(currentLineSplit[1].lower() == "stoprecording"):
#                    self._nextLine = None
#                    break
#                if(currentLineSplit[1].lower() == "vsttime"):
#                    print "v",
#                    self._updateVstTime(currentLineSplit)
#                    _, calcMidiTime = self._midiTiming.getSongPosition(calcTime)
#                if(currentLineSplit[1].lower() == "midi"):
#                    if(len(currentLineSplit) == 6):
#                        command = int(currentLineSplit[2], 16)
#                        data1 = int(currentLineSplit[3], 16)
#                        data2 = int(currentLineSplit[4], 16)
#                        data3 = int(currentLineSplit[5], 16)
#                        self._decodeMidiEvent(float(currentLineSplit[0]), command, data1, data2, data3)
#                        status = "(other)"
#                        mtype = command & 0xf0
#                        if(mtype == 0x80):
#                            status = "(off)"
#                        if(mtype == 0x90):
#                            (octav, noteLetter) = noteToOctavAndLetter(data1)
#                            status = "(" + str(octav) + str(noteLetter) + ")"
#                        if(mtype == 0xb0):
#                            if(data3 == 0x00):
#                                status = "(ctrl)"
#                            else:
#                                status = "(gui)"
#                        print "m|%d|%d|%d|%s" % ((command & 0x0f), data1, data2, status),
#            currentLine = self._eventLogFileHandle.readline()
#            if not currentLine:
#                self._nextLine = None
#                break
#            currentLineSplit = currentLine.split('|')
#            if(len(currentLineSplit) > 1):
#                currentTimeStamp = float(currentLineSplit[0])
#                _, currentMidiTimeStamp = self._midiTiming.getSongPosition(currentTimeStamp)
#                if(currentLineSplit[1].lower() == "midi"):
#                    noteTimeStamp = quantizePosition(currentMidiTimeStamp, self._quantizeValue)
#                    if(noteTimeStamp < currentMidiTimeStamp):
#                        currentMidiTimeStamp = noteTimeStamp
#            self._nextLine = currentLine
#            self._nextTimeStamp = currentMidiTimeStamp
