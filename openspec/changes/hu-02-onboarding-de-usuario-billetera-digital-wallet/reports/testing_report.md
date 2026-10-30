# Entrega de pruebas HU 02: Onboarding de billetera digital (Wallet)

Esta entrega contiene `testing_report.md`, los archivos de prueba (pytest + httpx para API, Selenium para UI y E2E), los comandos de preparación, ejecución y limpieza, y los datos sintéticos.

**Estado global: todas las pruebas están en NO EJECUTADO.** En esta tarea no se ejecutó ninguna herramienta, así que no existe salida real de las pruebas aquí diseñadas. La única evidencia numérica disponible es el informe del agente Backend (101 pruebas pasadas en su propia suite `tests/`). Está registrada como evidencia reportada por terceros y no verificada por QA.

## Contenido de la entrega

```
qa/
├── testing_report.md
├── pytest.ini
├── requirements-qa.txt
├── conftest.py
├── helpers.py
├── ui_helpers.py
├── api/
│   ├── conftest.py
│   ├── test_onboarding_api.py
│   ├── test_profile_api.py
│   ├── test_identity_api.py
│   ├── test_operations_api.py
│   └── test_access_privacy_contract_api.py
└── ui/
    ├── conftest.py
    ├── test_onboarding_ui.py
    └── test_profile_e2e.py
```

Se creó la carpeta `qa/` al lado de `backend/` y del frontend. Así se evita interferir con `tests/conftest.py` y con `pytest.ini` del backend, cuyo contenido no se recibió. La ubicación exacta de `qa/` y del frontend dentro del espacio de trabajo queda por confirmar.

---

## `qa/testing_report.md`

````markdown
# Informe de pruebas: HU 02 Onboarding de usuario billetera digital (Wallet)

- Fecha de elaboración: 2026-10-30 (America/Lima)
- Autor: Ingeniería de pruebas (QA automatizado)
- Artefactos de entrada: historia HU 02 y sus aclaraciones, OpenSpec, arquitectura y contrato OpenAPI local, informe del Backend, informe del Frontend.
- **Estado global: NO EJECUTADO.** No se ejecutó ninguna herramienta en esta tarea. Toda la sección "Resultado esperado" es un diseño, no un resultado observado.

---

## 1. Separación entre resultados observados y esperados

### 1.1 Resultados observados (con salida real)

| Origen | Observación | Verificado por QA |
|---|---|---|
| Informe del agente Backend | `pytest` sobre `backend/tests/` terminó con `101 passed, 1 warning in 1.59s` (warning de deprecación anyio/starlette). | **No.** Es evidencia de terceros sobre otra suite (`tests/`). No corresponde a las pruebas de `qa/`. |
| Informe del agente Backend | `ruff` reportó 65 hallazgos de estilo (informativo). | No aplica a QA. |
| Informe del agente Frontend | "No pude ejecutar `ng test` ni `ng build`": el código no está compilado ni probado. | Sin evidencia de ejecución. |

**Resultados observados de las pruebas de `qa/`: ninguno.**

### 1.2 Resultados esperados
Se detallan en la sección 7 (matriz de trazabilidad). Todos figuran como **NO EJECUTADO**.

---

## 2. Alcance y supuestos de diseño de las pruebas

- **API (FastAPI):** caja negra por HTTP real con `pytest` + `httpx` contra un servidor ya levantado (`API_BASE_URL`). Se basa en el contrato OpenAPI del Arquitecto. No se mockea nada del lado del servidor.
- **UI/E2E (Angular):** `Selenium` con Python y Chrome. Los selectores salen del código fuente del frontend (`id` y `data-testid`). La UI llama a `/api/...` y `proxy.conf.json` reescribe a `http://localhost:8000`.
- **Integración UI↔API:** tras acciones en la UI, se consulta la API con `httpx` y credenciales Basic (`GET /wallets/{id}`) para comprobar la persistencia observable.
- **Datos:** sintéticos y únicos por ejecución (prefijo `qa`, UUID), para no requerir limpieza previa.
- **Tiempos reales:** las pruebas de 45 s y 60 s del OTP usan esperas reales y llevan el marcador `slow`.
- **Sin dependencia de tokens:** la autenticación es HTTP Basic (la generación de token está fuera de alcance).

### Decisiones tomadas por brechas de especificación
| Brecha | Decisión en las pruebas |
|---|---|
| Contrato `openapi/wallet-onboarding-api.yaml` sin verificar (el Backend no confirmó que exista) | `API-SEC-07` compara contra `GET /openapi.json` generado por FastAPI y se omite (skip) si no está expuesto. |
| Código de error exacto para correo/celular inválido (`INVALID_*_FORMAT` o `VALIDATION_ERROR`) | Se acepta cualquiera de los dos con HTTP 422. |
| Precedencia entre 409 `ALREADY_VALIDATED` y 429 al repetir la solicitud justo tras validar | `API-OTP-09` espera 409 según el contrato. Si falla con 429, es una brecha de especificación y no un defecto confirmado. |
| El mock acepta cualquier OTP, y el OTP no se devuelve | La invalidación de OTP anteriores no es observable por API (ver pendientes P-03). |
| Nombres `ACTIVE_MOVIL` / `ACTIVE_BIOM` (supuesto S1 del Arquitecto, sin confirmar) | Las pruebas los usan como en el contrato. Si se renombran, deben actualizarse. |
| `balance` no se modifica en esta entrega (supuesto S5) | `API-OPS-12` verifica que sigue en 0. Depende del supuesto. |

---

## 3. Requisitos previos

| Requisito | Detalle |
|---|---|
| Python | 3.11 o superior (el backend se ejecutó con Python 3.13 según su salida). |
| Navegador | Google Chrome instalado (Selenium Manager de Selenium ≥ 4.6 resuelve el chromedriver; requiere acceso a red la primera vez). |
| Node/Angular | Los necesarios para `npm install` y `npm start` del frontend (Angular 18). |
| Backend | Código en `backend/` (`app/main.py`). **Comando de arranque no documentado en los artefactos.** Se asume `uvicorn app.main:app` (a confirmar). |
| `tzdata` | Necesario en Windows para `zoneinfo` (`America/Lima`). Incluido en `requirements-qa.txt`. |
| Frontend | `ng serve` con proxy a `http://localhost:8000`. El puerto 4200 es el predeterminado de Angular y no está fijado en `angular.json` (supuesto). |

### Variables de entorno de las pruebas

| Variable | Predeterminado | Uso |
|---|---|---|
| `API_BASE_URL` | `http://localhost:8000` | URL del backend. |
| `UI_BASE_URL` | `http://localhost:4200` | URL del frontend. |
| `MOCK_BIOMETRIC_ENABLED` | `true` | `true` si el backend corre con `APP_ENV=development` o `testing`; `false` si corre con otro valor. Activa o salta las pruebas de biometría mock habilitada o deshabilitada. |
| `API_LOG_FILE` | (sin definir) | Ruta del archivo donde se redirige la salida del backend. Si no existe, `API-SEC-06` se omite. |
| `BACKEND_DIR` | (sin definir) | Ruta a `backend/` para `API-SEC-08` (documento CA-11). Si no existe, se omite. |
| `HEADLESS` | `true` | `false` para ver Chrome. |
| `UI_WAIT_SECONDS` | `10` | Espera explícita de Selenium. |

Variables del backend (no las define QA): `APP_ENV` (mencionada en el contrato). El nombre de la variable de ruta de la base de datos **no consta** en los artefactos recibidos. Debe revisarse en `app/config.py`.

---

## 4. Datos de prueba sintéticos

| Dato | Valor / generación |
|---|---|
| Contraseña | `Clave#Segura2026` (16 caracteres, ASCII imprimible, sin espacios) |
| Nombres | `María José` (con espacio entre letras y tilde) |
| Apellido paterno / materno | `Quispe` / `Rojas` |
| Usuario | `qa` + hex de UUID (largo 12 por defecto, 20 en el borde). Único por prueba. |
| Correo | `qa.<12 hex>@example.com`. Único por prueba. |
| Celular | `9` + 8 dígitos aleatorios (9 dígitos, inicia con 9). Colisión posible pero improbable. |
| OTP | `000000`, `abcdef`, `1` (el mock confirma cualquier valor no vacío mientras haya OTP vigente) |
| Montos | `20.00`, `20.01`, `60.00`, `500.00`, `500.01`, `1000.00`, `0.01` |

No se usan datos personales reales, fotos de DNI ni videos.

---

## 5. Comandos exactos

Se muestra PowerShell (el espacio de trabajo del Backend es Windows). En bash se reemplaza la activación por `source .venv/bin/activate`.

### 5.1 Preparar
```powershell
# 1) Entorno de pruebas
cd <ruta>\qa
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements-qa.txt

# 2) Backend (ambiente que habilita la biometría mock)
cd <ruta>\code\backend
$env:APP_ENV = "testing"
#   Comando de arranque ASUMIDO (no documentado). Confirmar con el equipo de Backend:
cmd /c "uvicorn app.main:app --host 127.0.0.1 --port 8000 > ..\qa\api.log 2>&1"
#   (dejar esta terminal abierta)

# 3) Frontend (otra terminal)
cd <ruta>\<carpeta-wallet-frontend>
npm install
npm start          # ng serve --proxy-config proxy.conf.json  (UI en http://localhost:4200, supuesto)
```

### 5.2 Ejecutar
```powershell
cd <ruta>\qa
.\.venv\Scripts\Activate.ps1
New-Item -ItemType Directory -Force results | Out-Null

# API: pruebas rápidas
$env:API_BASE_URL = "http://localhost:8000"
$env:MOCK_BIOMETRIC_ENABLED = "true"
$env:API_LOG_FILE = "$PWD\api.log"
$env:BACKEND_DIR  = "<ruta>\code\backend"
pytest api -m "not slow" -v --junitxml=results\api-fast.xml

# API: pruebas lentas (esperas reales de 44-46 s y 61 s; varios minutos)
pytest api -m slow -v --junitxml=results\api-slow.xml

# UI / E2E (backend y frontend levantados)
$env:UI_BASE_URL = "http://localhost:4200"
pytest ui -m "not slow" -v --junitxml=results\ui-fast.xml
pytest ui -m slow -v --junitxml=results\ui-slow.xml

# Ver el navegador
$env:HEADLESS = "false"; pytest ui -m "not slow" -v

# Caso "ambiente distinto de development/testing" (API)
#   Reiniciar el backend con otro APP_ENV (valor aceptado por la config: a confirmar) y ejecutar:
$env:APP_ENV = "production"      # en la terminal del backend, y reiniciar uvicorn
$env:MOCK_BIOMETRIC_ENABLED = "false"
pytest api/test_identity_api.py -k "disabled" -v
#   Para UI-E2E-11 el frontend usa proxy fijo a :8000, por lo que el backend debe reiniciarse en :8000:
pytest ui/test_profile_e2e.py -k "ui_e2e_11" -v
```

### 5.3 Limpiar
```powershell
# 1) Detener frontend y backend (Ctrl+C en cada terminal)
# 2) Datos creados en la BD temporal: no existe API de borrado.
#    - Si el backend usa :memory: -> se eliminan al detener el proceso.
#    - Si usa archivo (la arquitectura menciona wallet.db; la ruta real está PENDIENTE de confirmar en app/config.py):
Remove-Item <ruta-real-de-wallet.db> -ErrorAction SilentlyContinue
# 3) Artefactos de pruebas
cd <ruta>\qa
Remove-Item -Recurse -Force results, api.log, .pytest_cache, .venv -ErrorAction SilentlyContinue
Get-ChildItem -Recurse -Filter __pycache__ | Remove-Item -Recurse -Force
```
Todos los usuarios creados tienen el prefijo `qa` (con `@example.com` en los correos).

---

## 6. Convenciones de la matriz

- **Tipo:** API (pytest + httpx), UI (Selenium), E2E (Selenium + verificación por API), INT (integración UI↔API), EST (verificación estática de archivo).
- **Estado:** `NO EJECUTADO` para todas. `PENDIENTE` significa que la prueba no pudo automatizarse y se explica qué falta.
- Archivo de cada prueba: `api/test_onboarding_api.py` (ONB/USR/REG), `api/test_profile_api.py` (OTP/EML/PHN/PRF), `api/test_identity_api.py` (IDN), `api/test_operations_api.py` (OPS), `api/test_access_privacy_contract_api.py` (SEC), `ui/test_onboarding_ui.py` (UI-ONB), `ui/test_profile_e2e.py` (UI-E2E).
- Parametrizaciones `[email|phone]`, `[PAYMENT|TOPUP_OWN]`, etc. generan un caso por valor.

---

## 7. Matriz de trazabilidad y resultados esperados

### CA-01 Inicio y seguimiento

