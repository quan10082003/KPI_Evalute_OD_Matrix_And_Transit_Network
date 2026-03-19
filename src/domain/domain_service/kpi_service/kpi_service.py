from typing import List
from domain.entities_and_dataclass.domain_dataclass import ODRoutingResult
from domain.entities_and_dataclass.domain_class import Stop, Route

# ──────────────────────────────────────────────────────────────────────────────
# Mỗi KPI Service con nằm trong file riêng biệt tại cùng package này.
# Quy ước: mỗi service chỉ tính 1 nhóm KPI và trả về dict kết quả của nhóm đó.
#
# Ví dụ khi thêm mới:
#   from domain.domain_service.kpi_service.kpi_A_service import KPIAService
#   from domain.domain_service.kpi_service.kpi_B_service import KPIBService
#
# Application Layer (kpi_evaluation_app.py) sẽ gọi từng service và
# tổng hợp kết quả — KHÔNG làm việc đó ở đây.
# ──────────────────────────────────────────────────────────────────────────────
