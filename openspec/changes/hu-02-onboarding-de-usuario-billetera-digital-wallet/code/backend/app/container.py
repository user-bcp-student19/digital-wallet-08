from app.clock import PeruClock
from app.config import Settings
from app.db import Database
from app.otp import MockOtpProvider
from app.services import (
    AccountService,
    IdentityService,
    OnboardingService,
    OperationService,
    OtpService,
)


class Container:
    def __init__(self, settings: Settings, clock: PeruClock) -> None:
        self.settings = settings
        self.clock = clock
        self.db = Database(settings.db_path)
        args = (self.db, clock, settings)
        self.accounts = AccountService(*args)
        self.onboarding = OnboardingService(*args)
        self.otp = OtpService(*args, provider=MockOtpProvider())
        self.identity = IdentityService(*args)
        self.operations = OperationService(*args)
