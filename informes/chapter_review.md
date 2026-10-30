# Revisión Chapter de Ingenieria de Software

VEREDICTO: RECHAZADO

Fecha de la revisión: 2026-10-30. Feature: HU 01 – Onboarding de usuario, billetera digital (Wallet).

Este veredicto es una recomendación técnica. La decisión de aceptación sigue en manos de las personas responsables del flujo.

**Alcance y estado de la evidencia.** La revisión es documental y no ejecutó nada. Se evaluaron `architect.md`, `backend.md`, `frontend.md` y `testing.md`.
- `architect.md` es el único informe con contenido de diseño inspeccionable.
- `backend.md` y `frontend.md` entregan solo listas de archivos y comandos de arranque. No incluyen código, contratos ni resultados de ejecución.
- `testing.md` marca todo como NO EJECUTADO y cubre solo CA-01.
- Resultados verificados por ejecución: **ninguno**.
- Verificado por lectura: la coherencia entre la HU y `architect.md` (valores de límites, estados y reglas de OTP) y la coherencia interna entre `architect.md` y `testing.md`.
- Todo lo demás es "diseñado" o "declarado", no demostrado.

---

## Motivos del veredicto

1. **No hay evidencia de ejecución de ningún tipo.**
   - `testing.md` declara "Ninguna prueba fue ejecutada" y "Resultados observados: ninguno".
   - `backend.md` y `frontend.md` no aportan salida de `pytest`, de `uvicorn`, ni de `npm start` o build.
   - No se puede afirmar que algún criterio de aceptación esté cumplido en ejecución (H-01).

2. **El backend y el frontend no son revisables.**
   - `backend.md` y `frontend.md` listan archivos sin contenido.
   - `backend.md` dice generar desde `architecture.mmd`, `sequence.mmd` y `openapi.yaml`, pero esos artefactos no están en el contexto.
   - `testing.md` afirma que no se entregó un OpenAPI.
   - La conformidad de la implementación con CA-01 a CA-13 solo puede inferirse de nombres de archivo (H-02, H-08).

3. **Cobertura de pruebas de QA limitada a CA-01.**
   - `testing.md` §8 y P-07: CA-02 a CA-13 no tienen pruebas de QA diseñadas.
   - Las pruebas Selenium están bloqueadas (`locators.json` con `null`, las pruebas se saltan). Un skip no equivale a una prueba aprobada.
   - Los escenarios `@wallet` dependen de un servicio externo y de un contrato no confirmado (H-03, H-05).

4. **La aplicación de topes de CA-05 y CA-13 no está demostrada.**
   - `architect.md` solo expone `limits` y una Política de Límites "consultada por los flujos de pago y recarga".
   - Esos flujos no existen en los contratos visibles (pregunta 2 de arquitectura abierta).
   - Tampoco se define el contador diario, su reinicio en `America/Lima` ni si los topes de `ACTIVE_FULL` son contadores independientes (pregunta 8) (H-04).

5. **CA-03 depende de un contrato externo sin confirmar.**
   - `architect.md` §3 y `testing.md` P-02 coinciden en que el contrato de `bcp-wallet-mock` llegó truncado.
   - Faltan el esquema `Kyc`, el cuerpo de `POST /kyc/verifications` y el contrato completo de `GET /wallets/{wallet_id}`.
   - Además, queda abierto qué saldo prevalece si el mock devuelve uno distinto de 0 (pregunta 11) (H-05).

6. **Seguridad de acceso sin mecanismo definido.**
   - `architect.md` §5 supuesto 2 y pregunta 9: no hay token ni login, y los endpoints se identifican solo por `user_id`.
   - Esto incluye los endpoints de verificación y el que activa `ACTIVE_FULL`. Cualquiera que conozca un `user_id` podría operarlos.
   - La respuesta 2 de la HU habla de autenticación por usuario y password. El diseño no define ningún endpoint ni verificación de credenciales posterior al registro.
   - Hace falta una decisión humana documentada (H-06).

7. **Puntos de contrato y configuración sin alinear entre entregas.**
   - Prefijo de ruta: `testing.md` usa `baseUrl=http://localhost:8000/v1`. `architect.md` lista rutas sin `/v1`.
   - Variables de entorno: `testing.md` usa `APP_ENV` y `WALLET_BASE_URL`. El `.env.example` del backend no se entregó.
   - Biometría mock: la forma de habilitarla por ambiente (pregunta 10) sigue abierta (H-07, H-08).

