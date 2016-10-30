from zipfile import ZipFile
from io import TextIOWrapper
from csv import DictReader
from math import pow, sqrt, pi, log

from osgeo import osr, ogr
from .compat import cairo

# WGS 84, http://spatialreference.org/ref/epsg/4326/
EPSG4326 = '+proj=longlat +ellps=WGS84 +datum=WGS84 +no_defs'

# Web Mercator, http://spatialreference.org/ref/sr-org/6864/
EPSG3857 = '+proj=merc +lon_0=0 +k=1 +x_0=0 +y_0=0 +a=6378137 +b=6378137 +towgs84=0,0,0,0,0,0,0 +units=m +no_defs'

def main():
    '''
    '''
    lonlats = iterate_zipfile_points('us-ca-berkeley.zip')
    points = project_points(lonlats)
    
    xmin, ymin, xmax, ymax = calculate_bounds(points)
    
    print(points[:3], (xmin, ymin), (xmax, ymax))
    
    resolution = 2
    surface, context, scale = make_context(xmin, ymin, xmax, ymax, resolution=resolution)

    # Map units per reference pixel (http://www.w3.org/TR/css3-values/#reference-pixel)
    muppx = resolution / scale
    
    black = 0, 0, 0
    light_green = 0x74/0xff, 0xA5/0xff, 0x78/0xff

    context.set_source_rgb(1, 1, 1)
    context.rectangle(xmin, ymax, xmax - xmin, ymin - ymax)
    context.fill()
    
    context.set_line_width(.25 * muppx)

    for (x, y) in points:
        context.arc(x, y, 15, 0, 2 * pi)
        context.set_source_rgb(*light_green)
        context.fill()
        context.arc(x, y, 15, 0, 2 * pi)
        context.set_source_rgb(*black)
        context.stroke()
    
    print('scale:', scale)
    print('zoom:', calculate_zoom(scale, resolution))
    
    surface.write_to_png('preview.png')

def iterate_zipfile_points(filename):
    '''
    '''
    with open(filename, 'rb') as file:
        zip = ZipFile(file)
        csv_names = [name for name in zip.namelist() if name.endswith('.csv')]
        csv_file = TextIOWrapper(zip.open(csv_names[0]))
        
        for row in DictReader(csv_file):
            try:
                lon, lat = float(row['LON']), float(row['LAT'])
            except:
                continue
            
            if -180 <= lon <= 180 and -90 <= lat <= 90:
                yield (lon, lat)

def project_points(lonlats):
    '''
    '''
    osr.UseExceptions()
    sref_geo = osr.SpatialReference(); sref_geo.ImportFromProj4(EPSG4326)
    sref_map = osr.SpatialReference(); sref_map.ImportFromProj4(EPSG3857)
    project = osr.CoordinateTransformation(sref_geo, sref_map)
    
    points = list()
    
    minlon, minlat, maxlon, maxlat = 180, 90, -180, -90
    
    for (lon, lat) in lonlats:
        geom = ogr.CreateGeometryFromWkt('POINT({:.7f} {:.7f})'.format(lon, lat))
        geom.Transform(project)
        points.append((geom.GetX(), geom.GetY()))
        
        minlon, minlat = min(lon, minlon), min(lat, minlat)
        maxlon, maxlat = max(lon, maxlon), max(lat, maxlat)
    
    print(minlon, minlat, maxlon, maxlat)
    
    return points

def stats(values):
    '''
    '''
    mean = sum(values) / len(values)
    deviations = [pow(val - mean, 2) for val in values]
    stddev = sqrt(sum(deviations) / len(values))

    return mean, stddev

def calculate_zoom(scale, resolution):
    ''' Calculate web map zoom based on scale.
    '''
    earth_diameter = 6378137 * 2 * pi
    scale_at_zero = resolution * 256 / earth_diameter
    zoom = log(scale / scale_at_zero) / log(2)
    
    return zoom

def calculate_bounds(points):
    '''
    '''
    xs, ys = zip(*points)

    # use standard deviation to avoid far-flung mistakes
    (xmean, xsdev), (ymean, ysdev) = stats(xs), stats(ys)
    xmin, xmax = xmean - 5 * xsdev, xmean + 5 * xsdev
    ymin, ymax = ymean - 5 * ysdev, ymean + 5 * ysdev
    
    # look at the actual points
    okay_xs = [x for (x, y) in points if (xmin <= x <= xmax)]
    okay_ys = [y for (x, y) in points if (ymin <= y <= ymax)]
    left, bottom = min(okay_xs), min(okay_ys)
    right, top = max(okay_xs), max(okay_ys)
    
    # pad by 2% on all sides
    width, height = right - left, top - bottom
    left -= width / 50
    bottom -= height / 50
    right += width / 50
    top += height / 50
    
    return left, bottom, right, top
    
def make_context(left, bottom, right, top, width=668, resolution=1):
    ''' Get Cairo surface, context, and drawing scale.
    
        668px is the width of a comment box in Github, one place where
        these previews are designed to be used.
    '''
    aspect = (right - left) / (top - bottom)

    hsize = int(resolution * width)
    vsize = int(hsize / aspect)

    hscale = hsize / (right - left)
    vscale = (hsize / aspect) / (bottom - top)

    hoffset = -left
    voffset = -top

    surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, hsize, vsize)
    context = cairo.Context(surface)
    context.scale(hscale, vscale)
    context.translate(hoffset, voffset)
    
    return surface, context, hscale

if __name__ == '__main__':
    exit(main())
