import os
from typing import Optional
from pydantic_settings import BaseSettings


class AppSettings(BaseSettings):
    # App related
    app_env: str = os.getenv("APP_ENV", "test")
    app_host: str = os.getenv("APP_HOST", "127.0.0.1")
    app_port: str = os.getenv("APP_PORT", "8080")
    generation_list_limit: int = os.getenv("GENERATION_GET_LIMIT", 50)

    # Clients
    yc_oauth_token: Optional[str] = os.getenv("YC_OAUTH_TOKEN", None)
    yc_node_id: Optional[str] = os.getenv("YC_NODE_ID", "datasphere.user.bento")
    yc_folder_id: Optional[str] = os.getenv("YC_FOLDER_ID", "b1gk61tkdst8hqagvopn")

    bento_negative_prompt: str = os.getenv("BENTO_NEGATIVE_PROMPT", "ugly, disfigured, ill-structured, low resolution")
    bento_url: str = os.getenv("BENTO_URL", "https://node-api.datasphere.yandexcloud.net/replace_background")
    bento_inference_steps: int = os.getenv("BENTO_NUM_INFERENCE", 50)

    # Databases
    pg_url: str = os.getenv("PG_URL", "postgresql://user:crackme@localhost:5432/yap")
    minio_endpoint: str = os.getenv("MINIO_ENDPOINT", "127.0.0.1:9000")
    minio_access_key: str = os.getenv("MINIO_ACCESS_KEY", "minio")
    minio_secret_key: str = os.getenv("MINIO_SECRET_KEY", "minio123")
    minio_cdn_path: str = os.getenv("MINIO_CDN_PATH", "http://127.0.0.1:9091")


settings = AppSettings()
