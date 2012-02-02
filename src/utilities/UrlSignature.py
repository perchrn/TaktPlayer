'''
Created on 2. feb. 2012

@author: pcn
'''
import hashlib
import time

class UrlSignature(object):
    def __init__(self, passwd = "GoGoGrillazEatingBananasFtw"):
        self._passwd = passwd
        self._offset = 0

    def setPasswd(self, passwd):
        self._passwd = passwd

    def calculateOffset(self, serverTime):
        self._offset = serverTime - time.time()

#GoGoGrillazEatingBananasFtw??imageThumb=0C&time=0.00&sigTime=1328193128.45  -> 9bbe4e9f088c673b8bf7e6201eeaecb9eb999b20471734192d7a12ef
#GoGoGrillazEatingBananasFtw?imageThumb=0C&time=0.00&sigTime=1328193128.45
    def _getSignature(self, query):
        if(query.startswith("?") == False):
            query = "?" + query
        passwdAndQuery = self._passwd + query
        return hashlib.sha224(passwdAndQuery).hexdigest()

    def getUrlWithSignature(self, url):
        timeString = str(time.time() + self._offset)
        urlPlusTime = url + "&sigTime=" + timeString
        signature = self._getSignature(urlPlusTime)
        return urlPlusTime + "&sig=%s" % signature

    def verifySignature(self, url):
        urlSplit = url.split("&sig=", 1)
        query = urlSplit[0]
        querySignature = urlSplit[1]
        if(self._getSignature(query) == querySignature):
            urlSplit2 = query.split("&sigTime=", 1)
            query = urlSplit2[0]
            queryTime = float(urlSplit2[1])
            if(abs(time.time() - queryTime) < 30.0):
                return query
            else:
                print "abs(time.time() - queryTime) >= 30.0 " + str(abs(time.time() - queryTime)) + " time: " + str(time.time()) + "queryTime: " + str(queryTime)
        else:
            print "self._getSignature(query) != querySignature " + str(self._getSignature(query)) + " X " + str(querySignature)
        return None

def getDefaultUrlSignaturePasswd():
    return "GoGoGrillazEatingBananasFtw"

