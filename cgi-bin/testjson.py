#!/usr/bin/python

import os
import sys
from datetime import datetime, timedelta
import cgi
import cgitb

cgitb.enable()
# cgitb.enable(display=0, logdir="/logfiles")

import array
import json

def main():

    global Tiles

    pars = cgi.FieldStorage()	# data from html/rest call

    resp = ""
    error = x1 = y1 = x2 = y2 = pointsDataFile = par = None
    args = sys.argv[1:]
    pointsdata = ""
    curveht = True
    maxht = True
    print"test of json"
    profilePoints = []
    rs = {}

    profilePoints.append({'xcoord':"1", 'ycoord':"2",'curheight':"3",'trueheight':"4"})
    profilePoints.append({'xcoord':"10", 'ycoord':"20",'curheight':"30",'trueheight':"40"})

    resp += "\"average\":%d," % (1)
    resp += "\"minGr\":%.3f,\n" % (1)
    resp += "\"maxGr\":%.3f," % (1)
    resp += "\"aveGr\":%.3f%s" % (1, "," )
    print "resp" +  resp



    t1 = datetime.now()
    tt = t1


    d = json.loads(resp)
    print d

    print json.dumps(profilePoints)

main()
