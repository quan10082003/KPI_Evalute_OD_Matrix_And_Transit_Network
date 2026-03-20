# KPI Evaluate OD Matrix and Transit Network

## Tổng quan (Overview)
Dự án này cung cấp một công cụ đánh giá mạng lưới giao thông công cộng (cụ thể là mạng lưới xe buýt) dựa trên dữ liệu ma trận OD (Origin-Destination) và dữ liệu hành trình tuyến. Mục tiêu chính là tính toán các chỉ số KPI (Key Performance Indicators) quan trọng nhằm đánh giá hiệu quả kết nối của hệ thống mạng lưới xe buýt hiện có, hỗ trợ cho việc quy hoạch.

## Các tính năng chính (Key Features)
- **Tải và Tiền xử lý dữ liệu (Data Loading & Preprocessing):** Hỗ trợ đọc dữ liệu mạng lưới (Stops, Routes) và nhu cầu đi lại (Zones, OD Pairs) từ các tệp định dạng XML (theo cấu trúc tựa MATSim/Cottbus).
- **Tìm kiếm Đường đi (Routing Engine):** 
  - Tìm kiếm kết nối trực tiếp (Direct Connection) không cần chuyển tuyến.
  - Tìm kiếm kết nối 1 lần chuyển tuyến (One Transfer Connection) với thuật toán tối ưu lộ trình đi bộ và khoảng cách.
- **Tính toán KPI:**
  - **Tỷ lệ chuyển tuyến (Transfer Rate):** Đánh giá số lần hành khách cần chuyển tiếp giữa các tuyến buýt với các điểm đi - đến khác nhau.
  - **Chỉ số vòng vèo (Circuity Index):** So sánh khoảng cách di chuyển thực tế trên tuyến đường (`L_route`) với khoảng cách đường chim bay (`L_straight`), qua đó đánh giá độ "thẳng" và tối ưu của lộ trình.
  - **Độ bao phủ không gian (Spatial Coverage):** Tính toán độ bao phủ diện tích bán kính đi bộ của hệ thống trạm dừng xe buýt (mặc định 500m) đối chiếu vào diện tích không gian hai khu vực xuất phát và đích đến (Origination/Destination Zones).
- **Xuất báo cáo (Exporting):** Tự động tổng hợp dữ liệu, lọc các chu trình không đạt và kết xuất KPIs dưới dạng JSON tinh gọn cho phép các dashboard báo cáo / Frontend xử lý kết quả hiệu quả.

## Cài đặt (Installation)
1. Đảm bảo rằng bạn đã cài đặt phiên bản Python 3.8 trở lên trên máy.
2. Clone repository chứa source code về thiết bị.
3. Thiết lập môi trường ảo và cài đặt các thư viện phụ thuộc:
   ```bash
   pip install -r requirements.txt
   ```
   *Lưu ý: Hai thư viện cốt lõi mạnh mẽ được sử dụng phục vụ phân tích trắc địa (geospatial) ở đây bao gồm `shapely` và `geopy`.*

## Hướng dẫn sử dụng (Usage)
Chạy tệp thực thi chính `main.py` ở lớp application context để kích hoạt trọn vẹn Use Case tải và đánh giá mạng:
```bash
python src/main.py
```
*(Mặc định, dữ liệu đầu vào đang trỏ tới tệp `schedule.xml` và `plans...xml` bên trong thư mục mock `cottbus` ở root directory của dự án)*

Toàn bộ các thông số đo lường KPI theo nhóm OD, Logs đường đi sẽ được trả ra tại tệp cấu trúc JSON `output_kpis.json` nằm tại gốc dự án.

## Cấu trúc thư mục quy ước (Folder Structure)
Hệ thống tuân thủ chặt chẽ mô hình **Clean Architecture**:
- `domain/`: Lưu trữ Domain Models cốt lõi không phụ thuộc vào Framework bên ngoài (VD: Entities, Dataclass) và Domain Services (Chứa Engine Routing, Khối tính KPI).
- `src/application/`: Chứa định nghĩa các Ports interface và Use Cases điểu phối logic luồng hoạt động ứng dụng chung (Services).
- `src/infrastructure/`: Chứa các Component tương tác vật lý (như Repository đọc file XML, lưu JSON).
- `cottbus/`: File giả lập/tĩnh từ luồng dữ liệu giao thông thật.
