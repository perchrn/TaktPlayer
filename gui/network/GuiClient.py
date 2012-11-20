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
import socket

def guiNetworkClientProcess(host, port, passwd, appDataDirectory, commandQueue, resultQueue):
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
                    noteForceUpdate = getFromXml(commandXml, "forceUpdate", "False")
                    if(noteTxt != None):
                        urlArgs = "?imageThumb=%s&time=%s&forceUpdate=%s" %(noteTxt, noteTime, noteForceUpdate)
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
                    resposeXmlString = requestUrl(hostPort, urlArgs, "text/xml", "trackStateRequest")
                    resultQueue.put(resposeXmlString)
                elif(commandXml.tag == "effectStateRequest"):
                    channelTxt = getFromXml(commandXml, "channel", "None")
                    noteTxt = getFromXml(commandXml, "note", "None")
                    urlArgs = "?effectState=true&channel=%s&note=%s" %(channelTxt, noteTxt)
                    urlArgs = urlSignaturer.getUrlWithSignature(urlArgs)
                    resposeXmlString = requestUrl(hostPort, urlArgs, "text/xml", "effectStateRequest")
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
                        resposeXmlString = requestUrl(hostPort, "%s" %(fileName), "image/jpg", appDataDirectory)
                        resultQueue.put(resposeXmlString)
                elif(commandXml.tag == "configuration"):
                    resposeXmlString = postXMLFile(urlSignaturer, hostPort, "configuration", "active configuration", command)
                    resultQueue.put(resposeXmlString)
                elif(commandXml.tag == "playerConfigurationSend"):
                    xmlString = getFromXml(commandXml, "string", "")
                    if(xmlString != ""):
                        resposeXmlString = postXMLFile(urlSignaturer, hostPort, "playerConfiguration", "player configuration", command)
                        resultQueue.put(resposeXmlString)
                    else:
                        resposeXmlString = MiniXml("playerConfigFileTransfer", "File error! XML string is empty!")
                        resultQueue.put(resposeXmlString)
                elif(commandXml.tag == "configFileRequest"):
                    requestType = getFromXml(commandXml, "type", "list")
                    requestName = getFromXml(commandXml, "name", "None")
                    urlArgs = "?configFileRequest=%s&name=%s" % (requestType, requestName)
                    urlArgs = urlSignaturer.getUrlWithSignature(urlArgs)
                    resposeXmlString = requestUrl(hostPort, urlArgs, "text/xml")
                    resultQueue.put(resposeXmlString)
                elif(commandXml.tag == "playerConfigurationRequest"):
                    urlArgs = "?playerConfigurationRequest=true"
                    urlArgs = urlSignaturer.getUrlWithSignature(urlArgs)
                    resposeXmlString = requestUrl(hostPort, urlArgs, "text/xml")
                    resultQueue.put(resposeXmlString)
                else:
                    resposeXmlString = MiniXml("servermessage", "Unknown command xml: %s" %(command))
                    resultQueue.put(resposeXmlString)
        except Empty:
            pass

