'''
Created on 2013-4-1
@author: Bobi Pu, bobi.pu@usc.edu
Extract IMVDB information 
'''

from bs4 import BeautifulSoup
from DateConverter import dateToSaturday, IMVDBDateStringToDate, lastSaturday
import urllib2
from StringCleaner import cleanNonAlphanumericDot, cleanUnicode, stringToInt
from datetime import datetime
from DBController import DBController

class IMVDBDataExtractor(object):
    def __init__(self):
        self.exceptionTitleDict, self.exceptionAritistDict = self.getExceptionDict()
    
    def getExceptionDict(self):
        exceptionTitleDict, exceptionArtistDict = {}, {}
        exceptionArtistDict['p!nk'] = 'pink'
        exceptionArtistDict['b.o.b'] = 'bob'
        exceptionArtistDict['ke$sha'] = 'kesha'
        exceptionArtistDict['weird al yankovic'] = 'weird al yankovic-1'
        exceptionTitleDict['my love'] = 'Medley: Let Me Talk To You/My Love'
        exceptionTitleDict['eminem, 50 cent, lloyd banks & cashis'] = 'eminem'
        return exceptionTitleDict, exceptionArtistDict
    
    def getURL(self, title, artist):
        artistURL = self.getArtistURL(artist)
        songURL = self.getTitleURL(title)
        URL = 'http://imvdb.com/video/' + artistURL + '/' + songURL
        return URL
        
    def getArtistURL(self, artist):
        if artist in self.exceptionAritistDict:
            artist = self.exceptionAritistDict[artist]
        return '-'.join(artist.lower().split()) 

    def getTitleURL(self, title):
        if  title in self.exceptionTitleDict:
            title = self.exceptionTitleDict[title]
        title = cleanNonAlphanumericDot(title)
        return '-'.join(title.lower().split())
        
    def extractDetailStatData(self, tables, URL):
        detailStatDict = {'week' : dateToSaturday(datetime.today()), 'URL' : URL}
        for table in tables:
            tableText = cleanUnicode(table.text)
            if tableText.find('Views') != -1:
                detailStatDict['MVViewCount'] = self.getDetailStatTableData(tableText, 'Views')
                detailStatDict['MVCommentCount'] = self.getDetailStatTableData(tableText, 'Comments')
            else:
                detailStatDict['FBLikeCount'] = self.getDetailStatTableData(tableText, 'Facebook Like Count')
                detailStatDict['FBShareCount'] = self.getDetailStatTableData(tableText, 'Facebook Share Count')
                detailStatDict['FBCommentCount'] = self.getDetailStatTableData(tableText, 'Facebook Comment Count')
                detailStatDict['TwitterCount'] = self.getDetailStatTableData(tableText, 'Twitter')
                detailStatDict['GooglePlusCount'] = self.getDetailStatTableData(tableText, 'GooglePlusOne')
        return detailStatDict
    
    def getDetailStatTableData(self, tableText, column):
        text = tableText.split(column)
        if text[0] == tableText:
            return None
        else:
            return stringToInt(text[1].split()[0])
        
    def extractStatDataFromScript(self, script):
        lines = script.split('\n')
        dateList = []
        dataList = []
        for line in lines:
            if line.find('categories: [') != -1:
                dateLine = line[line.find('[') + 1 : line.find(']') - 1]
                dateList = [IMVDBDateStringToDate(dateString) for dateString in dateLine.split(',')]
            elif line.find('data: [') != -1:
                dataLine = line[line.find('[') + 1 : line.find(']') - 1]
                dataList = [int(cleanUnicode(dataValue)) for dataValue in dataLine.split(',')]
                break
        rawDataList = zip(dateList, dataList)
        return self.filterDataByWeek(rawDataList)
    
    def filterDataByWeek(self, rawDataList):
        #loop item, if equals that week's Saturday, add it to statDataList
        statDataList = []
        for date, data in rawDataList:
            if date == dateToSaturday(date):
                statDataList.append({'week' : date, 'count' : data})
        return statDataList
    
    #print the exception URL
    def extractDataFromIMVDB(self, URL):
        try:
            page = urllib2.urlopen(URL)
            soup = BeautifulSoup(page.read())
            scriptBlocks = soup.findAll('script')
            viewBlockIndex, socialBlockIndex = 4, 5
            for i, script in enumerate(scriptBlocks):
                if script.text.find('Total Video Views') != -1:
                    viewBlockIndex = i
                elif script.text.find('Total Social Interactions') != -1:
                    socialBlockIndex = i
            viewStatDataList = self.extractStatDataFromScript(scriptBlocks[viewBlockIndex].text)
            socialInteractionDataList = self.extractStatDataFromScript(scriptBlocks[socialBlockIndex].text)
            detailStatDataDict = self.extractDetailStatData(soup.findAll(attrs = {'class' : 'table table-condensed'}), URL)
        except:
            raise Exception(URL + '\nURL error')
        return viewStatDataList, socialInteractionDataList, detailStatDataDict
    
    def extractDataToDB(self, songList):
        db = DBController()
        for song in songList:
            try:
                URL = self.getURL(song['title'], song['artist'])
                viewStatDataList, socialInteractionDataList, detailStatDataDict = self.extractDataFromIMVDB(URL)
                db.insertIMVDBDataToDB(song['id'], viewStatDataList, socialInteractionDataList, detailStatDataDict)
            except Exception as e:
                print e
                continue
            
if __name__ == '__main__':
    extractor = IMVDBDataExtractor()
    db = DBController()
#     songList = db.getAllSongs()
    songList = db.getSongByWeek(lastSaturday())
    extractor.extractDataToDB(songList)