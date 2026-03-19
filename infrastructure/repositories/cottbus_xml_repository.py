import xml.etree.ElementTree as ET
from typing import List, Tuple, Dict
from application.base_repository import EvaluationDataRepository
from domain.entities_and_dataclass.domain_class import Stop, Route, Zone, ODPair
from domain.entities_and_dataclass.domain_dataclass import Direction, Point

class CottbusXmlRepository(EvaluationDataRepository):
    """
    Repository Mock load dữ liệu trực tiếp từ các file XML của Cottbus.
    Các toạ độ x, y sẽ được chia tỷ lệ để giả lập toạ độ Lat/Lon nhằm không lỗi Geodesic Distance của geopy.
    - x / 10000 -> lon
    - y / 100000 -> lat
    """
    def __init__(self, schedule_path: str, plans_path: str, max_plans: int = 1000):
        self.schedule_path = schedule_path
        self.plans_path = plans_path
        self.max_plans = max_plans

    def load_network_and_demand(self) -> Tuple[List[Stop], List[Route], List[Zone], List[ODPair]]:
        print(f"[Repo] Bắt đầu đọc dữ liệu từ: {self.schedule_path} & {self.plans_path}")
        stops = self._parse_stops()
        routes = self._parse_routes(stops)
        zones, od_pairs = self._parse_zones_and_od_pairs()
        print(f"[Repo] Đã tải xong: {len(stops)} Stops, {len(routes)} Routes, {len(zones)} Zones, {len(od_pairs)} OD Pairs.")
        return stops, routes, zones, od_pairs
        
    def _parse_stops(self) -> List[Stop]:
        tree = ET.parse(self.schedule_path)
        root = tree.getroot()
        stops = []
        for stop_elem in root.findall('./transitStops/stopFacility'):
            s_id = stop_elem.get('id')
            x = float(stop_elem.get('x', 0))
            y = float(stop_elem.get('y', 0))
            # Scale coordinates into valid geopy lat/lon ranges POC
            lon = x / 10000.0
            lat = y / 100000.0
            stops.append(Stop(id=s_id, lat=lat, lon=lon))
        return stops

    def _parse_routes(self, stops: List[Stop]) -> List[Route]:
        stop_map = {s.id: s for s in stops}
        tree = ET.parse(self.schedule_path)
        root = tree.getroot()
        routes = []

        for line in root.findall('./transitLine'):
            line_id = line.get('id')
            for route_elem in line.findall('./transitRoute'):
                route_id = route_elem.get('id')
                dir_enum = Direction.INBOUND if "in" in route_id else Direction.OUTBOUND
                
                route_stops = []
                for profile in route_elem.findall('./routeProfile/stop'):
                    refId = profile.get('refId')
                    if refId in stop_map:
                        route_stops.append(stop_map[refId])
                
                # Shape is approximated by sequence of stop coords in POC
                shape_points = [s.coord for s in route_stops]
                routes.append(Route(id=f"{line_id}_{route_id}", direction=dir_enum, shape=shape_points, stops_seq=route_stops))
                
        return routes

    def _parse_zones_and_od_pairs(self) -> Tuple[List[Zone], List[ODPair]]:
        # Giả lập: Xây dựng grid-based Zones tĩnh 10x10.
        # Ở POC này, ta tạo các vùng 'Zone' mikcro bằng cách convert trực tiếp act 'home'/'work' của mỗi user thành một point zone.
        tree = ET.parse(self.plans_path)
        root = tree.getroot()
        
        zones = []
        od_pairs = []
        count = 0
        zone_id_counter = 1
        
        for person in root.findall('.//person'):
            if count >= self.max_plans:
                break
                
            plan = person.find("./plan[@selected='yes']")
            if plan is None: continue
            
            acts = plan.findall('act')
            if len(acts) < 2: continue
            
            # Simple assumption: first act is origin, second or max distance is destination
            act_o = acts[0]
            act_d = acts[1]
            
            x_o, y_o = float(act_o.get('x', 0)), float(act_o.get('y', 0))
            x_d, y_d = float(act_d.get('x', 0)), float(act_d.get('y', 0))
            
            lon_o, lat_o = x_o / 10000.0, y_o / 100000.0
            lon_d, lat_d = x_d / 10000.0, y_d / 100000.0
            
            # Create mock microscopic zones
            zone_o = Zone(id=f"Z{zone_id_counter}", boundary=[Point(lat_o, lon_o), Point(lat_o+0.001, lon_o), Point(lat_o, lon_o+0.001)], centroid=Point(lat_o, lon_o))
            zone_id_counter += 1
            zone_d = Zone(id=f"Z{zone_id_counter}", boundary=[Point(lat_d, lon_d), Point(lat_d+0.001, lon_d), Point(lat_d, lon_d+0.001)], centroid=Point(lat_d, lon_d))
            zone_id_counter += 1
            
            zones.extend([zone_o, zone_d])
            od_pairs.append(ODPair(id=f"OD_{person.get('id')}", origin_area=zone_o, destination_area=zone_d, travel_demand=1))
            
            count += 1

        return zones, od_pairs
