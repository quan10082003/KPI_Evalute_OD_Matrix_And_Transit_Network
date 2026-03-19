import pytest
from domain.entities_and_dataclass.domain_dataclass import Point, Direction
from domain.entities_and_dataclass.domain_class import Stop, Route, Zone, ODPair

def test_stop_initialization():
    s = Stop("S1", 21.0, 105.0)
    assert s.id == "S1"
    assert s.coord == Point(21.0, 105.0)
    assert isinstance(s.coord, Point)

def test_route_closest_stop():
    s1 = Stop("S1", 21.0, 105.0)
    s2 = Stop("S2", 21.1, 105.0)
    s3 = Stop("S3", 21.3, 105.0)
    s4 = Stop("S4", 21.5, 105.0)
    route = Route("R1", Direction.INBOUND, shape=[], stops_seq=[s1, s2,s3,s4])
    
    p = Point(21.03, 105.0) # Gần S1 hơn
    closest = route.get_closest_stop_to_point(p)
    assert closest.id == "S1"

def test_route_distance_and_circuity():
    # Tạo một shape hình tam giác vuông cơ bản cho Route
    shape = [Point(0.0, 0.0), Point(0.1, 0.0), Point(0.1, 0.1)]
    s1 = Stop("S1", 0.0, 0.0)
    s2 = Stop("S2", 0.1, 0.1)
    
    route = Route("R1", Direction.INBOUND, shape=shape, stops_seq=[s1, s2])
    
    # Kiểm tra phương thức cắt ghép và tính metrics
    dist = route.get_distance_between_stops(s1, s2)
    assert dist > 0 # Có độ dài tính bằng mét do C++ Shapely
    
    circuity = route.get_cricuity_index_between_2_stops(s1, s2)
    assert circuity >= 1.0 # Luôn lớn hơn hoặc bằng đường chim bay

def test_route_shared_stops():
    s1 = Stop("S1", 0, 0)
    s2 = Stop("S2", 0, 0)
    s3 = Stop("S3", 0, 0)
    
    r1 = Route("R1", Direction.INBOUND, shape=[], stops_seq=[s1, s2])
    r2 = Route("R2", Direction.INBOUND, shape=[], stops_seq=[s2, s3])
    
    shared = r1.get_share_stops_with_other_route(r2)
    assert len(shared) == 1
    assert shared[0].id == "S2"

def test_zone_point_in_zone():
    boundary = [Point(0.0, 0.0), Point(0.0, 1.0), Point(1.0, 1.0), Point(1.0, 0.0)]
    centroid = Point(0.5, 0.5)
    z = Zone("Z1", boundary, centroid)
    
    p_in = Point(0.5, 0.5)
    p_out = Point(2.0, 2.0)
    
    assert z.is_point_in_zone(p_in) is True
    assert z.is_point_in_zone(p_out) is False
