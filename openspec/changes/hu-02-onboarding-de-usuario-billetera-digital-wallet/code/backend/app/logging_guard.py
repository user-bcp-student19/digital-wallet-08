"""PersonalDataGuard: ningún log debe contener contraseñas, OTP ni la cabecera Authorization."""

import logging
import re

_BASIC = re.compile(r"Basic\s+[A-Za-z0-9+/=]+", re.IGNORECASE)
_KEYS = re.compile(r"(password|passwd|authorization|otp)\s*[=:]\s*\S+", re.IGNORECASE)


def redact(text: str) -> str:
    return _KEYS.sub("[REDACTED]", _BASIC.sub("[REDACTED]", text))


class PersonalDataFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        try:
            message = record.getMessage()
        except Exception:  # noqa: BLE001
            message = str(record.msg)
        redacted = redact(message)
        if redacted != message:
            record.msg = redacted
            record.args = ()
        return True


def install_log_guard() -> None:
    names = ("", "wallet", "uvicorn", "uvicorn.access", "uvicorn.error")
    for name in names:
        target = logging.getLogger(name)
        holders = [target] + list(target.handlers)
        for holder in holders:
            if not any(isinstance(f, PersonalDataFilter) for f in holder.filters):
                holder.addFilter(PersonalDataFilter())
