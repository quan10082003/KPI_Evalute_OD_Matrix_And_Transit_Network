from enum import Enum
from typing import List, Set
from dataclasses import dataclass
import numpy as np

@dataclass
class Direction(Enum):
    INBOUND = "inbound"
    OUTBOUND = "outbound"

@dataclass
class Point:
    lat: float # Vi do
    lon: float # Kinh do
    @property
    def distance_to(self, other: 'Point') -> float:
        return np.sqrt((self.lat - other.lat)**2 + (self.lon - other.lon)**2)
    @property
    def distance_to_straight_line(self, line_start_point: 'Point', line_end_point: 'Point') -> float:
        return np.sqrt((self.lat - line_start_point.lat)**2 + (self.lon - line_start_point.lon)**2)


@dataclass
class Leg:
    """Đại diện cho 1 chặng đi trên 1 tuyến."""
    route_ref_id: str
    board_stop_id: str
    alight_stop_id: str

@dataclass
class Itinerary:
    """Đại diện cho 1 hành trình từ Origin đến Destination."""
    legs: List[Leg]
    @property
    def total_transfers(self) -> int:
        return len(self.legs) - 1
    @property
    def set_origin_stops_id(self) -> Set[str]:
        if not self.legs: return set()
        # Chỉ lấy các bến lên xe của chặng ĐẦU TIÊN
        return self.legs[0].board_stop_id    
    @property
    def set_destination_stops_id(self) -> Set[str]:
        if not self.legs: return set()
        # Chỉ lấy các bến xuống xe của chặng CUỐI CÙNG
        return self.legs[-1].alight_stop_id


@dataclass(frozen=True)
class AggregatedLeg:
    """Đại diện cho 1 chặng đi TỔNG HỢP trên 1 tuyến."""
    route_ref_id: str
    possible_board_stop_ids: Set[str]  # Tập các bến CÓ THỂ lên
    possible_alight_stop_ids: Set[str] # Tập các bến CÓ THỂ xuống

@dataclass(frozen=True)
class AggregatedItinerary:
    """Đại diện cho 1 CÁCH ĐI TỔNG HỢP (Hyperpath) từ Origin đến Destination."""
    legs: List[AggregatedLeg]
    @property
    def total_transfers(self) -> int:
        return len(self.legs) - 1
    @property
    def set_origin_stops_id(self) -> Set[str]:
        if not self.legs: return set()
        # Chỉ lấy các bến lên xe của chặng ĐẦU TIÊN
        return self.legs[0].possible_board_stop_ids    
    @property
    def set_destination_stops_id(self) -> Set[str]:
        if not self.legs: return set()
        # Chỉ lấy các bến xuống xe của chặng CUỐI CÙNG
        return self.legs[-1].possible_alight_stop_ids

