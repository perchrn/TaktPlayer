'''
Created on 26. jan. 2012

@author: pcn
'''

from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
import socket
import urlparse
from multiprocessing import Process, Queue
from Queue import Empty
from utilities.MiniXml import MiniXml, stringToXml, getFromXml
import os


webInputQueue = None
webOutputQueue = None

class StoppableHTTPServer(HTTPServer):
    """HTTPServer class with timeout."""

    def get_request(self):
        """Get the request and client address from the socket."""
        # 10 second timeout
        self.socket.settimeout(10.0)
        result = None
        while result is None:
            try:
                result = self.socket.accept()
            except socket.timeout:
                pass
        # Reset timeout on the new socket
        result[0].settimeout(None)
        return result

class PcnWebHandler(BaseHTTPRequestHandler):
    def setup(self):
        self.request.settimeout(10)
        BaseHTTPRequestHandler.setup(self)

    def do_GET(self):
        parsed_path = urlparse.urlparse(self.path)
        queryDict = urlparse.parse_qsl(parsed_path.query)

        if(parsed_path.path.endswith(".jpg")):
            pathDir = os.path.dirname(parsed_path.path)
            pathFile = os.path.basename(parsed_path.path)
            filePath = ""
            dirOk = False
            if((pathDir == "/thumbs") or (pathDir == "thumbs")):
                dirOk = True
                filePath = "thumbs/%s" % pathFile
            else:
                serverMessageXml = MiniXml("servermessage", "Bad directory request sending 404: %s" % pathDir)
                webInputQueue.put(serverMessageXml.getXmlString())
            if(dirOk == True):
                self._returnFile(filePath, "image/jpg")
            else:
                serverMessageXml = MiniXml("servermessage", "Bad file request sending 404: %s" % parsed_path.path)
                self.send_error(404)
                webInputQueue.put(serverMessageXml.getXmlString())

        else:
            imageThumbNote = self._getKeyValueFromList(queryDict, 'imageThumb', None)
            configRequestPath = self._getKeyValueFromList(queryDict, 'configPath', None)
            testString = self._getKeyValueFromList(queryDict, 'test', None)
    
            if(imageThumbNote != None):
                thumbTime = float(self._getKeyValueFromList(queryDict, 'time', 0.0))
                thumbRequestXml = MiniXml("thumbRequest")
                thumbRequestXml.addAttribute("note", imageThumbNote)
                thumbRequestXml.addAttribute("time", "%.2f" % thumbTime)
                webInputQueue.put(thumbRequestXml.getXmlString())
                try:
                    configXmlString = webOutputQueue.get(True, 5.0)
                    self._returnXmlRespose(configXmlString)
                except:
                    serverMessageXml = MiniXml("servermessage", "Timeout waiting for configuration XML: %s" % configRequestPath)
                    self.send_error(500)
                    webInputQueue.put(serverMessageXml.getXmlString())
            if(configRequestPath != None):
                configRequestXml = MiniXml("configRequest")
                configRequestXml.addAttribute("path", configRequestPath)
                webInputQueue.put(configRequestXml.getXmlString())
                try:
                    configXmlString = webOutputQueue.get(True, 5.0)
                    self._returnXmlRespose(configXmlString)
                except:
                    serverMessageXml = MiniXml("servermessage", "Timeout waiting for configuration XML: %s" % configRequestPath)
                    self.send_error(500)
                    webInputQueue.put(serverMessageXml.getXmlString())
            elif(testString != None):
                serverMessageXml = MiniXml("servermessage", "Testing 1 2: %s" % testString)
                self._returnXmlRespose(serverMessageXml.getXmlString())
                webInputQueue.put(serverMessageXml.getXmlString())
            else:
                serverMessageXml = MiniXml("servermessage", "Bad request from client. Query: %s Client: %s:%d" % (parsed_path.query, self.client_address[0], self.client_address[1]))
                self.send_error(404)
                webInputQueue.put(serverMessageXml.getXmlString())
        return

    def _returnXmlRespose(self, message):
        self.send_response(200)
        self.send_header("Content-type", "text/xml")
        self.send_header("Content-length", str(len(message)))
        self.end_headers()
        self.wfile.write(message)

    def _returnFile(self, fileName, mime):
        if(os.path.isfile(fileName)):
            f=open(fileName, 'rb')
            self.send_response(200)
            self.send_header('Content-type', mime)
            self.end_headers()
            self.wfile.write(f.read())
            f.close()
        else:
            serverMessageXml = MiniXml("servermessage", "File not found sending 404: %s" % fileName)
            self.send_error(404)
            webInputQueue.put(serverMessageXml.getXmlString())

    def _getKeyValueFromList(self, keyValueList, key, default=None):
        for keyValue in keyValueList:
            if(keyValue[0] == key):
                return keyValue[1]
        return default

