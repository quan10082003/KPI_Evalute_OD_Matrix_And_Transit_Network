import pytest
from domain.entities_and_dataclass.domain_dataclass import Point, Direction, AggregatedLeg, AggregatedItinerary
from domain.entities_and_dataclass.domain_class import Stop, Route, Zone, ODPair
from domain.domain_service.routing_service.core_engine import DirectConnectionRoutingEngine
from domain.domain_service.routing_service.filter_strategy import OptimalWalkingDistanceFilter

def test_direct_connection_engine_find_aggregated():
    engine = DirectConnectionRoutingEngine(filter_strategy=OptimalWalkingDistanceFilter())
    
    # Setup basic zones with real boundaries to bypass Polygon Guard Clause
    z_origin_boundary = [Point(-1,-1), Point(-1, 5), Point(5, 5), Point(5, -1)]
    z_origin = Zone("Z1", z_origin_boundary, Point(0, 0))
    
    z_dest_boundary = [Point(6,6), Point(6, 15), Point(15, 15), Point(15, 6)]
    z_dest = Zone("Z2", z_dest_boundary, Point(10, 10))
    
    od = ODPair("OD1", z_origin, z_dest, 100)
    
    s1 = Stop("S1", 0, 0) # Thuộc Origin
    s2 = Stop("S2", 10, 10) # Thuộc Dest
    
    # R1 đi từ Z1 đến Z2 (Hợp lệ)
    r1 = Route("R1", Direction.INBOUND, [Point(0,0), Point(10,10)], [s1, s2])
    # R2 đi ngược chiều mạng (từ Z2 về Z1) -> Buộc phải bị LOẠI BỎ thông qua thuật toán idx array
    r2 = Route("R2", Direction.INBOUND, [Point(10,10), Point(0,0)], [s2, s1])
    
    # Inject spatial mock behavior to class logic
    aggs = engine._find_aggregated_itineraries(od, [r1, r2])
    
    # Nó chỉ chấp nhận R1 đi thuận chiều
    assert len(aggs) == 1
    assert aggs[0].legs[0].route_ref_id == "R1"
    assert "S1" in aggs[0].legs[0].possible_board_stop_ids
    assert "S2" in aggs[0].legs[0].possible_alight_stop_ids
