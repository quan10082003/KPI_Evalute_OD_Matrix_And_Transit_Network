from enum import Enum
from typing import List, Set
from dataclasses import dataclass
import geopy
import geopy.distance
import shapely.geometry

@dataclass
class Direction(Enum):
    INBOUND = "inbound"
    OUTBOUND = "outbound"

@dataclass
class Point:
    lat: float # Vi do
    lon: float # Kinh do
    
    @property
    def as_geopy(self):
        return geopy.Point(self.lat, self.lon)
        
    @property
    def as_shapely(self):
        return shapely.geometry.Point(self.lon, self.lat)
        
    def distance_to(self, other: 'Point') -> float:
        # Tính khoảng cách theo đại hình học cầu (meters)
        return geopy.distance.geodesic(self.as_geopy, other.as_geopy).meters
        
    def distance_to_straight_line(self, line_start_point: 'Point', line_end_point: 'Point') -> float:
        # Sử dụng đối tượng đường thẳng của Shapely
        line = shapely.geometry.LineString([line_start_point.as_shapely, line_end_point.as_shapely])
        # Khoảng cách ở đây là theo hệ tọa độ độ (degrees). 
        # Để chính xác ra mét, sau này có thể chiếu sang hệ UTM (CRS EPSG:32648 cho VN).
        return self.as_shapely.distance(line)


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


@dataclass
class ODRoutingResult:
    """
    Kết quả của bước Tiền xử lý (Preprocessing) cho 1 cặp OD.
    Đây là đầu ra của Routing Engine và là đầu vào cho KPI Service.
    """
    od_id: str
    origin_zone_id: str
    destination_zone_id: str
    travel_demand: int
    itineraries: List[Itinerary]  # Danh sách các hành trình khả thi tìm được

    @property
    def is_connected(self) -> bool:
        """True nếu tìm được ít nhất 1 hành trình kết nối OD."""
        return len(self.itineraries) > 0

    @property
    def best_itinerary(self) -> 'Itinerary | None':
        """Trả về hành trình tốt nhất (ưu tiên ít transfer nhất)."""
        if not self.itineraries:
            return None
        return min(self.itineraries, key=lambda it: it.total_transfers)
