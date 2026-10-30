from typing import Annotated, Literal, Optional
from uuid import UUID

from pydantic import BaseModel, Field, StringConstraints, field_validator

from app import validators as v

NombresT = Annotated[
    str, StringConstraints(min_length=1, max_length=30, pattern=v.NOMBRES_PATTERN)
]
ApellidoT = Annotated[
    str, StringConstraints(min_length=1, max_length=20, pattern=v.APELLIDO_PATTERN)
]
UsuarioT = Annotated[
    str, StringConstraints(min_length=1, max_length=20, pattern=v.USUARIO_PATTERN)
]
PasswordT = Annotated[
    str, StringConstraints(min_length=10, max_length=64, pattern=v.PASSWORD_PATTERN)
]


class StepRequest(BaseModel):
    step: Literal["NOMBRES", "APELLIDO_PATERNO", "APELLIDO_MATERNO", "USUARIO", "CONTRASENA"]


class UsernameAvailabilityRequest(BaseModel):
    username: str = Field(min_length=1, max_length=64)
    nombres: Optional[str] = Field(default=None, max_length=64)
    apellido_paterno: Optional[str] = Field(default=None, max_length=64)
    apellido_materno: Optional[str] = Field(default=None, max_length=64)


class RegistrationRequest(BaseModel):
    session_id: Optional[UUID] = None
    nombres: NombresT
    apellido_paterno: ApellidoT
    apellido_materno: ApellidoT
    usuario: UsuarioT
    password: PasswordT = Field(repr=False)


class EmailOtpRequest(BaseModel):
    email: str = Field(min_length=1, max_length=254)


class PhoneOtpRequest(BaseModel):
    phone: str = Field(min_length=1, max_length=32)


class OtpConfirmationRequest(BaseModel):
    otp: str = Field(min_length=1, max_length=32)


class IdentityMockRequest(BaseModel):
    terms_accepted: bool
    mock_inputs_confirmed: bool


class OperationRequest(BaseModel):
    operation_type: Literal["TOPUP_OWN", "TOPUP_THIRD_PARTY", "PAYMENT"]
    amount: str = Field(pattern=v.MONEY_PATTERN, max_length=16)

    @field_validator("amount")
    @classmethod
    def _positive(cls, value: str) -> str:
        if float(value) <= 0:
            raise ValueError("amount must be greater than zero")
        return value