| ID | Tipo | Resultado esperado | Estado |
|---|---|---|---|
| API-ONB-01 | API | `POST /onboarding/sessions` → 201 con `session_id` UUID y `started_at`. | NO EJECUTADO |
| API-ONB-02 | API | `POST /onboarding/sessions/{id}/steps` con `{"step":"NOMBRES"}` → 201 con `step` y `elapsed_ms` entero ≥ 0. | NO EJECUTADO |
| API-ONB-03 | API | Paso fuera del enum → 422 `VALIDATION_ERROR`. | NO EJECUTADO |
| API-ONB-04 | API | Sesión inexistente → 404 `NOT_FOUND`. | NO EJECUTADO |
| API-REG-06 | API | Registro con `session_id` → `registration_duration_ms` entero ≥ 0. Después, un paso en esa sesión → 409 `SESSION_CLOSED`. | NO EJECUTADO |
| API-REG-07 | API | Registro sin `session_id` → 201 y duración nula. | NO EJECUTADO |
| API-REG-08 | API | Registro con `session_id` inexistente → 404. | NO EJECUTADO |
| UI-ONB-01 | UI | Al mostrarse la pantalla, el navegador invoca `/onboarding/sessions` y se muestra "Pasos completados: 0". | NO EJECUTADO |
| UI-ONB-02 | UI | Al salir de un campo válido, el progreso pasa a "Pasos completados: 1" y se invoca `/steps`. | NO EJECUTADO |
| UI-ONB-03 | UI | Validación en línea: cada campo muestra `data-state` y mensaje mientras se escribe (casos de CA-02). | NO EJECUTADO |
| UI-ONB-11 | UI | El indicador de progreso muestra "de 5" y no texto literal (`${` o `{{`). Detecta si se aplicó la corrección pendiente del template. | NO EJECUTADO |
| P-01 | — | Medición "inicia cuando la pantalla es visible" y "termina al concluir la respuesta": solo hay evidencia indirecta (`started_at` y duración). El valor del tiempo no es comparable sin reloj controlado. | PENDIENTE |

### CA-02 Datos de registro

| ID | Tipo | Resultado esperado | Estado |
|---|---|---|---|
| API-REG-02 | API | Bordes válidos: nombres 30, apellidos 20, usuario 20, contraseña 10 (con y sin símbolo) → 201. | NO EJECUTADO |
| API-REG-03 | API | Inválidos (dígitos en nombres, 31 y 21 caracteres, doble espacio, usuario de 21, usuario sin letra o con espacio, contraseña de 9) → 422 `VALIDATION_ERROR`, sin eco del valor ni de la contraseña. | NO EJECUTADO |
| API-REG-04 | API | Falta un campo obligatorio → 422. | NO EJECUTADO |
| API-USR-01 | API | Usuario nuevo → 200 `AVAILABLE`, `suggestions=[]`. | NO EJECUTADO |
| API-USR-02 | API | Formato inválido (sin letra, 21 caracteres) → 200 `INVALID_FORMAT`. | NO EJECUTADO |
| API-USR-03 | API | Usuario ocupado → 200 `TAKEN`, sugerencias no vacías, todas `^[a-z0-9]{1,20}$` y todas `AVAILABLE` al consultarlas. | NO EJECUTADO |
| API-USR-04 | API | Unicidad sin distinguir mayúsculas → `TAKEN`. | NO EJECUTADO |
| API-REG-05 | API | Registro con usuario ocupado (también variante en mayúsculas) → 409 `USERNAME_TAKEN` con sugerencias válidas. | NO EJECUTADO |
| UI-ONB-03 | UI | Nombres `María José` válido; `Maria123`, 31 caracteres → inválido (mensaje "Solo letras" / "Máximo 30"). Apellidos: `Quispe` válido; `Quispe9`, 21 caracteres → inválido. Usuario `12345` y 21 caracteres → inválido. Contraseña de 9 → "Mínimo 10". | NO EJECUTADO |
| UI-ONB-04 | UI | Alerta de robustez: `abc` → "débil" con `role=alert`; `Clave#Segura2026` → "fuerte". | NO EJECUTADO |
| UI-ONB-05 | UI | Usuario libre → estado válido y "Usuario disponible."; el botón "Crear cuenta" permanece deshabilitado hasta completar el formulario. | NO EJECUTADO |
| UI-ONB-06 | UI | Usuario ocupado → chips de sugerencias sin símbolos; al elegir una queda disponible y con el valor del chip. | NO EJECUTADO |
| P-02 | — | "Sugerencias basadas en nombres, apellidos y números": la prueba verifica formato y disponibilidad y las imprime. Que deriven de los nombres requiere revisión humana (algoritmo no especificado). | PENDIENTE (revisión manual) |
| API-SEC-06 | API | La contraseña no aparece en logs del backend (si hay `API_LOG_FILE`). | NO EJECUTADO |
| UI-ONB-09 | UI | Tras registrarse, `localStorage`, `sessionStorage`, cookies y consola del navegador no contienen la contraseña. | NO EJECUTADO |

### CA-03 Creación de cuenta básica / CA-04 Aviso de perfil pendiente

| ID | Tipo | Resultado esperado | Estado |
|---|---|---|---|
| API-REG-01 | API | 201: `wallet_id` UUID válido, `ACTIVE_BASIC`, saldo 0, `PEN`; `welcome.display_name` = nombres; perfil con tres `PENDING_*`; condiciones BASIC (COMBINED, 20 / 60, `America/Lima`); la contraseña no figura en la respuesta. | NO EJECUTADO |
| API-REG-09 | API | `GET /wallets/{id}` con Basic → 200 coherente con el registro. | NO EJECUTADO |
| UI-ONB-08 | E2E | Registro por UI → ruta `/landing`, bienvenida con "María José", "Cuenta básica", saldo "S/ 0.00", wallet_id UUID, condiciones con "S/ 20.00" y "S/ 60.00", banner visible de perfil pendiente con enlace al perfil. | NO EJECUTADO |
| UI-ONB-10 | INT | Tras el registro por UI, `GET /wallets/{id}` con las credenciales → 200 `ACTIVE_BASIC`, saldo 0. | NO EJECUTADO |
| UI-ONB-07 | UI | Botón de envío deshabilitado al inicio. | NO EJECUTADO |

### CA-05 Operaciones ACTIVE_BASIC

| ID | Tipo | Resultado esperado | Estado |
|---|---|---|---|
| API-OPS-01[PAYMENT\|TOPUP_OWN] | API | Operación de S/20.00 → 201 con `operation_id` UUID, `operation_day` = hoy en Lima, acumulado 20.00, `daily_max` 60.00. | NO EJECUTADO |
| API-OPS-02[PAYMENT\|TOPUP_OWN] | API | S/20.01 → 422 `PER_OPERATION_LIMIT_EXCEEDED`. | NO EJECUTADO |
| API-OPS-03 | API | `TOPUP_THIRD_PARTY` en BASIC → 422 `OPERATION_NOT_ALLOWED`. | NO EJECUTADO |
| API-OPS-04 | API | 20+20+20 aceptadas (acumulado 20, 40, 60). Con 1.00 más → 422 `DAILY_LIMIT_EXCEEDED`. | NO EJECUTADO |
| API-OPS-05 | API | Acumulado 50 y operación 10.01 → 422 `DAILY_LIMIT_EXCEEDED`. Luego 10.00 → 201 (acumulado 60): lo rechazado no acumula. | NO EJECUTADO |
| API-OPS-06 | API | Recargas 20+20 y pago 20 aceptados (60); pago de 1.00 rechazado (acumulado combinado). | NO EJECUTADO |
| API-OPS-07 | API | Rechazos (20.01 o tercero) no acumulan: luego 20.00 → acumulado 20.00. | NO EJECUTADO |
| API-OPS-08 | API | Montos `0`, `0.00`, `-5`, `abc`, `20.001`, vacío → 422 `VALIDATION_ERROR`. | NO EJECUTADO |
| API-OPS-09 | API | `operation_type` inválido → 422. | NO EJECUTADO |
| API-OPS-10 | API | Condiciones BASIC en `GET /wallets/{id}`: COMBINED, tipos {TOPUP_OWN, PAYMENT}, 20.00 / 60.00, `America/Lima`. | NO EJECUTADO |
| API-OPS-12 | API | El saldo sigue en 0 tras operaciones aceptadas (supuesto S5). | NO EJECUTADO |
| UI-E2E-09 | E2E | Panel de operaciones en BASIC: solo 2 tipos; 20.00 aceptada; 20.01 muestra "tope por operación"; acumulado hasta 60.00 y luego "tope diario". | NO EJECUTADO |
| API-OPS-31 | — | Topes parametrizables (cambiar `limit_parameters` y observar el efecto sin cambiar código): no existe API de administración ni ruta/nombre de BD confirmados. | PENDIENTE |
| API-OPS-30 | — | Reinicio del contador al cambiar de día en Lima: el reloj es inyectable solo dentro del proceso del backend, no por HTTP. El Backend declara haberlo probado (23:59:59 / 00:00:00) en `tests/test_operations.py`, sin verificación de QA. Requiere reloj controlable en un entorno de pruebas o ejecutar el servidor con la hora simulada. | PENDIENTE |

### CA-06 Registro complementario

| ID | Tipo | Resultado esperado | Estado |
|---|---|---|---|
| API-PRF-01 | API | Tras el registro: `PENDING_EMAIL`, `PENDING_MOVIL`, `PENDING_BIOM`. | NO EJECUTADO |
| API-PRF-02 | API | Validar celular antes que correo: cada estado cambia de forma independiente, C3 no cambia. | NO EJECUTADO |
| UI-E2E-01 | E2E | Desde la landing, el enlace lleva al perfil con 3 tarjetas, "Cuenta básica" y badges "Pendiente". | NO EJECUTADO |
| UI-E2E-04 | E2E+INT | Celular primero y luego correo desde la UI; tras cada paso, la otra tarjeta sigue "Pendiente". Verificación final por API. | NO EJECUTADO |

### CA-07 Validación de correo / CA-08 Validación de celular

| ID | Tipo | Resultado esperado | Estado |
|---|---|---|---|
| API-OTP-01[email\|phone] | API | Solicitud válida → 201: `channel`, `expires_in_seconds=60`, `otp_length=6`, `delivery=MOCK_NOT_SENT`, sin campo de código; `expires_at − next_request_allowed_at ≈ 15 s`; estado del perfil sin cambio. | NO EJECUTADO |
| API-EML-01 | API | `ana@@example` y otros formatos inválidos → 422 (`INVALID_EMAIL_FORMAT` o `VALIDATION_ERROR`). | NO EJECUTADO |
| API-PHN-01 | API | `812345678`, `91234567`, `9123456789`, `abc123456`, `+51912345678` → 422. | NO EJECUTADO |
| API-PHN-02 | API | Prefijo no editable: con `prefix: +52` en el cuerpo, o se ignora (201 con `phone_e164` `+51…`) o se rechaza (422). Nunca +52. | NO EJECUTADO |
| API-PHN-03 | API | `phone_e164` = `+51` + 9 dígitos y cumple `^\+519[0-9]{8}$`. | NO EJECUTADO |
| API-OTP-03[email\|phone] | API | Segunda solicitud inmediata → 429 `OTP_RATE_LIMITED`, cabecera `Retry-After` entre 1 y 45. | NO EJECUTADO |
| API-OTP-04[email\|phone] | API | Confirmar sin OTP emitido → 422 `OTP_NOT_ACTIVE`; el estado no cambia. | NO EJECUTADO |
| API-OTP-05[email\|phone] | API | Confirmar con cualquier valor (`000000`, `abcdef`, `1`) con OTP vigente → 200, estado `ACTIVE_EMAIL` / `ACTIVE_MOVIL`; los otros estados no cambian. | NO EJECUTADO |
| API-OTP-06[email\|phone] | API | OTP vacío → 422 `VALIDATION_ERROR`. | NO EJECUTADO |
| API-OTP-07[email\|phone] | API | Reusar un OTP ya consumido → 422 `OTP_NOT_ACTIVE`. | NO EJECUTADO |
| API-OTP-08[email\|phone] | API | Correo/celular ya validado por otro usuario → 409 `EMAIL_ALREADY_REGISTERED` / `PHONE_ALREADY_REGISTERED` (correo también en mayúsculas). | NO EJECUTADO |
| API-OTP-09[email\|phone] | API | Canal ya validado y nueva solicitud → 409 `ALREADY_VALIDATED` (ver precedencia con 429 en la sección 2). | NO EJECUTADO |
| API-OTP-10[email\|phone] (slow) | API | A los ~44 s → 429; a los ~46 s → 201. | NO EJECUTADO |
| API-OTP-11[email\|phone] (slow) | API | Confirmar a los 61 s → 422 `OTP_EXPIRED`; estado sin cambio. | NO EJECUTADO |
| API-OTP-12[email\|phone] (slow) | API | OTP nuevo a los 46 s sigue vigente cuando el primero ya venció (t = 61 s) → confirmación 200. | NO EJECUTADO |
| UI-E2E-02 | UI | Correo inválido: botón "Enviar código" deshabilitado y mensaje de error; correo válido lo habilita. | NO EJECUTADO |
| UI-E2E-03 | UI | Prefijo "+51" de solo lectura; `812345678` y `91234567` mantienen el botón deshabilitado; `912345678` lo habilita. | NO EJECUTADO |
| UI-E2E-05 | UI | Tras solicitar OTP: nota "no se envía ningún correo/SMS real", botón "Reenviar en N s" deshabilitado, confirmación con cualquier valor valida el canal. | NO EJECUTADO |
| UI-E2E-06 | E2E | Correo ya registrado por otro usuario → mensaje "ya está registrado" y no se emite OTP. | NO EJECUTADO |
| UI-E2E-12 (slow) | UI | Pasados ~46 s el botón de reenvío se habilita. | NO EJECUTADO |
| P-03 | — | "La generación de un OTP nuevo invalida los anteriores": el OTP no se devuelve y el mock acepta cualquier valor, por lo que no es observable por API. Se verifica de forma indirecta con API-OTP-12. La verificación directa requiere acceder a `otp_challenges` (estado `INVALIDATED`; nombres de la arquitectura, sin confirmar contra el código real). | PENDIENTE |
| P-04 | — | "No se envía correo/SMS real / ausencia de llamadas de red": no observable por HTTP. El Backend declara que no hay llamadas salientes. Requiere bloquear la red del proceso o inspección de código. | PENDIENTE |

