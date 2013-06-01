'''
Created on 2013-3-30
@author: Bobi Pu, bobi.pu@usc.edu
'''

from bs4 import BeautifulSoup
import urllib2
from DateConverter import MTVSearchDateToSaturday, lastSaturday
from StringCleaner import cleanMTVSearchResultTitle, cleanUnicode
from DBController import DBController

class MusicReviewsExtracotr:
    def __init__(self):
        pass
    
    def extractReviewsToBD(self, songList):
        db = DBController()
        for i, song in enumerate(songList):
            print i
            try:
                review = self.extractReviewFromMTV(song)
                db.insertMTVReviewToDB(song['id'], review)
            except Exception as e:
                print e
                continue
    
    def extractReviewFromMTV(self, song):
        blogSearchResult = self.searchInMTV(song, 'blog')
        for blog in blogSearchResult:
            blog['content'] = self.extractContent(blog)
        articleSearchResult = self.searchInMTV(song, 'article')
        for article in articleSearchResult:
            article['content'] = self.extractContent(article)
        review = blogSearchResult + articleSearchResult
        return review
    
    def getSearchURL(self, song, searchArea):
        searchKeyword = song['title'] + ' ' + song['artist']
        songURL = urllib2.quote(searchKeyword)
        websiteURL = 'http://www.mtv.com/search/'
        return websiteURL + searchArea + '/?q=' + songURL

    #return list of dict, [{link(String), title(String), date(String, week)}]
    def searchInMTV(self, song, searchArea):   
        if searchArea != 'blog' and searchArea != 'article':
            raise Exception('searchArea ERROR')
        try:
            searchResults = []
            searchURL = self.getSearchURL(song, searchArea)
            page = urllib2.urlopen(searchURL)
            soup = BeautifulSoup(page.read())
            searchItems = soup.findAll(attrs = {'class':'mtvn-grp mtvn-item-content'})
            #FOR accuracy, only take first 10 resutls
            for i, item in enumerate(searchItems):
                if i == 10:
                    break
                try:
                    link = item.contents[1].contents[1].attrs['href']
                    title = cleanMTVSearchResultTitle(item.contents[1].text)
                    dateString = item.contents[3].contents[1].contents[1].text
                    date = MTVSearchDateToSaturday(dateString)
                    searchResults.append({'URL' : link, 'title' : title, 'type' : searchArea, 'week' : date})
                except Exception as e:
                    #some ERROR of parsing certain search result block
                    continue
        except Exception as e:
            print e
        return searchResults
    
    def extractContent(self, textDict):
        try:
            page = urllib2.urlopen(textDict['URL'])
            soup = BeautifulSoup(page.read())
            if textDict['type'] == 'article':
                body = soup.find(attrs = {'class' : 'article-body'})
            else:
                body = soup.find(attrs = {'class' : 'entry'})
            text = ''
            for content in body.contents:
                #iterate among body, check if it's tag class, and name is <p>
                if 'Tag' in type(content).__name__ and content.name == 'p':
                    text += content.text
        except Exception as e:
            #the URL link maybe invalid
            print e
            text = ''
        return cleanUnicode(text)

if __name__ == '__main__':
    extractor = MusicReviewsExtracotr()
    db = DBController()
    songList = db.getSongByWeek(lastSaturday())
    extractor.extractReviewsToBD(songList)