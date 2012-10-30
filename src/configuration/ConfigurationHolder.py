'''
Created on 11. jan. 2012

@author: pcn
'''
from xml.etree.ElementTree import Element, SubElement
from xml.etree import ElementTree

from BeautifulSoup import BeautifulStoneSoup
import os
import random

def xmlToPrettyString(xml):
    xmlString = ElementTree.tostring(xml, encoding="utf-8", method="xml")
    soup = BeautifulStoneSoup(xmlString)#, selfClosingTags=['global'])
    return soup.prettify()


class ParameterTypes():
    (Bool, Float, Int, Text) = range(4)


class Parameter(object):
    def __init__(self, name, default, value, paramType):
        self._name = name
        self._default = default
        self._value = value
        self._type = paramType

    def getName(self):
        return self._name

    def getValue(self):
        return self._value

    def getType(self):
        return self._type

    def setValue(self, value):
        self._value = value

    def resetToDefault(self):
        if(self._default == None):
            print "ERROR! Cannot reset this value! No default configured. " + self._name
        else:
            self._value = self._default

    def setString(self, string):
        if(self._type == ParameterTypes.Bool):
            if((string.lower() == "true") or (string.lower() == "yes")):
                self._value = True
            else:
                self._value = False
        elif(self._type == ParameterTypes.Float):
            try:
                self._value = float(string)
            except:
                if(self._default != None):
                    self._value = self._default
                else:
                    self._value = -1.0
        elif(self._type == ParameterTypes.Int):
            try:
                self._value = int(string)
            except:
                if(self._default != None):
                    self._value = self._default
                else:
                    self._value = -1
        elif(self._type == ParameterTypes.Text):
            self._value = string
        else:
            self._value = string

    def setDefaultValue(self, defaultValue):
        self._default = defaultValue