### CA-09 / CA-12 Biometría mock y ACTIVE_FULL

| ID | Tipo | Resultado esperado | Estado |
|---|---|---|---|
| API-IDN-01 | API | `terms_accepted=false` → 422 `TERMS_NOT_ACCEPTED`; la cuenta sigue en `ACTIVE_BASIC`. | NO EJECUTADO |
| API-IDN-02 | API | `mock_inputs_confirmed=false` → 422 `MOCK_INPUTS_INVALID`. | NO EJECUTADO |
| API-IDN-03 | API | Campos ausentes → 422 `VALIDATION_ERROR`. | NO EJECUTADO |
| API-IDN-04 | API | Éxito sin correo ni celular validados → 200 `ACTIVE_FULL`, C3 `ACTIVE_BIOM`, C1/C2 `PENDING_*`; condiciones FULL en `GET`. | NO EJECUTADO |
| API-IDN-05 | API | Repetir → 409 `ALREADY_ACTIVE_FULL`. | NO EJECUTADO |
| API-IDN-06 | API | Recorrido completo (registro, correo, celular, identidad) → `ACTIVE_FULL` con los tres estados validados. | NO EJECUTADO |
| API-IDN-07 | API | Backend con otro `APP_ENV` (`MOCK_BIOMETRIC_ENABLED=false`): 403 `BIOMETRIC_MOCK_DISABLED` y la cuenta sigue `ACTIVE_BASIC`. | NO EJECUTADO |
| API-IDN-08 | API | `identity_mock_available` = `MOCK_BIOMETRIC_ENABLED`. | NO EJECUTADO |
| UI-E2E-07 | E2E+INT | Aviso de nitidez; botón deshabilitado hasta marcar términos y datos simulados; luego identidad validada y "Cuenta completa" en la UI; por API `ACTIVE_FULL` con C1/C2 `PENDING_*`; tabla de condiciones con "S/ 1,000.00", "S/ 500.00" y "Sin tope". | NO EJECUTADO |
| UI-E2E-08 | E2E+INT | Recorrido completo por UI; por API los tres estados `ACTIVE_*`. | NO EJECUTADO |
| UI-E2E-11 | UI | Con backend en otro ambiente: mensaje "solo disponible en desarrollo y pruebas" y sin botón de validar. | NO EJECUTADO |

### CA-10 Datos personales

| ID | Tipo | Resultado esperado | Estado |
|---|---|---|---|
| API-IDN-01 / API-IDN-04 | API | Sin aceptar términos no se continúa (422). Con aceptación se activa. | NO EJECUTADO |
| API-SEC-01 | API | Sin credenciales, en los 7 endpoints protegidos → 401 `UNAUTHORIZED` (con `WWW-Authenticate` en GET). | NO EJECUTADO |
| API-SEC-02 | API | Contraseña incorrecta o usuario inexistente → 401. | NO EJECUTADO |
| API-SEC-03 | API | Credenciales de A sobre el wallet de B → 403 `FORBIDDEN` en los 7 endpoints. | NO EJECUTADO |
| API-SEC-04 | API | Credenciales válidas sobre wallet inexistente → 404 `NOT_FOUND`. | NO EJECUTADO |
| API-SEC-05 | API | Los 422 no devuelven el correo, el celular ni la contraseña enviados. | NO EJECUTADO |
| API-SEC-06 | API | Tras un flujo completo, el log del backend no contiene contraseña, nombres, apellidos, correo, celular ni el token Basic. Se omite si falta `API_LOG_FILE`. | NO EJECUTADO |
| UI-ONB-09 | UI | Sin credenciales en storage/cookies/consola. | NO EJECUTADO |
| P-05 | — | Datos no enviados a analítica: no hay SDK de analítica según el Arquitecto. No es verificable por prueba funcional más allá de storage y consola. Requiere revisión de dependencias y de tráfico de red. | PENDIENTE |
| P-06 | — | Retención, eliminación y texto/versión de términos y condiciones: fuera de alcance por la historia. | FUERA DE ALCANCE |

### CA-11 Documentos y video (contrato futuro, sin implementación)

| ID | Tipo | Resultado esperado | Estado |
|---|---|---|---|
| UI-E2E-07 | UI | Aviso de que las imágenes deben ser nítidas. | NO EJECUTADO |
| API-SEC-08 | EST | `docs/biometria-real-requisitos.md` existe y menciona 2 MB, 10 MB y 10 minutos (se omite sin `BACKEND_DIR`). | NO EJECUTADO |
| — | — | Validación real de tamaños, duración y metadatos: explícitamente no implementada. No se prueba. | FUERA DE ALCANCE |

### CA-13 Operaciones ACTIVE_FULL

| ID | Tipo | Resultado esperado | Estado |
|---|---|---|---|
| API-OPS-20 | API | Recarga de tercero 1000.00 → 201 (sin tope por operación). Con 0.01 más (tercero o propia) → 422 `DAILY_LIMIT_EXCEEDED`. | NO EJECUTADO |
| API-OPS-21 | API | Pago 500.00 → 201; 500.01 → 422 `PER_OPERATION_LIMIT_EXCEEDED`. | NO EJECUTADO |
| API-OPS-22 | API | Pagos 500+500 aceptados; 0.01 más → 422 `DAILY_LIMIT_EXCEEDED`. | NO EJECUTADO |
| API-OPS-23 | API | Recargas y pagos tienen acumulados separados: tras recargar 1000.00, un pago de 500.00 se acepta. | NO EJECUTADO |
| API-OPS-24 | API | Condiciones FULL: TOPUP (sin tope por operación, 1000.00) y PAYMENT (500.00 / 1000.00). | NO EJECUTADO |
| UI-E2E-10 | E2E | Panel en FULL: 3 tipos; recarga de terceros de 1000.00 aceptada ("S/ 1,000.00"); 0.01 más muestra "tope diario". | NO EJECUTADO |
| API-OPS-30 / 31 | — | Reinicio diario y parametrización (ver CA-05). | PENDIENTE |

### Transversal: conformidad del contrato

| ID | Tipo | Resultado esperado | Estado |
|---|---|---|---|
| API-SEC-07 | API | `GET /openapi.json` contiene los 11 pares método+ruta del contrato (se omite si no está expuesto). | NO EJECUTADO |

---

## 8. Brechas, pendientes y riesgos

| # | Tema | Qué se necesita |
|---|---|---|
| G-01 | Comando de arranque del backend y variable de ruta de la BD | Confirmar con Backend (`app/config.py`, `app/main.py`). Las instrucciones usan un comando asumido. |
| G-02 | Ubicación y puerto del frontend | Ruta de la carpeta `wallet-frontend` y puerto de `ng serve` (4200 supuesto). |
| G-03 | `openapi/wallet-onboarding-api.yaml` no confirmado | Confirmar su existencia. Hasta entonces, la conformidad se verifica solo con `openapi.json`. |
| G-04 | Reinicio diario (CA-05 y CA-13) | Reloj controlable en un entorno de pruebas, o ejecutar `tests/test_operations.py` del Backend y adjuntar la salida. |
| G-05 | Parametrización de topes | Acceso a `limit_parameters` o un endpoint de administración (no existe). |
| G-06 | Invalidación de OTP | Acceso a `otp_challenges` o un OTP observable en ambiente de pruebas. |
| G-07 | Frontend sin compilar | El Frontend no ejecutó `ng build` ni `ng test`. Si la compilación falla, todas las pruebas UI fallarán. Ejecutar antes `npm run build` y `npm run test:ci`. |
| G-08 | Defecto posible en el template de `OnboardingComponent` | La entrega del Frontend indica una corrección pendiente (`de ${'{'}total{'}'}` → `de {{ total }}`). UI-ONB-11 detecta si se aplicó. |
| G-09 | CORS | La UI usa proxy `/api`. Si se sirve sin proxy y el backend no habilita CORS, la UI fallará. |
| G-10 | Valor de `APP_ENV` "otro ambiente" | Confirmar qué valores acepta la configuración (se usa `production`). |
| G-11 | Ejecución cerca de medianoche (Lima) | Los acumulados diarios pueden cruzar de día durante una corrida. Evitar ejecutar entre 23:55 y 00:05. |
| G-12 | Preguntas abiertas del Arquitecto (nombres `ACTIVE_MOVIL` / `ACTIVE_BIOM`, saldo, acumulado entre BASIC y FULL, cambio de correo validado) | Su respuesta puede cambiar los resultados esperados. |
| G-13 | Las esperas de las pruebas `slow` | Duran varios minutos (≈ 46 s + 61 s + 61 s por canal). Se ejecutan en forma serial. |

## 9. Conclusión

Las pruebas están diseñadas y trazadas a CA-01 a CA-13. **Ninguna ha sido ejecutada.** No se puede afirmar que algún criterio esté verificado ni que alguna corrección esté validada. El siguiente paso es ejecutar los comandos de la sección 5 y registrar aquí la salida real, junto con cualquier resultado distinto del esperado.
````

---

## `qa/requirements-qa.txt`

```text
pytest
httpx
selenium
tzdata
```

(Las versiones no están definidas en el proyecto y no se fijan para no inventar configuración.)

## `qa/pytest.ini`

```ini
[pytest]
pythonpath = .
testpaths = api ui
addopts = -ra
markers =
    slow: pruebas con esperas reales (45 s / 60 s de OTP)
    api: pruebas de API (pytest + httpx)
    ui: pruebas de interfaz / E2E (Selenium)
```

## `qa/conftest.py`

```python
"""Conftest raíz: etiqueta automáticamente las pruebas como api o ui según su carpeta."""
import pytest


def pytest_collection_modifyitems(items):
    for item in items:
        if "ui" in item.path.parts:
            item.add_marker(pytest.mark.ui)
        elif "api" in item.path.parts:
            item.add_marker(pytest.mark.api)
```

## `qa/helpers.py`

