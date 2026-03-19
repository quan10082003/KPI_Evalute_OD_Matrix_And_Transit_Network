from typing import List, Dict, Any, Optional
import json

from domain.entities_and_dataclass.domain_dataclass import ODRoutingResult
from domain.domain_service.kpi_service.kpi_service import KPI_caculate, Tranfer_rate_caculate, Cricuity_index_caculate
from domain.entities_and_dataclass.domain_class import Route

class CalKPI:
    def __init__(self):
        pass

    def cal_kpi(self, 
                od_routing_results: ODRoutingResult, 
                kpi_calculators: List[KPI_caculate],
                route_list: Optional[List[Route]] = None,
                stop_list: Optional[List[Stop]] = None,
                zone_list: Optional[List[Zone]] = None,
                od_pair_list: Optional[List[ODPair]] = None) -> dict:
        
        # NOTE: Đoạn code cũ có gọi id_to_od() nhưng do chưa rõ được lấy từ đâu
        # Tạm thời comment lại và thay thế bằng các input mới cho phù hợp nhu cầu tính các KPIs
        # odpair = id_to_od(od_routing_results.od_id)
        # o_bound = odpair.origin_zone_id.boundary
        # d_bound = odpair.destination_zone_id.boundary

        if route_list is None:
            route_list = []

        results = {
            "od_id": od_routing_results.od_id,
            "kpi_results": {}
        }

        # Tính toán cho từng KPI calculator truyền vào
        for kpi_cal in kpi_calculators:
            kpi_name = kpi_cal.__class__.__name__
            results["kpi_results"][kpi_name] = []

            if isinstance(kpi_cal, Tranfer_rate_caculate):
                for idx in range(od_routing_results.total_aggregated_itineraries):
                    agg_itinerary = od_routing_results.aggregated_itineraries[idx]
                    kpi_res = kpi_cal.calculate_kpi(agg_itinerary)
                    results["kpi_results"][kpi_name].append({
                        f"agg_itinerary_{idx}": kpi_res
                    })

            elif isinstance(kpi_cal, Cricuity_index_caculate):
                for idx, itinerary in enumerate(od_routing_results.represent_itineraries):
                    kpi_res = kpi_cal.calculate_kpi(itinerary, route_list)
                    results["kpi_results"][kpi_name].append({
                        f"itinerary_{idx}": kpi_res
                    })
            else:
                # Nếu có thêm KPI mới, xử lý tương ứng ở đây hoặc theo template chung
                pass


        return results