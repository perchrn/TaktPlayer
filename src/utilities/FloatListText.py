'''
Created on 6. aug. 2012

@author: pcn
'''

def textToFloatValues(string, numberOfFloats, strict = False):
    if(string == None):
        stringSplit = []
    else:
        stringSplit = string.split('|')
    values = []
    i = 0
    while(i < numberOfFloats):
        if(i < len(stringSplit)):
            try:
                value = float(stringSplit[i])
            except:
                value = 0.0
            values.append(value)
        else:
            if(strict == True):
                values.append(None)
            else:
                values.append(0.0)
        i += 1
    if(len(values) == 1):
        return values[0]
    return tuple(values)

def floatValuesToString(floatValues):
    outputString = ""
    try:
        iter(floatValues)
    except TypeError:
        value = float(floatValues)
        floatValues = []
        floatValues.append(value)
    for value in floatValues:
        if(outputString == ""):
            outputString = str(value)
        else:
            outputString += "|" + str(value)
    return outputString