#!python

import os
import sys
from math import radians

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
