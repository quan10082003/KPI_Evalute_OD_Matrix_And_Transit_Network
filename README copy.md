# Báo cáo Phân tích và Đọc hiểu Mã nguồn Dự án `KPI_Evaluate` (Đã nâng cấp)

Dự án này (`KPI_Evaluate`) thuộc về công việc đánh giá các Chỉ số hiệu suất cốt lõi (KPI) liên quan đến Dữ liệu Ma trận Origin-Destination (OD - Điểm đi và Điểm đến) và Dữ liệu Mạng lưới Xe buýt (Transit Network).

Dưới đây là các diễn giải chi tiết về cấu trúc mã nguồn, ý nghĩa của các file và luồng logic thu thập được từ kiến trúc hệ thống **Domain-Driven Design (DDD)** đã được tinh biến và tối ưu hóa hiệu năng trong thư mục `domain/`.

## 1. Tổng quan cấu trúc dự án (Kiến trúc Mới)
Hệ thống nay đã thiết lập phân rã rõ ràng giữa Pure Data, Domain Model (Entities), Utility Services và Core Logic Services (như Routing Engine phân lớp).
Các tệp và phân vùng mã nguồn chính bao gồm:
* `domain/entities_and_dataclass/domain_dataclass.py`: Chứa các cấu trúc dữ liệu thuần túy bằng thư viện `@dataclass` lõi.
* `domain/entities_and_dataclass/domain_class.py`: Lớp thực thể (Domain Models) kết hợp tương tác Hình học nâng cao (Geometry/Topology) dựa trên thư viện Shapely siêu tốc và Geopy.
* `domain/domain_service/spatial_service.py`: Chứa các tính toán phi trạng thái (Stateless Utility Service) chuyên xử lý giao cắt không gian, lọc các tuyến/bến qua Zone, và đo đếm chỉ số vòng vèo (Circuity Index).
* Phân vùng `domain/domain_service/routing_service/`: Tổ hợp Module tính toán Lộ trình chuyên sâu:
  * `core_engine.py`: Các lõi tìm đường (0-transfer, 1-transfer) dựa trên tập hợp và Hash Map $O(1)$.
  * `filter_strategy.py`: Abstract Layer và các Concrete Class để bóc tách lộ trình (Unroll, Filter).
  * `routing_service.py`: Lớp Facade tổng quan bọc ngoài toàn bộ logic Routing.

## 2. Diễn giải chi tiết các Phân mảng 

### 2.1. File `domain_dataclass.py` (Cấu trúc Vật lý Nhẹ)
Mô-đun định nghĩa các cấu trúc dữ liệu cơ sở không mang nghiệp vụ tìm đường.
* **`Point`:** Biểu diễn điểm tọa độ (Kinh độ/Vĩ độ). Đã tích hợp tính toán khoảng cách thực địa qua thư viện `geopy` (Hàm đại hình học cầu - Geodesic - cực kỳ chính xác) thay cho định lý Pytago tạo sai số.
* **`Leg` & `Itinerary`:** Đại diện cho một "chặng" di chuyển một lần và "hành trình" hoàn chỉnh.
* **`AggregatedLeg` & `AggregatedItinerary`:** Mô hình nén giữ thông tin của **Tập hợp bến** (Possible Board/Alight Stops) chống lại sự bùng nổ dữ liệu (Hyperpath) do tính chất tổ hợp của các Trạm xe buýt.

### 2.2. File `domain_class.py` (Thực Thể Miền Thông Minh)
Mô-đun định nghĩa các đối tượng thông minh có kèm dữ liệu Hình học Không gian Vector (GeoSpatial Vector).
* **`Zone`:** O/D Area. Đã cập nhật áp dụng lõi C++ của Shapely (Phương thức `.contains()`) để check tọa độ cực nhanh thay vì thuật toán Ray Casting thủ công.
* **`Route`:** Lưu giữ hình dáng thật (Shape => LineString). 
  * **Đo khoảng cách trắc địa:** Đã hoàn thiện phương thức cắt xén (Substring) LineString dọc theo đường xe buýt bằng Shapely và tính toán khoảng cách chính xác bề mặt cong chiều dài thực (Geopy). Dùng cho việt xuất "Chỉ số Vòng vèo" (Circuity Index).
* **`ODPair`:** Ma trận nhu cầu đi lại từ `origin_area` tới `destination_area`.

