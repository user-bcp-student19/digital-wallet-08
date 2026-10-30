# Revisión Chapter de Ingenieria de Software

VEREDICTO: RECHAZADO

Fecha de la revisión: 2026-10-30. Feature: HU 01 – Onboarding de usuario, billetera digital (Wallet).

Este veredicto es una recomendación técnica basada en revisión estática de las entregas `architect.md`, `backend.md`, `frontend.md` y `testing.md`. La decisión de aceptación sigue siendo de las personas responsables del flujo.

**Estado de la evidencia.** Ninguna entrega aporta resultados de ejecución.
- `backend.md` declara: "No ejecuté el código ni las pruebas".
- `frontend.md` declara: "No ejecuté el código ni lo probé contra el backend".
- `testing.md` marca todo como NO EJECUTADO.
- Esta revisión tampoco ejecutó nada.

Por eso, en este documento "CUMPLE" significa solo "cumple según lectura del código". No existe ningún resultado verificado.

---

## Motivos del veredicto

1. **Topes de CA-05 y CA-13 incorrectos respecto a la HU (contrato incompatible entre entregas).**
   - `architect.md` §4 fija los valores de la HU: ACTIVE_BASIC S/20 por operación y S/60 diarios (2000 y 6000 céntimos); ACTIVE_FULL recargas S/1,000 diarios, pagos S/500 por operación y S/1,000 diarios.
   - `backend.md` (`config.py`, `DEFAULT_LIMITS`) usa otros valores y afirma que "la HU no da cifras". Eso es falso.
   - El frontend muestra esos valores erróneos al usuario como "condiciones de las operaciones" (CA-03).
   - Detalle en H-01.

2. **CA-01 (validación mientras el usuario escribe) no se cumple en el frontend.**
   - Nombres y apellidos están dentro de `st.form`, así que solo se validan al pulsar "Continuar".
   - La disponibilidad de usuario se dispara con `on_change` (Enter o pérdida de foco). El propio texto de ayuda dice "Presiona Enter para validar".
   - La contraseña se valida solo al pulsar "Crear mi billetera".
   - Detalle en H-04.

3. **La robustez de la contraseña no está implementada en ningún componente (CA-02).**
   - `architect.md` supuesto 2 delega la regla al cliente.
   - `validators.validate_password` y `schemas.py` solo validan longitud de 8 a 64.
   - No hay alerta de robustez. Ver H-05.

4. **Autorización inexistente en endpoints sensibles.**
   - `security.require_bearer` acepta cualquier cadena tras `Bearer`.
   - Cualquiera que conozca un `accountId` puede leer la cuenta, solicitar y verificar OTP, registrar consentimiento y activar `ACTIVE_FULL`.
   - El `accountId` viaja además en la URL del frontend (`st.query_params`).
   - El backend no emite ningún token tras crear la cuenta (pregunta 6 de arquitectura, sin respuesta). Ver H-03.

5. **CA-10 incompleto.**
   - No existen controles de retención ni eliminación.
   - `otps.target` guarda correo y celular en claro.
   - Los términos no se muestran al usuario y la versión la escribe el propio cliente.
   - El log de acceso por defecto de uvicorn registra la query de `/usernames/availability` con nombres, apellidos y usuario, lo que contradice "no se registran en logs".
   - El TC-SEC-01 de `testing.md` no lo detectaría. Ver H-07 y H-08.

6. **CA-03 depende de un contrato externo sin confirmar.**
   - El contrato de `bcp-wallet-mock` llegó truncado.
   - El cuerpo del KYC (`first_names`, `paternal_surname`, `maternal_surname`), el campo `wallet_id` y el campo de saldo (`_BALANCE_KEYS` con 6 candidatos, incluidos `balance` y `amount_cents`) son supuestos del adaptador.
   - Una unidad errónea (soles frente a céntimos) mostraría un saldo incorrecto sin error. Ver H-06.

7. **Las pruebas de QA no cubren los criterios y son parcialmente incompatibles con el frontend.**
   - `testing.md` solo diseña CA-01. CA-02 a CA-13 no tienen prueba de QA diseñada.
   - Las pruebas Selenium observan la red del navegador mediante el log `performance` de Chrome. El frontend es Streamlit y llama a la API desde el servidor, así que esas peticiones no aparecen en ese log.
   - TC-UI-01, TC-UI-02, TC-UI-04 y TC-INT-01 no pueden observar lo que verifican.
   - Detalle en H-10 y H-11.

8. **Hallazgos adicionales.**
   - El flag del flujo mock está abierto por defecto (`WALLET_ENV` por defecto `development`).
   - Una aserción de `tests/test_onboarding_flow.py` probablemente falla.
   - `main.py` se entregó con un cierre contradictorio.
   - La contraseña queda en `st.session_state`, a pesar de lo que afirma el README.
   - Hay un desajuste de puertos (8000 frente a 8080).
   - Varias decisiones abiertas de arquitectura siguen sin respuesta.
   - Detalle en H-09 y H-12 a H-17.

