import pytest
from flask_migrate import downgrade


@pytest.fixture
def hijack_db(db, monkeypatch, db_session):
    # make alembic run with our test db connection
    monkeypatch.setattr(db.engine, 'connect', db_session.get_bind)
    return db


def test_downgrade(hijack_db):
    downgrade()