8. **Brechas funcionales sin prueba ni evidencia.**
   - Robustez de contraseña con alerta en vivo (H-09).
   - Validación en vivo y momento de inicio de la medición (H-10).
   - Ausencia de PII y contraseñas en logs y analítica (H-11).
   - Semántica de OTP ("3 opciones" frente a "cualquier valor se confirma") (H-12).
   - Persistencia no documentada (H-13).
   - Diferimientos de CA-10 y CA-11 sin aceptación humana registrada (H-14).
   - Decisiones de arquitectura abiertas (H-15).

9. **Un `chapter_review.md` previo, incluido en el contexto, no corresponde a estas entregas (H-16).**
   - Describe Streamlit, `wallet-api`, SQLite, `/v1/accounts` y `config.py`. Estos elementos no coinciden con las entregas actuales (FastAPI con `app/`, Angular y rutas `/users`).
   - No se usó como evidencia.

**Lo sólido por lectura documental** (no verificado por ejecución):
- `architect.md` traza los 13 CA a componentes y endpoints.
- Los topes por defecto de `architect.md` coinciden con la HU: BASIC 2000 y 6000 céntimos combinados. FULL: pagos 50000 por operación y 100000 diarios, recargas 100000 diarios, sin tope por operación.
- Las reglas de OTP coinciden con CA-07 y CA-08: 6 caracteres, 60 s de vigencia, 45 s entre solicitudes, invalidación del OTP previo y aceptación de cualquier código vigente de 6 caracteres.
- Los datos personales viajan por POST con cuerpo y no por URL.
- El diseño de `testing.md` para CA-01 es coherente con `architect.md`: rutas `/onboarding/sessions`, `/steps`, `/usernames/availability-checks`, `registration_metrics`, política de contraseña de 10 caracteres y errores sin eco de valores.

---

## Matriz de criterios de aceptación

Escala de resultado, con el significado exacto de cada valor:
- **DISEÑADO**: `architect.md` cubre el criterio. No hay evidencia de implementación ni de ejecución.
- **PARCIAL**: hay diseño o pruebas diseñadas con brechas.
- **NO CUBIERTO**: falta una parte esencial del criterio en las entregas.

Ningún criterio está VERIFICADO por ejecución.

**Persistencia.** No se entregó modelo de datos, esquema ni migraciones.
- `architect.md` menciona "Persistencia local" (usuarios, sesiones, OTP, estados y configuración de límites).
- `backend.md` lista `app/repositories/*`.
- `testing.md` §11.5 afirma que los datos son en memoria.
- Lo anterior se infiere solo de nombres de archivo y de esa nota (H-13).

**Implementación.** Se cita por nombre de archivo, porque el contenido no se entregó.

### CA-01 – Inicio y seguimiento
- **Arquitectura:** Sesión y Métricas de Onboarding con `POST /onboarding/sessions` y `/steps`. `started_at` lo fija el servidor y la duración se calcula al cierre del registro (respuesta 7). La validación en vivo de formato se asigna al cliente. La disponibilidad se valida contra `POST /usernames/availability-checks`.
- **Persistencia:** no entregada. `architect.md` indica sesiones persistidas localmente.
- **Implementación:** backend `session_service.py`, `session_repository.py`, `routers/sessions.py` y `schemas/onboarding.py`. Frontend `onboarding.component.ts` y `form-utils.ts`. Contenido no revisable.
- **Pruebas:**
  - Karate KAR-S01 a S14, KAR-U01 a U07 y KAR-M01 a M08.
  - Selenium UI-01 a UI-05, bloqueadas por `locators.json` en `null`.
  - INT-01 sin código.
  - Pytest `tests/test_sessions.py` y `tests/test_usernames.py`, existentes por nombre.
  - Todo NO EJECUTADO.
- **Seguridad:** el registro de pasos guarda solo nombres de paso (diseño). KAR-S11 verifica que no se almacene el valor, pero no está ejecutado.
- **Resultado:** PARCIAL.
- **Brechas:**
  - `started_at` se toma al recibir `POST /sessions`, no al hacerse visible la pantalla (P-06). Solo UI-01 lo comprobaría, y está bloqueada.
  - No hay evidencia del frontend sobre la validación en vivo (H-10).
  - No hay `GET` de sesión; el estado se verifica de forma indirecta.

### CA-02 – Datos de registro
- **Arquitectura:** patrones y longitudes en `RegisterUserRequest`. Disponibilidad con sugerencias alfanuméricas (máx. 5, supuesto). Contraseña de mínimo 10 caracteres con letras y números, con símbolos permitidos. Hash de contraseña. La contraseña es `writeOnly` y está excluida de logs.
- **Persistencia:** no entregada. Unicidad de usuario sin confirmar.
- **Implementación:** `availability_service.py`, `routers/usernames.py`, `schemas/users.py`, `security.py`, `observability.py`. Contenido no revisable.
- **Pruebas:**
  - Karate KAR-U01 a U06, KAR-M04 y M05 (contraseña débil y corta).
  - KAR-U07 (usuario tomado, `@wallet`).
  - Sin pruebas de la alerta de robustez en UI ni del 409 con `suggestions` en `POST /users`.
  - Todo NO EJECUTADO.