**Lo que sí está sólido según lectura estática** (no verificado por ejecución):
- Modelo de errores sin eco de valores.
- Hash scrypt de contraseña.
- Orden de OTP: 60 s de vigencia, 45 s de reenvío e invalidación de anteriores.
- Unicidad de correo y celular.
- Gating del mock por ambiente en la ruta.
- Adaptador sin reintento de POST y sin propagación de `X-Mock-Latency-Ms`.
- Seguimiento de sesión con `durationMs` calculado por el servidor.

---

## Matriz de criterios de aceptación

Escala de resultado:
- **CUMPLE (estático)**: la lectura del código lo cubre, sin verificación.
- **PARCIAL**: hay cobertura con brechas.
- **NO CUMPLE**: contradice el criterio.
- **NO CUBIERTO**: no hay entrega que lo trate.

Persistencia: no se entregó un modelo de datos independiente. Se evalúa la persistencia implementada en `backend.md` (`db.py`, SQLite, esquema `SCHEMA` y repositorios). No hay migraciones ni definición de retención.

### CA-01 – Inicio y seguimiento
- **Arquitectura:** Servicio de Seguimiento (`POST /onboarding/sessions` y `/steps`). La validación en vivo se asigna al cliente.
- **Persistencia:** tabla `onboarding_sessions` (`started_at`, `ended_at`, `duration_ms`, `steps`, `completed`).
- **Implementación:**
  - Backend: `session_tracking.py` y `routers/onboarding.py`. El tiempo lo calcula el servidor. `LANDING_VISIBLE` cierra la sesión.
  - Frontend: `ensure_onboarding_session()` en `render_personal`, `report_step()` y `LANDING_VISIBLE` tras `load_summary()`.
  - La validación en vivo es parcial: nombres, apellidos y contraseña solo se validan al enviar (H-04).
- **Pruebas:** Karate TC-API-01 a 14, 20 a 27, 30, 31, 40 y 41 y Selenium TC-UI-01 a 04 y TC-INT-01, todas NO EJECUTADO. Los TC-UI son incompatibles con Streamlit (H-10).
- **Seguridad:** endpoints de sesión sin autenticación, `sessionId` UUID, sin PII en el modelo.
- **Resultado:** PARCIAL. CA-01-A, B y C cumplen (estático). CA-01-D no cumple.
- **Brechas:** H-04, H-10, y G-04/G-07 de `testing.md` (latencia entre visibilidad y llamada; `LANDING_VISIBLE` admitido sin pasos previos).

### CA-02 – Datos de registro
- **Arquitectura:** patrones y longitudes en `CreateAccountRequest`; `GET /usernames/availability`; `409 USERNAME_TAKEN` con sugerencias.
- **Persistencia:** `users` con `username_key UNIQUE` (minúsculas); `password_hash` scrypt.
- **Implementación:**
  - `schemas.py`: nombres máx. 30 con espacios simples, apellidos máx. 20 solo letras, usuario `^(?=.*[A-Za-z])[\x21-\x7E]{1,20}$`, contraseña 8 a 64.
  - `username.py`: sugerencias alfanuméricas de hasta 20 caracteres.
  - La robustez de contraseña y su alerta no existen (H-05).
  - La consulta de disponibilidad envía nombres y apellidos por query string (H-07).
- **Pruebas:** Karate TC-API-20 a 28, 30 y 31 y pytest `test_username_availability_and_conflict`, NO EJECUTADO. Sin prueba de robustez.
- **Seguridad:** el modelo de errores no refleja valores. La contraseña no va al KYC ni a logs de aplicación. El log de acceso de uvicorn expone nombres y usuario (H-07). Sin límite de tasa sobre disponibilidad, lo que permite enumerar usuarios.
- **Resultado:** PARCIAL.
- **Brechas:** H-04, H-05, H-07 y H-17 (usuario "alfabético" frente a imprimibles ASCII incluyendo dígitos; validar con negocio).

### CA-03 – Creación de cuenta básica
- **Arquitectura:** `POST /accounts` crea el wallet vía `POST /kyc/verifications`; `GET /accounts/{id}` lee el saldo de `GET /wallets/{wallet_id}`.
- **Persistencia:** `accounts` (`wallet_id UNIQUE`, `status`). El saldo no se replica, lo cual es coherente.
- **Implementación:**
  - `onboarding.py` crea la cuenta como `ACTIVE_BASIC`.
  - La landing saluda por `firstNames` y lista los límites.
  - Las URLs del adaptador coinciden con las de la HU.
  - Campos de KYC y saldo supuestos (H-06).
  - La cuenta queda con valores de límites incorrectos (H-01).
  - La medición cierra con `LANDING_VISIBLE`, que informa el cliente.
