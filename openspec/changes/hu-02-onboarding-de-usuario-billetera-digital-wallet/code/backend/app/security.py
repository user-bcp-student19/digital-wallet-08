import hashlib
import hmac
import secrets
from typing import Tuple

ALGO = "pbkdf2_sha256"


def hash_password(password: str, iterations: int) -> Tuple[str, str]:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
    return f"{ALGO}${iterations}${digest.hex()}", salt.hex()


def verify_password(password: str, stored_hash: str, salt_hex: str) -> bool:
    try:
        algo, iterations, digest_hex = stored_hash.split("$")
        if algo != ALGO:
            return False
        digest = hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"), bytes.fromhex(salt_hex), int(iterations)
        )
    except (ValueError, TypeError):
        return False
    return hmac.compare_digest(digest.hex(), digest_hex)


def dummy_verify(password: str, iterations: int) -> None:
    """Iguala el tiempo de respuesta cuando el usuario no existe."""
    hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), b"0" * 16, iterations)
