# Revisión Chapter de Ingenieria de Software

**VEREDICTO: RECHAZADO**

- **Feature:** HU 02 - Onboarding de usuario billetera digital - Wallet
- **Fecha de revisión:** 2026-10-30 (America/Lima)
- **Naturaleza:** revisión documental y estática sobre las entregas incluidas en el contexto. No ejecuté herramientas, pruebas, compilaciones ni peticiones HTTP.
- **Alcance de la recomendación:** este veredicto es una recomendación técnica. No reemplaza la aprobación humana del flujo ni aprueba nada en nombre de personas.

---

## Motivos del veredicto

Ningún criterio puede darse por demostrado con evidencia ejecutada. Además hay un defecto de código entregado, contratos incompatibles y hallazgos de seguridad altos sin resolver.

### 1. No existe evidencia ejecutada y verificada

| Entrega | Lo que declara | Lo que verifiqué |
|---|---|---|
| Backend | `101 passed, 1 warning` en su suite `tests/` y 65 hallazgos informativos de `ruff` | Es evidencia reportada por terceros. No la reproduje. Además, el contenido de `app/*.py`, `tests/*.py` y `docs/biometria-real-requisitos.md` no está en el contexto, solo la lista de archivos y el resumen. |
| Frontend | "No pude ejecutar `ng test` ni `ng build`, así que el código no está compilado ni probado" | Sin evidencia de compilación ni de pruebas. |
| QA | "Estado global: NO EJECUTADO". Todos los casos de `qa/` figuran como NO EJECUTADO. | Son diseños de prueba, no resultados. |
| Seguridad | Revisión estática. Ninguna comprobación ejecutada, 9 hallazgos sin confirmar dinámicamente. | No hay verificación dinámica. |

### 2. Defecto en código entregado (Frontend)

- `onboarding.component.ts` se entregó con `de ${'{'}total{'}'}` en el template. La corrección (`de {{ total }}`) solo aparece como nota debajo del archivo, no aplicada en el fuente.
- En Angular 18 las llaves sueltas en el texto del template pueden provocar error de compilación. Es un riesgo no verificado, porque el Frontend no compiló.
- Aunque compilara, la pantalla mostraría texto literal.
- La prueba de QA `UI-ONB-11` detecta justamente esto.

### 3. Contratos incompatibles o brechas entre entregas

- El contrato `Usuario` admite `:` y rompe HTTP Basic (SEC-07).
- La política de contraseña del contrato (`^[!-~]{10,64}$`) es más débil que "mínimo 10 caracteres alfanuméricos" (SEC-05).
- No hay forma de que el usuario recupere su `wallet_id` ni pantalla de login. El perfil solo es alcanzable dentro de la sesión en memoria del registro, lo que choca con CA-06 ("a requerimiento del usuario").
- `LandingComponent` lee un snapshot del registro y queda desactualizado tras completar el perfil.
- `openapi/wallet-onboarding-api.yaml` (tarea 2.1) no aparece en la lista de archivos del Backend. No se sabe contra qué compara `tests/test_contract.py`.

### 4. Hallazgos de seguridad altos sin resolver

- **SEC-01:** no hay control anti fuerza bruta en HTTP Basic.
- **SEC-02:** la puerta de la biometría mock depende de `APP_ENV`, cuyo valor por defecto no es visible. Esto afecta directamente la exigencia de CA-09 de que el mock exista solo en desarrollo y pruebas.

### 5. Decisiones de producto sin confirmar que afectan criterios

- Nombres `ACTIVE_MOVIL` y `ACTIVE_BIOM`.
- `balance` no se modifica.
- Actor de la recarga de terceros.
- Significado de "solo tiene 3 opciones" del OTP.
- Acumulados al pasar de BASIC a FULL el mismo día.

### Lo que sí está en orden (a nivel de diseño y lectura)

- La arquitectura, el contrato OpenAPI, el OpenSpec y las tareas cubren trazablemente CA-01 a CA-13.
- El código del Frontend recibido no muestra sumideros XSS, ni persistencia de la contraseña en storage, ni `console.*` con datos de usuario. Es lectura manual de seguridad, sin escáner.
- Hay pruebas diseñadas (Backend, Frontend y QA) para casi todos los criterios.

---

## Matriz de criterios de aceptación

**Leyenda de resultado:**
- **DISEÑADO:** cubierto en arquitectura, contrato y especificación.
- **REPORTADO:** hay implementación y pruebas declaradas por su autor, sin verificación mía.
- **NO VERIFICADO:** falta evidencia ejecutada.

Ningún criterio alcanza "VERIFICADO". Persistencia: el esquema SQLite está solo como diseño en el informe del Arquitecto. `app/db.py` consta en la lista del Backend, pero no se recibió su contenido.

