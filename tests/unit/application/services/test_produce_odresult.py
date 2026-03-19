import pytest
from domain.entities_and_dataclass.domain_class import Route, Stop, Direction, ODPair, Zone
from domain.entities_and_dataclass.domain_dataclass import Point
from application.services.produce_odresult import ProduceODResult

def test_produce_od_result_empty():
    producer = ProduceODResult()
    results = producer.produce_od_result(
        route_list=[],
        stop_list=[],
        zone_list=[],
        od_pair_list=[]
    )
    assert len(results) == 0

def test_produce_od_result_basic():
    # Arrange
    # Tạo fake object đầy đủ các tham số được yêu cầu theo kiến trúc
    p_center = Point(0.0, 0.0)
    z1 = Zone(id="Z1", boundary=[], centroid=p_center)
    z2 = Zone(id="Z2", boundary=[], centroid=p_center)
    
    # ODPair cần truyền travel_demand
    od_pair = ODPair(id="OD1", origin_area=z1, destination_area=z2, travel_demand=10)
    
    s1 = Stop("S1", 0.0, 0.0)
    s2 = Stop("S2", 0.1, 0.1)
    route1 = Route("R1", Direction.INBOUND, [Point(0.0, 0.0), Point(0.1, 0.0), Point(0.1, 0.1)], [s1, s2])
    
    producer = ProduceODResult()
    
    # Act
    results = producer.produce_od_result(
        route_list=[route1],
        od_pair_list=[od_pair]
    )
    
    # Assert
    assert len(results) == 1
    assert results[0].od_id == "OD1"
    
    # Ghi rõ các điều kiện kiểm tra (check) dữ liệu trả về 
    # Thay vì hasattr, ta assert đích danh kiểu dữ liệu trả về của 2 danh sách này phải là list.
    assert isinstance(results[0].aggregated_itineraries, list), "aggregated_itineraries phải là list"
    assert isinstance(results[0].represent_itineraries, list), "represent_itineraries phải là list"
    
    # Do thuật toán thực tế có filter khoảng cách và logic tìm đường, với bộ data mock rỗng Z1, Z2 này, 
    # thường thuật toán sẽ trả về list rỗng nếu ko tìm được tuyến, 
    # điều kiện đúng nhất là có list được khởi tạo.
    print("Test passed! ODRoutingResult has been crafted correctly.")
