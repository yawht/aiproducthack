import os

import pytest
from yarl import URL

from yap.alembic.utils import DEFAULT_PG_URL


@pytest.fixture(scope="session")
def pg_url():
    """
    Provides base PostgreSQL URL for creating temporary databases.
    """
    return URL(os.getenv("CI_PG_URL", DEFAULT_PG_URL))
