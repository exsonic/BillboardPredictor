'''
Created on 2013-3-30
@author: Bobi Pu, convert Date Object to Saturday of that week
'''
from datetime import datetime, timedelta
from dateutil import parser

# convert all the ***DATETIME** obj into that week's Saturday, because billboard publish new ranking on Saturday
def dateToSaturday(date):
    #set hour, min, second, etc to ZERO
    date = datetime(date.year, date.month, date.day)
    offsetDict = {'0' : 5, '1' : 4, '2' : 3, '3' : 2, '4' : 1, '5' : 0, '6' : 6}
    return date + timedelta(days = offsetDict[str(date.weekday())])
    
def dateToSaturdayString(date):
    convertedDate = dateToSaturday(date)
    return convertedDate.strftime('%Y-%m-%d')

def dateToString(date):
    return date.strftime('%Y-%m-%d')

def lastSaturday():
    date = datetime.today()
    date = dateToSaturday(date) - timedelta(weeks=1)
    return date

def MTVSearchDateToSaturday(dateString):
    try:
        inputDate = parser.parse(dateString).date()
    except:
        inputDate = datetime.strptime(dateString, '%Y-%m-%d:%H-%M')
    return dateToSaturday(inputDate)

def dateStringToSaturday(dateString):
    inputDate = parser.parse(dateString)
    return dateToSaturday(inputDate)

def IMVDBDateStringToDate(dateString):
    dateString = dateString.replace('\'', '')
    inputDate = parser.parse(dateString)
    return inputDate