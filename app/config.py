import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'default_secret_key_nosql_2026')
    DGRAPH_HOST = os.environ.get('DGRAPH_HOST', 'localhost')
    DGRAPH_GRPC_PORT = os.environ.get('DGRAPH_GRPC_PORT', '9080')
    DGRAPH_HTTP_PORT = os.environ.get('DGRAPH_HTTP_PORT', '8080')