- **Seguridad:** errores sin eco de valores (diseñado y probado en Karate, sin ejecutar). Sin evidencia de ausencia de la contraseña en logs y analítica. No hay límite de tasa en disponibilidad, lo que permite enumerar usuarios.
- **Resultado:** PARCIAL.
- **Brechas:** H-09, H-11 y la pregunta 4 de arquitectura (longitud mínima del usuario y símbolos permitidos).
- **Ambigüedad:** "usuario alfabético con símbolos" frente a las pruebas, que aceptan dígitos (`abcdefghij0123456789`) y rechazan "solo dígitos". Confirmar con negocio.

### CA-03 – Creación de cuenta básica
- **Arquitectura:** `POST /users` más Wallet Gateway hacia `POST /kyc/verifications`. Devuelve `wallet_id`, `ACTIVE_BASIC`, saldo 0, bienvenida por nombre y límites. `GET /users/{id}/wallet` consulta `GET /wallets/{wallet_id}`. Timeouts traducidos a 502 o 504.
- **Persistencia:** no entregada. Riesgo de wallet huérfana aceptado en arquitectura (supuesto 13).
- **Implementación:** `user_service.py`, `clients/wallet_gateway.py`, `routers/users.py`, `landing.component.ts`, `limits-card.component.ts`. Existe `tests/test_wallet_gateway.py` (por nombre).
- **Pruebas:** KAR-M01 a M03 y KAR-S14 (`@wallet`) exigen el servicio externo. NO EJECUTADO. Ninguna prueba de QA cubre el mapeo de errores 502 y 504.
- **Seguridad:** no se envía la contraseña al Wallet (diseño). Se envían datos personales al mock externo, lo que debe confirmarse contra el contrato.
- **Resultado:** PARCIAL.
- **Brechas:** H-05. Falta saber qué saldo prevalece (pregunta 11). La bienvenida y las condiciones en landing no tienen prueba de UI.

### CA-04 – Aviso de perfil pendiente
- **Arquitectura:** `profile_pending_notice` en el registro y en el perfil.
- **Persistencia:** no entregada.
- **Implementación:** `landing.component.ts` y `profile_service.py` (por nombre).
- **Pruebas:** ninguna de QA. Posible cobertura en pytest, sin contenido visible.
- **Seguridad:** sin hallazgos propios.
- **Resultado:** DISEÑADO.
- **Brechas:** no hay evidencia de que la landing muestre el mensaje.

### CA-05 – Operaciones de `ACTIVE_BASIC`
- **Arquitectura:** Política de Límites con 2000 por operación y 6000 diarios combinados, en configuración, zona `America/Lima`. Los valores coinciden con la HU.
- **Persistencia:** `limits_repository.py` existe por nombre. No se sabe si hay contadores diarios.
- **Implementación:** `limits_service.py`, `config.py`. Sin endpoints de pago ni recarga en los contratos visibles.
- **Pruebas:** ninguna de QA valida valores, aplicación ni cambio de día.
- **Seguridad:** n/a.
- **Resultado:** NO CUBIERTO en lo esencial. El criterio exige que la cuenta pueda recibir recargas y realizar pagos con topes. Solo se expone configuración.
- **Brechas:** H-04. Los valores por defecto de `backend.md` no son verificables (el código no se entregó).

### CA-06 – Registro complementario
- **Arquitectura:** `GET /users/{id}/profile`. Flags C1, C2 y C3 independientes. Estados iniciales `PENDING_EMAIL`, `PENDING_MOVIL` y `PENDING_BIOM`. `ACTIVE_MOVIL` y `ACTIVE_BIOM` son supuestos (pregunta 5).
- **Persistencia:** no entregada.
- **Implementación:** `profile_service.py`, `routers/profile.py`, `profile.component.ts`.
- **Pruebas:** ninguna de QA. Posible cobertura en `tests/test_profile_wallet.py` (por nombre).
- **Seguridad:** acceso por `user_id` sin autorización (H-06).
- **Resultado:** DISEÑADO.
- **Brechas:** nombres de estados activos sin confirmar; falta prueba de orden libre.

