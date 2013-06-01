'''
Created on 2013-3-25
@author: Bobi Pu, bobi.pu@usc.edu
use Youtube Data API, V2.0
'''
from youtube import service
from DateConverter import dateStringToSaturday, lastSaturday
from DBController import DBController

class YoutubeCommentsExtractor(object):
    def __init__(self, developerKey='AIzaSyA8VRba6Hg5upZsC86Au_UFnb2DyYM8_g4', clientID='569061869342.apps.googleusercontent.com'):
        self.client = service.YouTubeService()
        self.client.ssl = True
        self.client.developer_key = developerKey
        self.client.client_id = clientID

    def getVideoID(self, videoName):
        # return only one videoID
        try:
            query = service.YouTubeVideoQuery()
            query.vq = videoName
            query.orderby = 'relevance'
            query.racy = 'include'
            feed = self.client.YouTubeQuery(query)
            entry = feed.entry[0]
            videoID = entry.id.text.split('/')[-1]
        except:
            videoID = None
        return videoID

    def getComments(self, videoID):
        commentList = []
        if videoID is None:
            return commentList
        try:
            commentFeed = self.client.GetYouTubeVideoCommentFeed(video_id=videoID)
            while commentFeed is not None:
                for comment in commentFeed.entry:
                    commentText = comment.content.text
                    commentDate = dateStringToSaturday(comment.updated.text)
                    commentList.append({'week' : commentDate, 'comment' : commentText})
                next_link = commentFeed.GetNextLink()
                if next_link is None:
                    commentFeed = None
                else:
                    commentFeed = self.client.GetYouTubeVideoCommentFeed(next_link.href)
        except Exception, e:
            print e
        return commentList
        
    def extractYoutubeCommentsToDB(self, songList):
        db = DBController()
        for song in songList:
            try:
                searchVideoName =  song['title'] + ' ' + song['artist']
                videoID = self.getVideoID(searchVideoName)
                comments = self.getComments(videoID)
                db.insertCommentToDB(song['id'], comments)
            except Exception as e:
                print e
                continue

if __name__ == '__main__':
    extractor = YoutubeCommentsExtractor()
    db = DBController()
    songList = db.getSongByWeek(lastSaturday())
    extractor.extractYoutubeCommentsToDB(songList)