- **Pruebas:** pytest con `FakeWallet`; Karate TC-API-40 y 41 (`@requires-external`). NO EJECUTADO. Ninguna prueba toca el servicio real.
- **Seguridad:** la contraseña no se envía al KYC. Se envían nombres y apellidos al mock externo, lo cual es funcionalmente necesario pero debe confirmarse contra el contrato. Riesgo de wallet huérfano (decisión aceptada en arquitectura).
- **Resultado:** PARCIAL.
- **Brechas:** H-01, H-06, H-16 (wallet huérfano).

### CA-04 – Aviso de perfil pendiente
- **Arquitectura:** `profilePending` y `profilePendingMessage` en `AccountSummary`.
- **Persistencia:** `profiles` con estados `PENDING_*` por defecto.
- **Implementación:** `onboarding.get_summary` arma el mensaje; el frontend lo muestra con `st.warning` en `render_summary`.
- **Pruebas:** pytest asserta `profilePending is True`. No hay prueba del texto ni de la visibilidad en UI. NO EJECUTADO.
- **Seguridad:** sin hallazgos propios.
- **Resultado:** CUMPLE (estático).
- **Brechas:** ninguna propia, salvo el acceso por IDOR a la landing (H-03).

### CA-05 – Operaciones de `ACTIVE_BASIC`
- **Arquitectura:** Política de Límites con topes de la HU (S/20 por operación, S/60 diarios) y día en `America/Lima`. Pagos y recargas fuera de alcance de endpoints.
- **Persistencia:** `daily_usage` existe, pero ningún código escribe en ella (solo `get_daily_usage`).
- **Implementación:**
  - `config.py` usa topes distintos a la HU (H-01).
  - No existen endpoints de pago ni de recarga.
  - Nada aplica ni consume topes (H-02).
  - El cálculo del día en `America/Lima` en `get_summary` sí es correcto.
- **Pruebas:** ninguna valida valores de topes, aplicación ni cambio de día.
- **Seguridad:** n/a.
- **Resultado:** NO CUMPLE.
- **Brechas:** H-01, H-02, H-16 (S/60 combinado o por tipo).

### CA-06 – Registro complementario
- **Arquitectura:** `ProfileStatus` con endpoints independientes para correo, celular y biometría, sin orden impuesto.
- **Persistencia:** `profiles` con `email_status`, `mobile_status` y `biometric_status`.
- **Implementación:** estados iniciales `PENDING_EMAIL`, `PENDING_MOVIL` y `PENDING_BIOM` conformes. Los estados activos `ACTIVE_MOVIL` y `ACTIVE_BIOM` son supuestos de arquitectura. El frontend ofrece las tres pestañas en cualquier orden.
- **Pruebas:** pytest verifica los estados iniciales. NO EJECUTADO.
- **Seguridad:** acceso sin autorización por cuenta (H-03).
- **Resultado:** CUMPLE (estático), con nombres de estados activos pendientes de confirmar.
- **Brechas:** H-16.

### CA-07 – Validación de correo
- **Arquitectura:** `POST /email/otp` y `/email/otp/verification`, con OTP mock.
- **Persistencia:** `otps` (`code_hash` HMAC con pepper, `expires_at`, `state`); `profiles.email UNIQUE`.
- **Implementación:**
  - `otp.py`: vigencia 60 s, solicitud cada 45 s (429 con `Retry-After`), invalidación de anteriores.
  - `profile.py`: formato de correo, unicidad y `ACTIVE_EMAIL`.
  - El OTP mock se escribe en el log fuera de producción (pregunta 4 de arquitectura resuelta de hecho así).
- **Pruebas:** pytest `test_email_otp_rules` (probablemente correcto, NO EJECUTADO). Sin Karate ni Selenium para este criterio.
- **Seguridad:**
  - `otps.target` guarda el correo en claro y sin purga.
  - El OTP y el `accountId` van al log fuera de producción (aceptable solo en dev y test, y debe documentarse).
  - Vulnerable al acceso sin autorización por cuenta (H-03).
- **Resultado:** CUMPLE (estático), condicionado a H-03 y H-08.
- **Brechas:** H-03, H-08.

### CA-08 – Validación de celular
- **Arquitectura:** `POST /mobile/otp` y verificación, con prefijo +51 fijo y `^9[0-9]{8}$`.
- **Persistencia:** `profiles.mobile UNIQUE`; `otps.target` con el número.
- **Implementación:** `request_mobile_otp` antepone `+51`. La UI muestra el prefijo solo dentro de la etiqueta "Celular (+51)", no como componente fijo.
- **Pruebas:** pytest `test_mobile_otp_and_biometric_flow` cubre solo el camino feliz. NO EJECUTADO. Sin pruebas de 429, expiración ni duplicado para celular.
- **Seguridad:** igual que CA-07.
- **Resultado:** CUMPLE (estático), condicionado a H-03 y H-08.
- **Brechas:** H-03, H-08, cobertura de pruebas (H-11).