### CA-07 – Validación de correo
- **Arquitectura:** `POST /users/{id}/email-verification` y `/confirm`. Cubre formato, unicidad (409), 60 s de vigencia, 45 s entre solicitudes (429), invalidación del OTP previo y paso a `ACTIVE_EMAIL`. OTP mock interno.
- **Persistencia:** `otp_repository.py` (por nombre). No se conoce el almacenamiento del destino.
- **Implementación:** `otp_service.py`, `verification_service.py`, `routers/verifications.py`, `otp-verification.component.ts`. Existe `tests/test_verifications.py` (por nombre).
- **Pruebas:** ninguna de QA. Pytest no ejecutado ni visible.
- **Seguridad:** el mock acepta cualquier código de 6 caracteres vigente (respuesta 6). Los endpoints no tienen autorización (H-06).
- **Resultado:** DISEÑADO.
- **Brechas:** H-12. No hay pruebas de 429, expiración, invalidación ni duplicado.

### CA-08 – Validación de celular
- **Arquitectura:** `POST /users/{id}/mobile-verification` y `/confirm`. Patrón `^9[0-9]{8}$`, prefijo `+51` fijo, mismas reglas de OTP.
- **Persistencia:** igual que CA-07.
- **Implementación:** igual que CA-07. El prefijo no editable en la UI no es verificable.
- **Pruebas:** ninguna de QA.
- **Seguridad:** igual que CA-07.
- **Resultado:** DISEÑADO.
- **Brechas:** H-12, y falta evidencia de que la UI muestre el prefijo como no editable.

### CA-09 – Alcance de biometría
- **Arquitectura:** `POST /users/{id}/biometric-verification/mock`, solo dev y test (403 en otros ambientes) mediante feature flag. Sin verificación real.
- **Persistencia:** no entregada.
- **Implementación:** `biometric_service.py`, `routers/biometric.py`. Existe `tests/test_biometric.py` (por nombre).
- **Pruebas:** ninguna de QA.
- **Seguridad:** el mecanismo del flag por ambiente y su valor por defecto no están definidos (pregunta 10).
- **Resultado:** PARCIAL.
- **Brechas:** H-07. No está definido qué "inputs" verifica el mock (pregunta 6).

### CA-10 – Datos personales
- **Arquitectura:** `accepted_terms` en el paso biométrico. Observabilidad con redacción. El mock no recibe fotos ni video. Retención, eliminación y texto y versión de los términos quedan fuera de alcance (respuesta 8).
- **Persistencia:** no entregada. No hay definición de retención ni eliminación.
- **Implementación:** `observability.py`, `security.py`. Existe `tests/test_observability.py` (por nombre).
- **Pruebas:** ninguna de QA sobre PII en logs. Karate solo verifica no eco en respuestas.
- **Seguridad:** sin evidencia de ausencia de PII y contraseñas en logs ni de ausencia de analítica en el frontend. Controles de acceso débiles (H-06).
- **Resultado:** PARCIAL.
- **Brechas:** H-11, H-14 y la pregunta 7 (aceptación de términos en el registro).

### CA-11 – Documentos y video para futura integración
- **Arquitectura:** requisitos registrados en §1 (2 MB por cara, video de 5 a 10 s y 10 MB, aviso de imágenes nítidas, metadatos de los últimos 10 minutos). Sin endpoints, conforme al criterio.
- **Persistencia:** ninguna, correcto para el alcance.
- **Implementación:** ninguna, coherente con el alcance.
- **Pruebas:** ninguna, coherente.
- **Seguridad:** n/a.
- **Resultado:** DISEÑADO (documentado y diferido).
- **Brechas:** la persona responsable debe aceptar por escrito que la documentación en `architect.md` satisface el criterio (H-14).

### CA-12 – Activación completa simulada
- **Arquitectura:** el mock deja `account_status = ACTIVE_FULL` y aplica los límites FULL. No exige correo ni celular validados (respuesta 9).
- **Persistencia:** no entregada. No se sabe si el cambio de estado es atómico.
- **Implementación:** `biometric_service.py`, `routers/biometric.py`.
- **Pruebas:** ninguna de QA.
- **Seguridad:** cualquiera con el `user_id` podría activar `ACTIVE_FULL` (H-06).
- **Resultado:** PARCIAL.
- **Brechas:** H-04 (el estado habilita "operaciones reales" que no existen), H-06, H-07.

### CA-13 – Operaciones de `ACTIVE_FULL`
- **Arquitectura:** `SEPARATE`. Pagos 50000 por operación y 100000 diarios. Recargas 100000 diarios sin tope por operación. Admite recargas de terceros (`allows_third_party_recharges: true`).
- **Persistencia:** igual que CA-05.
- **Implementación:** igual que CA-05.
- **Pruebas:** ninguna de QA.
- **Seguridad:** n/a.
- **Resultado:** NO CUBIERTO en lo esencial (igual que CA-05).
- **Brechas:** H-04. Falta saber si los contadores de pagos y recargas son independientes (pregunta 8).

