'''
Created on 6. aug. 2012

@author: pcn
'''

def textToFloatValues(string, numberOfFloats):
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
            values.append(0.0)
        i += 1
    return tuple(values)

def floatValuesToString(floatValues):
    outputString = ""
    for value in floatValues:
        if(outputString == ""):
            outputString = str(value)
        else:
            outputString += "|" + str(value)
    return outputString