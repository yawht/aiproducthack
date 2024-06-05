import io
import logging as log

from minio import Minio


YA_ART_GEN_BUCKET = 'ya-art-generated'
INPAINTER_GEN_BUCKET = 'inpainter-generated'

USED_BUCKETS = [
    YA_ART_GEN_BUCKET,
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
        log.info('Buckets inited')

    def upload_photo(self, bucket_name, photo_name, file_type, data: bytes):
        result = self._client.put_object(
            bucket_name, photo_name, io.BytesIO(data),
            length=len(data),
            content_type=f'image/{file_type}'
        )
        return result