'''
Created on 2013-4-11
@author: Bobi Pu, bobi.pu@usc.edu
'''

from pymongo import MongoClient
from DateConverter import dateToSaturday
from AlchemyAPI import AlchemyAPI
from math import log10
import sys

class DBController(object):
    def __init__(self):
        try:
            self.db = MongoClient().Billboard
        except Exception as e:
            print e
            sys.exit()
        self.alchemyObj = AlchemyAPI() #sentiment analysis API
        self.alchemyObj.loadAPIKey('AlchemyAPIKey.txt')
    
    def insertSong(self, title, artist):
        if self.getSongId(title, artist) is None:
            newId = self.db.song.count()
            self.db.song.insert({'id' : newId, 'title': title, 'artist' : artist})
            return newId
        
    def insertSongFromSongList(self, songList):
        for title, artist in songList:
            self.insertSong(title, artist)
        
    def getSongId(self, title, artist=None):
        song = self.db.song.find_one({'title': title}) if artist is None else self.db.song.find_one({'title': title, 'artist' : artist}) 
        return None if song is None else song['id']
        
    def getSongById(self, songId):
        return self.db.song.find_one({'id' : songId})
    
    def getAllSongs(self):
        return list(self.db.song.find()) 
    
    def getSongByWeek(self, week):
        top50Dict = self.db.top50.find_one({'week' : week})
        if top50Dict is None:
            return None
        else:
            songList = []
            for songId in top50Dict['rank']:
                song = self.db.song.find_one({'id' : songId})
                songList.append(song)
            return songList
    
    def checkTop50ExistInDB(self, date):
        chart = self.db.top50.find_one({'week' : dateToSaturday(date)})
        if chart is None or len(chart['rank']) != 50:
            return False
        else:
            return True
    
    def checkSalesRankExistInDB(self, date):
        chart = self.db.sales.find_one({'week' : dateToSaturday(date)})
        return False if chart is None or len(chart['rank']) != 40 else True
    
    def insertCommentToDB(self, songId, commentsList):
        self.db.youtube.remove({'id' : songId})
        self.db.youtube.insert({'id' : songId, 'comment' : commentsList})
        
    def insertSalesChartToDB(self, week, chart):
        week = dateToSaturday(week)
        self.db.sales.remove({'week' : week})
        songList = []
        for title, artist, _, _, _, _ in chart:
            songId = self.getSongId(title, artist)
            if songId is None:
                songId = self.getSongId(title)
                if songId is None:
                    #only insert new song from Billboard chart
                    songId = None
            songList.append(songId)
        self.db.sales.insert({'week' : week, 'rank' : songList})
        
    def insertTop50ChartToDB(self, week, chart):
        #week is a datetime object, except for date part, other must be zero
        week = dateToSaturday(week) 
        self.db.top50.remove({'week' : week})
        songList = []
        for _, title, artist in chart:
            songId = self.getSongId(title, artist)
            if songId is None:
                songId = self.insertSong(title, artist)
            songList.append(songId)
        self.db.top50.insert({'week' : week, 'rank' : songList})
    
    def insertIMVDBDataToDB(self, songId, viewStatDataList, socialInteractionDataList, detailStatDataDict):
        dataDict = self.db.IMVDB.find_one({'id' : songId})
        if dataDict is not None:
            dataDict['viewCount'] = self.mergeDataList(dataDict['viewCount'], viewStatDataList)
            dataDict['socialInteraction'] = self.mergeDataList(dataDict['socialInteraction'], socialInteractionDataList)
            dataDict['detailData'] = self.mergeDataList(dataDict['detailData'], [detailStatDataDict])
        else:
            dataDict = {'id' : songId, 'viewCount' : viewStatDataList, 'socialInteraction' : socialInteractionDataList, 'detailData' : [detailStatDataDict]}
        self.db.IMVDB.remove({'id' : songId})
        self.db.IMVDB.insert(dataDict)
        
    def mergeDataList(self, oldList, newList):
        sorted(oldList, key= lambda item : item['week'])
        sorted(newList, key= lambda item : item['week'])
        index = 0
        for i, item in enumerate(oldList):
            if item['week'] >= newList[0]['week']:
                index = i
                break
        return oldList[0 : index] + newList
        
    def insertMTVReviewToDB(self, songId, review):
        self.db.MTV.remove({'id' : songId})
        self.db.MTV.insert({'id' : songId, 'review' : review})
        
    def getSongIdListByWeek(self, week):
        return self.db.top50.find_one({'week' : week})['rank']
    
    def getTop50Rank(self, week, songId):
        try:
            index =  self.db.top50.find_one({'week' : week})['rank'].index(songId)
            return index + 1
        except:
            return None

    def getSalesRank(self, week, songId):
        try:
            index = self.db.sales.find_one({'week' : week})['rank'].index(songId)
            return index + 1
        except:
            return None 
    
    def getRadioRank(self, week, songId):
        radioDict = self.db.radio.find_one({'week' : week})
        if radioDict is not None:
            for songDict in radioDict['songs']:
                if songDict['id'] == songId:
                    return int(songDict['rank'])
        return None
    
    def getStreamingRank(self, week, songId):
        streamingDict = self.db.streaming.find_one({'week' : week})
        if streamingDict is not None:
            for songDict in streamingDict['songs']:
                if songDict['id'] == songId:
                    return int(songDict['rank'])
        return None
    
    def getIMVDBData(self, week, songId):
        viewIndex, socialInteractionIndex = None, None #give an avgerage value
        songDict = self.db.IMVDB.find_one({'id' : songId})
        if songDict is not None:
            for viewCountDict in songDict['viewCount']:
                if week == viewCountDict['week']:
                    viewIndex = log10(viewCountDict['count'])
                    break
            for socialDict in songDict['socialInteraction']:
                if week == socialDict['week']:
                    socialInteractionIndex = log10(socialDict['count'])
                    break
        return viewIndex, socialInteractionIndex
      
    def getMTVReviewData(self, week, songId, useAlchemyAPI=False):
        MTVDict = self.db.MTV.find_one({'id' : songId})
        count, text = 0, ''
        if MTVDict is not None and 'review' in MTVDict:
            for review in MTVDict['review']:
                if review['week'] <= week:
                    count += 1
                    if useAlchemyAPI:
                        text += review['content']
        if count == 0:
            return None, None
        else:
            score = self.getSentimentScoreFromAPI(text) if useAlchemyAPI else self.getSentimentScoreFromLIWC(week, songId, 'MTV')                        
            return count, score
    
    def getYoutubeData(self, week, songId, useAlchemyAPI=False):
        youtubeDict = self.db.youtube.find_one({'id' : songId})
        count, text = 0, ''
        if youtubeDict is not None:
            for comment in youtubeDict['comment']:
                if comment['week'] == week:
                    count += 1
                    if useAlchemyAPI:
                        text += comment['comment']
        if count == 0:
            return None, None
        else:
            score = self.getSentimentScoreFromAPI(text) if useAlchemyAPI else self.getSentimentScoreFromLIWC(week, songId, 'youtube')
            return count, score
    
    def getTwitterData(self, week, songId, useAlchemyAPI=False):
        twitterDict = self.db.twitter.find_one({'week' : week})
        count, text = 0, ''
        if twitterDict is not None:
            for songDict in twitterDict['songs']:
                if songDict['id'] == songId:
                    count = len(songDict['tweets'])
                    if useAlchemyAPI:
                        for tweet in songDict['tweets']:
                            text += tweet['text']
        if count == 0:
            return None, None
        else:
            score = self.getSentimentScoreFromAPI(text) if useAlchemyAPI else self.getSentimentScoreFromLIWC(week, songId, 'twitter')
            return count, score
    
    def insertFeatureToDB(self, featureDict):
        self.db.feature.remove({'week' : featureDict['week'], 'id' : featureDict['id']})
        self.db.feature.insert(featureDict)
    
    def getFeature(self, week, songId):
        return self.db.feature({'week' : week, 'song' : songId})
    
    def getSentimentScoreFromAPI(self, text):
        if text is None:
            return 0
        else:
            try:
                result = self.alchemyObj.TextGetTextSentiment(text)
                score = float(result.split('<score>')[1].split('</score>')[0])
                return score * 100 #normalize
            except Exception as e:
                print e
                return 0
    
    def getSentimentScoreFromLIWC(self, week, songId, scoreType):
        sentimentDict = self.db.sentiment.find_one({'week' : week, 'song_id' : songId})
        if sentimentDict is None:
            return 0
        elif scoreType == 'youtube':
            posScore = 0 if sentimentDict['youtube_posemo'] is None else sentimentDict['youtube_posemo']
            negScore = 0 if sentimentDict['youtube_negemo'] is None else sentimentDict['youtube_negemo']
        elif scoreType == 'MTV':
            posScore = 0 if sentimentDict['MTV_posemo'] is None else sentimentDict['MTV_posemo']
            negScore = 0 if sentimentDict['MTV_negemo'] is None else sentimentDict['MTV_negemo']
        elif scoreType == 'twitter':
            posScore = 0 if sentimentDict['twitter_posemo'] is None else sentimentDict['twitter_posemo']
            negScore = 0 if sentimentDict['twitter_negemo'] is None else sentimentDict['twitter_negemo']
        else:
            raise Exception('invalid score type')
        return (posScore - negScore)
    
    def isFeatureInDB(self, week, songId):
        return self.db.feature.find_one({'week' : week, 'id' : songId}) is not None
    
    def getFeatureListByWeek(self, week):
        return list(self.db.feature.find({'week' : week}))
        
    def getAllFeatureListBySong(self, songId):
        return list(self.db.feature.find({'id' : songId}))
    
    def getFeatureVectorByWeekAndSongId(self, week, songId):
        return self.db.feature.find_one({'week' : week, 'id' : songId})
    
    
