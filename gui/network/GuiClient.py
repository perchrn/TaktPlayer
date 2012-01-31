'''
Created on 26. jan. 2012

@author: pcn
'''

import time

import socket
from multiprocessing import Process, Queue
from Queue import Empty
from xml.etree import ElementTree
import base64
import hashlib

class UrlSignature(object):
    def __init__(self, passwd = "GoGoGrillazEatingBananasFtw"):
        self._passwd = passwd

    def setPasswd(self, passwd):
        self._passwd = passwd

    def getUrlSignature(self, url):
        passwdUrl = self._passwd + url
        signature = hashlib.sha224(passwdUrl).hexdigest()
        return "sig=%s" % signature


def guiNetworkClientProcess(host, port, commandQueue, resultQueue):
    bufferSize = 1024
    tcpClientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcpClientSocket.settimeout(10.0)
    run = True
    while(run):
        try:
            tcpClientSocket.connect((host, port))
            resultQueue.put("<clientmessage message=\"connecting to " + str(host) + ":" + str(port) + "\"/>")
            while(run):
                try:
                    command = commandQueue.get_nowait()
                    if(command == "QUIT"):
                        run = False
                    else:
                        try:
                            tcpClientSocket.settimeout(5.0)
                            tcpClientSocket.send(command)
                            waitingForAnswer = True
                            dataReceived = ""
                            while(waitingForAnswer):
                                try:
                                    dataPart = tcpClientSocket.recv(bufferSize)
                                    if(len(dataPart) <= 0):
                                        waitingForAnswer = False
                                        if(len(dataReceived) > 0):
                                            resultQueue.put(dataReceived)
                                    elif(len(dataPart) < bufferSize):
                                        waitingForAnswer = False
                                        resultQueue.put(dataReceived + dataPart)
                                        resultQueue.put("<clientmessage message=\"Got a short message.\"/>")
                                    else:
                                        resultQueue.put("<clientmessage message=\"Got some data. len = " + str(len(dataPart)) + "\"/>")
                                        dataReceived += dataPart
                                except socket.timeout:
                                    resultQueue.put("<clientmessage message=\"Got a socket timeout exception while waiting for answer.\"/>")
                                    if(len(dataReceived) > 0):
                                        waitingForAnswer = False
                                        resultQueue.put(dataReceived)
                        except socket.timeout:
                            pass
                except Empty:
                    time.sleep(0.05)
        except socket.error:
            pass
        except socket.timeout:
            pass
        try:
            command = commandQueue.get_nowait()
            if(command == "QUIT"):
                run = False
            else:
                resultQueue.put("<clienterror message=\"Network trouble. Cannot connect to server. Please try again later.\"/>")
        except Empty:
            pass


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
            self._guiClientProcess.join(20.0)
            if(self._guiClientProcess.is_alive()):
                print "GuiNetworkClient did not respond to quit command. Terminating."
                self._guiClientProcess.terminate()
        self._guiClientProcess = None

    def requestImage(self, noteId, videoPos = 0.0):
        command = "<thumbnailrequest note=\"" + str(noteId) + "\" videoPosition=\"" + str(videoPos) + "\"/>"
        self._commandQueue.put(command)

    def getServerResponse(self):
        try:
            serverResponse = self._resultQueue.get_nowait()
            print "ServerResponse: " + str(serverResponse)
            serverXml = ElementTree.XML(serverResponse)
            if(serverXml.tag == "servermessage"):
                print "GuiClient Message: " + serverXml.get("message")
            elif(serverXml.tag == "thumbnailresponse"):
                noteId = int(serverXml.get("note"))
                videoPosition = float(serverXml.get("videoPosition"))
                thumbnailData = base64.b64decode(serverXml.get("data"))
#                thumbArray = numpy.fromstring(thumbnailData, dtype='uint8')
#                print "Returning... " + str(thumbArray)
                return thumbnailData
        except Empty:
            pass
