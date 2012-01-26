'''
Created on 26. jan. 2012

@author: pcn
'''

import time

import socket
from multiprocessing import Process, Queue
from Queue import Empty

def guiNetworkServerProcess(host, port, commandQueue, resultQueue):
    tcpServerSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcpServerSocket.bind((host, port))
    tcpServerSocket.listen(1)
    clientSocket, clientAddress = tcpServerSocket.accept()
    run = True
    while(run):
        socketData = clientSocket.recv(1024)
        commandQueue.put(socketData)
        print socketData
        clientSocket.send("<serverResponse client=\"" + str(clientAddress) +  "\">" + str(socketData))
        try:
            result = resultQueue.get_nowait()
            if(result == "QUIT"):
                run = False
        except Empty:
            time.sleep(0.05)


class GuiServer(object):
    def __init__(self, configurationTree, mediaPool):
        self._configurationTree = configurationTree
        self._mediaPool = mediaPool

        self._commandQueue = None
        self._resultQueue = None
        self._guiServerProcess = None

    def startGuiServerProcess(self, host, port):
        self._commandQueue = Queue(256)
        self._resultQueue = Queue(256)
        self._guiServerProcess = Process(target=guiNetworkServerProcess, args=(host, port, self._commandQueue, self._resultQueue))
        self._guiServerProcess.name = "guiNetworkServer"
        self._guiServerProcess.start()

    def stopGuiServerProcess(self):
        if(self._guiServerProcess != None):
            print "Stopping guiNetworkServer"
            self._commandQueue.put("QUIT")
            self._guiServerProcess.join(10.0)
        self._guiServerProcess = None
