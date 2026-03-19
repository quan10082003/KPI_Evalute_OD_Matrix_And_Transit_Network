import pytest
from domain.entities_and_dataclass.domain_dataclass import Point, Direction, Leg, Itinerary
from domain.entities_and_dataclass.domain_class import Stop, Route, Zone
from domain.domain_service.spatial_service import (
    find_all_routes_pass_through_zone,
    find_all_stops_on_a_route_located_in_a_certain_zone,
    find_cricuity_index_of_a_itinerary
)

def test_find_all_routes_pass_through_zone():
    boundary = [Point(0.0, 0.0), Point(0.0, 1.0), Point(1.0, 1.0), Point(1.0, 0.0)]
    z = Zone("Z1", boundary, Point(0.5, 0.5))
    
    # Tuyến đi thẳng qua zone nhưng ko có stop nào qua zone
    r1 = Route("R1", Direction.INBOUND, [Point(-0.5, 0.5), Point(1.5, 0.5)], [])
    # Tuyến ở tuốt bên ngoài
    r2 = Route("R2", Direction.INBOUND, [Point(2.0, 2.0), Point(3.0, 3.0)], [])
    #Tuyến đi quan zone và có stop trong zone
    r3 = Route("R3",Direction.INBOUND, [Point(-0.5,-0.5), Point(0.5,0.5), Point(1.5,1.5)], [Stop("S1",0.5,0.5)])
    
    passing = find_all_routes_pass_through_zone(z, [r1, r2, r3])
    assert len(passing) == 1
    assert passing[0].id == "R3"

def test_find_all_stops_on_a_route_located_in_a_certain_zone():
    boundary = [Point(0.0, 0.0), Point(0.0, 1.0), Point(1.0, 1.0), Point(1.0, 0.0)]
    z = Zone("Z1", boundary, Point(0.5, 0.5))
    
    s_in = Stop("S1", 0.5, 0.5)
    s_out = Stop("S2", 2.0, 2.0)
    
    r = Route("R1", Direction.INBOUND, [Point(-2, -2), Point(-2, 1.5), Point(-0.5, 0.5), Point(1.5, 0.5)], [s_in, s_out])
    
    passing_stops = find_all_stops_on_a_route_located_in_a_certain_zone(z, r)
    assert len(passing_stops) == 1
    assert passing_stops[0].id == "S1"

def test_find_cricuity_index_of_a_itinerary():
    # Setup Route
    shape = [Point(0.0, 0.0), Point(0.1, 0.0), Point(0.1, 0.1)]
    s1 = Stop("S1", 0.0, 0.0)
    s2 = Stop("S2", 0.1, 0.1)
    # Chúng ta đặt s1_alt nằm ngoài rìa nhưng vuông góc với Đoạn 1 dọc theo trục y=0.0
    s1_alt = Stop("S1_alt", 0.05, -0.01)   # Khi hạ vuông góc -> (0.05, 0.0) 
    
    # Chúng ta đặt s2_alt nằm ngoài rìa nhưng vuông góc với Đoạn 2 dọc theo trục x=0.1
    s2_alt = Stop("S2_alt", 0.11, 0.05)    # Khi hạ vuông góc -> (0.1, 0.05)
    
    r1 = Route("R1", Direction.INBOUND, shape, [s1, s2])
    r2 = Route("R2", Direction.INBOUND, shape, [s1_alt, s2_alt])
    
    # Setup Itinerary
    leg1 = Leg("R1", "S1", "S2")
    leg2 = Leg("R2", "S1_alt", "S2_alt")
    iti1 = Itinerary([leg1])
    iti2 = Itinerary([leg2])
    
    
    index_r1 = find_cricuity_index_of_a_itinerary(iti1, [r1,r2])
    index_r2 = find_cricuity_index_of_a_itinerary(iti2, [r1,r2])
    assert index_r1 >= 1.0
    assert index_r2 >= 1.0
