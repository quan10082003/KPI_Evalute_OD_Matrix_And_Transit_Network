from typing import List
from domain.entities_and_dataclass.domain_dataclass import ODRoutingResult
from domain.entities_and_dataclass.domain_class import Stop, Route

# Import từng KPI Domain Service tại đây khi chúng được triển khai.
# Ví dụ:
#   from domain.domain_service.kpi_service.kpi_A_service import KPIAService
#   from domain.domain_service.kpi_service.kpi_B_service import KPIBService


class KPIAggregatorService:
    """
    Application Service điều phối việc tổng hợp KPI.
    Nhận kết quả từ Preprocessing (Routing) và gọi các
    Domain KPI Services tương ứng rồi gom lại thành 1 report dict.
    """

    def aggregate_results(self, od_routing_results: List[ODRoutingResult], stops: List[Stop], routes: List[Route]) -> dict:
        kpi_report = {}

        # ── Placeholder: Connectivity cơ bản (Phase 1 POC) ────────────
        total = len(od_routing_results)
        connected = sum(1 for r in od_routing_results if r.is_connected)
        direct_only = sum(
            1 for r in od_routing_results
            if r.is_connected and r.best_itinerary and r.best_itinerary.total_transfers == 0
        )
        one_transfer = sum(
            1 for r in od_routing_results
            if r.is_connected and r.best_itinerary and r.best_itinerary.total_transfers == 1
        )

        kpi_report["connectivity"] = {
            "total_od_pairs": total,
            "connected_od_pairs": connected,
            "unconnected_od_pairs": total - connected,
            "connectivity_rate": round(connected / total, 4) if total > 0 else 0.0,
            "direct_connection_count": direct_only,
            "one_transfer_count": one_transfer,
        }

        # ── Hướng mở rộng (Phase 2) ───────────────────────────────────
        # kpi_report["kpi_a"] = KPIAService().calculate(od_routing_results, routes)
        # kpi_report["kpi_b"] = KPIBService().calculate(od_routing_results, stops, routes)

        # ── Chi tiết từng OD (để debug / export) ──────────────────────
        od_details = []
        for result in od_routing_results:
            best = result.best_itinerary
            od_details.append({
                "od_id": result.od_id,
                "origin_zone": result.origin_zone_id,
                "dest_zone": result.destination_zone_id,
                "demand": result.travel_demand,
                "feasible_itineraries_count": len(result.itineraries),
                "best_transfers": best.total_transfers if best else -1,
                "is_connected": result.is_connected,
            })
        kpi_report["detailed_od_evaluations"] = od_details

        return kpi_report