### CA-09 – Alcance de biometría
- **Arquitectura:** mock solo en dev y test (`404 MOCK_NOT_AVAILABLE` en otros ambientes). CA-11 no implementado.
- **Persistencia:** `profiles.biometric_status`. No se persiste DNI ni se almacenan fotos o videos.
- **Implementación:** `BiometricMockService` y `require_mock_enabled`. Solo valida un DNI de 8 dígitos y lo descarta. Pero `WALLET_ENV` tiene por defecto `development`, así que el flujo está abierto si no se configura (H-09).
- **Pruebas:** pytest `test_biometric_not_available_in_production`. NO EJECUTADO.
- **Seguridad:** apertura por defecto del mock (H-09).
- **Resultado:** PARCIAL.
- **Brechas:** H-09.

### CA-10 – Datos personales
- **Arquitectura:** consentimiento versionado; controles de acceso, protección, retención y eliminación "a nivel de Persistencia".
- **Persistencia:** tabla `consents`.
  - No hay retención, purga de `otps`, eliminación de usuario ni cifrado de PII.
  - La BD por defecto es un archivo local sin controles.
- **Implementación:**
  - Consentimiento: `POST /consents`. El frontend muestra un checkbox sin texto ni enlace a términos, y la versión es un campo editable por el usuario (H-08).
  - Logs: se sanitizan los de aplicación, pero el log de acceso de uvicorn expone la query de disponibilidad (H-07).
- **Pruebas:** TC-SEC-01 busca solo `S3cret!pass` y `Zq9!x` en `qa-server.log`; no busca nombres, apellidos, usuario, correo ni celular. NO EJECUTADO.
- **Seguridad:** controles de acceso insuficientes (H-03); datos de contacto en claro.
- **Resultado:** NO CUMPLE.
- **Brechas:** H-03, H-07, H-08.

### CA-11 – Documentos y video (futura integración)
- **Arquitectura:** requisitos documentados (2 MB, video de 5 a 10 s y 10 MB, metadatos de 10 min), sin endpoints.
- **Persistencia:** ninguna, correcto para el alcance.
- **Implementación:** ninguna. La UI no indica "imágenes nítidas" y no existe artefacto de documentación fuera de `architect.md`.
- **Pruebas:** ninguna, coherente con el alcance.
- **Seguridad:** n/a.
- **Resultado:** NO CUBIERTO por diseño ("estos requisitos no implican implementar").
- **Brechas:** requiere aceptación explícita humana del diferimiento (H-16).

### CA-12 – Activación completa simulada
- **Arquitectura:** `MockBiometricResult` con `ACTIVE_FULL`.
- **Persistencia:** `activate_biometric` actualiza `profiles` y `accounts.status` en una transacción.
- **Implementación:**
  - Exige consentimiento previo y devuelve 409 si ya es FULL.
  - No exige correo ni celular validados (pregunta 3 de arquitectura abierta).
  - Los límites devueltos para FULL son incorrectos (H-01).
- **Pruebas:** pytest comprueba `ACTIVE_FULL`, `ACTIVE_BIOM` y `allowsThirdPartyRecharge`. NO EJECUTADO.
- **Seguridad:** activación sin autorización por cuenta (H-03).
- **Resultado:** PARCIAL.
- **Brechas:** H-01, H-03, H-16.

### CA-13 – Operaciones de `ACTIVE_FULL`
- **Arquitectura:** recargas hasta S/1,000 diarios; pagos S/500 por operación y S/1,000 diarios (100000 y 50000 céntimos).
- **Persistencia:** `daily_usage` sin escritura.
- **Implementación:** `config.py` usa S/5,000 diarios de recarga, S/1,000 por pago y S/3,000 diarios de pago. Sin endpoints ni aplicación de topes.
- **Pruebas:** ninguna cubre valores de límites ni cambio de día.
- **Seguridad:** n/a.
- **Resultado:** NO CUMPLE.
- **Brechas:** H-01, H-02.

---

## Contratos incompatibles y hallazgos pendientes

### H-01 – Topes de `ACTIVE_BASIC` y `ACTIVE_FULL` incompatibles entre HU, arquitectura y backend (bloqueante)
- **Evidencia.**
  - `architect.md` §4 (CA-05, CA-13) y la HU fijan los valores siguientes.
  - `backend.md` `DEFAULT_LIMITS` usa los de la columna "Backend".
  - El README del backend dice "la HU no da cifras".

| Estado / concepto | HU y arquitectura | Backend |
|---|---|---|
| BASIC, por operación | S/20 (2,000) | recarga 30,000 (S/300); pago 20,000 (S/200) |
| BASIC, diario | S/60 (6,000) | recarga 60,000 (S/600); pago 40,000 (S/400) |
| FULL, recarga diaria | S/1,000 (100,000) | 500,000 (S/5,000) |
| FULL, pago por operación | S/500 (50,000) | 100,000 (S/1,000) |
| FULL, pago diario | S/1,000 (100,000) | 300,000 (S/3,000) |
| FULL, recarga por operación | no definido | 200,000 |

  El frontend (`render_summary`) muestra esos valores al usuario.
