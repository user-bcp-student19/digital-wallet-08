BODY = {"terms_accepted": True, "mock_inputs_confirmed": True}


def _url(wid):
    return f"/wallets/{wid}/profile/identity/mock-verification"


def test_mock_identity_reaches_active_full_without_email_or_phone(client, new_wallet):
    wid, auth = new_wallet(client)
    r = client.post(_url(wid), json=BODY, auth=auth)
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["account"]["status"] == "ACTIVE_FULL"
    assert data["profile"]["estado_c3"] == "ACTIVE_BIOM"
    assert data["profile"]["estado_c1"] == "PENDING_EMAIL"
    assert data["profile"]["estado_c2"] == "PENDING_MOVIL"


def test_mock_identity_enabled_in_development(make_client, register):
    client = make_client("development")
    r = register(client)
    wid = r.json()["account"]["wallet_id"]
    assert client.post(_url(wid), json=BODY, auth=("mjquispe", "Clave1234567")).status_code == 200


def test_mock_identity_disabled_outside_dev_and_test(make_client, register):
    client = make_client("production")
    r = register(client)
    assert r.status_code == 201
    wid = r.json()["account"]["wallet_id"]
    auth = ("mjquispe", "Clave1234567")
    res = client.post(_url(wid), json=BODY, auth=auth)
    assert res.status_code == 403
    assert res.json()["code"] == "BIOMETRIC_MOCK_DISABLED"
    detail = client.get(f"/wallets/{wid}", auth=auth).json()
    assert detail["identity_mock_available"] is False
    assert detail["account"]["status"] == "ACTIVE_BASIC"


def test_wallet_detail_reports_mock_available_in_testing(client, new_wallet):
    wid, auth = new_wallet(client)
    detail = client.get(f"/wallets/{wid}", auth=auth).json()
    assert detail["identity_mock_available"] is True


def test_mock_identity_requires_terms(client, new_wallet):
    wid, auth = new_wallet(client)
    r = client.post(
        _url(wid), json={"terms_accepted": False, "mock_inputs_confirmed": True}, auth=auth
    )
    assert r.status_code == 422
    assert r.json()["code"] == "TERMS_NOT_ACCEPTED"
    detail = client.get(f"/wallets/{wid}", auth=auth).json()
    assert detail["account"]["status"] == "ACTIVE_BASIC"


def test_mock_identity_requires_inputs_confirmed(client, new_wallet):
    wid, auth = new_wallet(client)
    r = client.post(
        _url(wid), json={"terms_accepted": True, "mock_inputs_confirmed": False}, auth=auth
    )
    assert r.status_code == 422
    assert r.json()["code"] == "MOCK_INPUTS_INVALID"


def test_mock_identity_twice_returns_conflict(client, new_wallet):
    wid, auth = new_wallet(client)
    assert client.post(_url(wid), json=BODY, auth=auth).status_code == 200
    r = client.post(_url(wid), json=BODY, auth=auth)
    assert r.status_code == 409
    assert r.json()["code"] == "ALREADY_ACTIVE_FULL"


def test_mock_identity_requires_auth(client, new_wallet):
    wid, _ = new_wallet(client)
    assert client.post(_url(wid), json=BODY).status_code == 401