```python
"""Utilidades compartidas por las pruebas de API y UI. Solo datos sintéticos."""
from __future__ import annotations

import os
import random
import re
import string
import uuid
from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from zoneinfo import ZoneInfo

import httpx
import pytest

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000").rstrip("/")
MOCK_BIOMETRIC_ENABLED = os.getenv("MOCK_BIOMETRIC_ENABLED", "true").strip().lower() == "true"
LIMA = ZoneInfo("America/Lima")

PASSWORD = "Clave#Segura2026"
UUID_RE = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", re.IGNORECASE
)
SUGGESTION_RE = re.compile(r"^[a-z0-9]{1,20}$")

requires_mock = pytest.mark.skipif(
    not MOCK_BIOMETRIC_ENABLED,
    reason="Requiere backend con APP_ENV=development/testing (MOCK_BIOMETRIC_ENABLED=true)",
)
requires_mock_disabled = pytest.mark.skipif(
    MOCK_BIOMETRIC_ENABLED,
    reason="Requiere backend con APP_ENV distinto de development/testing (MOCK_BIOMETRIC_ENABLED=false)",
)


# ---------------------------------------------------------------- datos sintéticos
def unique_username(length: int = 12) -> str:
    """Usuario único: empieza con 'qa' (contiene letras) + hex de UUID."""
    return ("qa" + uuid.uuid4().hex)[:length]


def unique_email() -> str:
    return f"qa.{uuid.uuid4().hex[:12]}@example.com"


def unique_phone() -> str:
    return "9" + "".join(random.choices(string.digits, k=8))


def random_letters(n: int) -> str:
    return "".join(random.choices(string.ascii_lowercase, k=n)).capitalize()


def registration_payload(**overrides) -> dict:
    payload = {
        "nombres": "María José",
        "apellido_paterno": "Quispe",
        "apellido_materno": "Rojas",
        "usuario": unique_username(),
        "password": PASSWORD,
    }
    payload.update(overrides)
    return payload


CHANNELS = {
    "email": {
        "path": "email",
        "field": "email",
        "new": unique_email,
        "state": "estado_c1",
        "pending": "PENDING_EMAIL",
        "active": "ACTIVE_EMAIL",
        "dup_code": "EMAIL_ALREADY_REGISTERED",
    },
    "phone": {
        "path": "phone",
        "field": "phone",
        "new": unique_phone,
        "state": "estado_c2",
        "pending": "PENDING_MOVIL",
        "active": "ACTIVE_MOVIL",
        "dup_code": "PHONE_ALREADY_REGISTERED",
    },
}


# ---------------------------------------------------------------- modelo y llamadas
@dataclass
class Wallet:
    wallet_id: str
    username: str
    password: str
    nombres: str
    registration: dict = field(repr=False, default_factory=dict)

    @property
    def auth(self) -> tuple[str, str]:
        return (self.username, self.password)


def parse_dt(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def money(value: str) -> Decimal:
    return Decimal(value)


def lima_today() -> date:
    return datetime.now(LIMA).date()


def assert_error(response: httpx.Response, status: int, code: str | tuple[str, ...]) -> dict:
    assert response.status_code == status, f"esperado {status}, recibido {response.status_code}"
    body = response.json()
    codes = (code,) if isinstance(code, str) else code
    assert body["code"] in codes, f"código esperado {codes}, recibido {body.get('code')}"
    return body


def register(client: httpx.Client, **overrides) -> Wallet:
    payload = registration_payload(**overrides)
    r = client.post("/onboarding/registrations", json=payload)
    assert r.status_code == 201, f"registro falló con {r.status_code}"
    body = r.json()
    return Wallet(
        wallet_id=body["account"]["wallet_id"],
        username=payload["usuario"],
        password=payload["password"],
        nombres=payload["nombres"],
        registration=body,
    )


def wallet_url(w: Wallet, suffix: str = "") -> str:
    return f"/wallets/{w.wallet_id}{suffix}"


def get_wallet(client: httpx.Client, w: Wallet) -> dict:
    r = client.get(wallet_url(w), auth=w.auth)
    assert r.status_code == 200, f"GET wallet falló con {r.status_code}"
    return r.json()


def otp_request(client, w: Wallet, channel: str, value: str | None = None) -> httpx.Response:
    cfg = CHANNELS[channel]
    value = value or cfg["new"]()
    return client.post(
        wallet_url(w, f"/profile/{cfg['path']}/otp-requests"),
        json={cfg["field"]: value},
        auth=w.auth,
    )


def otp_confirm(client, w: Wallet, channel: str, otp: str = "000000") -> httpx.Response:
    return client.post(
        wallet_url(w, f"/profile/{CHANNELS[channel]['path']}/otp-confirmations"),
        json={"otp": otp},
        auth=w.auth,
    )


def confirm_channel(client, w: Wallet, channel: str, value: str | None = None) -> str:
    """Solicita y confirma el OTP mock. Devuelve el valor (correo/celular) validado."""
    value = value or CHANNELS[channel]["new"]()
    r = otp_request(client, w, channel, value)
    assert r.status_code == 201, f"solicitud OTP falló con {r.status_code}"
    c = otp_confirm(client, w, channel)
    assert c.status_code == 200, f"confirmación OTP falló con {c.status_code}"
    return value


def activate_full(client, w: Wallet) -> dict:
    r = client.post(
        wallet_url(w, "/profile/identity/mock-verification"),
        json={"terms_accepted": True, "mock_inputs_confirmed": True},
        auth=w.auth,
    )
    assert r.status_code == 200, f"biometría mock falló con {r.status_code}"
    return r.json()


def post_op(client, w: Wallet, operation_type: str, amount: str) -> httpx.Response:
    return client.post(
        wallet_url(w, "/operations"),
        json={"operation_type": operation_type, "amount": amount},
        auth=w.auth,
    )
```

## `qa/api/conftest.py`

```python
import httpx
import pytest

from helpers import API_BASE_URL, MOCK_BIOMETRIC_ENABLED, activate_full, register


@pytest.fixture(scope="session")
def client():
    with httpx.Client(base_url=API_BASE_URL, timeout=15.0) as c:
        try:
            c.get("/openapi.json")
        except httpx.TransportError as exc:
            pytest.exit(
                f"API no disponible en {API_BASE_URL} ({type(exc).__name__}). "
                "Levante el backend antes de ejecutar las pruebas.",
                returncode=2,
            )
        yield c


@pytest.fixture
def basic_wallet(client):
    """Cuenta ACTIVE_BASIC nueva, con datos únicos."""
    return register(client)


@pytest.fixture
def full_wallet(client):
    """Cuenta llevada a ACTIVE_FULL por el flujo mock (requiere biometría mock habilitada)."""
    if not MOCK_BIOMETRIC_ENABLED:
        pytest.skip("Biometría mock deshabilitada en este ambiente")
    w = register(client)
    activate_full(client, w)
    return w
```

## `qa/api/test_onboarding_api.py`

```python
"""CA-01, CA-02, CA-03, CA-04: sesión de medición, usuario, registro."""
import uuid
from decimal import Decimal

import pytest

from helpers import (
    PASSWORD,
    SUGGESTION_RE,
    UUID_RE,
    assert_error,
    get_wallet,
    register,
    registration_payload,
    unique_username,
    wallet_url,
)


# ------------------------------------------------------------------ sesión (CA-01)
def test_api_onb_01_start_session(client):
    r = client.post("/onboarding/sessions")
    assert r.status_code == 201
    body = r.json()
    assert UUID_RE.match(body["session_id"])
    assert body["started_at"]


def test_api_onb_02_register_step(client):
    sid = client.post("/onboarding/sessions").json()["session_id"]
    r = client.post(f"/onboarding/sessions/{sid}/steps", json={"step": "NOMBRES"})
    assert r.status_code == 201
    body = r.json()
    assert body["step"] == "NOMBRES"
    assert isinstance(body["elapsed_ms"], int) and body["elapsed_ms"] >= 0


def test_api_onb_03_invalid_step(client):
    sid = client.post("/onboarding/sessions").json()["session_id"]
    r = client.post(f"/onboarding/sessions/{sid}/steps", json={"step": "CORREO"})
    assert_error(r, 422, "VALIDATION_ERROR")


def test_api_onb_04_unknown_session(client):
    r = client.post(f"/onboarding/sessions/{uuid.uuid4()}/steps", json={"step": "NOMBRES"})
    assert_error(r, 404, "NOT_FOUND")


# ------------------------------------------------------------------ usuario (CA-02)
def test_api_usr_01_available(client):
    r = client.post("/onboarding/username-availability", json={"username": unique_username()})
    assert r.status_code == 200
    assert r.json() == {"status": "AVAILABLE", "suggestions": []}


@pytest.mark.parametrize(
    "username",
    [pytest.param("12345", id="sin-letras"), pytest.param("a" * 21, id="21-caracteres")],
)
def test_api_usr_02_invalid_format(client, username):
    r = client.post("/onboarding/username-availability", json={"username": username})
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "INVALID_FORMAT"
    assert body["suggestions"] == []


def test_api_usr_03_taken_with_suggestions(client):
    w = register(client, nombres="Juan", apellido_paterno="Perez", apellido_materno="Soto")
    r = client.post(
        "/onboarding/username-availability",
        json={
            "username": w.username,
            "nombres": "Juan",
            "apellido_paterno": "Perez",
            "apellido_materno": "Soto",
        },
    )
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "TAKEN"
    assert len(body["suggestions"]) >= 1
    print("Sugerencias (revisión manual P-02):", body["suggestions"])
    for s in body["suggestions"]:
        assert SUGGESTION_RE.match(s), "sugerencia con símbolos o formato inválido"
        assert s.lower() != w.username.lower()
        check = client.post("/onboarding/username-availability", json={"username": s})
        assert check.json()["status"] == "AVAILABLE", "sugerencia no disponible"


def test_api_usr_04_case_insensitive(client):
    w = register(client)
    r = client.post("/onboarding/username-availability", json={"username": w.username.upper()})
    assert r.status_code == 200
    assert r.json()["status"] == "TAKEN"


# ------------------------------------------------------------------ registro (CA-02, CA-03, CA-04)
def test_api_reg_01_successful_registration(client):
    payload = registration_payload()
    r = client.post("/onboarding/registrations", json=payload)
    assert r.status_code == 201
    body = r.json()
    acc = body["account"]
    uuid.UUID(acc["wallet_id"])  # wallet_id válido (UUID)
    assert acc["status"] == "ACTIVE_BASIC"
    assert Decimal(acc["balance"]) == 0
    assert acc["currency"] == "PEN"
    assert body["welcome"]["display_name"] == "María José"
    assert body["profile"] == {
        "estado_c1": "PENDING_EMAIL",
        "estado_c2": "PENDING_MOVIL",
        "estado_c3": "PENDING_BIOM",
    }
    oc = body["operation_conditions"]
    assert oc["account_status"] == "ACTIVE_BASIC"
    assert oc["timezone"] == "America/Lima"
    assert len(oc["rules"]) == 1
    rule = oc["rules"][0]
    assert rule["operation_group"] == "COMBINED"
    assert set(rule["operation_types"]) == {"TOPUP_OWN", "PAYMENT"}
    assert Decimal(rule["per_operation_max"]) == 20
    assert Decimal(rule["daily_max"]) == 60
    assert PASSWORD not in r.text, "la contraseña no debe aparecer en la respuesta"


@pytest.mark.parametrize(
    "field_name,value",
    [
        pytest.param("nombres", "Ab" * 15, id="nombres-30"),
        pytest.param("apellido_paterno", "Ab" * 10, id="apellido-paterno-20"),
        pytest.param("apellido_materno", "Ab" * 10, id="apellido-materno-20"),
        pytest.param("usuario", None, id="usuario-20"),
        pytest.param("password", "Abcdefg123", id="password-10"),
        pytest.param("password", "Abcdef#123", id="password-10-con-simbolo"),
    ],
)
def test_api_reg_02_valid_boundaries(client, field_name, value):
    if field_name == "usuario":
        value = unique_username(20)
        assert len(value) == 20
    r = client.post("/onboarding/registrations", json=registration_payload(**{field_name: value}))
    assert r.status_code == 201


@pytest.mark.parametrize(
    "field_name,value",
    [
        pytest.param("nombres", "Maria123", id="nombres-digitos"),
        pytest.param("nombres", "a" * 31, id="nombres-31"),
        pytest.param("nombres", "María  José", id="nombres-doble-espacio"),
        pytest.param("nombres", "", id="nombres-vacio"),
        pytest.param("apellido_paterno", "Quispe9", id="paterno-digito"),
        pytest.param("apellido_paterno", "a" * 21, id="paterno-21"),
        pytest.param("apellido_materno", "Rojas9", id="materno-digito"),
        pytest.param("apellido_materno", "a" * 21, id="materno-21"),
        pytest.param("usuario", "a" * 21, id="usuario-21"),
        pytest.param("usuario", "12345", id="usuario-sin-letra"),
        pytest.param("usuario", "con espacio", id="usuario-con-espacio"),
        pytest.param("password", "Abcdef123", id="password-9"),
    ],
)
def test_api_reg_03_invalid_values(client, field_name, value):
    r = client.post("/onboarding/registrations", json=registration_payload(**{field_name: value}))
    assert_error(r, 422, "VALIDATION_ERROR")
    if value:
        assert value not in r.text, "el 422 no debe devolver el valor recibido"
    assert PASSWORD not in r.text


@pytest.mark.parametrize(
    "missing", ["nombres", "apellido_paterno", "apellido_materno", "usuario", "password"]
)
def test_api_reg_04_missing_field(client, missing):
    payload = registration_payload()
    payload.pop(missing)
    r = client.post("/onboarding/registrations", json=payload)
    assert r.status_code == 422


def test_api_reg_05_duplicate_username(client):
    first = register(client)
    r = client.post("/onboarding/registrations", json=registration_payload(usuario=first.username))
    body = assert_error(r, 409, "USERNAME_TAKEN")
    assert len(body["suggestions"]) >= 1
    assert all(SUGGESTION_RE.match(s) for s in body["suggestions"])
    # sin distinguir mayúsculas
    r2 = client.post(
        "/onboarding/registrations", json=registration_payload(usuario=first.username.upper())
    )
    assert_error(r2, 409, "USERNAME_TAKEN")


def test_api_reg_06_duration_and_session_closed(client):
    sid = client.post("/onboarding/sessions").json()["session_id"]
    client.post(f"/onboarding/sessions/{sid}/steps", json={"step": "NOMBRES"})
    r = client.post("/onboarding/registrations", json=registration_payload(session_id=sid))
    assert r.status_code == 201
    duration = r.json()["registration_duration_ms"]
    assert isinstance(duration, int) and duration >= 0
    late = client.post(f"/onboarding/sessions/{sid}/steps", json={"step": "USUARIO"})
    assert_error(late, 409, "SESSION_CLOSED")


def test_api_reg_07_no_session_null_duration(client):
    r = client.post("/onboarding/registrations", json=registration_payload())
    assert r.status_code == 201
    assert r.json().get("registration_duration_ms") is None


def test_api_reg_08_unknown_session(client):
    r = client.post(
        "/onboarding/registrations", json=registration_payload(session_id=str(uuid.uuid4()))
    )
    assert_error(r, 404, "NOT_FOUND")


def test_api_reg_09_wallet_detail_after_registration(client, basic_wallet):
    detail = get_wallet(client, basic_wallet)
    assert detail["account"]["wallet_id"] == basic_wallet.wallet_id
    assert detail["account"]["status"] == "ACTIVE_BASIC"
    assert Decimal(detail["account"]["balance"]) == 0
    assert detail["profile"]["estado_c1"] == "PENDING_EMAIL"
    assert detail["profile"]["estado_c2"] == "PENDING_MOVIL"
    assert detail["profile"]["estado_c3"] == "PENDING_BIOM"
    assert detail["operation_conditions"]["account_status"] == "ACTIVE_BASIC"
    assert isinstance(detail["identity_mock_available"], bool)
    assert wallet_url(basic_wallet).endswith(basic_wallet.wallet_id)
```

