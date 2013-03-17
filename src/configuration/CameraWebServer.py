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
oldFileNameList = None
taktPlayerAppDataDirectory = ""

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
    def setup(self):
        self.request.settimeout(10)
        BaseHTTPRequestHandler.setup(self)
        self._debugCounter = 0
        self._debugUniqueCounter = 0
        self._debugTimeStamp = int(time.time() / 100)
        self._debugLastFileName = ""

    def do_GET(self):
        global oldFileNameList
        parsed_path = urlparse.urlparse(self.path)

        queryDict = urlparse.parse_qsl(parsed_path.query)

        listOk = False
        fileNameList = None
        try:
            fileNameList = webOutputQueue.get(False)
            if(fileNameList != None):
                listOk = True
        except Empty:
            if(oldFileNameList != None):
                fileNameList = oldFileNameList
                listOk = True
        oldFileNameList = fileNameList
        if(listOk == False):
            serverMessageXml = MiniXml("servermessage", "No file list found!")
            self.send_error(404, "List error! Please wait until server is done initializing...")
            webInputQueue.put(serverMessageXml.getXmlString())
            return

        cameraIdString = self._getKeyValueFromList(queryDict, 'cameraId', None)
        checkOnlyString = self._getKeyValueFromList(queryDict, 'check', None)
        timeStampString = self._getKeyValueFromList(queryDict, 'timeStamp', None)

        if(cameraIdString != None):
            try:
                cameraId = int(cameraIdString)
                fileName = fileNameList[cameraId]
            except:
                serverMessageXml = MiniXml("servermessage", "FileName not found for ID: %d" % (cameraIdString))
                self.send_error(404, "FileName not found for id: %s!" % (cameraIdString))
                webInputQueue.put(serverMessageXml.getXmlString())
            finally:
                if(checkOnlyString == None):
                    self._returnFile(fileName, "image/jpg")
                else:
                    checkResult = MiniXml("checkresult", os.path.basename(fileName))
                    self._returnXmlRespose(checkResult.getXmlString())
        else:
            isMobile = False
            for agentLines in self.headers.getheaders("User-Agent"):
                if(agentLines.count("Mobile") > 0):
                    isMobile = True
            webPage = "<html><head>\n"
            webPage += "<script type=\"text/JavaScript\">\n"
            webPage += "<!--\n"
            webPage += "var cameraId = 0;\n"
            if(isMobile):
                webPage += "var chacheRequest = \"&chacheDummy=\";\n"
            else:
                webPage += "var chacheRequest = \"#\";\n"
            webPage += "var refreshInterval = 100;\n"
            webPage += "var chacheImage = new Image();\n"
            webPage += "chacheImage.src = \"?cameraId=0\";\n"
            webPage += "function updateImage() {\n"
            webPage += "    if(chacheImage.complete) {\n"
            webPage += "        document.getElementById(\"taktImage\").src = chacheImage.src;\n"
            webPage += "        chacheImage = new Image();\n"
            webPage += "        chacheImage.src = \"?cameraId=\" + cameraId + chacheRequest + new Date().getTime();\n"
            webPage += "    }\n"
            webPage += "    setTimeout(updateImage, refreshInterval)\n"
            webPage += "}\n"
            webPage += "function startImageUpdate(seconds) {\n"
            webPage += "        refreshInterval = seconds * 1000;\n"
            webPage += "        updateImage();\n"
            webPage += "}\n"
            webPage += "function changeCamera(newId) {\n"
            webPage += "        cameraId = newId;\n"
            webPage += "}\n"
            webPage += "// -->\n"
            webPage += "</script>\n"
            webPage += "</head>\n"
            webPage += "<body onload=\"JavaScript:startImageUpdate(0.5);\">\n"
            webPage += "<img src=\"?cameraId=0\" id=\"taktImage\" alt=\"Camera image\"><br>\n"
            numCameras = len(fileNameList)
            if(numCameras > 1):
                for i in range(len(fileNameList)):
                    webPage += "<input id=\"Camera " + str(i) + "\" type=\"button\" value=\"Camera " + str(i) + "\" onclick=\"changeCamera(" + str(i) + ");\"/>\n"
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
        if(os.path.isfile(fileName)):
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
        serverLogXml = MiniXml("serverLog")
        serverLogXml.addAttribute("server", self.address_string())
        serverLogXml.addAttribute("timeStamp", self.log_date_time_string())
        serverLogXml.addAttribute("message", formatString%args)
        webInputQueue.put(serverLogXml.getXmlString())


