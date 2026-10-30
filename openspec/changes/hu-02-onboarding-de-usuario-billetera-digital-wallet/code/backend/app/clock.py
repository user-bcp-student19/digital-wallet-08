from datetime import date, datetime, timedelta, timezone, tzinfo
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


def _lima_tz() -> tzinfo:
    try:
        return ZoneInfo("America/Lima")
    except ZoneInfoNotFoundError:  # Perú no tiene horario de verano: UTC-5 fijo
        return timezone(timedelta(hours=-5), "America/Lima")


LIMA = _lima_tz()


class PeruClock:
    """Reloj del servidor con día calendario en America/Lima. Inyectable en pruebas."""

    def now(self) -> datetime:
        return datetime.now(timezone.utc)

    def today_lima(self) -> date:
        return self.now().astimezone(LIMA).date()