class ConfigurationHolder(object):
    def __init__(self, name, parent = None, uniqueName = None, uniqueId = None):
        self._name = name
        self._parent = parent

        self._parameters = []
        self._children = []
        self._uniqueName = uniqueName
        self._uniqueId = uniqueId

        self._loadedXML = None
        self._loadedFileName = ""
        self._unsavedConfig = False

        self._configIsUpdated = True
        self._oldConfigId = -1
        self._configId = -1
        self._updateId()

        self._selfClosingList = None

    def setSelfclosingTags(self, tagList):
        self._selfClosingList = tagList

    def _updateId(self):
        newId = self._configId
        while(newId == self._configId):
            newId = random.randint(1, 999999)
        self._configId = newId

    def getConfigId(self):
        if(self._parent != None):
            return self._parent.getConfigId()
        else:
            if(self._oldConfigId != self._configId):
                self._oldConfigId = self._configId
                if(self._loadedXML != None):
                    #DEBUG pcn:
                    import difflib
                    loadedXml = self._xmlToString(self._loadedXML)
                    generatedXML = self.getConfigurationXMLString()
                    if(generatedXML != loadedXml):
                        print "L"*120
                        print loadedXml
                        print "G"*120
                        print generatedXML
                        print "="*120
                        for line in difflib.context_diff(a=loadedXml, b=generatedXML):
                            print line
    #                    differThing = difflib.SequenceMatcher(a=loadedXml, b=generatedXML)
    #                    for block in differThing.get_matching_blocks():
    #                        print "match at a[%d] and b[%d] of length %d" % block
                        print "="*120
                        print "DEBUG pcn: generatedXML != loadedXML"
            return self._configId

    def addXml(self, xmlPart):
        self._loadedXML = xmlPart

    def loadConfig(self, configName):
        print "Loading config: " + configName
        if(self._unsavedConfig == True):
            self.saveConfigFile(self._loadedFileName + ".bak")
        if(os.path.isabs(configName) == True):
            filePath = os.path.normpath(configName)
        else:
            filePath = os.path.normpath(os.path.join(os.getcwd(), "config", configName))
        self._loadedFileName = filePath
        if(os.path.isfile(filePath) == False):
            print "********** Error loading configuration: \"%s\" **********" %(filePath)
            filePath = os.path.normpath(os.path.join(os.getcwd(), "config", os.path.basename(configName)))
            print "********** Trying package configuration: \"%s\" **********" %(filePath)
        if(os.path.isfile(filePath) == False):
            print "********** Error loading configuration: \"%s\" **********" %(filePath)
            print "**********          Keeping last configuration.          **********"
            return
        try:
            print "DEBUG pcn: loadConfig: " + filePath
            loadFile = open(filePath, 'r')
            xmlString = loadFile.read()
            if(self._selfClosingList != None):
                soup = BeautifulStoneSoup(xmlString, selfClosingTags=self._selfClosingList)
            else:
                soup = BeautifulStoneSoup(xmlString)
            self._loadedXML = ElementTree.XML(soup.prettify())
            self._updateFromXml(self._loadedXML)
            self._unsavedConfig = False
        except:
            print "********** Error loading configuration: \"%s\" **********" %(filePath)
            raise

    def saveConfigFile(self, configName):
        if(configName.endswith(".cfg.bak") == False):
            if(configName.endswith(".cfg") == False):
                configName = configName + ".cfg"
        if(os.path.isabs(configName) == True):
            filePath = os.path.normpath(configName)
        else:
            filePath = os.path.normpath(os.path.join(os.getcwd(), "config", configName))
        try:
            saveFile = open(filePath, 'w')
            xmlString = self.getConfigurationXMLString()
            saveFile.write(xmlString)
            self._loadedFileName = filePath
            self._unsavedConfig = False
        except:
            print "********** Error saving configuration: \"%s\" **********" %(filePath)
            raise

    def newConfigFileName(self, configName):
        if(configName.endswith(".cfg.bak") == False):
            if(configName.endswith(".cfg") == False):
                configName = configName + ".cfg"
        if(os.path.isabs(configName) == True):
            filePath = os.path.normpath(configName)
        else:
            filePath = os.path.normpath(os.path.join(os.getcwd(), "config", configName))
        self._loadedFileName = filePath
        self._unsavedConfig = True

    def getConfigFileList(self, configDir):
        packageConfigDir = os.path.normpath(os.path.join(os.getcwd(), "config"))
        if((configDir != "") and (os.path.isabs(configDir) == True)):
            dirPath = os.path.normpath(configDir)
        else:
            dirPath = packageConfigDir

        fileListList = []
        fileListString = ""

        fileList = os.listdir(dirPath)
        for aFile in fileList:
            if(aFile.endswith(".cfg")):
                if((aFile != "PlayerConfig.cfg") and(aFile != "GuiConfig.cfg")):
                    if(fileListString != ""):
                        fileListString += ";"
                    fileListString += aFile
                    fileListList.append(aFile)

        firstExtraFile = True
        if(dirPath != packageConfigDir):
            fileList = os.listdir(packageConfigDir)
            for aFile in fileList:
                if(aFile.endswith(".cfg")):
                    if((aFile != "PlayerConfig.cfg") and(aFile != "GuiConfig.cfg")):
                        if(fileListList.count(aFile) == 0):
                            if(firstExtraFile == True):
                                fileListString += ";-------------------------"
                                firstExtraFile = False
                            if(fileListString != ""):
                                fileListString += ";"
                            fileListString += aFile

        return fileListString

    def getCurrentFileName(self):
        return os.path.basename(self._loadedFileName)

    def isConfigNotSaved(self):
        return self._unsavedConfig

    def setFromXmlString(self, xmlString):
        if(self._selfClosingList != None):
            soup = BeautifulStoneSoup(xmlString, selfClosingTags=self._selfClosingList)
        else:
            soup = BeautifulStoneSoup(xmlString)
        self._loadedXML = ElementTree.XML(soup.prettify())
        self._updateFromXml(self._loadedXML)
        self._unsavedConfig = True

    def setFromXml(self, xmlConfig):
        self._loadedXML = xmlConfig
        self._updateFromXml(self._loadedXML)
        self._unsavedConfig = True

    def _updateParamsFromXml(self):
        for param in self._parameters:
            oldVal = param.getValue()
            if(self._loadedXML != None):
                xmlValue = self._loadedXML.get(param.getName().lower())
            else:
                xmlValue = None
            if(xmlValue == None):
#                print "defaulting " + param.getName().lower()
                param.resetToDefault()
            else:
#                print "update: " + param.getName() + " val: " + xmlValue
                param.setString(xmlValue)
            if(oldVal != param.getValue()):
                self._configIsUpdated = True

    def _updateFromXml(self, xmlPart):
        if(self._parent != None):
            self._loadedXML = xmlPart
            self._updateParamsFromXml()
        for child in self._children:
            childName = child.getName()
            childUniqueId = child.getUniqueParameterName()
            if(childUniqueId != None):
                childUniqueValue = str(child._findParameter(childUniqueId).getValue())
                if(xmlPart != None):
                    childXmlPart = self._findXmlChild(xmlPart, childName, childUniqueId, childUniqueValue)
                else:
                    childXmlPart = None
            else:
                if(xmlPart != None):
                    childXmlPart = self._findXmlChild(xmlPart, childName)
                else:
                    childXmlPart = None
            child._updateFromXml(childXmlPart)
        self._configIsUpdated = True

    def getName(self):
        return self._name

    def getUniqueParameterName(self):
        return self._uniqueName

    def _findParameter(self, name):
        for param in self._parameters:
            if(param.getName() == name):
                return param
        return None

    def _addParameter(self, name, defaultValue, value, paramType):