### CA-01 Inicio y seguimiento
- **Arquitectura:** `OnboardingMetricsService`, `POST /onboarding/sessions`, `POST .../steps` y `registration_duration_ms`.
- **Persistencia:** tablas `onboarding_sessions` y `onboarding_steps` (solo diseño, sin valores de campos).
- **Implementación:**
  - Backend: reportado (`app/services.py` no recibido).
  - Frontend: `OnboardingComponent` llama a `startSession()` en `ngOnInit`, registra pasos en `blur` y muestra el resultado de validación por campo.
  - El template tiene el defecto CH-01.
  - Si `startSession` falla, el error se ignora y se registra sin sesión (CH-12).
- **Pruebas:**
  - Backend: reportadas.
  - Frontend: `onboarding.component.spec.ts` (no ejecutado).
  - QA: `API-ONB-01..04`, `API-REG-06..08`, `UI-ONB-01..03`, `UI-ONB-11` (no ejecutados).
  - QA marca como pendiente P-01 (tiempo comparable con reloj controlado).
- **Seguridad:** pasos sin datos personales (diseño). Sin hallazgo propio.
- **Resultado:** DISEÑADO / REPORTADO / NO VERIFICADO.
- **Brechas:** CH-01, CH-12 y P-01.

### CA-02 Datos de registro
- **Arquitectura:** `UsernameService`, validadores, `POST /onboarding/username-availability` y `POST /onboarding/registrations`.
- **Persistencia:** `wallet_accounts.username_normalized` UNIQUE (diseño).
- **Implementación:**
  - Backend: reportado.
  - Frontend: validadores 30/20/20/20, debounce de disponibilidad, chips de sugerencias y medidor de robustez.
  - Las sugerencias derivan de nombres, apellidos y números (P-02, revisión humana).
- **Pruebas:**
  - Backend: reportadas.
  - Frontend: `validators.spec.ts` y otras (no ejecutadas).
  - QA: `API-USR-01..04`, `API-REG-02..05`, `UI-ONB-03..06` (no ejecutados).
- **Seguridad:**
  - SEC-05: la política de contraseña es más débil que "alfanuméricos".
  - SEC-07: `:` en usuario rompe Basic.
  - SEC-04: enumeración sin límite de tasa.
  - Se observó que el 422 no devuelve valores (diseño).
- **Resultado:** NO VERIFICADO. Contrato incompatible con el Issue en contraseña y con HTTP Basic en usuario.
- **Brechas:** CH-04, CH-05, CH-13 y CH-14.

### CA-03 Creación de cuenta básica
- **Arquitectura:** `RegistrationService`, transacción de cuenta y perfil, `wallet_id` UUIDv4, saldo 0, `ACTIVE_BASIC`. El cierre de medición ocurre al concluir el procesamiento del registro, según la aclaración.
- **Persistencia:** `wallet_accounts` y `wallet_profiles` (diseño).
- **Implementación:** Backend reportado. `LandingComponent` muestra bienvenida por nombre real, estado, saldo, `wallet_id` y condiciones.
- **Pruebas:** `landing.component.spec.ts` (no ejecutado). QA: `API-REG-01`, `API-REG-09`, `UI-ONB-08`, `UI-ONB-10` (no ejecutados).
- **Seguridad:** hash PBKDF2 con sal por usuario (reportado por Backend, `app/security.py` no recibido, C-13 pendiente).
- **Resultado:** DISEÑADO / REPORTADO / NO VERIFICADO.
- **Brechas:** CH-07 (landing desactualizada tras cambios de perfil), CH-11 y CH-12.

### CA-04 Aviso de perfil pendiente
- **Arquitectura:** el mensaje lo muestra el Frontend a partir de `profile`.
- **Persistencia:** estados `PENDING_*` por defecto (diseño).
- **Implementación:** banner `pending-banner` con enlace a `/profile`.
- **Pruebas:** spec de la landing (no ejecutado), `UI-ONB-08` (no ejecutado).
- **Seguridad:** sin hallazgo.
- **Resultado:** DISEÑADO / NO VERIFICADO.
- **Brechas:** CH-07 (el banner no se actualiza tras validar) y CH-02 (compilación).

### CA-05 Operaciones de ACTIVE_BASIC
- **Arquitectura:** `OperationLimitService`, `PeruClock`, `limit_parameters` y `POST /wallets/{id}/operations`. Tope por operación S/20 y diario combinado S/60.
- **Persistencia:** `limit_parameters` con semilla y `operations` con `operation_day` (diseño).
- **Implementación:**
  - Backend: reportado, incluido el cambio de día 23:59:59 / 00:00:00.
  - Frontend: `OperationsPanelComponent`.
  - `balance` no se modifica (S5).
