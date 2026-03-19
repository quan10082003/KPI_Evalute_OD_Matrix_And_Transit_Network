import json
from typing import List

from application.base_repository import EvaluationDataRepository
from domain.entities_and_dataclass.domain_dataclass import ODRoutingResult
from domain.domain_service.routing_service.routing_service import find_routes
from domain.domain_service.kpi_service.kpi_service import KPIService


class KPIEvaluationApplication:
    """
    Application Service – điều phối luồng đánh giá KPI mạng lưới xe buýt.

    Luồng thực thi gồm 4 bước:
      1. Load data          : Tải mạng lưới & nhu cầu từ Repository.
      2. Preprocessing      : Routing – tìm hành trình khả thi cho từng OD pair.
      3. KPI Calculation    : Gọi các Domain KPI Service, tổng hợp kết quả thành dict.
      4. Export             : Xuất kết quả ra file JSON (Phase 2: trả response API).
    """

    def __init__(self, repository: EvaluationDataRepository):
        self.repository = repository
        self.kpi_service = KPIService()

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
        kpi_report: dict = self.kpi_service.calculate_network_kpis(
            od_routing_results=od_routing_results,
            stops=stops,
            routes=routes,
        )

        # ── Bước 4: Export ─────────────────────────────────────────────
        # Phase 1: xuất ra file JSON.
        # Phase 2 (tương lai): trả kpi_report về dưới dạng response cho API caller.
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
    # Private helpers
    # ------------------------------------------------------------------

    def _preprocess(self, od_pairs, routes) -> List[ODRoutingResult]:
        """
        Bước Tiền xử lý: chạy Routing Engine cho từng OD pair.
        Trả về danh sách ODRoutingResult chứa các hành trình khả thi.
        """
        results = []
        print(f"[Preprocessing] Bắt đầu Routing cho {len(od_pairs)} OD Pairs...")

        for index, od in enumerate(od_pairs):
            # Bỏ qua các cặp OD cùng vùng (chưa hỗ trợ)
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

    def _export_json(self, kpi_report: dict, output_json_path: str, meta: dict):
        """
        Bước Export: ghi kết quả KPI ra file JSON.
        Phase 2 (tương lai): hàm này sẽ được thay thế / bổ sung bằng
        endpoint trả về kpi_report dưới dạng JSON response cho frontend.
        """
        print(f"[Export] Đang lưu kết quả vào {output_json_path}...")
        report = {
            "summary": meta,
            "kpi_report": kpi_report,
        }
        with open(output_json_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=4)
        print(f"[Export] Đã lưu xong.")
