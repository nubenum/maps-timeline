The Google Maps Timeline (https://www.google.de/maps/timeline) allows you, if enabled, to view the places you visited and the paths you took. This script will convert the Timeline data to SVG or GeoJSON to view all your movements on one map.

![Example Timeline Map](example.png?raw=true)

View a zoomable version at https://projekt.nubenum.com/18/4/maps-timeline/

When exporting as SVG, you can view the result directly in the browser of your choice, however, you will probably need to zoom out and scroll around a bit to find your paths on the canvas (also see the `--scale` argument). Depending on the size of your history, the SVG might take some time to load.

To obtain your own data, use Google Takeout (http://takeout.google.com) to download your "Location History" in JSON format. This script will accept the downloaded and extracted JSON file as input.

Currently, the following data is presented:

* Blue: Weekdays (Mon-Fri)
* Red: Weekends (Sat-Sun)
* Dotted: In Vehicle
* Solid: On Foot
* Faded: Less recent paths

You can of course edit the script to suit your needs.


```
usage: convertmapstimeline.py [-h] [--geojson] [-w STROKE_WIDTH] [-s SCALE]
                              [-c CANVAS]
                              input_file output_file

Converts Google Maps Timeline data to GeoJSON or SVG so that you can view your
entire timeline on one map.

positional arguments:
  input_file            The input JSON timeline file obtained from Google
                        Takeout
  output_file           The output file to write the result to

optional arguments:
  -h, --help            show this help message and exit
  --geojson             Output GeoJSON for use with mapping applications. The
                        default is SVG for direct viewing in a browser.
  -w STROKE_WIDTH, --stroke-width STROKE_WIDTH
                        The width of the lines. Applies only to SVG output.
                        Useful if you want to generate different zoom levels.
                        (default: 0.5)
  -s SCALE, --scale SCALE
                        The scale of the canvas. Applies only to SVG output.
                        Increase to be able to zoom in more closely. (default:
                        100)
  -c CANVAS, --canvas CANVAS
                        lat,lon,height,width Set the SVG viewBox to the area
                        around the given center (lat,lon) with the given
                        height and width (in float degrees). If not given,
                        everything will be on the canvas. E.g.
                        48.86,2.34,0.05,0.06 for the city of Paris.

Example: python3 convertmapstimeline.py 'Location History.json' timeline.svg
```
