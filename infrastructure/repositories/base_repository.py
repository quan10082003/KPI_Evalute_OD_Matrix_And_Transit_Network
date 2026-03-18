from abc import ABC, abstractmethod
from typing import List, Tuple
from domain.entities_and_dataclass.domain_class import Stop, Route, Zone, ODPair

class EvaluationDataRepository(ABC):
    """
    Interface Repository tải dữ liệu đầu vào cho hệ thống đánh giá KPI.
    Giúp che giấu chi tiết lưu trữ (XML, DB, API API,...).
    """

    @abstractmethod
    def load_network_and_demand(self) -> Tuple[List[Stop], List[Route], List[Zone], List[ODPair]]:
        """
        Tải toàn bộ mạng lưới và nhu cầu đi lại.
        :return: Tuple chứa (Danh sách Stops, Danh sách Routes, Danh sách Zones, Danh sách ODPairs)
        """
        pass
