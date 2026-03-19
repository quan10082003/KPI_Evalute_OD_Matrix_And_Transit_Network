import math
from typing import Dict, Iterable, List

import shapely.geometry
import shapely.ops

from domain.entities_and_dataclass.domain_class import Stop, Zone
from domain.entities_and_dataclass.domain_dataclass import AggregatedItinerary, Point


class KPIASpatialCoverageService:
    """
    KPI A - Spatial Coverage cho AggregatedItinerary.
    """

    EARTH_RADIUS_M = 6_371_008.8

    def __init__(
        self,
        zones: List[Zone],
        stops: List[Stop],
        stop_coverage_radius_m: float = 500.0,
    ):
        if stop_coverage_radius_m <= 0:
            raise ValueError("stop_coverage_radius_m phải > 0")

        self.stop_coverage_radius_m = float(stop_coverage_radius_m)
        self.zone_map: Dict[str, Zone] = {zone.id: zone for zone in zones}
        self.stop_map: Dict[str, Stop] = self._build_stop_lookup(stops)

    def compute(
        self,
        origin_zone_id: str,
        destination_zone_id: str,
        aggregated_itinerary: AggregatedItinerary,
    ) -> dict:
        origin_zone = self._get_zone_or_raise(origin_zone_id)
        destination_zone = self._get_zone_or_raise(destination_zone_id)

        origin_stops = self._resolve_stops(aggregated_itinerary.get_origin_stops_id)
        destination_stops = self._resolve_stops(aggregated_itinerary.get_destination_stops_id)

        origin_coverage_ratio = self._calculate_zone_coverage_ratio(origin_zone, origin_stops)
        destination_coverage_ratio = self._calculate_zone_coverage_ratio(destination_zone, destination_stops)

        score_ratio = self._clamp_0_1(origin_coverage_ratio * destination_coverage_ratio)

        return {
            "score_percent": score_ratio * 100.0,
            "score_ratio": score_ratio,
            "origin_coverage_percent": origin_coverage_ratio * 100.0,
            "origin_coverage_ratio": origin_coverage_ratio,
            "destination_coverage_percent": destination_coverage_ratio * 100.0,
            "destination_coverage_ratio": destination_coverage_ratio,
            "origin_zone_id": origin_zone_id,
            "destination_zone_id": destination_zone_id,
            "radius_m": self.stop_coverage_radius_m,
            "origin_stop_count": len(origin_stops),
            "destination_stop_count": len(destination_stops),
        }

    def _build_stop_lookup(self, stops: List[Stop]) -> Dict[str, Stop]:
        lookup: Dict[str, Stop] = {}
        for stop in stops:
            if stop.id not in lookup:
                lookup[stop.id] = stop
        return lookup

    def _get_zone_or_raise(self, zone_id: str) -> Zone:
        zone = self.zone_map.get(zone_id)
        if zone is None:
            raise ValueError(f"Không tìm thấy zone_id: {zone_id}")
        return zone

    def _resolve_stops(self, stop_ids) -> List[Stop]:
        return [self.stop_map[stop_id] for stop_id in stop_ids if stop_id in self.stop_map]

    def _calculate_zone_coverage_ratio(self, zone: Zone, stops: Iterable[Stop]) -> float:
        local_zone_polygon = self._build_local_zone_polygon(zone)
        if local_zone_polygon.is_empty:
            return 0.0

        if not local_zone_polygon.is_valid:
            local_zone_polygon = local_zone_polygon.buffer(0)

        zone_area = local_zone_polygon.area
        if zone_area <= 0:
            return 0.0

        stop_buffers = [
            self._to_local_point(stop.coord, zone.centroid).buffer(self.stop_coverage_radius_m)
            for stop in stops
        ]
        if not stop_buffers:
            return 0.0

        covered_by_stops = shapely.ops.unary_union(stop_buffers)
        if covered_by_stops.is_empty:
            return 0.0

        covered_inside_zone = covered_by_stops.intersection(local_zone_polygon)
        if covered_inside_zone.is_empty:
            return 0.0

        return self._clamp_0_1(covered_inside_zone.area / zone_area)

    def _build_local_zone_polygon(self, zone: Zone):
        if not zone.boundary or len(zone.boundary) < 3:
            return shapely.geometry.Polygon()

        local_boundary = [self._to_local_xy(point, zone.centroid) for point in zone.boundary]
        return shapely.geometry.Polygon(local_boundary)

    def _to_local_point(self, point: Point, origin: Point):
        x, y = self._to_local_xy(point, origin)
        return shapely.geometry.Point(x, y)

    def _to_local_xy(self, point: Point, origin: Point):
        lat0_rad = math.radians(origin.lat)
        delta_lat_rad = math.radians(point.lat - origin.lat)
        delta_lon_rad = math.radians(point.lon - origin.lon)

        x = self.EARTH_RADIUS_M * delta_lon_rad * math.cos(lat0_rad)
        y = self.EARTH_RADIUS_M * delta_lat_rad
        return x, y

    def _clamp_0_1(self, value: float) -> float:
        return max(0.0, min(1.0, value))
