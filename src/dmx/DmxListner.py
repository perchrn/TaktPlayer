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
    def __init__(self, midiTimingClass, midiStateHolderClass, configLoadCallback = None, eventLogSaveQueue = None):

        self._midiTiming = midiTimingClass
        self._midiStateHolder = midiStateHolderClass
        self._configLoadCallback = configLoadCallback
        self._eventLogSaveQueue = eventLogSaveQueue

        #Daemon variables:
        self._dmxListnerProcess = None
        self._dmxQueue = Queue(1024)
        self._dmxListnerPrintQueue = Queue(1024)
        self._conectedAddress = None

    def startDaemon(self, dmxSettings):
        if(olaOk):
            _, _, _, universe = dmxSettings
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
                if((dataLen > 0) and (dataLen <= 512)):
                    sync, spp = self._midiTiming.getSongPosition(dataTimeStamp)
                    dataString = ""
                    for i in range(len(data)):
                        dataString += "|%02x" % (data[i])
                        self._midiStateHolder.dmxControllerChange(i, data[i], sync, spp)
                    self._addEventToSaveLog(str(dataTimeStamp) + "|DMX" + dataString)
#                    print str(dataTimeStamp) + "|DMX" + dataString
                else:
                    print "Bad DMX length: data: " + str(len(data))
            else:
                return gotDmxNote