- **Pruebas:**
  - Backend: reportadas.
  - QA: `API-OPS-01..10`, `API-OPS-12`, `UI-E2E-09` (no ejecutados).
  - QA marca como pendientes `API-OPS-30` (reinicio diario) y `API-OPS-31` (parametrización).
- **Seguridad:** autorización por `wallet_id` (diseño). SEC-01 afecta la protección de la cuenta que opera.
- **Resultado:** NO VERIFICADO.
- **Brechas:** reinicio y parametrización sin prueba verificada, CH-09, CH-12 y CH-13 (saldo no se afecta).

### CA-06 Registro complementario
- **Arquitectura:** `ProfileService` con tres estados independientes. `GET /wallets/{id}` y endpoints de `profile/*`.
- **Persistencia:** `wallet_profiles` (`estado_c1`, `estado_c2`, `estado_c3`).
- **Implementación:** `ProfileComponent` con tres tarjetas independientes.
- **Pruebas:** `profile.component.spec.ts` (no ejecutado). QA: `API-PRF-01..02`, `UI-E2E-01`, `UI-E2E-04` (no ejecutados).
- **Seguridad:** acceso por Basic y `wallet_id` propio.
- **Resultado:** NO VERIFICADO.
- **Brechas:** CH-06 (sin login ni resolución de `wallet_id`, por lo que "a requerimiento del usuario" solo vale dentro de la sesión en memoria) y CH-13 (nombres `ACTIVE_MOVIL` y `ACTIVE_BIOM` sin confirmar).

### CA-07 Validación de correo
- **Arquitectura:** `OtpService`, `MockOtpProvider`, vigencia 60 s, intervalo 45 s, invalidación, 429 con `Retry-After`.
- **Persistencia:** `otp_challenges` (estados ACTIVE, INVALIDATED y CONSUMED) y unicidad parcial de `email_normalized`.
- **Implementación:** Backend reportado. `ChannelValidationCardComponent` con cuenta regresiva de 45 s y 60 s.
- **Pruebas:**
  - Frontend: spec de la tarjeta (no ejecutado).
  - QA: `API-EML-01`, `API-OTP-01..12`, `UI-E2E-02`, `UI-E2E-05`, `UI-E2E-06`, `UI-E2E-12` (no ejecutados, incluidas las `slow`).
  - Pendientes por diseño: P-03 (invalidación directa de OTP) y P-04 (sin llamadas de red).
- **Seguridad:**
  - SEC-03: el mock acepta cualquier valor sin puerta por ambiente.
  - SEC-04: enumeración de correos.
  - `code_hash` sin algoritmo especificado (SEC-09).
- **Resultado:** NO VERIFICADO.
- **Brechas:** CH-10, CH-12, CH-13 (intentos "3 opciones" y precedencia 409/429 sin definir) y CH-14.

### CA-08 Validación de celular
- **Arquitectura:** igual que CA-07, con prefijo +51 fijo en servidor y `^9[0-9]{8}$`.
- **Persistencia:** `wallet_profiles.phone_e164` con unicidad parcial.
- **Implementación:** prefijo de solo lectura en el Frontend.
- **Pruebas:** `API-PHN-01..03`, `API-OTP-*[phone]`, `UI-E2E-03`, `UI-E2E-04` (no ejecutados).
- **Seguridad:** SEC-03 y SEC-04 aplican igual. Prospectivamente hay riesgo de SMS bombing cuando exista proveedor real.
- **Resultado:** NO VERIFICADO.
- **Brechas:** CH-10, CH-12, CH-13 y CH-14.

### CA-09 Alcance de la validación biométrica
- **Arquitectura:** `BiometricMockService` con puerta por `APP_ENV` en {development, testing}, sin proveedor real ni archivos.
- **Persistencia:** `wallet_accounts.status`, `wallet_profiles.estado_c3` y `terms_acceptances`.
- **Implementación:** Backend reportado (403 en otro ambiente). `IdentityCardComponent` oculta el flujo si `identity_mock_available` es falso.
- **Pruebas:** `API-IDN-03`, `API-IDN-07`, `API-IDN-08`, `UI-E2E-11` (no ejecutados, requieren reiniciar el backend en otro ambiente).
- **Seguridad:** SEC-02 (Alta). No se conoce el valor por defecto de `APP_ENV` ni los valores aceptados (G-10 de QA).
- **Resultado:** NO VERIFICADO.
- **Brechas:** CH-08.

