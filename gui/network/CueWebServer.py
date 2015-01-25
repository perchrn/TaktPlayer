'''
Created on 26. feb. 2013

@author: pcn
'''

from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
import urlparse
from multiprocessing import Process, Queue
from  multiprocessing.queues import Queue as QueueClass
from Queue import Empty, Full
from utilities.MiniXml import MiniXml, stringToXml
import os
import sys
import socket
import time

class SingleSizeQueue(QueueClass):
    def put(self, obj, block=True, timeout=None):
        try:
            self.get_nowait()
        except Empty:
            pass
        assert not self._closed
        if not self._sem.acquire(block, timeout):
            raise Full

        self._notempty.acquire()
        try:
            if self._thread is None:
                self._start_thread()
            self._buffer.append(obj)
            self._notempty.notify()
        finally:
            self._notempty.release()

    def get(self, block=True, timeout=None):
        if block and timeout is None:
            self._rlock.acquire()
            try:
                res = self._buffer[0]
                self._sem.release()
                return res
            finally:
                self._rlock.release()

        else:
            if block:
                deadline = time.time() + timeout
            if not self._rlock.acquire(block, timeout):
                raise Empty
            try:
                if block:
                    timeout = deadline - time.time()
                    if timeout < 0 or not self._poll(timeout):
                        raise Empty
                elif not self._poll():
                    raise Empty
                res = self._buffer[0]
                self._sem.release()
                return res
            finally:
                self._rlock.release()

webInputQueue = None
webOutputQueue = None
urlSignaturer = None
oldStreamName = None

class ErrorHandelingHTTPServer(HTTPServer):
    def handle_error(self, request, client_address):
        """Handle socket errors.    """
        import traceback
        cla, exc, trbk = sys.exc_info()
        if(cla == socket.error):
            cla, exc, trbk = sys.exc_info()
            try:
                excArgs = exc.args
            except KeyError:
                excArgs = "<no args>"
            excTb = traceback.format_tb(trbk, 5)
            if(webOutputQueue != None):
                serverExceptionXml = MiniXml("serverException")
                serverExceptionXml.addAttribute("client", str(client_address))
                serverExceptionXml.addAttribute("type", "socket.error")
                serverExceptionXml.addAttribute("id", str(excArgs[0]))
                serverExceptionXml.addAttribute("description", str(excArgs[1]))
                serverExceptionXml.addAttribute("traceback", excTb)
                webInputQueue.put(serverExceptionXml.getXmlString())
        else:
            print '-'*40
            print 'Exception happened during processing of request from' + str(client_address)
            traceback.print_exc() # XXX But this goes to stderr!
            print '-'*40