## `qa/api/test_profile_api.py`

```python
"""CA-06, CA-07, CA-08: perfil, OTP mock de correo y celular."""
import time

import pytest

from helpers import (
    CHANNELS,
    assert_error,
    confirm_channel,
    get_wallet,
    otp_confirm,
    otp_request,
    parse_dt,
    register,
    unique_email,
    unique_phone,
)

CHANNEL_PARAMS = [pytest.param("email", id="email"), pytest.param("phone", id="phone")]


def state_of(client, wallet, channel):
    return get_wallet(client, wallet)["profile"][CHANNELS[channel]["state"]]


# ------------------------------------------------------------------ estados (CA-06)
def test_api_prf_01_initial_states(client, basic_wallet):
    assert get_wallet(client, basic_wallet)["profile"] == {
        "estado_c1": "PENDING_EMAIL",
        "estado_c2": "PENDING_MOVIL",
        "estado_c3": "PENDING_BIOM",
    }


def test_api_prf_02_independence_phone_before_email(client, basic_wallet):
    confirm_channel(client, basic_wallet, "phone")
    p1 = get_wallet(client, basic_wallet)["profile"]
    assert p1 == {
        "estado_c1": "PENDING_EMAIL",
        "estado_c2": "ACTIVE_MOVIL",
        "estado_c3": "PENDING_BIOM",
    }
    confirm_channel(client, basic_wallet, "email")
    p2 = get_wallet(client, basic_wallet)["profile"]
    assert p2 == {
        "estado_c1": "ACTIVE_EMAIL",
        "estado_c2": "ACTIVE_MOVIL",
        "estado_c3": "PENDING_BIOM",
    }


# ------------------------------------------------------------------ formato (CA-07, CA-08)
@pytest.mark.parametrize("email", ["ana@@example", "sin-arroba.com", "a@b", " ", "@example.com"])
def test_api_eml_01_invalid_format(client, basic_wallet, email):
    r = otp_request(client, basic_wallet, "email", email)
    assert_error(r, 422, ("INVALID_EMAIL_FORMAT", "VALIDATION_ERROR"))
    if email.strip():
        assert email not in r.text


@pytest.mark.parametrize(
    "phone",
    ["812345678", "91234567", "9123456789", "abc123456", "+51912345678", "9123 45678"],
)
def test_api_phn_01_invalid_format(client, basic_wallet, phone):
    r = otp_request(client, basic_wallet, "phone", phone)
    assert_error(r, 422, ("INVALID_PHONE_FORMAT", "VALIDATION_ERROR"))


def test_api_phn_02_prefix_not_editable(client, basic_wallet):
    phone = unique_phone()
    r = client.post(
        f"/wallets/{basic_wallet.wallet_id}/profile/phone/otp-requests",
        json={"phone": phone, "prefix": "+52"},
        auth=basic_wallet.auth,
    )
    assert r.status_code in (201, 422)
    if r.status_code == 201:
        assert r.json()["phone_e164"].startswith("+51")
        assert not r.json()["phone_e164"].startswith("+52")


def test_api_phn_03_e164(client, basic_wallet):
    phone = unique_phone()
    r = otp_request(client, basic_wallet, "phone", phone)
    assert r.status_code == 201
    assert r.json()["phone_e164"] == "+51" + phone


# ------------------------------------------------------------------ OTP común (CA-07, CA-08)
@pytest.mark.parametrize("channel", CHANNEL_PARAMS)
def test_api_otp_01_issue(client, basic_wallet, channel):
    cfg = CHANNELS[channel]
    r = otp_request(client, basic_wallet, channel)
    assert r.status_code == 201
    b = r.json()
    assert b["channel"] == channel.upper()
    assert b["expires_in_seconds"] == 60
    assert b["otp_length"] == 6
    assert b["delivery"] == "MOCK_NOT_SENT"
    for forbidden in ("otp", "code", "otp_code", "mock_otp"):
        assert forbidden not in b, "el OTP no debe devolverse"
    delta = (parse_dt(b["expires_at"]) - parse_dt(b["next_request_allowed_at"])).total_seconds()
    assert 13 <= delta <= 17, f"vigencia 60 s menos intervalo 45 s debería ser ≈15 s, fue {delta}"
    assert state_of(client, basic_wallet, channel) == cfg["pending"]


@pytest.mark.parametrize("channel", CHANNEL_PARAMS)
def test_api_otp_03_rate_limit(client, basic_wallet, channel):
    first = otp_request(client, basic_wallet, channel)
    assert first.status_code == 201
    second = otp_request(client, basic_wallet, channel)
    assert_error(second, 429, "OTP_RATE_LIMITED")
    retry = int(second.headers["Retry-After"])
    assert 1 <= retry <= 45


@pytest.mark.parametrize("channel", CHANNEL_PARAMS)
def test_api_otp_04_confirm_without_otp(client, basic_wallet, channel):
    r = otp_confirm(client, basic_wallet, channel)
    assert_error(r, 422, "OTP_NOT_ACTIVE")
    assert state_of(client, basic_wallet, channel) == CHANNELS[channel]["pending"]


@pytest.mark.parametrize("otp", ["000000", "abcdef", "1"])
@pytest.mark.parametrize("channel", CHANNEL_PARAMS)
def test_api_otp_05_confirm_any_value(client, basic_wallet, channel, otp):
    cfg = CHANNELS[channel]
    assert otp_request(client, basic_wallet, channel).status_code == 201
    r = otp_confirm(client, basic_wallet, channel, otp)
    assert r.status_code == 200
    body = r.json()
    assert body["wallet_id"] == basic_wallet.wallet_id
    assert body["profile"][cfg["state"]] == cfg["active"]
    others = {"estado_c1", "estado_c2", "estado_c3"} - {cfg["state"]}
    for key in others:
        assert body["profile"][key].startswith("PENDING")
    assert state_of(client, basic_wallet, channel) == cfg["active"]


@pytest.mark.parametrize("channel", CHANNEL_PARAMS)
def test_api_otp_06_empty_otp(client, basic_wallet, channel):
    assert otp_request(client, basic_wallet, channel).status_code == 201
    r = otp_confirm(client, basic_wallet, channel, "")
    assert_error(r, 422, "VALIDATION_ERROR")
    assert state_of(client, basic_wallet, channel) == CHANNELS[channel]["pending"]


@pytest.mark.parametrize("channel", CHANNEL_PARAMS)
def test_api_otp_07_consumed_otp_not_reusable(client, basic_wallet, channel):
    confirm_channel(client, basic_wallet, channel)
    again = otp_confirm(client, basic_wallet, channel)
    assert again.status_code == 422
    assert again.json()["code"] in ("OTP_NOT_ACTIVE", "OTP_EXPIRED")


@pytest.mark.parametrize("channel", CHANNEL_PARAMS)
def test_api_otp_08_duplicate_destination(client, channel):
    cfg = CHANNELS[channel]
    owner = register(client)
    other = register(client)
    value = confirm_channel(client, owner, channel)
    r = otp_request(client, other, channel, value)
    assert_error(r, 409, cfg["dup_code"])
    if channel == "email":  # unicidad sin distinguir mayúsculas
        r2 = otp_request(client, other, channel, value.upper())
        assert_error(r2, 409, cfg["dup_code"])
    assert state_of(client, other, channel) == cfg["pending"]


@pytest.mark.parametrize("channel", CHANNEL_PARAMS)
def test_api_otp_09_already_validated(client, basic_wallet, channel):
    # La precedencia frente a 429 no está especificada (ver informe, sección 2).
    confirm_channel(client, basic_wallet, channel)
    r = otp_request(client, basic_wallet, channel)
    assert_error(r, 409, "ALREADY_VALIDATED")


# ------------------------------------------------------------------ OTP con tiempos reales (slow)
@pytest.mark.slow
@pytest.mark.parametrize("channel", CHANNEL_PARAMS)
def test_api_otp_10_resend_window(client, basic_wallet, channel):
    value = CHANNELS[channel]["new"]()
    t0 = time.monotonic()
    assert otp_request(client, basic_wallet, channel, value).status_code == 201
    time.sleep(max(0.0, 44 - (time.monotonic() - t0)))
    early = otp_request(client, basic_wallet, channel, value)
    assert_error(early, 429, "OTP_RATE_LIMITED")
    time.sleep(max(0.0, 46 - (time.monotonic() - t0)))
    late = otp_request(client, basic_wallet, channel, value)
    assert late.status_code == 201


@pytest.mark.slow
@pytest.mark.parametrize("channel", CHANNEL_PARAMS)
def test_api_otp_11_expiry_after_60s(client, basic_wallet, channel):
    assert otp_request(client, basic_wallet, channel).status_code == 201
    time.sleep(61)
    r = otp_confirm(client, basic_wallet, channel)
    assert_error(r, 422, "OTP_EXPIRED")
    assert state_of(client, basic_wallet, channel) == CHANNELS[channel]["pending"]


@pytest.mark.slow
@pytest.mark.parametrize("channel", CHANNEL_PARAMS)
def test_api_otp_12_new_otp_valid_after_first_expires(client, basic_wallet, channel):
    value = CHANNELS[channel]["new"]()
    t0 = time.monotonic()
    assert otp_request(client, basic_wallet, channel, value).status_code == 201
    time.sleep(max(0.0, 46 - (time.monotonic() - t0)))
    assert otp_request(client, basic_wallet, channel, value).status_code == 201
    time.sleep(max(0.0, 61 - (time.monotonic() - t0)))  # el primer OTP ya venció
    r = otp_confirm(client, basic_wallet, channel)
    assert r.status_code == 200
    assert state_of(client, basic_wallet, channel) == CHANNELS[channel]["active"]
```

## `qa/api/test_identity_api.py`

```python
"""CA-09, CA-10, CA-12: biometría mock y ACTIVE_FULL."""
import pytest

from helpers import (
    MOCK_BIOMETRIC_ENABLED,
    activate_full,
    assert_error,
    confirm_channel,
    get_wallet,
    register,
    requires_mock,
    requires_mock_disabled,
    wallet_url,
)


def mock_verify(client, w, body):
    return client.post(wallet_url(w, "/profile/identity/mock-verification"), json=body, auth=w.auth)


@requires_mock
def test_api_idn_01_terms_not_accepted(client, basic_wallet):
    r = mock_verify(client, basic_wallet, {"terms_accepted": False, "mock_inputs_confirmed": True})
    assert_error(r, 422, "TERMS_NOT_ACCEPTED")
    assert get_wallet(client, basic_wallet)["account"]["status"] == "ACTIVE_BASIC"


@requires_mock
def test_api_idn_02_mock_inputs_not_confirmed(client, basic_wallet):
    r = mock_verify(client, basic_wallet, {"terms_accepted": True, "mock_inputs_confirmed": False})
    assert_error(r, 422, "MOCK_INPUTS_INVALID")
    assert get_wallet(client, basic_wallet)["account"]["status"] == "ACTIVE_BASIC"


@requires_mock
@pytest.mark.parametrize(
    "body", [{}, {"terms_accepted": True}, {"mock_inputs_confirmed": True}], ids=["vacio", "sin-inputs", "sin-terminos"]
)
def test_api_idn_03_missing_fields(client, basic_wallet, body):
    r = mock_verify(client, basic_wallet, body)
    assert_error(r, 422, "VALIDATION_ERROR")


@requires_mock
def test_api_idn_04_success_without_email_or_phone(client, basic_wallet):
    r = mock_verify(client, basic_wallet, {"terms_accepted": True, "mock_inputs_confirmed": True})
    assert r.status_code == 200
    body = r.json()
    assert body["account"]["status"] == "ACTIVE_FULL"
    assert body["profile"] == {
        "estado_c1": "PENDING_EMAIL",
        "estado_c2": "PENDING_MOVIL",
        "estado_c3": "ACTIVE_BIOM",
    }
    detail = get_wallet(client, basic_wallet)
    assert detail["account"]["status"] == "ACTIVE_FULL"
    assert detail["operation_conditions"]["account_status"] == "ACTIVE_FULL"


@requires_mock
def test_api_idn_05_repeat_is_conflict(client, full_wallet):
    r = mock_verify(client, full_wallet, {"terms_accepted": True, "mock_inputs_confirmed": True})
    assert_error(r, 409, "ALREADY_ACTIVE_FULL")


@requires_mock
def test_api_idn_06_full_journey(client):
    w = register(client)
    confirm_channel(client, w, "email")
    confirm_channel(client, w, "phone")
    activate_full(client, w)
    detail = get_wallet(client, w)
    assert detail["account"]["status"] == "ACTIVE_FULL"
    assert detail["profile"] == {
        "estado_c1": "ACTIVE_EMAIL",
        "estado_c2": "ACTIVE_MOVIL",
        "estado_c3": "ACTIVE_BIOM",
    }


@requires_mock_disabled
def test_api_idn_07_mock_disabled_in_other_env(client, basic_wallet):
    r = mock_verify(client, basic_wallet, {"terms_accepted": True, "mock_inputs_confirmed": True})
    assert_error(r, 403, "BIOMETRIC_MOCK_DISABLED")
    detail = get_wallet(client, basic_wallet)
    assert detail["account"]["status"] == "ACTIVE_BASIC"
    assert detail["profile"]["estado_c3"] == "PENDING_BIOM"


def test_api_idn_08_identity_mock_available_flag(client, basic_wallet):
    assert get_wallet(client, basic_wallet)["identity_mock_available"] is MOCK_BIOMETRIC_ENABLED
```

