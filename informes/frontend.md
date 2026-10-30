# Cliente frontend (Streamlit) – HU 01 Onboarding Wallet

No ejecuté el código ni lo probé contra el backend. Está escrito para Python 3.10 o superior y Streamlit 1.37 o superior (usa `st.fragment` y `st.query_params`).

**Puerto del backend.** El encargo indica `http://localhost:8000`, pero el README del backend arranca en `:8080`. La URL base es configurable en la barra lateral o con la variable `WALLET_API_URL`. El valor por defecto es `http://localhost:8000`, y el cliente añade `/v1` si falta.

## Estructura

```
wallet-frontend/
├── README.md
├── requirements.txt
├── api_client.py      # Cliente HTTP tipado hacia los endpoints /v1 de FastAPI
├── validators.py      # Validaciones espejo del contrato (feedback inmediato)
├── app.py             # UI Streamlit: onboarding → landing → perfil → biometría mock
└── smoke_test.py      # Verificación end-to-end por consola contra el backend
```

---

## `requirements.txt`

```text
streamlit>=1.37
requests>=2.31
```

---

## `api_client.py`

```python
"""Cliente HTTP de la API Wallet (FastAPI). Un método por operationId del contrato.

- Todas las respuestas de error del backend siguen el esquema Error
  {code, message, fields?, traceId?} (+ suggestions en USERNAME_TAKEN).
- Nunca se registra ni se imprime el cuerpo de las peticiones (contiene contraseña/PII).
- Las peticiones POST no se reintentan automáticamente (evita wallets duplicados en el KYC).
"""
from __future__ import annotations

import os
from typing import Any

import requests

DEFAULT_BASE_URL = os.getenv("WALLET_API_URL", "http://localhost:8000")

# Mensajes amigables por código de error del backend (UX: lenguaje claro y acción siguiente).
ERROR_MESSAGES: dict[str, str] = {
    "INVALID_FIELD": "Revisa los datos ingresados, hay campos con formato inválido.",
    "USERNAME_TAKEN": "Ese usuario ya está en uso. Prueba con una de las sugerencias.",
    "UNAUTHORIZED": "Tu sesión no está autenticada. Revisa el token en la barra lateral.",
    "NOT_FOUND": "No encontramos el recurso solicitado.",
    "EXTERNAL_TIMEOUT": "El servicio de wallet tardó demasiado en responder. Inténtalo nuevamente.",
    "EXTERNAL_ERROR": "El servicio de wallet no está disponible en este momento. Inténtalo en unos minutos.",
    "EXTERNAL_BAD_REQUEST": "El servicio de wallet rechazó los datos enviados. Verifica tus nombres y apellidos.",
    "WALLET_NOT_FOUND_EXTERNAL": "Tu billetera no se encontró en el servicio externo. Contacta a soporte.",
    "OTP_TOO_SOON": "Debes esperar antes de pedir otro código.",
    "OTP_INVALID": "El código es incorrecto. Si sigues fallando, solicita uno nuevo.",
    "OTP_EXPIRED": "El código venció. Solicita uno nuevo.",
    "EMAIL_ALREADY_REGISTERED": "Ese correo ya está registrado en otra cuenta.",
    "MOBILE_ALREADY_REGISTERED": "Ese celular ya está registrado en otra cuenta.",
    "CONSENT_REQUIRED": "Primero debes aceptar los términos y el manejo de datos personales.",
    "ALREADY_ACTIVE_FULL": "Tu cuenta ya tiene la verificación completa.",
    "MOCK_NOT_AVAILABLE": "La verificación biométrica simulada no está disponible en este ambiente.",
    "SESSION_CLOSED": "La sesión de medición ya estaba cerrada.",
    "INTERNAL_ERROR": "Ocurrió un error interno. Inténtalo nuevamente.",
    "NETWORK_ERROR": "No pudimos conectar con el servidor. Verifica la URL de la API y que esté en ejecución.",
    "CLIENT_TIMEOUT": "El servidor tardó demasiado en responder. Inténtalo nuevamente.",
}


class ApiError(Exception):
    def __init__(
        self,
        status: int,
        code: str,
        message: str,
        *,
        fields: list[dict[str, str]] | None = None,
        trace_id: str | None = None,
        suggestions: list[str] | None = None,
        retry_after: int | None = None,
    ) -> None:
        super().__init__(message)
        self.status = status
        self.code = code
        self.message = message
        self.fields = fields or []
        self.trace_id = trace_id
        self.suggestions = suggestions or []
        self.retry_after = retry_after

    def friendly(self) -> str:
        text = ERROR_MESSAGES.get(self.code, self.message or "Ocurrió un error inesperado.")
        if self.code == "OTP_TOO_SOON" and self.retry_after:
            text += f" Intenta de nuevo en {self.retry_after} s."
        return text


class WalletApiClient:
    def __init__(self, base_url: str = DEFAULT_BASE_URL, token: str | None = None,
                 timeout: tuple[float, float] = (3.05, 20.0)) -> None:
        base = base_url.strip().rstrip("/")
        if not base.endswith("/v1"):
            base += "/v1"
        self.base = base
        self.token = (token or "").strip()
        # lectura 20 s: el backend puede tardar hasta ~2 s de conexión + 5 s de lectura (+ reintento GET) con el wallet externo.
        self.timeout = timeout

    # ------------------------------------------------------------ núcleo
    def _request(self, method: str, path: str, *, json: Any = None,
                 params: dict[str, Any] | None = None, auth: bool = False) -> Any:
        headers = {"Accept": "application/json"}
        if auth and self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        try:
            resp = requests.request(
                method, f"{self.base}{path}", json=json, params=params,
                headers=headers, timeout=self.timeout,
            )
        except requests.Timeout:
            raise ApiError(0, "CLIENT_TIMEOUT", "Timeout del cliente")
        except requests.RequestException:
            raise ApiError(0, "NETWORK_ERROR", "Sin conexión con el servidor")
        if resp.status_code >= 400:
            raise self._to_error(resp)
        try:
            return resp.json()
        except ValueError:
            raise ApiError(resp.status_code, "INTERNAL_ERROR", "Respuesta no válida del servidor")

    @staticmethod
    def _to_error(resp: requests.Response) -> ApiError:
        try:
            body = resp.json()
        except ValueError:
            body = {}
        if not isinstance(body, dict):
            body = {}
        retry_after = None
        raw = resp.headers.get("Retry-After")
        if raw and raw.isdigit():
            retry_after = int(raw)
        return ApiError(
            resp.status_code,
            str(body.get("code") or "HTTP_ERROR"),
            str(body.get("message") or f"Error HTTP {resp.status_code}"),
            fields=body.get("fields"),
            trace_id=body.get("traceId") or resp.headers.get("X-Trace-Id"),
            suggestions=body.get("suggestions"),
            retry_after=retry_after,
        )

    # --------------------------------------------------------- Onboarding
    def start_session(self) -> dict:                                  # startOnboardingSession
        return self._request("POST", "/onboarding/sessions")

    def register_step(self, session_id: str, step: str) -> dict:      # registerOnboardingStep
        return self._request("POST", f"/onboarding/sessions/{session_id}/steps", json={"step": step})

    def check_username(self, username: str, first_names: str = "",
                       paternal_surname: str = "", maternal_surname: str = "") -> dict:  # checkUsernameAvailability
        params = {"username": username}
        if first_names:
            params["firstNames"] = first_names
        if paternal_surname:
            params["paternalSurname"] = paternal_surname
        if maternal_surname:
            params["maternalSurname"] = maternal_surname
        return self._request("GET", "/usernames/availability", params=params)

    # ------------------------------------------------------------- Cuenta
    def create_account(self, payload: dict) -> dict:                  # createAccount (sin reintentos)
        return self._request("POST", "/accounts", json=payload)

    def get_account(self, account_id: str) -> dict:                   # getAccount (bearer)
        return self._request("GET", f"/accounts/{account_id}", auth=True)

    # ------------------------------------------------------------- Perfil
    def request_email_otp(self, account_id: str, email: str) -> dict:
        return self._request("POST", f"/accounts/{account_id}/email/otp", json={"email": email}, auth=True)

    def verify_email_otp(self, account_id: str, code: str) -> dict:
        return self._request("POST", f"/accounts/{account_id}/email/otp/verification",
                             json={"code": code}, auth=True)

    def request_mobile_otp(self, account_id: str, mobile_number: str) -> dict:
        return self._request("POST", f"/accounts/{account_id}/mobile/otp",
                             json={"mobileNumber": mobile_number}, auth=True)

    def verify_mobile_otp(self, account_id: str, code: str) -> dict:
        return self._request("POST", f"/accounts/{account_id}/mobile/otp/verification",
                             json={"code": code}, auth=True)

    def accept_consent(self, account_id: str, terms_version: str) -> dict:
        return self._request("POST", f"/accounts/{account_id}/consents",
                             json={"accepted": True, "termsVersion": terms_version}, auth=True)

    def mock_biometric(self, account_id: str, dni_number: str) -> dict:
        return self._request("POST", f"/accounts/{account_id}/biometric/mock-verification",
                             json={"dniNumber": dni_number}, auth=True)

    # ------------------------------------------------------------- Utilidad
    def ping(self) -> bool:
        """Comprueba que el servidor responde (usa /openapi.json, fuera de /v1)."""
        root = self.base[: -len("/v1")]
        try:
            return requests.get(f"{root}/openapi.json", timeout=self.timeout).status_code == 200
        except requests.RequestException:
            return False
```

