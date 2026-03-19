import json

from application.ports.base_repository import EvaluationDataRepository
from application.services.odresult_cal_kpi import CalKPI
from application.services.produce_odresult import ProduceODResult
from domain.domain_service.kpi_service.kpi_A_service import KPIASpatialCoverageService
from domain.domain_service.kpi_service.kpi_service import Cricuity_index_caculate, Tranfer_rate_caculate


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
        self.od_result_producer = ProduceODResult()
        self.kpi_calculator = CalKPI()

    def execute(self, output_json_path: str):
        print("=== BẮT ĐẦU ĐÁNH GIÁ MẠNG LƯỚI XE BUÝT ===")

        # 1. Load Data
        stops, routes, zones, od_pairs = self.repository.load_network_and_demand()

        # 2. Preprocessing (Routing)
        print(f"[Preprocessing] Bắt đầu Routing cho {len(od_pairs)} OD Pairs...")
        valid_od_pairs = [od for od in od_pairs if od.origin_area.id != od.destination_area.id]
        od_routing_results = self.od_result_producer.produce_od_result(
            route_list=routes,
            stop_list=stops,
            zone_list=zones,
            od_pair_list=valid_od_pairs,
        )

        od_pair_map = {od.id: od for od in valid_od_pairs}
        for result in od_routing_results:
            od = od_pair_map.get(result.od_id)
            if od is None:
                continue
            result.origin_zone_id = od.origin_area.id
            result.destination_zone_id = od.destination_area.id
            result.travel_demand = od.travel_demand

        connected = sum(1 for r in od_routing_results if len(r.aggregated_itineraries) > 0)
        print(f"[Preprocessing] Hoàn tất: {connected}/{len(od_routing_results)} OD Pairs có hành trình kết nối.")

        # 3. KPI Calculate
        kpi_calculators = [
            Tranfer_rate_caculate(),
            Cricuity_index_caculate(),
            KPIASpatialCoverageService(zones=zones, stops=stops, stop_coverage_radius_m=500.0),
        ]

        od_kpi_results = []
        for od_result in od_routing_results:
            kpi_result = self.kpi_calculator.cal_kpi(
                od_routing_results=od_result,
                kpi_calculators=kpi_calculators,
                route_list=routes,
            )
            od_kpi_results.append(kpi_result)

        kpi_report = {"od_kpi_results": od_kpi_results}

        # 4. Export
        meta = {
            "total_od_pairs_evaluated": len(od_routing_results),
            "total_stops": len(stops),
            "total_routes": len(routes),
            "phase": "POC Phase 1",
        }
        self._export_json(kpi_report, output_json_path, meta)

        print("=== HOÀN TẤT ĐÁNH GIÁ ===")

    def _export_json(self, kpi_report: dict, output_json_path: str, meta: dict):
        print(f"[Export] Đang lưu kết quả vào {output_json_path}...")
        report = {
            "summary": meta,
            "kpi_report": kpi_report,
        }
        with open(output_json_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=4)
        print(f"[Export] Đã lưu xong.")