## `qa/api/test_operations_api.py`

```python
"""CA-05 y CA-13: operaciones y topes."""
from decimal import Decimal

import pytest

from helpers import (
    activate_full,
    assert_error,
    get_wallet,
    lima_today,
    post_op,
    requires_mock,
    register,
)

TYPES_BASIC = [pytest.param("PAYMENT", id="PAYMENT"), pytest.param("TOPUP_OWN", id="TOPUP_OWN")]


# ------------------------------------------------------------------ ACTIVE_BASIC (CA-05)
@pytest.mark.parametrize("op_type", TYPES_BASIC)
def test_api_ops_01_accepts_20(client, basic_wallet, op_type):
    before = lima_today()
    r = post_op(client, basic_wallet, op_type, "20.00")
    after = lima_today()
    assert r.status_code == 201
    b = r.json()
    assert b["operation_type"] == op_type
    assert Decimal(b["amount"]) == 20
    assert Decimal(b["daily_accumulated"]) == 20
    assert Decimal(b["daily_max"]) == 60
    assert b["operation_day"] in {before.isoformat(), after.isoformat()}
    assert len(b["operation_id"]) == 36


@pytest.mark.parametrize("op_type", TYPES_BASIC)
def test_api_ops_02_rejects_20_01(client, basic_wallet, op_type):
    r = post_op(client, basic_wallet, op_type, "20.01")
    assert_error(r, 422, "PER_OPERATION_LIMIT_EXCEEDED")


def test_api_ops_03_third_party_not_allowed_in_basic(client, basic_wallet):
    r = post_op(client, basic_wallet, "TOPUP_THIRD_PARTY", "1.00")
    assert_error(r, 422, "OPERATION_NOT_ALLOWED")


def test_api_ops_04_daily_limit_combined(client, basic_wallet):
    for op_type, expected in (("TOPUP_OWN", "20"), ("PAYMENT", "40"), ("PAYMENT", "60")):
        r = post_op(client, basic_wallet, op_type, "20.00")
        assert r.status_code == 201
        assert Decimal(r.json()["daily_accumulated"]) == Decimal(expected)
    assert_error(post_op(client, basic_wallet, "PAYMENT", "1.00"), 422, "DAILY_LIMIT_EXCEEDED")
    assert_error(post_op(client, basic_wallet, "TOPUP_OWN", "1.00"), 422, "DAILY_LIMIT_EXCEEDED")


def test_api_ops_05_boundary_and_rejected_do_not_accumulate(client, basic_wallet):
    for amount in ("20.00", "20.00", "10.00"):
        assert post_op(client, basic_wallet, "PAYMENT", amount).status_code == 201  # 50
    assert_error(post_op(client, basic_wallet, "PAYMENT", "10.01"), 422, "DAILY_LIMIT_EXCEEDED")
    ok = post_op(client, basic_wallet, "PAYMENT", "10.00")
    assert ok.status_code == 201
    assert Decimal(ok.json()["daily_accumulated"]) == 60


def test_api_ops_06_payments_and_topups_share_accumulator(client, basic_wallet):
    assert post_op(client, basic_wallet, "TOPUP_OWN", "20.00").status_code == 201
    assert post_op(client, basic_wallet, "TOPUP_OWN", "20.00").status_code == 201
    paid = post_op(client, basic_wallet, "PAYMENT", "20.00")
    assert paid.status_code == 201
    assert Decimal(paid.json()["daily_accumulated"]) == 60
    assert_error(post_op(client, basic_wallet, "PAYMENT", "1.00"), 422, "DAILY_LIMIT_EXCEEDED")


def test_api_ops_07_rejected_do_not_accumulate(client, basic_wallet):
    assert_error(post_op(client, basic_wallet, "PAYMENT", "20.01"), 422, "PER_OPERATION_LIMIT_EXCEEDED")
    assert_error(post_op(client, basic_wallet, "TOPUP_THIRD_PARTY", "5.00"), 422, "OPERATION_NOT_ALLOWED")
    r = post_op(client, basic_wallet, "PAYMENT", "20.00")
    assert r.status_code == 201
    assert Decimal(r.json()["daily_accumulated"]) == 20


@pytest.mark.parametrize("amount", ["0", "0.00", "-5", "abc", "20.001", ""])
def test_api_ops_08_invalid_amount(client, basic_wallet, amount):
    r = post_op(client, basic_wallet, "PAYMENT", amount)
    assert_error(r, 422, "VALIDATION_ERROR")


def test_api_ops_09_invalid_operation_type(client, basic_wallet):
    r = post_op(client, basic_wallet, "REFUND", "5.00")
    assert r.status_code == 422


def test_api_ops_10_basic_conditions(client, basic_wallet):
    oc = get_wallet(client, basic_wallet)["operation_conditions"]
    assert oc["account_status"] == "ACTIVE_BASIC"
    assert oc["timezone"] == "America/Lima"
    (rule,) = oc["rules"]
    assert rule["operation_group"] == "COMBINED"
    assert set(rule["operation_types"]) == {"TOPUP_OWN", "PAYMENT"}
    assert Decimal(rule["per_operation_max"]) == 20
    assert Decimal(rule["daily_max"]) == 60


def test_api_ops_12_balance_unchanged(client, basic_wallet):
    # Supuesto S5 del Arquitecto: esta entrega no modifica balance.
    assert post_op(client, basic_wallet, "TOPUP_OWN", "20.00").status_code == 201
    assert Decimal(get_wallet(client, basic_wallet)["account"]["balance"]) == 0


# ------------------------------------------------------------------ ACTIVE_FULL (CA-13)
@requires_mock
def test_api_ops_20_topup_without_per_operation_limit(client, full_wallet):
    r = post_op(client, full_wallet, "TOPUP_THIRD_PARTY", "1000.00")
    assert r.status_code == 201
    assert Decimal(r.json()["daily_accumulated"]) == 1000
    assert Decimal(r.json()["daily_max"]) == 1000
    assert_error(post_op(client, full_wallet, "TOPUP_THIRD_PARTY", "0.01"), 422, "DAILY_LIMIT_EXCEEDED")
    assert_error(post_op(client, full_wallet, "TOPUP_OWN", "0.01"), 422, "DAILY_LIMIT_EXCEEDED")


@requires_mock
def test_api_ops_21_payment_per_operation_limit(client, full_wallet):
    assert post_op(client, full_wallet, "PAYMENT", "500.00").status_code == 201
    assert_error(post_op(client, full_wallet, "PAYMENT", "500.01"), 422, "PER_OPERATION_LIMIT_EXCEEDED")


@requires_mock
def test_api_ops_22_payment_daily_limit(client, full_wallet):
    assert post_op(client, full_wallet, "PAYMENT", "500.00").status_code == 201
    r = post_op(client, full_wallet, "PAYMENT", "500.00")
    assert r.status_code == 201
    assert Decimal(r.json()["daily_accumulated"]) == 1000
    assert_error(post_op(client, full_wallet, "PAYMENT", "0.01"), 422, "DAILY_LIMIT_EXCEEDED")


@requires_mock
def test_api_ops_23_topup_and_payment_groups_independent(client, full_wallet):
    assert post_op(client, full_wallet, "TOPUP_OWN", "1000.00").status_code == 201
    r = post_op(client, full_wallet, "PAYMENT", "500.00")
    assert r.status_code == 201
    assert Decimal(r.json()["daily_accumulated"]) == 500


@requires_mock
def test_api_ops_24_full_conditions(client, full_wallet):
    oc = get_wallet(client, full_wallet)["operation_conditions"]
    assert oc["account_status"] == "ACTIVE_FULL"
    rules = {r["operation_group"]: r for r in oc["rules"]}
    assert set(rules) == {"TOPUP", "PAYMENT"}
    assert set(rules["TOPUP"]["operation_types"]) == {"TOPUP_OWN", "TOPUP_THIRD_PARTY"}
    assert rules["TOPUP"]["per_operation_max"] is None
    assert Decimal(rules["TOPUP"]["daily_max"]) == 1000
    assert rules["PAYMENT"]["operation_types"] == ["PAYMENT"]
    assert Decimal(rules["PAYMENT"]["per_operation_max"]) == 500
    assert Decimal(rules["PAYMENT"]["daily_max"]) == 1000


@requires_mock
def test_api_ops_25_third_party_allowed_after_upgrade(client):
    w = register(client)
    assert_error(post_op(client, w, "TOPUP_THIRD_PARTY", "10.00"), 422, "OPERATION_NOT_ALLOWED")
    activate_full(client, w)
    assert post_op(client, w, "TOPUP_THIRD_PARTY", "10.00").status_code == 201
```

## `qa/api/test_access_privacy_contract_api.py`

```python
"""CA-10 (acceso y privacidad) y conformidad del contrato."""
import base64
import os
import re
import time
import uuid
from pathlib import Path

import pytest

from helpers import (
    PASSWORD,
    assert_error,
    confirm_channel,
    otp_request,
    random_letters,
    register,
    registration_payload,
    unique_email,
    unique_phone,
    unique_username,
)

PROTECTED = [
    ("GET", "", None),
    ("POST", "/profile/email/otp-requests", {"email": "a.qa@example.com"}),
    ("POST", "/profile/email/otp-confirmations", {"otp": "123456"}),
    ("POST", "/profile/phone/otp-requests", {"phone": "912345678"}),
    ("POST", "/profile/phone/otp-confirmations", {"otp": "123456"}),
    ("POST", "/profile/identity/mock-verification", {"terms_accepted": True, "mock_inputs_confirmed": True}),
    ("POST", "/operations", {"operation_type": "PAYMENT", "amount": "1.00"}),
]
PROTECTED_IDS = ["GET-wallet", "email-otp-req", "email-otp-conf", "phone-otp-req", "phone-otp-conf", "identity-mock", "operations"]


@pytest.mark.parametrize("method,suffix,body", PROTECTED, ids=PROTECTED_IDS)
def test_api_sec_01_no_credentials(client, basic_wallet, method, suffix, body):
    r = client.request(method, f"/wallets/{basic_wallet.wallet_id}{suffix}", json=body)
    assert_error(r, 401, "UNAUTHORIZED")


def test_api_sec_01b_www_authenticate_header(client, basic_wallet):
    r = client.get(f"/wallets/{basic_wallet.wallet_id}")
    assert r.status_code == 401
    assert "www-authenticate" in {k.lower() for k in r.headers}


def test_api_sec_02_wrong_credentials(client, basic_wallet):
    url = f"/wallets/{basic_wallet.wallet_id}"
    assert_error(client.get(url, auth=(basic_wallet.username, "Incorrecta#2026")), 401, "UNAUTHORIZED")
    assert_error(client.get(url, auth=(unique_username(), PASSWORD)), 401, "UNAUTHORIZED")


@pytest.mark.parametrize("method,suffix,body", PROTECTED, ids=PROTECTED_IDS)
def test_api_sec_03_foreign_wallet_forbidden(client, method, suffix, body):
    owner = register(client)
    intruder = register(client)
    r = client.request(method, f"/wallets/{owner.wallet_id}{suffix}", json=body, auth=intruder.auth)
    assert_error(r, 403, "FORBIDDEN")


def test_api_sec_04_unknown_wallet(client, basic_wallet):
    r = client.get(f"/wallets/{uuid.uuid4()}", auth=basic_wallet.auth)
    assert_error(r, 404, "NOT_FOUND")


def test_api_sec_05_validation_errors_do_not_echo_values(client, basic_wallet):
    bad_email = f"no-es-correo-{uuid.uuid4().hex[:8]}@@x"
    r1 = otp_request(client, basic_wallet, "email", bad_email)
    assert r1.status_code == 422
    assert bad_email not in r1.text

    bad_phone = "8" + unique_phone()[1:]
    r2 = otp_request(client, basic_wallet, "phone", bad_phone)
    assert r2.status_code == 422
    assert bad_phone not in r2.text

    short_pw = "Zq#" + uuid.uuid4().hex[:4]
    r3 = client.post("/onboarding/registrations", json=registration_payload(password=short_pw))
    assert r3.status_code == 422
    assert short_pw not in r3.text


@pytest.mark.skipif(not os.getenv("API_LOG_FILE"), reason="Defina API_LOG_FILE (salida del backend redirigida a archivo)")
def test_api_sec_06_no_personal_data_in_logs(client):
    nombres = random_letters(8)
    paterno = random_letters(7)
    materno = random_letters(6)
    password = "Zq#" + uuid.uuid4().hex[:10] + "Aa1"
    usuario = unique_username()
    email = unique_email()
    phone = unique_phone()

    w = register(client, nombres=nombres, apellido_paterno=paterno,
                 apellido_materno=materno, usuario=usuario, password=password)
    confirm_channel(client, w, "email", email)
    confirm_channel(client, w, "phone", phone)
    client.get(f"/wallets/{w.wallet_id}", auth=(usuario, "Mala#Clave2026"))  # intento fallido
    time.sleep(1.5)  # permitir el volcado de logs

    log = Path(os.environ["API_LOG_FILE"]).read_text(encoding="utf-8", errors="ignore")
    token = base64.b64encode(f"{usuario}:{password}".encode()).decode()
    for label, secret in {
        "contraseña": password,
        "nombres": nombres,
        "apellido paterno": paterno,
        "apellido materno": materno,
        "correo": email,
        "celular": phone,
        "token Basic": token,
    }.items():
        assert secret not in log, f"el log contiene {label}"


EXPECTED_OPERATIONS = {
    ("post", "/onboarding/sessions"),
    ("post", "/onboarding/sessions/{session_id}/steps"),
    ("post", "/onboarding/username-availability"),
    ("post", "/onboarding/registrations"),
    ("get", "/wallets/{wallet_id}"),
    ("post", "/wallets/{wallet_id}/profile/email/otp-requests"),
    ("post", "/wallets/{wallet_id}/profile/email/otp-confirmations"),
    ("post", "/wallets/{wallet_id}/profile/phone/otp-requests"),
    ("post", "/wallets/{wallet_id}/profile/phone/otp-confirmations"),
    ("post", "/wallets/{wallet_id}/profile/identity/mock-verification"),
    ("post", "/wallets/{wallet_id}/operations"),
}


def test_api_sec_07_contract_paths(client):
    r = client.get("/openapi.json")
    if r.status_code != 200:
        pytest.skip("El backend no expone /openapi.json")
    paths = r.json()["paths"]
    missing = {(m, p) for m, p in EXPECTED_OPERATIONS if m not in paths.get(p, {})}
    assert not missing, f"operaciones del contrato ausentes: {sorted(missing)}"


@pytest.mark.skipif(not os.getenv("BACKEND_DIR"), reason="Defina BACKEND_DIR (carpeta backend)")
def test_api_sec_08_future_biometric_requirements_documented():
    doc = Path(os.environ["BACKEND_DIR"]) / "docs" / "biometria-real-requisitos.md"
    assert doc.exists(), "falta docs/biometria-real-requisitos.md"
    text = doc.read_text(encoding="utf-8", errors="ignore")
    assert re.search(r"2\s*MB", text)
    assert re.search(r"10\s*MB", text)
    assert re.search(r"10\s*min", text, re.IGNORECASE)
```