---

## `validators.py`

```python
"""Validaciones del lado cliente, espejo de las reglas del contrato (el backend sigue siendo la autoridad).
Cada función devuelve un mensaje de error o None si es válido."""
from __future__ import annotations

import re

_L = "A-Za-zÁÉÍÓÚÜÑáéíóúüñ"
FIRST_NAMES_RE = re.compile(rf"^[{_L}]+( [{_L}]+)*$")
SURNAME_RE = re.compile(rf"^[{_L}]+$")
USERNAME_RE = re.compile(r"^(?=.*[A-Za-z])[\x21-\x7E]{1,20}$")
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
MOBILE_RE = re.compile(r"^9[0-9]{8}$")
OTP_RE = re.compile(r"^[0-9]{6}$")
DNI_RE = re.compile(r"^[0-9]{8}$")


def normalize_spaces(text: str) -> str:
    return " ".join((text or "").split())


def validate_first_names(value: str) -> str | None:
    if not value:
        return "Ingresa tus nombres."
    if len(value) > 30:
        return "Máximo 30 caracteres."
    if not FIRST_NAMES_RE.fullmatch(value):
        return "Solo letras y espacios simples (sin números ni símbolos)."
    return None


def validate_surname(value: str) -> str | None:
    if not value:
        return "Campo obligatorio."
    if len(value) > 20:
        return "Máximo 20 caracteres."
    if not SURNAME_RE.fullmatch(value):
        return "Solo letras, sin espacios, números ni símbolos."
    return None


def validate_username(value: str) -> str | None:
    if not value:
        return "Ingresa un usuario."
    if len(value) > 20:
        return "Máximo 20 caracteres."
    if not USERNAME_RE.fullmatch(value):
        return "Usa caracteres imprimibles sin espacios y al menos una letra."
    return None


def validate_password(value: str) -> str | None:
    if len(value) < 8:
        return "La contraseña debe tener al menos 8 caracteres."
    if len(value) > 64:
        return "La contraseña admite máximo 64 caracteres."
    return None


def validate_email(value: str) -> str | None:
    value = (value or "").strip()
    if not value:
        return "Ingresa tu correo."
    if len(value) > 254 or not EMAIL_RE.fullmatch(value):
        return "Ingresa un correo válido (nombre@dominio.com)."
    return None


def validate_mobile(value: str) -> str | None:
    if not MOBILE_RE.fullmatch((value or "").strip()):
        return "Ingresa 9 dígitos que empiecen con 9 (sin +51)."
    return None


def validate_otp(value: str) -> str | None:
    if not OTP_RE.fullmatch((value or "").strip()):
        return "El código tiene 6 dígitos."
    return None


def validate_dni(value: str) -> str | None:
    if not DNI_RE.fullmatch((value or "").strip()):
        return "El DNI tiene 8 dígitos."
    return None
```