---

## Contratos incompatibles y hallazgos pendientes

### H-01 – Sin evidencia de ejecución (bloqueante)
- **Evidencia:** `testing.md` §13 y §14 (todo NO EJECUTADO). `backend.md` y `frontend.md` no incluyen salidas de ejecución.
- **Responsable:** Backend, Frontend y QA.
- **Cambio requerido:** ejecutar las suites, adjuntar resultados reales y actualizar la matriz de trazabilidad de `testing.md` con "resultado observado". No marcar skips como aprobadas.
- **Verificación:** salidas reales de `pytest`, Karate y Selenium (ver "Pruebas pendientes").

### H-02 – Backend y frontend sin contenido inspeccionable; contratos fuente ausentes (bloqueante)
- **Evidencia:**
  - `backend.md` y `frontend.md` solo listan archivos.
  - `backend.md` cita `architecture.mmd`, `sequence.mmd` y `openapi.yaml`, ausentes en el contexto.
  - `testing.md` §1 afirma "No se entregó un archivo OpenAPI".
  - La lista de archivos del backend no incluye un OpenAPI propio.
- **Responsable:** Backend y Frontend.
- **Cambio requerido:** entregar el código fuente o su extracto revisable y el `openapi.yaml` o `/openapi.json` generado, junto con los diagramas citados.
- **Verificación:** contrastar cada CA con el código y contrastar rutas y esquemas de `testing.md` con el contrato.

### H-03 – Cobertura de QA limitada a CA-01 y Selenium bloqueado
- **Evidencia:**
  - `testing.md` P-07 y §8: CA-02 a CA-13 sin diseño de pruebas.
  - `locators.json` con valores `null`; las pruebas se saltan (P-01).
  - INT-01 sin código.
- **Responsable:** QA, con apoyo de Frontend (selectores `data-testid` estables).
- **Cambio requerido:** ampliar la cobertura a CA-02 a CA-13. Cubrir como mínimo:
  - OTP de correo y celular: 429, expiración, invalidación y duplicados.
  - Estados C1, C2 y C3 en cualquier orden, y `ACTIVE_FULL` mediante el mock.
  - Topes y cambio de día en Lima.
  - 409 con `suggestions` en `POST /users`.
  - Ausencia de PII y contraseñas en logs.

  Completar `locators.json`.
- **Verificación:** matriz CA → prueba con resultado observado y reporte adjunto.

### H-04 – Aplicación de topes y contadores no definida (CA-05, CA-12, CA-13)
- **Evidencia:** `architect.md` §6, preguntas 2 y 8. Solo se exponen `limits`, y no hay contratos de pago ni recarga. No hay prueba de topes.
- **Responsable:** Producto y Arquitectura (decidir el alcance); Backend (implementar si aplica).
- **Cambio requerido:** decidir por escrito una de dos opciones.
  - Diferir la aplicación de topes a otra historia, con aceptación humana explícita del recorte.
  - Implementarla: verificación y consumo atómico por operación y por día en `America/Lima`, con topes parametrizables.

  Confirmar si los contadores de pagos y recargas de `ACTIVE_FULL` son independientes.
- **Verificación:** pruebas con reloj controlado (23:59 y 00:00 de Lima) y topes en el límite. Además, una prueba que compare `limits` con los valores de la HU para BASIC y para FULL tras la biometría mock. No se proporcionó comando; las pruebas no existen.

### H-05 – Contrato externo del Wallet mock sin confirmar (CA-03)
- **Evidencia:**
  - `architect.md` §3 (limitación) y §6 pregunta 1.
  - `testing.md` P-02: el cuerpo de `POST /kyc/verifications` es un supuesto, y la concatenación `WALLET_BASE_URL` más path no está probada.
  - Pregunta 11 (saldo que prevalece).
  - Los escenarios `@wallet` crean wallets sin posibilidad de baja (P-03).
- **Responsable:** Arquitectura (obtener el contrato completo); Backend (ajustar el adaptador); QA.
- **Cambio requerido:**
  - Confirmar el cuerpo del KYC, el campo `wallet_id` y el campo y la unidad del saldo.
  - Definir qué saldo prevalece.
  - Probar los mapeos de error (400, 413 y 404 → 502, 404 y 504) en una prueba de QA o confirmar la cobertura de `tests/test_wallet_gateway.py`.
- **Verificación:** ejecutar `pytest` y los escenarios `@wallet` contra el servicio real o simulado. Estado: PENDIENTE (ver comandos).

