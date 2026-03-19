from abc import ABC, abstractmethod
from typing import List, Any
from domain.entities_and_dataclass.domain_dataclass import AggregatedItinerary, Itinerary
from domain.entities_and_dataclass.domain_class import Route
from domain.domain_service.spatial_service import find_cricuity_index_of_a_itinerary


class KPI_caculate(ABC):
    @abstractmethod
    def calculate_kpi(self, data: Any) -> dict:
        pass


class Tranfer_rate_caculate(KPI_caculate):
    def calculate_kpi(self, agg_itinerary: AggregatedItinerary, ) -> dict:
        """
        Tính toán KPI về số lần chuyển tuyến.
        
        Args:
            agg_itinerary: 1 cách đi tổng quát
            
        Returns:
            dict: Chứa thông tin số lần chuyển tuyến CỦA HÀNH TRÌNH ĐÓ
        """
        result = {
        "score" : ""
        }

        if agg_itinerary.total_transfers == 0:
            result["score"] = "0"
        elif agg_itinerary.total_transfers == 1:
            result["score"] = "1"
        else:
            result["score"] = "Not valid or >1"
        
        return result


class Cricuity_index_caculate(KPI_caculate):
    def calculate_kpi(self, itinerary: Itinerary, R_ref_list: List[Route]) -> dict:
        """
        Tính toán KPI về độ trực tiếp của chuyến đi cụ thể
        
        Args:
            itinerary: 1 hành trình cụ thể
            R_ref_list: Danh sách các tuyến đường tham chiếu
            
        Returns:
            dict: Chứa thông tin đọ vòng vèo và hành trình của hành trình
        """

        result = {
        "score" : "" ,
        "route_sequence" : [] ,
        "stop_sequence" : []
        }

        if itinerary.legs == [] :
            result["score"] = "Not valid or >1"
            result["route_sequence"] = []
            result["stop_sequence"] = []

        else:
            cricuity_index = find_cricuity_index_of_a_itinerary(itinerary, R_ref_list)
            result["score"] = cricuity_index
            result["route_sequence"] = itinerary.get_list_routes_id
            result["stop_sequence"] = itinerary.get_list_stops_id

        return result


