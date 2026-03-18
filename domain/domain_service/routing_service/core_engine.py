from abc import ABC, abstractmethod
from typing import List

from domain.domain_service.spatial_service import find_all_routes_pass_through_zone, find_all_stops_on_a_route_located_in_a_certain_zone

from domain.entities_and_dataclass.domain_dataclass import Itinerary, AggregatedItinerary, AggregatedLeg
from domain.entities_and_dataclass.domain_class import Route, ODPair

from domain.domain_service.routing_service.filter_strategy import ItineraryFilterStrategy

class AbstractRoutingEngine(ABC):
    """
    Lớp điều phối thuật toán tìm đường (Core Engine)
    """
    def __init__(self, filter_strategy: ItineraryFilterStrategy):
        # Ứng dụng Dependency Injection để truyền Filter từ bên ngoài vào
        self.filter_strategy = filter_strategy

    def find_feasible_itineraries(self, od_pair: ODPair, routes: List[Route]) -> List[Itinerary]:
        """ Template Method """
        # Bước 1: Tìm tất cả quỹ đạo di chuyển (Hyperpaths)
        aggregated_list = self._find_aggregated_itineraries(od_pair, routes)
        
        # Bước 2: Gọi Object Filter Strategy để bóc tách và chọn trạm tốt nhất
        detailed_list = []
        for agg_itinerary in aggregated_list:
            best_itinerary = self.filter_strategy.filter(agg_itinerary, od_pair, routes)
            if best_itinerary:
                detailed_list.append(best_itinerary)
                
        return detailed_list

    @abstractmethod
    def _find_aggregated_itineraries(self, od_pair: ODPair, routes: List[Route]) -> List[AggregatedItinerary]:
        # Engine con phải tự Override thuật toán Hash Map này
        pass


class DirectConnectionRoutingEngine(AbstractRoutingEngine):
    """
    Engine tìm đường kết nối trực tiếp (0-transfer).
    Sử dụng Toán tử Set và Mảng index tĩnh O(1).
    """
    def _find_aggregated_itineraries(self, od_pair: ODPair, routes: List[Route]) -> List[AggregatedItinerary]:
        
        # Logic O(1) Lookup từ Hash Map
       
        routes_in_origin = find_all_routes_pass_through_zone(od_pair.origin_area, routes)
        routes_in_dest = find_all_routes_pass_through_zone(od_pair.destination_area, routes)

        common_routes = set(routes_in_origin) & set(routes_in_dest)
        list_aggregated_itinerary = []
        
        # Build local index map since Route domain class lacks stop_index_map
        stop_index_maps = {
            r.id: {stop.id: idx for idx, stop in enumerate(r.stops_seq)} for r in common_routes
        }
        
        for route in common_routes:
            route_idx_map = stop_index_maps[route.id]
            origin_stops = find_all_stops_on_a_route_located_in_a_certain_zone(od_pair.origin_area, route)
            dest_stops = find_all_stops_on_a_route_located_in_a_certain_zone(od_pair.destination_area, route)
            
            valid_origin_stop_ids = set()
            valid_dest_stop_ids = set()
            
            for o_stop in origin_stops:
                for d_stop in dest_stops:
                    # Tra cứu trực tiếp từ Map O(1)
                    o_index = route_idx_map.get(o_stop.id, -1)
                    d_index = route_idx_map.get(d_stop.id, -1)
                    
                    if o_index != -1 and d_index != -1 and o_index < d_index: 
                        valid_origin_stop_ids.add(o_stop.id)
                        valid_dest_stop_ids.add(d_stop.id)
                        
            if valid_origin_stop_ids and valid_dest_stop_ids:
                
                aggregated_leg = AggregatedLeg(
                    route_ref_id=route.id, 
                    possible_board_stop_ids=valid_origin_stop_ids, 
                    possible_alight_stop_ids=valid_dest_stop_ids
                )
                list_aggregated_itinerary.append(AggregatedItinerary(legs=[aggregated_leg]))

        return list_aggregated_itinerary