---

## `app.py`

```python
"""UI Streamlit para HU 01 – Onboarding de usuario (billetera digital).

Flujo:
  1) Datos personales  →  2) Credenciales (usuario con disponibilidad en vivo + contraseña)
  3) Cuenta creada (ACTIVE_BASIC) → landing con saldo, límites, uso diario y perfil pendiente
  4) Perfil: correo (C1) y celular (C2) con OTP (vigencia 60 s, reenvío 45 s), consentimiento + biometría mock (C3)

Ejecutar:  streamlit run app.py
"""
from __future__ import annotations

import os
import time
import uuid

import streamlit as st

import validators as v
from api_client import DEFAULT_BASE_URL, ApiError, WalletApiClient

st.set_page_config(page_title="Wallet · Crea tu cuenta", page_icon="👛", layout="centered")

STAGES = ["personal", "credentials", "landing"]
STAGE_LABELS = {"personal": "1 · Tus datos", "credentials": "2 · Tu acceso", "landing": "3 · Tu billetera"}

STATE_DEFAULTS = {
    "base_url": DEFAULT_BASE_URL,
    "token": os.getenv("WALLET_API_TOKEN", "dev-token"),
    "stage": "personal",
    "form": {},                 # datos personales confirmados (la contraseña NUNCA se guarda aquí)
    "onb_session_id": None,
    "onb_session_tried": False,
    "account": None,            # respuesta de createAccount
    "summary": None,            # respuesta de getAccount
    "summary_dirty": True,
    "landing_reported": False,
    "otp": {},                  # estado local de temporizadores OTP por canal
    "consent_done": False,
    "username_check": None,
    "flash": None,
}
for _k, _v in STATE_DEFAULTS.items():
    st.session_state.setdefault(_k, _v)


# ----------------------------------------------------------------- utilidades
def client() -> WalletApiClient:
    return WalletApiClient(st.session_state.base_url, st.session_state.token)


def money(cents: int | None) -> str:
    return "Sin tope" if cents is None else f"S/ {cents / 100:,.2f}"


def show_error(err: ApiError) -> None:
    st.error(err.friendly())
    details = [f"código: `{err.code}`"]
    if err.status:
        details.append(f"HTTP {err.status}")
    if err.trace_id:
        details.append(f"traceId: `{err.trace_id}`")
    st.caption(" · ".join(details))
    if err.fields:
        st.caption("Campos: " + ", ".join(f"{f.get('field')} ({f.get('rule')})" for f in err.fields))


def safe(fn, *args, **kwargs):
    """Ejecuta una llamada a la API; muestra el error y devuelve (ok, resultado)."""
    try:
        return True, fn(*args, **kwargs)
    except ApiError as exc:
        show_error(exc)
        return False, exc


def flash(kind: str, text: str) -> None:
    st.session_state.flash = (kind, text)


def reset_flow() -> None:
    for key, default in STATE_DEFAULTS.items():
        if key not in ("base_url", "token"):
            st.session_state[key] = default if not isinstance(default, (dict, list)) else type(default)()
    for key in ("pwd", "pwd2", "username", "first_names_in", "paternal_in", "maternal_in",
                "email_in", "mobile_in", "email_code", "mobile_code", "dni_in"):
        st.session_state.pop(key, None)
    st.query_params.clear()


def ensure_onboarding_session() -> None:
    """CA-01: inicia la medición. Si falla, el flujo continúa sin medición (no bloquea al usuario)."""
    if st.session_state.onb_session_tried:
        return
    st.session_state.onb_session_tried = True
    try:
        st.session_state.onb_session_id = client().start_session()["sessionId"]
    except ApiError:
        st.session_state.onb_session_id = None


def report_step(step: str) -> None:
    """Registro de pasos best-effort: un fallo de medición nunca interrumpe al usuario."""
    sid = st.session_state.onb_session_id
    if not sid:
        return
    try:
        client().register_step(sid, step)
    except ApiError:
        pass


# --------------------------------------------------------------- barra lateral
with st.sidebar:
    st.header("⚙️ Conexión")
    st.text_input("URL de la API", key="base_url", help="Servidor FastAPI. Se añade /v1 automáticamente.")
    st.text_input("Token Bearer", key="token", type="password",
                  help="El backend solo valida que la cabecera Authorization: Bearer <token> esté bien formada.")
    if st.button("Probar conexión", use_container_width=True):
        st.success("Servidor disponible ✅") if client().ping() else st.error("No hay respuesta del servidor ❌")
    st.divider()
    if st.session_state.account:
        st.caption("Cuenta actual")
        st.code(st.session_state.account["accountId"], language=None)
    with st.expander("Ya tengo una cuenta"):
        acc_in = st.text_input("accountId (UUID)", key="existing_account")
        if st.button("Abrir mi billetera"):
            try:
                uuid.UUID(acc_in.strip())
            except ValueError:
                st.error("El identificador no es un UUID válido.")
            else:
                st.session_state.account = {"accountId": acc_in.strip()}
                st.session_state.stage = "landing"
                st.session_state.summary = None
                st.session_state.summary_dirty = True
                st.session_state.landing_reported = True  # sesión de medición ajena a este flujo
                st.query_params["accountId"] = acc_in.strip()
                st.rerun()
    if st.button("Reiniciar flujo", use_container_width=True):
        reset_flow()
        st.rerun()

# Recuperar cuenta tras recargar el navegador (el id viaja en la URL, nunca la contraseña).
if st.session_state.account is None and "accountId" in st.query_params:
    try:
        uuid.UUID(st.query_params["accountId"])
        st.session_state.account = {"accountId": st.query_params["accountId"]}
        st.session_state.stage = "landing"
        st.session_state.landing_reported = True
    except ValueError:
        st.query_params.clear()

# ------------------------------------------------------------------ cabecera
st.title("👛 Tu billetera digital")
current = STAGES.index(st.session_state.stage)
st.progress((current + 1) / len(STAGES), text=STAGE_LABELS[st.session_state.stage])

if st.session_state.flash:
    kind, text = st.session_state.flash
    getattr(st, kind)(text)
    st.session_state.flash = None


# ================================================================== PASO 1
def render_personal() -> None:
    ensure_onboarding_session()
    st.subheader("Cuéntanos quién eres")
    st.caption("Usa tus nombres y apellidos tal como figuran en tu DNI.")
    saved = st.session_state.form
    with st.form("personal_form"):
        first = st.text_input("Nombres", value=saved.get("firstNames", ""), max_chars=30,
                              key="first_names_in", placeholder="Ana María")
        pat = st.text_input("Apellido paterno", value=saved.get("paternalSurname", ""), max_chars=20,
                            key="paternal_in")
        mat = st.text_input("Apellido materno", value=saved.get("maternalSurname", ""), max_chars=20,
                            key="maternal_in")
        submitted = st.form_submit_button("Continuar", type="primary", use_container_width=True)
    if not submitted:
        return
    first, pat, mat = v.normalize_spaces(first), (pat or "").strip(), (mat or "").strip()
    errors = {
        "Nombres": v.validate_first_names(first),
        "Apellido paterno": v.validate_surname(pat),
        "Apellido materno": v.validate_surname(mat),
    }
    problems = {k: e for k, e in errors.items() if e}
    if problems:
        for label, msg in problems.items():
            st.error(f"**{label}:** {msg}")
        return
    st.session_state.form = {"firstNames": first, "paternalSurname": pat, "maternalSurname": mat}
    report_step("PERSONAL_DATA_COMPLETED")
    st.session_state.stage = "credentials"
    st.rerun()


# ================================================================== PASO 2
def run_username_check() -> None:
    """Callback de on_change: consulta disponibilidad (CA-02) y guarda el resultado para mostrarlo."""
    username = st.session_state.get("username", "")
    if not username:
        st.session_state.username_check = None
        return
    err = v.validate_username(username)
    if err:
        st.session_state.username_check = {"username": username, "error": err}
        return
    f = st.session_state.form
    try:
        res = client().check_username(username, f.get("firstNames", ""),
                                      f.get("paternalSurname", ""), f.get("maternalSurname", ""))
        st.session_state.username_check = {"username": username, **res}
    except ApiError as exc:
        st.session_state.username_check = {"username": username, "api_error": exc}


def pick_suggestion(suggestion: str) -> None:
    st.session_state["username"] = suggestion
    run_username_check()


def render_username_feedback() -> None:
    chk = st.session_state.username_check
    if not chk or chk.get("username") != st.session_state.get("username"):
        return
    if chk.get("error"):
        st.warning(chk["error"])
    elif chk.get("api_error"):
        st.warning("No pudimos verificar la disponibilidad ahora; lo validaremos al crear tu cuenta.")
    elif chk.get("available"):
        st.success("✅ Usuario disponible")
    else:
        st.error("Ese usuario ya está en uso.")
        suggestions = chk.get("suggestions") or []
        if suggestions:
            st.caption("Prueba con alguno de estos:")
            cols = st.columns(len(suggestions))
            for col, s in zip(cols, suggestions):
                col.button(s, key=f"sug_{s}", on_click=pick_suggestion, args=(s,), use_container_width=True)


def render_credentials() -> None:
    f = st.session_state.form
    st.subheader(f"Hola, {f.get('firstNames', '')} 👋")
    st.caption("Elige tu usuario y una contraseña para ingresar a tu billetera.")
    st.text_input("Usuario", key="username", max_chars=20, on_change=run_username_check,
                  help="Hasta 20 caracteres, sin espacios y con al menos una letra. Presiona Enter para validar.")
    render_username_feedback()
    st.text_input("Contraseña", key="pwd", type="password", max_chars=64,
                  help="Entre 8 y 64 caracteres.")
    st.text_input("Confirma tu contraseña", key="pwd2", type="password", max_chars=64)

    col_back, col_go = st.columns([1, 2])
    if col_back.button("← Volver", use_container_width=True):
        st.session_state.stage = "personal"
        st.rerun()
    if not col_go.button("Crear mi billetera", type="primary", use_container_width=True):
        return

    username, pwd, pwd2 = st.session_state.get("username", ""), st.session_state.get("pwd", ""), st.session_state.get("pwd2", "")
    errors = [e for e in (v.validate_username(username), v.validate_password(pwd)) if e]
    if pwd != pwd2:
        errors.append("Las contraseñas no coinciden.")
    if errors:
        for e in errors:
            st.error(e)
        return

    report_step("CREDENTIALS_COMPLETED")
    payload = {**f, "username": username, "password": pwd}
    if st.session_state.onb_session_id:
        payload["onboardingSessionId"] = st.session_state.onb_session_id

    # Sin reintentos automáticos: el KYC crea un wallet externo y no es idempotente.
    with st.spinner("Creando tu billetera…"):
        ok, result = safe(client().create_account, payload)
    payload["password"] = pwd = ""  # no conservar la contraseña en memoria más de lo necesario
    if not ok:
        err: ApiError = result
        if err.code == "USERNAME_TAKEN" and err.suggestions:
            st.session_state.username_check = {"username": username, "available": False,
                                               "suggestions": err.suggestions}
            st.info("Elegimos algunas alternativas para ti; revísalas arriba y vuelve a intentar.")
        elif err.code in ("EXTERNAL_TIMEOUT", "CLIENT_TIMEOUT"):
            st.info("Tus datos siguen aquí: puedes presionar nuevamente “Crear mi billetera”.")
        return

    st.session_state.account = result
    st.session_state.stage = "landing"
    st.session_state.summary_dirty = True
    st.query_params["accountId"] = result["accountId"]
    flash("success", "🎉 ¡Tu cuenta fue creada! Ya puedes usar tu billetera.")
    st.rerun()


# ================================================================== PASO 3
def load_summary() -> bool:
    """Carga/recarga la landing (getAccount). Mantiene el último resumen si la recarga falla."""
    if st.session_state.summary is not None and not st.session_state.summary_dirty:
        return True
    with st.spinner("Cargando tu billetera…"):
        ok, result = safe(client().get_account, st.session_state.account["accountId"])
    if ok:
        st.session_state.summary = result
        st.session_state.summary_dirty = False
        return True
    if st.button("Reintentar", key="retry_summary"):
        st.rerun()
    return st.session_state.summary is not None


PROFILE_ITEMS = [
    ("emailStatus", "ACTIVE_EMAIL", "Correo"),
    ("mobileStatus", "ACTIVE_MOVIL", "Celular"),
    ("biometricStatus", "ACTIVE_BIOM", "Identidad (biometría)"),
]


def render_summary(s: dict) -> None:
    status_label = "Cuenta completa" if s["status"] == "ACTIVE_FULL" else "Cuenta básica"
    st.subheader(f"Hola, {s['firstNames']} · {status_label}")
    c1, c2 = st.columns(2)
    c1.metric("Saldo disponible", money(s["balanceCents"]))
    c2.metric("Billetera", s["walletId"])

    if s.get("profilePending") and s.get("profilePendingMessage"):
        st.warning(s["profilePendingMessage"])

    prof = s["profile"]
    cols = st.columns(3)
    for col, (key, active, label) in zip(cols, PROFILE_ITEMS):
        col.markdown(f"{'✅' if prof.get(key) == active else '⏳'} **{label}**")

    lim, use = s["limits"], s["dailyUsage"]
    with st.expander("Mis límites y uso de hoy", expanded=True):
        st.caption(f"Día {use['date']} · zona horaria {use['timezone']}")
        for label, used, cap in (
            ("Recargas del día", use["rechargedCents"], lim.get("rechargeDailyCents")),
            ("Pagos del día", use["paidCents"], lim.get("paymentDailyCents")),
        ):
            ratio = min(1.0, used / cap) if cap else 0.0
            st.progress(ratio, text=f"{label}: {money(used)} de {money(cap)}")
        st.table({
            "Operación": ["Recarga propia", "Recarga a terceros", "Pagos",
                          "Tope por recarga", "Tope por pago"],
            "Permitido / Tope": [
                "Sí" if lim["allowsOwnRecharge"] else "No",
                "Sí" if lim["allowsThirdPartyRecharge"] else "No (verifica tu identidad)",
                "Sí" if lim["allowsPayments"] else "No",
                money(lim.get("rechargePerOperationCents")),
                money(lim.get("paymentPerOperationCents")),
            ],
        })
    if st.button("🔄 Actualizar", key="refresh"):
        st.session_state.summary_dirty = True
        st.rerun()


# ---- OTP (correo y celular) -------------------------------------------------
OTP_CHANNELS = {
    "email": dict(
        title="Correo electrónico", status_key="emailStatus", active="ACTIVE_EMAIL",
        input_label="Correo", placeholder="nombre@ejemplo.com", validate=v.validate_email,
        normalize=lambda x: x.strip().lower(), request="request_email_otp", verify="verify_email_otp",
    ),
    "mobile": dict(
        title="Celular", status_key="mobileStatus", active="ACTIVE_MOVIL",
        input_label="Celular (+51)", placeholder="987654321", validate=v.validate_mobile,
        normalize=lambda x: x.strip(), request="request_mobile_otp", verify="verify_mobile_otp",
    ),
}


@st.fragment(run_every=1)
def otp_countdown(channel: str) -> None:
    """Temporizador en vivo (vigencia 60 s / reenvío 45 s). Fuerza un rerun al cruzar cada umbral
    para habilitar/deshabilitar los botones."""
    o = st.session_state.otp.get(channel)
    if not o:
        return
    now = time.time()
    left_exp, left_resend = o["expires_at"] - now, o["resend_at"] - now
    if left_exp > 0:
        st.progress(max(0.0, min(1.0, left_exp / o["ttl"])), text=f"El código vence en {int(left_exp) + 1} s")
    else:
        st.caption("⌛ El código venció. Solicita uno nuevo.")
    if left_resend > 0:
        st.caption(f"Podrás pedir otro código en {int(left_resend) + 1} s")
    if (left_resend <= 0 and not o["notified_resend"]) or (left_exp <= 0 and not o["notified_exp"]):
        o["notified_resend"] = left_resend <= 0
        o["notified_exp"] = left_exp <= 0
        st.rerun()


def otp_section(account_id: str, channel: str, profile: dict) -> None:
    cfg = OTP_CHANNELS[channel]
    st.markdown(f"#### {cfg['title']}")
    if profile.get(cfg["status_key"]) == cfg["active"]:
        st.success(f"{cfg['title']} verificado ✅")
        return

    value = st.text_input(cfg["input_label"], key=f"{channel}_in", placeholder=cfg["placeholder"])
    o = st.session_state.otp.get(channel)
    can_resend = (o is None) or time.time() >= o["resend_at"]

    if st.button("Enviar código", key=f"{channel}_send", disabled=not can_resend):
        err = cfg["validate"](value)
        if err:
            st.error(err)
        else:
            api = getattr(client(), cfg["request"])
            try:
                res = api(account_id, cfg["normalize"](value))
            except ApiError as exc:
                show_error(exc)
                if exc.code == "OTP_TOO_SOON" and exc.retry_after:
                    now = time.time()
                    prev = st.session_state.otp.get(channel) or {"expires_at": now, "ttl": 60}
                    prev.update(resend_at=now + exc.retry_after, notified_resend=False)
                    prev.setdefault("notified_exp", True)
                    st.session_state.otp[channel] = prev
            else:
                now = time.time()  # reloj local: evita desfases con el reloj del servidor
                st.session_state.otp[channel] = {
                    "ttl": res["expiresInSeconds"],
                    "expires_at": now + res["expiresInSeconds"],
                    "resend_at": now + res["resendAfterSeconds"],
                    "notified_resend": False,
                    "notified_exp": False,
                }
                st.success("Código enviado. Revísalo e ingrésalo abajo.")
                st.rerun()

    if o:
        otp_countdown(channel)
        code = st.text_input("Código de 6 dígitos", key=f"{channel}_code", max_chars=6)
        if st.button("Verificar", key=f"{channel}_verify", type="primary"):
            err = v.validate_otp(code)
            if err:
                st.error(err)
            else:
                ok, res = safe(getattr(client(), cfg["verify"]), account_id, code.strip())
                if ok:
                    st.session_state.otp.pop(channel, None)
                    st.session_state.summary_dirty = True
                    flash("success", f"{cfg['title']} verificado correctamente ✅")
                    st.rerun()
                elif res.code == "OTP_EXPIRED":
                    st.session_state.otp[channel]["expires_at"] = time.time()
        st.caption("Ambiente de desarrollo: el OTP mock se escribe en el log del backend ([OTP-MOCK]) "
                   "o es fijo si `WALLET_OTP_FIXED_CODE` está definido.")


# ---- Consentimiento y biometría mock ---------------------------------------
def biometric_section(account_id: str, summary: dict) -> None:
    st.markdown("#### Verificación de identidad")
    if summary["profile"].get("biometricStatus") == "ACTIVE_BIOM":
        st.success("Identidad verificada ✅ — ya cuentas con límites ampliados.")
        return
    st.caption("Simulación de validación biométrica (solo ambientes de desarrollo/test).")

    if not st.session_state.consent_done:
        terms = st.text_input("Versión de términos", value="2026-10", max_chars=20, key="terms_version")
        accepted = st.checkbox("Acepto los términos y condiciones y el manejo de mis datos personales.",
                               key="accept_terms")
        if st.button("Guardar mi consentimiento", disabled=not (accepted and terms.strip())):
            ok, _ = safe(client().accept_consent, account_id, terms.strip())
            if ok:
                st.session_state.consent_done = True
                st.rerun()
        return

    st.success("Consentimiento registrado ✔")
    dni = st.text_input("DNI", key="dni_in", max_chars=8, placeholder="12345678")
    if st.button("Validar mi identidad", type="primary"):
        err = v.validate_dni(dni)
        if err:
            st.error(err)
            return
        with st.spinner("Validando…"):
            ok, res = safe(client().mock_biometric, account_id, dni.strip())
        if ok:
            st.session_state.summary_dirty = True
            flash("success", "🎉 ¡Identidad verificada! Tu cuenta ahora es ACTIVE_FULL.")
            st.rerun()
        elif res.code == "CONSENT_REQUIRED":
            st.session_state.consent_done = False
        elif res.code == "ALREADY_ACTIVE_FULL":
            st.session_state.summary_dirty = True


def render_landing() -> None:
    account_id = st.session_state.account["accountId"]
    if not load_summary():
        return
    summary = st.session_state.summary

    # CA-01/CA-03: la landing ya es visible -> se cierra la medición (una sola vez).
    if not st.session_state.landing_reported:
        st.session_state.landing_reported = True
        report_step("LANDING_VISIBLE")

    render_summary(summary)
    st.divider()
    st.subheader("Completa tu perfil")
    tab_mail, tab_mobile, tab_bio = st.tabs(["📧 Correo", "📱 Celular", "🪪 Identidad"])
    with tab_mail:
        otp_section(account_id, "email", summary["profile"])
    with tab_mobile:
        otp_section(account_id, "mobile", summary["profile"])
    with tab_bio:
        biometric_section(account_id, summary)


# ------------------------------------------------------------------ enrutador
{"personal": render_personal, "credentials": render_credentials, "landing": render_landing}[
    st.session_state.stage
]()
```

