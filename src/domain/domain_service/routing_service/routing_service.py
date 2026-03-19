from typing import List
from domain.entities_and_dataclass.domain_dataclass import Itinerary
from domain.entities_and_dataclass.domain_class import Route, ODPair

from domain.domain_service.routing_service.filter_strategy import OptimalWalkingDistanceFilter, OneTransferOptimalFilter
from domain.domain_service.routing_service.core_engine import DirectConnectionRoutingEngine, OneTransferRoutingEngine

def find_routes(od_pair: ODPair, routes: List[Route]) -> List[Itinerary]:
    """
    Facade API cho Routing Module.
    Khởi tạo Core Engine cùng với Strategy Filter tốt nhất theo mặc định,
    sau đó trả về kết quả 0-transfer hoặc 1-transfer Itineraries.
    """
    # 1. Khởi tạo chiến lược lọc
    walking_distance_filter_0_transfer = OptimalWalkingDistanceFilter()
    walking_distance_filter_1_transfer = OneTransferOptimalFilter()
    
    # 2. Khởi tạo Routing Engine và Tiêm (Inject) bộ lọc vào
    engine_0_transfer = DirectConnectionRoutingEngine(filter_strategy=walking_distance_filter_0_transfer)
    engine_1_transfer = OneTransferRoutingEngine(filter_strategy=walking_distance_filter_1_transfer)
    
    # 3. Yêu cầu các Engine tính toán
    itineraries_0 = engine_0_transfer.find_feasible_itineraries(od_pair=od_pair, routes=routes)
    itineraries_1 = engine_1_transfer.find_feasible_itineraries(od_pair=od_pair, routes=routes)
    
    # 4. Trả về tổng hợp 2 chặng
    return itineraries_0 + itineraries_1
