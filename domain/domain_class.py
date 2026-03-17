from enum import Enum
from typing import List, Set
from dataclasses import dataclass
from domain.domain_dataclass import Point, Direction, Leg, Itinerary

class Stop:
    def __init__ (self, id:str, lat:float, lon:float):
        self.id = id
        self.coord = Point(lat, lon)

class Route:
    def __init__ (self, id:str, direction:Direction, shape: List(Point), stops_seq: List(Stop)):
        self.id : str = id
        self.direction : Direction = direction
        self.shape : List(Point) = shape
        self.stops_seq : List(Stop) = stops_seq

    def get_closest_stop_to_point(self, point: Point) -> Stop:
        """
        Tìm stop gần nhất của route đến 1 point
        """
        min_distance = float('inf')
        closest_stop = None
        for stop in self.stops_seq:
            distance = point.distance_to(stop.coord)
            if distance < min_distance:
                min_distance = distance
                closest_stop = stop     

        return closest_stop

    def get_distance_between_stops(self, start_stop: Stop, end_stop: Stop) -> float:
        pass

    def get_cricuity_index_between_2_stops(self, start_stop: Stop, end_stop: Stop) -> float:
        pass
    
    def get_share_stops_with_other_route(self, other_route: Route) -> List[Stop]:
        my_stop_ids = {stop.id for stop in self.stops_seq}
        other_stop_ids = {stop.id for stop in other_route.stops_seq}
        
        # Phép & (intersection) của Set trong Python
        shared_ids = my_stop_ids & other_stop_ids 
    
        return [stop for stop in self.stops_seq if stop.id in shared_ids]

class Zone:
    def __init__(self, id:str, boundary: List[Point], centroid: Point):
        self.id = id
        self.boundary = boundary
        self.centroid = centroid

    def is_point_in_zone(self, P: Point) -> bool:
        """
        Kiểm tra xem điểm P có nằm trong boundary của Zone hay không
        dựa trên thuật toán Ray Casting.
        """
        if not self.boundary or len(self.boundary) < 3:
            return False
        x, y = P.lon, P.lat
        is_inside = False
        n = len(self.boundary)
        j = n - 1  
        for i in range(n):
            xi, yi = self.boundary[i].lon, self.boundary[i].lat
            xj, yj = self.boundary[j].lon, self.boundary[j].lat

            if (yi > y) != (yj > y):
                x_intersect = (xj - xi) * (y - yi) / (yj - yi) + xi
                if x < x_intersect:
                    is_inside = not is_inside
            j = i

        return is_inside
        
class ODPair:
    def __init__(self, id:str, origin_area: Zone, destination_area: Zone, travel_demand: int):
        self.id = id
        self.origin_area = origin_area
        self.destination_area = destination_area
        self.travel_demand = travel_demand







