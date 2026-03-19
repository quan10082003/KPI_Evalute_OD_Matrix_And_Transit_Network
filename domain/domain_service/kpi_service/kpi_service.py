from typing import List

from domain.entities_and_dataclass.domain_dataclass import ODRoutingResult
from domain.entities_and_dataclass.domain_class import Stop, Route

# Import các KPI service con tại đây khi chúng được triển khai.
# Ví dụ:
# from domain.domain_service.kpi_service.kpi_B_service import KPIBService


class KPIService:
    """
    KPI Service tổng hợp (Aggregate Service).

    Vai trò: gọi từng Domain KPI Service con, thu thập kết quả,
    sau đó trả về một dict tổng hợp để Application export/trả về API.

    Mỗi nhóm KPI sẽ được triển khai thành 1 Domain Service riêng biệt:
      - kpi_B_service.py   : KPI nhóm B (...)
      - kpi_C_service.py   : KPI nhóm C (...)
      - ...

    Application KHÔNG gọi trực tiếp từng KPI service con.
    Application chỉ gọi KPIService.calculate_network_kpis().
    """

    def calculate_network_kpis(
        self,
        od_routing_results: List[ODRoutingResult],
        stops: List[Stop],
        routes: List[Route],
    ) -> dict:
        """
        Tính toán toàn bộ bộ KPI mạng lưới xe buýt.

        :param od_routing_results: Kết quả Preprocessing – danh sách hành trình tìm được cho mỗi OD.
        :param stops: Danh sách tất cả điểm dừng trong mạng lưới.
        :param routes: Danh sách tất cả tuyến xe trong mạng lưới.
        :return: dict chứa kết quả KPI theo từng nhóm, sẵn sàng để serialize.

        --- Hướng mở rộng (Phase 2) ---
        Khi có thêm KPI service:
          kpi_b = KPIBService().calculate(od_routing_results, routes)
          ...
          Trả về dict tổng hợp từ kết quả các service con.
        """

        # ── Placeholder: Summary cơ bản (Phase 1 POC) ─────────────────
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

        connectivity_rate = round(connected / total, 4) if total > 0 else 0.0

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

        return {
            # ── Nhóm KPI: Khả năng tiếp cận (Connectivity) ────────────
            "connectivity": {
                "total_od_pairs": total,
                "connected_od_pairs": connected,
                "unconnected_od_pairs": total - connected,
                "connectivity_rate": connectivity_rate,
                "direct_connection_count": direct_only,
                "one_transfer_count": one_transfer,
            },
            # ── Placeholder cho các nhóm KPI sẽ phát triển ────────────
            # "kpi_B": KPIBService().calculate(od_routing_results, routes),
            # "kpi_C": KPICService().calculate(od_routing_results, stops, routes),

            # ── Chi tiết OD để kiểm tra/debug ─────────────────────────
            "detailed_od_evaluations": od_details,
        }