### H-06 – Autenticación y autorización por `user_id` no definidas (CA-06 a CA-08, CA-10, CA-12)
- **Evidencia:** `architect.md` supuesto 2 y pregunta 9. No hay token ni login. Los endpoints de perfil, OTP y biometría reciben `user_id` en la ruta.
  - La respuesta 2 de la HU indica autenticación por usuario y password, sin generación de token.
  - El diseño no incluye una verificación de credenciales.
- **Responsable:** Arquitectura y Producto (decisión); Backend; Frontend.
- **Cambio requerido:**
  - Aclarar si se espera un endpoint de verificación de usuario y password.
  - Definir un mecanismo mínimo de autorización para los endpoints de perfil, OTP y biometría.
  - Si se mantiene sin autorización para el MVP, documentar el riesgo y obtener aceptación humana explícita, porque CA-12 habilita operaciones de nivel FULL.
- **Verificación:** prueba de que un actor sin credencial, o con otra identidad, no pueda operar sobre un `user_id` ajeno. Hoy no existe y no se proporcionó comando.

### H-07 – Feature flag del mock biométrico no definido (CA-09, CA-12)
- **Evidencia:** `architect.md` pregunta 10 (variable de entorno o feature flag). `testing.md` §10 usa `APP_ENV=test`, un nombre no confirmado contra `.env.example` (no entregado).
- **Responsable:** Backend.
- **Cambio requerido:** definir y documentar la variable. El valor por defecto debe dejar el mock cerrado (403) y no deben existir flags de ambiente abiertos por defecto.
- **Verificación:** arrancar sin la variable y comprobar 403 en `POST /users/{id}/biometric-verification/mock`. Luego arrancar con el ambiente de prueba y comprobar que funciona. Revisar `tests/test_biometric.py` cuando se entregue su contenido.

### H-08 – Alineación de contrato y configuración entre entregas
- **Evidencia:**
  - `testing.md` usa `baseUrl .../v1`; `architect.md` lista rutas sin `/v1`.
  - `testing.md` usa `APP_ENV` y `WALLET_BASE_URL`; el `.env.example` no se entregó.
  - `testing.md` §4 cita una "corrección propuesta mencionada en la entrega del backend" (`StepName`) y nombres de pruebas pytest. Nada de eso aparece en `backend.md`.
  - El frontend usa `proxy.conf.json` (contenido no entregado).
- **Responsable:** Backend y QA (Frontend para el proxy).
- **Cambio requerido:**
  - Fijar el prefijo de ruta y el puerto.
  - Publicar las variables de entorno y los puertos en un único lugar (README o `.env.example`).
  - Reconciliar las referencias de `testing.md` con las entregas reales.
- **Verificación:** `curl -s http://localhost:8000/openapi.json` y contrastar rutas y prefijos con `testing.md` y `architect.md`. Seguir los README en un entorno limpio.

### H-09 – Robustez de contraseña y alerta en vivo (CA-02, CA-01.d)
- **Evidencia:**
  - `architect.md` §5 supuesto 3: mínimo de 10 caracteres con letras y números, con validación en el servidor.
  - `architect.md` supuesto 4: la validación en vivo de formato es del cliente.
  - `testing.md`: no hay pruebas de UI sobre contraseña. Solo KAR-M04 y M05 en la API.
- **Responsable:** Frontend (indicador y alerta); Backend; QA.
- **Cambio requerido:** implementar y probar la alerta de robustez en vivo según la política definida. Definir qué se considera "robusta" más allá del mínimo.
- **Verificación:** pruebas unitarias del validador (cliente y servidor) y una prueba UI. No se proporcionó comando.

### H-10 – Validación en vivo e inicio de la medición sin evidencia de frontend (CA-01)
- **Evidencia:**
  - `testing.md` P-01 y P-06: sin contenido del frontend; no se sabe cuándo se crea la sesión ni cuándo se envía cada paso.
  - `started_at` es el instante en que el servidor recibe `POST /sessions`.
  - Las pruebas UI-01 a UI-05 son estructurales y están bloqueadas.
- **Responsable:** Frontend y QA.
- **Cambio requerido:** garantizar y documentar que la sesión se crea cuando la pantalla es visible y que cada campo muestra su resultado de validación mientras se escribe. Completar los selectores y los textos esperados.
- **Verificación:** ejecutar Selenium UI-01 a UI-05 con `locators.json` completo (comando en "Pruebas pendientes"). Los skips no cuentan como aprobados.

### H-11 – PII y contraseñas en logs y analítica sin prueba (CA-02, CA-10)
- **Evidencia:**
  - `architect.md`: Observabilidad con redacción.
  - `backend.md`: existe `tests/test_observability.py` (por nombre).
  - `testing.md`: no hay prueba de QA sobre logs.
  - No hay evidencia sobre el frontend (analítica).
