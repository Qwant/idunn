import json
import os
from shapely.geometry import MultiPolygon, box, shape

# Approximate shape of Metropolitan France
# (source: https://download.geofabrik.de/europe/france.html)
france_poly_filename = os.path.join(
    os.path.dirname(os.path.realpath(__file__)), "./data/france.poly"
)

# Approximate shape of some cities surroundings. These shapes have been defined using the following
# script: https://gist.github.com/remi-dupre/6c4a1d699e48c00e134657dc1164a2c9
cities_surrounds_file = os.path.join(
    os.path.dirname(os.path.realpath(__file__)), "./data/surroundings.json"
)


def parse_poly(lines):
    """
    Parse an Osmosis polygon filter file.

    Accept a sequence of lines from a polygon file, return a shapely.geometry.MultiPolygon object.

    http://wiki.openstreetmap.org/wiki/Osmosis/Polygon_Filter_File_Format
    """
    in_ring = False
    coords = []

    for (index, line) in enumerate(lines):
        if index == 0:
            # first line is junk.
            pass

        elif index == 1:
            # second line is the first polygon ring.
            coords.append([[], []])
            ring = coords[-1][0]
            in_ring = True

        elif in_ring and line.strip() == "END":
            # we are at the end of a ring, perhaps with more to come.
            in_ring = False

        elif in_ring:
            # we are in a ring and picking up new coordinates.
            ring.append(list(map(float, line.split())))

        elif not in_ring and line.strip() == "END":
            # we are at the end of the whole polygon.
            break

        elif not in_ring and line.startswith("!"):
            # we are at the start of a polygon part hole.
            coords[-1][1].append([])
            ring = coords[-1][1][-1]
            in_ring = True

        elif not in_ring:
            # we are at the start of a polygon part.
            coords.append([[], []])
            ring = coords[-1][0]
            in_ring = True

    return MultiPolygon(coords)


# Load shape for France
with open(france_poly_filename) as france_file:
    france_polygon = parse_poly(france_file.readlines())

# Load shape for some cities surrounding
with open(cities_surrounds_file, "r") as f:
    city_surrounds_polygons = {
        city_name: shape(geojson) for city_name, geojson in json.load(f).items()
    }


def bbox_inside_polygon(minx, miny, maxx, maxy, poly, threshold=0.75):
    rect = box(minx, miny, maxx, maxy)
    return poly.intersection(rect).area / rect.area > threshold
