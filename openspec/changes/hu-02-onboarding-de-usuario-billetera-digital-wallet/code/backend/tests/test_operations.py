from datetime import datetime, timezone

import pytest


@pytest.fixture
def op(client):
    def _op(wid, auth, operation_type, amount):
        return client.post(
            f"/wallets/{wid}/operations",
            json={"operation_type": operation_type, "amount": amount},
            auth=auth,
        )

    return _op


@pytest.fixture
def make_full(client):
    def _full(wid, auth):
        r = client.post(
            f"/wallets/{wid}/profile/identity/mock-verification",
            json={"terms_accepted": True, "mock_inputs_confirmed": True},
            auth=auth,
        )
        assert r.status_code == 200, r.text

    return _full


# ---------------- ACTIVE_BASIC ----------------
def test_basic_per_operation_limit_exact_and_exceeded(client, new_wallet, op):
    wid, auth = new_wallet(client)
    r = op(wid, auth, "PAYMENT", "20.00")
    assert r.status_code == 201, r.text
    assert r.json()["operation_day"] == "2026-01-15"
    r = op(wid, auth, "PAYMENT", "20.01")
    assert r.status_code == 422
    assert r.json()["code"] == "PER_OPERATION_LIMIT_EXCEEDED"


def test_basic_rejects_third_party_topup(client, new_wallet, op):
    wid, auth = new_wallet(client)
    r = op(wid, auth, "TOPUP_THIRD_PARTY", "5.00")
    assert r.status_code == 422
    assert r.json()["code"] == "OPERATION_NOT_ALLOWED"


def test_basic_own_topup_accepted(client, new_wallet, op):
    wid, auth = new_wallet(client)
    assert op(wid, auth, "TOPUP_OWN", "10.00").status_code == 201


def test_basic_combined_daily_limit(client, new_wallet, op):
    wid, auth = new_wallet(client)
    assert op(wid, auth, "TOPUP_OWN", "20.00").status_code == 201
    assert op(wid, auth, "TOPUP_OWN", "20.00").status_code == 201
    r = op(wid, auth, "PAYMENT", "20.00")
    assert r.status_code == 201
    assert r.json()["daily_accumulated"] in ("60.00", "60")
    r = op(wid, auth, "PAYMENT", "1.00")
    assert r.status_code == 422
    assert r.json()["code"] == "DAILY_LIMIT_EXCEEDED"


def test_rejected_operation_is_not_accumulated(client, new_wallet, op):
    wid, auth = new_wallet(client)
    assert op(wid, auth, "PAYMENT", "25.00").status_code == 422
    for _ in range(3):
        assert op(wid, auth, "PAYMENT", "20.00").status_code == 201


def test_amount_must_be_positive(client, new_wallet, op):
    wid, auth = new_wallet(client)
    assert op(wid, auth, "PAYMENT", "0").status_code == 422


# ---------------- Día en Perú ----------------
def test_daily_counter_resets_at_lima_midnight(client, clock, new_wallet, op):
    wid, auth = new_wallet(client)
    for _ in range(3):
        assert op(wid, auth, "PAYMENT", "20.00").status_code == 201
    # 23:59:59 en Lima (04:59:59 UTC del día siguiente): mismo día, sigue rechazando
    clock.set(datetime(2026, 1, 16, 4, 59, 59, tzinfo=timezone.utc))
    r = op(wid, auth, "PAYMENT", "1.00")
    assert r.status_code == 422
    assert r.json()["code"] == "DAILY_LIMIT_EXCEEDED"
    # 00:00:00 en Lima: contador reiniciado
    clock.set(datetime(2026, 1, 16, 5, 0, 0, tzinfo=timezone.utc))
    r = op(wid, auth, "PAYMENT", "20.00")
    assert r.status_code == 201
    assert r.json()["operation_day"] == "2026-01-16"


# ---------------- ACTIVE_FULL ----------------
def test_full_topup_without_per_operation_limit(client, new_wallet, op, make_full):
    wid, auth = new_wallet(client)
    make_full(wid, auth)
    assert op(wid, auth, "TOPUP_THIRD_PARTY", "1000.00").status_code == 201
    r = op(wid, auth, "TOPUP_OWN", "0.01")
    assert r.status_code == 422
    assert r.json()["code"] == "DAILY_LIMIT_EXCEEDED"


def test_full_payment_limits(client, new_wallet, op, make_full):
    wid, auth = new_wallet(client)
    make_full(wid, auth)
    r = op(wid, auth, "PAYMENT", "500.01")
    assert r.status_code == 422
    assert r.json()["code"] == "PER_OPERATION_LIMIT_EXCEEDED"
    assert op(wid, auth, "PAYMENT", "500.00").status_code == 201
    assert op(wid, auth, "PAYMENT", "500.00").status_code == 201
    r = op(wid, auth, "PAYMENT", "0.01")
    assert r.status_code == 422
    assert r.json()["code"] == "DAILY_LIMIT_EXCEEDED"


def test_full_topup_and_payment_have_separate_daily_counters(client, new_wallet, op, make_full):
    wid, auth = new_wallet(client)
    make_full(wid, auth)
    assert op(wid, auth, "TOPUP_OWN", "1000.00").status_code == 201
    assert op(wid, auth, "PAYMENT", "500.00").status_code == 201


def test_operations_require_auth(client, new_wallet):
    wid, _ = new_wallet(client)
    r = client.post(
        f"/wallets/{wid}/operations", json={"operation_type": "PAYMENT", "amount": "1.00"}
    )
    assert r.status_code == 401
