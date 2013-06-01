'''
Created on 2013-3-26
@author: Bobi Pu, bobi.pu@usc.edu
'''

from datetime import datetime, timedelta
from DateConverter import dateToSaturday
from DBController import DBController
import numpy

class FeatureGenerator(object):
    def __init__(self):
        pass
    
    #song comes from last week, charts comes from last week
    def extractFeatureToDB(self, beginWeek, endWeek=datetime.today(), isReload=False, useAlchemyAPI=False):
        if beginWeek < datetime(2007, 1, 7) or endWeek > datetime.today():
            raise Exception('Invalid input date!')
        beginWeek, endWeek = dateToSaturday(beginWeek), dateToSaturday(endWeek)
        endWeek = endWeek - timedelta(days=7) if endWeek > datetime.today() else endWeek
        iterWeek = beginWeek
        db = DBController()
        while iterWeek <= endWeek:
            lastWeek = iterWeek - timedelta(days=7)
            songRankList = db.getSongIdListByWeek(lastWeek)
            for songId in songRankList:
                if isReload == False and db.isFeatureInDB(iterWeek, songId):
                    continue
                featureDict = {}
                featureDict['id'] = songId
                featureDict['week'] = iterWeek
                featureDict['sales'] = db.getSalesRank(lastWeek, songId)
                featureDict['radio'] = db.getRadioRank(lastWeek, songId)
                featureDict['streaming'] = db.getStreamingRank(lastWeek, songId)
                featureDict['MVView'], featureDict['MVSocialInteraction'] = db.getIMVDBData(iterWeek, songId)
                featureDict['MTVReviewCount'], featureDict['MTVReviewScore'] = db.getMTVReviewData(iterWeek, songId, useAlchemyAPI) 
                featureDict['youtubeCommentCount'], featureDict['youtubeCommentScore'] = db.getYoutubeData(iterWeek, songId, useAlchemyAPI)
                featureDict['twitterCount'], featureDict['twitterScore'] = db.getTwitterData(iterWeek, songId, useAlchemyAPI)
                featureDict['rank'] = db.getTop50Rank(iterWeek, songId)
                db.insertFeatureToDB(featureDict)
            iterWeek += timedelta(days=7)
    
    def rankToPopScore(self, rank):
        return (51 - rank) * 2          

    def getFeatureMatrix(self, beginWeek, endWeek=datetime.today(), mode=0, withSongId=False):
        if beginWeek < datetime(2007, 1, 1) or endWeek > datetime.today():
            raise Exception('Invalid input date!')
        beginWeek, endWeek = dateToSaturday(beginWeek), dateToSaturday(endWeek)
        endWeek = endWeek - timedelta(days=7) if endWeek > datetime.today() else endWeek
        iterWeek = beginWeek
        db = DBController()
        matrix = []
        while iterWeek <= endWeek:
            featureList = db.getFeatureListByWeek(iterWeek)
            for featureDict in featureList:
                featureVector = self.featureDictToList(featureDict, mode, withSongId)
                if featureVector is None:
                    continue
                else:
                    matrix.append(featureVector)
            iterWeek += timedelta(weeks=1)
        matrix = numpy.matrix(matrix)
        return matrix 

    #===========================================================================
    # Mode 0: all features
    # Mode 1: only charts
    # Mode 2: only NLP data
    #===========================================================================
    def featureDictToList(self, featureDict, mode=0, withSongId=False):
        if featureDict['rank'] is None:
            return None
        featureDict = self.fillMissingValue(featureDict)
        if mode == 0:
            featureList = [featureDict['sales'], featureDict['radio'], featureDict['streaming'], featureDict['MVView'], featureDict['MVSocialInteraction'],
                           featureDict['MTVReviewCount'], featureDict['MTVReviewScore'], featureDict['youtubeCommentCount'], featureDict['youtubeCommentScore'],
                           featureDict['twitterCount'], featureDict['twitterScore'], self.rankToPopScore(featureDict['rank'])]
        elif mode == 1:
            featureList = [featureDict['sales'], featureDict['radio'], featureDict['streaming'], self.rankToPopScore(featureDict['rank'])]
        elif mode == 2:
            featureList = [featureDict['MVView'], featureDict['MVSocialInteraction'],
                           featureDict['MTVReviewCount'], featureDict['MTVReviewScore'], featureDict['youtubeCommentCount'], featureDict['youtubeCommentScore'],
                           featureDict['twitterCount'], featureDict['twitterScore'], self.rankToPopScore(featureDict['rank'])]
        else:
            raise Exception('Invalid feature generate Mode, should be 0 or 1 or 2')
        if withSongId:
            featureList[:0] = [featureDict['id']]
        return featureList
    
    def fillMissingValue(self, featureDict):
        db = DBController()
        for k,v in featureDict.iteritems():
            if v is None:
                allFeatureList = db.getAllFeatureListBySong(featureDict['id'])
                valueList = []
                for featureVector in allFeatureList:
                    if featureVector[k] is not None:
                        valueList.append(featureVector[k])
                if len(valueList) != 0:
                    featureDict[k] = sum(valueList) / float(len(valueList))
                else:
                    if k == 'radio' or k == 'streaming' or k == 'sales':
                        featureDict[k] = featureDict['rank']
                    elif k == 'MVView':
                        featureDict[k] = 7
                    elif k == 'MVSocialInteraction':
                        featureDict[k] = 4
                    elif k == 'MTVReviewCount':
                        featureDict[k] = 10
                    elif k == 'MTVReviewScore':
                        featureDict[k] = 0
                    elif k == 'youtubeCommentCount':
                        featureDict[k] = 100
                    elif k == 'youtubeCommentScore':
                        featureDict[k] = 3
                    elif k == 'twitterCount':
                        featureDict[k] = 100
                    elif k == 'twitterScore':
                        featureDict[k] = 0
        return featureDict

if __name__ == '__main__':
    fg = FeatureGenerator()
    fg.extractFeatureToDB(datetime(2013,3,16), datetime.today(), isReload=True, useAlchemyAPI=False)

    
    
    
    
    
    
    
    