- **Responsable.** Backend (`config.py`, README). Frontend, solo para validar que muestre lo correcto.
- **Cambio requerido.**
  - Alinear `DEFAULT_LIMITS` con la HU.
  - Dejar en `None` el tope por operación de recarga de FULL, que la HU no define.
  - Corregir el README.
  - Añadir prueba que asserte los valores.
- **Verificación.**
  - Prueba pytest nueva (no existe, no hay comando propio) sobre `GET /v1/accounts/{id}`. Debe comparar `limits` con los valores de la HU para BASIC y para FULL tras la biometría mock.
  - Ejecutarla con `pytest -q` desde `wallet-api/`. Resultado pendiente.

### H-02 – Los topes no se aplican y `daily_usage` nunca se escribe
- **Evidencia.**
  - No hay endpoints de pago ni recarga (arquitectura §1, fuera de alcance).
  - `LimitsPolicy` solo devuelve configuración.
  - `daily_usage` solo se lee en `AccountRepository.get_daily_usage`.
  - CA-05 y CA-13 describen operaciones que la cuenta "puede" realizar y un contador que se reinicia por día.
- **Responsable.** Arquitectura y Producto (decidir alcance); Backend (implementar si aplica).
- **Cambio requerido.**
  - Decisión explícita: o se difiere la aplicación a otra HU, con aceptación humana documentada, o se implementa.
  - Si se implementa: verificación y consumo atómicos por operación y por día de `America/Lima`, para pagos y recargas.
  - Aclarar si S/60 es un acumulado combinado o por tipo (pregunta 2 de arquitectura).
- **Verificación.**
  - Pruebas con reloj falso en 23:59 y 00:00 de Lima y con la operación en el tope.
  - No se proporcionó comando para estas pruebas, que no existen.

### H-03 – Autorización inexistente (acceso a cuentas ajenas, activación FULL por cualquiera)
- **Evidencia.**
  - `security.py`: solo exige una cabecera `Bearer <algo>`.
  - Los endpoints reciben `accountId` por ruta sin comprobar propiedad.
  - `POST /accounts` no emite token.
  - El frontend guarda el `accountId` en la URL y trae `dev-token` por defecto.
  - `architect.md` supuesto 8 y pregunta 6 dejan el mecanismo fuera de alcance, sin respuesta.
- **Responsable.** Arquitectura (definir el mecanismo mínimo); Backend; Frontend.
- **Cambio requerido.**
  - Emitir una credencial ligada a la cuenta al crearla, o validar propiedad de otro modo.
  - Rechazar con 403 o 404 cuando el token no corresponda a `accountId`.
  - Aplicar lo mismo al mock biométrico.
  - Dejar de depender del `accountId` en la URL como credencial implícita.
  - Si se decide mantener un esquema simulado para esta entrega, documentarlo y obtener aceptación humana explícita del riesgo, porque CA-12 habilita operaciones reales.
- **Verificación.**
  - Prueba: token A sobre cuenta B devuelve 403 o 404 en `GET /accounts/{id}`, en OTP, en consentimiento y en biometría mock.
  - Prueba Karate equivalente. No se proporcionó comando; la prueba no existe.

### H-04 – CA-01-D: la validación en vivo no existe en el frontend
- **Evidencia.**
  - `app.py` `render_personal` usa `st.form` y valida solo al enviar.
  - `render_credentials` valida el usuario con `on_change` (Enter o blur), con ayuda "Presiona Enter para validar".
  - La contraseña se valida solo en el clic.
- **Responsable.** Frontend.
- **Cambio requerido.**
  - Mostrar el resultado de validación por campo durante la edición. Por ejemplo, sacar los campos del `st.form` y validar en callbacks, o usar un componente que emita eventos por pulsación.
  - Mostrar feedback de contraseña (longitud y robustez) en vivo.
  - Si la tecnología impide validar por pulsación, documentar el comportamiento y obtener aceptación humana del criterio.
- **Verificación.** Prueba de UI que escriba un valor inválido y compruebe el mensaje sin enviar el formulario. Selenium con selectores reales, comando en "Pruebas pendientes". Resultado pendiente.

### H-05 – Robustez de contraseña no implementada
- **Evidencia.** `architect.md` supuesto 2 ("se evalúa en el cliente"). `validators.validate_password` y `CreateAccountRequest.password` solo validan longitud. CA-02 exige validar robustez y alertar.
- **Responsable.** Arquitectura (definir la regla); Frontend (indicador y alerta); Backend (decidir si rechaza contraseñas débiles).
- **Cambio requerido.** Definir la regla de robustez, implementar el indicador y la alerta en vivo, y añadir las pruebas.
- **Verificación.** Pruebas unitarias de `validators` con contraseñas débiles y fuertes, y prueba de UI. No hay comando entregado.

