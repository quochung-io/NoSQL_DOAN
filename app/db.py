import os
# Khắc phục lỗi tương thích giữa pydgraph và protobuf phiên bản mới
os.environ['PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION'] = 'python'

import json
import pydgraph
from app.config import Config

class DgraphService:
    def __init__(self):
        self.host = Config.DGRAPH_HOST
        self.port = Config.DGRAPH_GRPC_PORT
        self.client_stub = None
        self.client = None
        self._connect()

    def _connect(self):
        try:
            self.client_stub = pydgraph.DgraphClientStub(f'{self.host}:{self.port}')
            self.client = pydgraph.DgraphClient(self.client_stub)
        except Exception as e:
            print(f"Lỗi khởi tạo kết nối Dgraph: {e}")

    def get_client(self):
        if not self.client:
            self._connect()
        return self.client

    def query(self, query_str, variables=None):
        client = self.get_client()
        txn = client.txn(read_only=True)
        try:
            res = txn.query(query_str, variables=variables)
            return json.loads(res.json)
        finally:
            txn.discard()

    def mutate(self, set_obj=None, del_obj=None):
        client = self.get_client()
        txn = client.txn()
        try:
            mu = pydgraph.Mutation()
            if set_obj:
                mu.set_json = json.dumps(set_obj).encode('utf-8')
            if del_obj:
                mu.delete_json = json.dumps(del_obj).encode('utf-8')
            response = txn.mutate(mu)
            txn.commit()
            return response
        except Exception as e:
            txn.discard()
            raise e

dgraph_db = DgraphService()