def requestUrl(hostPort, urlArgs, excpectedMimeType, appDataDirectory=None, xmlErrorResponseName = "servermessage"):
    try:
        httpConnection = httplib.HTTPConnection(hostPort, timeout=5)
        httpConnection.request("GET", urlArgs)
        serverResponse = httpConnection.getresponse()
        if(serverResponse.status == 200):
            resposeType = serverResponse.getheader("Content-type")
            if(resposeType == excpectedMimeType):
                if(excpectedMimeType == "image/jpg"):
                    pathDir = os.path.dirname(urlArgs)
                    pathFile = os.path.basename(urlArgs)
                    playerFilePath = ""
                    if((pathDir == "/thumbs") or (pathDir == "thumbs")):
                        playerFilePath = "thumbs/%s" % pathFile
                    else:
                        serverMessageXml = MiniXml(xmlErrorResponseName, "Bad directory in response: %s" % pathDir)
                        return serverMessageXml.getXmlString()
                    thumbsDirPath = os.path.normpath(os.path.join(appDataDirectory, "guiThumbs"))
                    if(os.path.exists(thumbsDirPath) == False):
                        os.makedirs(thumbsDirPath)
                    if(os.path.isdir(thumbsDirPath) == False):
                        serverMessageXml = MiniXml(xmlErrorResponseName, "Error! Cannot save thumbnail. \"guiThumbs\" directory is not in: %s" % appDataDirectory)
                        return serverMessageXml.getXmlString()
                    fullFilePath = os.path.join(thumbsDirPath, pathFile)
                    fileHandle=open(fullFilePath, 'wb')
                    fileHandle.write(serverResponse.read())
                    fileHandle.close()
                    downloadMessageXml = MiniXml("fileDownloaded")
                    downloadMessageXml.addAttribute("fileName", fullFilePath)
                    downloadMessageXml.addAttribute("playerFileName", playerFilePath)
                    return downloadMessageXml.getXmlString()
                else:
                    serverResponseData = serverResponse.read()
                    return serverResponseData
            else:
                clientMessageXml = MiniXml(xmlErrorResponseName, "Bad file type from server! Got: %s Expected: %s" % (resposeType, excpectedMimeType))
                return clientMessageXml.getXmlString()
        else:
            clientMessageXml = MiniXml(xmlErrorResponseName, "Server trouble. Server returned status: %d Reason: %s" %(serverResponse.status, serverResponse.reason))
            return clientMessageXml.getXmlString()
        httpConnection.close()
    except socket.timeout:
        clientMessageXml = MiniXml(xmlErrorResponseName, "Got timeout exception while requesting URL: " + urlArgs.split("&sigTime=")[0])
        clientMessageXml.addAttribute("exception", "timeout")
        return clientMessageXml.getXmlString()
    except socket.error as (errno, strerror):
        exception = ""
        description = ""
        if(errno == 10060):
            exception =  "timeout"
        elif(errno == 10061):
            exception = "connectionRefused"
        elif(errno == 11004):
            exception = "resolvError"
        else:
            exception = str(errno)
            description = str(strerror)
        clientMessageXml = MiniXml(xmlErrorResponseName, "Got " + exception + " exception while requesting URL: " + urlArgs.split("&sigTime=")[0])
        clientMessageXml.addAttribute("exception", exception)
        if(description != ""):
            clientMessageXml.addAttribute("description", description)
        return clientMessageXml.getXmlString()
    except Exception, e:
        clientMessageXml = MiniXml(xmlErrorResponseName, "Got exception while requesting URL: " + urlArgs.split("&sigTime=")[0])
        clientMessageXml.addAttribute("exception", str(e))
        return clientMessageXml.getXmlString()

