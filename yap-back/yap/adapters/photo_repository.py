import io
import os
import logging as log

from minio import Minio

ALLOWED_ENV = {"prod", "test"}


def get_app_env() -> str:
    app_env = os.getenv("APP_ENV", "test")
    if app_env in ALLOWED_ENV:
        return app_env
    raise ValueError("Unexpected APP_ENV %r", app_env)


def _get_bucket_name(bucket_prefix: str) -> str:
    return f"{bucket_prefix}-{get_app_env()}"


YA_ART_SOURCE_BUCKET = _get_bucket_name("ya-art-source")
YA_ART_GEN_BUCKET = _get_bucket_name("ya-art-generated")
INPAINTER_GEN_BUCKET = _get_bucket_name("inpainter-generated")

USED_BUCKETS = [
    YA_ART_GEN_BUCKET,
    YA_ART_SOURCE_BUCKET,
    INPAINTER_GEN_BUCKET,
]


class PhotoRepository:
    _target_buckets = USED_BUCKETS

    def __init__(self, client: Minio):
        self._client = client
        self._init_buckets()

    def _init_buckets(self):
        for bucket_name in self._target_buckets:
            if not self._client.bucket_exists(bucket_name):
                self._client.make_bucket(bucket_name)
        log.info("Buckets inited")

    def upload_photo(self, bucket_name, photo_name, file_type, data: bytes):
        result = self._client.put_object(
            bucket_name,
            photo_name,
            io.BytesIO(data),
            length=len(data),
            content_type=f"image/{file_type}",
        )
        return result

    def get_photo(self, bucket_name, photo_name) -> bytes:
        result = self._client.get_object(bucket_name, photo_name)
        return result.data
