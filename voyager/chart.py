import pandas as pd
import numpy as np
from scipy.interpolate import RegularGridInterpolator
import dask

from . import utils
from . import search

class Chart:
    """
    The Chart object symbolizes the map, including wind and current data, as well as the grid used for path finding.

    A chart at any moment is a bounding box of the underlying available data at a specific date interval.
    """

    def __init__(self, bbox, start_date, end_date) -> None:
        
        self.bbox = bbox
        self.start_date = start_date
        self.end_date = end_date

        self.u_current_all = None
        self.v_current_all = None
        self.u_wind_all = None
        self.v_wind_all = None

        self.longitudes = None
        self.latitudes  = None
        self.grid = None


    def load(self, data_dir: str, **kwargs):
        """Loads the Chart data for dynamical updating. Updated the winds, currents and the weighted grid.

        Args:
            data_dir (str): The root directory of the velocity data

        Returns:
            Chart: The Chart instance
        """

        self.data_dir = data_dir

        with dask.config.set(**{'array.slicing.split_large_chunks': True}):

            self.u_current_all, self.v_current_all  = utils.load_data(start=self.start_date, 
                                                                    end=self.end_date,
                                                                    bbox=self.bbox,
                                                                    data_directory=self.data_dir,
                                                                    source="currents")

            self.u_wind_all, self.v_wind_all        = utils.load_data(start=self.start_date, 
                                                                    end=self.end_date,
                                                                    bbox=self.bbox,
                                                                    data_directory=self.data_dir,
                                                                    source="winds")


        map          = self.u_current_all.sel(time=self.start_date)

        self.longitudes = map.longitude.values
        self.latitudes  = map.latitude.values

        self.grid    = search.WeightedGrid.from_map(map, **kwargs)


        return self

    def interpolate(self, date: pd.Timestamp, duration: int):
        """Interpolates the loaded data for a certain timestamp, and a duration in days.

        Args:
            date (pd.Timestamp): Date to start interpolating from
            duration (int): Duration of the interpolation in days

        Returns:
            Chart: The Chart instance
        """

        end_date = date + pd.Timedelta(duration, 'D')

        self.u_current = _interpolate(self.u_current_all, date, end_date) 
        self.v_current = _interpolate(self.v_current_all, date, end_date) 
            
        # Interpolate the wind speeds for the current day
        self.u_wind = _interpolate(self.u_wind_all, date, end_date) 
        self.v_wind = _interpolate(self.v_wind_all, date, end_date) 

        return self
        

def _interpolate(x, start_date, end_date):

    X = x.sel(time=slice(start_date, end_date))

    return RegularGridInterpolator((np.arange(X.shape[0]), x.longitude, x.latitude), 
                                    np.transpose(X.values, (0, 2, 1)), 
                                    bounds_error=False, 
                                    fill_value=np.nan)