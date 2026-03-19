from typing import List, Optional
from domain.entities_and_dataclass.domain_class import Route, Stop, Zone, ODPair
from domain.entities_and_dataclass.domain_dataclass import ODRoutingResult
from domain.domain_service.routing_service.filter_strategy import OptimalWalkingDistanceFilter, OneTransferOptimalFilter
from domain.domain_service.routing_service.core_engine import DirectConnectionRoutingEngine, OneTransferRoutingEngine

class ProduceODResult:
    def __init__(self):
        # Tối ưu hóa: Khởi tạo các engine và filter 1 lần duy nhất trong constructor
        # thay vì khởi tạo lại liên tục trong vòng lặp của hàng ngàn OD pair.
        self.wd_filter_0 = OptimalWalkingDistanceFilter()
        self.wd_filter_1 = OneTransferOptimalFilter()
        self.engine_0_transfer = DirectConnectionRoutingEngine(filter_strategy=self.wd_filter_0)
        self.engine_1_transfer = OneTransferRoutingEngine(filter_strategy=self.wd_filter_1)

    def produce_od_result(self,
                          route_list: Optional[List[Route]] = None,
                          stop_list: Optional[List[Stop]] = None,
                          zone_list: Optional[List[Zone]] = None,
                          od_pair_list: Optional[List[ODPair]] = None) -> List[ODRoutingResult]:

        od_routing_results = []
        
        if route_list is None: route_list = []
        if od_pair_list is None: od_pair_list = []
        
        for od_pair in od_pair_list:
           # Lấy Aggregated Itineraries (Chặng đi tổng hợp)
           agg_iti_0 = self.engine_0_transfer._find_aggregated_itineraries(od_pair=od_pair, routes=route_list)
           agg_iti_1 = self.engine_1_transfer._find_aggregated_itineraries(od_pair=od_pair, routes=route_list)
           agg_iti = agg_iti_0 + agg_iti_1
           
           # Lấy Represent Itineraries (Cách đi chi tiết)
           # Lưu ý: Không dùng find_routes() của routing_service.py ở đây vì hàm đó 
           # khởi tạo engine mới mỗi lần gọi làm mất đi tốc độ thực thi trong vòng lặp.
           rep_iti_0 = self.engine_0_transfer.find_feasible_itineraries(od_pair=od_pair, routes=route_list)
           rep_iti_1 = self.engine_1_transfer.find_feasible_itineraries(od_pair=od_pair, routes=route_list)
           represent_itineraries = rep_iti_0 + rep_iti_1

           od_routing_results.append(ODRoutingResult(
               od_id=od_pair.id, 
               aggregated_itineraries=agg_iti, 
               represent_itineraries=represent_itineraries
           ))
           
        return od_routing_results
        