def guiWebServerProcess(host, port, serverMessageQueue, serverCommandQueue, webIQ, webOQ):
    global webInputQueue
    global webOutputQueue
    webInputQueue = webIQ
    webOutputQueue = webOQ
    server = ErrorHandelingHTTPServer((host, port), PcnWebHandler)
    server.timeout = 10.0
    serverMessageXml = MiniXml("servermessage", "Started Web server. Address: %s Port: %d" % (host, port))
    serverMessageQueue.put(serverMessageXml.getXmlString())
    run = True
    while run:
        try:
            server.handle_request()
        except:
            pass
        try:
            result = serverCommandQueue.get_nowait()
            if(result == "QUIT"):
                serverMessageXml = MiniXml("servermessage", "Got QUIT command!")
                serverMessageQueue.put(serverMessageXml.getXmlString())
                run = False
        except Empty:
            pass
        try:
            webServerMessage = webInputQueue.get_nowait()
            serverMessageQueue.put(webServerMessage)
        except Empty:
            pass


class CameraWebServer(object):
    def __init__(self, configHolder):
        self._cameraConfig = configHolder
        self._serverMessageQueue = None
        self._serverCommandQueue = None
        self._webInputQueue = Queue(256)
        self._webOutputQueue = Queue(2)
        self._cameraWebServerProcess = None

    def startCameraWebServerProcess(self):
        self._serverMessageQueue = Queue(256)
        self._serverCommandQueue = Queue(256)
        host = self._cameraConfig.getWebServerAddress()
        port = self._cameraConfig.getWebServerPort()
        self._cameraWebServerProcess = Process(target=guiWebServerProcess, args=(host, port, self._serverMessageQueue, self._serverCommandQueue, self._webInputQueue, self._webOutputQueue))
        self._cameraWebServerProcess.name = "cameraWebServer"
        self._cameraWebServerProcess.start()

    def requestCameraWebServerProcessToStop(self):
        if(self._cameraWebServerProcess != None):
            print "Stopping cameraWebServer"
            self._serverCommandQueue.put("QUIT")

    def hasCameraWebServerProcessShutdownNicely(self):
        if(self._cameraWebServerProcess == None):
            return True
        else:
            if(self._cameraWebServerProcess.is_alive() == False):
                self._cameraWebServerProcess = None
                return True
            return False

    def forceCameraWebServerProcessToStop(self):
        if(self._cameraWebServerProcess != None):
            if(self._cameraWebServerProcess.is_alive()):
                print "Camera server daemon did not respond to quit command. Terminating."
                self._cameraWebServerProcess.terminate()
        self._cameraWebServerProcess = None

    def updateFileNameList(self, fileNameList):
        try:
            self._webOutputQueue.get_nowait()
        except Empty:
            pass
        try:
            self._webOutputQueue.put_nowait(fileNameList)
        except:
            pass

    def processCameraWebServerMessages(self):
        try:
            serverMessage = self._serverMessageQueue.get_nowait()
            serverMessageXml = stringToXml(serverMessage)
            if(serverMessageXml != None):
                if(serverMessageXml.tag == "servermessage"):
                    print "CameraWebServer Message: " + serverMessageXml.get("message")
#                elif(serverMessageXml.tag == "serverLog"):
#                    print "CameraWebServerLog: " + serverMessageXml.get("server"), serverMessageXml.get("timeStamp"), serverMessageXml.get("message")
        except Empty:
            pass



