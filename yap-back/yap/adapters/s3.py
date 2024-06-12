import os
from minio import Minio


def init_minio_client() -> Minio:
    return create_minio_client(
        endpoint=os.getenv("MINIO_ENDPOINT"),  # без http/https
        access_key=os.getenv("MINIO_ACCESS_KEY"),
        secret_key=os.getenv("MINIO_SECRET_KEY"),
    )


def create_minio_client(endpoint: str, access_key: str, secret_key: str) -> Minio:
    return Minio(
        endpoint=endpoint, access_key=access_key, secret_key=secret_key, secure=False
    )