---

## `smoke_test.py`

```python
"""Verificación end-to-end por consola del cliente contra el backend real.

Requisitos: backend en ejecución con WALLET_ENV=development y (opcional) WALLET_OTP_FIXED_CODE=123456.
Uso:  WALLET_API_URL=http://localhost:8000 WALLET_OTP_FIXED_CODE=123456 python smoke_test.py
"""
from __future__ import annotations

import os
import secrets
import sys

from api_client import DEFAULT_BASE_URL, ApiError, WalletApiClient

OTP = os.getenv("WALLET_OTP_FIXED_CODE", "123456")


def step(title: str) -> None:
    print(f"▶ {title}")


def main() -> int:
    api = WalletApiClient(DEFAULT_BASE_URL, token="smoke-token")
    if not api.ping():
        print(f"✘ Sin respuesta de {DEFAULT_BASE_URL}")
        return 1

    step("Inicia sesión de onboarding")
    sid = api.start_session()["sessionId"]
    api.register_step(sid, "PERSONAL_DATA_COMPLETED")

    username = f"u{secrets.token_hex(4)}"
    step(f"Disponibilidad de '{username}'")
    assert api.check_username(username, "Ana", "Quispe", "Rojas")["available"] is True

    api.register_step(sid, "CREDENTIALS_COMPLETED")
    step("Crea cuenta")
    acc = api.create_account({
        "firstNames": "Ana María", "paternalSurname": "Quispe", "maternalSurname": "Rojas",
        "username": username, "password": "S3cret!pass", "onboardingSessionId": sid,
    })
    assert acc["status"] == "ACTIVE_BASIC" and acc["balanceCents"] == 0
    aid = acc["accountId"]

    step("Usuario duplicado → 409 con sugerencias")
    try:
        api.create_account({"firstNames": "Ana", "paternalSurname": "Quispe", "maternalSurname": "Rojas",
                            "username": username, "password": "S3cret!pass"})
        raise SystemExit("✘ Se esperaba USERNAME_TAKEN")
    except ApiError as exc:
        assert exc.code == "USERNAME_TAKEN" and exc.suggestions

    step("Landing (getAccount)")
    summary = api.get_account(aid)
    assert summary["profilePending"] is True

    step("OTP correo")
    otp = api.request_email_otp(aid, f"{username}@example.com")
    assert otp["expiresInSeconds"] == 60 and otp["resendAfterSeconds"] == 45
    try:
        api.request_email_otp(aid, f"{username}@example.com")
        raise SystemExit("✘ Se esperaba OTP_TOO_SOON")
    except ApiError as exc:
        assert exc.code == "OTP_TOO_SOON" and exc.retry_after
    assert api.verify_email_otp(aid, OTP)["emailStatus"] == "ACTIVE_EMAIL"

    step("OTP celular")
    api.request_mobile_otp(aid, "987654321")
    assert api.verify_mobile_otp(aid, OTP)["mobileStatus"] == "ACTIVE_MOVIL"

    step("Consentimiento + biometría mock")
    api.accept_consent(aid, "2026-10")
    res = api.mock_biometric(aid, "12345678")
    assert res["status"] == "ACTIVE_FULL"

    api.register_step(sid, "LANDING_VISIBLE")
    print("✔ Flujo completo OK")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except ApiError as exc:
        print(f"✘ {exc.code} (HTTP {exc.status}) traceId={exc.trace_id}: {exc.message}")
        sys.exit(1)
```

