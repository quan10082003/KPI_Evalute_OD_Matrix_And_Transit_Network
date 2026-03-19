import pytest
from domain.entities_and_dataclass.domain_dataclass import Point, Direction
from domain.entities_and_dataclass.domain_class import Stop, Route, Zone, ODPair
from domain.domain_service.routing_service.routing_service import find_routes
def test_route_finding_service_facade():
    # Integration pattern for Facade with real polygon boundaries
    z_origin_boundary = [Point(-1,-1), Point(-1, 5), Point(5, 5), Point(5, -1)]
    z_origin = Zone("Z1", z_origin_boundary, Point(0, 0))
    
    z_dest_boundary = [Point(6,6), Point(6, 15), Point(15, 15), Point(15, 6)]
    z_dest = Zone("Z2", z_dest_boundary, Point(10, 10))
    
    od = ODPair("OD1", z_origin, z_dest, 100)
    
    s1 = Stop("S1", 0, 0)
    s2 = Stop("S2", 10, 10)
    s3 = Stop("S3", 0, 10)

    r1 = Route("R1", Direction.INBOUND, [Point(0,0), Point(10,10)], [s1, s2])
    r2 = Route("R2", Direction.INBOUND, [Point(10,10), Point(20,20)], [s2, s3])

    r3 = Route("R3", Direction.INBOUND, [Point(0,0), Point(0,10)], [s1, s3])
    r4 = Route("R4", Direction.INBOUND, [Point(0,10), Point(10,10)], [s3, s2])
    r4N = Route("R4N", Direction.INBOUND, [Point(10,10), Point(0,10)], [s2, s3])
    r5 = Route("R5", Direction.INBOUND, [Point(0,0), Point(0,10), Point(10,10)], [s1, s3, s2])
    
    # 0 transfer expectation
    itin_list = find_routes(od, [r1,r2,r3,r4,r4N,r5])
    
    assert len(itin_list) == 3
    assert itin_list[0].legs[0].route_ref_id == "R1"
    assert itin_list[1].legs[0].route_ref_id == "R5"
    assert itin_list[2].legs[0].route_ref_id == "R3"
    assert itin_list[2].legs[1].route_ref_id == "R4"
