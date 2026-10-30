import re

LETTERS = "A-Za-zÁÉÍÓÚÜÑáéíóúüñ"
NOMBRES_PATTERN = rf"^[{LETTERS}]+( [{LETTERS}]+)*$"
APELLIDO_PATTERN = rf"^[{LETTERS}]+$"
USUARIO_PATTERN = r"^[!-~]*[A-Za-z][!-~]*$"
PASSWORD_PATTERN = r"^[!-~]{10,64}$"
MONEY_PATTERN = r"^(0|[1-9][0-9]*)(\.[0-9]{1,2})?$"

_LABEL = r"[A-Za-z0-9](?:[A-Za-z0-9\-]*[A-Za-z0-9])?"
EMAIL_RE = re.compile(rf"[A-Za-z0-9._%+\-]+@{_LABEL}(?:\.{_LABEL})+")
PHONE_RE = re.compile(r"9[0-9]{8}")


def is_valid_nombres(value: str) -> bool:
    return len(value) <= 30 and re.fullmatch(NOMBRES_PATTERN, value) is not None


def is_valid_apellido(value: str) -> bool:
    return len(value) <= 20 and re.fullmatch(APELLIDO_PATTERN, value) is not None


def is_valid_usuario(value: str) -> bool:
    return 1 <= len(value) <= 20 and re.fullmatch(USUARIO_PATTERN, value) is not None


def is_valid_password(value: str) -> bool:
    return re.fullmatch(PASSWORD_PATTERN, value) is not None


def is_valid_email(value: str) -> bool:
    return len(value) <= 254 and EMAIL_RE.fullmatch(value) is not None


def is_valid_phone(value: str) -> bool:
    return PHONE_RE.fullmatch(value) is not None
