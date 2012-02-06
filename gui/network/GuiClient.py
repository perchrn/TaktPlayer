'''
Created on 26. jan. 2012

@author: pcn
'''

from multiprocessing import Process, Queue
from Queue import Empty
from utilities.MiniXml import MiniXml, stringToXml, getFromXml
import httplib
import os
from utilities.UrlSignature import UrlSignature, getDefaultUrlSignaturePasswd

def guiNetworkClientProcess(host, port, passwd, commandQueue, resultQueue):
    run = True
    hostPort = "%s:%d" %(host, port)
    urlSignaturer = UrlSignature(passwd)
    while(run):
        try:
            command = commandQueue.get(True, 5.0)
            if(command == "QUIT"):
                run = False
            else:
                commandXml = stringToXml(command)
#                httpConnection.request("GET", "?configPath=root")
#                httpConnection.request("GET", "?configPath=musicalvideoplayer.global.effectmodulation")
#                httpConnection.request("GET", "thumbs/6e5b995f7ac65a36ae54edfd28dcdf0fc729b79d021a65360d9b4a79_0.00.jpg")
                if(commandXml.tag == "thumbnailRequest"):
                    noteTxt = getFromXml(commandXml, "note", None)
                    noteTime = getFromXml(commandXml, "time", "0.0")
                    if(noteTxt != None):
                        urlArgs = "?imageThumb=%s&time=%s" %(noteTxt, noteTime)
                        urlArgs = urlSignaturer.getUrlWithSignature(urlArgs)
                        resposeXmlString = requestUrl(hostPort, urlArgs, "text/xml")
                        resultQueue.put(resposeXmlString)
                elif(commandXml.tag == "noteListRequest"):
                    urlArgs = "?noteList=true"
                    urlArgs = urlSignaturer.getUrlWithSignature(urlArgs)
                    resposeXmlString = requestUrl(hostPort, urlArgs, "text/xml")
                    resultQueue.put(resposeXmlString)
                elif(commandXml.tag == "trackStateRequest"):
                    urlArgs = "?trackState=true"
                    urlArgs = urlSignaturer.getUrlWithSignature(urlArgs)
                    resposeXmlString = requestUrl(hostPort, urlArgs, "text/xml")
                    resultQueue.put(resposeXmlString)
                elif(commandXml.tag == "thumbnailFileRequest"):
                    fileName = getFromXml(commandXml, "fileName", None)
                    if(fileName != None):
                        resposeXmlString = requestUrl(hostPort, "%s" %(fileName), "image/jpg")
                        resultQueue.put(resposeXmlString)
        except Empty:
            pass

def requestUrl(hostPort, urlArgs, excpectedMimeType = "text/xml"):
    try:
        httpConnection = httplib.HTTPConnection(hostPort)
        httpConnection.request("GET", urlArgs)
        serverResponse = httpConnection.getresponse()
        if(serverResponse.status == 200):
            resposeType = serverResponse.getheader("Content-type")
            if(resposeType == excpectedMimeType):
                if(excpectedMimeType == "image/jpg"):
                    pathDir = os.path.dirname(urlArgs)
                    pathFile = os.path.basename(urlArgs)
                    filePath = ""
                    if((pathDir == "/thumbs") or (pathDir == "thumbs")):
                        filePath = "thumbs/%s" % pathFile
                    else:
                        serverMessageXml = MiniXml("servermessage", "Bad directory request sending 404: %s" % pathDir)
                        return serverMessageXml.getXmlString()
                    fileHandle=open(filePath, 'wb')
                    fileHandle.write(serverResponse.read())
                    fileHandle.close()
                    downloadMessageXml = MiniXml("fileDownloaded")
                    downloadMessageXml.addAttribute("fileName", filePath)
                    return downloadMessageXml.getXmlString()
                else:
                    serverResponseData = serverResponse.read()
                    return serverResponseData
            else:
                clientMessageXml = MiniXml("clientmessage", "Bad file type from server! Got: %s Expected: %s" % (resposeType, excpectedMimeType))
                return clientMessageXml.getXmlString()
        else:
            clientMessageXml = MiniXml("clientmessage", "Server trouble. Server returned status: %d Reason: %s" %(serverResponse.status, serverResponse.reason))
            return clientMessageXml.getXmlString()
    except:
        clientMessageXml = MiniXml("clientmessage", "Got exception while requesting URL.")
        return clientMessageXml.getXmlString()