### CA-10 Datos personales
- **Arquitectura:** `PersonalDataGuard`, `terms_acceptances`, Basic Auth con control por `wallet_id`, mock sin archivos.
- **Persistencia:** datos personales en SQLite sin cifrado (SEC-09). `otp_challenges.destination` duplica el dato personal.
- **Implementación:**
  - Frontend: sin analítica ni `console.*`. Las credenciales viven solo en memoria. Hay casilla de términos en el flujo mock.
  - Backend: filtro de logs reportado, sin contenido recibido.
- **Pruebas:** Backend `tests/test_privacy.py` y `tests/test_access.py` (reportados). QA: `API-SEC-01..06`, `UI-ONB-09` (no ejecutados). P-05 (analítica) queda pendiente.
- **Seguridad:** SEC-01, SEC-03, SEC-04, SEC-08 y SEC-09.
- **Resultado:** NO VERIFICADO.
- **Brechas:**
  - La retención, la eliminación y el texto o versión de los términos están fuera de alcance por aclaración del Issue. CA-10 dice "se definen", así que requiere reconocimiento humano explícito (CH-15).
  - La casilla de términos no muestra texto ni enlace.
  - CH-09, CH-14 y CH-11.

### CA-11 Documentos y video para futura integración
- **Arquitectura:** solo documentación y aviso de nitidez. Sin implementación.
- **Persistencia:** no aplica.
- **Implementación:**
  - Frontend: aviso de nitidez y detalle de requisitos (2 MB, 10 MB, 5 a 10 s, últimos 10 min).
  - Backend: `docs/biometria-real-requisitos.md` figura en la lista de archivos, pero no recibí su contenido.
- **Pruebas:** `identity-card.component.spec.ts` (no ejecutado), `UI-E2E-07` (no ejecutado), `API-SEC-08` (verifica el documento, no ejecutado).
- **Seguridad:** sin hallazgo. El mock no recibe archivos.
- **Resultado:** DISEÑADO / REPORTADO / NO VERIFICADO.
- **Brechas:** contenido del documento sin revisar (CH-11).

### CA-12 Activación completa simulada
- **Arquitectura:** el mock pasa la cuenta a `ACTIVE_FULL` y C3 a `ACTIVE_BIOM`, sin tocar C1 ni C2.
- **Persistencia:** `wallet_accounts.status` y `wallet_profiles.estado_c3`.
- **Implementación:** `IdentityCardComponent` emite `verified` y `ProfileComponent` refresca.
- **Pruebas:** `API-IDN-04..06`, `UI-E2E-07`, `UI-E2E-08` (no ejecutados). Spec de `profile.component` (no ejecutado).
- **Seguridad:** SEC-02. Si el mock queda abierto, hay elevación de privilegios sin verificación.
- **Resultado:** NO VERIFICADO.
- **Brechas:** CH-07 (la landing no refleja `ACTIVE_FULL`), CH-08 y CH-13 (`ACTIVE_BIOM` sin confirmar).

### CA-13 Operaciones de ACTIVE_FULL
- **Arquitectura:** grupos TOPUP (sin tope por operación, S/1,000 diarios) y PAYMENT (S/500 por operación, S/1,000 diarios), con acumulados separados.
- **Persistencia:** `limit_parameters` y `operations` (diseño).
- **Implementación:** Backend reportado. El panel de operaciones muestra 3 tipos cuando las condiciones son FULL.
- **Pruebas:** `API-OPS-20..25`, `UI-E2E-10` (no ejecutados). Reinicio diario y parametrización pendientes (`API-OPS-30` y `API-OPS-31`).
- **Seguridad:** autorización por `wallet_id` (diseño). La recarga de terceros se simula bajo la misma autenticación del titular (S6).
- **Resultado:** NO VERIFICADO.
- **Brechas:** CH-12 y CH-13 (actor de la recarga de terceros, saldo sin modificar, acumulado entre BASIC y FULL).

---

## Contratos incompatibles y hallazgos pendientes

**Severidad de cierre:**
- **Bloqueante:** impide aprobar.
- **Mayor:** debe resolverse o aceptarse explícitamente por una persona.
- **Menor:** recomendable.

### CH-01 (Bloqueante): template defectuoso en `OnboardingComponent`
- **Evidencia:** `onboarding.component.ts` contiene `de ${'{'}total{'}'}`. La nota final del Frontend reconoce que "debe ser `de {{ total }}`" y no está aplicado. `UI-ONB-11` de QA lo detecta.
- **Responsable:** Frontend.
- **Cambio requerido:** aplicar la corrección en el fuente. Confirmar que no queden llaves sueltas en los templates.
- **Verificación (pendiente):** `npm run build` y `npm run test:ci` en `wallet-frontend`. `pytest ui -k ui_onb_11` en `qa/`.