#        print "DEBUG pcn: addParameter inId: " + str(self._uniqueId) + " name: " + name + " value: " + str(value)
        foundParam = self._findParameter(name)
        if(foundParam != None):
#            xmlValue = None
#            if(self._loadedXML != None):
#                xmlValue = self._getValueFromXml(self._loadedXML, name)
            if(foundParam.getType() == paramType):
                self._configIsUpdated = True
                foundParam.setDefaultValue(defaultValue)
#                if(xmlValue == None):
#                    print "Warning! Same parameter with same type added! Updating default value."
            else:
                print "Error! Same parameter with different type cannot be added!"
        else:
            self._configIsUpdated = True
            newParam = Parameter(name, defaultValue, value, paramType)
            self._parameters.append(newParam)
            if(self._loadedXML != None):
                self._getValueFromXml(self._loadedXML, name)
    def addBoolParameter(self, name, defaultValue):
        self._addParameter(name, defaultValue, defaultValue, ParameterTypes.Bool)

    def addFloatParameter(self, name, defaultValue):
        self._addParameter(name, defaultValue, defaultValue, ParameterTypes.Float)

    def addIntParameter(self, name, defaultValue):
        self._addParameter(name, defaultValue, defaultValue, ParameterTypes.Int)

    def addTextParameter(self, name, defaultValue):
        self._addParameter(name, defaultValue, defaultValue, ParameterTypes.Text)

    def addTextParameterStatic(self, name, value):
        self._addParameter(name, None, value, ParameterTypes.Text)

    def getValue(self, name):
        foundParameter = self._findParameter(name)
        if(foundParameter != None):
            return foundParameter.getValue()
        else:
            print "Error! Could not find parameter \"" + name +  "\""
            return None

    def removeParameter(self, name):
#        print "DEBUG pcn: removeParameter inId: " + str(self._uniqueId) + " name: " + name
        foundParameter = self._findParameter(name)
        if(foundParameter != None):
            self._parameters.remove(foundParameter)
        
    def _getValueFromXml(self, xml, name):
        param = self._findParameter(name)
        name = name.lower()
        if(param != None):
            value = xml.get(name)
            if(value != None):
                param.setString(value)
                return param.getValue()
            else:
                print "No xml value found for name: %s" % name
                return None
        else:
            print "No param for name: %s..." % name
            return None

    def setValue(self, name, value):
        foundParameter = self._findParameter(name)
        if(foundParameter != None):
            self._configIsUpdated = True
            foundParameter.setValue(value)
        else:
            print "Error! Trying to set unknown parameter!"

    def getConfigurationXML(self):
        root = Element("Configuration")
        if(self._parent != None):
            parentPath = self.getParentPath()
            root.attrib["path"] = parentPath
        self._addSelfToXML(root)
        return root

    def getParentPath(self):
        if(self._parent == None):
            return self._name
        else:
            return self._parent.getParentPath() + "." + self._name

    def getConfigurationXMLString(self):
        root = self.getConfigurationXML()
        xmlString = ElementTree.tostring(root, encoding="utf-8", method="xml")
        if(self._selfClosingList != None):
            soup = BeautifulStoneSoup(xmlString, selfClosingTags=self._selfClosingList)
        else:
            soup = BeautifulStoneSoup(xmlString)
        return soup.prettify()

    def _xmlToString(self, xml):
        xmlString = ElementTree.tostring(xml, encoding="utf-8", method="xml")
        if(self._selfClosingList != None):
            soup = BeautifulStoneSoup(xmlString, selfClosingTags=self._selfClosingList)
        else:
            soup = BeautifulStoneSoup(xmlString)
        return soup.prettify()

    def _printXml(self, xml):
        print self._xmlToString(xml)

    def _addSelfToXML(self, parentNode):
        ourNode = SubElement(parentNode, self._name)
        self._addXMLAttributes(ourNode)
        for child in self._children:
            child._addSelfToXML(ourNode)
