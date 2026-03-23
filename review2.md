# Đánh giá Kiến trúc Codebase theo Tư duy "Architecture Patterns with Python" (Cosmic Python)

Đây là bản đánh giá kỹ thuật mã nguồn hiện tại của dự án theo đúng triết lý của sách **Cosmic Python**. Trong thiết kế này, kiến trúc xoay quanh các khái niệm: **Domain**, **Adapters**, **Service Layer** và **Message Bus/Unit Of Work**.

Mã nguồn hiện tại của bạn đã nhích một bước về phía phân tách Domain, nhưng cấu trúc file và vị trí đặt các dependency (library) vẫn chưa thỏa mãn triết lý "Domain Is Pure" của sách.

---

## 1. Domain Leakage (Rò rỉ Dependency vào Tầng Domain)

**Vấn đề hiện tại:**
- Sách Cosmic Python nhấn mạnh: **Tầng Domain phải là "Pure Python" (Python Thuần)**. Không được nhập (`import`) bất kỳ thư viện thứ 3 nào xử lý cơ sở hạ tầng, DB, mạng cục bộ, hoặc tính toán phức tạp (như C++ Bindings).
- Hiện tại, `src/domain/entities_and_dataclass/domain_class.py` và `domain_dataclass.py` đang gọi thẳng thư viện `shapely.geometry` và `geopy`. Nếu Shapely bị lỗi hoặc bạn đổi sang thư viện C++ khác, lõi Domain sẽ sụp đổ.

**Cách giải quyết theo sách Cosmic (Ports & Adapters):**
- **Định nghĩa Port:** Tạo một hợp đồng (Interface) bằng chữ Python thuần ở tầng Domain, ví dụ `IGeometryCalculator` tại `domain/ports.py`.
- **Viết Adapter:** Chuyển phần mã Shapely/Geopy ra hẳn bên ngoài vào tầng `adapters/geospatial.py`.
- **Injection:** Tầng `Service Layer` (hoặc `bootstrap.py`) sẽ khởi tạo `ShapelyGeometryCalculator` từ `adapters` và truyền nó (inject) ngược lại vào các Logic Tính Toán (Domain Services) của Domain. 

---

## 2. Ranh giới Aggregate & Tính chất của Model

**Vấn đề hiện tại:**
- **Encapsulation:** Các thuộc tính Entity (`Route`, `Zone`...) đang để public và có thể thay đổi dễ dàng, vi phạm nguyên lý bảo vệ bất biến (Invariants) của Entity.
- **Reference By ID:** Entity `Route` hiện tại đang lưu thẳng mảng các đối tượng Bến Xe nguyên bản (`stops_seq: List[Stop]`). 
  - *Cosmic Python Rule:* Aggregate này chỉ nên tham chiếu sang Aggregate khác thông qua ID. 
  - Nếu load toàn mạng lưới xe buýt từ DB, việc lồng ghép list object sẽ gây phình cực lớn bộ nhớ đồ thị nội bộ và sinh ra N+1 vấn đề ở Database (ORM). **Cần đổi biến này thành `stops_seq: List[str]` để lưu chuỗi `stop_id`.** Khi tính toán tìm đường, bạn truyền một "Quyển từ điển các Bến" (Stop Map) vào Routing Engine là đủ khả năng chạy siêu tốc độ.

---

## 3. Lỗi Trách Nhiệm ở Tầng Adapters (Repositories)

**Vấn đề hiện tại:**
- Cosmic Python dùng tầng `adapters` (đặc biệt là Repository Pattern) **chỉ để trừu tượng hóa việc đọc/ghi dữ liệu**.
- `CottbusXmlRepository` hiện tại gọi và chạy luôn các thuật toán định tuyến (`DirectConnectionRoutingEngine`, `OneTransferRoutingEngine`) để lọc Data ngay trong lúc đọc luồng XML.
- Repository KHÔNG ĐƯỢC phép chạy Code Nghiệp Vụ (Domain Logic). Quyết định "Tuyế́n đường này có thoả mãn mạng lưới hay không?" là việc của `Domain Services` kích hoạt qua `Service Layer`. Repository chỉ trả về Dữ Liệu Thô (List Route, List OD).

---

## 4. Hardcode Dependency & Thiếu Bootstrap

**Vấn đề hiện tại:**
- File `EvaluateNetworkUseCase` và `ProduceODResult` đóng vai trò là tầng *Service Layer* của Cosmic Python (điều phối luồng), nhưng lại tự ý gọi `__init__` (tự khởi tạo) các thành phần thấp hơn như Filter, Routing Engine, và Calc KPI bên trong chính file đó.
- Cosmic Python phản đối việc này quyết liệt. Các service phải được truyền (inject) đầy đủ "đồ chơi" từ cổng vào (Entrypoint).

**Cách giải quyết (Dependency Injection Container):**
- Lập ra một tệp thiêng liêng tên là `bootstrap.py`.
- Đứng ở `bootstrap.py`, bạn kết nối TẤT CẢ mọi sợi dây: Khởi tạo UnitOfWork từ *Adapters*, Khởi tạo GeoCalculator từ *Adapters*, Khởi tạo MessageBus. Rồi nhét chúng vào *Service Layer*. `main.py` chỉ có việc gõ búa gọi lệnh từ Bootstrap.

---

## 5. Cốt Lõi Bị Khuyết: Unit of Work (và Message Bus)

**Vấn đề hiện tại:**
- Thiết kế hiện tại chạy "chay" hoàn toàn một mạch Python.
- Trong Cosmic Python, mọi truy cập DB từ *Service Layer* đều được bọc trong ngữ cảnh quản lý giao dịch của **Unit of Work** (UoW). 
  - Gọi Data: Mở kho `with uow:`. Lấy ra bằng `uow.network.get(...)`.
- Khi tính toán xong Routing, đáng nhẽ hệ thống phát sinh ra (yield) một Event (sự kiện) là `ODRoutingCompleted`, con `Message Bus` sẽ bắt lấy event đó và tự ném cho các Handler tính KPI. Hiện tại bạn đang gán ghép bằng một vòng lặp FOR khổng lồ. (Tạm thời cho bản MVP Routing thì chưa cần MessageBus, nhưng **UoW** là cực kỳ quan trọng nếu lấy Data từ SQL / Database thật).

---
**Tổng Kết Nhận Xét:** 
Cấu trúc có hơi hướng phân lớp tốt. Giờ chỉ cần bẻ lái một chút cấu trúc file thành 4 bộ mặt thuần túy `domain`, `adapters`, `service_layer`, `entrypoints` và chuyển thư viện ra rìa `adapters` là đạt tầm vóc kiến trúc Enterprise chuẩn sách Cosmic Python!
