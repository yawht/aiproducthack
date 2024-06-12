import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from yap.adapters.photo_repository import PhotoRepository
from yap.adapters.s3 import create_minio_client
from yap.settings import settings


engine = create_engine(settings.pg_url, connect_args={})
session_factory = sessionmaker(autocommit=False, bind=engine)

minio_client = create_minio_client(settings.minio_endpoint, settings.minio_access_key, settings.minio_secret_key)
photo_repo = PhotoRepository(minio_client)

def get_db():
    db = session_factory()
    try:
        yield db
    finally:
        db.close()

def get_photo_repo():
    yield photo_repo
