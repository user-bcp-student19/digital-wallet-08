import os
import sqlite3
import threading
from contextlib import contextmanager
from typing import Iterator

DDL = """
CREATE TABLE IF NOT EXISTS wallet_accounts (
    wallet_id TEXT PRIMARY KEY,
    username TEXT NOT NULL,
    username_normalized TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    password_salt TEXT NOT NULL,
    nombres TEXT NOT NULL,
    apellido_paterno TEXT NOT NULL,
    apellido_materno TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('ACTIVE_BASIC', 'ACTIVE_FULL')),
    balance_cents INTEGER NOT NULL DEFAULT 0,
    currency TEXT NOT NULL DEFAULT 'PEN',
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS wallet_profiles (
    wallet_id TEXT PRIMARY KEY REFERENCES wallet_accounts(wallet_id),
    email TEXT,
    email_normalized TEXT,
    estado_c1 TEXT NOT NULL DEFAULT 'PENDING_EMAIL',
    phone_e164 TEXT,
    estado_c2 TEXT NOT NULL DEFAULT 'PENDING_MOVIL',
    estado_c3 TEXT NOT NULL DEFAULT 'PENDING_BIOM',
    email_verified_at TEXT,
    phone_verified_at TEXT,
    identity_verified_at TEXT
);
CREATE UNIQUE INDEX IF NOT EXISTS ux_profiles_email
    ON wallet_profiles(email_normalized) WHERE email_normalized IS NOT NULL;
CREATE UNIQUE INDEX IF NOT EXISTS ux_profiles_phone
    ON wallet_profiles(phone_e164) WHERE phone_e164 IS NOT NULL;
CREATE TABLE IF NOT EXISTS onboarding_sessions (
    id TEXT PRIMARY KEY,
    started_at TEXT NOT NULL,
    completed_at TEXT,
    total_duration_ms INTEGER,
    wallet_id TEXT REFERENCES wallet_accounts(wallet_id)
);
CREATE TABLE IF NOT EXISTS onboarding_steps (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL REFERENCES onboarding_sessions(id),
    step TEXT NOT NULL,
    elapsed_ms INTEGER NOT NULL,
    completed_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS otp_challenges (
    id TEXT PRIMARY KEY,
    wallet_id TEXT NOT NULL REFERENCES wallet_accounts(wallet_id),
    channel TEXT NOT NULL CHECK (channel IN ('EMAIL', 'PHONE')),
    destination TEXT NOT NULL,
    code_hash TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('ACTIVE', 'INVALIDATED', 'CONSUMED')),
    created_at TEXT NOT NULL,
    expires_at TEXT NOT NULL,
    consumed_at TEXT
);
CREATE INDEX IF NOT EXISTS ix_otp_wallet_channel ON otp_challenges(wallet_id, channel, created_at);
CREATE TABLE IF NOT EXISTS terms_acceptances (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    wallet_id TEXT NOT NULL REFERENCES wallet_accounts(wallet_id),
    purpose TEXT NOT NULL,
    accepted_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS limit_parameters (
    account_status TEXT NOT NULL,
    operation_group TEXT NOT NULL CHECK (operation_group IN ('COMBINED', 'TOPUP', 'PAYMENT')),
    per_operation_max_cents INTEGER,
    daily_max_cents INTEGER NOT NULL,
    PRIMARY KEY (account_status, operation_group)
);
CREATE TABLE IF NOT EXISTS operations (
    id TEXT PRIMARY KEY,
    wallet_id TEXT NOT NULL REFERENCES wallet_accounts(wallet_id),
    operation_type TEXT NOT NULL
        CHECK (operation_type IN ('TOPUP_OWN', 'TOPUP_THIRD_PARTY', 'PAYMENT')),
    amount_cents INTEGER NOT NULL CHECK (amount_cents > 0),
    operation_day TEXT NOT NULL,
    account_status TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_operations_wallet_day ON operations(wallet_id, operation_day);
INSERT OR IGNORE INTO limit_parameters VALUES
    ('ACTIVE_BASIC', 'COMBINED', 2000, 6000),
    ('ACTIVE_FULL', 'TOPUP', NULL, 100000),
    ('ACTIVE_FULL', 'PAYMENT', 50000, 100000);
"""


class Database:
    """Conexión SQLite única, serializada con un lock. Transacciones con BEGIN IMMEDIATE."""

    def __init__(self, path: str) -> None:
        self._conn = sqlite3.connect(path, check_same_thread=False, isolation_level=None)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA foreign_keys=ON")
        self._lock = threading.RLock()
        self._conn.executescript(DDL)
        if path != ":memory:":
            try:
                os.chmod(path, 0o600)
            except OSError:
                pass

    @contextmanager
    def transaction(self) -> Iterator[sqlite3.Connection]:
        with self._lock:
            self._conn.execute("BEGIN IMMEDIATE")
            try:
                yield self._conn
            except BaseException:
                self._conn.execute("ROLLBACK")
                raise
            else:
                self._conn.execute("COMMIT")
