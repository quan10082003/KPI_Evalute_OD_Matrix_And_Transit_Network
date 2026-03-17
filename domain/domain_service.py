import numpy as np
from domain.domain_dataclass import Point, Direction, AggregatedLeg, AggregatedItinerary
from domain.domain_class import Stop, Route, Zone, OD_Pair
    
def find_all_routes_pass_through_zone(Z: Zone, R_list : List[Route]) -> List[Route]:
    """
    Lọc ra danh sách các tuyến đường có đi qua một Zone cụ thể.
    """
    passing_routes = []
    for route in R_list:
        for point in route.points:
            if Z.is_point_in_zone(point):
                passing_routes.append(route)
                break 
                   
    return passing_routes            

def find_all_stops_on_a_route_located_in_a_certain_zone(Z: Zone, R: Route) -> List[Stop]:
    """
    Tìm ra các trạm dừng của 1 tuyến nằm trong 1 vùng cho trước
    """
    passing_stops = []
    for stop in R.stops_seq:
        if Z.is_point_in_zone(stop.coord):
            passing_stops.append(stop)
                
    return passing_stops

def find_all_od_trips_for_a_odpair_0_transfer(OD: ODPair, R_list: List[Route]) -> List[AggregatedItinerary]:
    """
    Tìm ra tất cả các chuyến xe buýt đi thẳng (0 lần chuyển tuyến) cho một ODPair
    """
    # 1. Tìm các tuyến đi qua 2 vùng
    routes_in_origin = find_all_routes_pass_through_zone(OD.origin_area, R_list)
    routes_in_dest = find_all_routes_pass_through_zone(OD.destination_area, R_list)

    # 2. Tìm tập hợp các tuyến chung (Giao của 2 tập hợp) - Tối ưu O(N)
    common_routes = set(routes_in_origin) & set(routes_in_dest)
    
    list_aggregated_itinerary = []
    
    for route in common_routes:
        # Lấy danh sách trạm trong từng vùng
        origin_stops = find_all_stops_on_a_route_located_in_a_certain_zone(OD.origin_area, route)
        dest_stops = find_all_stops_on_a_route_located_in_a_certain_zone(OD.destination_area, route)
        
        valid_origin_stop_ids = set()
        valid_dest_stop_ids = set()
        
        # 3. LỌC CHIỀU DI CHUYỂN (Chặn lỗi đi ngược chiều)
        # Lấy danh sách toàn bộ ID trạm của tuyến để tra cứu index (thứ tự)
        route_stop_ids = [s.id for s in route.stops_seq] 
        
        for o_stop in origin_stops:
            for d_stop in dest_stops:
                o_index = route_stop_ids.index(o_stop.id)
                d_index = route_stop_ids.index(d_stop.id)
                
                # Bến lên phải xuất hiện TRƯỚC bến xuống
                if o_index < d_index: 
                    valid_origin_stop_ids.add(o_stop.id)
                    valid_dest_stop_ids.add(d_stop.id)
                    
        # 4. Nếu tồn tại ít nhất 1 cặp trạm hợp lệ, ta mới tạo Itinerary
        if valid_origin_stop_ids and valid_dest_stop_ids:
            aggregated_leg = AggregatedLeg(
                route_ref_id=route.id, 
                possible_board_stop_ids=valid_origin_stop_ids, 
                possible_alight_stop_ids=valid_dest_stop_ids
            )
            aggregated_itinerary = AggregatedItinerary(legs=[aggregated_leg])
            list_aggregated_itinerary.append(aggregated_itinerary)

    return list_aggregated_itinerary

def find_all_od_trips_for_a_odpair_1_transfer(OD: ODPair, R_list: List[Route]) -> List[AggregatedItinerary]:

    routes_in_origin = find_all_routes_pass_through_zone(OD.origin_area, R_list)
    routes_in_dest = find_all_routes_pass_through_zone(OD.destination_area, R_list)
    
    list_aggregated_itinerary = []
    
    # 1. Hai vòng lặp duyệt các cặp tuyến như X đề xuất
    for route_1 in routes_in_origin:
        for route_2 in routes_in_dest:
            
            # Bỏ qua nếu tuyến 1 và tuyến 2 là một (đó là trường hợp 0 transfer)
            if route_1.id == route_2.id: 
                continue 
                
            # 2. Tìm trạm giao nhau bằng method đã tối ưu
            shared_stops = route_1.get_shared_stops(route_2)
            if not shared_stops: 
                continue # Không cắt nhau thì bỏ qua luôn
                
            # 3. Lấy bến tiềm năng ở vùng O (cho Route 1) và vùng D (cho Route 2)
            origin_stops = find_all_stops_on_a_route_located_in_a_certain_zone(OD.origin_area, route_1)
            dest_stops = find_all_stops_on_a_route_located_in_a_certain_zone(OD.destination_area, route_2)
            
            # Khởi tạo các Set để chứa ID trạm ĐÃ QUA KIỂM DUYỆT chiều đi
            valid_origin_ids = set()
            valid_transfer_ids = set()
            valid_dest_ids = set()
            
            r1_stop_ids = [s.id for s in route_1.stops_seq]
            r2_stop_ids = [s.id for s in route_2.stops_seq]
            
            # 4. KIỂM TRA ĐIỀU KIỆN CHIỀU DI CHUYỂN
            for o_stop in origin_stops:
                for t_stop in shared_stops:
                    for d_stop in dest_stops:
                        
                        o_index_r1 = r1_stop_ids.index(o_stop.id)
                        t_index_r1 = r1_stop_ids.index(t_stop.id)
                        t_index_r2 = r2_stop_ids.index(t_stop.id)
                        d_index_r2 = r2_stop_ids.index(d_stop.id)
                        
                        # Điều kiện sống còn: Lên -> Chuyển (Tuyến 1) VÀ Chuyển -> Xuống (Tuyến 2)
                        if o_index_r1 < t_index_r1 and t_index_r2 < d_index_r2:
                            valid_origin_ids.add(o_stop.id)
                            valid_transfer_ids.add(t_stop.id)
                            valid_dest_ids.add(d_stop.id)
                            
            # 5. Đóng gói thành AggregatedItinerary nếu có phương án khả thi
            if valid_origin_ids and valid_transfer_ids and valid_dest_ids:
                leg_1 = AggregatedLeg(route_1.id, valid_origin_ids, valid_transfer_ids)
                leg_2 = AggregatedLeg(route_2.id, valid_transfer_ids, valid_dest_ids)
                
                itinerary = AggregatedItinerary(legs=[leg_1, leg_2])
                list_aggregated_itinerary.append(itinerary)
                
    return list_aggregated_itinerary 

def 