### H-06 – Contrato externo `bcp-wallet-mock` sin confirmar
- **Evidencia.**
  - `architect.md` §3: el contrato está truncado; faltan los esquemas `Kyc` y `Wallet`.
  - `wallet_mock.py` supone el cuerpo del KYC, `wallet_id` en la respuesta y varias claves candidatas para el saldo (`_BALANCE_KEYS`).
  - El README del backend lo reconoce como supuesto.
- **Responsable.** Arquitectura (obtener el contrato completo); Backend (adaptar el adaptador).
- **Cambio requerido.**
  - Fijar los campos exactos del KYC, de `wallet_id` y del saldo, con su unidad.
  - Reducir `_BALANCE_KEYS` a la clave real.
  - Eliminar el comportamiento de "adivinar" y fallar de forma explícita ante una forma inesperada.
- **Verificación.**
  - Ejecutar contra el servicio real: `WALLET_API_URL=http://localhost:8000 WALLET_OTP_FIXED_CODE=123456 python smoke_test.py` (README del frontend), más Karate TC-API-40 (`@requires-external`).
  - Ambos pendientes. Cada ejecución crea wallets sin posibilidad de baja (G-09).

### H-07 – Datos personales en logs de acceso y TC-SEC-01 insuficiente
- **Evidencia.**
  - `routers/onboarding.py` `GET /usernames/availability` recibe `username`, `firstNames`, `paternalSurname` y `maternalSurname` por query string.
  - El middleware propio registra solo la ruta, pero el comando documentado (`uvicorn app.main:get_app --factory --port ...`) deja activo el log de acceso por defecto, que incluye la query.
  - `testing.md` §7.2 captura esa salida con `tee qa-server.log`.
  - §7.6 solo busca `S3cret!pass` y `Zq9!x`.
- **Responsable.** Backend (diseño del endpoint y arranque); QA (TC-SEC-01).
- **Cambio requerido.**
  - Mover los datos personales a POST con cuerpo, o calcular sugerencias sin recibirlos, o desactivar y redactar el log de acceso (por ejemplo `--no-access-log`) y documentarlo.
  - Ampliar TC-SEC-01 para buscar también nombres, apellidos, usuario, correo y celular sintéticos.
- **Verificación.**
  - Tras ejecutar el flujo, `grep -c "Quispe" qa-server.log` y equivalentes para los demás valores sintéticos. El resultado esperado es 0 en todos.
  - El comando para esos valores no está en `testing.md`.
  - Pendiente.

### H-08 – CA-10: controles de retención y eliminación ausentes; consentimiento débil
- **Evidencia.**
  - `db.py`: `otps.target` en claro, sin purga ni retención; no hay eliminación de usuario.
  - `architect.md` pregunta 8 (plazos y procedimientos) sin respuesta.
  - Frontend `biometric_section`: checkbox sin texto de términos; la "Versión de términos" es un `text_input` editable.
  - `ConsentService` acepta cualquier versión.
- **Responsable.** Arquitectura (retención, términos); Backend; Frontend.
- **Cambio requerido.**
  - Definir y documentar plazos de retención.
  - Implementar purga de OTP vencidos y un mecanismo de eliminación o anonimización.
  - Mostrar el texto de términos y fijar la versión desde el servidor o la configuración, no desde el usuario.
  - Considerar guardar solo un hash del destino del OTP.
- **Verificación.**
  - Pruebas sobre la purga de OTP vencidos y sobre el rechazo de versiones no vigentes.
  - Revisión manual de que la UI muestra los términos.
  - No se proporcionó comando.

### H-09 – Flags de ambiente abiertos por defecto
- **Evidencia.** `Settings.environment` por defecto `development` y `from_env` usa `WALLET_ENV` con ese valor por defecto. El flujo biométrico mock y el log de OTP quedan habilitados si no se configura. `otp_pepper` por defecto `change-me-in-prod` sin validación al arrancar.
- **Responsable.** Backend.
- **Cambio requerido.**
  - Valor por defecto restrictivo (producción).
  - Fallar al arrancar fuera de dev y test con el pepper por defecto.
  - Exigir `WALLET_ENV` explícito.
- **Verificación.** Prueba que arranque sin `WALLET_ENV` y compruebe `404 MOCK_NOT_AVAILABLE`. No hay comando entregado; la prueba existente solo cubre `environment="production"` explícito.

### H-10 – Selenium incompatible con la arquitectura del frontend Streamlit
- **Evidencia.**
  - `testing.md` G-01 declara que no se recibió especificación del frontend.
  - `NetworkRecorder` usa el log `performance` de Chrome (solo ve peticiones del navegador).
  - El README del frontend indica que Streamlit llama a la API desde el servidor.
  - `test_ui_01`, `test_ui_02`, `test_ui_04` y `test_int_01` dependen de ver `POST/GET` hacia la API.
  - `locators.json` exige selectores y URL aún sin definir; Streamlit no ofrece `data-testid` estables.
