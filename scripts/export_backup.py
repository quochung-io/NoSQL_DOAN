import os
# Khắc phục lỗi tương thích giữa pydgraph và protobuf phiên bản mới
os.environ['PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION'] = 'python'

import json
import pydgraph

def get_client():
    host = os.environ.get('DGRAPH_HOST', 'localhost')
    port = os.environ.get('DGRAPH_GRPC_PORT', '9080')
    client_stub = pydgraph.DgraphClientStub(f'{host}:{port}')
    return pydgraph.DgraphClient(client_stub), client_stub

def export_json_backup(output_file='backup_data.json'):
    client, client_stub = get_client()
    try:
        query = """
        query GetAllData {
          faculties(func: type(Faculty)) {
            uid
            expand(_all_) {
              uid
              expand(_all_)
            }
          }
          users(func: type(User)) {
            uid
            username
            full_name
            email
            role
            must_change_password
            is_active
            in_faculty { uid }
            enrolled_in { uid }
          }
          topics(func: type(Topic)) {
            uid
            topic_name
            description
            handles { uid }
          }
        }
        """
        res = client.txn(read_only=True).query(query)
        data = json.loads(res.json)

        filepath = os.path.join(os.path.dirname(__file__), output_file)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        print(f">>> THÀNH CÔNG: Đã sao lưu dữ liệu ra file: {filepath}")
        return filepath
    finally:
        client_stub.close()

if __name__ == '__main__':
    export_json_backup()
