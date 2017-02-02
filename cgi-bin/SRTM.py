#!python
#
# SRTM.py v2.5, for Python 2.7
#
# Returns SRTM height data ...
#    Either:	Of a single point (x1,y1)
#    Or:	Of an elevation profile between two points (x1,y1) and (x2,y2)
#
# The data returned as JSON(P) is as follows:
#    Either:
#        ht	Elevation (metres referenced to EGM96)
#	Or:
#		dist	Horizontal distance (kilometres)
#		surface	Surface distance over the actual terrain (kilometres)
#		ascent	Surface distance ascending (kilometres)
#		level	Surface distance level (kilometres)
#		descent	Surface distance descending (kilometres)
#		min	Minimum elevation (metres referenced to EGM96)
#		max	Maximum elevation (ditto)
#		average	Average elevation (ditto)
#		minGr	Minimum gradient (calculated as vertical change in height over horizontal distance)
#		maxGr	Maximum gradient (ditto)
#		aveGr	Average gradient (ditto)
#		prof	An array of profile points (optional)
#		url	Google Static Image Charts URL to obtain a profile diagram (optional)
#
# Optionally for the profile, an array of up to 100 samples can be returned both as JSON and as a Google Static
# Image Charts URL.  If the path covers more than 100 SRTM cells, then, depending on the absence or presence
# of an mx=true parameter, each point returned represents either the average (by default) or maximum height
# that the path encounters from those cells in the neighbourhood of that point.  If an SRTM void pixel is
# encountered, then the height returned is interpolated from the nearest neighbouring valid pixels.
#
# The data columns returned in the profile have the following meaning:
#	Longitude (signed decimal degrees referenced to WGS84)
#	Latitude (ditto)
#	Height of curvature of Earth's surface (optional, metres referenced to EGM96)
#	Average or maximum height of terrain (including above when present, ditto)
#
# Before submitting the URL to the Google Static Image Charts API, ~Width~ and ~Height~ must be replaced
# by suitable dimensions in pixels, the product (multiplication) of the two being less than Google's limit
# of 300,000  -  see the Google Static Image Charts API documentation for details:
#	https://developers.google.com/chart/image/
# Note: Google Static Image Charts API has been deprecated by Google since 2012, but they have made unofficial
# noises about not turning it off or else replacing it with something similar.
#
# Usage (without the spaces and line breaks that have been inserted here for clarity):
#	http://<host>/cgi-bin/SRTM.py ? x1=<x1> & y1=<y1> [ & x2=<x2> & y2=<y2> ]
#					[ & cb=<callback function name> ]
#					[ & pr=True ] [ & cv=True ] [ & mx=True ]
#					[ & db=True ]
#
# Where:
#	x1	Longitude of first point (required, signed decimal degrees referenced to WGS84)
#	y1	Latitude of first point (ditto)
#	x2	Longitude of second point (required for profile, ditto)
#	y2	Latitude of second point (ditto)
#	cb	Optionally request the data be returned as a JSONP function call back
#			with the JSON data as the single argument to the call
#			(enables the returned data to be read as valid JavaScript by a <script> tag)
#	pr	Optionally request a full profile array and a Google Static Image Charts URL to draw it
#	cv	Optionally include the height of the curvature of Earth's surface in the returned data
#	mx	Optionally, have each sample point returned be the maximum, rather than the default average,
#			of the SRTM heights in the neighbourhood of the point.
#	db	Optionally request output in the form of HTML for debugging purposes
#	vb	As above, but more verbose
# And:
#	Failure to provide any of the first two or four required parameters returns a help message


import os
import sys

import cgi
import cgitb

cgitb.enable()
# cgitb.enable(display=0, logdir="/logfiles")

# import webapp2
# import jinja2
# JINJA_ENVIRONMENT = jinja2.Environment( loader = jinja2.FileSystemLoader( os.path.dirname(__file__) ) )

# Template location
TempPath = os.path.join("..", "Resources", "Templates", os.path.splitext(os.path.basename(__file__))[0] + ".html")
print "Tempath is", TempPath

# Page title
PageTitle = "www.macfh.co.uk"

import array
import json
import string
import zipfile

from datetime import datetime, timedelta

from math import acos
from math import atan
from math import cos
from math import sin
from math import degrees
from math import radians
from math import ceil
from math import floor
from math import log
from math import sqrt

# SRTM constants
# Longitude and latitude tile coverage limits
# (these cover the British Isles including the Channel Islands, Ireland, and the Isle of Man)
XMin = -11
XMax = 4
YMin = 49
YMax = 61
# Tile used count
Tiles = 0
# File extensions
SRTMExt = ".hgt"
ZipExt = ".zip"
# Constants for SRTM 1 arc second
SRTM1Path = "SRTM"
SRTM1FileName = "%s" + SRTMExt
SRTM1ZipName = "%s.SRTMGL1" + SRTMExt + ZipExt
SRTM1Cols = 3601
SRTM1Rows = SRTM1Cols
SRTM1AngRes = radians(float(1) / (SRTM1Cols - 1))
# Constants for SRTM 3 arc second
SRTM3Path = SRTM1Path
SRTM3FileName = SRTM1FileName
SRTM3ZipName = "%s" + SRTMExt + ZipExt
SRTM3Cols = 1201
SRTM3Rows = SRTM3Cols
SRTM3AngRes = radians(float(1) / (SRTM3Cols - 1))

