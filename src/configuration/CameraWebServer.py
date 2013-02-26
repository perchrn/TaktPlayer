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

    def do_GET(self):
        global oldFileNameList
        parsed_path = urlparse.urlparse(self.path)

        queryDict = urlparse.parse_qsl(parsed_path.query)

        cameraIdString = self._getKeyValueFromList(queryDict, 'cameraId', None)
        checkOnlyString = self._getKeyValueFromList(queryDict, 'check', None)
        timeStampString = self._getKeyValueFromList(queryDict, 'timeStamp', None)

        if(cameraIdString != None):
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
                self.send_error(404, "List error!")
                webInputQueue.put(serverMessageXml.getXmlString())
                return
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
            serverMessageXml = MiniXml("servermessage", "Bad request from client. Query: %s Client: %s:%d" % (parsed_path.query, self.client_address[0], self.client_address[1]))
            self.send_error(404, "Unknown request!")
            webInputQueue.put(serverMessageXml.getXmlString())
        return

    def do_POST(self):
        pass

    def _returnXmlRespose(self, message):
        self.send_response(200)
        self.send_header("Content-type", "text/xml")
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



