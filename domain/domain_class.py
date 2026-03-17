from enum import Enum
from typing import List
from dataclasses import dataclass

class Direction(Enum)
    INBOUND = "inbound"
    OUTBOUND = "outbound"

@dataclass
class Point :
    lat: float # Vi do
    lon: float # Kinh do

class Stop:
    id: str
    coord: Point

class Route:
    id: str
    direction: Direction
    shape: List(Point)
    stops_seq: List(Stop) # list cac stop
    # phan biet cac chieu ntn

class Zone:
    id: str
    boundary: List(Point)
    centroid: Point

class ODPair:
    id: str
    origin_area: Zone
    destination_area: Zone
    travel_demand: int

khoang cach hai point
do truc tiep tu stop A den stop B trong 1 Route
tim stop cua 1 route gan 1 diem nhat






