'''
Created on 16. feb. 2012

@author: pcn
'''
from configuration.ConfigurationHolder import ConfigurationHolder,\
    getDefaultDirectories
import sys
import os

class CameraConfiguration(object):
    def __init__(self, configDir, loadAndSave = True):
        self._cameraConfigurationTree = ConfigurationHolder("TaktCameraServer")
        self._cameraConfigurationTree.setSelfclosingTags(['camera', 'screen', 'server'])

        taktConfigDefaultDir, taktVideoDefaultDir = getDefaultDirectories()
        self._taktPlayerAppDataDir = taktConfigDefaultDir

        if((configDir != None) and (configDir != "")):
            self._configurationFile = os.path.join(configDir, "CameraServerConfig.cfg")
        else:
            self._configurationFile = os.path.join(taktConfigDefaultDir, "CameraServerConfig.cfg")

        if(loadAndSave == True):
            self._cameraConfigurationTree.loadConfig(self._configurationFile)

        self._cameraConfig = self._cameraConfigurationTree.addChildUnique("Camera")
        self._cameraConfig.addTextParameter("VideoDir", taktVideoDefaultDir)
        self._cameraConfig.addIntParameter("MaxCameras", 4)

        self._screenConfig = self._cameraConfigurationTree.addChildUnique("Screen")
        self._screenConfig.addIntParameter("ResolutionX", 800)
        self._screenConfig.addIntParameter("ResolutionY", 600)
        self._screenConfig.addTextParameter("FullscreenMode", "off") #on, off, auto
        self._screenConfig.addTextParameter("Position", "auto") #auto, xpos,ypos, 0,0 etc.
        if(sys.platform == "darwin"):
            self._screenConfig.addBoolParameter("AvoidScreensaver", False)
        else:
            self._screenConfig.addBoolParameter("AvoidScreensaver", True)
        self._updateScrrenValues()

        self._serverConfig = self._cameraConfigurationTree.addChildUnique("Server")
        self._serverConfig.addTextParameter("WebBindAddress", "0.0.0.0")
        self._serverConfig.addIntParameter("WebPort", 2025)

        if(loadAndSave == True):
            self._cameraConfigurationTree.saveConfigFile(self._configurationFile)

    def _updateScrrenValues(self):
        self._internalResolutionX =  self._screenConfig.getValue("ResolutionX")
        self._internalResolutionY =  self._screenConfig.getValue("ResolutionY")
        self._fullscreenMode =  self._screenConfig.getValue("FullscreenMode")
        self._avoidScreensaverMode =  self._screenConfig.getValue("AvoidScreensaver")
        self._positionAutoMode = True
        self._positionTuplet = (-1, -1)
        positionString = self._screenConfig.getValue("Position")
        if(positionString.lower != "auto"):
            positionList = positionString.split(',')
            if(len(positionList) < 2):
                positionList = positionString.split('.')
            if(len(positionList) < 2):
                positionList = positionString.split(':')
            if(len(positionList) < 2):
                positionList = positionString.split('x')
            if(len(positionList) < 2):
                positionList = positionString.split('X')
            if(len(positionList) == 2):
                self._positionTuplet = (int(positionList[0]), int(positionList[1]))
                self._positionAutoMode = False

    def setFromXmlString(self, xmlString):
        self._cameraConfigurationTree.setFromXmlString(xmlString)
        self._updateScrrenValues()

    def saveConfig(self):
        self._cameraConfigurationTree.saveConfigFile(self._configurationFile)

    def getXmlString(self):
        return self._cameraConfigurationTree.getConfigurationXMLString()

    def setCameraConfig(self, videoDir, numCameras):
        self._cameraConfig.setValue("VideoDir", videoDir)
        self._cameraConfig.setValue("MaxCameras", numCameras)

    def setScreenConfig(self, resX, resY, fullscreenMode, isAutoPos, posX, posY, isAvoidScreensaver):
        self._screenConfig.setValue("ResolutionX", resX)
        self._screenConfig.setValue("ResolutionY", resY)
        self._screenConfig.setValue("FullscreenMode", fullscreenMode)
        self._screenConfig.setValue("AvoidScreensaver", isAvoidScreensaver)
        if(isAutoPos == True):
            self._screenConfig.setValue("Position", "auto")
        else:
            self._screenConfig.setValue("Position", str(posX) + "," + str(posY))
 
    def setServerConfig(self, webAddress, webPort):
        self._serverConfig.setValue("WebBindAddress", webAddress)
        self._serverConfig.setValue("WebPort", webPort)

    def getResolution(self):
        return (self._internalResolutionX, self._internalResolutionY)

    def getFullscreenMode(self):
        return self._fullscreenMode

    def isAutoPositionEnabled(self):
        return self._positionAutoMode

    def isAvoidScreensaverEnabled(self):
        return self._avoidScreensaverMode

    def getPosition(self):
        return self._positionTuplet

    def getWebServerAddress(self):
#        print "WebAdr: " + str(self._serverConfig.getValue("WebBindAddress"))
        return self._serverConfig.getValue("WebBindAddress")

    def getWebServerPort(self):
#        print "WebPort: " + str(self._serverConfig.getValue("WebPort"))
        return self._serverConfig.getValue("WebPort")

    def getAppDataDirectory(self):
        return self._taktPlayerAppDataDir

    def getVideoDir(self):
        return self._cameraConfig.getValue("VideoDir")

    def getMaxCameras(self):
        return self._cameraConfig.getValue("MaxCameras")

