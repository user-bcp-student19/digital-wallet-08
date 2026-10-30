EXPECTED = {
    ("post", "/onboarding/sessions"): "startOnboardingSession",
    ("post", "/onboarding/sessions/{session_id}/steps"): "registerOnboardingStep",
    ("post", "/onboarding/username-availability"): "checkUsernameAvailability",
    ("post", "/onboarding/registrations"): "registerWallet",
    ("get", "/wallets/{wallet_id}"): "getWallet",
    ("post", "/wallets/{wallet_id}/operations"): "registerOperation",
    ("post", "/wallets/{wallet_id}/profile/email/otp-requests"): "requestEmailOtp",
    ("post", "/wallets/{wallet_id}/profile/email/otp-confirmations"): "confirmEmailOtp",
    ("post", "/wallets/{wallet_id}/profile/phone/otp-requests"): "requestPhoneOtp",
    ("post", "/wallets/{wallet_id}/profile/phone/otp-confirmations"): "confirmPhoneOtp",
    ("post", "/wallets/{wallet_id}/profile/identity/mock-verification"): "mockIdentityVerification",
}


def test_openapi_expone_las_rutas_y_operation_ids_del_contrato(client):
    spec = client.get("/openapi.json").json()
    found = {}
    for path, methods in spec["paths"].items():
        for method, op in methods.items():
            found[(method, path)] = op.get("operationId")
    for key, operation_id in EXPECTED.items():
        assert key in found, key
        assert found[key] == operation_id
    assert set(found) == set(EXPECTED)
