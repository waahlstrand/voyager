from typing import Dict, Tuple, List, Iterator, Optional, TypeVar
import heapq
import numpy as np
import cv2

T = TypeVar('T')
Position = Tuple[int, int]

def heuristic(a: Position, b: Position) -> float:
    (x1, y1) = a
    (x2, y2) = b
    return abs(x1 - x2) + abs(y1 - y2)

class Grid:
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.walls: List[Position] = []
    
    def in_bounds(self, id: Position) -> bool:
        (x, y) = id
        return 0 <= x < self.width and 0 <= y < self.height
    
    def passable(self, id: Position) -> bool:
        return id not in self.walls
    
    def neighbors(self, id: Position) -> Iterator[Position]:
        (x, y) = id
        # neighbors = [(x+1, y), (x-1, y), (x, y-1), (x, y+1)] # E W N S
        neighbors = [(x+1, y), (x-1, y), (x, y+1), (x, y-1), (x+1, y+1), (x-1, y-1), (x+1, y-1), (x-1, y+1)]
        # see "Ugly paths" section for an explanation:
        if (x + y) % 2 == 0: neighbors.reverse() # S N W E
        results = filter(self.in_bounds, neighbors)
        results = filter(self.passable, results)
        return results

class WeightedGrid(Grid):
    def __init__(self, width: int, height: int):
        super().__init__(width, height)
        self.weights: Dict[Position, float] = {}
        self.weighted_mask = None
    
    def cost(self, from_node: Position, to_node: Position) -> float:
        return self.weights.get(to_node, 1)

    @classmethod
    def from_map(cls, map, **kwargs):

        map = map.values

        mask = np.isnan(map).astype(np.float)
        grid = cls(*mask.shape)

        grid.weighted_mask = cls.create_shoreline_contour(mask, **kwargs)

        grid.weights = cls.mask_to_graph(grid.weighted_mask)
        grid.walls = [(x[0], x[1]) for x in np.argwhere(np.isnan(map))]

        return grid

    @staticmethod
    def create_shoreline_contour(mask, weights=[5, 0.5], iterations=[1, 4], kernel_size=3):

        kernel = np.ones((kernel_size, kernel_size), np.uint8)
        weighted_mask = np.ones(mask.shape)

        for weight, iters in zip(weights, iterations):

            # Calculate shorelines at different distance
            shoreline = cv2.dilate(mask, kernel, iterations=iters)

            # Start at zero and add shorelines with weights
            weighted_mask[shoreline.astype(np.bool)] = weight

        # immediate = cv2.dilate(mask, kernel, iterations=iterations[0]) 
        # distant   = cv2.dilate(mask, kernel, iterations=iterations[1]) 

        # # Start at zero and add shorelines with weights

        # weighted_mask[distant.astype(np.bool)] = weights[1]
        # weighted_mask[immediate.astype(np.bool)] = weights[0]
        weighted_mask[mask.astype(np.bool)] = np.nan    

        return weighted_mask

    @staticmethod
    def mask_to_graph(mask):

        return {index: value for index, value in np.ndenumerate(mask) if not np.isnan(value)}


class PriorityQueue:
    def __init__(self):
        self.elements: List[Tuple[float, T]] = []
    
    def empty(self) -> bool:
        return not self.elements
    
    def put(self, item: T, priority: float):
        heapq.heappush(self.elements, (priority, item))
    
    def get(self) -> T:
        return heapq.heappop(self.elements)[1]

class Astar:
    # Algorithm idea:
    # A traversal graph of the map is the set of indices on the mask of the map.
    # Distance is calculated per 

    def __init__(self, graph: WeightedGrid) -> None:
        
        self.graph  = graph

    def search(self, start: Position, goal: Position):

        frontier = PriorityQueue()
        frontier.put(start, 0)
        came_from: Dict[Position, Optional[Position]] = {}
        cost_so_far: Dict[Position, float] = {}
        came_from[start] = None
        cost_so_far[start] = 0
        
        while not frontier.empty():
            current: Position = frontier.get()
            
            if current == goal:
                break
            
            for next in self.graph.neighbors(current):
                new_cost = cost_so_far[current] + self.graph.cost(current, next)
                if next not in cost_so_far or new_cost < cost_so_far[next]:
                    cost_so_far[next] = new_cost
                    priority = new_cost + heuristic(next, goal)
                    frontier.put(next, priority)
                    came_from[next] = current
        
        return came_from, cost_so_far



    def reconstruct_path(self, came_from: Dict[Position, Position], 
                               start: Position, 
                               goal: Position) -> List[Position]:

        current: Position = goal
        path = []
        while current != start:
            
            path.append(current)

            current = came_from[current]

        path.reverse()
        return path