# Conversions & geographical constants
# Miles per kilometre
MPK = 0.6213
# Feet per metre
FPM = 3.2808
# Geometric mean radius of earth (m)
Re = float(6371001)

# Chart constants for Google Static Image Charts API
# Maximum reliable sample limit (determined empirically)
stLim = 100
# Colors
black = "000000"
white = "CCCCCC"
terr = "009900"
earth = black
sky1 = "336699"
sky2 = "6699CC"
axes = black
# Font size for axis labels
font = "10"
# Axis and line thickness
thick = 6

TRUE = ("true", "t", "yes", "y", "1")


# Spherical and cartographical geometry

# Class defining a 2D coordinate
class Duple:
    def __init__(self, xx, yy):
        self.x = xx
        self.y = yy


# Class defining a 3D coordinate
class Triple:
    def __init__(self, xx, yy, zz):
        self.x = xx
        self.y = yy
        self.z = zz


# Angular distance between two points (radians in and out)
def distAngr(d1, d2):
    dC1 = LL2XYZ(d1)
    dC2 = LL2XYZ(d2)
    return acos(min(dC1.x * dC2.x + dC1.y * dC2.y + dC1.z * dC2.z, 1))


# Calculate XYZ direction cosines Triple of a LonLat Duple (radians in)
def LL2XYZ(d):
    return Triple(cos(d.x) * cos(d.y), sin(d.x) * cos(d.y), sin(d.y))


# Calculate the LonLat Duple of an XYZ Triple (radians out)
def XYZ2LL(t):
    return Duple(atan(t.y / t.x), atan(t.z / sqrt(t.x ** 2 + t.y ** 2)))


# Routines for creating Google Static Image Charts URL
def axisStep(range, minNum):
    if range:
        interval = 10 ** floor(log(range) / log(10))
        turn = False
        while range / interval < minNum:
            interval = interval / (2 if turn else 5)
            turn = not turn
    else:
        interval = 0.0005
    return interval


def extEncodeGoogle(aValue, aMin, aMax):
    result = None
    if (aMin <= aValue) and (aValue <= aMax):
        value = (aValue - aMin) * 4096 / abs(aMax - aMin)
        dig1 = simEncodeGoogle(floor(value / 64), 0, 64, True)
        dig2 = simEncodeGoogle(floor(value % 64), 0, 64, True)
        result = dig1 + dig2
    return result


def simEncodeGoogle(aValue, aMin, aMax, extDigit):
    result = None
    if (aMin <= aValue) and (aValue <= aMax):
        value = int(round((aValue - aMin) * (64 if extDigit else 61) / abs(aMax - aMin)))
        if value < 26:
            result = chr(ord("A") + value)
        elif value < 52:
            result = chr(ord("a") + (value - 26))
        elif value < 62:
            result = chr(ord("0") + (value - 52))
        elif extDigit and (value == 62):
            result = "-"
        elif extDigit and (value == 63):
            result = "."
    return result


# print "Content-Type: text/html\n\n"