def postXMLFile(urlSignaturer, hostPort, fileType, fileName, xmlString, xmlErrorResponseName = "servermessage"):
    try:
        files = [(fileType, fileName, xmlString)]
        fields = urlSignaturer.getSigantureFieldsForFile(fileType, fileName, xmlString)
        content_type, body = encode_multipart_formdata(fields, files)
        headers = {"Content-type": content_type}
        httpConnection = httplib.HTTPConnection(hostPort, timeout=10)
        httpConnection.request("POST", "", body, headers)
        serverResponse = httpConnection.getresponse()
        if(serverResponse.status == 200):
            resposeType = serverResponse.getheader("Content-type")
            if(resposeType == "text/xml"):
                serverResponseData = serverResponse.read()
                return serverResponseData
            else:
                clientMessageXml = MiniXml(xmlErrorResponseName, "Bad file type from server! Got: %s Expected: %s" % (resposeType, "text/xml"))
                return clientMessageXml.getXmlString()
        else:
            clientMessageXml = MiniXml(xmlErrorResponseName, "Server trouble. Server returned status: %d Reason: %s" %(serverResponse.status, serverResponse.reason))
            return clientMessageXml.getXmlString()
        httpConnection.close()
    except socket.error as (errno, strerror):
        clientMessageXml = MiniXml(xmlErrorResponseName, "Got exception while posting file: " + fileName)
        if(errno == 10060):
            clientMessageXml.addAttribute("exception", "timeout")
        elif(errno == 10061):
            clientMessageXml.addAttribute("exception", "connectionRefused")
        elif(errno == 11004):
            clientMessageXml.addAttribute("exception", "resolvError")
        else:
            clientMessageXml.addAttribute("exception", str(errno))
            clientMessageXml.addAttribute("description", str(strerror))
        return clientMessageXml.getXmlString()
    except Exception, e:
        clientMessageXml = MiniXml(xmlErrorResponseName, "Got exception while posting file: " + fileName)
        clientMessageXml.addAttribute("exception", str(e))
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
    def __init__(self, appDataDirectory):
        self._commandQueue = None
        self._resultQueue = None
        self._lastTrackRequestError = None
        self._appDataDirectory = appDataDirectory

    def startGuiClientProcess(self, host, port, passwd):
        if(passwd == None):
            passwd = getDefaultUrlSignaturePasswd()
        self._commandQueue = Queue(256)
        self._resultQueue = Queue(256)
        self._guiClientProcess = Process(target=guiNetworkClientProcess, args=(host, port, passwd, self._appDataDirectory, self._commandQueue, self._resultQueue))
        self._guiClientProcess.name = "guiNetworkClient"
        self._guiClientProcess.start()

    def requestGuiClientProcessToStop(self):
        if(self._guiClientProcess != None):
            print "Stopping guiNetworkClient"
            self._commandQueue.put("QUIT")

    def hasGuiClientProcessToShutdownNicely(self):
        if(self._guiClientProcess == None):
            return True
        else:
            if(self._guiClientProcess.is_alive() == False):
                self._guiClientProcess = None
                return True
            return False

    def forceGuiClientProcessToStop(self):
        if(self._guiClientProcess != None):
            if(self._guiClientProcess.is_alive()):
                print "GuiNetworkClient did not respond to quit command. Terminating."
                self._guiClientProcess.terminate()
        self._guiClientProcess = None

    def requestActiveNoteList(self):
        commandXml = MiniXml("noteListRequest")
        self._commandQueue.put(commandXml.getXmlString())

    def requestImage(self, noteId, videoPos = 0.0, forceUpdate = False):
        commandXml = MiniXml("thumbnailRequest")
        commandXml.addAttribute("note", str(noteId))
        commandXml.addAttribute("time", "%.2f" % videoPos)
        if(forceUpdate == True):
            commandXml.addAttribute("forceUpdate", "True")
        else:
            commandXml.addAttribute("forceUpdate", "False")
        self._commandQueue.put(commandXml.getXmlString())

    def requestPreview(self):
        self.requestImageFile("thumbs/preview.jpg")

    def requestImageFile(self, fileName):
        commandXml = MiniXml("thumbnailFileRequest")
        commandXml.addAttribute("fileName", fileName)
        self._commandQueue.put(commandXml.getXmlString())

    def requestTrackState(self):
        commandXml = MiniXml("trackStateRequest")
        self._commandQueue.put(commandXml.getXmlString())

    def requestEffectState(self, channel, note):
        commandXml = MiniXml("effectStateRequest")
        commandXml.addAttribute("channel", channel)
        commandXml.addAttribute("note", note)
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

    def requestPlayerConfiguration(self):
        commandXml = MiniXml("playerConfigurationRequest")
        self._commandQueue.put(commandXml.getXmlString())

    def requestLatestControllers(self):
        commandXml = MiniXml("latestMidiContollersRequest")
        self._commandQueue.put(commandXml.getXmlString())

    def sendConfiguration(self, xmlString):
        print "DEBUG pcn: sending config:"
        #print xmlString
        self._commandQueue.put(xmlString)

    def sendPlayerConfiguration(self, xmlString):
#        print "DEBUG " * 20
#        print xmlString
#        print "DEBUG " * 20
        commandXml = MiniXml("playerConfigurationSend")
        commandXml.addAttribute("string", xmlString)
        self._commandQueue.put(commandXml.getXmlString())

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

    def requestConfigNew(self, configName):
        commandXml = MiniXml("configFileRequest")
        commandXml.addAttribute("type", "new")
        commandXml.addAttribute("name", configName)
        self._commandQueue.put(commandXml.getXmlString())

    class ResponseTypes():
        FileDownload, ThumbRequest, Preview, NoteList, TrackState, EffectState, TrackStateError, ConfigState, Configuration, PlayerConfiguration, ConfigFileTransfer, PlayerConfigFileTransfer, LatestControllers, ConfigFileList = range(14)

    def getServerResponse(self):
        returnValue = (None, None)
        try:
#            queueSize = self._commandQueue.qsize()
#            if(queueSize > 1):
#                print "DEBUG pcn: self._commandQueue queue size: " + str(queueSize)
            serverResponse = self._resultQueue.get_nowait()
            serverXml = stringToXml(serverResponse)
            if(serverXml != None):
