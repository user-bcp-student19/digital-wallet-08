from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient

from app.clock import PeruClock
from app.config import Settings
from app.main import create_app

PASSWORD = "Clave1234567"


class FakeClock(PeruClock):
    def __init__(self, start: datetime) -> None:
        self._now = start

    def now(self) -> datetime:
        return self._now

    def advance(self, seconds: float) -> None:
        self._now += timedelta(seconds=seconds)

    def set(self, value: datetime) -> None:
        self._now = value


@pytest.fixture
def clock():
    # 10:00 en Lima
    return FakeClock(datetime(2026, 1, 15, 15, 0, 0, tzinfo=timezone.utc))


@pytest.fixture
def make_client(clock):
    def _make(app_env: str = "testing") -> TestClient:
        settings = Settings(app_env=app_env, db_path=":memory:", pbkdf2_iterations=1000)
        return TestClient(create_app(settings, clock))

    return _make


@pytest.fixture
def client(make_client):
    return make_client()


@pytest.fixture
def password():
    return PASSWORD


@pytest.fixture
def register():
    def _register(client, usuario="mjquispe", **over):
        payload = {
            "nombres": "María José",
            "apellido_paterno": "Quispe",
            "apellido_materno": "Rojas",
            "usuario": usuario,
            "password": PASSWORD,
        }
        payload.update(over)
        return client.post("/onboarding/registrations", json=payload)

    return _register


@pytest.fixture
def new_wallet(register):
    def _new(client, usuario="mjquispe"):
        r = register(client, usuario=usuario)
        assert r.status_code == 201, r.text
        return r.json()["account"]["wallet_id"], (usuario, PASSWORD)

    return _new