class PcnWebHandler(BaseHTTPRequestHandler):
    global webInputQueue
    global webOutputQueue
    def setup(self):
        self.request.settimeout(10)
        BaseHTTPRequestHandler.setup(self)
        self._debugCounter = 0
        self._debugUniqueCounter = 0
        self._debugTimeStamp = int(time.time() / 100)
        self._debugLastFileName = ""

    def do_GET(self):
        global oldStreamName
        parsed_path = urlparse.urlparse(self.path)

        queryDict = urlparse.parse_qsl(parsed_path.query)


        streamNameString = self._getKeyValueFromList(queryDict, 'streamName', None)
        cueIdString = self._getKeyValueFromList(queryDict, 'cueId', None)
        statusString = self._getKeyValueFromList(queryDict, 'status', None)

        streamId = None

        if((statusString != None) or (streamNameString != None)):
            if(streamNameString == None):
                streamNameString = oldStreamName
            else:
                oldStreamName = streamNameString
            try:
                webInputQueue.put(["streamName", streamNameString])
                resultValues = webOutputQueue.get(True, 5)
                if(resultValues != None):
                    (timingInfo, configName, streamNameList, streamName, streamId) = resultValues
                else:
                    self.send_error(404, "List error! Please wait until server is done initializing...")
                    return
            except Empty:
                self.send_error(404, "Server error! Please try again later!")
                return

        if(statusString != None):
            statusJson = "{\n"
            statusJson += "  \"configName\": \"" + str(configName) + "\",\n"
            statusJson += "  \"timingInfo\": \"" + str(timingInfo) + "\"\n"
            statusJson += "}\n"
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.send_header("Content-length", str(len(statusJson)))
            self.end_headers()
            self.wfile.write(statusJson)
        elif(streamId != None):
            try:
                fileName = streamName
            except:
                serverMessageXml = MiniXml("servermessage", "FileName not found for streamID: %d" % (streamId))
                self.send_error(404, "FileName not found for id: %s!" % (streamNameString))
                webInputQueue.put(serverMessageXml.getXmlString())
            finally:
                self._returnFile("thumbs/preview.jpg", "image/jpg")
        else:
            isMobile = False
            for agentLines in self.headers.getheaders("User-Agent"):
                if(agentLines.count("Mobile") > 0):
                    isMobile = True
            webPage = "<html><head>\n"
            webPage += "<script type=\"text/JavaScript\">\n"
            webPage += "<!--\n"
            webPage += "var configName = \"\";\n"
            webPage += "var streamName = \"\";\n"
            webPage += "var cueId = 0;\n"
            if(isMobile):
                webPage += "var chacheRequest = \"&chacheDummy=\";\n"
            else:
                webPage += "var chacheRequest = \"#\";\n"
            webPage += "var refreshInterval = 100;\n"
            webPage += "var chacheImage = new Image();\n"
            webPage += "function updateImage() {\n"
            webPage += "    if(chacheImage.complete) {\n"
            webPage += "        document.getElementById(\"taktImage\").src = chacheImage.src;\n"
            webPage += "        chacheImage = new Image();\n"
            webPage += "        chacheImage.src = configName + \"?streamName=\" + streamName + \"&cueId=\" + cueId;\n"
            webPage += "    }\n"
            webPage += "}\n"
            webPage += "function getStatus() {\n"
            webPage += "    var xmlhttp = new XMLHttpRequest();\n"
            webPage += "    var url = \"?streamName=\" + streamName + \"&status=true\";\n"
            webPage += "    xmlhttp.onreadystatechange = function() {\n"
            webPage += "        if (xmlhttp.readyState == 4 && xmlhttp.status == 200) {\n"
            webPage += "            var jsonData = JSON.parse(xmlhttp.responseText);\n"
            webPage += "            configName = jsonData.configName;\n"
            webPage += "            cueId = jsonData.cueId;\n"
            webPage += "            (document.getElementById(\"timingInfo\")).innerHTML = jsonData.timingInfo;\n"
            webPage += "        }\n"
            webPage += "    }\n"
            webPage += "    xmlhttp.open(\"GET\", url, true);\n"
            webPage += "    xmlhttp.send();\n"
            webPage += "}\n"
            webPage += "function updateStatus() {\n"
            webPage += "    getStatus();\n"
            webPage += "    updateImage();\n"
            webPage += "    setTimeout(updateStatus, refreshInterval);\n"
            webPage += "}\n"
            webPage += "function startStatusUpdate(seconds) {\n"
            webPage += "        refreshInterval = seconds * 1000;\n"
            webPage += "        updateStatus();\n"
            webPage += "}\n"
            webPage += "function changeCueStream(newId) {\n"
            webPage += "        streamName = newId;\n"
            webPage += "}\n"
            webPage += "// -->\n"
            webPage += "</script>\n"
            webPage += "</head>\n"
            webPage += "<body onload=\"JavaScript:startStatusUpdate(0,5);\">\n"
            webPage += "<div id=\"timingInfo\">dummy</div>\n"
            webPage += "<img src=\"\" id=\"taktImage\" alt=\"Cue stream: UNKNOWN\"><br>\n"
#            numCues = len(streamNameList)
#            if(numCues > 1):
#                for i in range(len(streamNameList)):
#                    webPage += "<input id=\"" + streamNameList[i] + "\" type=\"button\" value=\"" + streamNameList[i] + "\" onclick=\"changeCueStream(" + streamNameList[i] + ");\"/>\n"
            webPage += "</body></html>\n"
            self._returnHtmlRespose(webPage)

