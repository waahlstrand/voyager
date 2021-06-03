from typing import Tuple
import numpy as np

from .vessel import Vessel
from .chart import Chart
from .move import Displacement

class Model:

    def __init__(self, duration: int, dt: float, sigma = 2000.0, tolerance = 0.5e-3) -> None:
        self.duration = duration
        self.dt       = dt
        self.chart = None
        self.sigma = sigma
        self.tolerance = tolerance

    def use(self, chart: Chart):

        self.chart = chart

        return self

    def velocity(self, t, longitude, latitude):

        assert self.chart != None

        # Calculate current speeds
        v_x_current = self.chart.u_current((t, longitude, latitude))
        v_y_current = self.chart.v_current((t, longitude, latitude))

        # Test if we have reached land
        # If so, break simulation
        if np.isnan(v_x_current) or np.isnan(v_y_current):
            return None, None

        # Calculate wind speeds
        v_x_wind = self.chart.u_wind((t, longitude, latitude))
        v_y_wind = self.chart.v_wind((t, longitude, latitude))

        return (np.array([v_x_current, v_y_current]), np.array([v_x_wind, v_y_wind]))

    def run(self, vessel: Vessel) -> Vessel:
        """Calculates the trajectory of a vessel object in space over time.

        Trajectories are calculated by estimating the displacement in km from a position in
        (longitude, latitude) coordinates, and converting the displacement back to (longitude, latitude).

        Simulation is stopped when the vessel encounters NaN, indicating land or area outside the simulation region.

        Assumes a spherical Earth.

        Args:
            vessel (Vessel): Vessel object with initial position

        Returns:
            Vessel: A modified vessel object with full trajectory
        """

        # Set random seed
        # Important, otherwise all virtual threads will return the same result
        np.random.seed()

        longitude = vessel.x
        latitude  = vessel.y

        # Constant
        N_SECONDS_IN_DAY = 86400

        # Initialization
        dx = 0
        dy = 0

        target_tol = (self.dt) * self.tolerance # 1/1000 is a good value

        # The type of displacement is handled by the vessel mode of traversal
        displacement = Displacement(vessel, self.dt)

        for t in np.arange(start=0, stop=self.duration, step=self.dt/N_SECONDS_IN_DAY):
            
            # Calculate interpolated velocity at current coordinates
            c, w = self.velocity(t, longitude, latitude)

            # If return is None, we have reached land
            if c is None or w is None:
                break

            # Calculate displacement
            dx, dy = displacement.move(c, w)\
                                 .with_uncertainty(sigma=self.sigma)\
                                 .km()
               
            # print(dx, dy)
            # Calculate new longitude, latitude from displacement
            # Using great circle distances
            longitude, latitude = displacement.to_lonlat(dx, dy, longitude, latitude)

            # Update vessel data
            vessel.update_distance(dx, dy)\
                  .update_position(longitude, latitude)\
                  .update_mean_speed(self.dt)

            # Check progress along route
            is_arrived = vessel.has_arrived(longitude, latitude, target_tol)

            if is_arrived:
                break

        return vessel