# Shuttle Radar Topography Mission (SRTM) terrain data: http://www2.jpl.nasa.gov/srtm/cbanddataproducts.html
# Required are 3" (~90m) v2 or v3 tiles covering the British Isles 11W to 3E, 49N to 60N inclusive
# (unfortunately, the original SRTM data, at least in v2, does not quite cover the far north of Shetland, and
# required supplementing from elsewhere  -  the Shetland tiles used here derive from OS Terrain 50 data)
# Format: 1201x1201 or 3601x3601 pixels per degree^2 tile, X Lon within Y Lat, starting from north west corner.
class SRTMTile:
    # Relative path to tiles
    Path = SRTM3Path
    # Unzipped file name template
    FName = SRTM3FileName
    # Zipped file name template
    ZName = SRTM3ZipName
    # Tile width (sample points)
    X = SRTM3Cols
    # Tile height (sample points)
    Y = SRTM3Rows
    # Angular resolution (radians)
    ARes = SRTM3AngRes
    # Value corresponding to void
    Null = -32768
    # Minimum height (metres)
    Min = -32767
    # Maximum height (metres)
    Max = 32767

    def __init__(self, lon, lat):
        if lon and lat:
            getSRTMData(lon, lat)
        else:
            self.N = self.D = None

    # Calc SRTM filename (degrees in)
    def getSRTMName(self, lon, lat):
        fn = ""
        if lat >= 0:
            fn = "N"
        else:
            fn = "S"
        fn = fn + "%02u" % abs(floor(lat))
        if lon >= 0:
            fn = fn + "E"
        else:
            fn = fn + "W"
        fn = fn + "%03u" % abs(floor(lon))
        return fn

    # Read SRTM file (degrees in)
    def getSRTMData(self, lon, lat):
        global Tiles
        tn = self.getSRTMName(lon, lat)
        if tn == self.N:
            data = self.D
        else:
            data = None
            fn = self.FName % tn
            try:
                bin = open(os.path.join(os.path.dirname(__file__), self.Path, fn), "rb", 2 * self.X * self.Y)
                data = array.array("h", bin.read())
                bin.close()
            except IOError:
                try:
                    bin = zipfile.ZipFile(os.path.join(os.path.dirname(__file__), self.Path, self.ZName % tn), "r")
                    data = array.array("h", bin.read(fn))
                    bin.close()
                except IOError:
                    # print "/* Could not open data file: %s */<br>\n" % fn
                    pass
            if data:
                # print "/* Loaded Tile: %s */<br>\n" % tn
                # Depending on endian-ness of hardware, may need to swap bytes
                if sys.byteorder == "little":
                    data.byteswap()
                self.N = tn
                self.D = data
                Tiles += 1
        return self.D

    # Look up raw height
    def getRawHt(self, x, y):
        of = x + (self.Y - 1 - y) * self.X
        ht = self.D[of]
        # print "/* x:%u, y:%u, of:%u, ht:%d, len:%u */<br>\n" % ( x, y, of, ht, len(self.D) )
        return ht

    # Look up height and interpolate data voids
    def getCleanHt(self, x, y):
        ht = self.getRawHt(x, y)
        i = 1
        j = 0
        hs = []
        while ht == self.Null:
            if (x - i >= 0) and (y - j >= 0):
                ht = self.getRawHt(x - i, y - j)
                if ht != self.Null:
                    hs.append(ht)
            if (x + i <= self.X - 1) and (y - j >= 0):
                ht = self.getRawHt(x + i, y - j)
                if ht != self.Null:
                    hs.append(ht)
            if j > 0:
                if (x - i >= 0) and (y + j <= self.Y - 1):
                    ht = self.getRawHt(x - i, y + j)
                    if ht != self.Null:
                        hs.append(ht)
                if (x + i <= self.X - 1) and (y + j <= self.Y - 1):
                    ht = self.getRawHt(x + i, y + j)
                    if ht != self.Null:
                        hs.append(ht)

            if j < i:
                if (x - j >= 0) and (y - i >= 0):
                    ht = self.getRawHt(x - j, y - i)
                    if ht != self.Null:
                        hs.append(ht)
                if (x - j >= 0) and (y + i <= self.Y - 1):
                    ht = self.getRawHt(x - j, y + i)
                    if ht != self.Null:
                        hs.append(ht)
                if j > 0:
                    if (x + j <= self.X - 1) and (y - i >= 0):
                        ht = self.getRawHt(x + j, y - i)
                        if ht != self.Null:
                            hs.append(ht)
                    if (x + j <= self.X - 1) and (y + i <= self.Y - 1):
                        ht = self.getRawHt(x + j, y + i)
                        if ht != self.Null:
                            hs.append(ht)

            if len(hs) > 0:
                ht = 0
                for k in range(len(hs)):
                    ht += hs[k]
                ht = float(ht) / len(hs)
            else:
                ht = self.Null

            # print "/* x:%u, y:%u, i:%u, j:%u, hs[0]:%d, hs[1]:%d, hs[2]:%d, hs[3]:%d, nn:%u, ih:%d, ht:%.1f */<br>\n" % ( x, y, i, j, hs[0], hs[1], hs[2], hs[3], nn, ih, ht )

            j += 1
            if j > i:
                i += 1
                j = 0

        return ht

    # Look up and interpolate height (degrees in)
    def getHeight(self, d):
        ht = 0
        da = self.getSRTMData(d.x, d.y)
        if da:
            cx = abs(d.x - floor(d.x)) * (self.X - 1)
            cy = abs(d.y - floor(d.y)) * (self.Y - 1)
            x0 = int(cx)
            y0 = int(cy)
            x1 = x0 + 1
            y1 = y0 + 1
            dx = cx - x0
            dy = cy - y0
            hSW = self.getCleanHt(x0, y0)
            hSE = self.getCleanHt(x1, y0)
            hNW = self.getCleanHt(x0, y1)
            hNE = self.getCleanHt(x1, y1)
            hS = (1 - dx) * hSW + dx * hSE
            hN = (1 - dx) * hNW + dx * hNE
            ht = (1 - dy) * hS + dy * hN
        # print "/* Lon:%.6f, Lat:%.6f, cx:%.3f, cy:%.3f, x0:%u, y0:%u, x1:%u, y1:%u, dx:%.2f, dy:%.2f, hSW:%d, hSE:%d, hNW:%d, hNE:%d, hS:%.2f, hN:%.2f, ht:%.2f */<br>\n" % (d.x,d.y,cx,cy,x0,y0,x1,y1,dx,dy,hSW,hSE,hNW,hNE,hS,hN,ht)
        return int(ht)


