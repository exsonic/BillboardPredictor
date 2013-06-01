'''
Created on 2013-4-20
@author: Bobi Pu, bobi.pu@usc.edu
'''

from FeatureGenerator import FeatureGenerator
from sklearn import linear_model, cross_validation, ensemble, metrics
from datetime import datetime, timedelta
from DateConverter import dateToSaturday
from DBController import DBController
import numpy, itertools

class RegressionModel(object):
    def __init__(self):
        pass
    
    def kFoldData(self, matrix, k=5):
        X = matrix[:, 0:-1]
        y = matrix[:, -1]
        kFold = cross_validation.KFold(n=matrix.shape[0], n_folds=k, shuffle=False)
        for trainIndex, testIndex in kFold:
            X_train, X_test, y_train, y_test = X[trainIndex], X[testIndex], y[trainIndex], y[testIndex]
            yield X_train, X_test, y_train, y_test
    
    def getRankArray(self, scoreArray):
        scoreList = scoreArray.tolist()
        sortedList = sorted(scoreList, reverse=True)
        rankList = [0] * len(scoreList)
        for i, score in enumerate(sortedList):
            index = scoreList.index(score)
            rankList[index] = i + 1
        return numpy.asarray(rankList)
    
    def train(self, beginWeek, endWeek, featureMode=0, regressionModelType=0):
        if beginWeek < datetime(2007, 1, 1) or endWeek > datetime.today():
            raise Exception('Invalid input date!')
        beginWeek, endWeek = dateToSaturday(beginWeek), dateToSaturday(endWeek)
        endWeek = endWeek - timedelta(days=7) if endWeek > datetime.today() else endWeek
        iterWeek = beginWeek 
        fg = FeatureGenerator()
        regression = self.getRegressionModel(regressionModelType)
        while iterWeek <= endWeek:
            matrix_train = fg.getFeatureMatrix(iterWeek, iterWeek, featureMode)
            X_train, y_train = matrix_train[:, 0:-1], matrix_train[:, -1]
            regression.fit(X_train, y_train)
            iterWeek += timedelta(weeks=1)
        return regression
    
    def test(self, model, week, featureMode=0, outputSong=False, x=10):
        fg = FeatureGenerator()
        matrix_test = fg.getFeatureMatrix(week, week, featureMode, True)
        X_test, y_test = matrix_test[:, 1:-1], matrix_test[:, -1]
        songIdList = matrix_test[:, 0].tolist()
        songIdList = list(itertools.chain(*songIdList))
        y_pred = model.predict(X_test)
        y_pred = self.getRankArray(y_pred)
        y_test = self.getRankArray(y_test)
        r2Score = metrics.r2_score(y_test, y_pred)
        meanSquare = metrics.mean_squared_error(y_test, y_pred)
        rankEvalScore = self.getRankEvalationScore(y_pred, y_test)
        print 'r2 score: ', r2Score, 'mean square error: ', meanSquare, ' rank score: ', rankEvalScore
        predTopX, realTopX = self.outputTopX(songIdList, y_pred.tolist()), self.outputTopX(songIdList, y_test.tolist())
        inclusiveAccuracy, rankMatchAccuracy = self.computTopXAccuracy(predTopX, realTopX)
        print 'Top', x, 'inclusive accuracy: ', inclusiveAccuracy, ',Top', x, 'rank match accuracy: ', rankMatchAccuracy
        if outputSong:
            print self.outputTopXSongNames(predTopX), '\n', self.outputTopXSongNames(realTopX)
        return r2Score, meanSquare, rankEvalScore
    
    def outputTopX(self, songIdList, rankList, x=10):
        if x > 40:
            raise Exception('x must be less than 40')
        db = DBController()
        songList = []
        for i in range(1, x+1):
            try:
                index = rankList.index(i)
                songId = songIdList[index]
                songList.append(db.getSongById(songId))
            except:
                continue
        return songList
    
    def outputTopXSongNames(self, songList):
        outputString = ''
        for i, song in enumerate(songList):
            outputString += (str(i+1) + ': ' + song['title'] + ', ')
        return outputString[:-2]
    
    def computTopXAccuracy(self, predTopX, realTopX):
        includeCount, rankMatchCount = 0, 0
        for i, song in enumerate(predTopX):
            if song == realTopX[i]:
                rankMatchCount += 1
            if song in realTopX:
                includeCount += 1
        return float(includeCount) / len(realTopX), float(rankMatchCount) / len(realTopX)
    
    def getRegressionModel(self, regressionModelType):
        if regressionModelType == 0:
            return linear_model.LinearRegression()
        elif regressionModelType == 1:
            return linear_model.Lasso()
        elif regressionModelType == 2:
            return linear_model.Ridge()
        elif regressionModelType == 3:
            return ensemble.RandomForestRegressor()
        else:
            raise Exception('Invalid regressionModelType, value should be 0,1,2,3')
    
    def getRankEvalationScore(self, y_pred, y_test):
        yPredIdRankList, yTestIdRankList = [None] * len(y_pred), [None] * len(y_pred)
        #i as temp songId
        for i, rank in enumerate(y_pred):
            yPredIdRankList[rank-1] = i
        for i, rank in enumerate(y_test):
            yTestIdRankList[rank-1] = i
        yPredSet, yTestSet = self.rankedIdListToPairSet(yPredIdRankList), self.rankedIdListToPairSet(yTestIdRankList)
        intersectionSet = yPredSet.intersection(yTestSet)
        score = len(intersectionSet) / float(len(yTestSet))
        return score
    
    #calculate the baseline
    def rankedIdListToPairSet(self, rankedIdList):
        outputSet = set()
        for i, leftSongId in enumerate(rankedIdList):
            for rightSongId in rankedIdList[i+1::]:
                outputSet.add((leftSongId, rightSongId))
        return outputSet
    
    #===========================================================================
    # baseline type, 0 is rank evaluation. 1 is r2 score, 2 is mean square error
    #===========================================================================
    def computeBaseLine(self, baselineType=0):
        iterWeek, endWeek = datetime(2013,3,23), datetime(2013,4,20)
        db = DBController()
        fg = FeatureGenerator()
        baselineScore = 0
        while iterWeek <= endWeek:
            lastWeek = iterWeek - timedelta(weeks=1)
            featureList = db.getFeatureListByWeek(iterWeek)
            y_pred, y_test = [], []
            for featureVector in featureList:
                songId = featureVector['id']
                lastWeekRank = db.getTop50Rank(lastWeek, songId)
                if lastWeekRank is None:
                    lastWeekScore = 0
                else:
                    lastWeekScore = fg.rankToPopScore(lastWeekRank)
                currentWeekRank = featureVector['rank']
                currentWeekScore = fg.rankToPopScore(currentWeekRank) if currentWeekRank is not None else lastWeekScore
                y_pred.append(lastWeekScore)
                y_test.append(currentWeekScore)
            y_pred, y_test = self.getRankArray(numpy.asarray(y_pred)), self.getRankArray(numpy.asarray(y_test))
            if baselineType == 0:
                baselineScore += self.getRankEvalationScore(y_pred, y_test)
            elif baselineType == 1:
                baselineScore += metrics.r2_score(y_pred, y_test)
            else:
                baselineScore += metrics.mean_squared_error(y_pred, y_test)
            iterWeek += timedelta(weeks=1)
        baselineScore = baselineScore / 5
        print baselineScore
        
    def outputAllResult(self, beginWeek, endWeek, outputSong=False, x=10):
        featureModeDict = {'allFeature' : 0, 'onlyCharts' : 1, 'onlyNLP' : 2}
        regressionModelDict = {'LinearRegression' : 0, 'LassonRegression' :1, 'RidgeRegression' : 2, 'RandomForestRegressor' : 3}
        for featureModeKey, featureModeValue in featureModeDict.iteritems():
            print featureModeKey
            for regressionModelKey, regressionModelValue in regressionModelDict.iteritems():
                print regressionModelKey
                model = self.train(beginWeek, endWeek, featureModeValue, regressionModelValue) 
                self.test(model, endWeek, featureModeValue, outputSong, x)

                
if __name__ == '__main__':
    rm = RegressionModel()
#     rm.outputAllResult(datetime(2013,3,16), datetime(2013,4,20), outputSong=True)
    rm.computeBaseLine(2)
