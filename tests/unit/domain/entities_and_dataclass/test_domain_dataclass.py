import pytest
from domain.entities_and_dataclass.domain_dataclass import Point, Direction, Leg, Itinerary, AggregatedLeg, AggregatedItinerary, ODRoutingResult

def test_point_initialization():
    p = Point(21.0, 105.0)
    assert p.lat == 21.0
    assert p.lon == 105.0

def test_point_distance_to():
    p1 = Point(21.0, 105.0)
    p2 = Point(21.1, 105.0)
    # 0.1 degree lat is ~ 11.1km
    dist = p1.distance_to(p2)
    assert 11000 < dist < 11200

def test_itinerary_properties():
    legs = [
        Leg("R1", "S1", "S2"),
        Leg("R2", "S2", "S3")
    ]
    iti = Itinerary(legs=legs)
    assert iti.total_transfers == 1
    assert iti.get_origin_stops_id == "S1"
    assert iti.get_destination_stops_id == "S3"
    
    # Test các Array methods mới thêm
    assert iti.get_list_stops_id == ["S1", "S2", "S3"]
    assert iti.get_list_routes_id == ["R1", "R2"]

def test_aggregated_itinerary_properties():
    legs = [
        AggregatedLeg("R1", {"S1", "S1_alt"}, {"S2"}),
        AggregatedLeg("R2", {"S2"}, {"S3", "S3_alt"})
    ]
    agg_iti = AggregatedItinerary(legs=legs)
    assert agg_iti.total_transfers == 1
    assert agg_iti.get_origin_stops_id == {"S1", "S1_alt"}
    assert agg_iti.get_destination_stops_id == {"S3", "S3_alt"}

def test_od_routing_result_properties():
    agg_leg1 = AggregatedLeg("R1", {"S1"}, {"S2"})
    agg_leg2 = AggregatedLeg("R2", {"S2"}, {"S3"})
    
    agg_iti_0_transfer = AggregatedItinerary(legs=[agg_leg1])
    agg_iti_1_transfer = AggregatedItinerary(legs=[agg_leg1, agg_leg2])
    
    od_res = ODRoutingResult(
        od_id="OD1", 
        aggregated_itineraries=[agg_iti_0_transfer, agg_iti_1_transfer],
        represent_itineraries=[]
    )
    
    # Test bộ lọc đếm transfer của result
    assert od_res.total_aggregated_itineraries == 2
    assert od_res.total_direct_itineraries == 1
    assert od_res.total_one_transfer_itineraries == 1
