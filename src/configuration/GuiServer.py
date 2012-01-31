'''
Created on 26. jan. 2012

@author: pcn
'''

from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
import socket
import urlparse
import cgi
import cgitb
from multiprocessing import Process, Queue
from Queue import Empty
from xml.etree import ElementTree


webInputQueue = Queue(128)

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
        cgitb.enable()
        parsed_path = urlparse.urlparse(self.path)
        queryDict = cgi.parse_qs(parsed_path.query)
        message_parts = [
                'CLIENT VALUES:',
                'client_address=%s (%s)' % (self.client_address,
                                            self.address_string()),
                'command=%s' % self.command,
                'path=%s' % self.path,
                'real path=%s' % parsed_path.path,
                'query=%s' % parsed_path.query,
                'request_version=%s' % self.request_version,
                '',
                'SERVER VALUES:',
                'server_version=%s' % self.server_version,
                'sys_version=%s' % self.sys_version,
                'protocol_version=%s' % self.protocol_version,
                '',
                'HEADERS RECEIVED:',
                ]
        if('test' in queryDict):
            webInputQueue.put("<webquery key=\"test\" value=\"%s\" />" % queryDict['test'])
        else:
            webInputQueue.put("<webquery message=\"test not found\" />")
        if('invalid' in queryDict):
            webInputQueue.put("<webquery key=\"invalid\" value=\"%s\" />" % queryDict['invalid'])
        else:
            webInputQueue.put("<webquery message=\"invalid not found\" />")
        for name, value in sorted(self.headers.items()):
            message_parts.append('%s=%s' % (name, value.rstrip()))
        message_parts.append('')
        message = '\r\n'.join(message_parts)
        self.send_response(200)
        self.end_headers()
        self.wfile.write(message)
        return

def guiWebServerProcess(host, port, commandQueue, resultQueue):
    server = StoppableHTTPServer((host, port), PcnWebHandler)
    commandQueue.put("<servermessage message=\"Started Web server.\"/>")
    run = True
    while run:
        server.handle_request()
        try:
            result = resultQueue.get_nowait()
            if(result == "QUIT"):
                commandQueue.put("<servermessage message=\"Got QUIT command!\"/>")
                run = False
        except Empty:
            pass
        try:
            webRequest = webInputQueue.get_nowait()
            commandQueue.put(webRequest)
        except Empty:
            pass


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
        self._guiServerProcess = Process(target=guiWebServerProcess, args=(host, port, self._commandQueue, self._resultQueue))
        self._guiServerProcess.name = "guiNetworkServer"
        self._guiServerProcess.start()

    def stopGuiServerProcess(self):
        if(self._guiServerProcess != None):
            print "Stopping guiNetworkServer"
            self._resultQueue.put("QUIT")
            self._guiServerProcess.join(20.0)
            if(self._guiServerProcess.is_alive()):
                print "guiNetworkServer did not respond to quit command. Terminating."
                self._guiServerProcess.terminate()
        self._guiServerProcess = None

    def processGuiRequests(self):
        try:
            clientCommand = self._commandQueue.get_nowait()
            clientXml = ElementTree.XML(clientCommand)
            if(clientXml.tag == "servermessage"):
                print "GuiServer Message: " + clientXml.get("message")
            elif(clientXml.tag == "webquery"):
                print "webquery: " + str(clientCommand)
            elif(clientXml.tag == "thumbnailrequest"):
                noteId = int(clientXml.get("note"))
                videoPosition = float(clientXml.get("videoPosition"))
                print "GuiServer client request for note: %d at %f" % (noteId, videoPosition)
                thumbnailString = self._mediaPool.getVideoThumbnail(noteId, videoPosition)
#                self._resultQueue.put("<thumbnailresponse note=\"" + str(noteId) + "\" videoPosition=\"" + str(videoPosition) + "\" data=\"" + base64.b64encode(thumbnailString) + "\"/>")
        except Empty:
            pass



