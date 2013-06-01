'''
Created on 2013-3-31
@author: Bobi Pu, bobi.pu@usc.edu
Extract charts ranking data from http://top40-charts.com/chart.php?cid=27&date=2013-03-30
'''

import urllib2
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from StringCleaner import stringToInt, cleanTitle, cleanAtrist
from DateConverter import dateToSaturday, lastSaturday
from DBController import DBController

class SalesChartExtractor:
    def __init__(self):
        pass
    
    def getSalesChartFromURL(self, URL):
        page = urllib2.urlopen(URL)
        soup = BeautifulSoup(page.read())
        songs = soup.findAll(attrs = {'class' : 'latc_song'})
        chart = []
        for song in songs:
            rank = stringToInt(song.contents[0].text)
            lastWeek = song.contents[2].text
            if lastWeek == 'New':
                lastWeek = None
            elif lastWeek == 'RE':
                lastWeek = rank
            else:
                lastWeek = stringToInt(lastWeek)   
            peak = stringToInt(song.contents[6].text)
            weeksOnChart = stringToInt(song.contents[7].text)
            title = cleanTitle(song.contents[3].contents[0].contents[0].contents[2].contents[0].text)
            artist = cleanAtrist(song.contents[3].contents[0].contents[0].contents[2].contents[1].text)
            item = (title, artist, rank, lastWeek, peak, weeksOnChart)
            chart.append(item)
        chart.sort(key= lambda song : song[2])
        return chart
    
    def extractSalesRankToDB(self, beginDate=datetime.today(), endDate=datetime.today()):
        if beginDate < datetime(2007, 1, 1) or endDate > datetime.today():
            raise Exception('Invalid input date!')
        beginDate = dateToSaturday(beginDate)
        endDate = dateToSaturday(endDate)
        endDate = endDate - timedelta(days=7) if endDate > datetime.today() else endDate
        iterDate = beginDate
        db = DBController()
        while iterDate <= endDate:
            if db.checkSalesRankExistInDB(iterDate):
                iterDate = iterDate + timedelta(days = 7)
                continue
            URL = self.getURL(iterDate)
            chart = self.getSalesChartFromURL(URL)
            db.insertSalesChartToDB(iterDate, chart)
            iterDate = iterDate + timedelta(days = 7)
    
    def getURL(self, date):
        return 'http://top40-charts.com/chart.php?cid=27&date=' + date.strftime('%Y-%m-%d')

if __name__ == '__main__':
    extractor = SalesChartExtractor()
    extractor.extractSalesRankToDB(lastSaturday())