import numpy as np
from . import utils
from . import geo
from . import search
from tqdm import tqdm_notebook as tqdm
import multiprocessing as mp
from xarray import DataArray
import pandas as pd

import geopandas
import matplotlib.pyplot as plt
import cartopy

from typing import Tuple, List, Dict




class Simulation:

    def __init__(self, model, 
                       craft, 
                       duration,
                       timestep, 
                       target_point, 
                       speed, 
                       start_date, 
                       end_date, 
                       launch_freq, 
                       bbox, 
                       departure_points, 
                       data_directory, 
                       n_reps=1) -> None:

        self.craft      = craft
        self.model      = model
        self.duration   = duration
        self.dt         = timestep
        self.n_reps     = n_reps

        self.target     = target_point
        self.speed      = speed

        self.data_directory = data_directory

        # Define datetime objects to limit simulation
        self.start_date     = pd.Timestamp(start_date)
        self.end_date       = pd.Timestamp(end_date) 
        
        # Interval in days to launch vessels
        self.launch_day_frequency = launch_freq
        
        # The bounding box limits the region of simulation
        self.bbox = bbox

        # Starting points for trajectories
        self.departure_points = departure_points

        # Load data in time period on currents
        self.u_current_all, self.v_current_all  = utils.load_data(start=self.start_date, 
                                                                  end=self.end_date,
                                                                  bbox=self.bbox,
                                                                  data_directory=self.data_directory,
                                                                  source="currents")
        # Load adata in time period on winds
        self.u_wind_all, self.v_wind_all        = utils.load_data(start=self.start_date, 
                                                                  end=self.end_date,
                                                                  bbox=self.bbox,
                                                                  data_directory=self.data_directory,
                                                                  source="winds")

        self.dates = pd.date_range(self.start_date, self.end_date) #self.u_current_all.time.sel(time=slice(self.start_date, self.end_date)).values
        
        # Find a sequence of targets to follow to the destination
        grid    = search.GridWithWeights()
        astar   = search.Astar(grid)
        courses = [astar.search(start, self.destination) for start in self.departure_points]


        # The choice of model governs the behaviour of the vessel trajectories
        self.model = Model(self.duration, self.dt, self.model, self.target, self.speed)

    def interpolate(self, x: DataArray, start_date: np.datetime64, end_date: np.datetime64) -> RegularGridInterpolator:
        """Wraps a RegularGridInterpolator object, estimating the velocity fields
        in undocumented longitudes and latitudes.

        Args:
            x (Xarray): Xarray of a velocity field with (longitude, latitude, time) fields
            start_date (np.datetime64): Start date of interpolation
            end_date (np.datetime64): End date of interpolation

        Returns:
            RegularGridInterpolator: Interpolation function
        """
        
        # Select data only in the specified time interval
        X = x.sel(time=slice(start_date, end_date))

        return RegularGridInterpolator((np.arange(X.shape[0]), x.longitude, x.latitude), np.transpose(X.values, (0, 2, 1)), bounds_error=False, fill_value=np.nan)

    def run(self, results_file: str):
        """Runs a model a specified number of times in time and space on Earth, generating a 
        GeoJSON file called 'results_file' with coordinates and timestamps for departure of all trajectories. 

        Args:
            results_file (str): A GeoJSON file with a list of trajectories with associated coordinates and timestamps.
        """

        time_delta     = pd.Timedelta(self.launch_day_frequency, 'D')
        date           = self.start_date

        all_results = {}
        # all_drifts  = []
        progress = tqdm(self.dates[::self.launch_day_frequency])
        for launch_day in progress:

            progress.set_description(f"Date: {launch_day.strftime('%Y-%m-%d')}")
            progress.refresh() # to show immediately the update

            end_date = launch_day + pd.Timedelta(self.duration, 'D')

            # Naming:
            # u_current - current in e-w direction / longitude / x
            # v_current - current in n-s direction / latitude / y

            # Interpolate the current speeds for the current day
            u_current = self.interpolate(self.u_current_all, launch_day, end_date) 
            v_current = self.interpolate(self.v_current_all, launch_day, end_date) 
            
            # Interpolate the wind speeds for the current day
            u_wind = self.interpolate(self.u_wind_all, launch_day, end_date) 
            v_wind = self.interpolate(self.v_wind_all, launch_day, end_date) 

            # Send out a number of vessels every day
            vessels  = self.initialize_vessels(self.departure_points, self.n_reps)

            # Input arguments to model
            options =  [(vessel, (u_current, v_current), (u_wind, v_wind)) for vessel in vessels]

            # Run several calls to the model in parallel,
            # In practice launching multiple vessels simultaneously
            # Observe that the gain is especially notable when simulating many vessels, not their duration
            with mp.Pool(mp.cpu_count()) as p:

                results = p.starmap(self.model, options)
                all_results[date.strftime('%Y-%m-%d')] = results

            date += time_delta

        # Save trajectories to file        
        utils.save_to_GeoJSON(all_results, results_file)


    def initialize_vessels(self, departure_points: List, n_reps=1) -> List[Vessel]:
        """Initializes a list of vessel objects from a list of departure coordinates.

        Args:
            departure_points (List): List of coordinate tuples or coordinate lists with two elements

        Returns:
            List[Vessel]: List of vessel objects
        """

        return [Vessel(np.array([x]), np.array([y]), craft=self.craft) for x, y in departure_points for rep in range(n_reps)]


    def plot(self, trajectory_file = None, **kwargs):
        """Utility function to statically visualize the calculated trajectories

        Args:
            trajectory_file (str, optional): The GeoJSON files with trajectories. Defaults to None.

        Returns:
            fig, ax: Matplotlib figure and axis tuples
        """
        
        # Create matplotlib figure objects
        fig, ax = plt.subplots(subplot_kw={'projection': cartopy.crs.PlateCarree()}, figsize=(20,10))

        # Choose coastline resolution
        ax.coastlines('50m')

        # Limit map to bounding box
        ax.set_extent([self.bbox[0], self.bbox[2], self.bbox[1], self.bbox[3]], cartopy.crs.PlateCarree())

        # Add ocean and land features, for visuals
        ax.add_feature(cartopy.feature.OCEAN, zorder=0)
        ax.add_feature(cartopy.feature.LAND, zorder=0, edgecolor='black')

        # Adds gridds to visual
        ax.gridlines(crs=cartopy.crs.PlateCarree(), draw_labels=True,
                  linewidth=2, color='gray', alpha=0.2, linestyle='--')

        # Use geopandas built-in GeoJSON processing and visualization
        df = geopandas.read_file(trajectory_file)
        df.plot(ax=ax, zorder=10, **kwargs)

        return fig, ax