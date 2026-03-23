# HƯỚNG DẪN REFACTOR TOÀN DIỆN DỰ ÁN (REFACTOR GUIDE)
*(Mục tiêu: Xây dựng bản MVP tính toán OD Result từ Database, tuân thủ CHUẨN MỰC "Cosmic Python" - Architecture Patterns with Python)*

Bạn đã nhận ra một điểm rất chính xác: Cuốn sách **Cosmic Python** không dùng các thuật ngữ `Application` hay `Infrastructure`. Cuốn sách sử dụng hệ thống thuật ngữ đặc trưng dựa trên kiến trúc **Ports and Adapters (Hexagonal Architecture)** kết hợp với **DDD**:
1. `domain`: Lõi nghiệp vụ (Models, Domain Services).
2. `adapters`: Các chi tiết hạ tầng (Database/ORM, HTTP Clients, Thư viện bên ngoài như Shapely).
3. `service_layer`: Lớp dịch vụ ứng dụng (Use Cases, Unit of Work, Message Bus).
4. `entrypoints`: Đầu vào của hệ thống (API, CLI, `main.py`).

Dưới đây là cấu trúc thư mục mới nhất và cách xử lý thư viện `Shapely/Geopy` theo chuẩn Cosmic Python.

---

## 1. CẤU TRÚC THƯ MỤC CHUẨN "COSMIC PYTHON"

```text
src/
├── domain/                      # PURE PYTHON - Không chứa bất cứ thư viện ngoài nào
│   ├── models.py                # Chứa Entities (Stop, Route), Value Objects (Point)
│   ├── services.py              # Domain Services (Thuật toán tìm đường cốt lõi)
│   ├── events.py                # Các Domain Events (nếu dùng Message Bus)
│   └── ports.py                 # Abstract Interfaces (Ví dụ: IGeometryCalculator)
│
├── adapters/                    # Nơi giao tiếp với THẾ GIỚI BÊN NGOÀI
│   ├── repository.py            # Abstract + Implementation của Repository (Lấy data từ DB)
│   ├── orm.py                   # Ánh xạ (Mapping) từ SQL/SQLAlchemy sang Domain Models
│   └── geospatial.py           # ADAPTER CHO SHAPELY! Chứa code thật gọi Shapely/Geopy
│
├── service_layer/               # ĐIỀU PHỐI (ORCHESTRATION)
│   ├── services.py              # Các hàm chạy logic (Trước gọi là Use Case / ProduceODResult)
│   ├── unit_of_work.py          # Abstract + Implementation của UoW
│   └── messagebus.py            # (Tùy chọn) Điều phối Command/Events
│
├── entrypoints/                 # ĐẦU VÀO CỦA APP
│   └── cli_main.py              # Chạy script từ terminal (main.py trước đây)
│
└── bootstrap.py                 # DEPENDENCY INJECTION: Nơi buộc Adapters vào Service Layer
```

---

## 2. GIẢI QUYẾT VẤN ĐỀ "THƯ VIỆN SHAPELY ĐỂ Ở ĐÂU?"

Trong Cosmic Python, nếu `Domain` cần tính toán phức tạp phụ thuộc thư viện C++ (như Shapely) thì thiết kế như sau:

**Bước 1: Tầng `domain/ports.py` định nghĩa Giao diện (Port) bằng Pure Python.**
```python
import abc
from domain.models import Point, Zone

class IGeometryCalculator(abc.ABC):
    @abc.abstractmethod
    def get_distance(self, p1: Point, p2: Point) -> float:
        pass
        
    @abc.abstractmethod
    def is_point_in_zone(self, p: Point, zone: Zone) -> bool:
        pass
```

**Bước 2: Tầng `adapters/geospatial.py` gọi thư viện thực (Adapter).**
*(Đây là Infrastructure/Adapter vì nó là công nghệ bên ngoài, thay đổi được tùy ý mà không chạm vào Domain)*
```python
import shapely.geometry
import geopy.distance
from domain.ports import IGeometryCalculator

class ShapelyGeometryCalculator(IGeometryCalculator):
    def get_distance(self, p1, p2):
        return geopy.distance.geodesic((p1.lat, p1.lon), (p2.lat, p2.lon)).meters
        
    def is_point_in_zone(self, p, zone):
        # build Polygon from zone.boundary points using shapely
        # return boolean
        pass
```

