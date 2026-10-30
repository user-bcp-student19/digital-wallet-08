# HU 01 – Onboarding de usuario, billetera digital (FastAPI)

No ejecuté el código ni las pruebas. Está escrito para Python 3.11 o superior, FastAPI y Pydantic v2.

## Estructura del proyecto

La estructura sigue el diagrama de arquitectura: un módulo por componente (REST, ONB, UNAME, SESS, PROF, OTPS, OTPM, LIM, CONS, BIOM, ADP, CFG, DB).

```
wallet-api/
├── README.md
├── requirements.txt
├── app/
│   ├── __init__.py
│   ├── main.py                    # REST: app, middleware, manejo de errores
│   ├── config.py                  # CFG: topes, zona America/Lima, ambiente
│   ├── clock.py
│   ├── errors.py                  # REST: manejo de errores (contrato Error)
│   ├── schemas.py                 # Modelos del contrato OpenAPI
│   ├── security.py                # Validación de cabecera Authorization
│   ├── db.py                      # DB: persistencia (SQLite)
│   ├── repositories.py
│   ├── container.py               # Composición de servicios
│   ├── adapters/
│   │   ├── __init__.py
│   │   └── wallet_mock.py         # ADP: cliente HTTP bcp-wallet-mock grupo 8
│   ├── services/
│   │   ├── __init__.py
│   │   ├── onboarding.py          # ONB
│   │   ├── username.py            # UNAME
│   │   ├── session_tracking.py    # SESS
│   │   ├── profile.py             # PROF (C1, C2, C3)
│   │   ├── otp.py                 # OTPS (60 s / 45 s)
│   │   ├── otp_mock.py            # OTPM
│   │   ├── limits.py              # LIM
│   │   ├── consent.py             # CONS
│   │   └── biometric.py           # BIOM (solo dev y test)
│   └── routers/
│       ├── __init__.py
│       ├── onboarding.py
│       ├── accounts.py
│       ├── profile.py
│       └── biometric.py
└── tests/
    └── test_onboarding_flow.py
```

---

## `requirements.txt`

```text
fastapi>=0.110
uvicorn[standard]>=0.29
httpx>=0.27
pydantic>=2.6
tzdata>=2024.1
# dev
pytest>=8.0
```

## `app/__init__.py`, `app/adapters/__init__.py`, `app/services/__init__.py`, `app/routers/__init__.py`

```python
# (archivo vacío)
```

---

## `app/config.py`

```python
"""CFG: configuración (topes por estado, zona horaria de negocio, ambiente, timeouts)."""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Any
from zoneinfo import ZoneInfo

STATUS_BASIC = "ACTIVE_BASIC"
STATUS_FULL = "ACTIVE_FULL"

# El flujo biométrico mock solo existe en estos ambientes (CA-12).
MOCK_ENVIRONMENTS = frozenset({"development", "dev", "test"})

# Topes parametrizables por estado (importes en céntimos de PEN). None = sin tope definido.
# SUPUESTO: la HU no fija las cifras; se pueden sobrescribir con WALLET_LIMITS_JSON.
DEFAULT_LIMITS: dict[str, dict[str, Any]] = {
    STATUS_BASIC: {
        "allowsOwnRecharge": True,
        "allowsThirdPartyRecharge": False,
        "allowsPayments": True,
        "rechargePerOperationCents": 30_000,
        "rechargeDailyCents": 60_000,
        "paymentPerOperationCents": 20_000,
        "paymentDailyCents": 40_000,
    },
    STATUS_FULL: {
        "allowsOwnRecharge": True,
        "allowsThirdPartyRecharge": True,
        "allowsPayments": True,
        "rechargePerOperationCents": 200_000,
        "rechargeDailyCents": 500_000,
        "paymentPerOperationCents": 100_000,
        "paymentDailyCents": 300_000,
    },
}


def _default_limits() -> dict[str, dict[str, Any]]:
    return json.loads(json.dumps(DEFAULT_LIMITS))


@dataclass(frozen=True)
class Settings:
    environment: str = "development"  # development | dev | test | production
    db_path: str = "wallet.db"

    # Servicio externo bcp-wallet-mock (grupo 8)
    wallet_base_url: str = "https://bcp-wallet-mock.yefri.workers.dev"
    wallet_group_id: int = 8
    wallet_connect_timeout_s: float = 2.0
    wallet_read_timeout_s: float = 5.0
    wallet_get_retries: int = 1  # solo GET (idempotente); POST KYC nunca se reintenta

    business_timezone: str = "America/Lima"

    otp_ttl_seconds: int = 60
    otp_resend_seconds: int = 45
    otp_max_attempts: int = 5
    otp_fixed_code: str | None = None  # solo se respeta fuera de producción
    otp_pepper: str = "change-me-in-prod"

    auth_enabled: bool = True
    limits: dict[str, dict[str, Any]] = field(default_factory=_default_limits)

    @property
    def env(self) -> str:
        return self.environment.strip().lower()

    @property
    def is_production(self) -> bool:
        return self.env not in MOCK_ENVIRONMENTS

    @property
    def mock_flow_enabled(self) -> bool:
        return self.env in MOCK_ENVIRONMENTS

    @property
    def tz(self) -> ZoneInfo:
        return ZoneInfo(self.business_timezone)

    @classmethod
    def from_env(cls) -> "Settings":
        env = os.getenv
        limits = _default_limits()
        if env("WALLET_LIMITS_JSON"):
            for status, overrides in json.loads(env("WALLET_LIMITS_JSON", "{}")).items():
                limits.setdefault(status, {}).update(overrides)
        return cls(
            environment=env("WALLET_ENV", "development"),
            db_path=env("WALLET_DB_PATH", "wallet.db"),
            wallet_base_url=env("WALLET_BASE_URL", cls.wallet_base_url),
            wallet_group_id=int(env("WALLET_GROUP_ID", "8")),
            wallet_connect_timeout_s=float(env("WALLET_CONNECT_TIMEOUT_S", "2")),
            wallet_read_timeout_s=float(env("WALLET_READ_TIMEOUT_S", "5")),
            wallet_get_retries=int(env("WALLET_GET_RETRIES", "1")),
            business_timezone=env("WALLET_TIMEZONE", "America/Lima"),
            otp_fixed_code=env("WALLET_OTP_FIXED_CODE") or None,
            otp_pepper=env("WALLET_OTP_PEPPER", "change-me-in-prod"),
            auth_enabled=env("WALLET_AUTH_ENABLED", "true").lower() != "false",
            limits=limits,
        )
```

## `app/clock.py`

```python
from __future__ import annotations

from datetime import datetime, timezone


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def to_iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def from_iso(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))
```

## `app/errors.py`

```python
"""REST: manejo de errores. Todas las respuestas de error siguen el esquema `Error` del contrato.
Nunca se incluyen valores de entrada (contraseñas, datos personales); solo nombre de campo y regla."""
from __future__ import annotations

import logging
from typing import Any

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger("wallet.errors")


class AppError(Exception):
    def __init__(
        self,
        status_code: int,
        code: str,
        message: str,
        *,
        fields: list[dict[str, str]] | None = None,
        headers: dict[str, str] | None = None,
        extra: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message
        self.fields = fields
        self.headers = headers
        self.extra = extra or {}


def _body(request: Request, code: str, message: str, fields=None, extra=None) -> dict[str, Any]:
    body: dict[str, Any] = {"code": code, "message": message}
    if fields:
        body["fields"] = fields
    if extra:
        body.update(extra)
    body["traceId"] = getattr(request.state, "trace_id", None)
    return body


async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content=_body(request, exc.code, exc.message, exc.fields, exc.extra),
        headers=exc.headers,
    )


async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    fields: list[dict[str, str]] = []
    path_error = False
    for err in exc.errors():
        loc = err.get("loc", ())
        if loc and loc[0] == "path":
            path_error = True
        name = ".".join(str(p) for p in loc if p not in ("body", "query", "path"))
        fields.append({"field": name or "request", "rule": str(err.get("type", "invalid"))})
    if path_error:  # identificador malformado en la ruta => recurso inexistente
        return JSONResponse(
            status_code=404, content=_body(request, "NOT_FOUND", "Recurso no encontrado")
        )
    return JSONResponse(
        status_code=400,
        content=_body(request, "INVALID_FIELD", "Entrada inválida", fields),
    )


async def http_error_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    code = {404: "NOT_FOUND", 405: "METHOD_NOT_ALLOWED"}.get(exc.status_code, "HTTP_ERROR")
    return JSONResponse(
        status_code=exc.status_code,
        content=_body(request, code, "Solicitud no válida para este recurso"),
        headers=getattr(exc, "headers", None),
    )


async def unhandled_error_handler(request: Request, exc: Exception) -> JSONResponse:
    # Se registra solo el tipo de excepción y el traceId, nunca el payload.
    logger.error(
        "Unhandled error type=%s trace=%s", type(exc).__name__, getattr(request.state, "trace_id", None)
    )
    return JSONResponse(
        status_code=500, content=_body(request, "INTERNAL_ERROR", "Error interno")
    )
```

