'''
Created on 2013-3-26
@author: Bobi Pu, bobi.pu@usc.edu
'''

from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import urllib2
from DateConverter import dateToSaturday
from DBController import DBController
from StringCleaner import cleanAtrist, cleanTitle

class BillboardTop50Extractor(object):
    def __init__(self):
        pass
    
    def getTop50ChartFromURL(self, url):
        page = urllib2.urlopen(url)
        soup = BeautifulSoup(page.read())
        songs = soup.findAll('tr')
        chart = []
        for song in songs:
            rank = int(song.contents[0].text.strip())
            title = cleanTitle(song.contents[1].text)
            artist = cleanAtrist(song.contents[2].text)
            item = (rank, title, artist)
            chart.append(item)
        chart.sort(key=lambda song : song[0])
        return chart
    
    def getURL(self, date):
        return 'http://musicchartsarchive.com/singles-chart/' + date.strftime('%Y-%m-%d')
    
    def extractTop50ToDB(self, beginDate=datetime.today(), endDate=datetime.today()):
        if beginDate < datetime(2007, 1, 1) or endDate > datetime.today():
            raise Exception('Invalid input date!')
        beginDate = dateToSaturday(beginDate)
        endDate = dateToSaturday(endDate)
        endDate = endDate - timedelta(days=7) if endDate > datetime.today() else endDate
        iterDate = beginDate
        db = DBController()
        while iterDate <= endDate:
            if db.checkTop50ExistInDB(iterDate):
                iterDate = iterDate + timedelta(days = 7)
                continue
            url = self.getURL(iterDate)
            chart = self.getTop50ChartFromURL(url)
            db.insertTop50ChartToDB(iterDate, chart)
            iterDate = iterDate + timedelta(days = 7)
            

if __name__ == '__main__':
    extractor = BillboardTop50Extractor()
    extractor.extractTop50ToDB(datetime(2013, 4, 14))