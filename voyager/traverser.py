import multiprocessing as mp

import pandas as pd
from .chart import Chart
from .models import Vessel, Model
from . import utils
from typing import *

class Traverser:

    def __init__(self, mode = 'drift', 
                       craft = 1, 
                       duration = 60,
                       timestep = 1, 
                       destination = [], 
                       speed = 2, 
                       start_date = '', 
                       end_date = '', 
                       launch_freq = 5, 
                       bbox = [], 
                       departure_points = [], 
                       data_directory = '', 
                       vessel_config='configs/vessels.yml') -> None:

        self.craft      = craft
        self.mode       = mode
        self.duration   = duration
        self.dt         = timestep
        self.vessel_config = vessel_config
        # self.n_reps     = n_reps

        self.destination = destination
        self.speed       = speed

        self.data_directory = data_directory

        # Define datetime objects to limit simulation
        self.start_date     = pd.to_datetime(start_date, infer_datetime_format=True)
        self.end_date       = pd.to_datetime(end_date, infer_datetime_format=True) 
        self.dates          = pd.date_range(self.start_date, self.end_date) 
        
        # Interval in days to launch vessels
        self.launch_day_frequency = launch_freq
        
        # The bounding box limits the region of simulation
        self.bbox = bbox

        # Starting points for trajectories
        self.departure_points = departure_points

    @classmethod
    def trajectory(
            cls,
            mode = 'drift', 
            craft = 1, 
            duration = 60,
            timestep = 1, 
            destination = [], 
            speed = 2, 
            date = '', 
            bbox = [], 
            departure_point = [], 
            data_directory = '', 
            vessel_params= {},
            chart_kwargs = {}, 
            model_kwargs = {}, 
            chart = None, 
            model = None) -> Dict:
        """Generates a single set of trajectories from a single set of departure and destination points.

        Args:
            mode (str, optional): The mode of propulsion, either 'sailing', 'paddling' or 'drift'. Defaults to 'drift'.
            craft (int, optional): The craft type. Defaults to 1.
            duration (int, optional): The maximal duration in days of the trajectories. Defaults to 60.
            timestep (int, optional): Timestep for updating the speed and position of the vessels. Defaults to 1.
            destination (list, optional): Destination coordinates in WGS84. Defaults to [].
            speed (int, optional): Paddling speed in m/s. Defaults to 2.
            date (str, optional): Date as a YYYY-MM-DD string. Defaults to ''.
            bbox (list, optional): Bounding box of the map. Defaults to [].
            departure_point (list, optional): Departure point in WGS84. Defaults to [].
            data_directory (str, optional): The root directory of the velocity data. Defaults to ''.
            vessel_params (dict, optional): Parameters for the vessel configuration. Defaults to {}.
            chart_kwargs (dict, optional): Parameters for the chart configuration. Defaults to {}.
            model_kwargs (dict, optional): Parameters for the model configuration. Defaults to {}.
            chart (_type_, optional): Pre-supplied Chart object. Defaults to None.
            model (_type_, optional): Pre-supplied Model object. Defaults to None.

        Returns:
            Dict: The trajectories as GeoJSON compliant dictionary
        """


        # The chart object keeps track of the region of interest
        # and the wind/current data for that region
        # It is shared by all vessels
        
        if not chart:
            start_date = pd.to_datetime(date, infer_datetime_format=True)
            end_date   = start_date + pd.Timedelta(duration, unit='days')
            chart = Chart(bbox, start_date, end_date).load(data_directory, **chart_kwargs)
        
        # The model object describes the equations of movement and
        # traversal across the oceans over time
        if not model:
            model = Model(duration, timestep, **model_kwargs)

        
        vessel = Vessel.from_position(departure_point, 
                                      craft = craft,
                                      chart = chart,
                                      destination = destination,
                                      speed =speed,
                                      mode = mode,
                                      params = vessel_params[mode][craft])

        # Interpolate the data for only the duration specified
        chart.interpolate(chart.start_date, duration)

        # Use the interpolated values in the model
        model.use(chart)

        # Run the model
        vessel = model.run(vessel)

        start_date_str = chart.start_date.strftime('%Y-%m-%d')
        stop_date_str  = (chart.start_date + pd.Timedelta(len(vessel.trajectory)*timestep, unit='s')).strftime('%Y-%m-%d')

        return utils.to_GeoJSON(vessel, start_date_str, stop_date_str, timestep)



    def run(self, model_kwargs={}, chart_kwargs={}) -> Dict[str, Dict]:
        """Generates a set of trajectories in a date range, with a certain launch day frequency for the vessels.

        Args:
            model_kwargs (dict, optional): Parameters for the model. Defaults to {}.
            chart_kwargs (dict, optional): Parameter for the chart. Defaults to {}.

        Returns:
            Dict[str, Dict]: A date-tagged dictionary with GeoJSON compliant dictionary results
        """

        # The chart object keeps track of the region of interest
        # and the wind/current data for that region
        # It is shared by all vessels
        chart = Chart(self.bbox, self.start_date, self.end_date).load(self.data_directory, **chart_kwargs)
        
        # The model object describes the equations of movement and
        # traversal across the oceans over time
        model = Model(self.duration, self.dt, **model_kwargs)

        results = {}
        for date in self.dates[::self.launch_day_frequency]:

            # Vessel objects are the individual agents traversing the ocean
            vessels = Vessel.from_positions(self.departure_points, 
                                            craft = self.craft,
                                            chart = chart, 
                                            destination = self.destination, 
                                            speed = self.speed, 
                                            mode = self.mode, 
                                            vessel_config=self.vessel_config)
            
            # Interpolate the data for only the duration specified
            chart.interpolate(date, self.duration)

            # Use the interpolated values in the model
            model.use(chart)

            trajectories = []

            for vessel in vessels:

                trajectories.append(model.run(vessel))

            # Add the trajectories for the date
            results.update({date.strftime('%Y-%m-%d'): trajectories})

        return results


    def run_mp(self, model_kwargs={}, chart_kwargs={}) -> Dict[str, Dict]:
        """Pseudo-parallel generation of a set of trajectories in a date range, with a certain launch day frequency for the vessels.

        Args:
            model_kwargs (dict, optional): Parameters for the model. Defaults to {}.
            chart_kwargs (dict, optional): Parameter for the chart. Defaults to {}.

        Returns:
            Dict[str, Dict]: A date-tagged dictionary with GeoJSON compliant dictionary results
        """
        # The chart object keeps track of the region of interest
        # and the wind/current data for that region
        # It is shared by all vessels
        chart = Chart(self.bbox, self.start_date, self.end_date).load(self.data_directory, **chart_kwargs)
        
        # The model object describes the equations of movement and
        # traversal across the oceans over time
        model = Model(self.duration, self.dt, **model_kwargs)

        results = {}
        for date in self.dates[::self.launch_day_frequency]:

            # Vessel objects are the individual agents traversing the ocean
            vessels = Vessel.from_positions(self.departure_points, 
                                            craft = self.craft,
                                            chart = chart, 
                                            destination = self.destination, 
                                            speed = self.speed, 
                                            mode = self.mode, 
                                            vessel_config=self.vessel_config)
            
            # Interpolate the data for only the duration specified
            chart.interpolate(date, self.duration)

            # Use the interpolated values in the model
            model.use(chart)

            with mp.Pool(mp.cpu_count()) as p:

                trajectories = p.map(model.run, vessels)

            # Add the trajectories for the date
            results.update({date.strftime('%Y-%m-%d'): trajectories})

        return results