## `app/schemas.py`

```python
"""Modelos del contrato OpenAPI (nombres camelCase tal como en el contrato)."""
from __future__ import annotations

import re
from datetime import date, datetime
from typing import Annotated, Literal
from uuid import UUID

from pydantic import AfterValidator, BaseModel, Field, StringConstraints

USERNAME_PATTERN = r"^(?=.*[A-Za-z])[\x21-\x7E]{1,20}$"
_USERNAME_RE = re.compile(USERNAME_PATTERN)  # lookahead => usamos `re` de Python


def _validate_username(value: str) -> str:
    if not _USERNAME_RE.fullmatch(value):
        raise ValueError("username_format")
    return value


FirstNames = Annotated[
    str,
    StringConstraints(
        max_length=30, pattern=r"^[A-Za-zÁÉÍÓÚÜÑáéíóúüñ]+( [A-Za-zÁÉÍÓÚÜÑáéíóúüñ]+)*$"
    ),
]
Surname = Annotated[
    str, StringConstraints(max_length=20, pattern=r"^[A-Za-zÁÉÍÓÚÜÑáéíóúüñ]+$")
]
Username = Annotated[
    str,
    StringConstraints(min_length=1, max_length=20),
    AfterValidator(_validate_username),
    Field(json_schema_extra={"pattern": USERNAME_PATTERN}),
]
Email = Annotated[str, StringConstraints(max_length=254, pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")]

OnboardingStepName = Literal[
    "PERSONAL_DATA_COMPLETED", "CREDENTIALS_COMPLETED", "ACCOUNT_CREATED", "LANDING_VISIBLE"
]
AccountStatus = Literal["ACTIVE_BASIC", "ACTIVE_FULL"]


# ---------- Errores ----------
class FieldError(BaseModel):
    field: str
    rule: str


class ErrorResponse(BaseModel):
    code: str
    message: str
    fields: list[FieldError] | None = None
    traceId: str | None = None


class UsernameTakenError(ErrorResponse):
    suggestions: list[str] = []


# ---------- Onboarding ----------
class OnboardingStepRequest(BaseModel):
    step: OnboardingStepName


class OnboardingSession(BaseModel):
    sessionId: UUID
    startedAt: datetime
    completedSteps: list[OnboardingStepName]
    completed: bool
    endedAt: datetime | None = None
    durationMs: int | None = None


class UsernameAvailability(BaseModel):
    username: str
    available: bool
    suggestions: list[str] | None = None


# ---------- Cuenta ----------
class CreateAccountRequest(BaseModel):
    firstNames: FirstNames
    paternalSurname: Surname
    maternalSurname: Surname
    username: Username
    password: Annotated[
        str,
        StringConstraints(min_length=8, max_length=64),
        Field(repr=False, json_schema_extra={"format": "password", "writeOnly": True}),
    ]
    onboardingSessionId: UUID | None = None


class ProfileStatus(BaseModel):
    emailStatus: Literal["PENDING_EMAIL", "ACTIVE_EMAIL"]
    mobileStatus: Literal["PENDING_MOVIL", "ACTIVE_MOVIL"]
    biometricStatus: Literal["PENDING_BIOM", "ACTIVE_BIOM"]


class OperationLimits(BaseModel):
    allowsOwnRecharge: bool
    allowsThirdPartyRecharge: bool
    allowsPayments: bool
    rechargePerOperationCents: int | None = None
    rechargeDailyCents: int | None = None
    paymentPerOperationCents: int | None = None
    paymentDailyCents: int | None = None


class DailyUsage(BaseModel):
    date: date
    timezone: Literal["America/Lima"]
    rechargedCents: int
    paidCents: int


class AccountCreated(BaseModel):
    accountId: UUID
    walletId: str
    status: AccountStatus
    balanceCents: Literal[0]
    currency: Literal["PEN"]
    firstNames: str
    profile: ProfileStatus


class AccountSummary(BaseModel):
    accountId: UUID
    walletId: str
    firstNames: str
    status: AccountStatus
    balanceCents: int
    currency: Literal["PEN"]
    limits: OperationLimits
    dailyUsage: DailyUsage
    profile: ProfileStatus
    profilePending: bool
    profilePendingMessage: str | None = None


# ---------- Perfil / OTP ----------
class EmailOtpRequest(BaseModel):
    email: Email


class MobileOtpRequest(BaseModel):
    mobileNumber: Annotated[str, StringConstraints(pattern=r"^9[0-9]{8}$")]


class OtpIssued(BaseModel):
    expiresAt: datetime
    nextAllowedAt: datetime
    expiresInSeconds: int
    resendAfterSeconds: int


class OtpVerificationRequest(BaseModel):
    code: Annotated[str, StringConstraints(pattern=r"^[0-9]{6}$")]


# ---------- Consentimiento / Biometría ----------
class ConsentRequest(BaseModel):
    accepted: Literal[True]
    termsVersion: Annotated[str, StringConstraints(min_length=1, max_length=20)]


class Consent(BaseModel):
    consentId: UUID
    termsVersion: str
    acceptedAt: datetime


class MockBiometricRequest(BaseModel):
    dniNumber: Annotated[str, StringConstraints(pattern=r"^[0-9]{8}$")]


class MockBiometricResult(BaseModel):
    accountId: UUID
    status: AccountStatus
    profile: ProfileStatus
    limits: OperationLimits
```

## `app/security.py`

```python
"""Validación de cabeceras. bearerAuth (opaque): el mecanismo concreto está fuera del alcance de la HU;
aquí se exige la cabecera `Authorization: Bearer <token>` bien formada (401 en caso contrario)."""
from __future__ import annotations

from fastapi import Request

from .errors import AppError


async def require_bearer(request: Request) -> None:
    settings = request.app.state.container.settings
    if not settings.auth_enabled:
        return
    header = request.headers.get("authorization", "")
    scheme, _, token = header.partition(" ")
    if scheme.lower() != "bearer" or not token.strip():
        raise AppError(
            401,
            "UNAUTHORIZED",
            "No autenticado",
            headers={"WWW-Authenticate": "Bearer"},
        )
```

## `app/db.py`

```python
"""DB: persistencia de usuarios, cuentas, perfil, OTP, consentimientos y sesiones (SQLite).
Nota: el acceso es síncrono y breve, protegido por un RLock. Para producción real cambiar a un
motor cliente-servidor con driver asíncrono manteniendo esta interfaz."""
from __future__ import annotations

import sqlite3
import threading
from contextlib import contextmanager
from typing import Any, Iterator, Sequence

SCHEMA = """
CREATE TABLE IF NOT EXISTS onboarding_sessions (
    id TEXT PRIMARY KEY,
    started_at TEXT NOT NULL,
    ended_at TEXT,
    duration_ms INTEGER,
    completed INTEGER NOT NULL DEFAULT 0,
    steps TEXT NOT NULL DEFAULT '[]'
);
CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    first_names TEXT NOT NULL,
    paternal_surname TEXT NOT NULL,
    maternal_surname TEXT NOT NULL,
    username TEXT NOT NULL,
    username_key TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS accounts (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES users(id),
    wallet_id TEXT NOT NULL UNIQUE,
    status TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS profiles (
    account_id TEXT PRIMARY KEY REFERENCES accounts(id),
    email TEXT UNIQUE,
    email_status TEXT NOT NULL DEFAULT 'PENDING_EMAIL',
    mobile TEXT UNIQUE,
    mobile_status TEXT NOT NULL DEFAULT 'PENDING_MOVIL',
    biometric_status TEXT NOT NULL DEFAULT 'PENDING_BIOM'
);
CREATE TABLE IF NOT EXISTS otps (
    id TEXT PRIMARY KEY,
    account_id TEXT NOT NULL REFERENCES accounts(id),
    channel TEXT NOT NULL,
    target TEXT NOT NULL,
    code_hash TEXT NOT NULL,
    created_at TEXT NOT NULL,
    expires_at TEXT NOT NULL,
    attempts INTEGER NOT NULL DEFAULT 0,
    state TEXT NOT NULL DEFAULT 'ACTIVE'
);
CREATE INDEX IF NOT EXISTS idx_otps_lookup ON otps(account_id, channel, created_at);
CREATE TABLE IF NOT EXISTS consents (
    id TEXT PRIMARY KEY,
    account_id TEXT NOT NULL REFERENCES accounts(id),
    terms_version TEXT NOT NULL,
    accepted_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS daily_usage (
    account_id TEXT NOT NULL REFERENCES accounts(id),
    day TEXT NOT NULL,
    recharged_cents INTEGER NOT NULL DEFAULT 0,
    paid_cents INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (account_id, day)
);
"""


class Database:
    def __init__(self, path: str) -> None:
        self._conn = sqlite3.connect(path, check_same_thread=False, isolation_level=None)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA foreign_keys = ON")
        self._lock = threading.RLock()

    def init_schema(self) -> None:
        with self._lock:
            self._conn.executescript(SCHEMA)

    def execute(self, sql: str, params: Sequence[Any] = ()) -> int:
        with self._lock:
            return self._conn.execute(sql, params).rowcount

    def fetchone(self, sql: str, params: Sequence[Any] = ()) -> sqlite3.Row | None:
        with self._lock:
            return self._conn.execute(sql, params).fetchone()

    def fetchall(self, sql: str, params: Sequence[Any] = ()) -> list[sqlite3.Row]:
        with self._lock:
            return self._conn.execute(sql, params).fetchall()

    @contextmanager
    def transaction(self) -> Iterator[None]:
        with self._lock:
            self._conn.execute("BEGIN IMMEDIATE")
            try:
                yield
            except BaseException:
                self._conn.execute("ROLLBACK")
                raise
            else:
                self._conn.execute("COMMIT")

    def close(self) -> None:
        with self._lock:
            self._conn.close()
```

