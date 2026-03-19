import pytest
from domain.entities_and_dataclass.domain_dataclass import AggregatedItinerary, AggregatedLeg, Leg, Itinerary, Point
from domain.entities_and_dataclass.domain_class import Stop, Route, Direction
from domain.domain_service.kpi_service.kpi_service import calculate_transfer_rate_kpi, calculate_cricuity_index_kpi

def test_calculate_transfer_rate_kpi():
    leg1 = AggregatedLeg("R1", {"S1"}, {"S2"})
    leg2 = AggregatedLeg("R2", {"S2"}, {"S3"})
    
    # 0 transfer
    agg_iti_0 = AggregatedItinerary([leg1])
    res_0 = calculate_transfer_rate_kpi(agg_iti_0)
    assert res_0["score"] == "0"
    
    # 1 transfer
    agg_iti_1 = AggregatedItinerary([leg1, leg2])
    res_1 = calculate_transfer_rate_kpi(agg_iti_1)
    assert res_1["score"] == "1"

def test_calculate_cricuity_index_kpi():
    s1 = Stop("S1", 0.0, 0.0)
    s2 = Stop("S2", 0.1, 0.1)
    
    route1 = Route("R1", Direction.INBOUND, [Point(0.0, 0.0), Point(0.1, 0.0), Point(0.1, 0.1)], [s1, s2])
    
    iti_valid = Itinerary([Leg("R1", "S1", "S2")])
    res_valid = calculate_cricuity_index_kpi(iti_valid, [route1])
    
    assert res_valid["score"] >= 1.0
    assert res_valid["route_sequence"] == ["R1"]
    assert res_valid["stop_sequence"] == ["S1", "S2"]
    
    iti_empty = Itinerary([])
    res_empty = calculate_cricuity_index_kpi(iti_empty, [route1])
    assert res_empty["score"] == "Not valid or >1"
