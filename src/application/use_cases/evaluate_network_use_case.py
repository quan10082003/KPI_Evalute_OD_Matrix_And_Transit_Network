import json
from typing import List

from application.ports.base_repository import EvaluationDataRepository
from application.services.kpi_aggregator_service import KPIAggregatorService
from domain.entities_and_dataclass.domain_dataclass import ODRoutingResult
from domain.domain_service.routing_service.routing_service import find_routes


class EvaluateNetworkUseCase:
    """
    Use Case phục vụ yêu cầu: Đánh giá toàn bộ mạng lưới xe buýt.
    
    Luồng thực thi:
      1. Load data
      2. Preprocessing (Routing)
      3. KPI Aggregation
      4. Export
    """

    def __init__(self, repository: EvaluationDataRepository):
        self.repository = repository
        self.kpi_aggregator = KPIAggregatorService()

    def execute(self, output_json_path: str):
        print("=== BẮT ĐẦU ĐÁNH GIÁ MẠNG LƯỚI XE BUÝT ===")

        # 1. Load Data
        stops, routes, zones, od_pairs = self.repository.load_network_and_demand()

        # 2. Preprocessing (Routing)
        od_routing_results = self._preprocess(od_pairs, routes)

        # 3. KPI Aggregation
        kpi_report = self.kpi_aggregator.aggregate_results(
            od_routing_results=od_routing_results,
            stops=stops,
            routes=routes,
        )

        # 4. Export
        meta = {
            "total_od_pairs_evaluated": len(od_routing_results),
            "total_stops": len(stops),
            "total_routes": len(routes),
            "phase": "POC Phase 1",
        }
        self._export_json(kpi_report, output_json_path, meta)

        print("=== HOÀN TẤT ĐÁNH GIÁ ===")

    def _preprocess(self, od_pairs, routes) -> List[ODRoutingResult]:
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

    def _export_json(self, kpi_report: dict, output_json_path: str, meta: dict):
        print(f"[Export] Đang lưu kết quả vào {output_json_path}...")
        report = {
            "summary": meta,
            "kpi_report": kpi_report,
        }
        with open(output_json_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=4)
        print(f"[Export] Đã lưu xong.")
