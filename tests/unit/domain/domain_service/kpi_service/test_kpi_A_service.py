import math

import pytest
import shapely.geometry
import shapely.ops

from domain.domain_service.kpi_service.kpi_A_service import KPIASpatialCoverageService
from domain.entities_and_dataclass.domain_class import Stop, Zone
from domain.entities_and_dataclass.domain_dataclass import AggregatedItinerary, AggregatedLeg, Point


EARTH_RADIUS_M = 6_371_008.8


def _make_square_zone(zone_id: str, min_lat: float, min_lon: float, max_lat: float, max_lon: float) -> Zone:
    boundary = [
        Point(min_lat, min_lon),
        Point(min_lat, max_lon),
        Point(max_lat, max_lon),
        Point(max_lat, min_lon),
    ]
    centroid = Point((min_lat + max_lat) / 2.0, (min_lon + max_lon) / 2.0)
    return Zone(zone_id, boundary, centroid)


def _to_local_xy(point: Point, origin: Point):
    lat0_rad = math.radians(origin.lat)
    delta_lat_rad = math.radians(point.lat - origin.lat)
    delta_lon_rad = math.radians(point.lon - origin.lon)
    x = EARTH_RADIUS_M * delta_lon_rad * math.cos(lat0_rad)
    y = EARTH_RADIUS_M * delta_lat_rad
    return x, y


@pytest.fixture
def sample_data():
    zone_o = _make_square_zone("ZO", 0.0, 0.0, 0.03, 0.03)
    zone_d = _make_square_zone("ZD", 0.05, 0.05, 0.08, 0.08)

    stops = {
        "SO_CENTER": Stop("SO_CENTER", 0.015, 0.015),
        "SO_OVER_1": Stop("SO_OVER_1", 0.0150, 0.0150),
        "SO_OVER_2": Stop("SO_OVER_2", 0.0150, 0.0158),
        "SO_OUTSIDE": Stop("SO_OUTSIDE", 0.015, 0.0308),
        "SD_CENTER": Stop("SD_CENTER", 0.065, 0.065),
    }

    service = KPIASpatialCoverageService(
        zones=[zone_o, zone_d],
        stops=list(stops.values()),
        stop_coverage_radius_m=500.0,
    )
    return service, {"ZO": zone_o, "ZD": zone_d}, stops


def test_compute_basic_single_stop_returns_positive_coverage(sample_data):
    service, _, _ = sample_data
    agg_itinerary = AggregatedItinerary(
        legs=[AggregatedLeg("R1", {"SO_CENTER"}, {"SD_CENTER"})]
    )

    result = service.compute("ZO", "ZD", agg_itinerary)

    assert result["origin_coverage_ratio"] > 0.0
    assert result["destination_coverage_ratio"] > 0.0
    assert result["score_ratio"] > 0.0
    assert result["score_percent"] == pytest.approx(result["score_ratio"] * 100.0)


def test_compute_overlap_buffers_do_not_double_count_area(sample_data):
    service, zones, stops = sample_data
    agg_itinerary = AggregatedItinerary(
        legs=[AggregatedLeg("R1", {"SO_OVER_1", "SO_OVER_2"}, {"SD_CENTER"})]
    )

    result = service.compute("ZO", "ZD", agg_itinerary)

    zone_o = zones["ZO"]
    local_zone = shapely.geometry.Polygon(
        [_to_local_xy(p, zone_o.centroid) for p in zone_o.boundary]
    )

    buffers = [
        shapely.geometry.Point(*_to_local_xy(stops["SO_OVER_1"].coord, zone_o.centroid)).buffer(500.0),
        shapely.geometry.Point(*_to_local_xy(stops["SO_OVER_2"].coord, zone_o.centroid)).buffer(500.0),
    ]

    expected_union_ratio = (
        shapely.ops.unary_union(buffers).intersection(local_zone).area / local_zone.area
    )
    naive_sum_ratio = sum(buffer.intersection(local_zone).area for buffer in buffers) / local_zone.area

    assert result["origin_coverage_ratio"] == pytest.approx(expected_union_ratio, rel=1e-6)
    assert result["origin_coverage_ratio"] < naive_sum_ratio


def test_compute_stop_outside_zone_is_clipped_by_zone_boundary(sample_data):
    service, _, _ = sample_data
    agg_inside = AggregatedItinerary(
        legs=[AggregatedLeg("R1", {"SO_CENTER"}, {"SD_CENTER"})]
    )
    agg_outside = AggregatedItinerary(
        legs=[AggregatedLeg("R1", {"SO_OUTSIDE"}, {"SD_CENTER"})]
    )

    inside_result = service.compute("ZO", "ZD", agg_inside)
    outside_result = service.compute("ZO", "ZD", agg_outside)

    assert outside_result["origin_coverage_ratio"] > 0.0
    assert outside_result["origin_coverage_ratio"] < inside_result["origin_coverage_ratio"]


def test_compute_missing_valid_stops_returns_zero_for_that_side(sample_data):
    service, _, _ = sample_data

    agg_missing_origin = AggregatedItinerary(
        legs=[AggregatedLeg("R1", {"UNKNOWN_O"}, {"SD_CENTER"})]
    )
    agg_missing_destination = AggregatedItinerary(
        legs=[AggregatedLeg("R1", {"SO_CENTER"}, {"UNKNOWN_D"})]
    )
    agg_empty = AggregatedItinerary(legs=[])

    missing_origin_result = service.compute("ZO", "ZD", agg_missing_origin)
    missing_destination_result = service.compute("ZO", "ZD", agg_missing_destination)
    empty_result = service.compute("ZO", "ZD", agg_empty)

    assert missing_origin_result["origin_coverage_ratio"] == 0.0
    assert missing_origin_result["score_ratio"] == 0.0

    assert missing_destination_result["destination_coverage_ratio"] == 0.0
    assert missing_destination_result["score_ratio"] == 0.0

    assert empty_result["origin_coverage_ratio"] == 0.0
    assert empty_result["destination_coverage_ratio"] == 0.0
    assert empty_result["score_ratio"] == 0.0


def test_compute_raises_error_when_zone_id_not_found(sample_data):
    service, _, _ = sample_data
    agg_itinerary = AggregatedItinerary(
        legs=[AggregatedLeg("R1", {"SO_CENTER"}, {"SD_CENTER"})]
    )

    with pytest.raises(ValueError, match="Không tìm thấy zone_id"):
        service.compute("UNKNOWN_ZONE", "ZD", agg_itinerary)

    with pytest.raises(ValueError, match="Không tìm thấy zone_id"):
        service.compute("ZO", "UNKNOWN_ZONE", agg_itinerary)


def test_compute_score_ratio_is_product_of_origin_and_destination_ratios(sample_data):
    service, _, _ = sample_data
    agg_itinerary = AggregatedItinerary(
        legs=[AggregatedLeg("R1", {"SO_CENTER"}, {"SD_CENTER"})]
    )

    result = service.compute("ZO", "ZD", agg_itinerary)

    expected = result["origin_coverage_ratio"] * result["destination_coverage_ratio"]
    assert result["score_ratio"] == pytest.approx(expected, rel=1e-9)
    assert result["score_percent"] == pytest.approx(expected * 100.0, rel=1e-9)
