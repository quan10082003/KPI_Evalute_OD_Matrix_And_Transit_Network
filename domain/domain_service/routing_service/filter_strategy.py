from abc import ABC, abstractmethod
from typing import List

from domain.entities_and_dataclass.domain_dataclass import Itinerary, AggregatedItinerary, Leg
from domain.entities_and_dataclass.domain_class import Route, ODPair

class ItineraryFilterStrategy(ABC):
    """
    Interface Abstract dành cho việc bóc tách (Unroll) và Lọc
    các trạm để lấy Itinerary tốt nhất từ AggregatedItinerary.
    """
    @abstractmethod
    def filter(self, agg_it: AggregatedItinerary, od_pair: ODPair, routes: List[Route]) -> Itinerary:
        pass

    def _get_closest_stop_id_to_centroid(self, stop_ids: set, route_id: str, centroid: 'Point', routes: List[Route]) -> str:
        route = next((r for r in routes if r.id == route_id), None)
        if not route: return None
        
        min_dist = float('inf')
        best_stop_id = None
        
        for stop in route.stops_seq:
            if stop.id in stop_ids:
                dist = stop.coord.distance_to(centroid)
                if dist < min_dist:
                    min_dist = dist
                    best_stop_id = stop.id
                    
        return best_stop_id

    def _get_extreme_stops_in_zone(self, stop_ids: set, route_id: str, routes: List[Route], find_min: bool) -> str:
        route = next((r for r in routes if r.id == route_id), None)
        if not route: return None
        
        best_idx = float('inf') if find_min else -1
        best_stop_id = None
        
        for idx, stop in enumerate(route.stops_seq):
            if stop.id in stop_ids:
                if find_min and idx < best_idx:
                    best_idx = idx
                    best_stop_id = stop.id
                elif not find_min and idx > best_idx:
                    best_idx = idx
                    best_stop_id = stop.id
                    
        return best_stop_id


class OptimalWalkingDistanceFilter(ItineraryFilterStrategy):
    """
    Strategy 1: Lọc trạm dựa trên "Walking Distance" ngắn nhất Dành riêng cho 0-transfer        .
    Yêu cầu: Bến lên phải sát tâm Origin nhất, Bến xuống phải sát tâm Destination nhất.
    """
    def filter(self, agg_it: AggregatedItinerary, od_pair: ODPair, routes: List[Route]) -> Itinerary:
        # Giả định hiện tại chỉ bóc tách cho trường hợp 0-transfer (1 Leg)
        if len(agg_it.legs) == 1:
            agg_leg = agg_it.legs[0]
            
            is_same_zone = od_pair.origin_area.id == od_pair.destination_area.id
            
            if is_same_zone:
                # Trùng OD zone -> ưu tiên điểm đầu và điểm cuối để được hành trình dài nhất
                # best_board_stop_id = self._get_extreme_stops_in_zone(
                #     stop_ids=agg_leg.possible_board_stop_ids,
                #     route_id=agg_leg.route_ref_id,
                #     routes=routes,
                #     find_min=True
                # )
                # best_alight_stop_id = self._get_extreme_stops_in_zone(
                #     stop_ids=agg_leg.possible_alight_stop_ids,
                #     route_id=agg_leg.route_ref_id,
                #     routes=routes,
                #     find_min=False
                # )
                raise ValueError("Không hỗ trợ trường hợp trùng OD zone")
            else:
                # 1. Tìm bến Lên tối ưu nhất (Gần O.centroid)
                best_board_stop_id = self._get_closest_stop_id_to_centroid(
                    stop_ids=agg_leg.possible_board_stop_ids,
                    route_id=agg_leg.route_ref_id,
                    centroid=od_pair.origin_area.centroid,
                    routes=routes
                )
                
                # 2. Tìm bến Xuống tối ưu nhất (Gần D.centroid)
                best_alight_stop_id = self._get_closest_stop_id_to_centroid(
                    stop_ids=agg_leg.possible_alight_stop_ids,
                    route_id=agg_leg.route_ref_id,
                    centroid=od_pair.destination_area.centroid,
                    routes=routes
                )
            
            if best_board_stop_id and best_alight_stop_id:
                final_leg = Leg(
                    route_ref_id=agg_leg.route_ref_id,
                    board_stop_id=best_board_stop_id,
                    alight_stop_id=best_alight_stop_id
                )
                return Itinerary(legs=[final_leg])
                
        return None
        



