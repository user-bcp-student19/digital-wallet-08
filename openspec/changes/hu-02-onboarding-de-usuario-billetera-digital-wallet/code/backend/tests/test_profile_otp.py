import pytest

CHANNELS = {
    "email": {
        "payload": {"email": "ana@example.com"},
        "state": "estado_c1",
        "pending": "PENDING_EMAIL",
        "active": "ACTIVE_EMAIL",
        "dup": "EMAIL_ALREADY_REGISTERED",
        "db": "EMAIL",
    },
    "phone": {
        "payload": {"phone": "912345678"},
        "state": "estado_c2",
        "pending": "PENDING_MOVIL",
        "active": "ACTIVE_MOVIL",
        "dup": "PHONE_ALREADY_REGISTERED",
        "db": "PHONE",
    },
}


def req(client, wid, auth, ch, payload=None):
    return client.post(
        f"/wallets/{wid}/profile/{ch}/otp-requests",
        json=payload or CHANNELS[ch]["payload"],
        auth=auth,
    )


def confirm(client, wid, auth, ch, otp="000000"):
    return client.post(f"/wallets/{wid}/profile/{ch}/otp-confirmations", json={"otp": otp}, auth=auth)


def profile(client, wid, auth):
    return client.get(f"/wallets/{wid}", auth=auth).json()["profile"]


@pytest.mark.parametrize("ch", ["email", "phone"])
def test_otp_issued_without_delivery(client, new_wallet, ch):
    wid, auth = new_wallet(client)
    r = req(client, wid, auth, ch)
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["otp_length"] == 6 and body["expires_in_seconds"] == 60
    assert body["delivery"] == "MOCK_NOT_SENT"
    assert "otp" not in body and "code" not in body
    if ch == "phone":
        assert body["phone_e164"] == "+51912345678"


@pytest.mark.parametrize("ch", ["email", "phone"])
def test_confirm_any_value_activates_state(client, new_wallet, clock, ch):
    cfg = CHANNELS[ch]
    wid, auth = new_wallet(client)
    req(client, wid, auth, ch)
    clock.advance(59)
    r = confirm(client, wid, auth, ch, "abc")
    assert r.status_code == 200, r.text
    prof = r.json()["profile"]
    assert prof[cfg["state"]] == cfg["active"]
    others = [k for k in ("estado_c1", "estado_c2", "estado_c3") if k != cfg["state"]]
    assert all(prof[k].startswith("PENDING") for k in others)


@pytest.mark.parametrize("ch", ["email", "phone"])
def test_expired_otp_rejected(client, new_wallet, clock, ch):
    cfg = CHANNELS[ch]
    wid, auth = new_wallet(client)
    req(client, wid, auth, ch)
    clock.advance(61)
    r = confirm(client, wid, auth, ch)
    assert r.status_code == 422 and r.json()["code"] == "OTP_EXPIRED"
    assert profile(client, wid, auth)[cfg["state"]] == cfg["pending"]


@pytest.mark.parametrize("ch", ["email", "phone"])
def test_confirm_without_request_or_twice(client, new_wallet, ch):
    wid, auth = new_wallet(client)
    r = confirm(client, wid, auth, ch)
    assert r.status_code == 422 and r.json()["code"] == "OTP_NOT_ACTIVE"
    req(client, wid, auth, ch)
    assert confirm(client, wid, auth, ch).status_code == 200
    r = confirm(client, wid, auth, ch)
    assert r.status_code == 422 and r.json()["code"] == "OTP_NOT_ACTIVE"


@pytest.mark.parametrize("ch", ["email", "phone"])
def test_rate_limit_45_seconds(client, new_wallet, clock, ch):
    wid, auth = new_wallet(client)
    assert req(client, wid, auth, ch).status_code == 201
    clock.advance(44)
    r = req(client, wid, auth, ch)
    assert r.status_code == 429
    assert r.json()["code"] == "OTP_RATE_LIMITED"
    assert r.json()["retry_after_seconds"] == 1
    assert r.headers["retry-after"] == "1"
    clock.advance(1)
    assert req(client, wid, auth, ch).status_code == 201


@pytest.mark.parametrize("ch", ["email", "phone"])
def test_new_otp_invalidates_previous(client, new_wallet, clock, ch):
    wid, auth = new_wallet(client)
    req(client, wid, auth, ch)
    clock.advance(45)
    req(client, wid, auth, ch)
    with client.app.state.ctx.db.transaction() as c:
        rows = c.execute(
            "SELECT status FROM otp_challenges WHERE wallet_id=? AND channel=? ORDER BY rowid",
            (wid, CHANNELS[ch]["db"]),
        ).fetchall()
    assert [r["status"] for r in rows] == ["INVALIDATED", "ACTIVE"]


@pytest.mark.parametrize("ch", ["email", "phone"])
def test_already_validated(client, new_wallet, ch):
    wid, auth = new_wallet(client)
    req(client, wid, auth, ch)
    confirm(client, wid, auth, ch)
    r = req(client, wid, auth, ch)
    assert r.status_code == 409 and r.json()["code"] == "ALREADY_VALIDATED"


@pytest.mark.parametrize("ch", ["email", "phone"])
def test_destination_registered_by_other_user(client, new_wallet, ch):
    wid_a, auth_a = new_wallet(client, "usuarioa")
    wid_b, auth_b = new_wallet(client, "usuariob")
    req(client, wid_a, auth_a, ch)
    confirm(client, wid_a, auth_a, ch)
    r = req(client, wid_b, auth_b, ch)
    assert r.status_code == 409 and r.json()["code"] == CHANNELS[ch]["dup"]


def test_email_uniqueness_is_case_insensitive(client, new_wallet):
    wid_a, auth_a = new_wallet(client, "usuarioa")
    wid_b, auth_b = new_wallet(client, "usuariob")
    req(client, wid_a, auth_a, "email")
    confirm(client, wid_a, auth_a, "email")
    r = req(client, wid_b, auth_b, "email", {"email": "ANA@Example.COM"})
    assert r.status_code == 409


def test_invalid_email_format(client, new_wallet):
    wid, auth = new_wallet(client)
    r = req(client, wid, auth, "email", {"email": "ana@@example"})
    assert r.status_code == 422 and r.json()["code"] == "INVALID_EMAIL_FORMAT"
    assert "ana@@example" not in r.text


@pytest.mark.parametrize("phone", ["812345678", "91234567", "9123456789", "+51912345678", "abc"])
def test_invalid_phone_format(client, new_wallet, phone):
    wid, auth = new_wallet(client)
    r = req(client, wid, auth, "phone", {"phone": phone})
    assert r.status_code == 422 and r.json()["code"] == "INVALID_PHONE_FORMAT"


def test_validations_in_any_order(client, new_wallet):
    wid, auth = new_wallet(client)
    req(client, wid, auth, "phone")
    confirm(client, wid, auth, "phone")
    assert profile(client, wid, auth)["estado_c1"] == "PENDING_EMAIL"
    req(client, wid, auth, "email")
    confirm(client, wid, auth, "email")
    prof = profile(client, wid, auth)
    assert prof["estado_c1"] == "ACTIVE_EMAIL" and prof["estado_c2"] == "ACTIVE_MOVIL"


def test_otp_requires_auth(client, new_wallet):
    wid, _ = new_wallet(client)
    r = client.post(f"/wallets/{wid}/profile/email/otp-requests", json={"email": "ana@example.com"})
    assert r.status_code == 401
