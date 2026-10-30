# Informe Backend

Proyecto FastAPI completo generado a partir de architecture.mmd, sequence.mmd y openapi.yaml.

Carpeta: `output/backend-python/api`

Ejecución: `pip install -r requirements.txt` y `uvicorn app.main:app --reload` (puerto 8000); pruebas: `pytest`.

## Archivos
- `.env.example`
- `.gitignore`
- `Dockerfile`
- `README.md`
- `app/__init__.py`
- `app/clients/__init__.py`
- `app/clients/wallet_gateway.py`
- `app/config.py`
- `app/dependencies.py`
- `app/errors.py`
- `app/main.py`
- `app/repositories/__init__.py`
- `app/repositories/limits_repository.py`
- `app/repositories/otp_repository.py`
- `app/repositories/session_repository.py`
- `app/repositories/user_repository.py`
- `app/routers/__init__.py`
- `app/routers/biometric.py`
- `app/routers/common.py`
- `app/routers/profile.py`
- `app/routers/sessions.py`
- `app/routers/usernames.py`
- `app/routers/users.py`
- `app/routers/verifications.py`
- `app/schemas/__init__.py`
- `app/schemas/common.py`
- `app/schemas/errors.py`
- `app/schemas/onboarding.py`
- `app/schemas/profile.py`
- `app/schemas/users.py`
- `app/schemas/verifications.py`
- `app/services/__init__.py`
- `app/services/availability_service.py`
- `app/services/biometric_service.py`
- `app/services/clock.py`
- `app/services/ids.py`
- `app/services/limits_service.py`
- `app/services/observability.py`
- `app/services/otp_service.py`
- `app/services/profile_service.py`
- `app/services/security.py`
- `app/services/session_service.py`
- `app/services/user_service.py`
- `app/services/verification_service.py`
- `pytest.ini`
- `requirements.txt`
- `tests/__init__.py`
- `tests/conftest.py`
- `tests/helpers.py`
- `tests/test_biometric.py`
- `tests/test_observability.py`
- `tests/test_profile_wallet.py`
- `tests/test_sessions.py`
- `tests/test_usernames.py`
- `tests/test_users.py`
- `tests/test_verifications.py`
- `tests/test_wallet_gateway.py`