- **Responsable:** Backend, Frontend y QA.
- **Cambio requerido:**
  - Añadir una prueba que ejecute el flujo completo con datos sintéticos (nombres, apellidos, usuario, correo, celular, contraseña y OTP) y busque esos valores en los logs del servidor y en la salida del frontend.
  - Confirmar que el frontend no incluye herramientas de analítica con datos del cliente.
  - Confirmar que el OTP mock no se registra, o documentarlo si se hace en dev y test.
- **Verificación:** no se proporcionó comando. Propuesta: arrancar el backend con salida a archivo (`> /tmp/wallet-api.log`) y ejecutar `grep -c "<valor sintético>" /tmp/wallet-api.log`. El resultado esperado es 0 para cada valor.

### H-12 – Semántica del OTP ambigua y sin pruebas (CA-07, CA-08)
- **Evidencia:**
  - Respuesta 5 de la HU ("solo tiene 3 opciones") y respuesta 6 ("con cualquier valor debería confirmarse").
  - `architect.md` supuesto 6: 3 intentos fallidos, bloqueo con 423, y aceptación de cualquier código de 6 caracteres vigente.
  - Si cualquier valor confirma, los intentos fallidos solo ocurren con códigos de formato inválido, lo que debe ser una decisión explícita.
- **Responsable:** Producto y Arquitectura (confirmar); Backend; QA.
- **Cambio requerido:** confirmar la interpretación y añadir pruebas de longitud (6 caracteres), vigencia de 60 s, intervalo de 45 s, invalidación del OTP previo y bloqueo tras 3 intentos.
- **Verificación:** pruebas de API con reloj controlado. No existen y no se proporcionó comando.

### H-13 – Persistencia no documentada
- **Evidencia:**
  - No hay modelo de datos, esquema ni migraciones.
  - `architect.md` indica "Persistencia local".
  - `testing.md` §11.5 indica datos en memoria.
- **Responsable:** Arquitectura y Backend.
- **Cambio requerido:** documentar el tipo de almacenamiento.
  - Unicidad de usuario, correo y celular.
  - Atomicidad del registro tras crear la wallet.
  - Qué datos de contacto se guardan en claro.
  - Consecuencia de la persistencia en memoria (se pierden los contadores y las sesiones al reiniciar).
- **Verificación:** revisión documental y una prueba de unicidad concurrente. No se proporcionó comando.

### H-14 – Diferimientos de CA-10 y CA-11 sin aceptación humana registrada
- **Evidencia:**
  - Respuesta 8 de la HU: retención, eliminación y texto y versión de los términos quedan fuera de alcance.
  - `architect.md` §1: CA-11 solo documentado.
  - Pregunta 7: aceptación de términos solo en el paso biométrico.
- **Responsable:** Producto (decisión humana).
- **Cambio requerido:** registrar por escrito que:
  - CA-10 se acepta sin retención, eliminación ni texto de términos en esta entrega.
  - La documentación de CA-11 en `architect.md` satisface el criterio.
  - Se decide si la aceptación de términos también se exige en el registro, ya que ahí se recolectan datos personales.
- **Verificación:** revisión documental de la decisión.

### H-15 – Decisiones de arquitectura abiertas
- **Evidencia:** `architect.md` §6.
  - Pregunta 3: expiración de la sesión de onboarding y reintento tras un registro fallido.
  - Pregunta 4: longitud mínima del usuario, símbolos permitidos y número de sugerencias (se asumieron 5).
  - Pregunta 5: nombres `ACTIVE_MOVIL` y `ACTIVE_BIOM`.
  - Pregunta 6: inputs que verifica la biometría mock.
  - Pregunta 11: saldo que prevalece.

  Las preguntas 1, 2, 7, 8, 9 y 10 se cubren en H-05, H-04, H-14, H-04, H-06 y H-07.
- **Responsable:** Producto y Arquitectura.
- **Cambio requerido:** respuesta escrita a cada punto y ajuste de las entregas afectadas.
- **Verificación:** revisión documental y contraste de los cambios en las entregas.

### H-16 – `chapter_review.md` previo incompatible con las entregas actuales
- **Evidencia:** el documento previo menciona Streamlit, `wallet-api`, `db.py` SQLite, `/v1/accounts` con `accountId`, `config.py DEFAULT_LIMITS` y IDs TC-API/TC-UI. Las entregas actuales usan FastAPI con `app/`, Angular y rutas `/users`, `/onboarding/sessions` y KAR/UI IDs.
- **Responsable:** persona responsable del flujo y Chapter.
- **Cambio requerido:** descartar o archivar ese documento como evidencia, o aclarar a qué iteración corresponde. Sus hallazgos no se confirman ni se descartan aquí y se reevaluarán cuando exista el código.
- **Verificación:** confirmar la trazabilidad entre la versión de las entregas y el documento de revisión que se use.

