import pytest
from domain.entities_and_dataclass.domain_dataclass import Point, Direction, AggregatedLeg, AggregatedItinerary
from domain.entities_and_dataclass.domain_class import Stop, Route, Zone, ODPair
from domain.domain_service.routing_service.filter_strategy import OptimalWalkingDistanceFilter, OneTransferOptimalFilter

def test_optimal_walking_distance_filter():
    # Setup Zones
    z_origin = Zone("Z1", [], Point(0, 0))
    z_dest = Zone("Z2", [], Point(10, 10))
    od = ODPair("OD1", z_origin, z_dest, 100)
    
    # Setup Stops
    # Origin stops
    s1 = Stop("S1", 0.1, 0.1) # Rất gần Z1 centroid
    s2 = Stop("S2", 2.0, 2.0)
    # Dest stops
    s3 = Stop("S3", 9.9, 9.9) # Rất gần Z2 centroid
    s4 = Stop("S4", 8.0, 8.0)
    
    r1 = Route("R1", Direction.INBOUND, [], [s1, s2, s3, s4])
    
    agg_leg = AggregatedLeg("R1", {"S1", "S2"}, {"S3", "S4"})
    agg_iti = AggregatedItinerary([agg_leg])
    
    filter = OptimalWalkingDistanceFilter()
    filtered_iti = filter.filter(agg_iti, od, [r1])
    
    assert filtered_iti is not None
    assert len(filtered_iti.legs) == 1
    # Do thuật toán ưu tiên tìm trạm Board (s1, s2) gần z_origin nhất 
    # Và tìm trạm Alight (s3, s4) gần z_dest nhất
    assert filtered_iti.legs[0].board_stop_id == "S1"
    assert filtered_iti.legs[0].alight_stop_id == "S3"

def test_optimal_walking_distance_filter_same_zone():
    z_origin = Zone("Z1", [], Point(0, 0))
    od = ODPair("OD1", z_origin, z_origin, 100) # Cùng zone
    
    r1 = Route("R1", Direction.INBOUND, [], [])
    agg_leg = AggregatedLeg("R1", {"S1", "S2"}, {"S3", "S4"})
    agg_iti = AggregatedItinerary([agg_leg])
    
    filter = OptimalWalkingDistanceFilter()
    
    # Kiểm tra bộ lọc có raise đúng lỗi ValueError ngoại lệ ko
    with pytest.raises(ValueError, match="Không hỗ trợ trường hợp trùng OD zone"):
        filter.filter(agg_iti, od, [r1])