# The current SRTM tile
SRTM = SRTMTile(None, None)


# Spherical and cartographical geometry

# Class defining a 2D coordinate
class Duple:
    def __init__(self, xx, yy):
        self.x = xx
        self.y = yy


# Class defining a 3D coordinate
class Triple:
    def __init__(self, xx, yy, zz):
        self.x = xx
        self.y = yy
        self.z = zz


# Angular distance between two points (radians in and out)
def distAngr(d1, d2):
    dC1 = LL2XYZ(d1)
    dC2 = LL2XYZ(d2)
    return acos(min(dC1.x * dC2.x + dC1.y * dC2.y + dC1.z * dC2.z, 1))


# Calculate XYZ direction cosines Triple of a LonLat Duple (radians in)
def LL2XYZ(d):
    return Triple(cos(d.x) * cos(d.y), sin(d.x) * cos(d.y), sin(d.y))


# Calculate the LonLat Duple of an XYZ Triple (radians out)
def XYZ2LL(t):
    return Duple(atan(t.y / t.x), atan(t.z / sqrt(t.x ** 2 + t.y ** 2)))


# Routines for creating Google Static Image Charts URL
def axisStep(range, minNum):
    if range:
        interval = 10 ** floor(log(range) / log(10))
        turn = False
        while range / interval < minNum:
            interval = interval / (2 if turn else 5)
            turn = not turn
    else:
        interval = 0.0005
    return interval


def extEncodeGoogle(aValue, aMin, aMax):
    result = None
    if (aMin <= aValue) and (aValue <= aMax):
        value = (aValue - aMin) * 4096 / abs(aMax - aMin)
        dig1 = simEncodeGoogle(floor(value / 64), 0, 64, True)
        dig2 = simEncodeGoogle(floor(value % 64), 0, 64, True)
        result = dig1 + dig2
    return result


def simEncodeGoogle(aValue, aMin, aMax, extDigit):
    result = None
    if (aMin <= aValue) and (aValue <= aMax):
        value = int(round((aValue - aMin) * (64 if extDigit else 61) / abs(aMax - aMin)))
        if value < 26:
            result = chr(ord("A") + value)
        elif value < 52:
            result = chr(ord("a") + (value - 26))
        elif value < 62:
            result = chr(ord("0") + (value - 52))
        elif extDigit and (value == 62):
            result = "-"
        elif extDigit and (value == 63):
            result = "."
    return result


