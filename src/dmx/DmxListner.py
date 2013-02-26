'''
Created on 12. des. 2011

@author: pcn
'''

import time
from multiprocessing import Process, Queue
import traceback
import subprocess
import os
import signal

try:
    from ola.ClientWrapper import ClientWrapper #@UnresolvedImport
    olaOk = True
except:
    olaOk = False


outputQueue = None

def NewDataCallback(data):
    outputQueue.put_nowait((time.time(), data))

def dmxListnerDaemon(universe, dmxOutputQueue, logQueue):
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
        self._dmxServerProcessInfo = None
        self._dmxQueue = Queue(1024)
        self._dmxListnerPrintQueue = Queue(1024)
        self._conectedAddress = None

    def _tryToStartDaemon(self, daemonBinary):
        try:
            print "Trying to start DmxServer daemon: " + str(daemonBinary)
            self._dmxServerProcessInfo = subprocess.Popen(['olad'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            time.sleep(1)
        except:
            print "Error starting olad daemon!"
            traceback.print_exc()
            self._dmxServerProcessInfo = None

    def startDaemon(self, dmxSettings):
        if(olaOk):
            _, _, _, universe, daemonBinary = dmxSettings
            self._tryToStartDaemon(daemonBinary)
            if(self._dmxServerProcessInfo == None):
                self._tryToStartDaemon("olad")
            if(self._dmxServerProcessInfo == None):
                self._tryToStartDaemon("/opt/local/bin/olad")
            print "Starting DmxListner daemon in universe: " + str(universe)
            self._dmxListnerProcess = Process(target=dmxListnerDaemon, args=(universe, self._dmxQueue, self._dmxListnerPrintQueue))
            self._dmxListnerProcess.name = "dmxListner"
            self._dmxListnerProcess.start()
            self.hasDmxListnerProcessToShutdownNicely()

    def requestDmxListnerProcessToStop(self):
        if(self._dmxListnerProcess != None):
            print "Stopping DmxListner daemon"
            self._dmxListnerProcess.terminate()
        if(self._dmxServerProcessInfo != None):
            print "Stopping DmxServer daemon"
            print "Killing olad process whith id: " + str(self._dmxServerProcessInfo.pid)
            os.kill(self._dmxServerProcessInfo.pid, signal.SIGINT)
            self._dmxServerProcessInfo = None

    def hasDmxListnerProcessToShutdownNicely(self):
        if(self._dmxListnerProcess != None):
            if(self._dmxListnerProcess.is_alive() == False):
                self._dmxListnerProcess = None
            else:
                return False
        if(self._dmxServerProcessInfo != None):
            return False
        return True

    def forceDmxListnerProcessToStop(self):
        if(self._dmxListnerProcess != None):
            if(self._dmxListnerProcess.is_alive()):
                print "DmxListner daemon did not respond to quit command. Terminating."
                self._dmxListnerProcess.terminate()
        self._dmxListnerProcess = None
        if(self._dmxServerProcessInfo != None):
            print "DmxServer daemon did not respond to quit command. Terminating."
            os.kill(self._dmxServerProcessInfo.pid, signal.SIGINT)
        self._dmxServerProcessInfo = None

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

