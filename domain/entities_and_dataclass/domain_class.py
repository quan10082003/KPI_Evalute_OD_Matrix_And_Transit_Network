from enum import Enum
from typing import List, Set
from dataclasses import dataclass
import shapely.geometry
from domain.entities_and_dataclass.domain_dataclass import Point, Direction, Leg, Itinerary

class Stop:
    def __init__ (self, id:str, lat:float, lon:float):
        self.id = id
        self.coord = Point(lat, lon)

class Route:
    def __init__ (self, id:str, direction:Direction, shape: List[Point], stops_seq: List[Stop]):
        self.id : str = id
        self.direction : Direction = direction
        self.shape : List[Point] = shape
        self.stops_seq : List[Stop] = stops_seq
        
        # Khởi tạo đối tượng hình học LineString từ shapely
        if self.shape and len(self.shape) > 1:
            self.linestring = shapely.geometry.LineString([p.as_shapely for p in self.shape])
        else:
            self.linestring = None

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
        if not self.linestring:
            return 0.0
            
        # Tìm hình chiếu của stop lên tuyến đường (ở khoảng cách nào trên toàn tuyến)
        dist_start = self.linestring.project(start_stop.coord.as_shapely)
        dist_end = self.linestring.project(end_stop.coord.as_shapely)
        
        min_dist = min(dist_start, dist_end)
        max_dist = max(dist_start, dist_end)
        
        # Lấy đoạn phụ (sub-line) nằm giữa 2 hình chiếu dọc theo hành trình
        from shapely.ops import substring
        sub_line = substring(self.linestring, min_dist, max_dist)
        
        # Nếu cắt không thành công hoặc chỉ là 1 điểm
        if not sub_line or sub_line.is_empty or sub_line.geom_type == 'Point':
            return 0.0
            
        import geopy.distance
        real_distance = 0.0
        coords = list(sub_line.coords)
        for i in range(len(coords) - 1):
            p1 = (coords[i][1], coords[i][0]) # (lat, lon)
            p2 = (coords[i+1][1], coords[i+1][0])
            real_distance += geopy.distance.geodesic(p1, p2).meters
            
        return real_distance

    def get_cricuity_index_between_2_stops(self, start_stop: Stop, end_stop: Stop) -> float:
        route_dist = self.get_distance_between_stops(start_stop, end_stop)
        straight_dist = start_stop.coord.distance_to(end_stop.coord)
        if straight_dist == 0:
            return 1.0 # Tránh lỗi chia cho 0
        return route_dist / straight_dist
    
    def get_share_stops_with_other_route(self, other_route: 'Route') -> List[Stop]:
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
        
        # Khởi tạo đối tượng hình học Polygon từ shapely
        if self.boundary and len(self.boundary) >= 3:
            self.polygon = shapely.geometry.Polygon([p.as_shapely for p in self.boundary])
        else:
            self.polygon = None

    def is_point_in_zone(self, P: Point) -> bool:
        """
        Kiểm tra xem điểm P có nằm trong boundary của Zone hay không.
        Sử dụng library shapely C++ siêu việt thay cho Ray Casting bằng Python thủ công.
        """
        if not self.polygon:
            return False
            
        return self.polygon.contains(P.as_shapely)
        
class ODPair:
    def __init__(self, id:str, origin_area: Zone, destination_area: Zone, travel_demand: int):
        self.id = id
        self.origin_area = origin_area
        self.destination_area = destination_area
        self.travel_demand = travel_demand
