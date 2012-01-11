'''
Created on 11. jan. 2012

@author: pcn
'''
from xml.etree.ElementTree import Element, SubElement
from xml.etree import ElementTree
from BeautifulSoup import BeautifulStoneSoup

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

    def setValue(self, value):
        self._value = value

class ConfigurationHolder(object):
    def __init__(self, name, parent = None):
        self._name = name
        self._parent = parent

        self._parameters = []
        self._children = []

        self._configIsUpdated = True

    def getName(self):
        return self._name

    def _findParameter(self, name):
        for param in self._parameters:
            if(param.getName() == name):
                return param
        return None

    def _addParameter(self, name, defaultValue, value, paramType):
        foundParam = self._findParameter(name)
        if(foundParam != None):
            if(foundParam.getType() == paramType):
                self._configIsUpdated = True
                foundParam.setDefaultValue(defaultValue)
                print "Warning! Same parameter with same type added! Updating default value."
            else:
                print "Error! Same parameter with different type cannot be added!"
        else:
            self._configIsUpdated = True
            newParam = Parameter(name, defaultValue, value, paramType)
            self._parameters.append(newParam)

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
            print "Adding path!!!"
            parentPath = self._parent.getParentPath()
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
        soup = BeautifulStoneSoup(xmlString)
        return soup.prettify()

    def _addSelfToXML(self, parentNode):
        ourNode = SubElement(parentNode, self._name)
        self._addXMLAttributes(ourNode)
        for child in self._children:
            child._addSelfToXML(ourNode)

    def _addXMLAttributes(self, node):
        for param in self._parameters:
            node.attrib[param.getName()] = str(param.getValue())

    def _findChild(self, name, idName = None, idValue = None):
        for child in self._children:
            if(child.getName() == name):
                if(idName == None):
                    return child
                else:
                    foundValue = child.getValue(idName)
                    if(foundValue == idValue):
                        return child
        return None

    def addChildUniqueId(self, name, idName, idValue):
        foundChild = self._findChild(name, idName, idValue)
        if(foundChild != None):
            print "Warning! Child exist already. Duplicate name?"
            return foundChild
        else:
            self._configIsUpdated = True
            newChild = ConfigurationHolder(name, self)
            newChild.addTextParameterStatic(idName, idValue)
            self._children.append(newChild)
            return newChild

    def addChildUnique(self, name):
        foundChild = self._findChild(name)
        if(foundChild != None):
            print "Warning! Child exist already. Duplicate name?"
            return foundChild
        else:
            self._configIsUpdated = True
            newChild = ConfigurationHolder(name, self)
            self._children.append(newChild)
            return newChild

    def resetConfigurationUpdated(self):
        self._configIsUpdated = False

    def isConfigurationUpdated(self):
        if(self._configIsUpdated == True):
            return True
        else:
            for child in self._children:
                if(child.isConfigurationUpdated() == True):
                    self._configIsUpdated = True
                    return True
        return False
