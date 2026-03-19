from typing import List

from domain.entities_and_dataclass.domain_dataclass import Itinerary
from domain.entities_and_dataclass.domain_class import Route, ODPair

from domain.domain_service.routing_service.filter_strategy import OptimalWalkingDistanceFilter, OneTransferOptimalFilter
from domain.domain_service.routing_service.core_engine import DirectConnectionRoutingEngine, OneTransferRoutingEngine


def find_routes(od_pair: ODPair, routes: List[Route]) -> List[Itinerary]:
    """
    Facade API của Routing Module.

    Chiến lược fallback theo thứ tự ưu tiên:
      1. Tìm hành trình trực tiếp (0-transfer).
      2. Nếu không có, tìm hành trình 1 lần đổi tuyến (1-transfer).

    Trả về danh sách Itinerary rỗng nếu không tìm được hành trình nào.
    """
    direct_engine = DirectConnectionRoutingEngine(
        filter_strategy=OptimalWalkingDistanceFilter()
    )
    transfer_engine = OneTransferRoutingEngine(
        filter_strategy=OneTransferOptimalFilter()
    )

    # Ưu tiên Direct trước
    itineraries = direct_engine.find_feasible_itineraries(od_pair=od_pair, routes=routes)

    # Fallback sang 1-transfer nếu không có trực tiếp
    if not itineraries:
        itineraries = transfer_engine.find_feasible_itineraries(od_pair=od_pair, routes=routes)

    return itineraries
