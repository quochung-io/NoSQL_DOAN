import os
import sys

# Khắc phục lỗi tương thích giữa pydgraph và protobuf
os.environ['PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION'] = 'python'

# Đảm bảo đường dẫn import hoạt động cả khi chạy trực tiếp hoặc import từ app
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

try:
    from scripts.set_schema import set_schema
    from scripts.seed_data import seed
except ImportError:
    from set_schema import set_schema
    from seed_data import seed

def restore():
    print("=== TIẾN HÀNH PHỤC HỒI DỮ LIỆU TỪ BẢN GỐC ===")
    print("Bước 1: Thiết lập lại Schema và Indexes...")
    set_schema(drop_all=True)
    print("Bước 2: Nạp lại toàn bộ dữ liệu mẫu...")
    seed()
    print(">>> PHỤC HỒI DỮ LIỆU HOÀN TẤT NGUYÊN TRẠNG!")

if __name__ == '__main__':
    restore()