def guiWebServerProcess(host, port, serverMessageQueue, serverCommandQueue, webIQ, webOQ):
    global webInputQueue
    global webOutputQueue
    webInputQueue = webIQ
    webOutputQueue = webOQ
    server = StoppableHTTPServer((host, port), PcnWebHandler)
    serverMessageXml = MiniXml("servermessage", "Started Web server.")
    serverMessageQueue.put(serverMessageXml.getXmlString())
    run = True
    while run:
        server.handle_request()
        try:
            result = serverCommandQueue.get_nowait()
            if(result == "QUIT"):
                serverMessageXml = MiniXml("servermessage", "Got QUIT command!")
                serverMessageQueue.put(serverMessageXml.getXmlString())
                run = False
        except Empty:
            pass


class GuiServer(object):
    def __init__(self, configurationTree, mediaPool):
        self._configurationTree = configurationTree
        self._mediaPool = mediaPool

        self._serverMessageQueue = None
        self._serverCommandQueue = None
        self._webInputQueue = Queue(256)
        self._webOutputQueue = Queue(256)
        self._guiServerProcess = None

    def startGuiServerProcess(self, host, port):
        self._serverMessageQueue = Queue(256)
        self._serverCommandQueue = Queue(256)
        self._guiServerProcess = Process(target=guiWebServerProcess, args=(host, port, self._serverMessageQueue, self._serverCommandQueue, self._webInputQueue, self._webOutputQueue))
        self._guiServerProcess.name = "guiNetworkServer"
        self._guiServerProcess.start()

    def stopGuiServerProcess(self):
        if(self._guiServerProcess != None):
            print "Stopping guiNetworkServer"
            self._serverCommandQueue.put("QUIT")
            self._guiServerProcess.join(20.0)
            if(self._guiServerProcess.is_alive()):
                print "guiNetworkServer did not respond to quit command. Terminating."
                self._guiServerProcess.terminate()
        self._guiServerProcess = None

    def processGuiRequests(self):
        try:
            serverMessage = self._serverMessageQueue.get_nowait()
            serverMessageXml = stringToXml(serverMessage)
            if(serverMessageXml != None):
                if(serverMessageXml.tag == "servermessage"):
                    print "DEBUG: " + str(serverMessage)
                    print "GuiServer Message: " + serverMessageXml.get("message")
        except Empty:
            pass
        try:
            webCommand = self._webInputQueue.get_nowait()
            webCommandXml = stringToXml(webCommand)
            if(webCommandXml != None):
                if(webCommandXml.tag == "servermessage"):
                    print "GuiServer Message: " + webCommandXml.get("message")
                elif(webCommandXml.tag == "thumbRequest"):
                    noteText = getFromXml(webCommandXml, "note", "0C")
                    imageTime = float(getFromXml(webCommandXml, "time", "0.0"))
                    print "GuiServer client request for note: %s at %f" % (noteText, imageTime)
                    thumbnailFileName = self._mediaPool.requestVideoThumbnail(noteText, imageTime)
                    resposeXml = MiniXml("thumbRequest")
                    resposeXml.addAttribute("note", noteText)
                    resposeXml.addAttribute("time", "%.2F" % imageTime)
                    resposeXml.addAttribute("fileName", thumbnailFileName)
                    self._webOutputQueue.put(resposeXml.getXmlString())
                elif(webCommandXml.tag == "configRequest"):
                    path = webCommandXml.get("path")
                    if(path == "root"):
                        path = "musicalvideoplayer"
                    print "DEBUG configRequest path: %s" % path
                    xmlTree = self._configurationTree.getPath(path)
                    if(xmlTree != None):
                        self._webOutputQueue.put(xmlTree.getConfigurationXMLString())
                    else:
                        resposeXml = MiniXml("configRequest", "Could not find path: %s" % path)
                        self._webOutputQueue.put(resposeXml.getXmlString())
                    print "XML: " + xmlTree.getConfigurationXMLString()
                else:
                    print "ERROR! Unknown command from web server: " + str(webCommand)
            else:
                print "ERROR! Web server command is not a valid XML: " + str(webCommand)
        except Empty:
            pass



