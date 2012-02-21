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
import mimetypes
import time

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
#                httpConnection.request("GET", "?configPath=musicalvideoplayer.global.effectmodulation")
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
                elif(commandXml.tag == "configStateRequest"):
                    oldId = getFromXml(commandXml, "id", "-1")
                    urlArgs = "?configState=%s" %(oldId)
                    urlArgs = urlSignaturer.getUrlWithSignature(urlArgs)
                    resposeXmlString = requestUrl(hostPort, urlArgs, "text/xml")
                    resultQueue.put(resposeXmlString)
                elif(commandXml.tag == "configurationRequest"):
                    path = getFromXml(commandXml, "path", "root")
                    urlArgs = "?configPath=%s" %(path)
                    urlArgs = urlSignaturer.getUrlWithSignature(urlArgs)
                    resposeXmlString = requestUrl(hostPort, urlArgs, "text/xml")
                    resultQueue.put(resposeXmlString)
                elif(commandXml.tag == "latestMidiContollersRequest"):
                    urlArgs = "?latestMidiContollers=true"
                    urlArgs = urlSignaturer.getUrlWithSignature(urlArgs)
                    resposeXmlString = requestUrl(hostPort, urlArgs, "text/xml")
                    resultQueue.put(resposeXmlString)
                elif(commandXml.tag == "thumbnailFileRequest"):
                    fileName = getFromXml(commandXml, "fileName", None)
                    if(fileName != None):
                        resposeXmlString = requestUrl(hostPort, "%s" %(fileName), "image/jpg")
                        resultQueue.put(resposeXmlString)
                elif(commandXml.tag == "configuration"):
                    resposeXmlString = postXMLFile(urlSignaturer, hostPort, "configuration", "active configuration", command)
                    resultQueue.put(resposeXmlString)
                elif(commandXml.tag == "configFileRequest"):
                    requestType = getFromXml(commandXml, "type", "list")
                    requestName = getFromXml(commandXml, "name", "None")
                    urlArgs = "?configFileRequest=%s&name=%s" % (requestType, requestName)
                    urlArgs = urlSignaturer.getUrlWithSignature(urlArgs)
                    resposeXmlString = requestUrl(hostPort, urlArgs, "text/xml")
                    resultQueue.put(resposeXmlString)
                else:
                    print "Unknown command xml: " + command
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
                clientMessageXml = MiniXml("servermessage", "Bad file type from server! Got: %s Expected: %s" % (resposeType, excpectedMimeType))
                return clientMessageXml.getXmlString()
        else:
            clientMessageXml = MiniXml("servermessage", "Server trouble. Server returned status: %d Reason: %s" %(serverResponse.status, serverResponse.reason))
            return clientMessageXml.getXmlString()
        httpConnection.close()
    except:
        clientMessageXml = MiniXml("servermessage", "Got exception while requesting URL.")
        return clientMessageXml.getXmlString()

def postXMLFile(urlSignaturer, hostPort, fileType, fileName, xmlString):
    try:
        files = [(fileType, fileName, xmlString)]
        fields = urlSignaturer.getSigantureFieldsForFile(fileType, fileName, xmlString)
        content_type, body = encode_multipart_formdata(fields, files)
        headers = {"Content-type": content_type}
        httpConnection = httplib.HTTPConnection(hostPort)
        httpConnection.request("POST", "", body, headers)
        serverResponse = httpConnection.getresponse()
        if(serverResponse.status == 200):
            resposeType = serverResponse.getheader("Content-type")
            if(resposeType == "text/xml"):
                serverResponseData = serverResponse.read()
                return serverResponseData
            else:
                clientMessageXml = MiniXml("servermessage", "Bad file type from server! Got: %s Expected: %s" % (resposeType, "text/xml"))
                return clientMessageXml.getXmlString()
        else:
            clientMessageXml = MiniXml("servermessage", "Server trouble. Server returned status: %d Reason: %s" %(serverResponse.status, serverResponse.reason))
            return clientMessageXml.getXmlString()
        httpConnection.close()
    except:
        clientMessageXml = MiniXml("servermessage", "Got exception while requesting URL.")
        return clientMessageXml.getXmlString()

def encode_multipart_formdata(fields, files):
    """
    fields is a sequence of (name, value) elements for regular form fields.
    files is a sequence of (name, filename, value) elements for data to be uploaded as files
    Return (content_type, body) ready for httplib.HTTP instance
    """
    BOUNDARY = '----------ThIs_Is_tHe_bouNdaRY_$'
    body = None
    for (key, value) in fields:
        if(body == None):
            body = '--' + BOUNDARY + "\n"
        else:
            body += '--' + BOUNDARY + "\n"
        body += 'Content-Disposition: form-data; name="%s"' % key + "\n"
        body += "\n"
        body += value + "\n"
    for (key, filename, value) in files:
        if(body == None):
            body = '--' + BOUNDARY + "\n"
        else:
            body += '--' + BOUNDARY + "\n"
        body += 'Content-Disposition: form-data; name="%s"; filename="%s"' % (key, filename) + "\n"
        body += 'Content-Type: %s' % get_content_type(filename) + "\n"
        body += "\n"
        body += value + "\n"
    body += '--' + BOUNDARY + '--' + "\n"
    body += "\n"
    content_type = 'multipart/form-data; boundary=%s' % BOUNDARY
    return content_type, body