- **Responsable.** QA, con apoyo de Frontend para identificadores estables.
- **Cambio requerido.**
  - Rediseñar la verificación de CA-01-A y C: observar el efecto en el backend (por ejemplo, un `GET` de sesión; G-02 pide ese endpoint) o con registro del lado servidor, en lugar de la red del navegador.
  - Mantener Selenium para validación visible por campo, con selectores reales de Streamlit.
- **Verificación.** Ejecutar la suite revisada. Resultado pendiente.

### H-11 – Cobertura de pruebas insuficiente y todo sin ejecutar
- **Evidencia.**
  - `testing.md` §1 y §9: solo CA-01 diseñado; CA-02 a CA-13 sin diseñar.
  - Sin prueba para topes, cambio de día en Lima, robustez de contraseña, retención, flujo completo en UI ni seguridad de acceso.
  - Todas las pruebas figuran como NO EJECUTADO.
  - Incoherencia de conteo en `testing.md`: la tabla de resumen indica 20 + 3 pruebas Karate y el resumen operativo 24 + 4; la lista real de IDs son 24 sin servicio externo (TC-API-01 a 14, 20 a 27, 30, 31) y 3 con él (28, 40, 41).
- **Responsable.** QA.
- **Cambio requerido.**
  - Ampliar el alcance a CA-02 a CA-13 con trazabilidad, en particular topes, Lima, OTP de celular (429, expiración, duplicado), consentimiento, mock en producción y autorización.
  - Corregir los conteos.
  - Adjuntar los resultados reales de ejecución.
- **Verificación.** Matriz de trazabilidad con resultado observado por prueba y su reporte (`target/karate-reports/karate-summary.html`, `report-ui.xml`, salida de `pytest`).

### H-12 – Aserción probablemente defectuosa en `tests/test_onboarding_flow.py`
- **Evidencia.**
  - `assert "short" not in bad.text`.
  - El manejador devuelve `fields[].rule` con el tipo de Pydantic, previsiblemente `string_too_short`, que contiene "short". `testing.md` §4 ya lo señala.
- **Responsable.** Backend.
- **Cambio requerido.** Usar un valor centinela que no coincida con nombres de regla, como hacen las pruebas Karate (`Zq9!x`).
- **Verificación.** `pytest -q` desde `wallet-api/`. Pendiente.

### H-13 – La contraseña queda en `st.session_state` (el README del frontend afirma lo contrario)
- **Evidencia.**
  - `st.text_input("Contraseña", key="pwd")` y `key="pwd2"` almacenan el valor en `st.session_state`.
  - `payload["password"] = pwd = ""` solo limpia variables locales.
  - `reset_flow` las elimina solo si el usuario reinicia el flujo.
  - El README del frontend dice: "la contraseña nunca se guarda en session_state".
- **Responsable.** Frontend.
- **Cambio requerido.** Eliminar `pwd` y `pwd2` de `session_state` tras crear la cuenta (con `pop`) o con `st.form(clear_on_submit=True)`. Corregir la afirmación del README.
- **Verificación.** Inspección del código y prueba que compruebe que `pwd` no existe en `session_state` tras el alta. No se proporcionó comando.

### H-14 – `main.py` entregado con cierre contradictorio
- **Evidencia.** El bloque de `main.py` en `backend.md` termina con `app = create_app() if __name__ != "__main__" and False else None  # placeholder` y una nota que pide sustituir el cierre. El archivo entregado y el corregido son contradictorios.
- **Responsable.** Backend.
- **Cambio requerido.** Entregar `main.py` final consolidado, solo con `get_app()`.
- **Verificación.** `uvicorn app.main:get_app --factory --port 8080` y `curl -i http://localhost:8080/openapi.json`. Pendiente.

### H-15 – Puerto y contrato de arranque inconsistentes
- **Evidencia.** El README del backend arranca en `8080`; el frontend (`DEFAULT_BASE_URL`), `smoke_test.py` y el README del frontend usan `8000`; `testing.md` usa `8080`.
- **Responsable.** Frontend, Backend y QA (acordar un puerto único).
- **Cambio requerido.** Unificar el puerto en los tres README y en los valores por defecto, o exigir `WALLET_API_URL` explícito.
- **Verificación.** Seguir los README literalmente en un entorno limpio. Pendiente.

### H-16 – Decisiones abiertas de arquitectura sin respuesta
- **Evidencia.** `architect.md` §5:
  - S/60 combinado o por tipo (pregunta 2).
  - `ACTIVE_FULL` con o sin correo y celular validados (pregunta 3).
  - Entrega del OTP al tester (pregunta 4).
  - Aceptación del consentimiento y texto (pregunta 5).
  - Autenticación (pregunta 6).
  - Endpoints de pago y recarga (pregunta 7).
  - Retención (pregunta 8).
  - Wallet huérfano (pregunta 9).
  - Nombres `ACTIVE_MOVIL` y `ACTIVE_BIOM` (supuesto 4).
  - Diferimiento de CA-11, incluido el aviso "imágenes nítidas".