---

## `qa/ui_helpers.py`

```python
"""Utilidades Selenium. Los selectores provienen del código fuente del frontend Angular."""
import os
import re

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select, WebDriverWait

from helpers import PASSWORD, unique_username

UI_BASE_URL = os.getenv("UI_BASE_URL", "http://localhost:4200").rstrip("/")
WAIT = float(os.getenv("UI_WAIT_SECONDS", "10"))
WALLET_UUID_RE = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", re.I)


def wait(driver, timeout=None):
    return WebDriverWait(driver, timeout or WAIT)


def tid(driver, testid):
    return driver.find_element(By.CSS_SELECTOR, f'[data-testid="{testid}"]')


def wait_tid(driver, testid):
    return wait(driver).until(
        EC.visibility_of_element_located((By.CSS_SELECTOR, f'[data-testid="{testid}"]'))
    )


def wait_tid_text(driver, testid, fragment):
    wait(driver).until(lambda d: fragment in tid(d, testid).text)
    return tid(driver, testid)


def set_text(driver, element_id, text, tab=False):
    el = driver.find_element(By.ID, element_id)
    el.clear()
    el.send_keys(text)
    if tab:
        el.send_keys(Keys.TAB)
    return el


def field_state(driver, element_id):
    el = driver.find_element(By.ID, element_id)
    field = el.find_element(
        By.XPATH, "./ancestor::div[contains(concat(' ', normalize-space(@class), ' '), ' field ')][1]"
    )
    return field.get_attribute("data-state")


def wait_state(driver, element_id, expected):
    wait(driver).until(
        lambda d: field_state(d, element_id) == expected,
        message=f"campo {element_id} no llegó a data-state={expected}",
    )


def field_message(driver, element_id):
    return driver.find_element(By.ID, f"{element_id}-msg").text


def resource_urls(driver):
    return driver.execute_script(
        "return performance.getEntriesByType('resource').map(function(e){return e.name;});"
    )


def register_via_ui(driver, usuario=None, nombres="María José", paterno="Quispe",
                    materno="Rojas", password=PASSWORD):
    usuario = usuario or unique_username()
    driver.get(f"{UI_BASE_URL}/onboarding")
    wait(driver).until(EC.visibility_of_element_located((By.ID, "nombres")))
    set_text(driver, "nombres", nombres)
    set_text(driver, "apellido_paterno", paterno)
    set_text(driver, "apellido_materno", materno)
    set_text(driver, "usuario", usuario)
    set_text(driver, "password", password)
    wait_state(driver, "usuario", "valid")
    submit = tid(driver, "submit")
    wait(driver).until(lambda d: tid(d, "submit").is_enabled())
    submit.click()
    wait(driver).until(EC.url_contains("/landing"))
    wait_tid(driver, "wallet-id")
    return {
        "username": usuario,
        "password": password,
        "nombres": nombres,
        "wallet_id": tid(driver, "wallet-id").text.strip(),
    }


def open_profile(driver):
    tid(driver, "pending-banner").find_element(By.TAG_NAME, "a").click()
    wait(driver).until(EC.url_contains("/profile"))
    wait(driver).until(lambda d: len(cards(d)) == 2)


def cards(driver):
    return driver.find_elements(By.CSS_SELECTOR, "app-channel-validation-card")


def card(driver, idx):
    """idx 0 = correo, idx 1 = celular."""
    wait(driver).until(lambda d: len(cards(d)) > idx)
    return cards(driver)[idx]


def card_badge(driver, idx):
    return card(driver, idx).find_element(By.CSS_SELECTOR, '[data-testid="state-badge"]').text


def request_otp_ui(driver, idx, value):
    c = card(driver, idx)
    c.find_element(By.CSS_SELECTOR, 'input[id$="-value"]').send_keys(value)
    wait(driver).until(
        lambda d: card(d, idx).find_element(By.CSS_SELECTOR, '[data-testid="send-otp"]').is_enabled()
    )
    card(driver, idx).find_element(By.CSS_SELECTOR, '[data-testid="send-otp"]').click()
    wait(driver).until(
        lambda d: card(d, idx).find_elements(By.CSS_SELECTOR, '[data-testid="mock-note"]')
    )


def confirm_otp_ui(driver, idx, otp="000000"):
    card(driver, idx).find_element(By.CSS_SELECTOR, 'input[id$="-otp"]').send_keys(otp)
    wait(driver).until(
        lambda d: card(d, idx).find_element(By.CSS_SELECTOR, '[data-testid="confirm-otp"]').is_enabled()
    )
    card(driver, idx).find_element(By.CSS_SELECTOR, '[data-testid="confirm-otp"]').click()
    wait(driver).until(
        lambda d: card(d, idx).find_elements(By.CSS_SELECTOR, '[data-testid="validated-msg"]')
    )


def identity_card(driver):
    return driver.find_element(By.CSS_SELECTOR, "app-identity-card")


def verify_identity_ui(driver):
    driver.find_element(By.CSS_SELECTOR, '[data-testid="terms"]').click()
    driver.find_element(By.CSS_SELECTOR, '[data-testid="mock-inputs"]').click()
    wait(driver).until(lambda d: tid(d, "verify").is_enabled())
    tid(driver, "verify").click()
    wait(driver).until(
        lambda d: identity_card(d).find_elements(By.CSS_SELECTOR, '[data-testid="validated-msg"]')
    )


def operation_type_select(driver):
    return Select(driver.find_element(By.ID, "operation_type"))


def submit_operation(driver, op_type, amount):
    operation_type_select(driver).select_by_value(op_type)
    set_text(driver, "amount", amount)
    wait(driver).until(lambda d: tid(d, "submit-operation").is_enabled())
    tid(driver, "submit-operation").click()
```

## `qa/ui/conftest.py`

```python
import os

import httpx
import pytest
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

from helpers import API_BASE_URL
from ui_helpers import register_via_ui


@pytest.fixture
def driver():
    opts = Options()
    if os.getenv("HEADLESS", "true").lower() == "true":
        opts.add_argument("--headless=new")
    opts.add_argument("--window-size=1280,1100")
    opts.set_capability("goog:loggingPrefs", {"browser": "ALL"})
    d = webdriver.Chrome(options=opts)  # Selenium Manager resuelve chromedriver
    d.implicitly_wait(0)
    yield d
    d.quit()


@pytest.fixture(scope="session")
def api_client():
    with httpx.Client(base_url=API_BASE_URL, timeout=15.0) as c:
        yield c


@pytest.fixture
def ui_user(driver):
    """Usuario registrado desde la UI; el navegador queda en /landing (sesión en memoria)."""
    return register_via_ui(driver)
```

## `qa/ui/test_onboarding_ui.py`

```python
"""CA-01 a CA-04 por interfaz (Angular) + integración con la API."""
import re

import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

from helpers import PASSWORD, register, unique_username
from ui_helpers import (
    UI_BASE_URL,
    WALLET_UUID_RE,
    field_message,
    field_state,
    register_via_ui,
    resource_urls,
    set_text,
    tid,
    wait,
    wait_state,
    wait_tid,
    wait_tid_text,
)


def open_onboarding(driver):
    driver.get(f"{UI_BASE_URL}/onboarding")
    wait(driver).until(EC.visibility_of_element_located((By.ID, "nombres")))


def wait_session_started(driver):
    wait(driver).until(lambda d: any(u.endswith("/onboarding/sessions") for u in resource_urls(d)))


def test_ui_onb_01_session_started_when_visible(driver):
    open_onboarding(driver)
    wait_session_started(driver)
    assert "Pasos completados: 0" in wait_tid(driver, "progress").text


def test_ui_onb_02_step_registered_on_blur(driver):
    open_onboarding(driver)
    wait_session_started(driver)
    set_text(driver, "nombres", "María José", tab=True)
    wait_tid_text(driver, "progress", "Pasos completados: 1")
    wait(driver).until(lambda d: any("/steps" in u for u in resource_urls(d)))


CASES = [
    ("nombres", "María José", "valid", "Válido"),
    ("nombres", "Maria123", "invalid", "Solo letras"),
    ("nombres", "a" * 31, "invalid", "Máximo 30"),
    ("apellido_paterno", "Quispe", "valid", "Válido"),
    ("apellido_paterno", "Quispe9", "invalid", "Solo letras"),
    ("apellido_paterno", "a" * 21, "invalid", "Máximo 20"),
    ("apellido_materno", "Rojas", "valid", "Válido"),
    ("apellido_materno", "Rojas9", "invalid", "Solo letras"),
    ("apellido_materno", "a" * 21, "invalid", "Máximo 20"),
    ("usuario", "12345", "invalid", "al menos una letra"),
    ("usuario", "a" * 21, "invalid", "Máximo 20"),
    ("password", "Abcdef123", "invalid", "Mínimo 10"),
    ("password", PASSWORD, "valid", "Válido"),
]


@pytest.mark.parametrize(
    "field_id,value,state,fragment",
    [pytest.param(*c, id=f"{c[0]}-{c[2]}-{i}") for i, c in enumerate(CASES)],
)
def test_ui_onb_03_inline_validation(driver, field_id, value, state, fragment):
    open_onboarding(driver)
    set_text(driver, field_id, value)  # sin salir del campo: validación mientras se escribe
    wait_state(driver, field_id, state)
    assert fragment in field_message(driver, field_id)


def test_ui_onb_04_password_strength_alert(driver):
    open_onboarding(driver)
    set_text(driver, "password", "abc")
    weak = wait_tid(driver, "strength")
    assert "débil" in weak.text
    assert weak.get_attribute("role") == "alert"
    set_text(driver, "password", PASSWORD)
    wait_tid_text(driver, "strength", "fuerte")


def test_ui_onb_05_available_username(driver):
    open_onboarding(driver)
    set_text(driver, "usuario", unique_username())
    wait_state(driver, "usuario", "valid")
    assert "Usuario disponible" in field_message(driver, "usuario")
    assert not tid(driver, "submit").is_enabled(), "el formulario aún está incompleto"


def test_ui_onb_06_taken_username_suggestions(driver, api_client):
    taken = register(api_client)
    open_onboarding(driver)
    set_text(driver, "nombres", "Juan")
    set_text(driver, "apellido_paterno", "Perez")
    set_text(driver, "apellido_materno", "Soto")
    set_text(driver, "usuario", taken.username)
    wait(driver).until(lambda d: d.find_elements(By.CSS_SELECTOR, '[data-testid="suggestions"] .chip'))
    assert field_state(driver, "usuario") == "invalid"
    chips = driver.find_elements(By.CSS_SELECTOR, '[data-testid="suggestions"] .chip')
    texts = [c.text for c in chips]
    print("Sugerencias en UI (revisión manual P-02):", texts)
    assert texts and all(re.fullmatch(r"[a-z0-9]{1,20}", t) for t in texts)
    chips[0].click()
    wait_state(driver, "usuario", "valid")
    assert driver.find_element(By.ID, "usuario").get_attribute("value") == texts[0]


def test_ui_onb_07_submit_disabled_initially(driver):
    open_onboarding(driver)
    assert not tid(driver, "submit").is_enabled()


def test_ui_onb_08_registration_and_landing(driver):
    user = register_via_ui(driver)
    assert "/landing" in driver.current_url
    assert "María José" in tid(driver, "welcome").text
    assert "Cuenta básica" in tid(driver, "status").text
    assert "S/ 0.00" in tid(driver, "account").text
    assert WALLET_UUID_RE.fullmatch(user["wallet_id"])
    row = tid(driver, "condition-row").text
    assert "S/ 20.00" in row and "S/ 60.00" in row
    banner = tid(driver, "pending-banner")
    assert banner.is_displayed()
    assert "perfil" in banner.text.lower()
    assert banner.find_element(By.TAG_NAME, "a").get_attribute("href").endswith("/profile")
    assert "Registro completado en" in tid(driver, "duration").text


def test_ui_onb_09_no_credentials_in_browser_storage_or_console(driver):
    user = register_via_ui(driver)
    storage = driver.execute_script(
        "return JSON.stringify([localStorage, sessionStorage, document.cookie]);"
    )
    assert user["password"] not in storage
    console = " ".join(entry["message"] for entry in driver.get_log("browser"))
    assert user["password"] not in console


def test_ui_onb_10_registration_persisted_in_api(driver, api_client):
    user = register_via_ui(driver)
    r = api_client.get(f"/wallets/{user['wallet_id']}", auth=(user["username"], user["password"]))
    assert r.status_code == 200
    body = r.json()
    assert body["account"]["status"] == "ACTIVE_BASIC"
    assert float(body["account"]["balance"]) == 0


def test_ui_onb_11_progress_shows_total(driver):
    # Detecta si se aplicó la corrección pendiente del template (de ${'{'}total{'}'} → de {{ total }}).
    open_onboarding(driver)
    text = wait_tid(driver, "progress").text
    assert "de 5" in text
    assert "${" not in text and "{{" not in text
```