---

## `README.md`

````markdown
# Wallet Frontend – HU 01 Onboarding (Streamlit)

Cliente web que consume la API FastAPI del backend (`/v1`).

## Ejecutar
```bash
# 1) Backend (en otra terminal, carpeta wallet-api). Puerto 8000 por defecto en este cliente:
WALLET_ENV=development WALLET_OTP_FIXED_CODE=123456 \
  uvicorn app.main:get_app --factory --port 8000

# 2) Frontend
pip install -r requirements.txt
streamlit run app.py

# 3) (opcional) prueba end-to-end por consola
WALLET_API_URL=http://localhost:8000 WALLET_OTP_FIXED_CODE=123456 python smoke_test.py
```
Si el backend corre en otro puerto (el README del backend usa 8080), cambia la URL en la barra lateral
o define `WALLET_API_URL`. No hay problemas de CORS: Streamlit llama a la API desde el servidor.

## Cobertura de endpoints
| Pantalla / acción | Endpoint |
|---|---|
| Inicio del flujo (CA-01) | `POST /v1/onboarding/sessions` |
| Pasos completados (CA-01, CA-03) | `POST /v1/onboarding/sessions/{id}/steps` |
| Usuario disponible + sugerencias (CA-02) | `GET /v1/usernames/availability` |
| Crear cuenta básica (CA-02/03) | `POST /v1/accounts` |
| Landing: saldo, límites, uso diario, perfil pendiente (CA-03..06, 13) | `GET /v1/accounts/{id}` (Bearer) |
| OTP correo / celular, vigencia 60 s y reenvío 45 s (CA-06..08) | `POST /accounts/{id}/email|mobile/otp` y `/otp/verification` |
| Consentimiento (CA-10) | `POST /v1/accounts/{id}/consents` |
| Biometría mock → ACTIVE_FULL (CA-09, 12) | `POST /v1/accounts/{id}/biometric/mock-verification` |

