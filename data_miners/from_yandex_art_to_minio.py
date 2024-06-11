"""
Генерирует фотографии по промпту и выгружает их

Пример:
API_KEY='**key**' DB_PASSWORD='**psw**' MINIO_SECRET_KEY='fff', MINIO_ACCESS_KEY='fff' python3 from_yandex_art_to_minio.py 'Мебель от икея, диван в комнате (высокая детализация, реалистично)' 10

Искать фотки в табличке unsplash_loaded, могут дублироваться, уникальные фотки во вьюшке unique_unsplash_loaded
"""

import http
import logging
from random import randint
import requests
import base64
import io
import os
from time import sleep
from minio import Minio
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, Session
from sqlalchemy import String, Integer, create_engine, Engine
from dataclasses import dataclass
import argparse
import datetime


URL = 'https://llm.api.cloud.yandex.net/foundationModels/v1/imageGenerationAsync'
URL_OPERATION_PREFIX = 'https://llm.api.cloud.yandex.net:443/operations/'
API_KEY = os.getenv('API_KEY')
MINIO_URL = os.getenv('MINIO_URL', '158.160.151.53:9091')
MINIO_SECRET_KEY = os.getenv('MINIO_SECRET_KEY')
MINIO_ACCESS_KEY = os.getenv('MINIO_ACCESS_KEY')
DB_NAME = os.getenv('DB_NAME', 'yap-junk')
DB_USER = os.getenv('DB_USER', 'yap')
DB_HOST = os.getenv('DB_HOST', '158.160.151.53')
DB_PORT = os.getenv('DB_PORT', '5432')
ORGAINZATION_ID = os.getenv('ORGAINZATION_ID', 'b1gk61tkdst8hqagvopn')
DB_PASSWORD = os.getenv('DB_PASSWORD')


logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger('unsplash_loader')


@dataclass
class GeneratadPhoto:
    prompt: str
    seed: int
    data: bytes
    file_name: str
    file_type: str


def gen_pic_by_prompt(propmt: str) -> GeneratadPhoto:
    seed = randint(0, 10000000)
    body = {
        "modelUri": f"art://{ORGAINZATION_ID}/yandex-art/latest",
        "generationOptions": {
          "seed": seed
        },
        "messages": [
          {
            "weight": 1,
            "text": propmt
          }
        ]
    }
    resp = requests.post(URL, json=body, headers={'Authorization': f'Api-Key {API_KEY}'})

    image_data = {}

    while image_data.get('response', {}).get('image') is None:
        sleep(0.5)
        resp = requests.get(URL_OPERATION_PREFIX + resp.json()['id'], json=body, headers={
            'Authorization': f'Api-Key {API_KEY}',
        })
        if resp.status_code != http.HTTPStatus.OK:
            raise resp
        image_data = resp.json()

    base64_data = base64.b64decode(image_data['response']['image'])
    filename = f'{datetime.datetime.now().timestamp()}-{seed}.jpg'
    log.info(f'with prompt "{propmt}" and seed {seed} generated {filename}')
    return GeneratadPhoto(propmt, seed, base64_data, filename, 'jpg')


def build_engine() -> Engine:
    return create_engine(
        f'postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}',
        connect_args={
            'sslmode': 'disable',
        },
        pool_recycle=1800,
        pool_pre_ping=True,
    )


class Base(DeclarativeBase):
    pass


class YandexArtPhotoData(Base):
    __tablename__ = "ya_art_generated"

    id: Mapped[int] = mapped_column(primary_key=True)
    prompt: Mapped[str] = mapped_column(String())
    seed: Mapped[int] = mapped_column(Integer())
    bucket_name: Mapped[str] = mapped_column(String())
    file_name: Mapped[str] = mapped_column(String())


YA_ART_GEN_BACKET = 'ya-art-generated'


class PhotoRepository:
    _target_buckets = [
        YA_ART_GEN_BACKET,
    ]

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

def _parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('prompt')
    parser.add_argument('iterations', type=int)
    return parser.parse_args()

def _main():
    args = _parse_args()
    minio_client = Minio(MINIO_URL, MINIO_ACCESS_KEY, MINIO_SECRET_KEY, secure=False)
    photo_repo = PhotoRepository(minio_client)
    engine = build_engine()
    Base.metadata.create_all(engine, checkfirst=True)

    for i in range(args.iterations):
        photo_data = gen_pic_by_prompt(args.prompt)
        photo_repo.upload_photo(
            YA_ART_GEN_BACKET,
            photo_data.file_name,
            photo_data.file_type,
            photo_data.data,
        )
        with Session(engine) as session:
            session.add(YandexArtPhotoData(
                prompt=args.prompt,
                seed=photo_data.seed,
                bucket_name=YA_ART_GEN_BACKET,
                file_name=photo_data.file_name
            ))
            session.commit()
        log.info(f'generated and uploaded {i+1} photos')


if __name__ == '__main__':
    _main()
