import uuid


def test_requires_credentials(client, new_wallet):
    wid, _ = new_wallet(client)
    r = client.get(f"/wallets/{wid}")
    assert r.status_code == 401
    assert r.json()["code"] == "UNAUTHORIZED"
    assert r.headers["www-authenticate"] == "Basic"


def test_wrong_password_and_unknown_user(client, new_wallet):
    wid, (user, _) = new_wallet(client)
    assert client.get(f"/wallets/{wid}", auth=(user, "incorrecta123")).status_code == 401
    assert client.get(f"/wallets/{wid}", auth=("nadie", "incorrecta123")).status_code == 401


def test_other_wallet_forbidden_and_missing_not_found(client, new_wallet):
    wid_a, auth_a = new_wallet(client, "usuarioa")
    wid_b, _ = new_wallet(client, "usuariob")
    r = client.get(f"/wallets/{wid_b}", auth=auth_a)
    assert r.status_code == 403 and r.json()["code"] == "FORBIDDEN"
    r = client.get(f"/wallets/{uuid.uuid4()}", auth=auth_a)
    assert r.status_code == 404
    assert client.get("/wallets/no-es-uuid", auth=auth_a).status_code == 422
    assert client.get(f"/wallets/{wid_a}", auth=auth_a).status_code == 200


def test_wallet_detail(client, new_wallet):
    wid, auth = new_wallet(client)
    body = client.get(f"/wallets/{wid}", auth=auth).json()
    assert body["account"]["status"] == "ACTIVE_BASIC"
    assert body["identity_mock_available"] is True
    assert body["profile"]["estado_c3"] == "PENDING_BIOM"
    assert "password" not in str(body).lower()


def test_unknown_route_uses_error_schema(client):
    r = client.get("/no-existe")
    assert r.status_code == 404 and r.json()["code"] == "NOT_FOUND"
