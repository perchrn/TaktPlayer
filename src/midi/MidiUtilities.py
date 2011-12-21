'''
Created on 21. des. 2011

@author: pcn
'''

def noteToLetter(note):
    if(note == 0):
        return "C"
    if(note == 1):
        return "C#"
    if(note == 2):
        return "D"
    if(note == 3):
        return "D#"
    if(note == 4):
        return "E"
    if(note == 5):
        return "F"
    if(note == 6):
        return "F#"
    if(note == 7):
        return "G"
    if(note == 8):
        return "G#"
    if(note == 9):
        return "A"
    if(note == 10):
        return "A#"
    if(note == 11):
        return "H"

def noteToOctavAndLetter(note):
    octav = int(note / 12) - 2
    note = note % 12
    noteLetter = noteToLetter(note)
    return (octav, noteLetter)

def letterToNote(letter):
    if(letter.startswith("C")):
        if(letter.startswith("C#")):
            return 1
        else:
            return 0
    if(letter.startswith("D")):
        if(letter.startswith("D#")):
            return 3
        else:
            return 2
    if(letter.startswith("E")):
        return 4
    if(letter.startswith("F")):
        if(letter.startswith("F#")):
            return 6
        else:
            return 5
    if(letter.startswith("G")):
        if(letter.startswith("G#")):
            return 8
        else:
            return 7
    if(letter.startswith("A")):
        if(letter.startswith("A#")):
            return 10
        else:
            return 9
    if(letter.startswith("H")):
        return 11

def noteStringToNoteNumber(string):
    octav = int(string[0:1])
    note = letterToNote(string[1:])
    noteValue = (((octav + 2) * 12) + note) % 128
    return noteValue


