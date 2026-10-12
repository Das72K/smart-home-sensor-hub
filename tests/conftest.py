"""Test setup: the API runs against an in-memory SQLite database.

No PostgreSQL needed to run the tests. main.py creates its engine at import
time, so DATABASE_URL must point somewhere harmless *before* it is imported;
each test then gets a fresh in-memory database through a get_db override.
"""

import os
import tempfile

os.environ["DATABASE_URL"] = "sqlite:///" + os.path.join(tempfile.gettempdir(), "hub_import_test.db")
os.environ["DEBUG"] = "False"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import main
from database import get_db
from models import Base

engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,  # one shared connection -> the in-memory DB survives across requests
)
TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture()
def db():
    Base.metadata.create_all(bind=engine)
    session = TestingSession()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def client(db):
    def override_get_db():
        s = TestingSession()
        try:
            yield s
        finally:
            s.close()

    main.app.dependency_overrides[get_db] = override_get_db
    with TestClient(main.app) as c:
        yield c
    main.app.dependency_overrides.clear()


@pytest.fixture()
def dht(client):
    r = client.post("/api/sensors", json={"sensor_id": "dht22_01", "type": "temperature_humidity",
                                          "location": "living_room"})
    assert r.status_code == 201
    return r.json()
