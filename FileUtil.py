'''
Created on 2013-4-11
@author: Bobi Pu, bobi.pu@usc.edu
'''
import xml.etree.ElementTree as ET
from StringCleaner import cleanAtrist, cleanTitle

    
def getSongListFromXML(XMLFileDir):
    root = ET.parse(XMLFileDir).getroot()
    songDict = {}
    songList = []
    for song in root.iter('song'):
        title = cleanTitle(song.attrib['title'])
        artist = cleanAtrist(song.attrib['artist'])
        key = title + '_' + artist
        if key not in songDict:
            songDict[key] = True
            songList.append((title, artist))
    return songList
    

def writeListToCSVFile(inputList, fileName, writeId=True):
    with open(fileName, 'w') as f:
        for i, value in enumerate(inputList):
            if writeId:
                line = str(i) + ',\"' + value + '\"\n'
            else:
                line = '\"' + value + '\"\n'
            f.write(line)         
    