## `app/repositories.py`

```python
from __future__ import annotations

import sqlite3

from .db import Database


class AccountRepository:
    def __init__(self, db: Database) -> None:
        self._db = db

    def get(self, account_id: str) -> sqlite3.Row | None:
        return self._db.fetchone(
            """SELECT a.id, a.wallet_id, a.status, u.first_names
               FROM accounts a JOIN users u ON u.id = a.user_id WHERE a.id = ?""",
            (account_id,),
        )

    def exists(self, account_id: str) -> bool:
        return self._db.fetchone("SELECT 1 FROM accounts WHERE id = ?", (account_id,)) is not None

    def get_profile(self, account_id: str) -> dict[str, str] | None:
        row = self._db.fetchone(
            "SELECT email_status, mobile_status, biometric_status FROM profiles WHERE account_id = ?",
            (account_id,),
        )
        if row is None:
            return None
        return {
            "emailStatus": row["email_status"],
            "mobileStatus": row["mobile_status"],
            "biometricStatus": row["biometric_status"],
        }

    def get_daily_usage(self, account_id: str, day: str) -> tuple[int, int]:
        row = self._db.fetchone(
            "SELECT recharged_cents, paid_cents FROM daily_usage WHERE account_id = ? AND day = ?",
            (account_id, day),
        )
        return (row["recharged_cents"], row["paid_cents"]) if row else (0, 0)
```

---

## `app/adapters/wallet_mock.py`

```python
"""ADP: adaptador (cliente HTTP) del servicio externo bcp-wallet-mock grupo 8.

Mapeo (contrato OpenAPI local):
  POST /groups/8/kyc/verifications
      201 -> wallet_id | 400/413 -> 502 EXTERNAL_BAD_REQUEST | otras 4xx/5xx -> 502 EXTERNAL_ERROR
      timeout/sin conexión -> 504 EXTERNAL_TIMEOUT
  GET /groups/8/wallets/{wallet_id}
      200 -> saldo | 404 -> 502 WALLET_NOT_FOUND_EXTERNAL | otras 4xx/5xx -> 502 EXTERNAL_ERROR
      timeout/sin conexión -> 504 EXTERNAL_TIMEOUT

El header X-Mock-Latency-Ms no se propaga (nunca se copian cabeceras externas a la respuesta local).

SUPUESTOS (el contrato externo recibido está truncado, confirmar con el informe):
  * Cuerpo del KYC: first_names, paternal_surname, maternal_surname  -> ver `_build_kyc_payload`.
  * Respuesta Kyc: campo `wallet_id`.
  * Saldo del wallet: se busca en `_BALANCE_KEYS` (entero en céntimos PEN).
Todos los supuestos están aislados en este módulo.
"""
from __future__ import annotations

import asyncio
import logging
from typing import Any
from urllib.parse import quote

import httpx

from ..config import Settings
from ..errors import AppError

logger = logging.getLogger("wallet.adapter")

_WALLET_ID_KEYS = ("wallet_id", "walletId")
_BALANCE_KEYS = ("balance_cents", "balanceCents", "balance", "saldo_cents", "saldo", "amount_cents")


def _timeout_error() -> AppError:
    return AppError(504, "EXTERNAL_TIMEOUT", "El servicio de wallet no respondió a tiempo")


def _external_error() -> AppError:
    return AppError(502, "EXTERNAL_ERROR", "Error en el servicio de wallet")


def _as_int(value: Any) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float) and value.is_integer():
        return int(value)
    if isinstance(value, str) and value.isdigit():
        return int(value)
    return None


class WalletMockClient:
    def __init__(self, settings: Settings, client: httpx.AsyncClient | None = None) -> None:
        self._base = f"{settings.wallet_base_url.rstrip('/')}/groups/{settings.wallet_group_id}"
        self._get_retries = max(0, settings.wallet_get_retries)
        self._client = client or httpx.AsyncClient(
            timeout=httpx.Timeout(
                settings.wallet_read_timeout_s,
                connect=settings.wallet_connect_timeout_s,
            ),
            headers={"Accept": "application/json"},
        )

    async def aclose(self) -> None:
        await self._client.aclose()

    # ------------------------------------------------------------------ KYC
    @staticmethod
    def _build_kyc_payload(first_names: str, paternal_surname: str, maternal_surname: str) -> dict:
        # SUPUESTO: nombres de campos del contrato externo. Nunca se envía la contraseña.
        return {
            "first_names": first_names,
            "paternal_surname": paternal_surname,
            "maternal_surname": maternal_surname,
        }

    async def create_kyc_wallet(
        self, *, first_names: str, paternal_surname: str, maternal_surname: str
    ) -> str:
        url = f"{self._base}/kyc/verifications"
        payload = self._build_kyc_payload(first_names, paternal_surname, maternal_surname)
        try:
            # POST no idempotente: sin reintentos para no duplicar wallets.
            resp = await self._client.post(url, json=payload)
        except (httpx.TimeoutException, httpx.TransportError):
            logger.warning("KYC timeout/transport error")
            raise _timeout_error()
        except httpx.HTTPError:
            raise _external_error()

        if resp.status_code == 201:
            wallet_id = self._extract_wallet_id(resp)
            if wallet_id is None:
                logger.error("KYC 201 sin wallet_id")
                raise _external_error()
            return wallet_id
        if resp.status_code in (400, 413):
            logger.warning("KYC rechazado status=%s", resp.status_code)
            raise AppError(502, "EXTERNAL_BAD_REQUEST", "El servicio de wallet rechazó la solicitud")
        logger.warning("KYC status inesperado=%s", resp.status_code)
        raise _external_error()

    @staticmethod
    def _extract_wallet_id(resp: httpx.Response) -> str | None:
        try:
            data = resp.json()
        except ValueError:
            return None
        if not isinstance(data, dict):
            return None
        for key in _WALLET_ID_KEYS:
            value = data.get(key)
            if isinstance(value, (str, int)) and not isinstance(value, bool) and str(value):
                return str(value)
        return None

    # --------------------------------------------------------------- Wallet
    async def get_wallet_balance_cents(self, wallet_id: str) -> int:
        url = f"{self._base}/wallets/{quote(wallet_id, safe='')}"
        last_exc: AppError | None = None
        for attempt in range(self._get_retries + 1):
            try:
                resp = await self._client.get(url)
            except (httpx.TimeoutException, httpx.TransportError):
                last_exc = _timeout_error()
            except httpx.HTTPError:
                last_exc = _external_error()
            else:
                if resp.status_code == 200:
                    return self._extract_balance(resp)
                if resp.status_code == 404:
                    raise AppError(
                        502, "WALLET_NOT_FOUND_EXTERNAL", "Wallet no encontrado en el servicio externo"
                    )
                last_exc = _external_error()
                if resp.status_code < 500:  # 4xx no se reintenta
                    raise last_exc
            if attempt < self._get_retries:
                await asyncio.sleep(0.1 * (attempt + 1))
        assert last_exc is not None
        raise last_exc

    @staticmethod
    def _extract_balance(resp: httpx.Response) -> int:
        try:
            data = resp.json()
        except ValueError:
            raise _external_error()
        if not isinstance(data, dict):
            raise _external_error()
        sources = [data]
        if isinstance(data.get("wallet"), dict):
            sources.append(data["wallet"])
        for source in sources:
            for key in _BALANCE_KEYS:
                if key in source:
                    value = _as_int(source[key])
                    if value is not None:
                        return value
        logger.error("Respuesta de wallet sin saldo reconocible")
        raise _external_error()
```

---

## `app/services/username.py` (UNAME)

