'''
Created on 16. feb. 2012

@author: pcn
'''
from midi.MidiUtilities import noteStringToNoteNumber
from configuration.ConfigurationHolder import ConfigurationHolder
import sys
import os

class PlayerConfiguration(object):
    def __init__(self, configDir, loadAndSave = True):
        self._playerConfigurationTree = ConfigurationHolder("TaktPlayer")
        self._playerConfigurationTree.setSelfclosingTags(['startup', 'screen', 'server'])

        taktPackageConfigDir = os.path.join(os.getcwd(), "config")
        if(sys.platform == "win32"):
            appDataDir = os.getenv('APPDATA')
            taktConfigDefaultDir = os.path.join(appDataDir, "TaktPlayer")
        elif(sys.platform == "darwin"):
            appDataDir = os.path.join(os.getenv('USERPROFILE') or os.getenv('HOME'), "Library")
            taktConfigDefaultDir = os.path.join(appDataDir, "TaktPlayer")
        else:
            appDataDir = os.getenv('USERPROFILE') or os.getenv('HOME')
            taktConfigDefaultDir = os.path.join(appDataDir, ".TaktPlayer")
        if(os.path.isdir(appDataDir) == True):
            if(os.path.isdir(taktConfigDefaultDir) == False):
                os.makedirs(taktConfigDefaultDir)
            if(os.path.isdir(taktConfigDefaultDir) == False):
                taktConfigDefaultDir = taktPackageConfigDir
                taktVideoDefaultDir = os.path.join(os.getcwd(), "testVideo")
            else:
                taktVideoDefaultDir = os.path.join(taktConfigDefaultDir, "Video")
                if(os.path.isdir(taktVideoDefaultDir) == False):
                    os.makedirs(taktVideoDefaultDir)
                if(os.path.isdir(taktVideoDefaultDir) == False):
                    taktVideoDefaultDir = os.path.join(os.getcwd(), "testVideo")
        else:
            taktConfigDefaultDir = taktPackageConfigDir
            taktVideoDefaultDir = os.path.join(os.getcwd(), "testVideo")
        print "*" * 100
        print "DEBUG pcn: appDataDir: " + str(appDataDir)
        print "DEBUG pcn: taktConfigDefaultDir: " + str(taktConfigDefaultDir)
        print "DEBUG pcn: taktVideoDefaultDir: " + str(taktVideoDefaultDir)
        print "*" * 100

        if((configDir != "") and (configDir != None)):
            self._configurationFile = os.path.join(configDir, "PlayerConfig.cfg")
        else:
            self._configurationFile = os.path.join(taktConfigDefaultDir, "PlayerConfig.cfg")

        if(loadAndSave == True):
            self._playerConfigurationTree.loadConfig(self._configurationFile)

        self._startupConfig = self._playerConfigurationTree.addChildUnique("Startup")
        self._startupConfig.addTextParameter("ConfigDir", taktConfigDefaultDir)
        self._startupConfig.addTextParameter("VideoDir", taktVideoDefaultDir)
        self._startupConfig.addTextParameter("StartConfig", "Default.cfg")
        self._startupConfig.addTextParameter("StartNote", "0C") #"" "-1D", "0C", "2H" etc.

        self._screenConfig = self._playerConfigurationTree.addChildUnique("Screen")
        self._screenConfig.addIntParameter("ResolutionX", 800)
        self._screenConfig.addIntParameter("ResolutionY", 600)
        self._screenConfig.addTextParameter("FullscreenMode", "off") #on, off, auto
        self._screenConfig.addTextParameter("Position", "auto") #auto, xpos,ypos, 0,0 etc.
        self._updateScrrenValues()

        self._serverConfig = self._playerConfigurationTree.addChildUnique("Server")
        self._serverConfig.addBoolParameter("MidiBroadcast", True)
        self._serverConfig.addTextParameter("MidiBindAddress", "0.0.0.0")
        self._serverConfig.addIntParameter("MidiPort", 2020)
        self._serverConfig.addTextParameter("WebBindAddress", "0.0.0.0")
        self._serverConfig.addIntParameter("WebPort", 2021)

        if(loadAndSave == True):
            self._playerConfigurationTree.saveConfigFile(self._configurationFile)

    def _updateScrrenValues(self):
        self._internalResolutionX =  self._screenConfig.getValue("ResolutionX")
        self._internalResolutionY =  self._screenConfig.getValue("ResolutionY")
        self._fullscreenMode =  self._screenConfig.getValue("FullscreenMode")
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
        self._playerConfigurationTree.setFromXmlString(xmlString)
        self._updateScrrenValues()

    def saveConfig(self):
        self._playerConfigurationTree.saveConfigFile(self._configurationFile)

    def getXmlString(self):
        return self._playerConfigurationTree.getConfigurationXMLString()

    def setStartupConfig(self, startConfig, startNote, videoDir, configDir):
        self._startupConfig.setValue("StartConfig", startConfig)
        self._startupConfig.setValue("StartNote", startNote)
        self._startupConfig.setValue("VideoDir", videoDir)
        self._startupConfig.setValue("ConfigDir", configDir)

    def setScreenConfig(self, resX, resY, fullscreenMode, isAutoPos, posX, posY):
        self._screenConfig.setValue("ResolutionX", resX)
        self._screenConfig.setValue("ResolutionY", resY)
        self._screenConfig.setValue("FullscreenMode", fullscreenMode)
        if(isAutoPos == True):
            self._screenConfig.setValue("Position", "auto")
        else:
            self._screenConfig.setValue("Position", str(posX) + "," + str(posY))
 
    def setServerConfig(self, midiBcast, midiAddress, midiPort, webAddress, webPort):
        self._serverConfig.setValue("MidiBroadcast", midiBcast)
        self._serverConfig.setValue("MidiBindAddress", midiAddress)
        self._serverConfig.setValue("MidiPort", midiPort)
        self._serverConfig.setValue("WebBindAddress", webAddress)
        self._serverConfig.setValue("WebPort", webPort)

    def getResolution(self):
        return (self._internalResolutionX, self._internalResolutionY)

    def getFullscreenMode(self):
        return self._fullscreenMode

    def isAutoPositionEnabled(self):
        return self._positionAutoMode

    def getPosition(self):
        return self._positionTuplet

    def getMidiServerUsesBroadcast(self):
#        print "UseBcast: " + str(self._serverConfig.getValue("MidiBroadcast"))
        return self._serverConfig.getValue("MidiBroadcast")

    def getMidiServerAddress(self):
#        print "MidiAdr: " + str(self._serverConfig.getValue("MidiBindAddress"))
        return self._serverConfig.getValue("MidiBindAddress")

    def getMidiServerPort(self):
#        print "MidiPort: " + str(self._serverConfig.getValue("MidiPort"))
        return self._serverConfig.getValue("MidiPort")

    def getWebServerAddress(self):
#        print "WebAdr: " + str(self._serverConfig.getValue("WebBindAddress"))
        return self._serverConfig.getValue("WebBindAddress")

    def getWebServerPort(self):
#        print "WebPort: " + str(self._serverConfig.getValue("WebPort"))
        return self._serverConfig.getValue("WebPort")

    def getVideoDir(self):
        return self._startupConfig.getValue("VideoDir")

    def getConfigDir(self):
        return self._startupConfig.getValue("ConfigDir")

    def getStartConfig(self):
        return self._startupConfig.getValue("StartConfig")

    def getStartNoteNumber(self):
        noteString = self._startupConfig.getValue("StartNote")
        if(noteString == None):
            return -1
        else:
            return noteStringToNoteNumber(noteString)
