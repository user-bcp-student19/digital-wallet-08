import re
import uuid


def test_start_session(client):
    r = client.post("/onboarding/sessions")
    assert r.status_code == 201
    uuid.UUID(r.json()["session_id"])
    assert r.json()["started_at"]


def test_step_records_elapsed_time(client, clock):
    sid = client.post("/onboarding/sessions").json()["session_id"]
    clock.advance(2)
    r = client.post(f"/onboarding/sessions/{sid}/steps", json={"step": "NOMBRES"})
    assert r.status_code == 201
    assert r.json() == {"step": "NOMBRES", "elapsed_ms": 2000}


def test_step_unknown_session_and_bad_input(client):
    r = client.post(f"/onboarding/sessions/{uuid.uuid4()}/steps", json={"step": "NOMBRES"})
    assert r.status_code == 404 and r.json()["code"] == "NOT_FOUND"
    r = client.post("/onboarding/sessions/xyz/steps", json={"step": "NOMBRES"})
    assert r.status_code == 422
    sid = client.post("/onboarding/sessions").json()["session_id"]
    r = client.post(f"/onboarding/sessions/{sid}/steps", json={"step": "OTRO"})
    assert r.status_code == 422


def test_registration_creates_basic_account(client, register, clock, password):
    sid = client.post("/onboarding/sessions").json()["session_id"]
    clock.advance(5)
    r = register(client, session_id=sid)
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["account"]["status"] == "ACTIVE_BASIC"
    assert body["account"]["balance"] == "0.00"
    assert body["account"]["currency"] == "PEN"
    uuid.UUID(body["account"]["wallet_id"])
    assert body["profile"] == {
        "estado_c1": "PENDING_EMAIL",
        "estado_c2": "PENDING_MOVIL",
        "estado_c3": "PENDING_BIOM",
    }
    assert body["welcome"]["display_name"] == "María José"
    assert body["registration_duration_ms"] == 5000
    rule = body["operation_conditions"]["rules"][0]
    assert rule["per_operation_max"] == "20.00" and rule["daily_max"] == "60.00"
    assert body["operation_conditions"]["timezone"] == "America/Lima"
    assert password not in r.text


def test_registration_without_session_has_no_duration(register, client):
    assert register(client).json()["registration_duration_ms"] is None


def test_session_closed_after_registration(client, register):
    sid = client.post("/onboarding/sessions").json()["session_id"]
    assert register(client, session_id=sid).status_code == 201
    r = client.post(f"/onboarding/sessions/{sid}/steps", json={"step": "USUARIO"})
    assert r.status_code == 409 and r.json()["code"] == "SESSION_CLOSED"
    r = register(client, usuario="otro1", session_id=sid)
    assert r.status_code == 409 and r.json()["code"] == "SESSION_CLOSED"


def test_registration_unknown_session(client, register):
    r = register(client, session_id=str(uuid.uuid4()))
    assert r.status_code == 404


def test_invalid_fields_return_422_without_echo(client, register):
    r = register(client, nombres="Maria123", password="corta")
    assert r.status_code == 422
    body = r.json()
    assert body["code"] == "VALIDATION_ERROR"
    assert {d["field"] for d in body["details"]} == {"nombres", "password"}
    assert "Maria123" not in r.text and "corta" not in r.text


def test_length_limits(client, register):
    assert register(client, nombres="a" * 31).status_code == 422
    assert register(client, apellido_paterno="a" * 21).status_code == 422
    assert register(client, apellido_materno="a" * 21).status_code == 422
    assert register(client, usuario="a" * 21).status_code == 422
    assert register(client, password="a" * 9).status_code == 422
    assert register(client, usuario="u" * 20, nombres="a" * 30).status_code == 201


def test_username_taken_returns_suggestions(client, register):
    assert register(client).status_code == 201
    r = register(client, usuario="MJQuispe")
    assert r.status_code == 409
    body = r.json()
    assert body["code"] == "USERNAME_TAKEN"
    assert body["suggestions"]


def test_username_availability(client, register):
    r = client.post("/onboarding/username-availability", json={"username": "libre_1"})
    assert r.status_code == 200 and r.json() == {"status": "AVAILABLE", "suggestions": []}
    r = client.post("/onboarding/username-availability", json={"username": "a" * 21})
    assert r.json()["status"] == "INVALID_FORMAT"
    r = client.post("/onboarding/username-availability", json={"username": "1234"})
    assert r.json()["status"] == "INVALID_FORMAT"


def test_suggestions_are_available_and_symbol_free(client, register):
    assert register(client, usuario="jperez").status_code == 201
    assert register(client, usuario="juan1").status_code == 201
    r = client.post(
        "/onboarding/username-availability",
        json={"username": "jperez", "nombres": "Juan", "apellido_paterno": "Pérez",
              "apellido_materno": "Gómez"},
    )
    body = r.json()
    assert body["status"] == "TAKEN"
    suggestions = body["suggestions"]
    assert 1 <= len(suggestions) <= 3 and len(set(suggestions)) == len(suggestions)
    assert "juan1" not in suggestions
    for s in suggestions:
        assert re.fullmatch(r"[a-z0-9]{1,20}", s)
        check = client.post("/onboarding/username-availability", json={"username": s})
        assert check.json()["status"] == "AVAILABLE"
    assert any("juan" in s or "perez" in s or "gomez" in s for s in suggestions)