```python
"""UNAME: disponibilidad de usuario y sugerencias (sin símbolos, basadas en nombres, apellidos y números)."""
from __future__ import annotations

import re
import secrets
import unicodedata

from ..db import Database


def _alnum(text: str) -> str:
    ascii_text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    return re.sub(r"[^A-Za-z0-9]", "", ascii_text)


class UsernameService:
    def __init__(self, db: Database) -> None:
        self._db = db

    @staticmethod
    def key(username: str) -> str:
        return username.lower()

    def is_available(self, username: str) -> bool:
        row = self._db.fetchone("SELECT 1 FROM users WHERE username_key = ?", (self.key(username),))
        return row is None

    def suggestions(
        self,
        username: str,
        first_names: str | None = None,
        paternal_surname: str | None = None,
        maternal_surname: str | None = None,
        limit: int = 3,
    ) -> list[str]:
        first = _alnum((first_names or "").split(" ")[0])
        pat = _alnum(paternal_surname or "")
        mat = _alnum(maternal_surname or "")
        base = _alnum(username)

        stems: list[str] = []
        for stem in (first + pat, first[:1] + pat, pat + mat[:1], first + mat[:1], first, pat, base):
            if stem and stem not in stems:
                stems.append(stem)

        result: list[str] = []

        def consider(candidate: str) -> None:
            candidate = candidate[:20]
            if (
                candidate
                and candidate not in result
                and self.key(candidate) != self.key(username)
                and self.is_available(candidate)
            ):
                result.append(candidate)

        for stem in stems:
            if len(result) >= limit:
                break
            consider(stem)
            for _ in range(2):
                if len(result) >= limit:
                    break
                consider(f"{stem[:17]}{secrets.randbelow(900) + 100}")

        tries = 0
        while len(result) < limit and tries < 20 and (base or stems):
            consider(f"{(base or stems[0])[:16]}{secrets.randbelow(9000) + 1000}")
            tries += 1
        return result[:limit]
```

## `app/services/session_tracking.py` (SESS)

```python
"""SESS: seguimiento de onboarding (medición de tiempo y pasos, CA-01 y CA-03)."""
from __future__ import annotations

import json
import logging
import uuid
from typing import Any, Callable
from datetime import datetime

from ..clock import from_iso, to_iso
from ..db import Database
from ..errors import AppError

logger = logging.getLogger("wallet.sessions")
LANDING_VISIBLE = "LANDING_VISIBLE"


class SessionTrackingService:
    def __init__(self, db: Database, clock: Callable[[], datetime]) -> None:
        self._db = db
        self._clock = clock

    @staticmethod
    def _to_dto(row) -> dict[str, Any]:
        return {
            "sessionId": row["id"],
            "startedAt": row["started_at"],
            "completedSteps": json.loads(row["steps"]),
            "completed": bool(row["completed"]),
            "endedAt": row["ended_at"],
            "durationMs": row["duration_ms"],
        }

    def start(self) -> dict[str, Any]:
        session_id = str(uuid.uuid4())
        started = to_iso(self._clock())
        self._db.execute(
            "INSERT INTO onboarding_sessions (id, started_at, steps) VALUES (?, ?, '[]')",
            (session_id, started),
        )
        return self._to_dto(
            self._db.fetchone("SELECT * FROM onboarding_sessions WHERE id = ?", (session_id,))
        )

    def register_step(self, session_id: str, step: str) -> dict[str, Any]:
        with self._db.transaction():
            row = self._db.fetchone("SELECT * FROM onboarding_sessions WHERE id = ?", (session_id,))
            if row is None:
                raise AppError(404, "NOT_FOUND", "Sesión de onboarding no encontrada")
            if row["completed"]:
                # Idempotente para el mismo paso de cierre ya registrado; si no, 409.
                raise AppError(409, "SESSION_CLOSED", "La sesión de onboarding ya está cerrada")
            steps: list[str] = json.loads(row["steps"])
            if step not in steps:
                steps.append(step)
            if step == LANDING_VISIBLE:
                now = self._clock()
                duration = int((now - from_iso(row["started_at"])).total_seconds() * 1000)
                self._db.execute(
                    """UPDATE onboarding_sessions
                       SET steps = ?, completed = 1, ended_at = ?, duration_ms = ? WHERE id = ?""",
                    (json.dumps(steps), to_iso(now), max(duration, 0), session_id),
                )
            else:
                self._db.execute(
                    "UPDATE onboarding_sessions SET steps = ? WHERE id = ?",
                    (json.dumps(steps), session_id),
                )
        return self._to_dto(
            self._db.fetchone("SELECT * FROM onboarding_sessions WHERE id = ?", (session_id,))
        )

    def try_register_step(self, session_id: str, step: str) -> None:
        """Best effort: la medición nunca debe romper la creación de la cuenta."""
        try:
            self.register_step(session_id, step)
        except AppError:
            logger.info("Paso %s no registrado en sesión (inexistente o cerrada)", step)
```

## `app/services/otp_mock.py` (OTPM)

```python
"""OTPM: generador de OTP mock para correo y SMS. No envía nada."""
from __future__ import annotations

import logging
import secrets

from ..config import Settings

logger = logging.getLogger("wallet.otp_mock")


class OtpMockGenerator:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def generate(self, account_id: str, channel: str) -> str:
        if self._settings.otp_fixed_code and not self._settings.is_production:
            code = self._settings.otp_fixed_code
        else:
            code = f"{secrets.randbelow(1_000_000):06d}"
        if not self._settings.is_production:
            # Único canal de "entrega" del mock: log de desarrollo (sin correo ni teléfono).
            logger.warning("[OTP-MOCK] channel=%s account=%s code=%s", channel, account_id, code)
        return code
```

## `app/services/otp.py` (OTPS)

```python
"""OTPS: vigencia 60 s, reenvío cada 45 s, un OTP nuevo invalida los anteriores."""
from __future__ import annotations

import hashlib
import hmac
import math
import uuid
from datetime import datetime, timedelta
from typing import Any, Callable

from ..clock import from_iso, to_iso
from ..config import Settings
from ..db import Database
from ..errors import AppError
from .otp_mock import OtpMockGenerator


class OtpService:
    def __init__(
        self,
        db: Database,
        generator: OtpMockGenerator,
        settings: Settings,
        clock: Callable[[], datetime],
    ) -> None:
        self._db = db
        self._gen = generator
        self._settings = settings
        self._clock = clock

    def _hash(self, otp_id: str, code: str) -> str:
        return hmac.new(
            self._settings.otp_pepper.encode(), f"{otp_id}:{code}".encode(), hashlib.sha256
        ).hexdigest()

    def issue(self, account_id: str, channel: str, target: str) -> dict[str, Any]:
        ttl = self._settings.otp_ttl_seconds
        resend = self._settings.otp_resend_seconds
        now = self._clock()
        with self._db.transaction():
            last = self._db.fetchone(
                """SELECT created_at FROM otps WHERE account_id = ? AND channel = ?
                   ORDER BY created_at DESC LIMIT 1""",
                (account_id, channel),
            )
            if last is not None:
                next_allowed = from_iso(last["created_at"]) + timedelta(seconds=resend)
                if now < next_allowed:
                    remaining = max(1, min(resend, math.ceil((next_allowed - now).total_seconds())))
                    raise AppError(
                        429,
                        "OTP_TOO_SOON",
                        "Debes esperar antes de solicitar otro código",
                        headers={"Retry-After": str(remaining)},
                    )
            code = self._gen.generate(account_id, channel)
            otp_id = str(uuid.uuid4())
            self._db.execute(
                "UPDATE otps SET state = 'INVALIDATED' WHERE account_id = ? AND channel = ? AND state = 'ACTIVE'",
                (account_id, channel),
            )
            self._db.execute(
                """INSERT INTO otps (id, account_id, channel, target, code_hash, created_at, expires_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    otp_id,
                    account_id,
                    channel,
                    target,
                    self._hash(otp_id, code),
                    to_iso(now),
                    to_iso(now + timedelta(seconds=ttl)),
                ),
            )
        return {
            "expiresAt": now + timedelta(seconds=ttl),
            "nextAllowedAt": now + timedelta(seconds=resend),
            "expiresInSeconds": ttl,
            "resendAfterSeconds": resend,
        }

    def verify(self, account_id: str, channel: str, code: str) -> str:
        """Devuelve el `target` verificado o lanza OTP_INVALID / OTP_EXPIRED."""
        now = self._clock()
        error: tuple[str, str] | None = None
        with self._db.transaction():
            row = self._db.fetchone(
                """SELECT * FROM otps WHERE account_id = ? AND channel = ? AND state = 'ACTIVE'
                   ORDER BY created_at DESC LIMIT 1""",
                (account_id, channel),
            )
            if row is None:
                error = ("OTP_INVALID", "Código inválido")
            elif now >= from_iso(row["expires_at"]):
                error = ("OTP_EXPIRED", "El código venció, solicita uno nuevo")
            elif hmac.compare_digest(row["code_hash"], self._hash(row["id"], code)):
                self._db.execute("UPDATE otps SET state = 'CONSUMED' WHERE id = ?", (row["id"],))
                return row["target"]
            else:
                attempts = row["attempts"] + 1
                state = "INVALIDATED" if attempts >= self._settings.otp_max_attempts else "ACTIVE"
                self._db.execute(
                    "UPDATE otps SET attempts = ?, state = ? WHERE id = ?", (attempts, state, row["id"])
                )
                error = ("OTP_INVALID", "Código inválido")
        assert error is not None
        raise AppError(400, error[0], error[1])
```

## `app/services/limits.py` (LIM)

