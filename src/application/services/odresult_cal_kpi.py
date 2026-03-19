from typing import List, Any, Optional

from domain.entities_and_dataclass.domain_dataclass import ODRoutingResult
from domain.domain_service.kpi_service.kpi_service import KPI_caculate, Tranfer_rate_caculate, Cricuity_index_caculate
from domain.entities_and_dataclass.domain_class import Route, Stop, Zone, ODPair
from domain.domain_service.kpi_service.kpi_A_service import KPIASpatialCoverageService


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

            elif isinstance(kpi_cal, KPIASpatialCoverageService):
                if not od_routing_results.aggregated_itineraries:
                    kpi_res = self._empty_spatial_kpi(od_routing_results, kpi_cal.stop_coverage_radius_m)
                else:
                    if not hasattr(od_routing_results, "origin_zone_id") or not hasattr(od_routing_results, "destination_zone_id"):
                        raise ValueError("ODRoutingResult thiếu origin_zone_id/destination_zone_id cho Spatial KPI")

                    kpi_res = kpi_cal.compute(
                        od_routing_results.origin_zone_id,
                        od_routing_results.destination_zone_id,
                        od_routing_results.aggregated_itineraries[0],
                    )
                results["kpi_results"][kpi_name].append({
                    f"od_id_{od_routing_results.od_id}": kpi_res
                })

            else:
                raise ValueError(f"Không tìm thấy KPI calculator: {kpi_name}")

        return results

    def _empty_spatial_kpi(self, od_routing_results: ODRoutingResult, radius_m: float) -> dict:
        origin_zone_id = getattr(od_routing_results, "origin_zone_id", "")
        destination_zone_id = getattr(od_routing_results, "destination_zone_id", "")
        return {
            "score_percent": 0.0,
            "score_ratio": 0.0,
            "origin_coverage_percent": 0.0,
            "origin_coverage_ratio": 0.0,
            "destination_coverage_percent": 0.0,
            "destination_coverage_ratio": 0.0,
            "origin_zone_id": origin_zone_id,
            "destination_zone_id": destination_zone_id,
            "radius_m": radius_m,
            "origin_stop_count": 0,
            "destination_stop_count": 0,
        }
