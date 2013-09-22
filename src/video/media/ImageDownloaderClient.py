'''
Created on Feb 28, 2013

@author: pcn
'''
from utilities.MiniXml import MiniXml
import httplib
import os
import socket
import shutil
import time

def imageDownloaderProcess(hostPort, urlArgs, useChacheTrick, fileName, messageQueue):
    if((hostPort == None) or (hostPort == "")):
        serverMessageXml = MiniXml("servermessage", "Cannot start image downloader without host information!")
        messageQueue.put(serverMessageXml)
        return
    if((urlArgs == None)):
        serverMessageXml = MiniXml("servermessage", "Cannot start image downloader without URL information! Host: " + str(hostPort))
        messageQueue.put(serverMessageXml)
        return
    if((fileName == None) or (fileName == "")):
        serverMessageXml = MiniXml("servermessage", "Cannot start image downloader without fileName! URL: " + str(hostPort) + "/" + str(urlArgs))
        messageQueue.put(serverMessageXml)
        return

    run = True
    httpConnection = None
    while(run):
        if(httpConnection == None):
            try:
                httpConnection = httplib.HTTPConnection(hostPort, timeout=5)
            except:
                serverMessageXml = MiniXml("servermessage", "Failed to open HTTP connection: " + str(hostPort) + "/" + str(urlArgs))
                messageQueue.put(serverMessageXml)
        if(httpConnection != None):
            errorMessageXmlString = requestUrl(httpConnection, hostPort, urlArgs, useChacheTrick, fileName)
            if(errorMessageXmlString != None):
                messageQueue.put(errorMessageXmlString)

def requestUrl(httpConnection, hostPort, urlArgs, useChacheTrick, saveFileName):
    excpectedMimeType = "image/jpg"
    try:
        if(useChacheTrick == True):
            urlArgs += "#" + time.time()
        httpConnection.request("GET", urlArgs)
        serverResponse = httpConnection.getresponse()
        if(serverResponse.status == 200):
            resposeType = serverResponse.getheader("Content-type")
            if(resposeType == excpectedMimeType):
                pathDir = os.path.dirname(saveFileName)
                if(os.path.exists(pathDir) == False):
                    os.makedirs(pathDir)
                if(os.path.isdir(pathDir) == False):
                    serverMessageXml = MiniXml("servermessage", "Error! Cannot save image. Directory does not exist: %s for file: %s" % (pathDir, saveFileName))
                    return serverMessageXml.getXmlString()
                tmpFile = saveFileName + ".tmp"
                fileHandle=open(tmpFile, 'wb')
                fileHandle.write(serverResponse.read())
                fileHandle.close()
                shutil.move(tmpFile, saveFileName)
                return None
            else:
                clientMessageXml = MiniXml("servermessage", "Bad file type from server! Got: %s Expected: %s. URL: %s Heaers: %s" % (resposeType, excpectedMimeType, (hostPort + "?" + urlArgs), str(serverResponse.getheaders()) ))
                return clientMessageXml.getXmlString()
        else:
            clientMessageXml = MiniXml("servermessage", "Server trouble. Server returned status: %d Reason: %s" %(serverResponse.status, serverResponse.reason))
            return clientMessageXml.getXmlString()
    except socket.timeout:
        clientMessageXml = MiniXml("servermessage", "Got timeout exception while requesting URL: " + urlArgs)
        clientMessageXml.addAttribute("exception", "timeout")
        return clientMessageXml.getXmlString()
    except socket.error as (errno, strerror):
        exception = ""
        description = ""
        if(errno == 10060):
            exception =  "timeout"
        elif((errno == 10061) or (errno == 61)):
            exception = "connectionRefused"
        elif((errno == 10065) or (errno == 65)):
            exception = "noRouteToHost"
        elif((errno == 11004) or (errno == 8)):
            exception = "resolvError"
        else:
            exception = str(errno)
            description = str(strerror)
        clientMessageXml = MiniXml("servermessage", "Got " + exception + " exception while requesting URL: " + hostPort + "?" + urlArgs)
        clientMessageXml.addAttribute("exception", exception)
        if(description != ""):
            clientMessageXml.addAttribute("description", description)
        return clientMessageXml.getXmlString()
    except Exception, e:
        clientMessageXml = MiniXml("servermessage", "Got exception while requesting URL: " + urlArgs)
        clientMessageXml.addAttribute("exception", str(e))
        return clientMessageXml.getXmlString()

