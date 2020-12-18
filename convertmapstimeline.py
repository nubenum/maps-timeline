#!/usr/bin/env python3

import json
from datetime import datetime
import argparse

PATH = ''

class GoogJsonLocation:
    def __init__(self, l):
        self.l = l

    def get_time(self):
        ts = int(self.l['timestampMs'])/1000
        return datetime.utcfromtimestamp(ts)

    @staticmethod
    def _get_scalar(coord):
        return int(coord)/1e7

    def get_lon_lat(self):
        return [GoogJsonLocation._get_scalar(self.l['longitudeE7']), GoogJsonLocation._get_scalar(self.l['latitudeE7'])]

    def _get_first_type(self):
        if 'activity' in self.l:
            act_confidences = self.l['activity'][0]['activity']
            return act_confidences[0]['type']
        return None

    def is_walking(self):
        if self._get_first_type() == 'IN_VEHICLE':
            return False
        return True
    
    def is_confirmed(self):
        if self._get_first_type() == 'UNKNOWN':
            return False
        return True



class Tryable:
    def __init__(self):
        self._value = None

    def set(self, value):
        if self._value != None and value != self._value:
            return False
        self._value = value
        return True

    def get(self):
        return self._value


class Canvas:
    def __init__(self, scale):
        self.scale = scale
        self.l = None
        self.r = None
        self.t = None
        self.b = None

    def add(self, coord):
        if self.l is None:
            self.l = coord[0]
            self.r = coord[0]
            self.t = coord[1]
            self.b = coord[1]
        else:
            if coord[0] < self.l: self.l = coord[0]
            if coord[0] > self.r: self.r = coord[0]
            if coord[1] > self.t: self.t = coord[1]
            if coord[1] < self.b: self.b = coord[1]

    def set_center_dimensions(self, lat, lon, height, width):
        self.l = lon-width/2
        self.r = lon+width/2
        self.t = lat+height/2
        self.b = lat-height/2
    
    def width(self):
        return round((self.r-self.l)*self.scale, 6)
    
    def height(self):
        return round((self.t-self.b)*self.scale, 6)

    def left(self):
        return round(self.l*self.scale, 6)

    def top(self):
        return round(self.t*-self.scale, 6)


class Path:
    DASHED = '0.1,3'
    SOLID = '0'
    def __init__(self):
        self.coords = []
        self.opacity = Tryable()
        self.color = Tryable()
        self.stroke = Tryable()

    def append(self, lon_lat):
        self.coords.append(lon_lat)

    def try_set_opacity(self, opacity):
        return self.opacity.set(opacity)

    def try_set_color(self, color):
        return self.color.set(color)

    def try_set_stroke(self, stroke):
        return self.stroke.set(stroke)

    def rgb_str(self):
        red = round(self.color.get()*255)
        return '%s,0,%s' % (red, 255-red)


class SvgPath:
    def __init__(self, path, scale):
        self.path = path
        self.scale = scale

    def _scale_coord(self, c):
        return str(round(c[0]*self.scale, 6)) + ',' + str(round(c[1]*-self.scale, 6))

    def _coord_str(self):
        return 'M ' + ' L '.join(self._scale_coord(c) for c in self.path.coords)

    def tosvg(self):
        return '<path d="%s" stroke="rgb(%s)" stroke-dasharray="%s" opacity="%s" />' % (
            self._coord_str(),
            self.path.rgb_str(),
            self.path.stroke.get(),
            self.path.opacity.get()
        )


class GeoJsonPath:
    def __init__(self, path):
        self.path = path

    def togeojson(self):
        return {
            'type' : 'Feature',
            'properties': {},
            'geometry' : {
                'type' : 'LineString',
                'coordinates' : self.path.coords
            },
            'style' : {
                'stroke' : 'rgb(' + self.path.rgb_str() + ')',
                'stroke-dasharray' : self.path.stroke.get(),
                'opacity' : self.path.opacity.get()
            }
        }


def read_googjson(filename):
    with open(PATH+filename) as f:
        data = json.load(f)
        return data['locations']    

def write_geojson(filename, paths):
    geojson = {
        'type' : 'FeatureCollection',
        'features' : [GeoJsonPath(e).togeojson() for e in paths]
    }
    with open(PATH+filename, 'w') as outfile:
        json.dump(geojson, outfile)

def write_svg(filename, paths, canvas, stroke_width, scale):
    dimensions = 'width="%s" height="%s" viewBox="%s %s %s %s"' % (
        canvas.width(),
        canvas.height(),
        canvas.left(),
        canvas.top(),
        canvas.width(),
        canvas.height()
    )
    svg = '<svg %s xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink">' % dimensions

    svg += """
    <style>
        path {
            stroke-linecap: round;
            stroke-width: %s;
            fill: none;
        }
    </style>
    """ % stroke_width
    
    svg += ''.join(SvgPath(e, scale).tosvg() for e in paths)
    svg += '</svg>'
    with open(PATH+filename, 'w') as outfile:
        outfile.write(svg)


def analyze(googjson_locations, scale):
    count = len(googjson_locations)
    paths = []
    canvas = Canvas(scale)
    p = Path()
    i = 0
    while i < count:
        l = GoogJsonLocation(googjson_locations[i])
        if not l.is_confirmed():
            i += 1
            continue
        coord = l.get_lon_lat()
        p.append(coord)
        canvas.add(coord)
        p.try_set_opacity(round(1-i/count, 2))
        same_color = p.try_set_color(0 if l.get_time().weekday() < 5 else 1)
        stroke = Path.SOLID if l.is_walking() else Path.DASHED
        same_stroke = p.try_set_stroke(stroke)
        if not same_stroke or not same_color:
            paths.append(p)
            p = Path()
        else:
            i += 1
    paths.reverse()
    return paths, canvas


if __name__ == '__main__':
    p = argparse.ArgumentParser(description="Converts Google Maps Timeline data to GeoJSON or SVG so that you can view your entire timeline on one map.",
    epilog="Example: python3 convertmapstimeline.py 'Location History.json' timeline.svg")
    p.add_argument('input_file', help='The input JSON timeline file obtained from Google Takeout')
    p.add_argument('output_file', help='The output file to write the result to')
    p.add_argument('--geojson', action='store_true', help='Output GeoJSON for use with mapping applications. The default is SVG for direct viewing in a browser.')
    p.add_argument('-w', '--stroke-width', type=float, default=0.5, help='The width of the lines. Applies only to SVG output. Useful if you want to generate different zoom levels. (default: 0.5)')
    p.add_argument('-s', '--scale', type=float, default=100.0, help='The scale of the canvas. Applies only to SVG output. Increase to be able to zoom in more closely. (default: 100)')
    p.add_argument('-c', '--canvas', help='lat,lon,height,width Set the SVG viewBox to the area around the given center (lat,lon) with the given height and width (in float degrees). If not given, everything will be on the canvas. E.g. 48.86,2.34,0.05,0.06 for the city of Paris.')

    args = p.parse_args()

    print('Reading input file...')
    data = read_googjson(args.input_file)

    print('Analyzing data...')
    paths, canvas = analyze(data, args.scale)
    if args.canvas:
        d = args.canvas.split(',')
        canvas.set_center_dimensions(float(d[0]), float(d[1]), float(d[2]), float(d[3]))

    print('Rendering output file...')
    if args.geojson:
        write_geojson(args.output_file, paths)
    else:
        write_svg(args.output_file, paths, canvas, args.stroke_width, args.scale)

#opacity age
#dotted speed
#color weekday