class GuiClient(object):
    def __init__(self):
        self._commandQueue = None
        self._resultQueue = None

    def startGuiClientProcess(self, host, port, passwd):
        if(passwd == None):
            passwd = getDefaultUrlSignaturePasswd()
        self._commandQueue = Queue(256)
        self._resultQueue = Queue(256)
        self._guiClientProcess = Process(target=guiNetworkClientProcess, args=(host, port, passwd, self._commandQueue, self._resultQueue))
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

    def requestActiveNoteList(self):
        commandXml = MiniXml("noteListRequest")
        self._commandQueue.put(commandXml.getXmlString())

    def requestImage(self, noteId, videoPos = 0.0):
        commandXml = MiniXml("thumbnailRequest")
        commandXml.addAttribute("note", str(noteId))
        commandXml.addAttribute("time", "%.2f" % videoPos)
        self._commandQueue.put(commandXml.getXmlString())

    def requestImageFile(self, fileName):
        commandXml = MiniXml("thumbnailFileRequest")
        commandXml.addAttribute("fileName", fileName)
        self._commandQueue.put(commandXml.getXmlString())

    def requestTrackState(self):
        commandXml = MiniXml("trackStateRequest")
        self._commandQueue.put(commandXml.getXmlString())

    class ResponseTypes():
        FileDownload, ThumbRequest, NoteList, TrackState, Configuration = range(5)

    def getServerResponse(self):
        returnValue = (None, None)
        try:
            serverResponse = self._resultQueue.get_nowait()
            serverXml = stringToXml(serverResponse)
            if(serverXml != None):
                if(serverXml.tag == "servermessage"):
                    print "GuiClient Message: " + serverXml.get("message")
                elif(serverXml.tag == "fileDownloaded"):
                    fileName = serverXml.get("fileName")
                    if(fileName == None):
                        print "ERRORRRRRRR!!!!! file"
                        returnValue = (self.ResponseTypes.FileDownload, None)
                    else:
                        fileName = os.path.normcase(fileName)
                        returnValue = (self.ResponseTypes.FileDownload, fileName)
                elif(serverXml.tag == "thumbRequest"):
                    noteTxt = serverXml.get("note")
                    noteTime = float(serverXml.get("time", "0.0"))
                    fileName = serverXml.get("fileName")
                    if((noteTxt == None) or (fileName == None)):
                        print "ERRORRRRRRR!!!!! note"
                        return (self.ResponseTypes.ThumbRequest, None)
                    noteId = max(min(int(noteTxt), 127), 0)
                    print "Got thumbRequest response: %s at %.2f with filename: %s" % (noteTxt, noteTime, fileName)
                    fileName = os.path.normcase(fileName)
                    returnValue = (self.ResponseTypes.ThumbRequest, (noteId, noteTime, fileName))
                elif(serverXml.tag == "noteListRequest"):
                    returnValue = (self.ResponseTypes.NoteList, None)
                    listTxt = serverXml.get("list")
                    print "Got noteListRequest response: list: %s" % (listTxt)
                    returnValue = (self.ResponseTypes.NoteList, listTxt.split(',', 128))
                elif(serverXml.tag == "trackStateRequest"):
                    returnValue = (self.ResponseTypes.TrackState, None)
                    listTxt = serverXml.get("list")
#                    print "Got trackStateRequest response: list: %s" % (listTxt)
                    returnValue = (self.ResponseTypes.TrackState, listTxt.split(',', 128))
            else:
                print "ERROR! Web server command is not a valid XML: " + str(serverResponse)
        except Empty:
            pass
        return returnValue
