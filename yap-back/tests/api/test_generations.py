"""
Example of tests, that require database.

Separate database is created by `migrated_postgres` fixture for every test.

It works very fast even with many migrations: all hard work is done by fixture
`migrated_postgres_template` once per tests run, when `migrated_postgres`
fixture just clones ready database.
"""

from http import HTTPStatus


def test_get(api_client, migrated_postgres):
    response = api_client.get("/api/generations")
    assert response.status_code == HTTPStatus.OK

    data = response.json()
    assert len(data) == 1