### CH-02 (Bloqueante): Frontend sin compilar ni probar
- **Evidencia:** declaración del Frontend (no ejecutó `ng build` ni `ng test`). QA G-07.
- **Responsable:** Frontend.
- **Cambio requerido:** compilar, ejecutar las pruebas unitarias y adjuntar la salida real.
- **Verificación (pendiente):** `npm install`, `npm run build`, `npm run test:ci`.

### CH-03 (Mayor): contrato YAML no verificado en el entregable
- **Evidencia:**
  - La tarea 2.1 exige guardar `openapi/wallet-onboarding-api.yaml`.
  - El Backend dijo que no verificó su existencia y no aparece en su lista de archivos.
  - La prueba 4.13 compara `openapi.json` contra ese YAML.
  - `API-SEC-07` de QA solo verifica la presencia de métodos y rutas.
- **Responsable:** Backend (con el Arquitecto).
- **Cambio requerido:** incluir el YAML en el entregable. La prueba de contrato debe compararlo con el `openapi.json` generado, incluidos esquemas, códigos y cabeceras.
- **Verificación (pendiente):** `pytest tests/test_contract.py` en el espacio del Backend. El comando exacto no fue documentado. Se infiere de `pytest.ini`.

### CH-04 (Mayor): `Usuario` admite `:`, incompatible con HTTP Basic (SEC-07)
- **Evidencia:** `Usuario.pattern = '^[!-~]*[A-Za-z][!-~]*$'` incluye 0x3A. `USUARIO_PATTERN` en el Frontend es idéntico. `session.store.ts` arma `usuario:contraseña`. RFC 7617 prohíbe `:` en el identificador.
- **Responsable:** Arquitecto (contrato), Backend (validador) y Frontend (`USUARIO_PATTERN`).
- **Cambio requerido:** excluir `:` del conjunto permitido en los tres puntos. Por ejemplo `^[!-9;-~]*[A-Za-z][!-9;-~]*$`. Añadir un caso a las pruebas.
- **Verificación (pendiente, propuesta C-06):** `POST /onboarding/username-availability` con `{"username":"ab:cd1"}` debe responder `INVALID_FORMAT`. No se proporcionó un comando completo para el caso de login posterior.

### CH-05 (Mayor): política de contraseña menos exigente que el Issue (SEC-05)
- **Evidencia:**
  - El Issue pide "mínimo 10 caracteres alfanuméricos".
  - El contrato usa `^[!-~]{10,64}$`, que acepta `!!!!!!!!!!`.
  - La prueba del Frontend declara `abcdefghij` como `acceptable: true`.
  - CA-02 pide validar robustez y alertar. En el servidor la robustez no se valida.
- **Responsable:** Arquitecto, Backend y Frontend.
- **Cambio requerido:**
  - Validar en servidor, en código, al menos una letra y un dígito, repeticiones triviales y que no contenga el usuario.
  - Reflejar las mismas reglas en `passwordValidators` y `evaluatePasswordStrength`.
  - Pedir a producto que aclare "alfanuméricos" frente a "permite símbolos".
- **Verificación (pendiente, C-05):** una contraseña de 10 letras iguales debe devolver 422.

### CH-06 (Mayor): no hay login ni forma de resolver el `wallet_id`
- **Evidencia:**
  - Todos los endpoints de perfil, operaciones y consulta requieren `/wallets/{wallet_id}` con Basic.
  - El `wallet_id` solo se obtiene en la respuesta del registro.
  - El README del Frontend admite "sin pantalla de login" y que al recargar se pierde la sesión.
  - CA-06 pide completar el perfil "a requerimiento del usuario" y la aclaración dice que la autenticación es por usuario y password.
- **Responsable:** Arquitecto (contrato) y Frontend, con decisión de producto.
- **Cambio requerido:** decidir uno de dos caminos y reflejarlo en contrato, backend y frontend:
  - (a) añadir un mecanismo para resolver el wallet del usuario autenticado y una pantalla de login, sin tokens.
  - (b) aceptar por escrito que, en este MVP, el perfil solo es completable dentro de la sesión del registro.
- **Verificación:** caso E2E: registrar, recargar la página, volver a ingresar y completar el perfil. No existe prueba ni comando hoy.

