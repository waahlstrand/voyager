
from . import geo, search, chart
import numpy as np
from typing import *

class Vessel:

    def __init__(self, x, 
                       y, 
                       craft=None, 
                       mode="drift", 
                       route = None,
                       destination = None,
                       launch_date = None,
                       speed = 0,
                       params = {}
                       ):

        self.craft = craft
        self.mode = mode
        self.launch_date = launch_date
        self.destination = destination
        self.x = x
        self.y = y
        self.speed = speed

        # Initialize parameters to save
        self.trajectory = [[self.x, self.y]]
        self.distance = 0
        self.mean_speed = 0

        self.route  = route
        self.route_taken = [[float(x),float(y)] for x,y in self.route]
        self.target = self.route.pop()

        # Read the features of the vessel
        self.params = params


    @classmethod
    def from_position(cls, point: Tuple[float, float], chart: chart.Chart = None, destination: Tuple[float, float] = None, interval: int =5, **kwargs):
        """Creates a vessel from a start position, using a pre-supplied Chart object and destination.
        The chart and interval parameters are used to create a route from the start position and the destination, the interval
        deciding the number of milestones along the way.

        Args:
            point (Tuple[float, float]): Start position
            chart (chart.Chart, optional): A Chart object. Defaults to None.
            destination (Tuple[float, float], optional): Destination position. Defaults to None.
            interval (int, optional): Interval to create route targets. Defaults to 5.

        Raises:
            RuntimeError: Raised if there is no possible route between start and end

        Returns:
            Vessel: A Vessel instance
        """
        

        x, y = point

        if (destination is not None) and (chart is not None):

            # Find the closest latlon to the start and destination
            i = geo.closest_coordinate_index(chart.longitudes, x)
            j = geo.closest_coordinate_index(chart.latitudes, y)

            i_goal = geo.closest_coordinate_index(chart.longitudes, destination[0])
            j_goal = geo.closest_coordinate_index(chart.latitudes, destination[1]) 

            # Find the optimal route to the target
            astar = search.Astar(chart.grid)
            came_from, cost_so_far = astar.search(start=(j, i), goal=(j_goal, i_goal))

            # Chart the route
            try:
                route = astar.reconstruct_path(came_from, start=(j, i), goal=(j_goal, i_goal))
                route = [(chart.longitudes[i], chart.latitudes[j]) for j, i in route]
                route = [route[0], *route[1:-2:interval], route[-1]]
                route.reverse()

            except Exception as e:
                raise RuntimeError("No possible route") from e


            # Create a vessel
            vessel = cls(x, y, route=route, destination=destination, **kwargs)

        else:

            # Create a vessel without a route
            vessel = cls(x, y, destination=destination, **kwargs)

        return vessel


    @classmethod
    def from_positions(cls, points: List[Tuple[float, float]], chart: chart.Chart = None, destination: Tuple[float, float] = None, interval: int = 5, **kwargs) -> List:
        """Generates a list of vessels from multiple positions.
            The chart and interval parameters are used to create a route from the start position and the destination, the interval
            deciding the number of milestones along the way.

        Args:
            points (List[Tuple[float, float]]): List of positions
            chart (chart.Chart, optional): A chart object. Defaults to None.
            destination (Tuple[float, float], optional): Destination coordinates in WGS84. Defaults to None.
            interval (int, optional): Interval to create route targets. Defaults to 5.

        Returns:
            List: List of Vessel instances
        """
        vessels = []
        for point in points:

            vessel = cls.from_position(point, chart, destination, interval, kwargs)

            vessels.append(vessel)


        return vessels

    def update_position(self, x: float, y: float):
        """Updates position and records it to the trajectory

        Args:
            x (float): longitudinal position
            y (float): latitudinal position
        """
            
        self.x = x
        self.y = y

        # Record position to trajectory
        self.trajectory.append([x, y])

        return self

    def update_distance(self, dx: float, dy: float):
        """Updates the cumulative distance travelled for the trajectory

        Args:
            dx (float): longitudinal displacement (km)
            dy (float): latitudinal displacement (km)
        """

        self.distance += np.linalg.norm(np.vstack((dx.squeeze(), dy.squeeze()))).squeeze().item()

        return self

    def update_mean_speed(self, dt: float):
        """Updates the total mean speed of the trajectory
        from the total distance travelled.

        Args:
            dt (float): time step during the simulation (s)
        """

        N_SECONDS_PER_HOUR = 3600
        self.mean_speed = self.distance / (len(self.trajectory) * dt / N_SECONDS_PER_HOUR) # km/h

        return self

    def has_arrived(self, longitude: float, latitude: float, target_tol: float) -> bool:
        """Calculates whether the vessel has arrived to its destination with in a certain tolerance.

        Args:
            longitude (float): Longutide
            latitude (float): Latitude
            target_tol (float): Distance tolerance away from the target destination

        Returns:
            bool: Whether the vessel has arrived or not
        """

        is_close = geo.distance((longitude, latitude), self.target) <= target_tol

        if is_close:
            if len(self.route) > 0:
                self.target = self.route.pop()
            else:
                return True
        else:
            return False

    def to_dict(self):

        return {
            "trajectory": self.trajectory,
            "distance": self.distance,
            "route": self.route_taken,
            "mean_speed": self.mean_speed,
            "destination": self.destination
        }

    def to_GeoJSON(self, start_date: str, stop_date: str, dt: float) -> Dict:
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
                    "coordinates": self.trajectory,

                },
                "properties": {
                    "start_date": start_date,
                    "stop_date": stop_date,
                    "timestep": dt,
                    "distance": self.distance,
                    "mean_speed": self.mean_speed,
                    "destination": self.destination,
                    "route": self.route_taken
                }          
            }
        )

        return format_dict