class OneTransferRoutingEngine(AbstractRoutingEngine):
    """
    Engine tìm đường gián tiếp qua 1 lần đổi chuyến (1-transfer).
    Sử dụng Array Hash Map để giảm Complexity O(N).
    """
    def _find_aggregated_itineraries(self, od_pair: ODPair, routes: List[Route]) -> List[AggregatedItinerary]:
        routes_in_origin = find_all_routes_pass_through_zone(od_pair.origin_area, routes)
        routes_in_dest = find_all_routes_pass_through_zone(od_pair.destination_area, routes)
        
        # Loại bỏ các tuyến chung (vì chúng đã được lo bởi DirectConnectionEngine)
        common_routes = set(routes_in_origin) & set(routes_in_dest)
        
        r1_list = [r for r in routes_in_origin if r not in common_routes]
        r2_list = [r for r in routes_in_dest if r not in common_routes]
        
        list_aggregated_itinerary = []
        
        # Build local index map since Route domain class lacks stop_index_map
        stop_index_maps = {
            r.id: {stop.id: idx for idx, stop in enumerate(r.stops_seq)} for r in (r1_list + r2_list)
        }
        
        for r1 in r1_list:
            r1_idx_map = stop_index_maps[r1.id]
            for r2 in r2_list:
                r2_idx_map = stop_index_maps[r2.id]
                
                # Tìm trạm chung giữa 2 tuyến (điểm giao / trung chuyển tiềm năng)
                shared_stops = r1.get_share_stops_with_other_route(r2)
                if not shared_stops:
                    continue
                    
                shared_stop_ids = {stop.id for stop in shared_stops}
                
                # Check r1: Bến lên O phải TRƯỚC Bến trung chuyển
                origin_stops = find_all_stops_on_a_route_located_in_a_certain_zone(od_pair.origin_area, r1)
                valid_board_stop_ids = set()
                valid_r1_transfer_stop_ids = set()
                
                for o_stop in origin_stops:
                    o_idx = r1_idx_map.get(o_stop.id, -1)
                    if o_idx == -1: continue
                    
                    for t_stop_id in shared_stop_ids:
                        t_idx = r1_idx_map.get(t_stop_id, -1)
                        if t_idx != -1 and o_idx < t_idx:
                            valid_board_stop_ids.add(o_stop.id)
                            valid_r1_transfer_stop_ids.add(t_stop_id)
                            
                if not valid_board_stop_ids:
                    continue
                    
                # Check r2: Bến trung chuyển phải TRƯỚC Bến xuống D
                dest_stops = find_all_stops_on_a_route_located_in_a_certain_zone(od_pair.destination_area, r2)
                valid_r2_transfer_stop_ids = set()
                valid_alight_stop_ids = set()
                
                for d_stop in dest_stops:
                    d_idx = r2_idx_map.get(d_stop.id, -1)
                    if d_idx == -1: continue
                    
                    for t_stop_id in valid_r1_transfer_stop_ids:
                        # Chỉ check các bến transfer hợp lệ từ r1
                        t_idx = r2_idx_map.get(t_stop_id, -1)
                        if t_idx != -1 and t_idx < d_idx:
                            valid_r2_transfer_stop_ids.add(t_stop_id)
                            valid_alight_stop_ids.add(d_stop.id)
                            
                # Tạo Aggregated Itinerary với 2 Legs nếu có giao dịch trung chuyển chốt
                if valid_board_stop_ids and valid_r2_transfer_stop_ids and valid_alight_stop_ids:
                    leg1 = AggregatedLeg(
                        route_ref_id=r1.id,
                        possible_board_stop_ids=valid_board_stop_ids,
                        possible_alight_stop_ids=valid_r2_transfer_stop_ids # Tập các bến transfer
                    )
                    leg2 = AggregatedLeg(
                        route_ref_id=r2.id,
                        possible_board_stop_ids=valid_r2_transfer_stop_ids, # Tập các bến transfer (chung)
                        possible_alight_stop_ids=valid_alight_stop_ids
                    )
                    list_aggregated_itinerary.append(AggregatedItinerary(legs=[leg1, leg2]))

        return list_aggregated_itinerary