- **Responsable.** Producto y Arquitectura (decisión humana).
- **Cambio requerido.** Respuesta escrita a cada punto, con ajuste de las entregas afectadas.
- **Verificación.** Revisión documental de la respuesta y de los cambios en las entregas.

### H-17 – Observaciones menores
- `DailyUsage.timezone` es `Literal["America/Lima"]`, pero `business_timezone` es configurable. Un valor distinto produciría un 500 al serializar.
- `Annotated[Username, Query()]` combina `Field(json_schema_extra)` con `Query`. No se validó que arranque ni genere el OpenAPI (G-11).
- `GET /usernames/availability` y `POST /accounts` sin límite de tasa permiten enumerar usuarios.
- El criterio "usuario: caracteres alfabéticos" se implementa como "imprimibles ASCII con al menos una letra", lo que admite dígitos. Confirmar con negocio.
- Los pasos de onboarding no tienen orden obligatorio; `LANDING_VISIBLE` cierra la sesión sin pasos previos (G-07).
- **Responsable.** Backend (salvo la confirmación de negocio sobre el usuario).
- **Cambio requerido.** Corregir o documentar cada punto.
- **Verificación.**
  - Arranque y `GET /openapi.json`.
  - Prueba con `business_timezone` distinto (no existe).
  - Revisión de negocio del criterio de usuario.

---

## Pruebas pendientes

**Estado de ejecución: ninguna prueba ha sido ejecutada** por ninguna entrega ni por esta revisión. Todo lo listado está PENDIENTE y ningún resultado debe considerarse verificado.

| Prueba / verificación | Comando disponible | Estado |
|---|---|---|
| Pruebas del backend (`tests/test_onboarding_flow.py`, 5 pruebas) | `cd wallet-api && pip install -r requirements.txt && pytest -q` | PENDIENTE. Se espera fallo en `test_username_availability_and_conflict` por H-12. |
| Arranque y humo del backend | `WALLET_ENV=test WALLET_DB_PATH=./qa-test.db WALLET_OTP_FIXED_CODE=123456 uvicorn app.main:get_app --factory --port 8080 2>&1 \| tee qa-server.log`; luego `curl -s -i -X POST http://localhost:8080/v1/onboarding/sessions` y `curl -s -i "http://localhost:8080/v1/usernames/availability?username=qa.humo"` (`testing.md` §7.2 y §7.3) | PENDIENTE. Resuelve G-11 y H-14. |
| Karate sin servicio externo (TC-API-01 a 14, 20 a 27, 30, 31) | `cd wallet-api/qa/karate && WALLET_API_BASE_URL=http://localhost:8080 mvn -B test -Dtest=OnboardingRunner -Dkarate.env=test -Dkarate.options="--tags ~@requires-external"` | PENDIENTE |
| Karate con servicio externo (TC-API-28, 40, 41) | `WALLET_API_BASE_URL=http://localhost:8080 mvn -B test -Dtest=OnboardingRunner -Dkarate.env=test` | PENDIENTE. Crea wallets sin baja posible (G-09). Depende de H-06. |
| Humo extremo a extremo del frontend contra el backend | `WALLET_API_URL=http://localhost:8000 WALLET_OTP_FIXED_CODE=123456 python smoke_test.py` (ajustar a `8080` si el backend corre allí; H-15) | PENDIENTE |
| UI Streamlit (flujo manual) | `streamlit run app.py` | PENDIENTE. Solo guía de uso, sin pruebas automáticas. |
| Selenium (TC-UI-01 a 04, TC-INT-01) | `cd wallet-api/qa/selenium && cp locators.example.json locators.json && API_BASE_URL=http://localhost:8080 HEADLESS=true UI_TIMEOUT_S=10 pytest -v --junitxml=report-ui.xml` | BLOQUEADO. Requiere `locators.json` completo y rediseño (H-10). Una prueba omitida (SKIPPED) no equivale a pasada. |
| TC-SEC-01 (búsqueda en logs) | `grep -c "S3cret!pass" qa-server.log` y `grep -c "Zq9!x" qa-server.log` | PENDIENTE y insuficiente (H-07). |
| Búsqueda ampliada de PII en logs | No se proporcionó comando; propuesta: `grep -c` con los valores sintéticos de nombres, apellidos, usuario, correo y celular | PENDIENTE |
| Pruebas nuevas por H-01, H-02, H-03, H-05, H-08, H-09 y H-13 | No se proporcionó comando; las pruebas no existen. Podrían ejecutarse con `pytest -q` una vez escritas. | PENDIENTE |
| Cobertura de CA-02 a CA-13 por QA | No se proporcionó comando; no hay pruebas diseñadas (H-11) | PENDIENTE |

**Condiciones mínimas para reevaluar la solución:**
- Resolver H-01, H-03, H-04, H-05, H-06, H-07 y H-08.
- Decidir H-02 y H-16 por escrito.
- Adjuntar resultados reales de ejecución de pytest, Karate, el humo extremo a extremo y las pruebas de UI revisadas.

La aprobación o aceptación final corresponde a las personas responsables del flujo.