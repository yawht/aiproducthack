import os
from minio import Minio

def init_minio_client() -> Minio:
    return Minio(
        endpoint=os.getenv('MINIO_ENDPOINT'),  # без http/https
        access_key=os.getenv('MINIO_ACCESS_KEY'),
        secret_key=os.getenv('MINIO_SECRET_KEY'),
        secure=False,
    )
