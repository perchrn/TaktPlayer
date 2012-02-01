'''
Created on 1. feb. 2012

@author: pcn
'''

from xml.sax.saxutils import quoteattr
from xml.etree import ElementTree

class MiniXml(object):
    def __init__(self, name, message=None):
        self._name = name
        self._attributesString = ""
        if(message != None):
            self.addAttribute("message", message)

    def addAttribute(self, key, value):
        escapedValue = str(value)
        self._attributesString += " "
        self._attributesString += key + "=" + quoteattr(escapedValue)

    def getXmlString(self):
        return "<" + self._name + self._attributesString + " />"

def stringToXml(xmlString):
    try:
        return ElementTree.XML(xmlString)
    except:
        print "could not make XML from string: %s" %xmlString
    return None

def getFromXml(xml, key, default = None):
    return xml.get(key, default)
