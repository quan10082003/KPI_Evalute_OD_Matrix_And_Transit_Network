from typing import List
from domain.entities_and_dataclass.domain_class import Stop, Route, Zone, Itinerary

def find_all_routes_pass_through_zone(Z: Zone, R_list : List[Route]) -> List[Route]:
    """
    Lọc ra danh sách các tuyến đường có đi qua một Zone cụ thể và có trạm dừng trên zone đó.
    Thuật toán mới sử dụng Topology của thư viện shapely để kiểm tra giao cắt.
    """
    passing_routes = []
    
    # Bảo vệ (Guard clause) trường hợp Zone bị lỗi Polygon
    if getattr(Z, 'polygon', None) is None:
        return passing_routes
        
    for route in R_list:
        # Kiểm tra cực ngắn qua phép giao C++ (cực kỳ nhanh so với lặp từng Point)
        for stop in route.stops_seq:
            if Z.is_point_in_zone(stop.coord):
                passing_routes.append(route)
                break
                   
    return passing_routes            

def find_all_stops_on_a_route_located_in_a_certain_zone(Z: Zone, R: Route) -> List[Stop]:
    """
    Tìm ra các trạm dừng của 1 tuyến nằm trong 1 vùng cho trước
    """
    passing_stops = []
    for stop in R.stops_seq:
        # Hàm is_point_in_zone giờ đây đã được nâng cấp dùng C++ bên trong Zone class
        if Z.is_point_in_zone(stop.coord):
            passing_stops.append(stop)
                
    return passing_stops

def find_cricuity_index_of_a_itinerary(I: Itinerary, R_list : List[Route]) -> float:
    """
    Tính độ vòng vèo (Circuity Index) của một hành trình chi tiết.
    Bằng tổng khoảng cách thực tế đi dọc THEO TUYẾN BUS chia cho 
    tổng khoảng cách ĐƯỜNG THẲNG TRỰC TIẾP nối qua các trạm.
    """
    total_route_dist = 0.0
    total_straight_dist = 0.0
    
    for leg in I.legs:
        route = next((r for r in R_list if r.id == leg.route_ref_id), None)
        
        if route:
            # Tra cứu đối tượng Stop từ file gốc
            start_stop = next((s for s in route.stops_seq if s.id == leg.board_stop_id), None)
            end_stop = next((s for s in route.stops_seq if s.id == leg.alight_stop_id), None)
            
            if start_stop and end_stop:
                total_route_dist += route.get_distance_between_stops(start_stop, end_stop)
            

    start_stop_id = I.get_origin_stops_id
    end_stop_id = I.get_destination_stops_id
    
    # Do start_stop_id chỉ là String (Ví dụ "S1"), ta phải tìm Object Stop thật sự trong R_list để đo toạ độ
    start_stop = next((s for r in R_list for s in r.stops_seq if s.id == start_stop_id), None)
    end_stop = next((s for r in R_list for s in r.stops_seq if s.id == end_stop_id), None)
    
    total_straight_dist = 0.0
    if start_stop and end_stop:
        total_straight_dist = start_stop.coord.distance_to(end_stop.coord)
    if total_straight_dist == 0:
        return 1.0
        
    return total_route_dist / total_straight_dist