### 2.3. Phân vùng `spatial_service.py`
Xử lý toàn cục không lệ thuộc vào quy trình Core Routing:
* Gom các Logic giao cắt tập hợp (Intersect) cho Shapely LineString và Shapely Polygon.
* Tính tổng quan Mức độ vòng vèo `find_cricuity_index_of_a_itinerary` thông qua đo đạc trực quan từ Hình chiếu (Projected Index) của các bến xe trên trục đường dích dắc của Tuyến Buýt.

### 2.4. Phân vùng `routing_service/` (Trái Tim Hệ Thống)
**`core_engine.py` (Lõi Lọc Tập hợp cực nhanh $O(1)$)**
Sử dụng kiến trúc OOP Base `AbstractRoutingEngine`, thừa kế độc lập các nhánh thuật toán:
* Nhánh `DirectConnectionRoutingEngine`: Xử lý đi xe trực tiếp.
* Nhánh `OneTransferRoutingEngine`: Xử lý sang xe 1 lần.
* **Đột phá Hiệu năng:** 
  * Tạo Dictionaries Lookup trực tiếp tại các vòng lặp `.get(id, -1)` thay cho hàm `.index()` chậm chạp $O(N)$.  
  * Tùy biến Local Hash Map khi Engine gọi hàm, giữ được sự thuần khiết cho Mô hình Dữ liệu (Không thay đổi Class gốc). Thời gian tính toán được chập xuống cận tuyến tính thay vì $O(N^4)$ như phiên bản cũ.

**`filter_strategy.py` (Kiến trúc Strategy Tách Biệt)**
* Thực thi `ItineraryFilterStrategy` để tạo ra Bộ lọc Tùy chỉnh (Dependency Injection).
* Trạm trung chuyển và Trạm đón/trả được tìm siêu nhanh thông qua `OptimalWalkingDistanceFilter` & `OneTransferOptimalFilter`. Đã tích hợp Block bắt Exception (Khi Origin Zone trùng Destination Zone).

**`routing_service.py` (Controller/Facade)**
Bộ vi xử lý bề mặt với đúng 5 dòng Code. Yêu cầu song song hai Engine (0-transfer, 1-transfer) chạy và gộp mảng list trả lại Front-End trong nháy mắt.

## 3. Đánh giá Khách quan Kế quả và Cải tiến còn lại

### 3.1. Các mục tiêu Đã Chinh Phục Siêu Tốc
1. [x] **Giải bải toán Sai số Không gian:** Loại bỏ Pytago, áp dụng hoàn toàn Geodesic dựa theo thư viện hạng nặng Shapely và Geopy.
2. [x] **Giải quyết Nút thắt Cổ chai (Bottlenecks):** Dẹp vòng lặp `.index()`. Refactor các truy vấn chỉ bằng Key Hash Map Dictionary $O(1)$. 
3. [x] **Thiết kế lại theo Clean Architecture OOP:** Chia Abstract Core Engine, Injectable Filter Strategy. Phân rã Component riêng có quy củ. Thiết lập ngoại lệ trùng OD Zone chuẩn chỉnh.

### 3.2. Yếu điểm tiềm tàng (Bottlenecks) & Kế hoạch Tương lai
1. **Bài toán Hiệu suất Không gian Số lượng cực lớn:**
   Dù đã dùng Shapely, nhưng bản chất vẫn là duyệt tuần tự các `Route` qua `Zone`. Nếu chạy cho Mega Cities với *Hàng vạn Route*, tương lai cần tính tới Indexing Không gian B-Tree / R-Tree như `sindex` của `Geopandas` để dò vùng quét Radar thay vì For-Loop thuần.
2. **Quản trị Bộ nhớ RAM (OOM Crash):**
   Vẫn cần đánh dấu Memory Profiling. Nếu Server tràn RAM, sẽ cân nhắc thêm `__slots__ = [...]` cho các Class cơ bản để khóa chặt dung lượng Heap của Từng Object `Point`, `Stop`, `Leg`.
3. **Mở rộng tuyến độ sâu N-Transfer (> 1 Transfer):**
   *(Ghi chú: Cải tiến số 3 này tạm thời bị loại bỏ vào lúc này theo quyết định của tác giả vì hiện tại mức 1-transfer đã đáp ứng đủ Use Cases nghiệp vụ cốt lõi).* 
   Tuy nhiên, nếu tái khởi động: Bắt buộc đập đi xây lại luồng Search bằng Đồ thị Trọng số (Nodes Network) sử dụng thư viện `networkx` và áp dụng Thuật toán `Dijkstra`/`A*`. Phương thức Intersection Set chập mảng như hiện tại sẽ sập nguồn hệ thống vì Bùng nổ Tổ hợp nếu cố nhét thêm 2-transfers.
