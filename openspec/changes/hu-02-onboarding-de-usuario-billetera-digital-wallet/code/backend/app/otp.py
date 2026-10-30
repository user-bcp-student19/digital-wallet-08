import hashlib
import secrets
import string
from typing import Protocol

OTP_LENGTH = 6
OTP_TTL_SECONDS = 60
OTP_INTERVAL_SECONDS = 45


def hash_code(code: str) -> str:
    return hashlib.sha256(code.encode("utf-8")).hexdigest()


class OtpProvider(Protocol):
    def generate(self, channel: str, destination: str) -> str: ...

    def confirm(self, submitted: str, code_hash: str) -> bool: ...


class MockOtpProvider:
    """Genera un OTP de 6 caracteres sin enviarlo y confirma cualquier valor no vacío.

    La vigencia e invalidación las controla OtpService. Sin llamadas de red.
    """

    def generate(self, channel: str, destination: str) -> str:
        return "".join(secrets.choice(string.digits) for _ in range(OTP_LENGTH))

    def confirm(self, submitted: str, code_hash: str) -> bool:
        return bool(submitted.strip())
