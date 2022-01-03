
from . import geo, search
import numpy as np
import yaml

class Vessel:

    def __init__(self, x, 
                       y, 
                       craft=None, 
                       mode="drift", 
                       route = None,
                       destination = None,
                       launch_date = None,
                       speed = 0,
                       vessel_config='configs/vessels.yml'):

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
        with open(vessel_config, 'r') as file:
            config = yaml.load(file, Loader=yaml.FullLoader)

        self.params = config[self.mode][self.craft]


    @classmethod
    def from_position(cls, point, chart=None, destination=None, interval=5, **kwargs):

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

            except:
                print("No possible route.")
                return None


            # Create a vessel
            vessel = cls(x, y, route=route, destination=destination, **kwargs)

        else:

            # Create a vessel without a route
            vessel = cls(x, y, destination=destination, **kwargs)

        return vessel


    @classmethod
    def from_positions(cls, points, chart=None, destination=None, interval=5, **kwargs):
        
        vessels = []
        for point in points:

            vessel = cls.from_position(point, chart, destination, interval, kwargs)

            vessels.append(vessel)


        return vessels

    def update_position(self, x, y):
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

    def update_distance(self, dx, dy):
        """Updates the cumulative distance travelled for the trajectory

        Args:
            dx (float): longitudinal displacement (km)
            dy (float): latitudinal displacement (km)
        """

        self.distance += np.linalg.norm(np.vstack((dx.squeeze(), dy.squeeze()))).squeeze().item()

        return self

    def update_mean_speed(self, dt):
        """Updates the total mean speed of the trajectory
        from the total distance travelled.

        Args:
            dt (float): time step during the simulation (s)
        """

        N_SECONDS_PER_HOUR = 3600
        self.mean_speed = self.distance / (len(self.trajectory) * dt / N_SECONDS_PER_HOUR) # km/h

        return self

    def has_arrived(self, longitude, latitude, target_tol):

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