```python
"""LIM: política de límites por estado (ACTIVE_BASIC y ACTIVE_FULL), leída desde CFG."""
from __future__ import annotations

from typing import Any

from ..config import Settings

_FIELDS = (
    "allowsOwnRecharge",
    "allowsThirdPartyRecharge",
    "allowsPayments",
    "rechargePerOperationCents",
    "rechargeDailyCents",
    "paymentPerOperationCents",
    "paymentDailyCents",
)


class LimitsPolicy:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def limits_for(self, status: str) -> dict[str, Any]:
        conf = self._settings.limits[status]
        return {name: conf.get(name) for name in _FIELDS}
```

## `app/services/consent.py` (CONS)

```python
"""CONS: consentimiento de términos y manejo de datos personales (CA-10)."""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Callable

from ..clock import to_iso
from ..db import Database
from ..errors import AppError
from ..repositories import AccountRepository


class ConsentService:
    def __init__(self, db: Database, accounts: AccountRepository, clock: Callable[[], datetime]) -> None:
        self._db = db
        self._accounts = accounts
        self._clock = clock

    def record(self, account_id: str, terms_version: str) -> dict[str, Any]:
        if not self._accounts.exists(account_id):
            raise AppError(404, "NOT_FOUND", "Cuenta no encontrada")
        consent_id = str(uuid.uuid4())
        now = self._clock()
        self._db.execute(
            "INSERT INTO consents (id, account_id, terms_version, accepted_at) VALUES (?, ?, ?, ?)",
            (consent_id, account_id, terms_version, to_iso(now)),
        )
        return {"consentId": consent_id, "termsVersion": terms_version, "acceptedAt": now}

    def has_consent(self, account_id: str) -> bool:
        return (
            self._db.fetchone("SELECT 1 FROM consents WHERE account_id = ? LIMIT 1", (account_id,))
            is not None
        )
```

## `app/services/profile.py` (PROF)

```python
"""PROF: estados del perfil C1 (correo), C2 (celular) y C3 (biometría)."""
from __future__ import annotations

import sqlite3
from typing import Any

from ..db import Database
from ..errors import AppError
from ..repositories import AccountRepository
from .otp import OtpService

CHANNEL_EMAIL = "EMAIL"
CHANNEL_MOBILE = "MOBILE"


class ProfileService:
    def __init__(self, db: Database, accounts: AccountRepository, otp: OtpService) -> None:
        self._db = db
        self._accounts = accounts
        self._otp = otp

    def _require_account(self, account_id: str) -> None:
        if not self._accounts.exists(account_id):
            raise AppError(404, "NOT_FOUND", "Cuenta no encontrada")

    def get_status(self, account_id: str) -> dict[str, str]:
        profile = self._accounts.get_profile(account_id)
        if profile is None:
            raise AppError(404, "NOT_FOUND", "Cuenta no encontrada")
        return profile

    # ------------------------------------------------------------ correo (C1)
    def request_email_otp(self, account_id: str, email: str) -> dict[str, Any]:
        self._require_account(account_id)
        email = email.strip().lower()
        taken = self._db.fetchone(
            "SELECT 1 FROM profiles WHERE email = ? AND account_id <> ?", (email, account_id)
        )
        if taken:
            raise AppError(409, "EMAIL_ALREADY_REGISTERED", "El correo ya está registrado")
        return self._otp.issue(account_id, CHANNEL_EMAIL, email)

    def verify_email_otp(self, account_id: str, code: str) -> dict[str, str]:
        self._require_account(account_id)
        email = self._otp.verify(account_id, CHANNEL_EMAIL, code)
        try:
            self._db.execute(
                "UPDATE profiles SET email = ?, email_status = 'ACTIVE_EMAIL' WHERE account_id = ?",
                (email, account_id),
            )
        except sqlite3.IntegrityError:
            raise AppError(409, "EMAIL_ALREADY_REGISTERED", "El correo ya está registrado")
        return self.get_status(account_id)

    # ----------------------------------------------------------- celular (C2)
    def request_mobile_otp(self, account_id: str, mobile_number: str) -> dict[str, Any]:
        self._require_account(account_id)
        mobile = f"+51{mobile_number}"  # prefijo fijo Perú
        taken = self._db.fetchone(
            "SELECT 1 FROM profiles WHERE mobile = ? AND account_id <> ?", (mobile, account_id)
        )
        if taken:
            raise AppError(409, "MOBILE_ALREADY_REGISTERED", "El celular ya está registrado")
        return self._otp.issue(account_id, CHANNEL_MOBILE, mobile)

    def verify_mobile_otp(self, account_id: str, code: str) -> dict[str, str]:
        self._require_account(account_id)
        mobile = self._otp.verify(account_id, CHANNEL_MOBILE, code)
        try:
            self._db.execute(
                "UPDATE profiles SET mobile = ?, mobile_status = 'ACTIVE_MOVIL' WHERE account_id = ?",
                (mobile, account_id),
            )
        except sqlite3.IntegrityError:
            raise AppError(409, "MOBILE_ALREADY_REGISTERED", "El celular ya está registrado")
        return self.get_status(account_id)

    # --------------------------------------------------------- biometría (C3)
    def activate_biometric(self, account_id: str) -> None:
        with self._db.transaction():
            self._db.execute(
                "UPDATE profiles SET biometric_status = 'ACTIVE_BIOM' WHERE account_id = ?",
                (account_id,),
            )
            self._db.execute(
                "UPDATE accounts SET status = 'ACTIVE_FULL' WHERE id = ?", (account_id,)
            )
```

## `app/services/biometric.py` (BIOM)

```python
"""BIOM: flujo mock biométrico (solo dev y test). No procesa fotos ni video: solo verifica inputs."""
from __future__ import annotations

from typing import Any

from ..config import STATUS_FULL, Settings
from ..errors import AppError
from ..repositories import AccountRepository
from .consent import ConsentService
from .limits import LimitsPolicy
from .profile import ProfileService


class BiometricMockService:
    def __init__(
        self,
        settings: Settings,
        accounts: AccountRepository,
        profiles: ProfileService,
        consents: ConsentService,
        limits: LimitsPolicy,
    ) -> None:
        self._settings = settings
        self._accounts = accounts
        self._profiles = profiles
        self._consents = consents
        self._limits = limits

    def ensure_available(self) -> None:
        if not self._settings.mock_flow_enabled:
            raise AppError(404, "MOCK_NOT_AVAILABLE", "Flujo no disponible en este ambiente")

    def verify(self, account_id: str, dni_number: str) -> dict[str, Any]:
        self.ensure_available()
        account = self._accounts.get(account_id)
        if account is None:
            raise AppError(404, "NOT_FOUND", "Cuenta no encontrada")
        if not self._consents.has_consent(account_id):
            raise AppError(409, "CONSENT_REQUIRED", "Debes aceptar los términos y el manejo de datos")
        if account["status"] == STATUS_FULL:
            raise AppError(409, "ALREADY_ACTIVE_FULL", "La cuenta ya está en ACTIVE_FULL")
        # dni_number ya fue validado (8 dígitos); se descarta, no se persiste ni se registra.
        self._profiles.activate_biometric(account_id)
        return {
            "accountId": account_id,
            "status": STATUS_FULL,
            "profile": self._profiles.get_status(account_id),
            "limits": self._limits.limits_for(STATUS_FULL),
        }
```

## `app/services/onboarding.py` (ONB)