### CH-07 (Mayor): landing con datos desactualizados tras cambios de perfil
- **Evidencia:** `LandingComponent` renderiza `store.registration()`, un snapshot del registro. `ProfileComponent.refresh()` solo actualiza su señal local. Tras `ACTIVE_FULL`, "Inicio" seguiría mostrando "Cuenta básica", las condiciones BASIC y el banner de perfil pendiente. Esto afecta CA-03, CA-04 y CA-12. `UI-E2E-07` no navega de vuelta a la landing.
- **Responsable:** Frontend.
- **Cambio requerido:** que la landing consulte `GET /wallets/{id}` o que `refresh()` actualice el store. Añadir una prueba unitaria y un caso E2E.
- **Verificación (pendiente):** spec nuevo en `landing.component.spec.ts` y un caso de QA nuevo, ya que no hay uno equivalente.

### CH-08 (Mayor, SEC-02): puerta de la biometría mock dependiente de `APP_ENV`
- **Evidencia:** el valor por defecto de `APP_ENV` y los valores aceptados no constan en ningún artefacto. QA G-10. CA-09 exige mock solo en desarrollo y pruebas.
- **Responsable:** Backend.
- **Cambio requerido:**
  - `APP_ENV` como enumeración cerrada, con valor por defecto `production`.
  - Abortar el arranque ante valores desconocidos.
  - Lista blanca {development, testing}.
  - Verificar la puerta también en el servicio.
- **Verificación (pendiente, C-02):** arrancar con `APP_ENV` sin definir, con `production` y con un valor desconocido. Esperar 403 `BIOMETRIC_MOCK_DISABLED` o fallo de arranque. Ejecutar `API-IDN-07` y `UI-E2E-11` de QA con el backend en otro ambiente (comandos en `qa/testing_report.md`, sección 5.2).

### CH-09 (Mayor, SEC-01): sin control anti fuerza bruta en HTTP Basic
- **Evidencia:** el único 429 del contrato es `OtpRateLimited`. Ninguna tarea lo cubre. `username-availability` permite descubrir usuarios sin autenticación. La autenticación precede a la verificación del `wallet_id`.
- **Responsable:** Arquitecto (contrato y tareas) y Backend.
- **Cambio requerido:** conteo de fallos por usuario e IP con bloqueo o retardo y 429 con `Retry-After`. Respuesta de tiempo uniforme con usuario inexistente y `hmac.compare_digest`. Declarar el 429 en el contrato.
- **Verificación (pendiente, C-01):** 30 peticiones con credenciales incorrectas deben terminar en 429 (comando en el informe de seguridad).

### CH-10 (Mayor, SEC-03): OTP mock sin puerta por ambiente
- **Evidencia:** la especificación acota la biometría mock a desarrollo y pruebas, pero no el OTP mock. Cualquier usuario registrado puede "validar" el correo o celular de otra persona, que queda reservado por la unicidad.
- **Responsable:** Arquitecto y Backend, con decisión de producto.
- **Cambio requerido:** confirmar si el OTP mock debe seguir la misma restricción de ambiente. Si es así, instanciarlo solo en development y testing. Definir el límite de intentos ("solo tiene 3 opciones") antes del proveedor real.
- **Verificación (pendiente, C-03):** procedimiento descrito en el informe de seguridad.

### CH-11 (Mayor): código del Backend y archivos clave no recibidos
- **Evidencia:** solo se recibió la lista de archivos y el resumen. No pude revisar `app/db.py` (persistencia real), `app/security.py` (hash), `app/logging_guard.py`, `app/services.py`, `app/config.py`, los tests ni `docs/biometria-real-requisitos.md`.
- **Responsable:** Backend.
- **Cambio requerido:** entregar el código y los documentos para revisión. Confirmar comando de arranque y ruta de `wallet.db` (G-01 de QA).
- **Verificación (pendiente, C-09, C-13, C-14):** revisión de código, permisos del archivo de base de datos y `API-SEC-06` con `API_LOG_FILE`.

### CH-12 (Mayor): pruebas sin ejecutar y casos no automatizados
- **Evidencia:** todo `qa/` figura como NO EJECUTADO. QA lista como pendientes el reinicio diario (G-04), la parametrización de topes (G-05), la invalidación de OTP (G-06), la ausencia de llamadas de red (P-04) y de analítica (P-05).
- **Responsable:** QA, con apoyo de Backend.
- **Cambio requerido:**
  - Ejecutar las suites y adjuntar salidas.
  - Habilitar un reloj controlable o ejecutar `tests/test_operations.py` del Backend y adjuntar su salida.
  - Dar acceso observable a `limit_parameters` y `otp_challenges` en un ambiente de pruebas.
  - Acordar cómo evidenciar P-04 y P-05.
- **Verificación:** ver "Pruebas pendientes".