#            serverMessageXml = MiniXml("servermessage", "DEBUG pcn: %s %s ***%s***" % (parsed_path.query, str(self.headers), str(self.headers.getheaders("User-Agent"))))
#            webInputQueue.put(serverMessageXml.getXmlString())
        return

    def do_POST(self):
        self.send_error(404, "Unknown POST request!")

    def _returnXmlRespose(self, message):
        self.send_response(200)
        self.send_header("Content-type", "text/xml")
        self.send_header("Content-length", str(len(message)))
        self.end_headers()
        self.wfile.write(message)

    def _returnHtmlRespose(self, message):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.send_header("Content-length", str(len(message)))
        self.end_headers()
        self.wfile.write(message)

    def _returnFile(self, fileName, mime):
        serverMessageXml = MiniXml("servermessage", "Trying %s" % (fileName))
        webInputQueue.put(serverMessageXml.getXmlString())
        if(os.path.isfile(os.path.normpath(fileName))):
            fileHandle=open(fileName, 'rb')
            self.send_response(200)
            self.send_header('Content-type', mime)
            self.end_headers()
            self.wfile.write(fileHandle.read())
            fileHandle.close()
            self._debugCounter += 1
            if(self._debugLastFileName != fileName):
                self._debugUniqueCounter += 1
                self._debugLastFileName = fileName
            timeStampId = int(time.time() / 100)
            if(timeStampId != self._debugTimeStamp):
                serverMessageXml = MiniXml("servermessage", "DEBUG pcn: Delivered %d images. %d unique." % (self._debugCounter, self._debugUniqueCounter))
                self._debugTimeStamp = timeStampId
                self._debugCounter = 0
                self._debugUniqueCounter = 0
        else:
            serverMessageXml = MiniXml("servermessage", "File not found sending 404: %s" % (fileName))
            self.send_error(404, "Returnfile: File not found: %s" % (fileName))
            webInputQueue.put(serverMessageXml.getXmlString())

    def _getKeyValueFromList(self, keyValueList, key, default=None):
        for keyValue in keyValueList:
            if(keyValue[0] == key):
                return keyValue[1]
        return default

    def log_message(self, formatString, *args):
        pass
#        serverLogXml = MiniXml("serverLog")
#        serverLogXml.addAttribute("server", self.address_string())
#        serverLogXml.addAttribute("timeStamp", self.log_date_time_string())
#        serverLogXml.addAttribute("message", formatString%args)
#        webInputQueue.put(serverLogXml.getXmlString())


def guiWebServerProcess(host, port, serverMessageQueue, serverCommandQueue, webIQ, webOQ):
    global webInputQueue
    global webOutputQueue
    webInputQueue = webIQ
    webOutputQueue = webOQ
    server = ErrorHandelingHTTPServer((host, port), PcnWebHandler)
    server.timeout = 10.0
    serverMessageXml = MiniXml("servermessage", "Started Web server. Address: %s Port: %d %s" % (host, port, os.path.abspath(os.path.curdir)))
    serverMessageQueue.put(serverMessageXml.getXmlString())
    timingInfo = None
    configName = None
    streamNameList = None
    run = True
    while run:
        try:
            server.handle_request()
        except:
            pass
        empty = False
        while not empty:
            try:
                result = serverCommandQueue.get_nowait()
                if(result != None):
                    if(result == "QUIT"):
                        serverMessageXml = MiniXml("servermessage", "CueServer got QUIT command!")
                        serverMessageQueue.put(serverMessageXml.getXmlString())
                        run = False
                    else:
                        if(result[0] == "taktInfo_timingInfo"):
                            timingInfo = result[1]
                        elif(result[0] == "taktInfo_configName"):
                            configName = result[1]
                        else:
                            streamNameList = result
            except Empty:
                empty = True
        empty = False
        while not empty:
            try:
                webServerMessage = webInputQueue.get_nowait()
                if(webServerMessage[0] == "streamName"):
                    if(len(streamNameList) < 1):
                        webOutputQueue.put(None)
                    else:
                        streamId = 0
                        for i in range(len(streamNameList)):
                            if(streamNameList[i] == webServerMessage[1]):
                                streamId = i
                        streamName = streamNameList[streamId]
                        webOutputQueue.put([timingInfo, configName, streamNameList, streamName, streamId])
                else:
                    serverMessageQueue.put(webServerMessage)
            except Empty:
                empty = True


