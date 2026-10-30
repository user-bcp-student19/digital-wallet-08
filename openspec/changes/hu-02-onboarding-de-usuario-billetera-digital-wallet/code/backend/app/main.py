from typing import Optional
from uuid import UUID

from fastapi import Depends, FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.clock import PeruClock
from app.config import Settings
from app.container import Container
from app.errors import (
    ApiError,
    api_error_handler,
    http_error_handler,
    validation_error_handler,
)
from app.logging_guard import install_log_guard
from app.schemas import (
    EmailOtpRequest,
    IdentityMockRequest,
    OperationRequest,
    OtpConfirmationRequest,
    PhoneOtpRequest,
    RegistrationRequest,
    StepRequest,
    UsernameAvailabilityRequest,
)

basic = HTTPBasic(auto_error=False)


def get_ctx(request: Request) -> Container:
    return request.app.state.ctx


def current_wallet(
    wallet_id: UUID,
    ctx: Container = Depends(get_ctx),
    credentials: Optional[HTTPBasicCredentials] = Depends(basic),
) -> str:
    """HTTP Basic (sin tokens). El wallet_id de la ruta debe pertenecer al usuario."""
    challenge = {"WWW-Authenticate": "Basic"}
    if credentials is None:
        raise ApiError(401, "UNAUTHORIZED", "Credenciales requeridas", headers=challenge)
    own = ctx.accounts.authenticate(credentials.username, credentials.password)
    if own is None:
        raise ApiError(401, "UNAUTHORIZED", "Credenciales inválidas", headers=challenge)
    target = str(wallet_id)
    if target != own:
        if ctx.accounts.wallet_exists(target):
            raise ApiError(403, "FORBIDDEN", "La wallet no pertenece al usuario autenticado")
        raise ApiError(404, "NOT_FOUND", "Wallet no encontrada")
    return own


def create_app(settings: Optional[Settings] = None, clock: Optional[PeruClock] = None) -> FastAPI:
    settings = settings or Settings()
    install_log_guard()
    app = FastAPI(title="Wallet Onboarding API", version="1.0.0")
    app.state.ctx = Container(settings, clock or PeruClock())

    app.add_exception_handler(ApiError, api_error_handler)
    app.add_exception_handler(RequestValidationError, validation_error_handler)
    app.add_exception_handler(StarletteHTTPException, http_error_handler)

    # ---------------- Onboarding ----------------
    @app.post("/onboarding/sessions", status_code=201, tags=["Onboarding"],
              operation_id="startOnboardingSession")
    def start_session(ctx: Container = Depends(get_ctx)):
        return ctx.onboarding.start_session()

    @app.post("/onboarding/sessions/{session_id}/steps", status_code=201, tags=["Onboarding"],
              operation_id="registerOnboardingStep")
    def register_step(session_id: UUID, body: StepRequest, ctx: Container = Depends(get_ctx)):
        return ctx.onboarding.record_step(str(session_id), body.step)

    @app.post("/onboarding/username-availability", tags=["Onboarding"],
              operation_id="checkUsernameAvailability")
    def username_availability(body: UsernameAvailabilityRequest, ctx: Container = Depends(get_ctx)):
        return ctx.onboarding.check_username(
            body.username, body.nombres, body.apellido_paterno, body.apellido_materno
        )

    @app.post("/onboarding/registrations", status_code=201, tags=["Onboarding"],
              operation_id="registerWallet")
    def register_wallet(body: RegistrationRequest, ctx: Container = Depends(get_ctx)):
        return ctx.onboarding.register(body)

    # ---------------- Wallet ----------------
    @app.get("/wallets/{wallet_id}", tags=["Wallet"], operation_id="getWallet")
    def get_wallet(wid: str = Depends(current_wallet), ctx: Container = Depends(get_ctx)):
        return ctx.accounts.get_wallet(wid)

    @app.post("/wallets/{wallet_id}/operations", status_code=201, tags=["Wallet"],
              operation_id="registerOperation")
    def register_operation(
        body: OperationRequest, wid: str = Depends(current_wallet), ctx: Container = Depends(get_ctx)
    ):
        return ctx.operations.register_operation(wid, body.operation_type, body.amount)

    # ---------------- Perfil ----------------
    @app.post("/wallets/{wallet_id}/profile/email/otp-requests", status_code=201, tags=["Perfil"],
              operation_id="requestEmailOtp")
    def request_email_otp(
        body: EmailOtpRequest, wid: str = Depends(current_wallet), ctx: Container = Depends(get_ctx)
    ):
        return ctx.otp.request_otp(wid, "EMAIL", body.email)

    @app.post("/wallets/{wallet_id}/profile/email/otp-confirmations", tags=["Perfil"],
              operation_id="confirmEmailOtp")
    def confirm_email_otp(
        body: OtpConfirmationRequest,
        wid: str = Depends(current_wallet),
        ctx: Container = Depends(get_ctx),
    ):
        return ctx.otp.confirm_otp(wid, "EMAIL", body.otp)

    @app.post("/wallets/{wallet_id}/profile/phone/otp-requests", status_code=201, tags=["Perfil"],
              operation_id="requestPhoneOtp")
    def request_phone_otp(
        body: PhoneOtpRequest, wid: str = Depends(current_wallet), ctx: Container = Depends(get_ctx)
    ):
        return ctx.otp.request_otp(wid, "PHONE", body.phone)

    @app.post("/wallets/{wallet_id}/profile/phone/otp-confirmations", tags=["Perfil"],
              operation_id="confirmPhoneOtp")
    def confirm_phone_otp(
        body: OtpConfirmationRequest,
        wid: str = Depends(current_wallet),
        ctx: Container = Depends(get_ctx),
    ):
        return ctx.otp.confirm_otp(wid, "PHONE", body.otp)

    @app.post("/wallets/{wallet_id}/profile/identity/mock-verification", tags=["Perfil"],
              operation_id="mockIdentityVerification")
    def mock_identity(
        body: IdentityMockRequest,
        wid: str = Depends(current_wallet),
        ctx: Container = Depends(get_ctx),
    ):
        return ctx.identity.mock_verify(wid, body.terms_accepted, body.mock_inputs_confirmed)

    return app
