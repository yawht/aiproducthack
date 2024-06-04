"""
Выгружает все фотки из unsplash по поисковому запросу, учитывая пагинацию и квотирование (50rph)

Пример:
ACCESS_KEY='**key**' DB_PASSWORD='**psw**' python3 parse_unsplash.py 'interior room'

Искать фотки в табличке unsplash_loaded, могут дублироваться, уникальные фотки во вьюшке unique_unsplash_loaded
"""

import requests
from typing import Generator, Optional
from http import HTTPStatus
import logging
from itertools import batched
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, Session
from sqlalchemy import String, create_engine, Engine
from time import sleep
import os
import argparse


logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger('unsplash_loader')


UNSPLASH_URL = 'https://api.unsplash.com'
SAVE_BATCH_SIZE = 10

ACCESS_KEY = os.getenv('ACCESS_KEY')
DB_NAME = os.getenv('DB_NAME', 'yap-junk')
DB_USER = os.getenv('DB_USER', 'yap')
DB_HOST = os.getenv('DB_HOST', '158.160.151.53')
DB_PORT = os.getenv('DB_PORT', '5432')
DB_PASSWORD = os.getenv('DB_PASSWORD')


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('query')
    return parser.parse_args()


class Base(DeclarativeBase):
    pass


class ImageDataModel(Base):
    __tablename__ = "unsplash_loaded"
    id: Mapped[int] = mapped_column(primary_key=True)
    query: Mapped[str] = mapped_column(String())
    query: Mapped[str] = mapped_column(String())
    asset_type: Mapped[str] = mapped_column(String())
    width: Mapped[str] = mapped_column(String())
    height: Mapped[str] = mapped_column(String())
    full_image: Mapped[str] = mapped_column(String())
    regular_image: Mapped[str] = mapped_column(String())
    small_image: Mapped[str] = mapped_column(String())


def build_engine():
    return create_engine(
        f'postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}',
        connect_args={
            'sslmode': 'disable',
        },
        pool_recycle=1800,
        pool_pre_ping=True,
    )


class UnsplashLoader:
    def __init__(
        self, access_key: str, query: str,
        pn: int =1, order_by: str = 'relevant',
    ):
        self._base_headers = {'Authorization': f'Client-ID {access_key}'}
        self._remaining_rate_limit = None
        self._query = query
        self._order_by = order_by
        self._pn = pn
        self._total_pages = None

    def load(self) -> Generator[ImageData, None, None]:
        while self._total_pages is None or self._pn <= self._total_pages:
            resp = requests.get(f'{UNSPLASH_URL}/search/photos', {
                'query': self._query,
                'pn': self._pn,
                'order_by': self._order_by,
            }, headers=self._base_headers)
            if resp.status_code != HTTPStatus.OK:
                self._remaining_rate_limit = 0
                log.warning('Unexpected resp (%s|%s)', resp.status_code, resp.content)
                return
            data = resp.json()
            self._total_pages = data['total_pages']
            self._pn += 1
            yield from self._parse_results(data['results'], query=self._query)

            self._remaining_rate_limit = resp.headers.get('X-Ratelimit-Remaining')
            if self._remaining_rate_limit == 0:
                return

    @property
    def remaining_rate_limit(self) -> Optional[int]:
        return self._remaining_rate_limit

    @property
    def locked(self) -> bool:
        return self._remaining_rate_limit is not None and not bool(self._remaining_rate_limit)

    @property
    def finished(self) -> bool:
        return self._total_pages and self._pn == self._total_pages

    @staticmethod
    def _parse_results(results, query=''):
        for im_data in results:
            yield ImageDataModel(
                query=query,
                asset_type=im_data['asset_type'],
                width=im_data['width'],
                height=im_data['height'],
                full_image=im_data['urls'].get('full'),
                regular_image=im_data['urls'].get('regular'),
                small_image=im_data['urls'].get('small'),
            )


def _main():
    args = get_args()
    log.info('init app with query "%s"', args.query)
    engine = build_engine()
    Base.metadata.create_all(engine, checkfirst=True)
    loader = UnsplashLoader(ACCESS_KEY, args.query)
    while not loader.finished:
        _process(loader, engine)
    log.info('down loading finished')


def _process(loader: UnsplashLoader, engine: Engine):
    image_data = loader.load()
    with Session(engine) as session:
        for batch in batched(image_data, SAVE_BATCH_SIZE):
            with session.begin():
                log.info('try to save batch (%r)', len(batch))
                session.add_all(batch)
            log.info('Saved %d photos', len(batch))
    if loader.locked:
        log.info('Api locked, wait for 300s')
        sleep(300)


if __name__ == '__main__':
    _main()