#        print "DEBUG pcn: _addSelfToXML: ourNode"
#        self._printXml(ourNode)
#        print "DEBUG pcn: _addSelfToXML: loaded"
#        if(self._loadedXML != None):
#            self._printXml(self._loadedXML)
#        print "DEBUG pcn: _addSelfToXML:"

    def _addXMLAttributes(self, node):
        for param in self._parameters:
            value = param.getValue()
            if isinstance( value, basestring ):
                node.attrib[param.getName()] = value.encode("utf-8").decode("utf-8")
            else:
                node.attrib[param.getName()] = str(value)

    def _findChild(self, name, idName = None, idValue = None):
        lowername = name.lower()
        for child in self._children:
            if(child.getName().lower() == lowername):
                if(idName == None):
                    return child
                else:
                    foundValue = child.getValue(idName)
                    if(foundValue == idValue):
                        return child
        return None

    def _findChildPath(self, path, getValue):
        pathSplit = path.split('.', 32)#Max 32 levels
        if(len(pathSplit) == 1):
            if(getValue == True):
                return self.getValue(path)
            else:
                if(path.lower() == self._name.lower()):
                    return self
                else:
                    return self._findChild(path)
        else:
            if(pathSplit[0].lower() == self._name.lower()):
                child = self
            else:
                child = self._findChild(pathSplit[0])
            if(child != None):
                first = True
                subPath = ""
                for name in pathSplit:
                    if(first == True):
                        first = False
                    else:
                        if(subPath != ""):
                            subPath += "."
                        subPath = subPath + name
                return child._findChildPath(subPath, getValue)
        print "Did not find: " + pathSplit[0] + " in " + self._name + (len)
        return None
        
    def getPath(self, path):
        if(self._parent != None):
            return self._parent.getPath(path)
        else:
            return self._findChildPath(path, False)

    def getValueFromPath(self, path):
        if(self._parent != None):
            return self._parent.getValueFromPath(path)
        else:
            return self._findChildPath(path, True)

    def _findXmlChild(self, loadedXml, name, idName = None, idValue = None):
        if(self._parent == None):
            loadedXml = self._findXmlChildInternal(loadedXml, self._name, idName, idValue)
        return self._findXmlChildInternal(loadedXml, name, idName, idValue)

    def _findXmlChildInternal(self, loadedXml, name, idName = None, idValue = None):
        name = name.lower()
        if(idName != None):
            idName = idName.lower()
        if(loadedXml != None):
#            print "loadedXml len = " + str(len(loadedXml))
            for xmlChild in loadedXml:#self._loadedXML.findall(name):
#                print "tag: " + str(xmlChild.tag)
                if(name == xmlChild.tag):
                    if(idName != None):
                        if(xmlChild.get(idName) == idValue):
#                            print "Found: " + name + " with id " + idName + " = " + str(idValue)
                            return xmlChild
                    else:
#                        print "Found: " + name
                        return xmlChild
        print "Could not find child with name: " + name + " in " + self._name
        return None

    def findXmlChildrenList(self, name):
        if(self._loadedXML == None):
#            print "findXmlChildrenList self._loadedXML == None"
            return None
        name = name.lower()
        return self._loadedXML.findall(name)

    def removeChildUniqueId(self, name, idName, idValue):
        for i in range(len(self._children)):
            child = self._children[i]
            if(child.getName() == name):
                if(idName == None):
                    self._children.pop(i)
                    return True
                else:
                    foundValue = child.getValue(idName)
                    if(foundValue == idValue):
                        self._children.pop(i)
                        return True
        return False

    def findChildUniqueId(self, name, idName, idValue):
        foundChild = self._findChild(name, idName, idValue)
        if(foundChild != None):
#            print "findChildUniqueId: Child found. " + name
            return foundChild
        else:
            return None

    def addChildUniqueId(self, name, idName, idValue, idRaw = None):
        foundChild = self._findChild(name, idName, idValue)
        if(foundChild != None):
            print "Warning! addChildUniqueId: Child exist already. Duplicate name? " + name + " idName: " + str(idName) + " idValue: " + str(idValue)
            return foundChild
        else:
            #print "Add Child Unique: " + name + " idName: " + str(idName) + " idValue: " + str(idValue) + " idRaw: " + str(idRaw)
            self._configIsUpdated = True
            if(idRaw == None):
                idRaw = idValue
            newChild = ConfigurationHolder(name, self, idName, idRaw)
            newChild.addTextParameterStatic(idName, idValue)
            newChild.addXml(self._findXmlChild(self._loadedXML, name, idName, idValue))
            self._children.append(newChild)
            self._children.sort(key=lambda x: x._uniqueId)
            return newChild

    def addChildUnique(self, name):
        foundChild = self._findChild(name)
        if(foundChild != None):
#            print "Warning! addChildUnique: Child exist already. Duplicate name? " + name
            return foundChild
        else:
#            print "Add Child: " + name
            self._configIsUpdated = True
            newChild = ConfigurationHolder(name, self)
            newChild.addXml(self._findXmlChild(self._loadedXML, name))
            self._children.append(newChild)
            return newChild

    def resetConfigurationUpdated(self):
        self._configIsUpdated = False
        for child in self._children:
            child.resetConfigurationUpdated()

    def isConfigurationUpdated(self):
        if(self._configIsUpdated == True):
            self._updateId()
            #print "DEBUG pcn: self._configIsUpdated == True for: " + self._name
            return True
        else:
            for child in self._children:
                if(child.isConfigurationUpdated() == True):
                    self._configIsUpdated = True
                    self._updateId()
                    return True
        return False
