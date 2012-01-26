'''
Created on 26. jan. 2012

@author: pcn
'''

import time

import socket
from multiprocessing import Process, Queue
from Queue import Empty

def guiNetworkClientProcess(host, port, commandQueue, resultQueue):
    tcpClientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcpClientSocket.connect((host, port))
    run = True
    while(run):
        try:
            command = commandQueue.get_nowait()
            if(command == "QUIT"):
                run = False
            else:
                tcpClientSocket.send(command)
                waitingForAnswer = True
                while(waitingForAnswer):
                    dataPart = tcpClientSocket.recv(1024)
                    print dataPart
                    waitingForAnswer = False
                    resultQueue.put(dataPart)
        except Empty:
            time.sleep(0.05)


class GuiClient(object):
    def __init__(self):
        self._commandQueue = None
        self._resultQueue = None

    def startGuiClientProcess(self, host, port):
        self._commandQueue = Queue(256)
        self._resultQueue = Queue(256)
        self._guiClientProcess = Process(target=guiNetworkClientProcess, args=(host, port, self._commandQueue, self._resultQueue))
        self._guiClientProcess.name = "guiNetworkClient"
        self._guiClientProcess.start()

    def stopGuiClientProcess(self):
        if(self._guiClientProcess != None):
            print "Stopping guiNetworkClient"
            self._commandQueue.put("QUIT")
            self._guiClientProcess.join(10.0)
        self._guiClientProcess = None

    def sendCommando(self, commando):
        self._commandQueue.put(commando)
        result = self._resultQueue.get()
        return result
