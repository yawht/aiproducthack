import base64
from pathlib import Path
from fastapi.testclient import TestClient
import pytest
from alembic.command import upgrade
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from yarl import URL

from yap.main import app
from yap.dependencies import get_db
from yap.alembic.utils import alembic_config_from_url, tmp_database


@pytest.fixture(scope="session")
def migrated_postgres_template(pg_url):
    """
    Creates temporary database and applies migrations.
    Database can be used as template to fast creation databases for tests.

    Has "session" scope, so is called only once per tests run.
    """
    with tmp_database(pg_url, "template") as tmp_url:
        alembic_config = alembic_config_from_url(tmp_url)
        upgrade(alembic_config, "head")
        yield tmp_url


@pytest.fixture
def migrated_postgres(pg_url, migrated_postgres_template):
    """
    Quickly creates clean migrated database using temporary database as base.
    Use this fixture in tests that require migrated database.
    """
    template_db = URL(migrated_postgres_template).name
    with tmp_database(pg_url, "pytest", template=template_db) as tmp_url:
        yield tmp_url


@pytest.fixture
def orm_session(migrated_postgres):
    engine = create_engine(migrated_postgres)
    session_factory = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = session_factory()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def api_client(orm_session):
    def get_db_wrapper():  # god bless generators
        yield orm_session

    app.dependency_overrides[get_db] = get_db_wrapper
    client = TestClient(app=app, base_url="http://test")
    yield client

@pytest.fixture
def encoded_img():
    samples_img = Path(__file__).parent / 'samples' / 'img.jpeg'
    with open(samples_img, 'rb') as image_file:
        raw = image_file.read()
        yield base64.b64encode(raw).decode('utf-8')
    