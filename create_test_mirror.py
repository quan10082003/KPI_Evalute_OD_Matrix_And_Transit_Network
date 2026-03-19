import os
import shutil

def clone_test_structure(src_dir: str, test_dir: str):
    """
    Quét thưa mục `src_dir` (ví dụ: domain).
    Sao chép y hệt cấu trúc thư mục con sang `test_dir` (ví dụ: test).
    Đồng thời tạo sẵn các file test tương ứng cho từng file .py trong source.
    """
    
    # 1. Nếu muốn Cài đặt lại từ đầu thì bỏ comment dòng dưới để xóa thư mục test cũ (CẨN THẬN mất code test đã viết)
    # if os.path.exists(test_dir):
    #     shutil.rmtree(test_dir)

    # 2. Duyệt qua toàn bộ cây thư mục gốc
    for root, dirs, files in os.walk(src_dir):
        # Đường dẫn tương đối từ src_dir (VD: "domain_service/routing_service")
        relative_path = os.path.relpath(root, src_dir)
        
        # Nếu thư mục gốc là "." thì bỏ qua name 
        if relative_path == ".":
            relative_path = ""
            
        # -- Cách Đặt Tên Folder Test --
        # Bạn có thể giữ nguyên tên folder (như "routing_service") hoặc thêm tiền tố "test_" (thành "test_routing_service")
        # Ở đây làm theo sample của bạn: Thêm "test_" vào trước mỗi folder name
        parts = relative_path.split(os.sep)
        test_parts = ["test_" + p if p else "" for p in parts]
        target_sub_dir = os.path.join(test_dir, *test_parts)
        
        # Tạo cấu trúc thư mục con bên folder `test`
        os.makedirs(target_sub_dir, exist_ok=True)
        
        # -- Đặt Tên File Test --
        for file in files:
            # Bỏ qua các file rác hoặc các file không phải code (ví dụ markdown, config, init)
            if file.endswith('.py') and not file.startswith('__'):
                # Sinh tên file test (ví dụ: "domain_class.py" -> "test_domain_class.py")
                test_file_name = f"test_{file}"
                test_file_path = os.path.join(target_sub_dir, test_file_name)
                
                # Tạo file rỗng hoặc chứa sẵn boilerplate code nếu file chưa tồn tại
                if not os.path.exists(test_file_path):
                    with open(test_file_path, 'w', encoding='utf-8') as f:
                        f.write(f'"""\nTest cases for {file}\n"""\n')
                        f.write("import pytest\n\n")
                    print(f"[Created] {test_file_path}")
                else:
                    print(f"[Skipped] {test_file_path} (Already exists)")
                    
    print("\n✅ Đã đồng bộ hoàn tất bộ khung Mirror Testing!")

if __name__ == "__main__":
    # Thay đường dẫn thực tế tại máy tính của bạn
    # Dùng đường dẫn tuyệt đối hoặc đường dẫn tương đối (từ nơi chạy script)
    SOURCE_DIRECTORY = "./domain"
    TEST_DIRECTORY = "./test/unit/domain"
    
    clone_test_structure(SOURCE_DIRECTORY, TEST_DIRECTORY)