### CH-13 (Mayor): supuestos sin confirmar que afectan criterios
- **Evidencia:** preguntas abiertas del Arquitecto, QA G-12 y el Backend.
- **Responsable:** persona de producto, con Arquitecto.
- **Cambio requerido:** confirmar o corregir cada punto:
  - Nombres `ACTIVE_MOVIL` y `ACTIVE_BIOM` (el Issue solo nombra `ACTIVE_EMAIL`).
  - `balance` sin modificar: CA-05 dice "puede recibir recargas" y los pagos no exigen saldo.
  - Actor y autenticación de la recarga de terceros (hoy se simula con la misma autenticación del titular).
  - Acumulados al pasar de BASIC a FULL el mismo día.
  - Significado de "3 opciones" del OTP.
  - Precedencia de 409 `ALREADY_VALIDATED` frente a 429.
  - Cambio de un correo o celular ya validado.
- **Verificación:** decisión registrada. Después actualizar contrato y pruebas afectadas (`API-OPS-12`, `API-OTP-09`).

### CH-14 (Menor): enumeración, límites de uso, transporte y datos en reposo (SEC-04, 06, 08, 09)
- **Evidencia:** informe de seguridad.
  - Los endpoints públicos no tienen límites de tasa ni de tamaño.
  - La unicidad se revela antes de probar posesión.
  - El contrato y el proxy usan HTTP, y no hay CSP ni `Cache-Control: no-store`.
  - Los datos personales están en claro en SQLite y `code_hash` no tiene algoritmo especificado.
- **Responsable:** Backend, Arquitecto y Frontend (CSP).
- **Cambio requerido:** límite de tasa por IP en `/onboarding/*` y en consultas de unicidad. `maxLength` en `Money`. TLS en despliegue. Cabeceras de seguridad. CORS con lista blanca. Purga de `otp_challenges` vencidos. HMAC con clave de servidor para `code_hash`.
- **Verificación (pendiente):** C-04, C-07, C-08 y C-09 del informe de seguridad.

### CH-15 (Menor): CA-10 retención, eliminación y términos fuera de alcance
- **Evidencia:** la aclaración del Issue los deja fuera. CA-10 dice "se definen controles de acceso, protección, retención y eliminación". La casilla de términos del Frontend no muestra texto ni enlace.
- **Responsable:** persona de producto.
- **Cambio requerido:** registrar la exclusión como decisión explícita, para que el criterio no quede como incumplido por omisión.
- **Verificación:** constancia en la documentación de la entrega.

### CH-16 (Menor): seguimiento silencioso si falla la sesión de medición
- **Evidencia:** en `OnboardingComponent.ngOnInit` el `error` de `startSession` se ignora. El registro continúa sin `session_id` y `registration_duration_ms` queda nulo, por lo que CA-01 no se cumple y nadie lo ve.
- **Responsable:** Frontend, con confirmación de producto.
- **Cambio requerido:** decidir si el fallo debe reintentarse o registrarse (sin datos personales).
- **Verificación:** prueba unitaria con `startSession` fallido.

### CH-17 (Menor): estilo del Backend
- **Evidencia:** `ruff` reporta 65 hallazgos (47 corregibles automáticamente). El Backend los consideró informativos.
- **Responsable:** Backend.
- **Cambio requerido:** corregir o justificar.
- **Verificación (pendiente):** ejecutar `ruff check`. El comando exacto no fue proporcionado (solo se menciona la herramienta `run_ruff`).

---

## Pruebas pendientes

**Nada de lo siguiente fue ejecutado por esta revisión.** Lo único con resultado numérico es el `101 passed, 1 warning` del Backend, que es evidencia de terceros no verificada por mí.

### Backend, Frontend y estilo

| Prueba | Comando | Estado |
|---|---|---|
| Suite del Backend (`tests/`) | No se documentó el comando. Se infiere `pytest` desde el espacio del Backend (existe `pytest.ini`). | Reportado por el Backend. No verificado. Reejecutar. |
| Contrato Backend (`tests/test_contract.py`) | `pytest tests/test_contract.py` (inferido). Debe comparar contra el YAML del contrato (CH-03). | Reportado. Referencia de comparación no confirmada. |
| Estilo (`ruff`) | No se proporcionó comando. | 65 hallazgos informativos reportados. |
| Compilación del Frontend | `npm install` y `npm run build` | Pendiente. El Frontend declara que no lo ejecutó. |
| Pruebas unitarias del Frontend | `npm run test:ci` (Karma y Jasmine, ChromeHeadless) | Pendiente. |

### QA (de `qa/testing_report.md`, sección 5.2)

Requiere backend en `http://localhost:8000` (con `APP_ENV=testing`) y frontend en `http://localhost:4200`. Esta URL del frontend es un supuesto de QA. El comando de arranque del backend también es un supuesto (G-01).

