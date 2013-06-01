'''
Created on 2013-3-30
@author: Bobi Pu, bobi.pu@usc.edu
'''
import re

def cleanUnicode(inputString):
    return inputString.strip().encode('ascii', 'ignore')

def cleanMTVSearchResultTitle(inputString):
    inputString = cleanUnicode(inputString).strip()
    return inputString.split(' - ')[0].split('|')[0] 

def cleanSymbolsForXML(inputString):
    return inputString.replace('&', '&amp;').replace('\"', '&quot;').replace('\'', '&apos;').replace('<', '&lt;').replace('>', '&gt;')

def cleanNonAlphanumeric(inputString):
    return re.sub('[^0-9a-zA-Z ]+', '', inputString)

def cleanNonAlphanumericDot(inputString):
    return re.sub('[^0-9a-zA-Z .]+', '', inputString)

def cleanAtrist(inputString):
    return inputString.lower().split('feat')[0].strip()

def cleanTitle(inputString):
    return inputString.lower().strip()

def stringToInt(inputString):
    return int(inputString.replace(',', ''))