class OneTransferOptimalFilter(ItineraryFilterStrategy):
    """
    Strategy 2: Lọc trạm dành riêng cho 1-transfer.
    Yêu cầu: Bến lên sát tâm Origin nhất, Điểm trung chuyển kết nối tốt nhất, Bến xuống sát tâm Destination nhất.
    """
    def filter(self, agg_it: AggregatedItinerary, od_pair: ODPair, routes: List[Route]) -> Itinerary:
        if len(agg_it.legs) == 2:
            agg_leg1 = agg_it.legs[0]
            agg_leg2 = agg_it.legs[1]
            
            is_same_zone = od_pair.origin_area.id == od_pair.destination_area.id
            
            if is_same_zone:
                # Trùng OD zone -> ưu tiên điểm đầu và điểm cuối để được hành trình dài nhất
                # best_board_stop_id = self._get_extreme_stops_in_zone(
                #     stop_ids=agg_leg1.possible_board_stop_ids,
                #     route_id=agg_leg1.route_ref_id,
                #     routes=routes,
                #     find_min=True
                # )
                # best_alight_stop_id = self._get_extreme_stops_in_zone(
                #     stop_ids=agg_leg2.possible_alight_stop_ids,
                #     route_id=agg_leg2.route_ref_id,
                #     routes=routes,
                #     find_min=False
                # )
                raise ValueError("Không hỗ trợ trường hợp trùng OD zone")
            else:
                # 1. Tìm bến Lên tối ưu nhất (Gần O.centroid)
                best_board_stop_id = self._get_closest_stop_id_to_centroid(
                    stop_ids=agg_leg1.possible_board_stop_ids,
                    route_id=agg_leg1.route_ref_id,
                    centroid=od_pair.origin_area.centroid,
                    routes=routes
                )
                
                # 2. Tìm bến Xuống tối ưu nhất (Gần D.centroid)
                best_alight_stop_id = self._get_closest_stop_id_to_centroid(
                    stop_ids=agg_leg2.possible_alight_stop_ids,
                    route_id=agg_leg2.route_ref_id,
                    centroid=od_pair.destination_area.centroid,
                    routes=routes
                )
            
            # 3. Tìm bến Trung chuyển. Vì agg_leg1 và agg_leg2 đã share chung tập transfer stop IDs.
            valid_transfers = agg_leg1.possible_alight_stop_ids.intersection(agg_leg2.possible_board_stop_ids)
            if not valid_transfers:
                return None
                
            # Tiêu chí phụ cho trạm trung chuyển (nếu có nhiều trạm).
            # Có thể nâng cấp để tìm trạm transfer có khoảng cách đến O.centroid + D.centroid là tổng min.
            best_transfer_stop_id = min(
                valid_transfers, 
                key=lambda stop_id: self._get_direct_distance_to_od_centroids(stop_id, agg_leg1.route_ref_id, od_pair, routes)
            )
            
            if best_board_stop_id and best_alight_stop_id and best_transfer_stop_id:
                final_leg1 = Leg(
                    route_ref_id=agg_leg1.route_ref_id,
                    board_stop_id=best_board_stop_id,
                    alight_stop_id=best_transfer_stop_id
                )
                final_leg2 = Leg(
                    route_ref_id=agg_leg2.route_ref_id,
                    board_stop_id=best_transfer_stop_id,
                    alight_stop_id=best_alight_stop_id
                )
                return Itinerary(legs=[final_leg1, final_leg2])
                
        return None
        
    def _get_direct_distance_to_od_centroids(self, stop_id: str, route_id: str, od_pair: ODPair, routes: List[Route]) -> float:
        route = next((r for r in routes if r.id == route_id), None)
        if not route: return float('inf')
        
        stop = next((s for s in route.stops_seq if s.id == stop_id), None)
        if not stop: return float('inf')
        
        dist_o = stop.coord.distance_to(od_pair.origin_area.centroid)
        dist_d = stop.coord.distance_to(od_pair.destination_area.centroid)
        return dist_o + dist_d


