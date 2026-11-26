import os
import sys
import json

# Khắc phục lỗi tương thích giữa pydgraph và protobuf
os.environ['PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION'] = 'python'

import pydgraph

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
    print("=== TIẾN HÀNH PHỤC HỒI DỮ LIỆU TỪ BẢN SAO LƯU ===")
    print("Bước 1: Thiết lập lại Schema và Indexes...")
    set_schema(drop_all=True)
    print("Bước 2: Nạp dữ liệu từ backup_data.json...")
    backup_file = os.path.join(os.path.dirname(__file__), 'backup_data.json')
    if not os.path.isfile(backup_file):
        print("Không tìm thấy backup_data.json. Tái nạp dữ liệu mẫu thay thế...")
        seed()
        return

    with open(backup_file, 'r', encoding='utf-8') as f:
        backup = json.load(f)

    nodes = {}

    def collect(value):
        if isinstance(value, list):
            for item in value:
                collect(item)
        elif isinstance(value, dict):
            uid = value.get('uid')
            if uid:
                node = nodes.setdefault(uid, {'uid': uid})
                for key, item in value.items():
                    if key not in ('uid',):
                        node[key] = item
            for item in value.values():
                collect(item)

    for data in backup.values():
        collect(data)

    host = os.environ.get('DGRAPH_HOST', 'localhost')
    port = os.environ.get('DGRAPH_GRPC_PORT', '9080')
    stub = pydgraph.DgraphClientStub(f'{host}:{port}')
    client = pydgraph.DgraphClient(stub)
    txn = client.txn()
    try:
        mutation = pydgraph.Mutation()
        mutation.set_json = json.dumps(list(nodes.values())).encode('utf-8')
        txn.mutate(mutation)
        txn.commit()
    finally:
        txn.discard()
        stub.close()

    print(">>> PHỤC HỒI DỮ LIỆU HOÀN TẤT NGUYÊN TRẠNG!")

if __name__ == '__main__':
    restore()
