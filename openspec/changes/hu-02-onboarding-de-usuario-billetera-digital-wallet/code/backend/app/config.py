import os
from dataclasses import dataclass, field

MOCK_ENVIRONMENTS = {"development", "testing"}


@dataclass
class Settings:
    """Configuración por entorno. No contiene secretos."""

    app_env: str = field(default_factory=lambda: os.getenv("APP_ENV", "development"))
    db_path: str = field(default_factory=lambda: os.getenv("WALLET_DB_PATH", "wallet.db"))
    pbkdf2_iterations: int = 120_000

    @property
    def identity_mock_available(self) -> bool:
        return self.app_env in MOCK_ENVIRONMENTS