def main(pars):
    global Tiles

    resp = ""
    error = x1 = y1 = x2 = y2 = cb = pr = cv = mx = db = vb = par = None
    args = sys.argv[1:]

    print ' '.join(args)
    try:
        # x1 = float(pars.getvalue("x1"))
        x1 = float(sys.argv[1])
    except Exception:
        error = True
        resp += "<p>ERROR: required x1 parameter missing!</p>\n"

    try:
        # y1 = float(pars.getvalue("y1"))
        y1 = float(sys.argv[2])
    except Exception:
        error = True
        resp += "<p>ERROR: required y1 parameter missing!</p>\n"

    try:
        # x2 = float(pars.getvalue("x2"))
        x2 = float(sys.argv[3])
    except Exception:
        error = True
        # resp	+= "<p>ERROR: required x2 parameter missing!</p>\n"
        pass

    try:
        # y2 = float(pars.getvalue("y2"))
        y2 = float(sys.argv[4])
    except Exception:
        # error	= True
        # resp	+= "<p>ERROR: required y2 parameter missing!</p>\n"
        pass

    try:
        #  par = pars.getvalue("cb")
        par = (sys.argv[5])
        if not par == 'none':
            cb = par
    except Exception:
        pass

    try:
        # par = pars.getvalue("pr")
        par = (sys.argv[6])
        if par.lower() in TRUE:
            pr = True
    except Exception:
        pass

    try:
        # par = pars.getvalue("cv")
        par = (sys.argv[7])
        if par.lower() in TRUE:
            cv = True
    except Exception:
        pass

    try:
        # par = pars.getvalue("mx")
        par = (sys.argv[8])
        if par.lower() in TRUE:
            mx = True
    except Exception:
        pass

    try:
        # par = pars.getvalue("db")
        par = (sys.argv[9])
        if par.lower() in TRUE:
            db = True
    except Exception:
        pass

    try:
        # par = pars.getvalue("vb")
        par = (sys.argv[10])
        if par.lower() in TRUE:
            vb = db = True
    except Exception:
        pass


    if (x1 != None) and (x1 >= XMin) and (x1 < XMax) and (y1 != None) and (y1 >= YMin) and (y1 < YMax) and (
                x2 != None) and (x2 >= XMin) and (x2 < XMax) and (y2 != None) and (y2 >= YMin) and (y2 < YMax):
        #pointsdata is a JSON representation of the height point information for the profile
        pointsdata = "{\"points\":{"
        if db:
            t0 = datetime.now()

        Tiles = 0

        rad1 = Duple(radians(x1), radians(y1))
        rad2 = Duple(radians(x2), radians(y2))

        aD = distAngr(rad1, rad2)
        d = aD * Re

        xyz1 = LL2XYZ(rad1)
        xyz2 = LL2XYZ(rad2)

        nS = max(int(ceil(aD / SRTM.ARes)), 1)
        dS = d / nS

        # Set up profile calculations
        if pr:
            nP = min(nS, stLim - 1)
            stP = aD / nP
            points = []
            if db:
                prof = "\"prof\":[<br>\n"
            thisP = 0
            nextP = 1
            lastP = aD + 0.1

            # Maximum or average sample height
            if mx:
                TrHt = SRTM.Min
            else:
                TrHt = 0
                nTr = 0

        stA = aD / nS
        stX = (xyz2.x - xyz1.x) / nS
        stY = (xyz2.y - xyz1.y) / nS
        stZ = (xyz2.z - xyz1.z) / nS

        # Set up return values
        minEl = SRTM.Max
        maxEl = SRTM.Min
        average = 0
        minGr = float("Infinity")
        maxGr = float("-Infinity")
        aveGr = 0
        ascent = 0
        level = 0
        descent = 0
        surface = 0
        lastTr = None

        for i in range(0, nS + 1):
            aS = i * stA
            s = aS * Re

            p = XYZ2LL(Triple(xyz1.x + i * stX, xyz1.y + i * stY, xyz1.z + i * stZ))
            ll = Duple(degrees(p.x), degrees(p.y))

            if cv != None:
                cv = Re * (cos((aD / 2) - aS) - cos(aD / 2))
                tr = cv + SRTM.getHeight(ll)
                cv = int(round(cv))
            else:
                tr = SRTM.getHeight(ll)

            # Minimum, maximum, and average elevations
            minEl = min(tr, minEl)
            maxEl = max(tr, maxEl)
            average += tr

            # Min and max gradients, totals for ascent, level, descent, and surface dist
            if lastTr != None:
                lastTr -= tr
                delta = sqrt(dS ** 2 + lastTr ** 2)
                surface += delta
                if lastTr < 0:
                    ascent += delta
                if lastTr == 0:
                    level += delta
                if lastTr > 0:
                    descent += delta
                if dS:
                    delta = lastTr / dS
                elif lastTr:
                    delta = lastTr / (SRTM.ARes * Re)
                else:
                    delta = 0
                minGr = min(delta, minGr)
                maxGr = max(delta, maxGr)
                aveGr += delta
            lastTr = tr

            # Profile
            if pr:
                if i and abs(nextP * stP - aS) <= abs(aS - thisP * stP):
                    if mx:
                        point[len(point) - 1] = int(round(TrHt))
                        TrHt = SRTM.Min
                    else:
                        point[len(point) - 1] = int(round(TrHt / nTr))
                        TrHt = 0
                        nTr = 0
                    points.append(point)
                    if db:
                        # This is where the points array are generated
                        #point[0] = xcoord, point[1] = ycoord, point[2] = curved earth height, point[3] true height
                        print "{\"xcoord\":%.6f,\"ycoord\":%.6f,\"curheight\":%.0f,\"trueheight\":%.0f},\n" % (point[0], point[1], point[2], point[3])
                        pointsdata +=  "{\"xcoord\":%.6f,\"ycoord\":%.6f,\"curheight\":%.0f,\"trueheight\":%.0f},\n" % (point[0], point[1], point[2], point[3])

                        if cv != None:
                            prof += "[%.6f,%.6f,%.0f,%.0f],<br>\n" % (point[0], point[1], point[2], point[3])
                        else:
                            prof += "[%.6f,%.6f,%.0f],<br>\n" % (point[0], point[1], point[2])
                    thisP += 1
                    nextP += 1
                    lastP = aD + 0.1

                if abs(aS - thisP * stP) < lastP:
                    lastP = abs(aS - thisP * stP)
                    if cv != None:
                        point = [round(ll.x, 6), round(ll.y, 6), int(round(cv)), 0]
                    else:
                        point = [round(ll.x, 6), round(ll.y, 6), 0]

                # Maximum or average local sample height
                if mx:
                    TrHt = max(tr, TrHt)
                else:
                    TrHt += tr
                    nTr += 1

                if vb:
                    if cv != None:
                        prof += "/* {%d,%.6f,%.6f,%.0f,%.0f} */<br>\n" % (i, ll.x, ll.y, cv, tr)
                    else:
                        prof += "/* {%d,%.6f,%.6f,%.0f} */<br>\n" % (i, ll.x, ll.y, tr)

        # If profile, finish last point
        if pr:
            if mx:
                point[len(point) - 1] = int(round(TrHt))
            else:
                point[len(point) - 1] = int(round(TrHt / nTr))
            points.append(point)
            if db:
                if cv != None:
                    prof += "[%.6f,%.6f,%.0f,%.0f]<br>\n" % (point[0], point[1], point[2], point[3])
                else:
                    prof += "[%.6f,%.6f,%.0f]<br>\n" % (point[0], point[1], point[2])
                prof += "],<br>\n"
            pointsdata += "}"
        if vb:
            prof += "/* Tiles Used: %d */<br>\n" % Tiles

        # Clean up values for output
        d = round(d / 1000, 3)
        surface = round(surface / 1000, 3)
        ascent = round(ascent / 1000, 3)
        level = round(level / 1000, 3)
        descent = round(descent / 1000, 3)
        minEl = int(floor(minEl))
        maxEl = int(ceil(maxEl))
        average = round(average / (nS + 1))
        minGr = round(minGr, 3)
        maxGr = round(maxGr, 3)
        aveGr = round(aveGr / nS, 3)

        # Compile the output
        rs = {}
        if db:
            resp += "{<br>\n"

        # Distances in km
        rs["dist"] = d
        rs["surface"] = surface
        rs["ascent"] = ascent
        rs["level"] = level
        rs["descent"] = descent
        if db:
            resp += "\"dist\":%.3f,<br>\n" % rs["dist"]
            resp += "\"surface\":%.3f,<br>\n" % rs["surface"]
            resp += "\"ascent\":%.3f,<br>\n" % rs["ascent"]
            resp += "\"level\":%.3f,<br>\n" % rs["level"]
            resp += "\"descent\":%.3f,<br>\n" % rs["descent"]

        # Min and max elevations and gradients
        rs["min"] = minEl
        rs["max"] = maxEl
        rs["average"] = average
        rs["minGr"] = minGr
        rs["maxGr"] = maxGr
        rs["aveGr"] = aveGr
        if db:
            resp += "\"min\":%d,<br>\n" % (rs["min"])
            resp += "\"max\":%d,<br>\n" % (rs["max"])
            resp += "\"average\":%d,<br>\n" % (rs["average"])
            resp += "\"minGr\":%.3f,<br>\n" % (rs["minGr"])
            resp += "\"maxGr\":%.3f,<br>\n" % (rs["maxGr"])
            resp += "\"aveGr\":%.3f%s<br>\n" % (rs["aveGr"], "," if pr else "")

        # If profile, insert the profile data array and the Google Static Image Charts URL
        if pr:
            rs["prof"] = points
            if db:
                resp += prof
            # Google Static Image Charts URL
            # See https://developers.google.com/chart/image/docs/chart_params

            maxEl += 1
            src = ""  # "&lt;placeholder&gt;"

            # Curvature (optional), terrain
            for i in range(len(rs["prof"][0]) - 1, 1, -1):
                for j in range(0, len(rs["prof"])):
                    if (j == 0) and (src != ""):
                        src += ","
                    try:
                        src += extEncodeGoogle(max(minEl, rs["prof"][j][i]), minEl, maxEl)
                    except Exception:
                        src += "__"
                        if vb:
                            resp += "/* !!!Error!!!  -  i: %u, j: %u, p: %u */<br>\n" % (i, j, rs["prof"][j][i])

            src = "http://chart.apis.google.com/chart" \
                  + "?chs=~Width~x~Height~" \
                  + "&chma=" + ("35" if maxEl >= 1000 else "30") + "," + (
                      "35" if maxEl * FPM >= 1000 else "30") + ",22,23" \
                  + "&cht=lc" \
                  + "&chd=e:" \
                  + src + "," \
                  + extEncodeGoogle(minEl, minEl, maxEl) + extEncodeGoogle(minEl, minEl, maxEl) \
                  + "&chf=bg,s," + white + "|c,lg,90," + sky1 + ",1," + sky2 + ",0" \
                  + "&chco=" \
                  + terr + "," \
                  + ((earth + ",") if cv != None else "") \
                  + axes \
                  + "&chm=" \
                  + "b," + terr + ",0,1,0" \
                  + (("|b," + earth + ",1,2,0") if cv != None else "") \
                  + "&chxt=x,y,t,r" \
                  + "&chxs=" \
                  + "0," + axes + "," + font + ",0,lt," + axes + "," + axes \
                  + "|1," + axes + "," + font + ",1,lt," + axes + "," + axes \
                  + "|2," + axes + "," + font + ",0,lt," + axes + "," + axes \
                  + "|3," + axes + "," + font + ",-1,lt," + axes + "," + axes \
                  + "&chxtc=0," + str(thick) + "|1," + str(thick) + "|2," + str(thick) + "|3," + str(thick)

            # Axis scales
            scale = d
            interval = axisStep(scale, 5)
            src += "&chxr=0,0," + str(round(scale, 2)) + "," + str(interval)

            scale = MPK * d
            interval = axisStep(scale, 5)
            src += "|2,0," + str(round(scale, 2)) + "," + str(interval)
            scale = maxEl - minEl
            interval = max(int(round(axisStep(scale, 3))), 1)
            chxl = "&chxl=0:|km|1:|m"
            chxp = "&chxp=1,0"
            for i in range(int(floor(minEl / interval) * interval), maxEl + 1, interval):
                if i > minEl + interval / 3:
                    chxl += "|" + str(i)
                    chxp += "," + str(int(round(100 * (i - minEl) / scale)))

            minEl = int(round(minEl * FPM))
            maxEl = int(round(maxEl * FPM))
            scale = maxEl - minEl
            interval = max(int(round(axisStep(scale, 3))), 1)
            chxl += "|2:|mi|3:|ft"
            chxp += "|3,0"
            for i in range(int(floor(minEl / interval) * interval), maxEl, interval):
                if i > minEl + interval / 3:
                    chxl += "|" + str(i)
                    chxp += "," + str(int(round(100 * (i - minEl) / scale)))
            src += chxl + chxp
            rs["url"] = src
            src = src.replace("&", "&amp;").replace("|", "%7C")
            if db:
                resp += "\"url\":\"%s\"<br>\n" % src

        if db:
            resp += "}"
        else:
            resp = json.dumps(rs, separators=(",", ":"), sort_keys=True)

        if cb:
            resp = cb + "(" + resp + ");"

        if db:
            resp = "<p>Output:<br>\n" + resp + "</p>\n"
            if pr:
                resp += "<img src=\"%s\" style=\"width:180mm; height:60mm;\" alt=\"Google Static Image Chart\">\n" % (
                    src.replace("~Width~", "680").replace("~Height~", "227"))

            t1 = datetime.now()
            tt = t1 - t0
            resp += "<p>Time taken: %0.3fs</p>\n" % (tt.seconds + float(tt.microseconds) / 1000000)

        error = False

    elif (x1 != None) and (x1 >= XMin) and (x1 < XMax) and (y1 != None) and (y1 >= YMin) and (y1 < YMax) and (
                x2 == None) and (y2 == None):
        if db:
            t0 = datetime.now()

        # Get spot height for a single point
        tr = SRTM.getHeight(Duple(x1, y1))
        resp += "{\"ht\":%.0f}" % tr
        if cb:
            resp = cb + "(" + resp + ");"

        # Compile the output
        if db:
            t1 = datetime.now()
            tt = t1 - t0
            resp = "<p>Output:&nbsp; %s</p>\n<p>Time taken: %0.3fs</p>\n" % (
                resp, tt.seconds + float(tt.microseconds) / 1000000)

        error = False

    else:
        error = True

    if db or error:
        version = os.path.basename(sys.argv[0]) + " v2.5, " \
                  + datetime.utcfromtimestamp(os.path.getmtime(sys.argv[0])).isoformat(" ")
        page = PageTitle + " - " + version

        if error:
            resp += "<h2>HELP</h2>\n" \
                    + "<p>This program calculates from <a href=\"http://www2.jpl.nasa.gov/srtm/\" title=\"Shuttle Radar Topography Mission\" target=\"_blank\">SRTM</a> data either the elevation of a single point or an elevation profile between two points.</p>\n" \
                    + "<p>When called successfully, the data returned as <abbr title=\"JavaScript Object Notation\">JSON</abbr> is as follows:<br>\n" \
                    + "&nbsp;&nbsp;&nbsp;Either:<br>\n" \
                    + "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<strong>ht</strong>&nbsp;&nbsp;Point elevation (metres referenced to EGM96)<br>\n" \
                    + "&nbsp;&nbsp;&nbsp;Or:<br>\n" \
                    + "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<strong>dist</strong>&nbsp;&nbsp;Horizontal distance (kilometres)<br>\n" \
                    + "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<strong>surface</strong>&nbsp;&nbsp;Surface distance over the actual terrain (kilometres)<br>\n" \
                    + "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<strong>ascent</strong>&nbsp;&nbsp;Surface distance ascending (kilometres)<br>\n" \
                    + "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<strong>level</strong>&nbsp;&nbsp;Surface distance level (kilometres)<br>\n" \
                    + "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<strong>descent</strong>&nbsp;&nbsp;Surface distance descending (kilometres)<br>\n" \
                    + "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<strong>min</strong>&nbsp;&nbsp;Minimum elevation (metres referenced to EGM96)<br>\n" \
                    + "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<strong>max</strong>&nbsp;&nbsp;Maximum elevation (ditto)<br>\n" \
                    + "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<strong>average</strong>&nbsp;&nbsp;Average elevation (ditto)<br>\n" \
                    + "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<strong>minGr</strong>&nbsp;&nbsp;Minimum gradient (calculated as vertical change in height over horizontal distance)<br>\n" \
                    + "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<strong>maxGr</strong>&nbsp;&nbsp;Maximum gradient (ditto)<br>\n" \
                    + "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<strong>aveGr</strong>&nbsp;&nbsp;Average gradient (ditto)<br>\n" \
                    + "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<strong>prof</strong>&nbsp;&nbsp;An array of profile points (optional)<br>\n" \
                    + "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<strong>url</strong>&nbsp;&nbsp;Google Static Image Charts URL to obtain a profile diagram (optional)<br>\n" \
                    + "<p>For both a point height and a profile, location parameters must be given as&nbsp;&hellip;<br>\n" \
                    + "&nbsp;&nbsp;&nbsp;<strong>x1</strong>&nbsp;&nbsp;Point or start longitude (signed decimal degrees &gt;= %.1f and &lt; %.1f, referenced to WGS84)<br>\n" % (
                XMin, XMax) \
                    + "&nbsp;&nbsp;&nbsp;<strong>y1</strong>&nbsp;&nbsp;Point or start latitude (signed decimal degrees &gt;= %.1f and &lt; %.1f, ditto)<br>\n" % (
                YMin, YMax) \
                    + "&hellip;&nbsp;and additionally for a profile&nbsp;&hellip;<br>\n" \
                    + "&nbsp;&nbsp;&nbsp;<strong>x2</strong>&nbsp;&nbsp;End longitude (signed decimal degrees &gt;= %.1f and &lt; %.1f, ditto)<br>\n" % (
                XMin, XMax) \
                    + "&nbsp;&nbsp;&nbsp;<strong>y2</strong>&nbsp;&nbsp;End latitude (signed decimal degrees &gt;= %.1f and &lt; %.1f, ditto)<br>\n" % (
                YMin, YMax) \
                    + "<p>Optionally, a callback function name can be given as <strong>cb</strong>.&nbsp; The data will then be returned as <span title=\"JSON with Padding\">JSONP</span> which can be loaded directly by a <code>&lt;script&gt;</code> tag</p>\n" \
                    + "<p>The following parameters are ignored if a second point is not given&nbsp;&hellip;</p>\n" \
                    + "<p>Optionally, use the parameter <strong>pr=true</strong> to obtain a full profile and a Google Static Image Charts URL for displaying it.</p>" \
                    + "<p>Optionally, use the parameter <strong>cv=true</strong> to include the height of curvature of Earth's surface in the returned data.</p>" \
                    + "<p>Optionally, use the parameter <strong>mx=true</strong> to have each sample point returned be the maximum, rather than by default the average, of the SRTM heights in the neighbourhood of the point.</p>" \
                    + "<p>The data columns returned in the optional profile array have the following meaning:<br>\n" \
                    + "&nbsp;&nbsp;&nbsp;Longitude (signed decimal degrees referenced to WGS84)<br>\n" \
                    + "&nbsp;&nbsp;&nbsp;Latitude (ditto)<br>\n" \
                    + "&nbsp;&nbsp;&nbsp;Height of curvature of Earth's surface (optional, metres referenced to EGM96)<br>\n" \
                    + "&nbsp;&nbsp;&nbsp;Average, or maximum if specified, height of local terrain (including optional curvature when present, ditto)</p>\n" \
                    + "<p>Before submitting the URL to Google, <strong>~Width~</strong> and <strong>~Height~</strong> " \
                    + "must be replaced by suitable dimensions (pixels), the product (multiplication) of the two being less than Google's limit of 300,000&nbsp; -&nbsp; " \
                    + "see the <a href=\"https://developers.google.com/chart/image/\" title=\"developers.google.com\" target=\"_blank\">Google Static Image Charts API</a> for further information (this service has been deprecated since 2012 but thankfully is still running).</p>\n" \
                    + "<p>Optionally, use the parameter <strong>db=true</strong> " \
                    + "to obtain output as HTML as an aid to debugging.</p>\n"

            page += " - Error"
        else:
            page += " - Debug"
        template = open(os.path.join(os.path.dirname(__file__), TempPath), "r").read()
        resp = "Content-Type: text/html\n\n" \
               + template.replace("{{app}}", "MacFH - UK SRTM Elevation Profiler") \
                   .replace("{{page}}", page) \
                   .replace("{{x1}}", "%s" % x1) \
                   .replace("{{y1}}", "%s" % y1) \
                   .replace("{{x2}}", "%s" % x2) \
                   .replace("{{y2}}", "%s" % y2) \
                   .replace("{{cb}}", "%s" % cb) \
                   .replace("{{pr}}", "%s" % pr) \
                   .replace("{{cv}}", "%s" % ("True" if cv != None else "None")) \
                   .replace("{{mx}}", "%s" % mx) \
                   .replace("{{db}}", "%s" % db) \
                   .replace("{{resp}}", resp)
    else:
        resp = "Content-Type: application/json\n\n" + resp

    sys.stdout.write(resp)

    file = open('testfile.txt','w')

    file.write(pointsdata)

    file.close()


main(cgi.FieldStorage())
