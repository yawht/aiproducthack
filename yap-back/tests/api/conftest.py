from fastapi.testclient import TestClient
import pytest
from alembic.command import upgrade
from yarl import URL

from yap.main import app
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
def api_client():
    client = TestClient(app=app, base_url="http://test")
    yield client
