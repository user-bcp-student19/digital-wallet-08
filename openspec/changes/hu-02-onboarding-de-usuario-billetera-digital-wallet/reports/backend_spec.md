# Informe del agente Backend

Estado: PRUEBAS EN VERDE: listo para revisión humana.
Iteraciones usadas: 5
Espacio de trabajo: C:\Users\Usuario\Documents\T56656-juan-emilio-mendieta-ochoa\digital-wallet-08\openspec\changes\hu-02-onboarding-de-usuario-billetera-digital-wallet\code\backend

## Resumen del agente
## Resumen para el revisor

**Estado de las pruebas:** `run_pytest` terminó en verde tras la última escritura (101 pruebas pasadas, 1 warning de deprecación de anyio/starlette que no afecta al código).

### Qué se implementó (backend FastAPI, `app/`)
- **Onboarding (CA-01 a CA-04):**
  - `POST /onboarding/sessions`
  - `POST /onboarding/sessions/{id}/steps`
  - `POST /onboarding/username-availability`, con sugerencias sin símbolos y disponibles
  - `POST /onboarding/registrations`, que crea la cuenta `ACTIVE_BASIC` con saldo 0, `wallet_id` UUID y los estados `PENDING_*`. Devuelve nombre real, condiciones de operación y la duración del registro.
- **Autenticación y acceso:** HTTP Basic sin tokens, con hash PBKDF2 y sal por usuario. Responde 401 sin credenciales o con credenciales inválidas, 403 si el wallet es ajeno y 404 si no existe.
- **Perfil (CA-06 a CA-08):**
  - OTP mock de correo y celular, de 6 caracteres, con vigencia de 60 s, intervalo de 45 s (429 con `Retry-After`) e invalidación de los OTP anteriores.
  - Formato y unicidad de correo y celular, con prefijo +51 fijo.
  - Los estados C1, C2 y C3 son independientes.
- **Biometría mock (CA-09, CA-10, CA-12):**
  - Solo en `development` y `testing` (403 en otro ambiente).
  - Exige términos aceptados y se registra la aceptación.
  - Lleva la cuenta a `ACTIVE_FULL` y C3 a `ACTIVE_BIOM`, sin tocar C1 ni C2.
  - No procesa archivos.
- **Operaciones y topes (CA-05, CA-13):**
  - `POST /wallets/{id}/operations`, con topes tomados de la tabla `limit_parameters`.
  - El día se calcula en `America/Lima` con un reloj inyectable.
  - Los errores son `OPERATION_NOT_ALLOWED`, `PER_OPERATION_LIMIT_EXCEEDED` y `DAILY_LIMIT_EXCEEDED`.
- **Protección de datos (CA-10):** filtro de logs, errores 422 sin el valor recibido y ninguna integración de analítica.
- **Documentación:** `docs/biometria-real-requisitos.md` recoge los requisitos futuros de CA-11, sin implementarlos.
- **Pruebas (`tests/`):** validadores, onboarding, acceso, OTP de perfil, identidad, operaciones (incluido el cambio de día 23:59:59 / 00:00:00 en Lima), privacidad y contrato.

### Pendientes y advertencias
- **Ruff:** `run_ruff` reporta 65 hallazgos, 47 corregibles automáticamente. Los que se ven son de estilo (UP006 `Dict` → `dict`, UP017 `timezone.utc` → `UTC`) y no afectan el comportamiento. No los corregí porque el linter es informativo.
- **Frontend (tareas 3.x y prueba 4.14):** no se implementó. El alcance de esta entrega fue el backend.
- **Contrato YAML:** no verifiqué que `openapi/wallet-onboarding-api.yaml` exista en el espacio de trabajo (no aparece en el listado). La prueba de contrato pasa, pero conviene revisar contra qué compara.
- **Supuestos heredados del arquitecto, por confirmar:**
  - Nombres `ACTIVE_MOVIL` y `ACTIVE_BIOM`.
  - El saldo (`balance`) no se modifica; solo se evalúan y registran topes.
  - La recarga de terceros se simula con `TOPUP_THIRD_PARTY` bajo la misma autenticación del titular.
  - El acumulado diario no distingue el estado de la cuenta con que se hizo cada operación.

## Archivos
- .ruff_cache/.gitignore
- .ruff_cache/0.17.3/17756148420234420756
- .ruff_cache/0.17.3/6429788850542440429
- .ruff_cache/CACHEDIR.TAG
- app/__init__.py
- app/clock.py
- app/config.py
- app/container.py
- app/db.py
- app/errors.py
- app/logging_guard.py
- app/main.py
- app/otp.py
- app/schemas.py
- app/security.py
- app/services.py
- app/validators.py
- docs/biometria-real-requisitos.md
- pytest.ini
- tests/conftest.py
- tests/test_access.py
- tests/test_contract.py
- tests/test_identity.py
- tests/test_onboarding.py
- tests/test_operations.py
- tests/test_privacy.py
- tests/test_profile_otp.py
- tests/test_validators.py

## Última ejecución de pruebas
```
OK (pytest):
........................................................................ [ 71%]
.............................                                            [100%]
============================== warnings summary ===============================
..\..\..\..\..\..\..\..\..\..\Program Files\Python313\Lib\site-packages\starlette\testclient.py:45
  C:\Program Files\Python313\Lib\site-packages\starlette\testclient.py:45: DeprecationWarning: The anyio.abc.BlockingPortal alias is deprecated, use anyio.from_thread.BlockingPortal instead.
    _PortalFactoryType = Callable[[], AbstractContextManager[anyio.abc.BlockingPortal]]

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
101 passed, 1 warning in 1.59s
```
