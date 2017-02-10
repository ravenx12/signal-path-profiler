#!python

import os
import sys

# Shuttle Radar Topography Mission (SRTM) terrain data: http://www2.jpl.nasa.gov/srtm/cbanddataproducts.html
# Required are 3" (~90m) v2 or v3 tiles covering the British Isles 11W to 3E, 49N to 60N inclusive
# (unfortunately, the original SRTM data, at least in v2, does not quite cover the far north of Shetland, and
# required supplementing from elsewhere  -  the Shetland tiles used here derive from OS Terrain 50 data)
# Format: 1201x1201 or 3601x3601 pixels per degree^2 tile, X Lon within Y Lat, starting from north west corner.
class SRTMTile:
    def __init__(self, lon, lat, path=SRTM3Path,fName=SRTM3FileName ,
                 zName=SRTM3ZipName ,x=SRTM3Cols, y=SRTM3Rows,aRes=SRTM3AngRes  ):
         # Relative path to tiles
        self.Path = path
        # Unzipped file name template
        self.FName = fName
        # Zipped file name template
        self.ZName = zName
        # Tile width (sample points)
        self.X=x
        # Tile height (sample points)
        self.Y = y
        # Angular resolution (radians)
        self.ARes = aRes
        # Value corresponding to void
        self.Null = -32768
        # Minimum height (metres)
        self.Min = -32767
        # Maximum height (metres)
        self.Max = 32767

        if lon and lat:
            self.getSRTMData(lon, lat)
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