**Bước 3: Tầng `domain/services.py` (Thuật toán Routing) nhận Port vào để dùng.**
```python
class DirectConnectionEngine:
    # Nhận Port qua Injection thay vì tự import
    def __init__(self, geo_calculator: IGeometryCalculator):
        self.geo_calculator = geo_calculator

    def find_routes(self, ...):
        # Dùng geo_calculator trong hàm thuật toán
        dist = self.geo_calculator.get_distance(p1, p2) 
```

---

## 3. CHI TIẾT TỪNG LỚP TRONG BẢN REFACTOR

### 3.A. Tầng `domain/`
1. **`models.py`**:
   - Chứa `Stop`, `Route`, `Zone`, `ODPair`.
   - **Thay đổi quan trọng:** `Route.stops_seq` trở thành mảng `List[str]` (lưu mảng `stop_id`) để tuân thủ DDD (Entity tham chiếu đến nhau qua ID). Việc này giúp Database cực nhẹ và không phình RAM.
2. **`services.py`**:
   - Bưng cái lô-gíc của `routing_service/core_engine.py` cũ vứt vào đây. Đây là Domain Service. Nó nhận danh sách (từ điển) các `Stop` và thực thi toán học.

### 3.B. Tầng `adapters/`
1. **`repository.py`**: 
   - Không chứa bất kỳ lô-gíc Routing nào!
   - Gồm Interface: `class AbstractNetworkRepository(abc.ABC):`
   - Gồm Implementation cho MVP: `class PostgresNetworkRepository(AbstractNetworkRepository):` (Dùng SQL query thẳng ra data, hoặc nếu chưa viết SQL thì giữ file Mock tạo lại object Python).
2. **`orm.py`** (Nếu xài DB thật): Viết bảng SQLAlchemy và ánh xạ nó vào `domain.models`.
3. **`geospatial.py`**: Như ví dụ Adapter ở trên.

### 3.C. Tầng `service_layer/`
1. **`unit_of_work.py`**: Tạo `AbstractUnitOfWork` sở hữu `network_repo` và `od_repo`.
2. **`services.py`**:
   - Bác bỏ Use Case file. Tại đây viết các hàm service functions:
   ```python
   def evaluate_network_for_od(uow: AbstractUnitOfWork, engine: DirectConnectionEngine, ...):
       with uow:
           routes = uow.network.get_all_routes()
           # ... code gọi engine.find_routes chạy thuật toán
           # uow.commit() # Nếu muốn lưu lại kết quả vào DB
   ```

### 3.D. Tập tin TRỌNG YẾU: `bootstrap.py`
Tách biệt toàn bộ khởi tạo ra một chỗ. File `main.py` sẽ nhập (vô) hàm từ đây.
```python
# bootstrap.py
from adapters import repository, geospatial
from service_layer import services, unit_of_work
from domain import services as domain_services

def bootstrap() -> dict: # Hoặc trả về messagebus
    geo_calculator = geospatial.ShapelyGeometryCalculator()
    routing_engine = domain_services.DirectConnectionEngine(geo_calculator)
    uow = unit_of_work.SqlAlchemyUnitOfWork()
    
    return {
        'uow': uow,
        'routing_engine': routing_engine
    }
```

## 4. BẢNG TỪ ĐIỂN REFACTOR (NAMING REFACTOR)

| Tên Cũ (Code Smell) | Đổi Sang Chuẩn Mới | Vị Trí Thư Mục Mới |
|:---|:---|:---|
| `Tranfer_rate_caculate` | `TransferRateKpiCalculator` | Tùy chọn: `domain/services.py` hoặc 1 module KPI |
| `domain_class.py` | `models.py` | Nằm trong `domain/models.py` |
| `ProduceODResult` | Lược bỏ, chuyển hàm sang `service_layer/services.py` | Tầng điều phối của Service Layer |
| `cottbus_xml_repository.py`| Tách thành `repository.py` và `xml_adapter.py` | Nằm trong `adapters/` |
| `geopy / shapely` in Models | Gỡ toàn bộ khỏi Models. Chuyển vào `adapters/geospatial.py` | Gọi qua interface định nghĩa ở `domain/ports.py` |