```python
"""ONB: onboarding y cuenta. Orquesta UNAME, ADP (KYC y wallet), LIM y DB."""
from __future__ import annotations

import asyncio
import base64
import hashlib
import hmac
import secrets
import sqlite3
import uuid
from datetime import datetime
from typing import Any, Callable

from ..adapters.wallet_mock import WalletMockClient
from ..clock import to_iso
from ..config import STATUS_BASIC, Settings
from ..db import Database
from ..errors import AppError
from ..repositories import AccountRepository
from ..schemas import CreateAccountRequest
from .limits import LimitsPolicy
from .session_tracking import SessionTrackingService
from .username import UsernameService

_SCRYPT_N, _SCRYPT_R, _SCRYPT_P = 2**14, 8, 1


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.scrypt(
        password.encode(), salt=salt, n=_SCRYPT_N, r=_SCRYPT_R, p=_SCRYPT_P, dklen=32
    )
    return "scrypt${}${}${}${}${}".format(
        _SCRYPT_N, _SCRYPT_R, _SCRYPT_P,
        base64.b64encode(salt).decode(), base64.b64encode(digest).decode(),
    )


def verify_password(password: str, stored: str) -> bool:
    _, n, r, p, salt, digest = stored.split("$")
    candidate = hashlib.scrypt(
        password.encode(), salt=base64.b64decode(salt), n=int(n), r=int(r), p=int(p), dklen=32
    )
    return hmac.compare_digest(candidate, base64.b64decode(digest))


class OnboardingService:
    def __init__(
        self,
        *,
        db: Database,
        accounts: AccountRepository,
        usernames: UsernameService,
        sessions: SessionTrackingService,
        wallet: WalletMockClient,
        limits: LimitsPolicy,
        settings: Settings,
        clock: Callable[[], datetime],
    ) -> None:
        self._db = db
        self._accounts = accounts
        self._usernames = usernames
        self._sessions = sessions
        self._wallet = wallet
        self._limits = limits
        self._settings = settings
        self._clock = clock

    # ------------------------------------------------------- CA-02 y CA-03
    async def create_account(self, req: CreateAccountRequest) -> dict[str, Any]:
        # 1) Campos ya validados por el esquema; hash de contraseña (CPU-bound, fuera del event loop).
        password_hash = await asyncio.to_thread(hash_password, req.password)

        # 2) Usuario libre?
        if not self._usernames.is_available(req.username):
            raise self._username_taken(req)

        # 3) KYC externo: crea el wallet (la contraseña no se envía).
        wallet_id = await self._wallet.create_kyc_wallet(
            first_names=req.firstNames,
            paternal_surname=req.paternalSurname,
            maternal_surname=req.maternalSurname,
        )

        # 4) Persistencia: cuenta ACTIVE_BASIC y C1, C2, C3 pendientes.
        user_id, account_id = str(uuid.uuid4()), str(uuid.uuid4())
        now = to_iso(self._clock())
        try:
            with self._db.transaction():
                self._db.execute(
                    """INSERT INTO users (id, first_names, paternal_surname, maternal_surname,
                                          username, username_key, password_hash, created_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        user_id, req.firstNames, req.paternalSurname, req.maternalSurname,
                        req.username, self._usernames.key(req.username), password_hash, now,
                    ),
                )
                self._db.execute(
                    "INSERT INTO accounts (id, user_id, wallet_id, status, created_at) VALUES (?, ?, ?, ?, ?)",
                    (account_id, user_id, wallet_id, STATUS_BASIC, now),
                )
                self._db.execute("INSERT INTO profiles (account_id) VALUES (?)", (account_id,))
        except sqlite3.IntegrityError as exc:
            # Carrera: otro request tomó el usuario entre la verificación y el INSERT.
            if "username_key" in str(exc):
                raise self._username_taken(req)
            raise

        if req.onboardingSessionId:
            self._sessions.try_register_step(str(req.onboardingSessionId), "ACCOUNT_CREATED")

        return {
            "accountId": account_id,
            "walletId": wallet_id,
            "status": STATUS_BASIC,
            "balanceCents": 0,
            "currency": "PEN",
            "firstNames": req.firstNames,
            "profile": self._accounts.get_profile(account_id),
        }

    def _username_taken(self, req: CreateAccountRequest) -> AppError:
        return AppError(
            409,
            "USERNAME_TAKEN",
            "El usuario no está disponible",
            extra={
                "suggestions": self._usernames.suggestions(
                    req.username, req.firstNames, req.paternalSurname, req.maternalSurname
                )
            },
        )

    # ------------------------------------------------ CA-03, CA-04, CA-05 (landing)
    async def get_summary(self, account_id: str) -> dict[str, Any]:
        account = self._accounts.get(account_id)
        if account is None:
            raise AppError(404, "NOT_FOUND", "Cuenta no encontrada")
        profile = self._accounts.get_profile(account_id) or {}

        # Día calendario según la hora del servidor en America/Lima.
        today = self._clock().astimezone(self._settings.tz).date()
        recharged, paid = self._accounts.get_daily_usage(account_id, today.isoformat())

        balance = await self._wallet.get_wallet_balance_cents(account["wallet_id"])

        pending = [
            label
            for label, value in (
                ("correo", profile.get("emailStatus") != "ACTIVE_EMAIL"),
                ("celular", profile.get("mobileStatus") != "ACTIVE_MOVIL"),
                ("identidad", profile.get("biometricStatus") != "ACTIVE_BIOM"),
            )
            if value
        ]
        message = (
            "Completa tu perfil (" + ", ".join(pending) + ") para ampliar tus límites de operación."
            if pending
            else None
        )
        return {
            "accountId": account["id"],
            "walletId": account["wallet_id"],
            "firstNames": account["first_names"],
            "status": account["status"],
            "balanceCents": balance,
            "currency": "PEN",
            "limits": self._limits.limits_for(account["status"]),
            "dailyUsage": {
                "date": today,
                "timezone": "America/Lima",
                "rechargedCents": recharged,
                "paidCents": paid,
            },
            "profile": profile,
            "profilePending": bool(pending),
            "profilePendingMessage": message,
        }
```

## `app/container.py`

```python
"""Composición de servicios (raíz de dependencias)."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable

from fastapi import Request

from .adapters.wallet_mock import WalletMockClient
from .clock import utcnow
from .config import Settings
from .db import Database
from .repositories import AccountRepository
from .services.biometric import BiometricMockService
from .services.consent import ConsentService
from .services.limits import LimitsPolicy
from .services.onboarding import OnboardingService
from .services.otp import OtpService
from .services.otp_mock import OtpMockGenerator
from .services.profile import ProfileService
from .services.session_tracking import SessionTrackingService
from .services.username import UsernameService


@dataclass
class Container:
    settings: Settings
    db: Database
    wallet: Any
    usernames: UsernameService
    sessions: SessionTrackingService
    limits: LimitsPolicy
    otp: OtpService
    profiles: ProfileService
    consents: ConsentService
    biometric: BiometricMockService
    onboarding: OnboardingService


def build_container(
    settings: Settings,
    wallet: Any | None = None,
    clock: Callable[[], datetime] = utcnow,
) -> Container:
    db = Database(settings.db_path)
    db.init_schema()
    accounts = AccountRepository(db)
    wallet = wallet or WalletMockClient(settings)
    usernames = UsernameService(db)
    sessions = SessionTrackingService(db, clock)
    limits = LimitsPolicy(settings)
    otp = OtpService(db, OtpMockGenerator(settings), settings, clock)
    profiles = ProfileService(db, accounts, otp)
    consents = ConsentService(db, accounts, clock)
    biometric = BiometricMockService(settings, accounts, profiles, consents, limits)
    onboarding = OnboardingService(
        db=db, accounts=accounts, usernames=usernames, sessions=sessions,
        wallet=wallet, limits=limits, settings=settings, clock=clock,
    )
    return Container(
        settings, db, wallet, usernames, sessions, limits, otp, profiles, consents, biometric, onboarding
    )


def get_container(request: Request) -> Container:
    return request.app.state.container
```

---

## `app/routers/onboarding.py`

```python
from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from ..container import Container, get_container
from ..schemas import (
    ErrorResponse,
    FirstNames,
    OnboardingSession,
    OnboardingStepRequest,
    Surname,
    Username,
    UsernameAvailability,
)

router = APIRouter()
ERR = {"model": ErrorResponse}


@router.post(
    "/onboarding/sessions",
    status_code=201,
    response_model=OnboardingSession,
    tags=["Onboarding"],
    operation_id="startOnboardingSession",
    summary="Inicia la medición del onboarding (CA-01)",
    responses={500: ERR},
)
async def start_session(c: Container = Depends(get_container)):
    return c.sessions.start()


@router.post(
    "/onboarding/sessions/{sessionId}/steps",
    response_model=OnboardingSession,
    tags=["Onboarding"],
    operation_id="registerOnboardingStep",
    summary="Registra un paso completado (CA-01, CA-03)",
    responses={400: ERR, 404: ERR, 409: ERR},
)
async def register_step(
    sessionId: UUID, body: OnboardingStepRequest, c: Container = Depends(get_container)
):
    return c.sessions.register_step(str(sessionId), body.step)


@router.get(
    "/usernames/availability",
    response_model=UsernameAvailability,
    response_model_exclude_none=True,
    tags=["Cuenta"],
    operation_id="checkUsernameAvailability",
    summary="Valida la disponibilidad del usuario (CA-02)",
    responses={400: ERR},
)
async def check_username(
    username: Annotated[Username, Query()],
    first_names: Annotated[FirstNames | None, Query(alias="firstNames")] = None,
    paternal_surname: Annotated[Surname | None, Query(alias="paternalSurname")] = None,
    maternal_surname: Annotated[Surname | None, Query(alias="maternalSurname")] = None,
    c: Container = Depends(get_container),
):
    if c.usernames.is_available(username):
        return {"username": username, "available": True}
    return {
        "username": username,
        "available": False,
        "suggestions": c.usernames.suggestions(
            username, first_names, paternal_surname, maternal_surname
        ),
    }
```

## `app/routers/accounts.py`

```python
from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends

from ..container import Container, get_container
from ..schemas import AccountCreated, AccountSummary, CreateAccountRequest, ErrorResponse, UsernameTakenError
from ..security import require_bearer

router = APIRouter(tags=["Cuenta"])
ERR = {"model": ErrorResponse}


@router.post(
    "/accounts",
    status_code=201,
    response_model=AccountCreated,
    operation_id="createAccount",
    summary="Crea la cuenta básica (CA-02, CA-03)",
    responses={
        400: ERR,
        409: {"model": UsernameTakenError, "description": "USERNAME_TAKEN con sugerencias"},
        502: ERR,
        504: ERR,
        500: ERR,
    },
)
async def create_account(body: CreateAccountRequest, c: Container = Depends(get_container)):
    return await c.onboarding.create_account(body)


@router.get(
    "/accounts/{accountId}",
    response_model=AccountSummary,
    operation_id="getAccount",
    summary="Landing y estado de la cuenta (CA-03, CA-04, CA-05, CA-06, CA-13)",
    dependencies=[Depends(require_bearer)],
    responses={401: ERR, 404: ERR, 502: ERR, 504: ERR},
)
async def get_account(accountId: UUID, c: Container = Depends(get_container)):
    return await c.onboarding.get_summary(str(accountId))
```

