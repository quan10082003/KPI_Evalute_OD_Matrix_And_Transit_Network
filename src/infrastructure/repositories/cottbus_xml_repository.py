import xml.etree.ElementTree as ET
from typing import List, Tuple
from application.ports.base_repository import EvaluationDataRepository
from domain.entities_and_dataclass.domain_class import Stop, Route, Zone, ODPair
from domain.entities_and_dataclass.domain_dataclass import Direction, Point
from domain.domain_service.routing_service.core_engine import (
    DirectConnectionRoutingEngine,
    OneTransferRoutingEngine,
)
from domain.domain_service.routing_service.filter_strategy import (
    OneTransferOptimalFilter,
    OptimalWalkingDistanceFilter,
)

class CottbusXmlRepository(EvaluationDataRepository):
    """
    Repository Mock load dữ liệu trực tiếp từ các file XML của Cottbus.
    Các toạ độ x, y sẽ được chia tỷ lệ để giả lập toạ độ Lat/Lon nhằm không lỗi Geodesic Distance của geopy.
    - x / 10000 -> lon
    - y / 100000 -> lat
    """
    def __init__(
        self,
        schedule_path: str,
        plans_path: str,
        max_plans: int = 1000,
        zone_half_size_deg: float = 0.01,
    ):
        self.schedule_path = schedule_path
        self.plans_path = plans_path
        self.max_plans = max_plans
        if zone_half_size_deg <= 0:
            raise ValueError("zone_half_size_deg phải > 0")
        self.zone_half_size_deg = zone_half_size_deg
        # Reuse routing engines để pre-filter OD có kết nối ngay tại parsing.
        self._direct_engine = DirectConnectionRoutingEngine(filter_strategy=OptimalWalkingDistanceFilter())
        self._one_transfer_engine = OneTransferRoutingEngine(filter_strategy=OneTransferOptimalFilter())

    def load_network_and_demand(self) -> Tuple[List[Stop], List[Route], List[Zone], List[ODPair]]:
        print(f"[Repo] Bắt đầu đọc dữ liệu từ: {self.schedule_path} & {self.plans_path}")
        stops = self._parse_stops()
        routes = self._parse_routes(stops)
        zones, od_pairs = self._parse_zones_and_od_pairs()
        filtered_zones, filtered_od_pairs = self._filter_connected_od_pairs(zones, od_pairs, routes)
        print(
            f"[Repo] Đã tải xong: {len(stops)} Stops, {len(routes)} Routes, "
            f"{len(filtered_zones)} Zones, {len(filtered_od_pairs)} OD Pairs (connected-only)."
        )
        return stops, routes, filtered_zones, filtered_od_pairs
        
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
            
            # Nới zone thành hình vuông quanh centroid để tăng khả năng chạm stop thực tế.
            half = self.zone_half_size_deg
            zone_o = Zone(
                id=f"Z{zone_id_counter}",
                boundary=[
                    Point(lat_o - half, lon_o - half),
                    Point(lat_o - half, lon_o + half),
                    Point(lat_o + half, lon_o + half),
                    Point(lat_o + half, lon_o - half),
                ],
                centroid=Point(lat_o, lon_o),
            )
            zone_id_counter += 1
            zone_d = Zone(
                id=f"Z{zone_id_counter}",
                boundary=[
                    Point(lat_d - half, lon_d - half),
                    Point(lat_d - half, lon_d + half),
                    Point(lat_d + half, lon_d + half),
                    Point(lat_d + half, lon_d - half),
                ],
                centroid=Point(lat_d, lon_d),
            )
            zone_id_counter += 1
            
            zones.extend([zone_o, zone_d])
            od_pairs.append(ODPair(id=f"OD_{person.get('id')}", origin_area=zone_o, destination_area=zone_d, travel_demand=1))
            
            count += 1

        return zones, od_pairs

    def _filter_connected_od_pairs(
        self,
        zones: List[Zone],
        od_pairs: List[ODPair],
        routes: List[Route],
    ) -> Tuple[List[Zone], List[ODPair]]:
        connected_od_pairs: List[ODPair] = []
        connected_zone_map = {}

        for od_pair in od_pairs:
            if self._is_od_connected(od_pair, routes):
                connected_od_pairs.append(od_pair)
                connected_zone_map[od_pair.origin_area.id] = od_pair.origin_area
                connected_zone_map[od_pair.destination_area.id] = od_pair.destination_area

        return list(connected_zone_map.values()), connected_od_pairs

    def _is_od_connected(self, od_pair: ODPair, routes: List[Route]) -> bool:
        aggregated_0 = self._direct_engine._find_aggregated_itineraries(od_pair=od_pair, routes=routes)
        if aggregated_0:
            return True

        aggregated_1 = self._one_transfer_engine._find_aggregated_itineraries(od_pair=od_pair, routes=routes)
        return len(aggregated_1) > 0