## `qa/ui/test_profile_e2e.py`

```python
"""CA-06 a CA-13: perfil, OTP mock, identidad mock y topes desde la UI (E2E + verificación por API)."""
import time

import pytest
from selenium.webdriver.common.by import By

from helpers import (
    MOCK_BIOMETRIC_ENABLED,
    confirm_channel,
    register,
    requires_mock,
    requires_mock_disabled,
    unique_email,
    unique_phone,
)
from ui_helpers import (
    card,
    card_badge,
    confirm_otp_ui,
    identity_card,
    open_profile,
    operation_type_select,
    request_otp_ui,
    submit_operation,
    tid,
    verify_identity_ui,
    wait,
    wait_tid,
    wait_tid_text,
)

EMAIL, PHONE = 0, 1


def api_profile(api_client, user):
    r = api_client.get(f"/wallets/{user['wallet_id']}", auth=(user["username"], user["password"]))
    assert r.status_code == 200
    return r.json()


def send_button(driver, idx):
    return card(driver, idx).find_element(By.CSS_SELECTOR, '[data-testid="send-otp"]')


def test_ui_e2e_01_open_profile_from_landing(driver, ui_user):
    open_profile(driver)
    assert "Cuenta básica" in tid(driver, "status").text
    assert card_badge(driver, EMAIL) == "Pendiente"
    assert card_badge(driver, PHONE) == "Pendiente"
    assert "Pendiente" in identity_card(driver).find_element(By.CSS_SELECTOR, '[data-testid="state-badge"]').text


def test_ui_e2e_02_email_format_validation(driver, ui_user):
    open_profile(driver)
    c = card(driver, EMAIL)
    field = c.find_element(By.CSS_SELECTOR, 'input[id$="-value"]')
    field.send_keys("ana@@example")
    wait(driver).until(lambda d: card(d, EMAIL).find_elements(By.CSS_SELECTOR, '[data-testid="value-error"]'))
    assert not send_button(driver, EMAIL).is_enabled()
    field.clear()
    field.send_keys("ana.qa@example.com")
    wait(driver).until(lambda d: send_button(d, EMAIL).is_enabled())


def test_ui_e2e_03_phone_prefix_and_format(driver, ui_user):
    open_profile(driver)
    prefix = card(driver, PHONE).find_element(By.CSS_SELECTOR, '[data-testid="phone-prefix"]')
    assert prefix.get_attribute("value") == "+51"
    assert prefix.get_attribute("readonly") is not None
    field = card(driver, PHONE).find_element(By.CSS_SELECTOR, 'input[id$="-value"]')
    for bad in ("812345678", "91234567"):
        field.clear()
        field.send_keys(bad)
        assert not send_button(driver, PHONE).is_enabled()
    field.clear()
    field.send_keys(unique_phone())
    wait(driver).until(lambda d: send_button(d, PHONE).is_enabled())


def test_ui_e2e_04_phone_then_email_independent(driver, api_client, ui_user):
    open_profile(driver)
    request_otp_ui(driver, PHONE, unique_phone())
    confirm_otp_ui(driver, PHONE)
    assert card_badge(driver, PHONE) == "Validado"
    assert card_badge(driver, EMAIL) == "Pendiente"
    p = api_profile(api_client, ui_user)["profile"]
    assert p["estado_c2"] == "ACTIVE_MOVIL" and p["estado_c1"] == "PENDING_EMAIL"

    request_otp_ui(driver, EMAIL, unique_email())
    confirm_otp_ui(driver, EMAIL)
    assert card_badge(driver, EMAIL) == "Validado"
    p = api_profile(api_client, ui_user)["profile"]
    assert p == {"estado_c1": "ACTIVE_EMAIL", "estado_c2": "ACTIVE_MOVIL", "estado_c3": "PENDING_BIOM"}


def test_ui_e2e_05_mock_otp_and_resend_lock(driver, ui_user):
    open_profile(driver)
    request_otp_ui(driver, EMAIL, unique_email())
    note = card(driver, EMAIL).find_element(By.CSS_SELECTOR, '[data-testid="mock-note"]').text
    assert "no se envía ningún correo real" in note
    btn = send_button(driver, EMAIL)
    assert not btn.is_enabled()
    assert "Reenviar en" in btn.text
    confirm_otp_ui(driver, EMAIL, "abcdef")  # el mock acepta cualquier valor
    assert card_badge(driver, EMAIL) == "Validado"


def test_ui_e2e_06_email_already_registered(driver, api_client, ui_user):
    owner = register(api_client)
    taken_email = confirm_channel(api_client, owner, "email")
    open_profile(driver)
    c = card(driver, EMAIL)
    c.find_element(By.CSS_SELECTOR, 'input[id$="-value"]').send_keys(taken_email)
    wait(driver).until(lambda d: send_button(d, EMAIL).is_enabled())
    send_button(driver, EMAIL).click()
    wait(driver).until(lambda d: card(d, EMAIL).find_elements(By.CSS_SELECTOR, '[data-testid="card-error"]'))
    err = card(driver, EMAIL).find_element(By.CSS_SELECTOR, '[data-testid="card-error"]').text
    assert "ya está registrado" in err
    assert not card(driver, EMAIL).find_elements(By.CSS_SELECTOR, '[data-testid="mock-note"]')


@requires_mock
def test_ui_e2e_07_identity_mock_activation(driver, api_client, ui_user):
    open_profile(driver)
    notice = identity_card(driver).find_element(By.CSS_SELECTOR, '[data-testid="clarity-notice"]').text
    assert "nítidas" in notice
    assert not tid(driver, "verify").is_enabled()
    verify_identity_ui(driver)
    wait_tid_text(driver, "status", "Cuenta completa")
    p = api_profile(api_client, ui_user)
    assert p["account"]["status"] == "ACTIVE_FULL"
    assert p["profile"] == {
        "estado_c1": "PENDING_EMAIL",
        "estado_c2": "PENDING_MOVIL",
        "estado_c3": "ACTIVE_BIOM",
    }
    wait(driver).until(lambda d: len(d.find_elements(By.CSS_SELECTOR, '[data-testid="condition-row"]')) == 2)
    rows = " ".join(r.text for r in driver.find_elements(By.CSS_SELECTOR, '[data-testid="condition-row"]'))
    assert "S/ 1,000.00" in rows and "S/ 500.00" in rows and "Sin tope" in rows


@requires_mock
def test_ui_e2e_08_full_journey(driver, api_client, ui_user):
    open_profile(driver)
    request_otp_ui(driver, EMAIL, unique_email())
    confirm_otp_ui(driver, EMAIL)
    request_otp_ui(driver, PHONE, unique_phone())
    confirm_otp_ui(driver, PHONE)
    verify_identity_ui(driver)
    wait_tid_text(driver, "status", "Cuenta completa")
    p = api_profile(api_client, ui_user)
    assert p["account"]["status"] == "ACTIVE_FULL"
    assert p["profile"] == {
        "estado_c1": "ACTIVE_EMAIL",
        "estado_c2": "ACTIVE_MOVIL",
        "estado_c3": "ACTIVE_BIOM",
    }


def test_ui_e2e_09_basic_operations_and_limits(driver, ui_user):
    open_profile(driver)
    wait(driver).until(lambda d: len(operation_type_select(d).options) == 2)
    submit_operation(driver, "PAYMENT", "20.00")
    ok = wait_tid_text(driver, "operation-ok", "Acumulado del día: S/ 20.00")
    assert "S/ 60.00" in ok.text
    submit_operation(driver, "PAYMENT", "20.01")
    wait_tid_text(driver, "operation-error", "tope por operación")
    submit_operation(driver, "TOPUP_OWN", "20.00")
    wait_tid_text(driver, "operation-ok", "Acumulado del día: S/ 40.00")
    submit_operation(driver, "PAYMENT", "20.00")
    wait_tid_text(driver, "operation-ok", "Acumulado del día: S/ 60.00")
    submit_operation(driver, "PAYMENT", "1.00")
    wait_tid_text(driver, "operation-error", "tope diario")


@requires_mock
def test_ui_e2e_10_full_operations(driver, ui_user):
    open_profile(driver)
    verify_identity_ui(driver)
    wait(driver).until(lambda d: len(operation_type_select(d).options) == 3)
    submit_operation(driver, "TOPUP_THIRD_PARTY", "1000.00")
    ok = wait_tid_text(driver, "operation-ok", "S/ 1,000.00")
    assert "Recarga de terceros" in ok.text
    submit_operation(driver, "TOPUP_THIRD_PARTY", "0.01")
    wait_tid_text(driver, "operation-error", "tope diario")


@requires_mock_disabled
def test_ui_e2e_11_mock_unavailable_in_other_env(driver, ui_user):
    open_profile(driver)
    msg = wait_tid(driver, "mock-unavailable").text
    assert "desarrollo y pruebas" in msg
    assert not driver.find_elements(By.CSS_SELECTOR, '[data-testid="verify"]')


@pytest.mark.slow
def test_ui_e2e_12_resend_enabled_after_45s(driver, ui_user):
    open_profile(driver)
    t0 = time.monotonic()
    request_otp_ui(driver, EMAIL, unique_email())
    assert not send_button(driver, EMAIL).is_enabled()
    time.sleep(max(0.0, 46 - (time.monotonic() - t0)))
    wait(driver, 5).until(lambda d: send_button(d, EMAIL).is_enabled())
```

---

## Resumen de lo que queda pendiente para cerrar el ciclo de pruebas

1. **Ejecutar** los comandos de la sección 5 del informe y completar la columna "Estado" con `EJECUTADO - PASA` o `EJECUTADO - FALLA`, adjuntando las salidas (`results/*.xml`). Hoy todo está **NO EJECUTADO**.
2. **Confirmar con Backend** el comando de arranque y la ruta de la BD (G-01), la existencia del YAML del contrato (G-03) y los valores aceptados de `APP_ENV` (G-10).
3. **Confirmar con Frontend** que `npm run build` compila (G-07) y que se aplicó la corrección del template de progreso (G-08).
4. **Pruebas no automatizables hoy:**
   - reinicio diario (G-04),
   - parametrización de topes (G-05),
   - invalidación directa de OTP (G-06),
   - ausencia de llamadas de red salientes (P-04),
   - ausencia de analítica (P-05).

   Cada una indica en el informe qué se necesita para completarla.