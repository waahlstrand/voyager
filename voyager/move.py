from . import geo
import numpy as np
from typing import *

class Displacement:

    def __init__(self, vessel, dt) -> None:
        super().__init__()

        self.vessel = vessel
        self.dt     = dt
        self.dxy = None

    def move(self, c: np.ndarray, w: np.ndarray):
        """Creates the displacement due to a current and wind velocity.

        Args:
            c (np.ndarray): current velocity
            w (np.ndarray): wind velocity

        Raises:
            ValueError: Raised if the model displacement is not drifting, paddling or sailing

        Returns:
            Displacement: The Displacement instance
        """

        if self.vessel.mode == 'drifting':
            return self.from_drift(c, w)

        elif self.vessel.mode == 'paddling':
            return self.from_paddling(c, w, (self.vessel.x, self.vessel.y), self.vessel.target, self.vessel.speed)

        elif self.vessel.mode == 'sailing':
            return self.from_sailing(c, w, (self.vessel.x, self.vessel.y), self.vessel.target)

        else:
            raise ValueError("Mode of displacement should be drifting, paddling or sailing")

    @staticmethod
    def leeway_displacement(w: np.ndarray, Sl: float, Yt: float, dt: float):
        """Calculates the leeway displacement from vessel parameters 
        and wind speed.

        Args:
            w (np.ndarray): The wind velocity with two components
            Sl (float): vessel parameter
            Yt (float): vessel parameter
            dt (float): Time step

        Returns:
            np.ndarray: The displacement due to leeway wind
        """

        # Calculate leeway velocity from wind
        leeway = Displacement.leeway_velocity(w, Sl, Yt)

        # Convert leeway to m/s from knots
        leeway = Displacement.knots_to_si(leeway)

        # Calculate displacement
        dxy_leeway = leeway * dt

        return dxy_leeway

    @staticmethod
    def leeway_velocity(w: np.ndarray, Sl: float, Yt: float) -> np.ndarray:
        """Calculates the leeway wind velocity from vessel parameters and
        wind speed.

        Args:
            w (np.ndarray): The wind velocity with two components
            Sl (float): vessel parameter
            Yt (float): vessel parameter

        Returns:
            np.ndarray: The velocity from leeway wind
        """

        # Convert from m/s to knots
        w = Displacement.si_to_knots(w)

        leeway = np.zeros_like(w)

        if np.abs(w[0]) > 6:
            leeway[0] = (Sl * w[0]) + Yt
        else:
            leeway[0] = (Sl + Yt / 6) * w[0]

        if np.abs(w[1]) > 6:
            leeway[1] = (Sl * w[1]) + Yt
        else:
            leeway[1] = (Sl + Yt / 6) * w[1]

        return leeway

    @staticmethod
    def levison_leeway_displacement(w: np.ndarray, dt: float):
        """Calculates the displacement due to leeway forces,
        using the Levison method.

        Args:
            w (np.ndarray): Wind velocity
            dt (float): Timestep

        Raises:
            ValueError: Raised if the absolute wind velocity is a non-positive number

        Returns:
            np.ndarray: The displacement due to leeway forces
        """

        # Convert from m/s to knots
        w = Displacement.si_to_knots(w)

        # Prefill the leeway velocity
        leeway = np.zeros_like(w)

        for idx in (0, 1):

            w_abs = np.abs(w[idx])
            w_sign = np.sign(w[idx])
            
            if w_abs < 1:
                leeway[idx] = 0
            elif 1 <= w_abs <= 3:
                leeway[idx] = 0.5
            elif 3 < w_abs <= 6:
                leeway[idx] = 1 
            elif 6 < w_abs <= 10:
                leeway[idx] = 2
            elif 10 < w_abs <= 16:
                leeway[idx] = 3 
            elif 16 < w_abs <= 21:
                leeway[idx] = 4.5
            elif 21 < w_abs <= 27:
                leeway[idx] = 6 
            elif 27 < w_abs <= 33:
                leeway[idx] = 7 
            elif 33 < w_abs <= 40:
                leeway[idx] = 6 
            elif w_abs > 40:
                leeway[idx] = 4.5
            else:
                raise ValueError(f"Invalid absolute velocity {w_abs}")

            leeway[idx] *= w_sign

        leeway = Displacement.knots_to_si(leeway)

        dxy_leeway = leeway * dt

        return dxy_leeway


    @staticmethod
    def rotate(x: np.ndarray, angle: float) -> np.ndarray:

        r = np.array(( 
                    (np.cos(angle), -np.sin(angle)),
                    (np.sin(angle),  np.cos(angle)) 
                    ))

        return r.dot(x)

    def from_drift(self, c: np.ndarray, w: np.ndarray):
        """Generate displacement due to only drifting with the winds and currents. 

        Args:
            c (np.ndarray): Current velocity
            w (np.ndarray): Wind velocity

        Returns:
            Displacement: The Displacement instance
        """

        # Calculate the drift due to the currents
        dxy_c = c * self.dt

        if self.vessel.craft != 7:

            # Load vessel parameters
            Sl = self.vessel.params["Sl"]
            Yt = self.vessel.params["Yt"]
            Da = self.vessel.params["Da"]

            # Convert to degrees
            Da = np.deg2rad(Da)

            # the deflections due to Da half right
            ## and half left of the wind
            flip = np.random.choice((1, -1))

            # Calculate the leeway speed and displacement
            dxy_leeway = Displacement.leeway_displacement(w, Sl, Yt, self.dt)

            # Calculate the deflection as a rotation
            dxy_deflect = Displacement.rotate(dxy_leeway, angle=Da*flip)

            # Total displacement in metres
            self.dxy = dxy_deflect + dxy_c

        elif self.vessel.craft == 7:

            dxy_leeway = Displacement.levison_leeway_displacement(w, self.dt)

            self.dxy = dxy_leeway + dxy_c

        return self

    def from_paddling(self, c: np.ndarray, w: np.ndarray, position: np.ndarray, target: np.ndarray, speed: float):
        """Generate displacement due to paddling with a certain paddling speed, as well as environmental factors from
        currents and winds.

        Args:
            c (np.ndarray): Current velocity
            w (np.ndarray): Wind velocity
            position (np.ndarray): Current position coordinates
            target (np.ndarray): Destination position coordinates
            speed (float): Paddling speed

        Returns:
            Displacement: The Displacement instance
        """

        # Calculate the bearing from the current position to the target
        a = geo.bearing_from_lonlat(position, target)
        a = np.deg2rad(a)

        # Get the displacement due to paddling towards the target
        dxy_paddle = speed * self.dt * np.array([-np.sin(a), np.cos(a)])

        # Calculate the displacement due to drift
        dxy_drift = self.from_drift(c, w).dxy

        self.dxy = dxy_drift + dxy_paddle

        return self

    def from_sailing(self, c: np.ndarray, w: np.ndarray, position: np.ndarray, target: np.ndarray):
        """Generate displacement due to sailing, reinforcing the wind speed contribution over the currents.

        Args:
            c (np.ndarray): Current velocity
            w (np.ndarray): Wind velocity
            position (np.ndarray): Current position coordinates
            target (np.ndarray): Destination position coordinates

        Raises:
            ValueError: Raised if the angle between the bearing and reference is a non-positive number

        Returns:
            Displacement: The Displacement instance
        """

        position = np.array(position)
        target   = np.array(target)

        # Calculate the drift due to the currents
        dxy_c = c * self.dt
        # print("displacement from c:", dxy_c)
        # print("current velocity:", np.linalg.norm(c))

        # Calculate the bearing
        bearing = target - position
        a = geo.bearing_from_lonlat(position, target)
        a = np.deg2rad(a)
        bearing = np.array([np.cos(a), np.sin(a)]).squeeze()

        bearing = bearing.squeeze()
        w   = w.squeeze()

        # Angle between bearing and reference vector
        b = np.arctan2(np.linalg.det([bearing, w]), np.dot(bearing, w))
        b = np.abs(np.rad2deg(b))

        w_abs = np.linalg.norm(w)
        # print("wind velocity:", np.linalg.norm(w))

        mt          = self.vessel.params["mt"]
        wf_0_40     = self.vessel.params["wf 0-40"]
        wf_40_80    = self.vessel.params["wf 40-80"]
        wf_80_100   = self.vessel.params["wf 80-100"]
        wf_100_110  = self.vessel.params["wf 100-110"]
        wf_110_120  = self.vessel.params["wf 110-120"]

        if b  <= 40:
            sailing_velocity = wf_0_40 
        elif b > 40 or b <= 80:
            sailing_velocity = wf_40_80 
        elif b > 80 or b <= 100:
            sailing_velocity = wf_80_100 
        elif b > 100 or b <= 110:
            sailing_velocity = wf_100_110 
        elif b > 110:
            sailing_velocity = wf_110_120 
        else:
            raise ValueError(f"Invalid angle b={b}")

        sailing_velocity *= w_abs

        if b <= mt:
            displacement = sailing_velocity * self.dt
        else:
            tacking = np.deg2rad(b-mt)
            displacement = np.cos(tacking)*sailing_velocity*self.dt

        dxy_sailing = displacement * np.array([-np.sin(a), np.cos(a)])


        self.dxy = dxy_sailing + dxy_c

        return self
 


    @staticmethod
    def knots_to_si(knots: float) -> float:
        """Converts knots to SI units (m/s)

        Args:
            knots (float): Speed in knots

        Returns:
            float: Speed in metres/second
        """

        return knots / 1.94

    @staticmethod
    def si_to_knots(si: float) -> float:
        """Converts SI units (m/s) to knots

        Args:
            si (float): Speed in m/s

        Returns:
            float: Speed in knots
        """

        return si * 1.94

    def with_uncertainty(self, sigma=1) -> np.ndarray:
        """Adds normal distributed noise to the current position.

        Args:
            sigma (float): The standard deviation of the added noise. Default: 1.

        Returns:
            Displacement: The Displacement object
        """

        self.dxy += np.random.normal(0, sigma, size=self.dxy.shape)
        
        return self

    def km(self):
        """Returns the displacement in kilometres, from metres.

        Returns:
            np.array: A numpy array with shape (2,) with the displacement in kilometres.
        """
        
        return self.dxy / 1e3

    def to_lonlat(self, dx: float, dy: float, longitude: float, latitude: float) -> Tuple[float, float]:
        """Convenience function to convert a displacement into longitude and latitude

        Args:
            dx (float): Displacement in x-axis
            dy (float): Displacement in y-axis
            longitude (float): Longitudinal displacement
            latitude (float): Latitudinal displacement

        Returns:
            Tuple[float, float]: A tuple of the longitude and latitude
        """

        return geo.lonlat_from_displacement(dx, dy, (longitude, latitude))
