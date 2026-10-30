import logging


def test_logs_no_contienen_password_ni_datos_personales(client, register, password, caplog):
    caplog.set_level(logging.DEBUG)
    r = register(client, usuario="privuser")
    assert r.status_code == 201
    wid = r.json()["account"]["wallet_id"]
    client.post(
        f"/wallets/{wid}/profile/email/otp-requests",
        json={"email": "secreto.privado@example.com"},
        auth=("privuser", password),
    )
    client.post(
        f"/wallets/{wid}/profile/phone/otp-requests",
        json={"phone": "987654321"},
        auth=("privuser", password),
    )
    text = caplog.text
    assert password not in text
    assert "secreto.privado" not in text
    assert "987654321" not in text
    assert "Quispe" not in text
    assert "Rojas" not in text


def test_error_422_no_devuelve_los_valores_recibidos(client, register):
    r = register(client, usuario="privuser2", nombres="Zz9Marker", password="Qq1x")
    assert r.status_code == 422
    assert "Zz9Marker" not in r.text
    assert "Qq1x" not in r.text
