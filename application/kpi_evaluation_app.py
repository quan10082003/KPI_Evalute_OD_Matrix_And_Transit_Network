import json
from infrastructure.repositories.base_repository import EvaluationDataRepository
from domain.domain_service.routing_service.core_engine import DirectConnectionRoutingEngine, OneTransferRoutingEngine
from domain.domain_service.routing_service.filter_strategy import OptimalWalkingDistanceFilter, OneTransferOptimalFilter

class KPIEvaluationApplication:
    """
    Application Service thực thi luồng chính:
    1. Lấy dữ liệu từ Repository (network, demand).
    2. Khởi tạo Core Engine để filter tuyến đường cho từng OD.
    3. Tính KPI (sẽ phát triển ở phase sau).
    4. Xuất báo cáo.
    """
    def __init__(self, repository: EvaluationDataRepository):
        self.repository = repository
        
        # Setup Core Routing Engines
        # Phase này ưu tiên POC nên hardcode setup các Engine có sẵn trong domain
        self.direct_engine = DirectConnectionRoutingEngine(filter_strategy=OptimalWalkingDistanceFilter())
        self.transfer_engine = OneTransferRoutingEngine(filter_strategy=OneTransferOptimalFilter())

    def run_evaluation(self, output_json_path: str):
        print("=== BẮT ĐẦU ĐÁNH GIÁ MẠNG LƯỚI XE BUÝT ===")
        # 1. Load Data
        stops, routes, zones, od_pairs = self.repository.load_network_and_demand()
        
        print(f"Bắt đầu tìm Itineraries cho {len(od_pairs)} OD Pairs...")
        
        # 2. Tìm kiếm Itineraries (Routing)
        evaluation_results = []
        for index, od in enumerate(od_pairs):
            
            # TODO: Ở giai đoạn này nếu O và D nằm trong cùng Zone thì Engine có thể throw lỗi chưa hỗ trợ.
            if od.origin_area.id == od.destination_area.id:
                continue
                
            itineraries = self.direct_engine.find_feasible_itineraries(od_pair=od, routes=routes)
            # Nếu không tìm thấy Direct, tìm OneTransfer
            if not itineraries:
                itineraries = self.transfer_engine.find_feasible_itineraries(od_pair=od, routes=routes)
                
            # Log results
            if itineraries:
                found = len(itineraries)
                transfers = itineraries[0].total_transfers if len(itineraries) > 0 else 0
                evaluation_results.append({
                    "od_id": od.id,
                    "origin_zone": od.origin_area.id,
                    "dest_zone": od.destination_area.id,
                    "demand": od.travel_demand,
                    "feasible_itineraries_count": found,
                    "sample_transfers": transfers,
                    "note": "Phát hiện tuyến đường thành công."
                })
            else:
                 evaluation_results.append({
                    "od_id": od.id,
                    "origin_zone": od.origin_area.id,
                    "dest_zone": od.destination_area.id,
                    "demand": od.travel_demand,
                    "feasible_itineraries_count": 0,
                    "sample_transfers": -1,
                    "note": "Không có tuyến Public Transit nào kết nối."
                })
                
            if (index + 1) % 100 == 0:
                print(f"Đã xử lý {index + 1}/{len(od_pairs)} OD Pairs...")
                
        # 3. Phối hợp tính toán KPI (Orchestration)
        # Tuyệt đối KHÔNG viết công thức tính KPI ở đây.
        # Ở bước này, Application sẽ truyền danh sách Itineraries vừa tìm được 
        # vào các Domain Service (nằm ở domain/domain_service/kpi_service) để tính các chỉ số.
        # Ví dụ: kpi_results = self.kpi_service.calculate_network_kpis(evaluation_results)
        summary = {
            "total_od_pairs_evaluated": len(evaluation_results),
            "total_stops": len(stops),
            "total_routes": len(routes),
            "phase": "POC Phase 1"
        }
                
        # 4. Xuất file kết quả JSON
        print(f"Đang lưu kết quả vào {output_json_path}...")
        report = {
            "summary": summary,
            "detailed_od_evaluations": evaluation_results
        }
        with open(output_json_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=4)
            
        print("=== HOÀN TẤT ĐÁNH GIÁ ===")