#                queueSize = self._resultQueue.qsize()
#                if(queueSize > 1):
#                    print "DEBUG pcn: self._resultQueue queue size: " + str(queueSize)
                if(serverXml.tag == "servermessage"):
                    print "GuiClient Message: " + serverXml.get("message")
                elif(serverXml.tag == "fileDownloaded"):
                    playerFileName = serverXml.get("playerFileName")
                    fileName = serverXml.get("fileName")
                    if(playerFileName == None):
                        playerFileName = ""
                    if(fileName == None):
                        print "ERRORRRRRRR!!!!! file"
                        returnValue = (self.ResponseTypes.FileDownload, None)
                    else:
                        returnValue = (self.ResponseTypes.FileDownload, (fileName, playerFileName))
                elif(serverXml.tag == "thumbRequest"):
                    noteTxt = serverXml.get("note")
                    noteTime = float(serverXml.get("time", "0.0"))
                    fileName = serverXml.get("fileName")
                    if((noteTxt == None) or (fileName == None)):
#                        print "ERRORRRRRRR!!!!! thumbRequest"
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
                    if(listTxt != None):
#                        print "Got trackStateRequest response: list: %s" % (listTxt)
                        returnValue = (self.ResponseTypes.TrackState, listTxt.split(',', 128))
                        self._lastTrackRequestError = None
                    else:
                        exception  = serverXml.get("exception")
                        if(exception == "timeout"):
                            if(self._lastTrackRequestError != "timeout"):
                                print "Track request timed out."
                                self._lastTrackRequestError = "timeout"
                            returnValue = (self.ResponseTypes.TrackStateError, "timeout")
                        elif(exception == "connectionRefused"):
                            if(self._lastTrackRequestError != "connectionRefused"):
                                print "Track request connection was refused."
                                self._lastTrackRequestError = "connectionRefused"
                            returnValue = (self.ResponseTypes.TrackStateError, "connectionRefused")
                        elif(exception == "resolvError"):
                            if(self._lastTrackRequestError != "resolvError"):
                                print "Track request connection error could not resolve host."
                                self._lastTrackRequestError = "resolvError"
                            returnValue = (self.ResponseTypes.TrackStateError, "resolvError")
                        else:
                            if(self._lastTrackRequestError != "unknown"):
                                print "Unknown Error: " + serverResponse
                                self._lastTrackRequestError = "unknown"
                elif(serverXml.tag == "effectStateRequest"):
                    effectState = serverXml.get("state")
                    guiState = serverXml.get("gui")
                    if((effectState == None) or (guiState == None)):
#                        print "ERRORRRRRRR!!!!! effectStateRequest"
                        return (self.ResponseTypes.EffectState, None)
#                    print "Got effectStateRequest response: %s GUI: %s" % (effectState, guiState)
                    returnValue = (self.ResponseTypes.EffectState, (effectState, guiState))
                elif(serverXml.tag == "configStateRequest"):
#                    returnValue = (self.ResponseTypes.ConfigState, None)
                    configId = serverXml.get("id")
#                    print "Got configStateRequest response: list: %s" % (configId)
                    returnValue = (self.ResponseTypes.ConfigState, int(configId))
                elif(serverXml.tag == "configuration"):
                    returnValue = (self.ResponseTypes.Configuration, serverXml)
#                    print "Got configurationRequest response."
                elif(serverXml.tag == "playerConfiguration"):
                    xmlString = serverXml.get("xmlString")
                    returnValue = (self.ResponseTypes.PlayerConfiguration, xmlString)
#                    print "Got playerConfigurationRequest response. " + str(serverResponse)
                elif(serverXml.tag == "configFileTransfer"):
                    returnValue = (self.ResponseTypes.ConfigFileTransfer, serverXml)
#                    print "Got configuration transfer response."
                elif(serverXml.tag == "playerConfigFileTransfer"):
                    returnValue = (self.ResponseTypes.PlayerConfigFileTransfer, serverXml)
#                    print "Got player configuration transfer response."
                elif(serverXml.tag == "latestMidiControllersRequest"):
                    listTxt = serverXml.get("controllers")
                    returnValue = (self.ResponseTypes.LatestControllers, listTxt.split(',', 128))
#                    print "Got latestMidiControllersRequest response: " + listTxt
                elif(serverXml.tag == "configFileRequest"):
                    listTxt = serverXml.get("configFiles")
                    activeConfig = serverXml.get("activeConfig")
                    configSavedStateString = serverXml.get("configIsSaved")
                    if(configSavedStateString == "True"):
                        configSavedState = True
                    else:
                        configSavedState = False
                    returnValue = (self.ResponseTypes.ConfigFileList, (listTxt, activeConfig, configSavedState))
#                    print "Got configFileRequest response: " + listTxt
                else:
                    print "Unknown Message: " + serverResponse
            else:
                print "ERROR! Web server command is not a valid XML: " + str(serverResponse)
        except Empty:
            pass
        return returnValue
