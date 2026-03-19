import os
from infrastructure.repositories.cottbus_xml_repository import CottbusXmlRepository
from application.use_cases.evaluate_network_use_case import EvaluateNetworkUseCase

def main():
    # 1. Cấu hình file path. 
    # Tính đường dẫn bằng cách lùi 2 cấp (từ src/main.py -> src/ -> root)
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)
    
    cottbus_dir = os.path.join(project_root, 'cottbus')
    
    schedule_xml = os.path.join(cottbus_dir, 'schedule.xml')
    plans_xml = os.path.join(cottbus_dir, 'plans_scale0.375true.xml')
    output_json = os.path.join(project_root, 'output_kpis.json')

    print("Khởi tạo hệ thống...")
    
    # 2. Wire Dependency: Khởi tạo Repository chứa logic load từ file
    repository = CottbusXmlRepository(
        schedule_path=schedule_xml, 
        plans_path=plans_xml,
        max_plans=200 
    )

    # 3. Khởi tạo Use Case và inject Data Repository vào (Dependency Injection)
    evaluate_network_use_case = EvaluateNetworkUseCase(repository=repository)

    # 4. Chạy thực thi Use Case
    evaluate_network_use_case.execute(output_json_path=output_json)

if __name__ == "__main__":
    main()