class CueWebServer(object):
    def __init__(self, configHolder):
        self._cueConfig = configHolder
        self._serverMessageQueue = None
        self._serverCommandQueue = None
        self._webInputQueue = Queue(256)
        self._webOutputQueue = Queue(10)
        self._cueWebServerProcess = None
        self._oldBarPos = None
        self._oldBeatPos = None
        self._oldConfigName = ""
        self._oldStreamConfig = []

    def startCueWebServerProcess(self):
        self._serverMessageQueue = Queue(256)
        self._serverCommandQueue = Queue(256)
        host = self._cueConfig.getCueWebServerAddress()
        port = self._cueConfig.getCueWebServerPort()
        self._cueWebServerProcess = Process(target=guiWebServerProcess, args=(host, port, self._serverMessageQueue, self._serverCommandQueue, self._webInputQueue, self._webOutputQueue))
        self._cueWebServerProcess.name = "cueWebServer"
        self._cueWebServerProcess.start()

    def requestCueWebServerProcessToStop(self):
        if(self._cueWebServerProcess != None):
            print "Stopping cueWebServer"
            self._serverCommandQueue.put("QUIT")

    def hasCueWebServerProcessShutdownNicely(self):
        if(self._cueWebServerProcess == None):
            return True
        else:
            try:
                self._serverMessageQueue.get_nowait()
            except Empty:
                pass
            if(self._cueWebServerProcess.is_alive() == False):
                self._cueWebServerProcess = None
                return True
            return False

    def forceCueWebServerProcessToStop(self):
        if(self._cueWebServerProcess != None):
            if(self._cueWebServerProcess.is_alive()):
                print "Cue server daemon did not respond to quit command. Terminating."
                self._cueWebServerProcess.terminate()
        self._cueWebServerProcess = None

    def updateFromConfig(self, configHolder, activeConfigName):
        self._cueConfig = configHolder
        if(activeConfigName != self._oldConfigName):
            print str(self._oldConfigName) + " != " + str(activeConfigName)
            self._oldConfigName = activeConfigName
            try:
                self._serverCommandQueue.put_nowait(["taktInfo_configName", activeConfigName])
            except:
                pass

        if(self._cueConfig.getCueStreamList() != self._oldStreamConfig):
            print str(self._cueConfig.getCueStreamList()) + " != " + str(self._oldStreamConfig)
            self._oldStreamConfig = self._cueConfig.getCueStreamList()
            try:
                self._serverCommandQueue.put_nowait(self._cueConfig.getCueStreamList())
            except:
                pass

    def updateTimingInfo(self, bar, beat):
        if((self._oldBarPos != bar) or (self._oldBeatPos != beat)):
            self._oldBarPos = bar
            self._oldBeatPos = beat
            try:
                self._serverCommandQueue.put_nowait(["taktInfo_timingInfo" , str(bar) + ":" + str(beat)])
            except:
                pass

    def processCueWebServerMessages(self):
        try:
            serverMessage = self._serverMessageQueue.get_nowait()
            serverMessageXml = stringToXml(serverMessage)
            if(serverMessageXml != None):
                if(serverMessageXml.tag == "servermessage"):
                    print "CueWebServer Message: " + serverMessageXml.get("message")
                elif(serverMessageXml.tag == "serverLog"):
                    print "CueWebServerLog: " + serverMessageXml.get("server"), serverMessageXml.get("timeStamp"), serverMessageXml.get("message")
        except Empty:
            pass