## `app/routers/profile.py`

```python
from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends

from ..container import Container, get_container
from ..schemas import (
    Consent,
    ConsentRequest,
    EmailOtpRequest,
    ErrorResponse,
    MobileOtpRequest,
    OtpIssued,
    OtpVerificationRequest,
    ProfileStatus,
)
from ..security import require_bearer

router = APIRouter(tags=["Perfil"], dependencies=[Depends(require_bearer)])
ERR = {"model": ErrorResponse}


@router.post(
    "/accounts/{accountId}/email/otp",
    status_code=202,
    response_model=OtpIssued,
    operation_id="requestEmailOtp",
    summary="Solicita OTP de correo (CA-06, CA-07)",
    responses={400: ERR, 401: ERR, 404: ERR, 409: ERR, 429: ERR},
)
async def request_email_otp(accountId: UUID, body: EmailOtpRequest, c: Container = Depends(get_container)):
    return c.profiles.request_email_otp(str(accountId), body.email)


@router.post(
    "/accounts/{accountId}/email/otp/verification",
    response_model=ProfileStatus,
    operation_id="verifyEmailOtp",
    summary="Valida el OTP de correo (CA-07)",
    responses={400: ERR, 401: ERR, 404: ERR},
)
async def verify_email_otp(accountId: UUID, body: OtpVerificationRequest, c: Container = Depends(get_container)):
    return c.profiles.verify_email_otp(str(accountId), body.code)


@router.post(
    "/accounts/{accountId}/mobile/otp",
    status_code=202,
    response_model=OtpIssued,
    operation_id="requestMobileOtp",
    summary="Solicita OTP de celular (CA-06, CA-08)",
    responses={400: ERR, 401: ERR, 404: ERR, 409: ERR, 429: ERR},
)
async def request_mobile_otp(accountId: UUID, body: MobileOtpRequest, c: Container = Depends(get_container)):
    return c.profiles.request_mobile_otp(str(accountId), body.mobileNumber)


@router.post(
    "/accounts/{accountId}/mobile/otp/verification",
    response_model=ProfileStatus,
    operation_id="verifyMobileOtp",
    summary="Valida el OTP de celular (CA-08)",
    responses={400: ERR, 401: ERR, 404: ERR},
)
async def verify_mobile_otp(accountId: UUID, body: OtpVerificationRequest, c: Container = Depends(get_container)):
    return c.profiles.verify_mobile_otp(str(accountId), body.code)


@router.post(
    "/accounts/{accountId}/consents",
    status_code=201,
    response_model=Consent,
    operation_id="acceptDataConsent",
    summary="Acepta términos y manejo de datos personales (CA-10)",
    responses={400: ERR, 401: ERR, 404: ERR},
)
async def accept_consent(accountId: UUID, body: ConsentRequest, c: Container = Depends(get_container)):
    return c.consents.record(str(accountId), body.termsVersion)
```

## `app/routers/biometric.py`

```python
from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends

from ..container import Container, get_container
from ..schemas import ErrorResponse, MockBiometricRequest, MockBiometricResult
from ..security import require_bearer

router = APIRouter(tags=["Biometría mock"])
ERR = {"model": ErrorResponse}


def require_mock_enabled(c: Container = Depends(get_container)) -> None:
    # Se evalúa antes que la validación del body: en producción siempre 404 MOCK_NOT_AVAILABLE.
    c.biometric.ensure_available()


@router.post(
    "/accounts/{accountId}/biometric/mock-verification",
    response_model=MockBiometricResult,
    operation_id="mockBiometricVerification",
    summary="Simula la validación biométrica exitosa (CA-09, CA-12)",
    dependencies=[Depends(require_bearer), Depends(require_mock_enabled)],
    responses={400: ERR, 401: ERR, 404: ERR, 409: ERR},
)
async def mock_verification(accountId: UUID, body: MockBiometricRequest, c: Container = Depends(get_container)):
    return c.biometric.verify(str(accountId), body.dniNumber)
```

## `app/main.py`

```python
"""REST: capa /v1, middleware de trazabilidad y manejo de errores."""
from __future__ import annotations

import logging
import time
import uuid
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any, Callable

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from .clock import utcnow
from .config import Settings
from .container import build_container
from .errors import (
    AppError,
    app_error_handler,
    http_error_handler,
    unhandled_error_handler,
    validation_error_handler,
)
from .routers import accounts, biometric, onboarding, profile

logger = logging.getLogger("wallet.http")


def create_app(
    settings: Settings | None = None,
    wallet: Any | None = None,
    clock: Callable[[], datetime] = utcnow,
) -> FastAPI:
    settings = settings or Settings.from_env()
    container = build_container(settings, wallet=wallet, clock=clock)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        yield
        await container.wallet.aclose()
        container.db.close()

    app = FastAPI(
        title="Wallet Local API - Onboarding de usuario",
        version="0.1.0",
        description="HU 01 - Onboarding de usuario billetera digital. Importes en céntimos de PEN.",
        lifespan=lifespan,
    )
    app.state.container = container

    app.add_exception_handler(AppError, app_error_handler)
    app.add_exception_handler(RequestValidationError, validation_error_handler)
    app.add_exception_handler(StarletteHTTPException, http_error_handler)
    app.add_exception_handler(Exception, unhandled_error_handler)

    @app.middleware("http")
    async def trace_and_log(request: Request, call_next):
        request.state.trace_id = uuid.uuid4().hex
        started = time.perf_counter()
        response = await call_next(request)
        response.headers["X-Trace-Id"] = request.state.trace_id
        # Solo método, ruta (sin query), estado y latencia: nunca cuerpos ni cabeceras.
        logger.info(
            "%s %s -> %s (%.1f ms)",
            request.method, request.url.path, response.status_code,
            (time.perf_counter() - started) * 1000,
        )
        return response

    for router in (onboarding.router, accounts.router, profile.router, biometric.router):
        app.include_router(router, prefix="/v1")

    return app


logging.basicConfig(level=logging.INFO)
app = create_app() if __name__ != "__main__" and False else None  # placeholder, ver abajo


def get_app() -> FastAPI:  # uvicorn --factory app.main:get_app
    return create_app()
```

Las dos últimas líneas de `main.py` son confusas. Reemplázalas por este cierre, que es el correcto:

```python
logging.basicConfig(level=logging.INFO)


def get_app() -> FastAPI:
    """Fábrica para uvicorn: `uvicorn app.main:get_app --factory --port 8080`."""
    return create_app()
```

---

## `tests/test_onboarding_flow.py`

