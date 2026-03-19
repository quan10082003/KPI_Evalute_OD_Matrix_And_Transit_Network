import json
from typing import List

from application.base_repository import EvaluationDataRepository
from domain.entities_and_dataclass.domain_dataclass import ODRoutingResult
from domain.domain_service.routing_service.routing_service import find_routes

# Import từng KPI Domain Service tại đây khi chúng được triển khai.
# Ví dụ:
#   from domain.domain_service.kpi_service.kpi_A_service import KPIAService
#   from domain.domain_service.kpi_service.kpi_B_service import KPIBService


class KPIEvaluationApplication:
    """
    Application Service – điều phối luồng đánh giá KPI mạng lưới xe buýt.

    Luồng thực thi gồm 4 bước:
      1. Load data          : Tải mạng lưới & nhu cầu từ Repository.
      2. Preprocessing      : Routing – tìm hành trình khả thi cho từng OD pair.
      3. KPI Calculation    : Gọi từng Domain KPI Service, ghép kết quả thành dict.
      4. Export             : Xuất kết quả ra file JSON (Phase 2: trả response API).

    Việc gộp kết quả từ các KPI service thuộc trách nhiệm của Application layer
    (orchestration), không phải Domain layer (nghiệp vụ thuần túy).
    """

    def __init__(self, repository: EvaluationDataRepository):
        self.repository = repository

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def run_evaluation(self, output_json_path: str):
        print("=== BẮT ĐẦU ĐÁNH GIÁ MẠNG LƯỚI XE BUÝT ===")

        # ── Bước 1: Load Data ──────────────────────────────────────────
        stops, routes, zones, od_pairs = self.repository.load_network_and_demand()

        # ── Bước 2: Preprocessing (Routing) ───────────────────────────
        od_routing_results = self._preprocess(od_pairs, routes)

        # ── Bước 3: KPI Calculation ────────────────────────────────────
        # Application gọi từng KPI Domain Service rồi ghép kết quả.
        # Mỗi service trả về 1 dict ứng với nhóm KPI của nó.
        kpi_report = self._calculate_kpis(
            od_routing_results=od_routing_results,
            stops=stops,
            routes=routes,
        )

        # ── Bước 4: Export ─────────────────────────────────────────────
        # Phase 1: xuất ra file JSON.
        # Phase 2 (tương lai): trả kpi_report dưới dạng response cho API caller.
        self._export_json(
            kpi_report=kpi_report,
            output_json_path=output_json_path,
            meta={
                "total_od_pairs_evaluated": len(od_routing_results),
                "total_stops": len(stops),
                "total_routes": len(routes),
                "phase": "POC Phase 1",
            },
        )

        print("=== HOÀN TẤT ĐÁNH GIÁ ===")

    # ------------------------------------------------------------------
    # Private: Bước 2 – Preprocessing
    # ------------------------------------------------------------------

    def _preprocess(self, od_pairs, routes) -> List[ODRoutingResult]:
        """
        Chạy Routing Engine cho từng OD pair.
        Trả về danh sách ODRoutingResult chứa các hành trình khả thi.
        """
        results = []
        print(f"[Preprocessing] Bắt đầu Routing cho {len(od_pairs)} OD Pairs...")

        for index, od in enumerate(od_pairs):
            if od.origin_area.id == od.destination_area.id:
                continue

            itineraries = find_routes(od_pair=od, routes=routes)

            results.append(ODRoutingResult(
                od_id=od.id,
                origin_zone_id=od.origin_area.id,
                destination_zone_id=od.destination_area.id,
                travel_demand=od.travel_demand,
                itineraries=itineraries,
            ))

            if (index + 1) % 100 == 0:
                print(f"[Preprocessing] Đã xử lý {index + 1}/{len(od_pairs)} OD Pairs...")

        connected = sum(1 for r in results if r.is_connected)
        print(f"[Preprocessing] Hoàn tất: {connected}/{len(results)} OD Pairs có hành trình kết nối.")
        return results

    # ------------------------------------------------------------------
    # Private: Bước 3 – KPI Calculation (Orchestration)
    # ------------------------------------------------------------------

    def _calculate_kpis(self, od_routing_results, stops, routes) -> dict:
        """
        Application tự ghép kết quả từ các Domain KPI Service thành 1 dict.

        Mỗi KPI Service con trả về 1 dict ứng với nhóm KPI của nó.
        Application là nơi duy nhất biết cần gọi những service nào và ghép ra sao.

        Hướng mở rộng (Phase 2) – chỉ cần thêm dòng gọi service mới:
            kpi_report["kpi_A"] = KPIAService().calculate(od_routing_results, routes)
            kpi_report["kpi_B"] = KPIBService().calculate(od_routing_results, stops, routes)
        """
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

    # ------------------------------------------------------------------
    # Private: Bước 4 – Export
    # ------------------------------------------------------------------

    def _export_json(self, kpi_report: dict, output_json_path: str, meta: dict):
        """
        Phase 1: ghi kết quả KPI ra file JSON.
        Phase 2 (tương lai): trả kpi_report về dưới dạng JSON response cho frontend.
        """
        print(f"[Export] Đang lưu kết quả vào {output_json_path}...")
        report = {
            "summary": meta,
            "kpi_report": kpi_report,
        }
        with open(output_json_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=4)
        print(f"[Export] Đã lưu xong.")