### H-17 – Calidad de la suite de QA propuesta
- **Evidencia:** `testing.md` §14: los archivos `.feature` y Python no se validaron sintácticamente.
  - Algunas aserciones de "no eco" buscan subcadenas como `1234`, que podrían aparecer en un `trace_id`. Riesgo de falsos positivos en KAR-U02b.
  - `postData` puede no estar disponible en el log de red de Chrome (UI-04 y UI-05 quedarían inconclusas).
  - El helper de KAR-S06 y la variable no usada `last`.
  - Las wallets creadas por los `@wallet` no se pueden borrar (P-03).
- **Responsable:** QA.
- **Cambio requerido:** validar sintaxis con Karate y Selenium reales, usar valores centinela sin riesgo de colisión, definir una estrategia para wallets de prueba y documentar la versión de Karate (P-04).
- **Verificación:** primera ejecución real de las suites y revisión del reporte (`qa/karate/target/karate/`, `pytest -v`).

---

## Pruebas pendientes

**Estado de ejecución: ninguna prueba ha sido ejecutada** por ninguna entrega ni por esta revisión. Todo lo listado está PENDIENTE y no debe considerarse verificado. Los comandos se toman de `testing.md` y `backend.md` tal como fueron propuestos, sin validarlos.

| Prueba o verificación | Comando disponible | Estado |
|---|---|---|
| Pruebas del backend (`tests/test_biometric.py`, `test_observability.py`, `test_profile_wallet.py`, `test_sessions.py`, `test_usernames.py`, `test_users.py`, `test_verifications.py`, `test_wallet_gateway.py`) | `pip install -r requirements.txt` y `pytest` (`backend.md`, `testing.md` §11.4) | PENDIENTE. No ejecutado. |
| Arranque del backend | `uvicorn app.main:app --reload` (`backend.md`). Variante de QA: `APP_ENV=test WALLET_BASE_URL="https://bcp-wallet-mock.yefri.workers.dev/groups/8" uvicorn app.main:app --port 8000` seguido de `curl -s -o /dev/null -w "%{http_code}\n" http://localhost:8000/openapi.json` (`testing.md` §11.1) | PENDIENTE. Variables no confirmadas (H-07, H-08). |
| Karate completo | `java -DbaseUrl=http://localhost:8000/v1 -jar "$KARATE_JAR" -o target/karate features` (desde `qa/karate`) | PENDIENTE. Requiere el servicio externo y el JAR (P-04). |
| Karate sin servicio externo | `java -DbaseUrl=http://localhost:8000/v1 -jar "$KARATE_JAR" -t "~@wallet" -o target/karate features` | PENDIENTE |
| Karate con servicio externo (`@wallet`) | `java -DbaseUrl=http://localhost:8000/v1 -jar "$KARATE_JAR" -t "@wallet" -o target/karate features` | PENDIENTE. Crea wallets sin baja posible (P-03). Depende de H-05. |
| Frontend Angular | `npm install` y `npm start` (`frontend.md`) | PENDIENTE. No se aportó salida de build. |
| Selenium (UI-01 a UI-05) | `pip install -r qa/selenium/requirements-e2e.txt`; con `FRONTEND_URL` y `locators.json` completos, `pytest qa/selenium -v` | BLOQUEADO por P-01. Un skip no equivale a una prueba pasada. |
| INT-01 (formulario completo UI→API) | No se proporcionó comando; la prueba no tiene código | PENDIENTE |
| Búsqueda de PII y contraseñas en logs | No se proporcionó comando (propuesta en H-11) | PENDIENTE |
| Pruebas nuevas de H-04, H-06, H-07, H-09, H-12 y H-13 (topes con cambio de día en Lima, autorización, mock cerrado por defecto, robustez, OTP, unicidad) | No se proporcionó comando; las pruebas no existen | PENDIENTE |
| Cobertura de QA para CA-02 a CA-13 | No se proporcionó comando; no hay pruebas diseñadas (H-03) | PENDIENTE |

**Condiciones mínimas para reevaluar la solución:**
- Entregar el código y los contratos del backend y el frontend (H-02).
- Adjuntar resultados reales de ejecución: pytest, Karate, Selenium con selectores reales y comprobación de logs (H-01, H-03, H-10, H-11).
- Resolver o decidir por escrito H-04, H-05, H-06, H-07, H-09, H-12 y H-14.
- Alinear contratos y configuración (H-08) y resolver o aceptar por escrito las decisiones abiertas de H-13, H-15 y H-16.

La aceptación o rechazo final de la entrega corresponde a las personas responsables del flujo.