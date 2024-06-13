import logging
import os
import io
from minio import Minio
from sqlalchemy.orm import Session

from yap.dependencies import session_factory, minio_client
from yap.adapters import PhotoRepository, init_minio_client


# то что выше надо разнести в другие места

class S3TaskMixin:
    def _init_s3(self):
        self._minio_client = minio_client
        self._photo_repository = PhotoRepository(self._minio_client)

    @property
    def photo_repository(self):
        return self._photo_repository


class DBTaskMixin:

    def new_session(self) -> Session:
        return session_factory()
