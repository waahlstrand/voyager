import numpy as np
import json
import os
import glob
import xarray as xr
import pandas as pd
from typing import *

from .vessel import Vessel

def lonlat_from_displacement(dx: float, dy: float, origin: Tuple[float, float]) -> Tuple[float, float]:
    """Calculate a new longitude and latitude from a displacement from an origin, using the Great Circle Approximation.

    Args:
        dx (float): Displacement in x-axis
        dy (float): Displacement in y-axis
        origin (Tuple[float, float]): Origin in longitude-latitude, WGS84

    Returns:
        Tuple[float, float]: New coordinates in longitude-latitude, WGS84
    """

    longitude, latitude = origin

    r_earth = 6371 # km

    new_latitude  = latitude  + (dy / r_earth) * (180 / np.pi)
    new_longitude = longitude + (dx / r_earth) * (180 / np.pi) / np.cos(latitude * np.pi/180)

    return np.asscalar(new_longitude), np.asscalar(new_latitude)

def normalize_longitude(lon: np.ndarray) -> np.ndarray:
    """Normalize the longitude such that longitudinal degrees left of the prime meridian count as the east, 
    and the degrees right of the meridian count as the west. Used to normalize data from ECMWF vs CMEMS.

    Args:
        lon (nd.array): An array of longitudinal degrees

    Returns:
        np.ndarray: A normalized array of longitudinal degrees
    """

    east = lon[np.where((lon >= 0) & (lon <= 180))]

    west = lon[np.where((lon > 180) & (lon <= 360))]-360

    return np.concatenate([east, west])


def save_to_GeoJSON(data, filename):

    format_dict = to_GeoJSON(data)

    with open(filename, 'w') as file:
        json.dump(format_dict, file, indent=4)


def to_GeoJSON(vessel: Vessel, start_date: str, stop_date: str, dt: float) -> Dict:
    """Converts vessel data into a GeoJSON representation

    Args:
        vessel (Vessel): A Vessel object
        start_date (str): The start date of the trajectory
        stop_date (str): The end date of the trajectory
        dt (float): Timestep

    Returns:
        Dict: A dictionary compliant with GeoJSON
    """

    format_dict = {"type": "FeatureCollection",
                   "features": []
                   }

    format_dict["features"].append(
        {
            "type": "Feature",
            "geometry": {
                "type": "LineString",
                # "coordinates": [[y, x] for x, y in vessel.trajectory],
                "coordinates": vessel.trajectory,

            },
            "properties": {
                "start_date": start_date,
                "stop_date": stop_date,
                "timestep": dt,
                "distance": vessel.distance,
                "mean_speed": vessel.mean_speed,
                "destination": vessel.destination,
                "route": vessel.route_taken
            }          
        }
    )

    return format_dict


def ecmwf_to_xr(winds: xr.Dataset) -> xr.Dataset:
    """Normalizes the ECMWF data into a standard XArray format.

    Args:
        winds (xr.Dataset): Winds as a Dataset

    Returns:
        xr.Dataset: Winds as a normalized Dataset
    """

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

def cmems_to_xr(currents: xr.Dataset) -> xr.Dataset:
    """Normalizes the ECMWF data into a standard XArray format.

    Args:
        currents (xr.Dataset): Currents as a Dataset

    Returns:
        xr.Dataset: Currents as a normalized Dataset
    """
    # Remove single value in depth dimension
    # Change variable names
    currents = currents.drop("depth")\
                       .squeeze()\
                       .rename({"uo_oras": "u", "vo_oras": "v"})

    currents["time"] = currents.indexes['time'].normalize()

    return currents

def load_data(start: pd.Timestamp, end: pd.Timestamp, bbox: List, data_directory: str, source: str, parallel=False) -> Tuple[xr.DataArray, xr.DataArray]:
    """Reads the wind and current data from a directory with a specified structure, namely


    Args:
        start (pd.Timestamp): The start date 
        end (pd.Timestamp): The end date
        bbox (List): Bounding box of where to fetch data
        data_directory (str): Root directory of the data files
        source (str): Data source, either "currents" or "winds"
        parallel (bool, optional): Whether to load the data in parallel. Defaults to False.

    Raises:
        ValueError: Raised if the data source is not "currents" or "winds"

    Returns:
        Tuple[xr.DataArray, xr.DataArray]: A tuple of the velocity x (east-west) and y (south-north) components respectively.
    """

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
        data = xr.open_mfdataset(filenames, parallel=parallel)
        data = cmems_to_xr(data)

    elif source == "winds":
        data = xr.open_mfdataset(filenames, parallel=parallel)
        data = ecmwf_to_xr(data)


    else:
        raise ValueError("Source must be currents or winds.")

    data = data.sel(time=dates, longitude=slice(bbox[0], bbox[2]), latitude=slice(bbox[1], bbox[3])).load()

    return data.u, data.v