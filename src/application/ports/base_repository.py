from abc import ABC, abstractmethod
from typing import List, Tuple
from domain.entities_and_dataclass.domain_class import Stop, Route, Zone, ODPair


class EvaluationDataRepository(ABC):
    """
    Interface (Port) của Application Layer – định nghĩa hợp đồng tải dữ liệu đầu vào.
    Application Service phụ thuộc vào interface này, KHÔNG phụ thuộc vào chi tiết cài đặt.

    Các implementation (Adapter) cụ thể nằm ở Infrastructure Layer.
    """

    @abstractmethod
    def load_network_and_demand(self) -> Tuple[List[Stop], List[Route], List[Zone], List[ODPair]]:
        """
        Tải toàn bộ mạng lưới giao thông và ma trận nhu cầu đi lại.
        :return: Tuple (stops, routes, zones, od_pairs)
        """
        pass