```python
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.errors import AppError
from app.main import create_app

AUTH = {"Authorization": "Bearer test-token"}
ACCOUNT_BODY = {
    "firstNames": "Ana María",
    "paternalSurname": "Quispe",
    "maternalSurname": "Rojas",
    "username": "ana.quispe",
    "password": "S3cret!pass",
}


class FakeClock:
    def __init__(self):
        self.now = datetime(2026, 10, 30, 19, 0, tzinfo=timezone.utc)

    def __call__(self):
        return self.now

    def advance(self, seconds):
        self.now += timedelta(seconds=seconds)


class FakeWallet:
    def __init__(self):
        self.fail_create = None
        self.fail_get = None
        self.balances = {}

    async def create_kyc_wallet(self, **kwargs):
        if self.fail_create:
            raise self.fail_create
        wallet_id = f"w-{uuid4().hex[:8]}"
        self.balances[wallet_id] = 0
        return wallet_id

    async def get_wallet_balance_cents(self, wallet_id):
        if self.fail_get:
            raise self.fail_get
        return self.balances[wallet_id]

    async def aclose(self):
        pass


def make_client(env="test"):
    clock, wallet = FakeClock(), FakeWallet()
    settings = Settings(environment=env, db_path=":memory:", otp_fixed_code="123456")
    return TestClient(create_app(settings, wallet=wallet, clock=clock)), clock, wallet


@pytest.fixture
def ctx():
    client, clock, wallet = make_client()
    with client:
        yield client, clock, wallet


def create_account(client, **overrides):
    resp = client.post("/v1/accounts", json={**ACCOUNT_BODY, **overrides})
    assert resp.status_code == 201, resp.text
    return resp.json()


def test_session_lifecycle_and_landing(ctx):
    client, clock, _ = ctx
    session = client.post("/v1/onboarding/sessions").json()
    sid = session["sessionId"]
    r = client.post(f"/v1/onboarding/sessions/{sid}/steps", json={"step": "PERSONAL_DATA_COMPLETED"})
    assert r.status_code == 200 and r.json()["completedSteps"] == ["PERSONAL_DATA_COMPLETED"]

    account = create_account(client, onboardingSessionId=sid)
    assert account["status"] == "ACTIVE_BASIC" and account["balanceCents"] == 0
    assert account["profile"] == {
        "emailStatus": "PENDING_EMAIL", "mobileStatus": "PENDING_MOVIL", "biometricStatus": "PENDING_BIOM",
    }

    assert client.get(f"/v1/accounts/{account['accountId']}").status_code == 401
    summary = client.get(f"/v1/accounts/{account['accountId']}", headers=AUTH).json()
    assert summary["firstNames"] == "Ana María" and summary["profilePending"] is True
    assert summary["dailyUsage"]["date"] == "2026-10-30"
    assert summary["limits"]["allowsThirdPartyRecharge"] is False

    clock.advance(12)
    closed = client.post(f"/v1/onboarding/sessions/{sid}/steps", json={"step": "LANDING_VISIBLE"}).json()
    assert closed["completed"] is True and closed["durationMs"] == 12000
    assert "ACCOUNT_CREATED" in closed["completedSteps"]
    again = client.post(f"/v1/onboarding/sessions/{sid}/steps", json={"step": "LANDING_VISIBLE"})
    assert again.status_code == 409


def test_username_availability_and_conflict(ctx):
    client, _, _ = ctx
    create_account(client)
    r = client.get("/v1/usernames/availability", params={
        "username": "ANA.quispe", "firstNames": "Ana", "paternalSurname": "Quispe"})
    body = r.json()
    assert body["available"] is False and body["suggestions"]
    assert all(s.isalnum() and len(s) <= 20 for s in body["suggestions"])

    dup = client.post("/v1/accounts", json=ACCOUNT_BODY)
    assert dup.status_code == 409 and dup.json()["code"] == "USERNAME_TAKEN"
    assert dup.json()["suggestions"]

    bad = client.post("/v1/accounts", json={**ACCOUNT_BODY, "password": "short"})
    assert bad.status_code == 400 and bad.json()["code"] == "INVALID_FIELD"
    assert "short" not in bad.text


def test_external_failures_are_mapped(ctx):
    client, _, wallet = ctx
    wallet.fail_create = AppError(504, "EXTERNAL_TIMEOUT", "timeout")
    r = client.post("/v1/accounts", json=ACCOUNT_BODY)
    assert r.status_code == 504 and r.json()["code"] == "EXTERNAL_TIMEOUT"
    wallet.fail_create = None
    account = create_account(client)
    wallet.fail_get = AppError(502, "WALLET_NOT_FOUND_EXTERNAL", "nf")
    r = client.get(f"/v1/accounts/{account['accountId']}", headers=AUTH)
    assert r.status_code == 502 and r.json()["code"] == "WALLET_NOT_FOUND_EXTERNAL"


def test_email_otp_rules(ctx):
    client, clock, _ = ctx
    acc = create_account(client)["accountId"]
    url = f"/v1/accounts/{acc}/email/otp"
    first = client.post(url, json={"email": "ana@example.com"}, headers=AUTH)
    assert first.status_code == 202 and first.json()["expiresInSeconds"] == 60

    too_soon = client.post(url, json={"email": "ana@example.com"}, headers=AUTH)
    assert too_soon.status_code == 429 and too_soon.headers["retry-after"] == "45"
    assert too_soon.json()["code"] == "OTP_TOO_SOON"

    clock.advance(61)
    expired = client.post(f"{url}/verification", json={"code": "123456"}, headers=AUTH)
    assert expired.status_code == 400 and expired.json()["code"] == "OTP_EXPIRED"

    assert client.post(url, json={"email": "ana@example.com"}, headers=AUTH).status_code == 202
    wrong = client.post(f"{url}/verification", json={"code": "000000"}, headers=AUTH)
    assert wrong.status_code == 400 and wrong.json()["code"] == "OTP_INVALID"
    ok = client.post(f"{url}/verification", json={"code": "123456"}, headers=AUTH)
    assert ok.status_code == 200 and ok.json()["emailStatus"] == "ACTIVE_EMAIL"

    other = create_account(client, username="luis.perez")["accountId"]
    conflict = client.post(f"/v1/accounts/{other}/email/otp", json={"email": "ana@example.com"}, headers=AUTH)
    assert conflict.status_code == 409 and conflict.json()["code"] == "EMAIL_ALREADY_REGISTERED"


def test_mobile_otp_and_biometric_flow(ctx):
    client, _, _ = ctx
    acc = create_account(client)["accountId"]
    m = client.post(f"/v1/accounts/{acc}/mobile/otp", json={"mobileNumber": "987654321"}, headers=AUTH)
    assert m.status_code == 202
    v = client.post(f"/v1/accounts/{acc}/mobile/otp/verification", json={"code": "123456"}, headers=AUTH)
    assert v.json()["mobileStatus"] == "ACTIVE_MOVIL"

    bio = f"/v1/accounts/{acc}/biometric/mock-verification"
    no_consent = client.post(bio, json={"dniNumber": "12345678"}, headers=AUTH)
    assert no_consent.status_code == 409 and no_consent.json()["code"] == "CONSENT_REQUIRED"

    consent = client.post(f"/v1/accounts/{acc}/consents",
                          json={"accepted": True, "termsVersion": "2026-10"}, headers=AUTH)
    assert consent.status_code == 201

    done = client.post(bio, json={"dniNumber": "12345678"}, headers=AUTH)
    assert done.status_code == 200 and done.json()["status"] == "ACTIVE_FULL"
    assert done.json()["profile"]["biometricStatus"] == "ACTIVE_BIOM"
    assert done.json()["limits"]["allowsThirdPartyRecharge"] is True


def test_biometric_not_available_in_production():
    client, _, _ = make_client(env="production")
    with client:
        r = client.post(f"/v1/accounts/{uuid4()}/biometric/mock-verification",
                        json={"dniNumber": "12345678"}, headers=AUTH)
        assert r.status_code == 404 and r.json()["code"] == "MOCK_NOT_AVAILABLE"
```

---

## `README.md`

````markdown
# Wallet API – HU 01 Onboarding (FastAPI)

## Ejecutar
```bash
pip install -r requirements.txt
WALLET_ENV=development uvicorn app.main:get_app --factory --port 8080
pytest -q
```
Los endpoints quedan bajo `http://localhost:8080/v1` y la documentación en `/docs`.

## Variables de entorno
| Variable | Default | Descripción |
|---|---|---|
| WALLET_ENV | development | `development`, `dev` y `test` habilitan la biometría mock; cualquier otro valor responde 404 MOCK_NOT_AVAILABLE |
| WALLET_DB_PATH | wallet.db | Archivo SQLite (`:memory:` para pruebas) |
| WALLET_BASE_URL | https://bcp-wallet-mock.yefri.workers.dev | Base del servicio externo (se añade `/groups/8`) |
| WALLET_CONNECT_TIMEOUT_S / WALLET_READ_TIMEOUT_S | 2 / 5 | Timeouts del adaptador (agotarlos produce 504 EXTERNAL_TIMEOUT) |
| WALLET_GET_RETRIES | 1 | Reintentos solo para GET de wallet |
| WALLET_OTP_FIXED_CODE | – | Código fijo para dev y test (ignorado en producción) |
| WALLET_OTP_PEPPER | change-me-in-prod | Pepper del hash de OTP |
| WALLET_AUTH_ENABLED | true | Exige `Authorization: Bearer` en endpoints con `bearerAuth` |
| WALLET_LIMITS_JSON | – | Sobrescribe topes por estado, p. ej. `{"ACTIVE_BASIC":{"rechargeDailyCents":50000}}` |

## Supuestos y puntos a confirmar
1. **Contrato externo truncado**: los nombres de los campos del KYC (cuerpo) y del saldo del wallet están aislados en `app/adapters/wallet_mock.py`. Se asume `wallet_id` en la respuesta Kyc y se buscan varios nombres para el saldo (`_BALANCE_KEYS`).
2. **Topes de ACTIVE_BASIC y ACTIVE_FULL**: la HU no da cifras; los valores por defecto están en `config.py` y son parametrizables.
3. **bearerAuth**: solo se valida la presencia y el formato de la cabecera (el mecanismo está fuera del alcance de la HU).
4. **Códigos de error no listados en el contrato**: `SESSION_CLOSED` (409 en steps), `ALREADY_ACTIVE_FULL` (409 en biometría), `NOT_FOUND` y `UNAUTHORIZED`.
5. **Orden de validación**: un identificador malformado en la ruta responde 404. Una validación fallida de campos responde 400 `INVALID_FIELD`, con nombre de campo y regla, nunca valores.
6. **Privacidad**: la contraseña se guarda con scrypt, nunca se registra ni se envía al KYC, y no hay logs de cuerpos. El OTP mock se escribe en el log solo fuera de producción. `X-Mock-Latency-Ms` nunca se propaga al cliente.
7. **Consistencia con el KYC**: si el INSERT falla por carrera de usuario tras un KYC 201, el wallet externo queda huérfano. El mock no tiene endpoint de baja; el índice único sobre `username_key` evita duplicados locales.
````