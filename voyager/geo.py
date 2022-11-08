import geopy.distance as gp
import numpy as np
import math
from typing import *


def closest_coordinate_index(array, value):

    idx = np.searchsorted(array, value, side="left")
    if idx > 0 and (idx == len(array) or math.fabs(value - array[idx-1]) < math.fabs(value - array[idx])):
        return idx-1
    else:
        return idx

def lonlat_from_displacement(dx: float, dy: float, origin: Tuple[float, float], method='geodesic') -> Tuple[float, float]:

    if method == 'geodesic': 

        lon, lat = geodesic(dx, dy, origin)

        return lon, lat

    elif method == 'great circle':

        lon, lat = great_circle(dx, dy, origin)

        return lon, lat

    else: 
        raise ValueError("Method must be geodesic or great circle")

def geodesic(dx, dy, origin):

    # Calculate the bearing of the displacement
    bearing = bearing_from_displacement(dx, dy)

    # Calculate the distance from the displacement
    distance = distance_from_displacement(dx, dy)

    # Transforms the point to a geopy point
    start = gp.lonlat(*origin)

    # Using WGS-84 per default
    destination = (gp.distance(kilometers=distance)
                      .destination(point=start, bearing=bearing))

    return destination.longitude, destination.latitude


def great_circle(dx, dy, origin):

    longitude, latitude = origin

    r_earth = 6371 # km

    new_latitude  = latitude  + (dy / r_earth) * (180 / np.pi)
    new_longitude = longitude + (dx / r_earth) * (180 / np.pi) / np.cos(latitude * np.pi/180)

    return new_longitude.item(), new_latitude.item()


def distance(origin, target):

    return gp.distance(gp.lonlat(*origin), gp.lonlat(*target)).km

def distance_from_displacement(dx, dy):

    return np.linalg.norm(np.array((dx, dy)))

def bearing_from_displacement(dx, dy):

    angle = np.rad2deg(np.arctan2(dy, dx))

    bearing = (90 - angle)

    return bearing

def bearing_from_lonlat(position: np.ndarray, target: np.ndarray):

    lat_pos = np.deg2rad(position[1])
    lat_tgt = np.deg2rad(target[1])
    d_lon = np.deg2rad(position[0]-target[0])

    x = np.sin(d_lon) * np.cos(lat_tgt)
    y = np.cos(lat_pos) * np.sin(lat_tgt) - np.sin(lat_pos) * np.cos(lat_tgt) * np.cos(d_lon)

    bearing = np.arctan2(x, y)

    bearing = (np.rad2deg(bearing) + 360) % 360

    return bearing