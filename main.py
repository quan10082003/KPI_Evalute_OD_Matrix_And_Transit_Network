import os
from infrastructure.repositories.cottbus_xml_repository import CottbusXmlRepository
from application.kpi_evaluation_app import KPIEvaluationApplication

def main():
    # 1. Cấu hình file path trỏ vào thư mục cottbus
    base_dir = os.path.dirname(os.path.abspath(__file__))
    cottbus_dir = os.path.join(base_dir, 'cottbus')
    
    schedule_xml = os.path.join(cottbus_dir, 'schedule.xml')
    plans_xml = os.path.join(cottbus_dir, 'plans_scale0.375true.xml')
    output_json = os.path.join(base_dir, 'output_kpis.json')

    print("Khởi tạo hệ thống...")
    
    # 2. Wire Dependency: Khởi tạo Repository chứa logic load từ file
    # Giới hạn phân tích 200 OD cho nhẹ ở phase POC. Bạn có thể tăng lên nếu muốn.
    repository = CottbusXmlRepository(
        schedule_path=schedule_xml, 
        plans_path=plans_xml,
        max_plans=200 
    )

    # 3. Khởi tạo Application Component và inject Data Repository vào
    app = KPIEvaluationApplication(repository=repository)

    # 4. Chạy thực thi (Pipeline)
    app.run_evaluation(output_json_path=output_json)

if __name__ == "__main__":
    main()
