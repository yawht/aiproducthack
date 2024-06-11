import os
from pydantic_settings import BaseSettings


class AppSettings (BaseSettings):
    pg_url: str = os.getenv('PG_URL', 'postgresql://user:crackme@localhost:5432/yap')
    app_env: str = os.getenv('APP_ENV', 'test')
    app_host: str = os.getenv('APP_HOST', '127.0.0.1')
    app_port: str = os.getenv('APP_PORT', '8080')
    minio_endpoint: str = os.getenv('MINIO_ENDPOINT', '127.0.0.1:9000')
    minio_access_key: str = os.getenv('MINIO_ACCESS_KEY', 'minio')
    minio_secret_key: str = os.getenv('MINIO_SECRET_KEY', 'minio123')

settings = AppSettings()
