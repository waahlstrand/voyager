import numpy as np
import json
import os
import glob
import xarray as xr
import pandas as pd
from typing import List

from . import geo

def lonlat_from_displacement(dx, dy, origin):

    longitude, latitude = origin

    r_earth = 6371 # km

    new_latitude  = latitude  + (dy / r_earth) * (180 / np.pi)
    new_longitude = longitude + (dx / r_earth) * (180 / np.pi) / np.cos(latitude * np.pi/180)

    return np.asscalar(new_longitude), np.asscalar(new_latitude)

def normalize_longitude(lon):

    east = lon[np.where((lon >= 0) & (lon <= 180))]

    west = lon[np.where((lon > 180) & (lon <= 360))]-360

    return np.concatenate([east, west])

def get_departure_points(mask, longitude, latitude, offset=-1):

    mask[:,-1] = np.nan

    lon_coords = np.argmax(mask, axis=0) 

    lon_points = longitude[lon_coords]+offset
    lat_points = latitude[::-1]

    return np.vstack((lon_points, lat_points)).T

def save_to_GeoJSON(data, filename):

    format_dict = to_GeoJSON(data)

    with open(filename, 'w') as file:
        json.dump(format_dict, file, indent=4)


def to_GeoJSON(data):

    format_dict = {"type": "FeatureCollection",
                   "features": []}

    for date_key, vessels in data.items():
        # print(date_key, vessels)

        for vessel in vessels:

            d = {"type": "Feature", 
                "geometry": {
                    "type": "LineString",
                    "coordinates": vessel.trajectory
                },
                "properties": {
                    "date": date_key,
                    "number of points": len(vessel.trajectory),
                    "distance": vessel.distance,
                    "mean speed": vessel.mean_speed
                }}

            format_dict["features"].append(d)  

    return format_dict                



def ecmwf_to_xr(winds):

    # Change order of indexation, strictly ascending coordinates
    # longitude from -180 to +180
    # latitude from -90 to +90
    winds = winds.assign_coords(longitude = normalize_longitude(winds.longitude.values))
    winds = winds.reindex(latitude = list(reversed(winds.latitude)),
                          longitude = list(sorted(winds.longitude)))
    winds["time"] = winds.indexes['time'].normalize()
    
    # Change variable names
    winds = winds.rename({"u10": "u", "v10": "v"})

    return winds

def cmems_to_xr(currents):

    # Remove single value in depth dimension
    # Change variable names
    currents = currents.drop("depth")\
                       .squeeze()\
                       .rename({"uo_oras": "u", "vo_oras": "v"})

    currents["time"] = currents.indexes['time'].normalize()

    return currents

def load_data(start: pd.Timestamp, end: pd.Timestamp, bbox, data_directory, source, parallel=False):

    start_year = start.year
    end_year   = end.year

    years = pd.date_range(str(start_year), str(end_year)).to_period('Y')\
                                                .format(formatter=lambda x: x.strftime('%Y'))
    years = set(years)

    dates = pd.date_range(start, end)
    
    filenames = []
    for year in years:

        pattern = os.path.join(data_directory, source, year, "*.nc")

        filenames.extend(glob.glob(pattern))

    if source == "currents":
        # data = cmems_to_xr(filenames) 
        data = xr.open_mfdataset(filenames, parallel=parallel)
        data = cmems_to_xr(data)

    elif source == "winds":
        # data = ecmwf_to_xr(filenames)
        data = xr.open_mfdataset(filenames, parallel=parallel)
        data = ecmwf_to_xr(data)


    else:
        raise ValueError("Source must be currents or winds.")

    data = data.sel(time=dates, longitude=slice(bbox[0], bbox[2]), latitude=slice(bbox[1], bbox[3])).load()

    return data.u, data.v