| Prueba | Comando | Estado |
|---|---|---|
| API rápidas | `pytest api -m "not slow" -v --junitxml=results\api-fast.xml` | NO EJECUTADO |
| API lentas (OTP 45 s y 60 s reales) | `pytest api -m slow -v --junitxml=results\api-slow.xml` | NO EJECUTADO |
| UI y E2E rápidas | `pytest ui -m "not slow" -v --junitxml=results\ui-fast.xml` | NO EJECUTADO |
| UI lenta (`UI-E2E-12`) | `pytest ui -m slow -v --junitxml=results\ui-slow.xml` | NO EJECUTADO |
| Biometría mock en otro ambiente (CH-08) | Reiniciar el backend con `APP_ENV` distinto y `MOCK_BIOMETRIC_ENABLED=false`. Luego `pytest api/test_identity_api.py -k "disabled" -v` y `pytest ui/test_profile_e2e.py -k "ui_e2e_11" -v`. | NO EJECUTADO |
| Privacidad en logs (`API-SEC-06`) | Requiere `API_LOG_FILE`. Se ejecuta dentro de `pytest api`. | NO EJECUTADO |
| Documento CA-11 (`API-SEC-08`) | Requiere `BACKEND_DIR`. Se ejecuta dentro de `pytest api`. | NO EJECUTADO |

### Seguridad (propuestas del informe de seguridad)

| Comprobación | Comando disponible | Estado |
|---|---|---|
| C-01 fuerza bruta | Bucle de 30 peticiones `curl -u usuario_qa:clave_incorrecta` contra `/wallets/{uuid aleatorio}` | No ejecutada |
| C-02 puerta del mock | `curl -u "$U:$P" -X POST .../identity/mock-verification ...` con `APP_ENV` sin definir, `production` y desconocido | No ejecutada |
| C-03 OTP mock ajeno | Procedimiento con dos cuentas (sin comando único) | No ejecutada |
| C-04 enumeración | Bucle de 60 peticiones a `/onboarding/username-availability` | No ejecutada |
| C-05 contraseña débil | `POST /onboarding/registrations` con 10 letras iguales | No ejecutada |
| C-06 usuario con `:` | `POST /onboarding/username-availability` con `{"username":"ab:cd1"}` | No ejecutada |
| C-07 cabeceras | `curl -sI` sobre `/wallets/{id}` y el frontend | No ejecutada |
| C-08 abuso de sesiones | Bucle de 500 peticiones a `/onboarding/sessions` | No ejecutada |
| C-09 permisos de `wallet.db` | `icacls` o `stat`. La ruta real no se conoce. | Pendiente |
| C-10 XSS | `grep -rEn "innerHTML\|bypassSecurityTrust\|document\.write\|eval\(" wallet-frontend/src` | No ejecutada (solo lectura manual) |
| C-11 secretos | `gitleaks detect --no-banner` | No ejecutada |
| C-12 dependencias | `pip-audit` y `npm audit --omit=dev`. No se recibió `requirements` del Backend. | No ejecutada |
| C-13 hash de contraseña | Revisión de `app/security.py`, que no fue recibido | Pendiente |

### Sin comando proporcionado

- Reinicio diario del contador en hora de Lima (`API-OPS-30`). El Backend declara haberlo probado en `tests/test_operations.py`, sin verificación. Falta un reloj controlable o ejecutar esa prueba con salida.
- Parametrización de topes (`API-OPS-31`). No hay API de administración y no se conoce la ruta de la base de datos.
- Invalidación directa de OTP anteriores (P-03). El OTP no es observable por API.
- Ausencia de llamadas de red salientes (P-04) y de analítica (P-05).
- Caso de landing actualizada tras `ACTIVE_FULL` (CH-07).
- Caso de login o recuperación de sesión (CH-06).
- Caso de usuario con `:` (CH-04).
- Sugerencias basadas en nombres, apellidos y números (P-02): requiere revisión humana.

---

## Condiciones mínimas para una nueva revisión

1. Corregir y compilar el Frontend (CH-01 y CH-02) y adjuntar la salida de `npm run build` y `npm run test:ci`.
2. Entregar el código del Backend, el YAML del contrato y `docs/biometria-real-requisitos.md` (CH-03 y CH-11).
3. Resolver o aceptar por escrito CH-04 a CH-10 y CH-13.
4. Ejecutar las suites del Backend, del Frontend y de QA, y adjuntar salidas reales. Las brechas que hoy no tienen comando deben quedar cubiertas o aceptadas explícitamente (CH-12).

Esta recomendación técnica no reemplaza la aprobación humana del flujo. La decisión final de aceptación corresponde a las personas responsables.