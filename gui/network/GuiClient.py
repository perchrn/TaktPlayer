'''
Created on 26. jan. 2012

@author: pcn
'''

from multiprocessing import Process, Queue
from Queue import Empty
import base64
import hashlib
from utilities.MiniXml import MiniXml, stringToXml
import httplib
import time

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
    run = True
    while(run):
        try:
            command = commandQueue.get_nowait()
            if(command == "QUIT"):
                run = False
            else:
                httpConnection = httplib.HTTPConnection("127.0.0.1:2021")
#                httpConnection.request("GET", "?imageThumb=0C&time=0.0")
#                httpConnection.request("GET", "?configPath=root")
                httpConnection.request("GET", "?configPath=musicalvideoplayer.global.effectmodulation")
#                httpConnection.request("GET", "thumbs/6e5b995f7ac65a36ae54edfd28dcdf0fc729b79d021a65360d9b4a79_0.00.jpg")
                serverResponse = httpConnection.getresponse()
                if(serverResponse.status == 200):
                    resposeType = serverResponse.getheader("Content-type")
                    serverResponseData = serverResponse.read()
                    clientMessageXml = MiniXml("clientmessage", "Got response from server. Type: %s content: %s" % (resposeType, str(serverResponseData)))
                    resultQueue.put(clientMessageXml.getXmlString())
                else:
                    clientMessageXml = MiniXml("clientmessage", "Server trouble. Server returned status: %d Reson: %s" %(serverResponse.status, serverResponse.reason))
                    resultQueue.put(clientMessageXml.getXmlString())
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
            self._guiClientProcess.join(20.0)
            if(self._guiClientProcess.is_alive()):
                print "GuiNetworkClient did not respond to quit command. Terminating."
                self._guiClientProcess.terminate()
        self._guiClientProcess = None

    def requestImage(self, noteTxt, videoPos = 0.0):
        commandXml = MiniXml("thumbnailrequest")
        commandXml.addAttribute("note", noteTxt)
        commandXml.addAttribute("time", "%.2f" % videoPos)
        self._commandQueue.put(commandXml.getXmlString())

    def getServerResponse(self):
        try:
            serverResponse = self._resultQueue.get_nowait()
            print "ServerResponse: " + str(serverResponse)
            serverXml = stringToXml(serverResponse)
            if(serverXml != None):
                if(serverXml.tag == "servermessage"):
                    print "GuiClient Message: " + serverXml.get("message")
                elif(serverXml.tag == "thumbnailresponse"):
                    noteId = int(serverXml.get("note"))
                    videoPosition = float(serverXml.get("videoPosition"))
                    thumbnailData = base64.b64decode(serverXml.get("data"))
    #                thumbArray = numpy.fromstring(thumbnailData, dtype='uint8')
    #                print "Returning... " + str(thumbArray)
                    return thumbnailData
            else:
                print "ERROR! Web server command is not a valid XML: " + str(serverResponse)
        except Empty:
            pass