def get_content_type(filename):
    return mimetypes.guess_type(filename)[0] or 'application/octet-stream'

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
            roundsLeft = 20
            while(roundsLeft >= 0):
                if(self._guiClientProcess.is_alive()):
                    time.sleep(1)
                    print ".",
                    roundsLeft -= 1
                else:
                    roundsLeft = -1
            print "."
            self._guiClientProcess.join(1.0)
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

    def requestConfigState(self, oldState):
        commandXml = MiniXml("configStateRequest")
        commandXml.addAttribute("oldState", oldState)
        self._commandQueue.put(commandXml.getXmlString())

    def requestConfiguration(self, path=None):
        commandXml = MiniXml("configurationRequest")
        if(path == None):
            path = "root"
        commandXml.addAttribute("path", path)
        self._commandQueue.put(commandXml.getXmlString())

    def requestLatestControllers(self):
        commandXml = MiniXml("latestMidiContollersRequest")
        self._commandQueue.put(commandXml.getXmlString())

    def sendConfiguration(self, xmlString):
        self._commandQueue.put(xmlString)

    def requestConfigList(self):
        commandXml = MiniXml("configFileRequest")
        commandXml.addAttribute("type", "list")
        self._commandQueue.put(commandXml.getXmlString())

    def requestConfigChange(self, configName):
        commandXml = MiniXml("configFileRequest")
        commandXml.addAttribute("type", "load")
        commandXml.addAttribute("name", configName)
        self._commandQueue.put(commandXml.getXmlString())

    def requestConfigSave(self, configName):
        commandXml = MiniXml("configFileRequest")
        commandXml.addAttribute("type", "save")
        commandXml.addAttribute("name", configName)
        self._commandQueue.put(commandXml.getXmlString())

    class ResponseTypes():
        FileDownload, ThumbRequest, NoteList, TrackState, ConfigState, Configuration, LatestControllers, ConfigFileList = range(8)

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
                        returnValue = (self.ResponseTypes.FileDownload, fileName)
                elif(serverXml.tag == "thumbRequest"):
                    noteTxt = serverXml.get("note")
                    noteTime = float(serverXml.get("time", "0.0"))
                    fileName = serverXml.get("fileName")
                    if((noteTxt == None) or (fileName == None)):
                        print "ERRORRRRRRR!!!!! note"
                        return (self.ResponseTypes.ThumbRequest, None)
                    noteId = max(min(int(noteTxt), 127), 0)
#                    print "Got thumbRequest response: %s at %.2f with filename: %s" % (noteTxt, noteTime, fileName)
                    returnValue = (self.ResponseTypes.ThumbRequest, (noteId, noteTime, fileName))
                elif(serverXml.tag == "noteListRequest"):
#                    returnValue = (self.ResponseTypes.NoteList, None)
                    listTxt = serverXml.get("list")
#                    print "Got noteListRequest response: list: %s" % (listTxt)
                    returnValue = (self.ResponseTypes.NoteList, listTxt.split(',', 128))
                elif(serverXml.tag == "trackStateRequest"):
#                    returnValue = (self.ResponseTypes.TrackState, None)
                    listTxt = serverXml.get("list")
#                    print "Got trackStateRequest response: list: %s" % (listTxt)
                    returnValue = (self.ResponseTypes.TrackState, listTxt.split(',', 128))
                elif(serverXml.tag == "configStateRequest"):
#                    returnValue = (self.ResponseTypes.ConfigState, None)
                    configId = serverXml.get("id")
#                    print "Got configStateRequest response: list: %s" % (configId)
                    returnValue = (self.ResponseTypes.ConfigState, int(configId))
                elif(serverXml.tag == "configuration"):
                    returnValue = (self.ResponseTypes.Configuration, serverXml)
#                    print "Got configurationRequest response."
                elif(serverXml.tag == "latestMidiControllersRequest"):
                    listTxt = serverXml.get("controllers")
                    returnValue = (self.ResponseTypes.LatestControllers, listTxt.split(',', 128))
#                    print "Got latestMidiControllersRequest response: " + listTxt
                elif(serverXml.tag == "configFileRequest"):
                    listTxt = serverXml.get("configFiles")
                    activeConfig = serverXml.get("activeConfig")
                    returnValue = (self.ResponseTypes.ConfigFileList, (listTxt, activeConfig))
#                    print "Got configFileRequest response: " + listTxt
                else:
                    print "Unknown Message: " + serverResponse
            else:
                print "ERROR! Web server command is not a valid XML: " + str(serverResponse)
        except Empty:
            pass
        return returnValue