## Decisiones de UX
- Validación inmediata en cliente (espejo del contrato) y disponibilidad de usuario al presionar Enter; sugerencias con un clic.
- Estados del pago/cuenta visibles: ⏳ pendiente / ✅ verificado, barra de uso diario vs. tope, banner `profilePendingMessage`.
- Temporizadores OTP en vivo (`st.fragment`); el botón “Enviar código” se habilita a los 45 s; 429 usa `Retry-After`.
- Errores del backend traducidos a mensajes claros, con `code`, HTTP y `traceId` para soporte.
- 502/504 del KYC: los datos se conservan y se puede reintentar manualmente. Los POST no se reintentan automáticamente porque el KYC crea un wallet externo.
- La medición de onboarding es best-effort: si falla, nunca bloquea al usuario. `LANDING_VISIBLE` se envía una sola vez (la sesión se cierra y un segundo envío daría 409).
- Privacidad: la contraseña nunca se guarda en `session_state` ni en la URL ni en logs; solo viaja en el `POST /accounts`. En la URL solo se guarda `accountId` para recuperar la landing al recargar.

## Supuestos
1. `bearerAuth` es opaco: el token de la barra lateral (por defecto `dev-token`) solo debe estar bien formado.
2. Los OTP son mock: se leen en el log del backend (`[OTP-MOCK]`) o son fijos con `WALLET_OTP_FIXED_CODE`.
3. La biometría solo existe en `development`/`dev`/`test`; en producción el backend responde `404 MOCK_NOT_AVAILABLE` y la UI lo informa.
4. Los importes llegan en céntimos de PEN y se muestran como `S/ x.xx`.
````