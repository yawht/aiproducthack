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
    yc_folder_id: Optional[str] = os.getenv("YC_FOLDER_ID", "bt1m4kq9p8ojupu1d0co")

    bento_negative_prompt: str = os.getenv(
        "BENTO_NEGATIVE_PROMPT",
        "curved lines, ornate, baroque, abstract, grunge, logo, text,word,cropped,low quality,normal quality,username,watermark,signature,blurry,soft,soft line,sketch,ugly,logo,pixelated,lowres",
    )
    bento_url: str = os.getenv(
        "BENTO_URL", "https://node-api.datasphere.yandexcloud.net/replace_background"
    )
    bento_inference_steps: int = os.getenv("BENTO_NUM_INFERENCE", 50)

    ollama_url: str = os.getenv("OLLAMA_URL", "http://factorio.info.gf:11434")
    ollama_system: str = os.getenv("OLLAMA_SYSTEM_PROMPT", "You are the assistant who comes up with prompt for stable diffusion. You need to come up with a prompt to generate the background for the object.")

    # Databases
    pg_url: str = os.getenv("PG_URL", "postgresql://user:crackme@localhost:5432/yap")
    minio_endpoint: str = os.getenv("MINIO_ENDPOINT", "127.0.0.1:9000")
    minio_access_key: str = os.getenv("MINIO_ACCESS_KEY", "minio")
    minio_secret_key: str = os.getenv("MINIO_SECRET_KEY", "minio123")
    minio_cdn_path: str = os.getenv("MINIO_CDN_PATH", "http://127.0.0.1:9091")


settings = AppSettings()
