"""Servicios de dominio de la HU 02."""

from __future__ import annotations

import logging
import math
import unicodedata
import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional

from app import validators as v
from app.clock import PeruClock
from app.config import Settings
from app.db import Database
from app.errors import ApiError
from app.otp import (
    OTP_INTERVAL_SECONDS,
    OTP_LENGTH,
    OTP_TTL_SECONDS,
    OtpProvider,
    hash_code,
)
from app.security import dummy_verify, hash_password, verify_password

log = logging.getLogger("wallet")

GROUP_TYPES = {
    "COMBINED": ["TOPUP_OWN", "PAYMENT"],
    "TOPUP": ["TOPUP_OWN", "TOPUP_THIRD_PARTY"],
    "PAYMENT": ["PAYMENT"],
}


def cents_to_money(cents: int) -> str:
    return f"{cents // 100}.{cents % 100:02d}"


def money_to_cents(value: str) -> int:
    return int(Decimal(value) * 100)


def _ts(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat(timespec="microseconds")


def _parse(value: str) -> datetime:
    return datetime.fromisoformat(value)


def _account_dict(row: Any) -> Dict[str, Any]:
    return {
        "wallet_id": row["wallet_id"],
        "status": row["status"],
        "balance": cents_to_money(row["balance_cents"]),
        "currency": row["currency"],
    }


def _profile_dict(row: Any) -> Dict[str, str]:
    return {
        "estado_c1": row["estado_c1"],
        "estado_c2": row["estado_c2"],
        "estado_c3": row["estado_c3"],
    }


def operation_conditions(conn: Any, status: str) -> Dict[str, Any]:
    rows = conn.execute(
        "SELECT operation_group, per_operation_max_cents, daily_max_cents "
        "FROM limit_parameters WHERE account_status=? ORDER BY operation_group",
        (status,),
    ).fetchall()
    rules = []
    for r in rows:
        per = r["per_operation_max_cents"]
        rules.append(
            {
                "operation_group": r["operation_group"],
                "operation_types": GROUP_TYPES[r["operation_group"]],
                "per_operation_max": None if per is None else cents_to_money(per),
                "daily_max": cents_to_money(r["daily_max_cents"]),
            }
        )
    return {"account_status": status, "timezone": "America/Lima", "rules": rules}


def _slug(text: str) -> str:
    nfkd = unicodedata.normalize("NFKD", text)
    return "".join(ch for ch in nfkd.lower() if ch.isascii() and ch.isalnum())


class _Base:
    def __init__(self, db: Database, clock: PeruClock, settings: Settings) -> None:
        self.db = db
        self.clock = clock
        self.settings = settings


class AccountService(_Base):
    def authenticate(self, username: str, password: str) -> Optional[str]:
        with self.db.transaction() as c:
            row = c.execute(
                "SELECT wallet_id, password_hash, password_salt FROM wallet_accounts "
                "WHERE username_normalized=?",
                (username.lower(),),
            ).fetchone()
        if row is None:
            dummy_verify(password, self.settings.pbkdf2_iterations)
            return None
        if verify_password(password, row["password_hash"], row["password_salt"]):
            return row["wallet_id"]
        return None

    def wallet_exists(self, wallet_id: str) -> bool:
        with self.db.transaction() as c:
            return (
                c.execute("SELECT 1 FROM wallet_accounts WHERE wallet_id=?", (wallet_id,)).fetchone()
                is not None
            )

    def get_wallet(self, wallet_id: str) -> Dict[str, Any]:
        with self.db.transaction() as c:
            acc = c.execute("SELECT * FROM wallet_accounts WHERE wallet_id=?", (wallet_id,)).fetchone()
            if acc is None:
                raise ApiError(404, "NOT_FOUND", "Wallet no encontrada")
            prof = c.execute("SELECT * FROM wallet_profiles WHERE wallet_id=?", (wallet_id,)).fetchone()
            return {
                "account": _account_dict(acc),
                "profile": _profile_dict(prof),
                "operation_conditions": operation_conditions(c, acc["status"]),
                "identity_mock_available": self.settings.identity_mock_available,
            }


class OnboardingService(_Base):
    def start_session(self) -> Dict[str, str]:
        session_id = str(uuid.uuid4())
        now = self.clock.now()
        with self.db.transaction() as c:
            c.execute(
                "INSERT INTO onboarding_sessions (id, started_at) VALUES (?, ?)",
                (session_id, _ts(now)),
            )
        return {"session_id": session_id, "started_at": _ts(now)}

    def record_step(self, session_id: str, step: str) -> Dict[str, Any]:
        now = self.clock.now()
        with self.db.transaction() as c:
            s = c.execute("SELECT * FROM onboarding_sessions WHERE id=?", (session_id,)).fetchone()
            if s is None:
                raise ApiError(404, "NOT_FOUND", "Sesión no encontrada")
            if s["completed_at"] is not None:
                raise ApiError(409, "SESSION_CLOSED", "La sesión ya finalizó")
            elapsed = max(0, int((now - _parse(s["started_at"])).total_seconds() * 1000))
            c.execute(
                "INSERT INTO onboarding_steps (session_id, step, elapsed_ms, completed_at) "
                "VALUES (?, ?, ?, ?)",
                (session_id, step, elapsed, _ts(now)),
            )
        return {"step": step, "elapsed_ms": elapsed}

    def _suggestions(
        self,
        conn: Any,
        username: str,
        nombres: Optional[str],
        paterno: Optional[str],
        materno: Optional[str],
        limit: int = 3,
    ) -> List[str]:
        parts = (nombres or "").split()
        fragments = [
            f
            for f in (_slug(parts[0] if parts else ""), _slug(paterno or ""), _slug(materno or ""))
            if f
        ]
        if not fragments:
            fragments = [_slug(username) or "usuario"]
        bases: List[str] = []

        def add(base: str) -> None:
            base = base[:17]
            if base and base not in bases:
                bases.append(base)

        for f in fragments:
            add(f)
        for i, f1 in enumerate(fragments):
            for j, f2 in enumerate(fragments):
                if i != j:
                    add(f1 + f2)
                    add(f1[0] + f2)
        result: List[str] = []
        for n in range(1, 1000):
            suffix = str(n)
            for base in bases:
                cand = base[: 20 - len(suffix)] + suffix
                if cand in result:
                    continue
                taken = conn.execute(
                    "SELECT 1 FROM wallet_accounts WHERE username_normalized=?", (cand,)
                ).fetchone()
                if taken is None:
                    result.append(cand)
                    if len(result) >= limit:
                        return result
        return result

    def check_username(
        self,
        username: str,
        nombres: Optional[str],
        paterno: Optional[str],
        materno: Optional[str],
    ) -> Dict[str, Any]:
        if not v.is_valid_usuario(username):
            return {"status": "INVALID_FORMAT", "suggestions": []}
        with self.db.transaction() as c:
            taken = c.execute(
                "SELECT 1 FROM wallet_accounts WHERE username_normalized=?", (username.lower(),)
            ).fetchone()
            if taken is not None:
                return {
                    "status": "TAKEN",
                    "suggestions": self._suggestions(c, username, nombres, paterno, materno),
                }
        return {"status": "AVAILABLE", "suggestions": []}

    def register(self, req: Any) -> Dict[str, Any]:
        norm = req.usuario.lower()
        pwd_hash, salt = hash_password(req.password, self.settings.pbkdf2_iterations)
        wallet_id = str(uuid.uuid4())
        session_id = str(req.session_id) if req.session_id else None
        with self.db.transaction() as c:
            session = None
            if session_id:
                session = c.execute(
                    "SELECT * FROM onboarding_sessions WHERE id=?", (session_id,)
                ).fetchone()
                if session is None:
                    raise ApiError(404, "NOT_FOUND", "Sesión no encontrada")
                if session["completed_at"] is not None:
                    raise ApiError(409, "SESSION_CLOSED", "La sesión ya finalizó")
            if c.execute(
                "SELECT 1 FROM wallet_accounts WHERE username_normalized=?", (norm,)
            ).fetchone():
                raise ApiError(
                    409,
                    "USERNAME_TAKEN",
                    "El usuario ya está registrado",
                    suggestions=self._suggestions(
                        c, req.usuario, req.nombres, req.apellido_paterno, req.apellido_materno
                    ),
                )
            now = self.clock.now()
            c.execute(
                "INSERT INTO wallet_accounts (wallet_id, username, username_normalized, "
                "password_hash, password_salt, nombres, apellido_paterno, apellido_materno, "
                "status, balance_cents, currency, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'ACTIVE_BASIC', 0, 'PEN', ?)",
                (
                    wallet_id,
                    req.usuario,
                    norm,
                    pwd_hash,
                    salt,
                    req.nombres,
                    req.apellido_paterno,
                    req.apellido_materno,
                    _ts(now),
                ),
            )
            c.execute("INSERT INTO wallet_profiles (wallet_id) VALUES (?)", (wallet_id,))
            duration = None
            if session is not None:
                duration = max(
                    0, int((now - _parse(session["started_at"])).total_seconds() * 1000)
                )
                c.execute(
                    "UPDATE onboarding_sessions SET completed_at=?, total_duration_ms=?, "
                    "wallet_id=? WHERE id=?",
                    (_ts(now), duration, wallet_id, session_id),
                )
            conditions = operation_conditions(c, "ACTIVE_BASIC")
        log.info("registration_completed")
        return {
            "account": {
                "wallet_id": wallet_id,
                "status": "ACTIVE_BASIC",
                "balance": cents_to_money(0),
                "currency": "PEN",
            },
            "welcome": {"display_name": req.nombres},
            "profile": {
                "estado_c1": "PENDING_EMAIL",
                "estado_c2": "PENDING_MOVIL",
                "estado_c3": "PENDING_BIOM",
            },
            "operation_conditions": conditions,
            "registration_duration_ms": duration,
        }


_CHANNELS = {
    "EMAIL": {
        "state": "estado_c1",
        "active": "ACTIVE_EMAIL",
        "norm": "email_normalized",
        "verified": "verified_email",
        "verified_col": "email_verified_at",
        "dup_code": "EMAIL_ALREADY_REGISTERED",
        "dup_msg": "El correo ya está registrado por otro usuario",
    },
    "PHONE": {
        "state": "estado_c2",
        "active": "ACTIVE_MOVIL",
        "norm": "phone_e164",
        "verified": "verified_phone",
        "verified_col": "phone_verified_at",
        "dup_code": "PHONE_ALREADY_REGISTERED",
        "dup_msg": "El celular ya está registrado por otro usuario",
    },
}


class OtpService(_Base):
    def __init__(
        self, db: Database, clock: PeruClock, settings: Settings, provider: OtpProvider
    ) -> None:
        super().__init__(db, clock, settings)
        self.provider = provider

    def request_otp(self, wallet_id: str, channel: str, destination: str) -> Dict[str, Any]:
        cfg = _CHANNELS[channel]
        if channel == "EMAIL":
            value = destination.strip()
            if not v.is_valid_email(value):
                raise ApiError(
                    422,
                    "INVALID_EMAIL_FORMAT",
                    "Formato de correo inválido",
                    details=[{"field": "email", "rule": "format"}],
                )
            norm = value.lower()
        else:
            if not v.is_valid_phone(destination):
                raise ApiError(
                    422,
                    "INVALID_PHONE_FORMAT",
                    "El celular debe tener 9 dígitos y empezar con 9",
                    details=[{"field": "phone", "rule": "pattern"}],
                )
            norm = "+51" + destination
        now = self.clock.now()
        with self.db.transaction() as c:
            prof = c.execute("SELECT * FROM wallet_profiles WHERE wallet_id=?", (wallet_id,)).fetchone()
            if prof[cfg["state"]] == cfg["active"]:
                raise ApiError(409, "ALREADY_VALIDATED", "El dato ya está validado")
            dup = c.execute(
                f"SELECT 1 FROM wallet_profiles WHERE {cfg['norm']}=? AND wallet_id<>?",
                (norm, wallet_id),
            ).fetchone()
            if dup is not None:
                raise ApiError(409, cfg["dup_code"], cfg["dup_msg"])
            last = c.execute(
                "SELECT created_at FROM otp_challenges WHERE wallet_id=? AND channel=? "
                "ORDER BY rowid DESC LIMIT 1",
                (wallet_id, channel),
            ).fetchone()
            if last is not None:
                allowed_at = _parse(last["created_at"]) + timedelta(seconds=OTP_INTERVAL_SECONDS)
                if now < allowed_at:
                    remaining = max(1, math.ceil((allowed_at - now).total_seconds()))
                    raise ApiError(
                        429,
                        "OTP_RATE_LIMITED",
                        "Debe esperar antes de solicitar un nuevo OTP",
                        retry_after_seconds=remaining,
                    )
            c.execute(
                "UPDATE otp_challenges SET status='INVALIDATED' "
                "WHERE wallet_id=? AND channel=? AND status='ACTIVE'",
                (wallet_id, channel),
            )
            code = self.provider.generate(channel, norm)  # mock: no se envía ni se devuelve
            expires_at = now + timedelta(seconds=OTP_TTL_SECONDS)
            c.execute(
                "INSERT INTO otp_challenges (id, wallet_id, channel, destination, code_hash, "
                "status, created_at, expires_at) VALUES (?, ?, ?, ?, ?, 'ACTIVE', ?, ?)",
                (
                    str(uuid.uuid4()),
                    wallet_id,
                    channel,
                    norm,
                    hash_code(code),
                    _ts(now),
                    _ts(expires_at),
                ),
            )
        result: Dict[str, Any] = {
            "channel": channel,
            "expires_at": _ts(expires_at),
            "expires_in_seconds": OTP_TTL_SECONDS,
            "next_request_allowed_at": _ts(now + timedelta(seconds=OTP_INTERVAL_SECONDS)),
            "otp_length": OTP_LENGTH,
            "delivery": "MOCK_NOT_SENT",
        }
        if channel == "PHONE":
            result["phone_e164"] = norm
        return result

    def confirm_otp(self, wallet_id: str, channel: str, submitted: str) -> Dict[str, Any]:
        cfg = _CHANNELS[channel]
        now = self.clock.now()
        with self.db.transaction() as c:
            ch = c.execute(
                "SELECT * FROM otp_challenges WHERE wallet_id=? AND channel=? "
                "ORDER BY rowid DESC LIMIT 1",
                (wallet_id, channel),
            ).fetchone()
            if ch is None or ch["status"] != "ACTIVE":
                raise ApiError(422, "OTP_NOT_ACTIVE", "No existe un OTP vigente")
            if now >= _parse(ch["expires_at"]):
                raise ApiError(422, "OTP_EXPIRED", "El OTP ha vencido")
            if not self.provider.confirm(submitted, ch["code_hash"]):
                raise ApiError(
                    422,
                    "VALIDATION_ERROR",
                    "OTP inválido",
                    details=[{"field": "otp", "rule": "non_empty"}],
                )
            dest = ch["destination"]
            dup = c.execute(
                f"SELECT 1 FROM wallet_profiles WHERE {cfg['norm']}=? AND wallet_id<>?",
                (dest, wallet_id),
            ).fetchone()
            if dup is not None:
                raise ApiError(409, cfg["dup_code"], cfg["dup_msg"])
            sets = {cfg["state"]: cfg["active"], cfg["verified_col"]: _ts(now)}
            if channel == "EMAIL":
                sets["email"] = dest
                sets["email_normalized"] = dest.lower()
            else:
                sets["phone_e164"] = dest
            sql = "UPDATE wallet_profiles SET " + ", ".join(f"{k}=?" for k in sets) + " WHERE wallet_id=?"
            c.execute(sql, (*sets.values(), wallet_id))
            c.execute(
                "UPDATE otp_challenges SET status='CONSUMED', consumed_at=? WHERE id=?",
                (_ts(now), ch["id"]),
            )
            prof = c.execute("SELECT * FROM wallet_profiles WHERE wallet_id=?", (wallet_id,)).fetchone()
            return {"wallet_id": wallet_id, "profile": _profile_dict(prof)}


class IdentityService(_Base):
    def mock_verify(self, wallet_id: str, terms_accepted: bool, inputs_confirmed: bool) -> Dict[str, Any]:
        if not self.settings.identity_mock_available:
            raise ApiError(403, "BIOMETRIC_MOCK_DISABLED", "El flujo mock no está habilitado")
        now = self.clock.now()
        with self.db.transaction() as c:
            acc = c.execute("SELECT * FROM wallet_accounts WHERE wallet_id=?", (wallet_id,)).fetchone()
            if acc["status"] == "ACTIVE_FULL":
                raise ApiError(409, "ALREADY_ACTIVE_FULL", "La identidad ya fue validada")
            if not terms_accepted:
                raise ApiError(422, "TERMS_NOT_ACCEPTED", "Debe aceptar los términos y condiciones")
            if not inputs_confirmed:
                raise ApiError(422, "MOCK_INPUTS_INVALID", "Debe confirmar los datos simulados")
            c.execute(
                "INSERT INTO terms_acceptances (wallet_id, purpose, accepted_at) VALUES (?, ?, ?)",
                (wallet_id, "BIOMETRIC_VERIFICATION", _ts(now)),
            )
            c.execute("UPDATE wallet_accounts SET status='ACTIVE_FULL' WHERE wallet_id=?", (wallet_id,))
            c.execute(
                "UPDATE wallet_profiles SET estado_c3='ACTIVE_BIOM', identity_verified_at=? "
                "WHERE wallet_id=?",
                (_ts(now), wallet_id),
            )
            acc = c.execute("SELECT * FROM wallet_accounts WHERE wallet_id=?", (wallet_id,)).fetchone()
            prof = c.execute("SELECT * FROM wallet_profiles WHERE wallet_id=?", (wallet_id,)).fetchone()
            return {"account": _account_dict(acc), "profile": _profile_dict(prof)}


class OperationService(_Base):
    def register_operation(self, wallet_id: str, op_type: str, amount: str) -> Dict[str, Any]:
        cents = money_to_cents(amount)
        today = self.clock.today_lima().isoformat()
        now = self.clock.now()
        with self.db.transaction() as c:
            acc = c.execute("SELECT * FROM wallet_accounts WHERE wallet_id=?", (wallet_id,)).fetchone()
            rules = c.execute(
                "SELECT * FROM limit_parameters WHERE account_status=? ORDER BY operation_group",
                (acc["status"],),
            ).fetchall()
            rule = next((r for r in rules if op_type in GROUP_TYPES[r["operation_group"]]), None)
            if rule is None:
                raise ApiError(
                    422, "OPERATION_NOT_ALLOWED", "Operación no permitida para el estado de la cuenta"
                )
            per = rule["per_operation_max_cents"]
            if per is not None and cents > per:
                raise ApiError(
                    422, "PER_OPERATION_LIMIT_EXCEEDED", "El monto supera el tope por operación"
                )
            types = GROUP_TYPES[rule["operation_group"]]
            marks = ",".join("?" for _ in types)
            accumulated = c.execute(
                "SELECT COALESCE(SUM(amount_cents), 0) AS total FROM operations "
                f"WHERE wallet_id=? AND operation_day=? AND operation_type IN ({marks})",
                (wallet_id, today, *types),
            ).fetchone()["total"]
            if accumulated + cents > rule["daily_max_cents"]:
                raise ApiError(422, "DAILY_LIMIT_EXCEEDED", "El monto supera el tope diario")
            operation_id = str(uuid.uuid4())
            c.execute(
                "INSERT INTO operations (id, wallet_id, operation_type, amount_cents, "
                "operation_day, account_status, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (operation_id, wallet_id, op_type, cents, today, acc["status"], _ts(now)),
            )
            return {
                "operation_id": operation_id,
                "operation_type": op_type,
                "amount": cents_to_money(cents),
                "operation_day": today,
                "daily_accumulated": cents_to_money(accumulated + cents),
                "daily_max": cents_to_money(rule["daily_max_cents"]),
            }
