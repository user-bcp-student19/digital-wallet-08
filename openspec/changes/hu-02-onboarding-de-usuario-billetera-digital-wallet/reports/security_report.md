# security_report.md

**Feature:** HU 02 – Onboarding de usuario billetera digital (Wallet)
**Fecha del informe:** 2026-10-30 (America/Lima)
**Rol:** Analista Senior de Seguridad de Aplicaciones
**Tipo de revisión:** estática y documental, sin ejecución de herramientas ni pruebas.

---

## 1. Resumen ejecutivo y alcance revisado

### 1.1 Resumen

Se revisaron la autenticación, la autorización (acceso a recursos de otra persona), la validación de entradas, la inyección, los secretos y la exposición de datos sensibles de la HU 02.

- **Evidencia disponible:** la propuesta y las capacidades OpenSpec, la arquitectura (diagramas, esquema SQLite, tareas), el contrato OpenAPI local, el informe del Backend, el código fuente completo del Frontend Angular y el diseño de pruebas de QA.
- **Evidencia no disponible:** el código fuente del Backend (`app/*.py`). Solo se recibió su lista de archivos y su resumen. Por eso los controles del servidor se evalúan contra el **contrato y el diseño**, no contra la implementación.
- **Resultado:** 9 hallazgos sustentados en evidencia localizable (2 Altos, 3 Medios, 4 Bajos). Ninguno es una vulnerabilidad confirmada por ejecución. Se clasifican por la evidencia que los sustenta.

| Clase | Hallazgos |
|---|---|
| Sustentado directamente en el contrato, el código o la especificación recibidos | SEC-03, SEC-04, SEC-05, SEC-07, SEC-08 |
| Ausencia de control en contrato y diseño, pendiente de confirmar en el código del Backend | SEC-01, SEC-06, SEC-09 |
| Riesgo condicional que depende de configuración no visible | SEC-02 |

### 1.2 Distinción entre riesgos detectados, correcciones propuestas y verificaciones ejecutadas

| Concepto | Estado |
|---|---|
| Riesgos detectados | 9 (sección 2). Surgen de lectura de documentos y del código del Frontend. |
| Correcciones propuestas | Una por hallazgo. **No se aplicó ninguna** ni se modificó código. |
| Verificaciones ejecutadas por este análisis | **Ninguna.** No se ejecutó ninguna herramienta, prueba, escáner ni petición HTTP. |
| Evidencia de terceros no verificada | El Backend reporta `101 passed` en `tests/`, incluidas pruebas de acceso y privacidad. QA diseñó una suite (`qa/`) con todo en "NO EJECUTADO". El Frontend declara que no compiló ni probó. |

### 1.3 Alcance revisado

| Área | Material revisado | Profundidad |
|---|---|---|
| Autenticación HTTP Basic, hash, 401/403/404 | Contrato OpenAPI, arquitectura §3 y §7, tareas 2.3 y 2.4, informe del Backend | Contrato y diseño. Sin código. |
| Autorización por `wallet_id` | Contrato (`Forbidden`, `NotFound`), arquitectura, pruebas `API-SEC-01` a `04` | Contrato y diseño |
| Validación de entradas | Esquemas del contrato (`Nombres`, `Apellido`, `Usuario`, `Money`, `RegistrationRequest`, OTP) y validadores del Frontend | Contrato y código del Frontend |
| Inyección (SQL, XSS, HTML) | Esquema SQLite y tareas 1.7 y 2.2 (diseño). Código Angular completo. | SQL: diseño. XSS: lectura del código. |
| Secretos | Todo el material recibido | Búsqueda por lectura, no con escáner |
| Datos sensibles (logs, errores, almacenamiento) | `PersonalDataGuard` (diseño), esquema SQLite, `SessionStore`, interceptor, pruebas de privacidad | Diseño y código del Frontend |
| Control de acceso a datos de otras personas | Contrato, CA-07/CA-08, flujo de OTP y unicidad | Contrato y diseño |

### 1.4 Controles observados sin hallazgo (por lectura)

| Control | Evidencia | Tipo de verificación |
|---|---|---|
| No hay sumideros XSS en el Frontend: no hay `innerHTML`, `bypassSecurityTrust*` ni `[innerHTML]`. Todo se renderiza con interpolación de Angular. Esto incluye `welcome.display_name` y los mensajes de error (`describeError`). | Todos los componentes entregados | Lectura del código. Sin escáner. |
| El interceptor añade `Authorization` solo a `${base}/wallets/*`, no a `/onboarding/*`. | `basic-auth.interceptor.ts` | Lectura |
| La contraseña no se guarda en storage. Vive en memoria (`SessionStore`) y se limpia del formulario tras el registro (`password.reset('')`). | `session.store.ts`, `onboarding.component.ts` | Lectura |
| La disponibilidad de usuario va por `POST` con cuerpo, no por URL. | Contrato y `onboarding-api.service.ts` | Lectura |
| El Frontend no usa `console.*` con datos de usuario. Solo `console.error(err)` en `main.ts`, que es el error de arranque. | `main.ts` | Lectura |
| El diseño del Backend contempla consultas parametrizadas, 422 sin eco del valor, no registrar `Authorization` y `BEGIN IMMEDIATE` en topes. | Arquitectura §3, tareas 1.7, 2.2 y 2.11 | **Solo diseño. No verificado en código.** |

---

## 2. Hallazgos (ordenados por severidad)

**Convención de ubicación:** no se recibieron números de línea (los archivos se entregaron inline, sin numeración). La ubicación se da como archivo más símbolo o sección. Los archivos del Backend se citan por su nombre en el informe del Backend. Su contenido **no fue recibido**.

---

### SEC-01 – Sin control anti fuerza bruta en HTTP Basic

| Campo | Detalle |
|---|---|
| **Severidad** | Alta |
| **Confianza** | 6/10 (la ausencia consta en contrato y diseño. Falta confirmar en el código) |
| **Categoría** | Autenticación |
| **Archivo / ubicación** | Contrato OpenAPI: `components.securitySchemes.basicAuth`, `components.responses.Unauthorized`. Arquitectura §3 ("Auth y control de acceso") y §7. Tareas 2.3 y 2.4. Código no recibido: `app/security.py`. Línea: no disponible. |

**Evidencia**
- La autenticación se evalúa en cada petición a 7 endpoints (`/wallets/{wallet_id}/...`).
- El único 429 definido en el contrato es `OtpRateLimited`. Ningún endpoint protegido declara 429 por fallo de autenticación.
- Ninguna tarea de las 1.x a 4.x cubre bloqueo, retardo progresivo ni conteo de intentos fallidos. Tampoco existe una tabla para ello en el esquema SQLite.
- Las pruebas `API-SEC-01` y `02` solo verifican que se devuelva 401. No verifican limitación.
- El nombre de usuario es consultable sin autenticación (`POST /onboarding/username-availability`, `security: []`).

**Escenario**
1. El atacante descubre nombres de usuario existentes mediante `username-availability` o con un diccionario.
2. Envía muchas peticiones `GET /wallets/{uuid-aleatorio}` con `Authorization: Basic` y contraseñas candidatas.
3. La autenticación precede a la verificación de pertenencia, porque `API-SEC-04` espera 404 solo con credenciales válidas. Por tanto, el `wallet_id` no necesita ser real para probar credenciales.

**Impacto**
- Toma de cuentas por adivinación de contraseñas.
- Con la política de contraseña descrita en SEC-05, el riesgo aumenta.
- Una cuenta tomada puede registrar operaciones (hasta S/60 por día en BASIC y S/1,000 en FULL), validar correo y celular, y activar `ACTIVE_FULL` en ambientes donde el mock esté disponible.

**Corrección recomendada (compatible con FastAPI y SQLite)**
1. En la dependencia de autenticación, registrar intentos fallidos por `username_normalized` y por IP de origen. Usar una tabla nueva `auth_failures(key, window_start, count)` sin datos personales en claro (clave hasheada con HMAC).
2. Aplicar retardo progresivo o bloqueo temporal tras N fallos (por ejemplo 5 en 15 minutos). Responder **429 con `Retry-After`** y agregar ese código al contrato de los endpoints protegidos.
3. Igualar el tiempo de respuesta cuando el usuario no existe: verificar contra un hash ficticio y comparar con `hmac.compare_digest`.
4. Confirmar que los parámetros del hash (iteraciones de PBKDF2 o costo de scrypt) sean los recomendados vigentes.
5. No registrar el usuario ni la contraseña en los logs del control.

**Comprobación reproducible:** C-01 (sección 3).

---

### SEC-02 – La puerta de la biometría mock depende de `APP_ENV` y puede quedar abierta por configuración

| Campo | Detalle |
|---|---|
| **Severidad** | Alta (condicional: solo si el ambiente no restringe el mock) |
| **Confianza** | 5/10 (el valor por defecto de `APP_ENV` no es visible) |
| **Categoría** | Autorización / configuración insegura |
| **Archivo / ubicación** | Contrato: `POST /wallets/{wallet_id}/profile/identity/mock-verification` (descripción y 403 `BIOMETRIC_MOCK_DISABLED`). Arquitectura §3 (`BiometricMockService`) y supuesto S10. Tarea 2.1. Código no recibido: `app/config.py`, `app/services.py`. Línea: no disponible. |

**Evidencia**
- La habilitación del mock se decide únicamente por la variable de entorno `APP_ENV` ("development" o "testing").
- El informe de QA (brecha G-10) deja pendiente confirmar qué valores acepta la configuración.
- El valor por defecto cuando `APP_ENV` no está definido no consta en ningún artefacto.
- Para activar `ACTIVE_FULL` solo se exige enviar `terms_accepted=true` y `mock_inputs_confirmed=true`. No se exige correo, celular ni evidencia alguna (CA-12 y OpenSpec lo definen así).

**Escenario**
1. Se despliega fuera de desarrollo y pruebas con `APP_ENV` sin definir, o con un valor distinto como `staging`, `prod` o `local`. Si la lógica es "habilitado salvo que sea `production`", el mock queda activo.
2. Cualquier usuario registrado llama al endpoint con dos booleanos verdaderos y pasa a `ACTIVE_FULL`.

**Impacto**
- Elevación de privilegios funcional sin verificación de identidad.
- Pasa a tope de S/500 por pago, S/1,000 diarios y recargas de terceros.
- Incumple el supuesto técnico de que el mock solo existe en desarrollo y pruebas.

**Corrección recomendada**
1. Modelar `APP_ENV` en `config.py` como enumeración cerrada, con valor por defecto **`production`** (fail-closed). Abortar el arranque si el valor es desconocido.
2. Habilitar el mock solo con lista blanca explícita: `development` y `testing`, nada más.
3. Considerar un segundo interruptor `BIOMETRIC_MOCK_ENABLED` que no pueda ser verdadero si el ambiente es `production`.
4. Verificar la puerta en el servicio, no solo en el router. Mantener el 403 definido en el contrato.
5. Añadir al arranque un log sin datos personales que indique el modo activo.

**Comprobación reproducible:** C-02.

---

### SEC-03 – El OTP mock no tiene puerta por ambiente, acepta cualquier valor y permite "validar" correos o celulares ajenos

| Campo | Detalle |
|---|---|
| **Severidad** | Media (acotada hoy porque C1/C2 no condicionan `ACTIVE_FULL`. Sube si se usan después para recuperación o límites) |
| **Confianza** | 8/10 (comportamiento explícito en la especificación) |
| **Categoría** | Autenticación / verificación de propiedad |
| **Archivo / ubicación** | OpenSpec: `profile-email-validation` y `profile-phone-validation`, requisitos "OTP … con servicio mock". Contrato: `confirmEmailOtp`, `confirmPhoneOtp`. Arquitectura §3 (`MockOtpProvider`) y decisión 5. Código no recibido: `app/otp.py`, `app/services.py`. Línea: no disponible. |

**Evidencia**
- "El mock SHALL confirmar cualquier valor ingresado mientras exista un OTP vigente". El contrato dice "confirma cualquier valor no vacío".
- A diferencia de la biometría ("solo en desarrollo y pruebas"), el OTP mock **no tiene restricción de ambiente** en la especificación, el contrato ni las tareas.
- Los índices UNIQUE parciales sobre `email_normalized` y `phone_e164` reservan el dato para quien lo confirme primero (arquitectura §5, supuesto S8).

**Escenario**
1. El atacante crea una cuenta desechable (registro abierto).
2. Solicita OTP para el correo o celular de una víctima y confirma con cualquier valor.
3. El dato queda como "validado" para el atacante.
4. Cuando la víctima intenta validar su propio dato recibe `409 EMAIL_ALREADY_REGISTERED` o `PHONE_ALREADY_REGISTERED`.

**Impacto**
- Falsa verificación de posesión. Los estados `ACTIVE_EMAIL` y `ACTIVE_MOVIL` no son confiables.
- Denegación de la validación al titular legítimo.
- Si se promueve el mock a un ambiente real, la validación queda anulada.
- Riesgo prospectivo cuando se integren SMS y correo reales:
  - El límite de 45 s es por wallet y canal, no por destinatario. Desde múltiples cuentas desechables se podría saturar el teléfono de una víctima (SMS bombing) o generar costos por envíos fraudulentos.
  - La respuesta de negocio sobre intentos fallidos ("solo tiene 3 opciones") quedó sin resolver. La arquitectura indica que el límite de intentos no se especifica. Con OTP real de 6 caracteres y 60 s de vigencia, sin límite de intentos el OTP sería adivinable.

**Corrección recomendada**
1. Aplicar la misma puerta por ambiente que a la biometría: el proveedor mock solo se instancia en `development` y `testing`. Fuera de ellos, la fábrica exige un `OtpProvider` real o el endpoint responde 503 o 403.
2. En `development` y `testing`, mantener la aceptación de "cualquier valor" detrás de un indicador explícito (por ejemplo `OTP_MOCK_ACCEPT_ANY=true`).
3. Al implementar el proveedor real:
   - Limitar intentos por desafío. Confirmar con negocio qué significa "3 opciones" y fijar el límite.
   - Limitar solicitudes por destinatario y por IP.
   - Comparar el `code_hash` con `hmac.compare_digest`.
4. Guardar `code_hash` con HMAC y clave de servidor, no con hash simple. Un código de 6 caracteres es trivialmente reversible si se filtra el hash.

**Comprobación reproducible:** C-03.

---

### SEC-04 – Exposición de datos de otras personas por consultas de unicidad (enumeración)

| Campo | Detalle |
|---|---|
| **Severidad** | Media |
| **Confianza** | 8/10 (comportamiento definido en el contrato) |
| **Categoría** | Exposición de datos sensibles / control de acceso a datos de terceros |
| **Archivo / ubicación** | Contrato: `requestEmailOtp` y `requestPhoneOtp` (409 `EMAIL_ALREADY_REGISTERED` y `PHONE_ALREADY_REGISTERED`), `checkUsernameAvailability` (`security: []`), `registerWallet` (409 `USERNAME_TAKEN`), respuestas `Forbidden` y `NotFound`. Arquitectura, secuencia §3. Línea: no disponible. |

**Evidencia**
- La unicidad se comprueba y se informa **en la solicitud de OTP, antes de demostrar posesión** del correo o celular.
- Para obtener una cuenta autenticada basta registrarse (sin verificación, sin límite descrito).
- `username-availability` no requiere autenticación y no declara limitación de tasa.
- El contrato distingue 403 (wallet ajeno) de 404 (wallet inexistente) para un usuario autenticado. Esto permite saber si un `wallet_id` existe. Con UUIDv4 el riesgo práctico es mínimo.

**Escenario**
Una cuenta desechable consulta en masa listas de correos y celulares. Las respuestas 409 revelan cuáles personas tienen billetera, y `username-availability` revela nombres de usuario existentes.

**Impacto**
- Fuga de pertenencia a la plataforma (dato personal bajo CA-10).
- Insumo para phishing dirigido y para el ataque de SEC-01.
- El requisito de rechazar duplicados es legítimo. El hallazgo es la ausencia de límites que acoten el abuso.

**Corrección recomendada**
1. Limitación de tasa por IP y por wallet para `username-availability` y para solicitudes de OTP que comprueben unicidad. Registrar solo contadores, no los valores consultados.
2. Cuando exista proveedor real, comprobar la unicidad en la **confirmación** y responder de forma uniforme en la solicitud, para no revelar pertenencia sin demostrar posesión.
3. Opcional: unificar 403 y 404 en un único 404 tras autenticar, para no revelar existencia de wallets. Requiere cambiar el contrato y la prueba `API-SEC-03/04`, y es prioridad baja.

**Comprobación reproducible:** C-04.

---

### SEC-05 – La política de contraseña es más débil de lo especificado y no impide claves triviales

| Campo | Detalle |
|---|---|
| **Severidad** | Media |
| **Confianza** | 7/10 |
| **Categoría** | Autenticación / validación de entradas |
| **Archivo / ubicación** | Contrato: `RegistrationRequest.password` (`pattern: '^[!-~]{10,64}$'`). Frontend: `field-validators.ts` (`PASSWORD_CHARS_PATTERN`, `passwordValidators`) y `password-strength.ts` (`acceptable`). `validators.spec.ts`. Línea: no disponible. |

**Evidencia**
- Aclaración del Issue: "mínimo 10 caracteres **alfanuméricos**", con símbolos permitidos y alerta de robustez.
- El patrón del contrato acepta cualquier cadena de 10 a 64 caracteres ASCII imprimibles. No exige letras ni números. Acepta `"!!!!!!!!!!"` y una cadena de 10 repeticiones de la misma letra.
- La prueba del Frontend afirma que `abcdefghij` es `acceptable: true` con nivel `weak`. La robustez es solo una alerta informativa y no bloquea.
- No se describen controles contra contraseñas comunes ni contra contraseñas iguales al usuario.
- El tope de 64 caracteres impide frases de contraseña largas.

**Escenario**
Un usuario elige una contraseña trivial que cumple el contrato. Combinado con SEC-01 (sin límite de intentos), queda expuesta a adivinación.

**Impacto**
Debilita la única barrera de autenticación de una cuenta con saldo y límites de operación.

**Corrección recomendada**
1. Validar en el servidor, en código (el diseño indica que Pydantic v2 no admite lookahead), que la contraseña:
   - Contenga al menos una letra y un dígito, según "alfanumérica".
   - Rechace repeticiones triviales (misma letra repetida, secuencias simples).
   - No contenga el nombre de usuario.
   - Se compare contra una lista corta de contraseñas comunes.
2. Subir el tope máximo a 128 como mínimo.
3. Reflejar las mismas reglas en `evaluatePasswordStrength.acceptable` y en `passwordValidators` del Frontend.
4. Pedir a producto que aclare el alcance de "alfanuméricos" frente a "permite símbolos".

**Comprobación reproducible:** C-05.

---

### SEC-06 – Endpoints públicos sin límites de uso ni de tamaño

| Campo | Detalle |
|---|---|
| **Severidad** | Baja |
| **Confianza** | 5/10 (ausencia en contrato y diseño. Código no visto) |
| **Categoría** | Disponibilidad / abuso de funcionalidad |
| **Archivo / ubicación** | Contrato: tag `Onboarding` con `security: []` (`startOnboardingSession`, `registerOnboardingStep`, `registerWallet`). Arquitectura §5 (`onboarding_sessions`, `onboarding_steps`). Línea: no disponible. |

**Evidencia**
- `POST /onboarding/sessions` y `/steps` no tienen autenticación y escriben filas en SQLite. No hay vínculo entre `session_id` y un cliente.
- No se describe limitación de tasa, tope de sesiones abiertas, TTL ni límite de tamaño de cuerpo.
- La idempotencia del registro está fuera de alcance.
- El campo `amount` (`Money`) no tiene `maxLength` en el contrato.

**Escenario**
Un cliente automatizado crea sesiones y cuentas de forma masiva. Esto llena la base y consume recursos. Además, cada cuenta nueva obtiene sus propios topes diarios sin verificación de identidad hasta la biometría real, lo que multiplica la capacidad de operación.

**Impacto**
Degradación del servicio y crecimiento descontrolado de datos. Hay un riesgo de negocio por creación masiva de cuentas, no de confidencialidad.

**Corrección recomendada**
1. Limitación de tasa por IP en `/onboarding/*`.
2. Middleware de tamaño máximo de cuerpo.
3. `maxLength` en `Money` (por ejemplo 12 caracteres).
4. Limpieza programada de `onboarding_sessions` sin completar (TTL).
5. Valorar CAPTCHA o prueba de trabajo en el registro si se expone públicamente.

**Comprobación reproducible:** C-08.

---

### SEC-07 – Nombres de usuario con `:` son incompatibles con HTTP Basic

| Campo | Detalle |
|---|---|
| **Severidad** | Baja |
| **Confianza** | 9/10 (derivable del patrón del contrato) |
| **Categoría** | Autenticación / validación de entradas |
| **Archivo / ubicación** | Contrato: `components.schemas.Usuario.pattern` (`'^[!-~]*[A-Za-z][!-~]*$'`). Frontend: `field-validators.ts` (`USUARIO_PATTERN`) y `session.store.ts` (`authorizationHeader`, que construye `usuario:contraseña`). Línea: no disponible. |

**Evidencia**
- El rango `!-~` (0x21 a 0x7E) incluye `:` (0x3A).
- HTTP Basic concatena `usuario:contraseña` y el servidor separa en el **primer** `:` (RFC 7617: el identificador de usuario no puede contener `:`).

**Escenario**
Un usuario registra `ab:cd1`. Al autenticarse, el servidor interpreta usuario `ab` y contraseña `cd1:<contraseña real>`. Falla con 401 y la cuenta queda inutilizable para el titular.

**Impacto**
Pérdida de acceso a la propia cuenta (disponibilidad e integridad del flujo). No se identificó una vía de suplantación de otra cuenta con esta condición.

**Corrección recomendada**
Excluir `:` del conjunto de símbolos permitidos para usuario. Ajustar el patrón en el contrato, en el validador del servidor y en `USUARIO_PATTERN`. Usar `^[!-9;-~]*[A-Za-z][!-9;-~]*$`, que omite el rango de 0x3A. Confirmar con producto el conjunto de símbolos.

**Comprobación reproducible:** C-06.

---

### SEC-08 – Transporte, caché y cabeceras de seguridad no definidos para credenciales Basic

| Campo | Detalle |
|---|---|
| **Severidad** | Baja |
| **Confianza** | 6/10 |
| **Categoría** | Datos sensibles en tránsito / configuración |
| **Archivo / ubicación** | Contrato: `servers` (`http://localhost:8000`). `proxy.conf.json` (`target: http://localhost:8000`). `src/index.html` (sin CSP). Informe de QA, brecha G-09 (CORS sin definir). Línea: no disponible. |

**Evidencia**
- Con HTTP Basic la contraseña viaja en **cada** petición a `/wallets/*`.
- El diagrama de arquitectura indica "HTTPS JSON", pero el contrato y el proxy apuntan a HTTP. No hay requisito de TLS, HSTS ni de `Cache-Control: no-store`.
- `index.html` no define Content-Security-Policy.
- La política CORS del backend es desconocida.
- El "cerrar sesión" del Frontend solo limpia memoria. No hay sesión en servidor que invalidar, y la contraseña sigue siendo la credencial.

**Impacto**
Interceptación de credenciales si se despliega sin TLS. Mayor exposición a XSS futuro por ausencia de CSP, aunque hoy no hay sumideros.

**Corrección recomendada**
1. Exigir TLS en el despliegue, con redirección y HSTS.
2. Enviar `Cache-Control: no-store` en respuestas de `/wallets/*`.
3. Fijar una CSP restrictiva y `X-Content-Type-Options: nosniff` en el servidor estático.
4. Configurar CORS con lista blanca de orígenes, sin comodín, si no se usa proxy.
5. Documentar que HTTP Basic es temporal para el MVP y que se reemplazará por tokens.

**Comprobación reproducible:** C-07.

---

### SEC-09 – Datos personales en reposo sin cifrado y código OTP con protección no especificada

| Campo | Detalle |
|---|---|
| **Severidad** | Baja (informativa en el alcance MVP) |
| **Confianza** | 4/10 (permisos y ruta del archivo no visibles) |
| **Categoría** | Exposición de datos sensibles |
| **Archivo / ubicación** | Arquitectura §5 (`wallet_accounts`, `wallet_profiles`, `otp_challenges.destination`, `otp_challenges.code_hash`). Tarea 1.1. Línea: no disponible. |

**Evidencia**
- Nombres, apellidos, correo y celular se almacenan en texto claro en SQLite (`wallet.db`). `otp_challenges.destination` repite el dato personal.
- La tarea 1.1 menciona permisos de archivo restringidos, pero no consta su implementación.
- El algoritmo de `code_hash` no está especificado.
- Los periodos de retención y eliminación están **fuera de alcance** por decisión del Issue. No se reporta como defecto.

**Impacto**
La lectura del archivo de base de datos expone todos los datos personales. Los desafíos OTP vencidos permanecen sin purga.

**Corrección recomendada**
1. Verificar y aplicar permisos de lectura solo para el proceso del servicio.
2. Excluir `wallet.db` del control de versiones.
3. Purgar `otp_challenges` vencidos o consumidos, lo que además reduce el volumen de datos personales.
4. Usar HMAC con clave de servidor para `code_hash`.
5. Antes de pasar a un ambiente real, migrar a un motor con cifrado en reposo y definir retención.

**Comprobación reproducible:** C-09.

---

## 3. Comprobaciones

**Estado global: ninguna comprobación de esta tabla fue ejecutada por este análisis.** Las filas "propuesta" describen el procedimiento reproducible para validar la corrección y quedan listas para ejecutarse. Los comandos usan marcadores (`$API`, `$WALLET`) y valores ficticios. No incluyen secretos reales.

| ID | Hallazgo | Procedimiento / comando | Resultado esperado tras la corrección | Estado |
|---|---|---|---|---|
| C-00 | Referencia | `pytest` en `backend/tests/` (suite del Backend) | El Backend reporta `101 passed, 1 warning` | **Ejecutada por terceros. No verificada por este análisis.** |
| C-01 | SEC-01 | `API=http://localhost:8000`; `for i in $(seq 1 30); do curl -s -o /dev/null -w "%{http_code}\n" -u "usuario_qa:clave_incorrecta" "$API/wallets/$(python -c 'import uuid;print(uuid.uuid4())')"; done \| sort \| uniq -c` | Tras N fallos aparecen respuestas **429** con `Retry-After`. Hoy se espera solo 401. | **No ejecutada (propuesta)** |
| C-02 | SEC-02 | Arrancar el backend con `APP_ENV` sin definir, luego con `production`, luego con un valor desconocido. En cada caso: `curl -s -u "$U:$P" -X POST "$API/wallets/$WALLET/profile/identity/mock-verification" -H "Content-Type: application/json" -d '{"terms_accepted":true,"mock_inputs_confirmed":true}'` y después `GET /wallets/$WALLET` | 403 `BIOMETRIC_MOCK_DISABLED` y estado `ACTIVE_BASIC`. Un valor desconocido debe impedir el arranque. | **No ejecutada (propuesta)** |
| C-03 | SEC-03 | Con dos cuentas A y B, A solicita y confirma OTP para un correo ficticio `x@example.com`. B solicita OTP para el mismo correo. Repetir con el backend en modo no desarrollo. | Hoy: B recibe 409. Tras la corrección, en ambiente no dev el endpoint no acepta OTP arbitrario. | **No ejecutada (propuesta)** |
| C-04 | SEC-04 | `for i in $(seq 1 60); do curl -s -o /dev/null -w "%{http_code}\n" -X POST "$API/onboarding/username-availability" -H "Content-Type: application/json" -d "{\"username\":\"qa$i\"}"; done \| sort \| uniq -c` | Aparecen 429 tras el umbral. Hoy se espera solo 200. | **No ejecutada (propuesta)** |
| C-05 | SEC-05 | `POST /onboarding/registrations` con una contraseña de 10 letras minúsculas iguales (valor ficticio) y usuario único | 422 `VALIDATION_ERROR`. Hoy el contrato la acepta con 201. | **No ejecutada (propuesta)** |
| C-06 | SEC-07 | `POST /onboarding/username-availability` con `{"username":"ab:cd1"}`. Si devuelve `AVAILABLE`, registrar y luego `curl -u "ab:cd1:<clave>" "$API/wallets/$WALLET"` | Tras la corrección: `INVALID_FORMAT`. Hoy: registro posible y 401 al autenticarse. | **No ejecutada (propuesta)** |
| C-07 | SEC-08 | `curl -sI "$API/wallets/$WALLET" -u "$U:$P"` y `curl -sI http://localhost:4200/` | Presencia de `Cache-Control: no-store`, `Content-Security-Policy`, `X-Content-Type-Options`. HSTS solo sobre TLS. | **No ejecutada (propuesta)** |
| C-08 | SEC-06 | `for i in $(seq 1 500); do curl -s -o /dev/null -X POST "$API/onboarding/sessions"; done`, luego contar filas de `onboarding_sessions` | Limitación de tasa activa y filas acotadas. Probar también un cuerpo de más de 1 MB. | **No ejecutada (propuesta)** |
| C-09 | SEC-09 | En Windows, `icacls <ruta-wallet.db>`. En Linux, `stat -c "%a %U" <ruta-wallet.db>`. Confirmar la ruta real en `app/config.py`. | Solo la cuenta del servicio con lectura y escritura. Archivo ausente del repositorio. | **Pendiente: ruta y código no recibidos** |
| C-10 | Sumideros XSS | `grep -rEn "innerHTML\|bypassSecurityTrust\|document\.write\|eval\(" wallet-frontend/src` | Sin coincidencias | **No ejecutada. Equivalente realizado solo por lectura manual** |
| C-11 | Secretos | `gitleaks detect --no-banner` (o equivalente) sobre todo el repositorio | Sin hallazgos. Las constantes sintéticas de prueba son esperables. | **No ejecutada** |
| C-12 | Dependencias | `pip-audit` sobre las dependencias del Backend. `npm audit --omit=dev` en `wallet-frontend`. | Sin vulnerabilidades altas o críticas sin tratar | **No ejecutada.** No se recibió `requirements` del Backend. |
| C-13 | Hash de contraseña | Revisar en `app/security.py`: algoritmo, iteraciones o costo, sal por usuario, uso de `hmac.compare_digest`, comportamiento con usuario inexistente | Parámetros dentro de las recomendaciones vigentes y tiempo uniforme | **Pendiente: código no recibido** |
| C-14 | Privacidad en logs | Ejecutar `API-SEC-06` de `qa/` con `API_LOG_FILE` definido | Ningún dato personal, contraseña ni token Basic en el log | **No ejecutada** |
| C-15 | Autorización por `wallet_id` | Ejecutar `API-SEC-01` a `API-SEC-04` de `qa/` | 401 sin credenciales, 403 con wallet ajeno, 404 con wallet inexistente | **No ejecutada.** El Backend reporta pruebas equivalentes (`tests/test_access.py`) sin verificación de este análisis. |

---

## 4. Limitaciones y preguntas abiertas

### 4.1 Limitaciones de alcance y evidencia

1. **No se recibió el código fuente del Backend.** Solo hay lista de archivos y resumen. Todo lo relativo al servidor (hash, comparaciones, consultas SQL, filtro de logs, manejo de 422, valor por defecto de `APP_ENV`) se evalúa contra contrato y diseño. No se confirmó ni descartó ninguna inyección SQL en el código del Backend.
2. **No se ejecutó nada.** Ni pruebas, ni escáneres, ni peticiones HTTP, ni compilación. No se afirma que el Frontend compile: su propio informe indica que no corrió `ng build` ni `ng test`.
3. **Sin números de línea.** La ubicación se da por archivo y símbolo o sección.
4. **El contrato `openapi/wallet-onboarding-api.yaml` no está verificado en el espacio de trabajo.** El Backend lo reporta como no comprobado. La comparación se hizo contra el texto del contrato entregado.
5. **Secretos:** en el material revisado no se observaron claves, tokens ni credenciales reales. El código de pruebas contiene una **contraseña sintética de prueba** (no se reproduce aquí). Conviene que no se reutilice fuera de pruebas. Como no se vio `config.py`, no se puede afirmar la ausencia de secretos en el Backend.
6. **Fuera de alcance por decisión del Issue, no evaluado como defecto:** emisión de tokens, idempotencia del registro, retención y eliminación de datos, texto y versión de términos, SMS y correo reales, biometría real.
7. **Datos de otras personas en el cliente:** el Frontend no maneja datos de terceros más allá de los que devuelve la API. No se detectaron exposiciones adicionales en el código recibido.
8. **No se revisó CORS, el servidor estático, la infraestructura ni la configuración de despliegue.**

### 4.2 Preguntas abiertas

1. ¿Cuál es el valor por defecto de `APP_ENV` y qué valores acepta `config.py`? (SEC-02)
2. ¿Existe alguna limitación de tasa o bloqueo por intentos de autenticación fallidos, a nivel de aplicación o de infraestructura? (SEC-01)
3. ¿Se pretende que el OTP mock exista fuera de `development` y `testing`? ¿Se acepta que "validar" correo y celular no pruebe posesión en ese caso? (SEC-03)
4. ¿Qué significa "solo tiene 3 opciones" para el OTP? ¿Son 3 intentos o 3 reenvíos? (SEC-03)
5. ¿Qué iteraciones o costo usa el hash de contraseña y se compara en tiempo constante? (SEC-01, C-13)
6. ¿Qué conjunto de símbolos admite el usuario? ¿Se acepta excluir `:`? (SEC-07)
7. ¿Cómo debe interpretarse "alfanuméricos" frente a "permite símbolos" en la contraseña? (SEC-05)
8. ¿Dónde se aloja `wallet.db`, con qué permisos y fuera del repositorio? (SEC-09)
9. ¿Se aceptará exponer la existencia de un correo o celular registrado a usuarios sin verificación de posesión, o se prefiere diferir esa comprobación? (SEC-04)
10. ¿Cuál es la política CORS prevista si el frontend se sirve sin proxy? (SEC-08)

---

## 5. Conclusión

**Qué quedó cubierto**
- Se contrastaron contra el contrato y la especificación la autenticación, la autorización por `wallet_id`, la validación de entradas, la exposición de datos de terceros y la protección de datos personales.
- Se revisó línea a línea el código completo del Frontend en busca de XSS, almacenamiento de credenciales, alcance del interceptor y registro en consola. No se encontraron sumideros XSS ni persistencia de la contraseña.
- Se identificaron 9 hallazgos con evidencia localizable y corrección propuesta:
  - **Altos:** SEC-01 (sin control anti fuerza bruta en HTTP Basic) y SEC-02 (puerta de la biometría mock que puede quedar abierta).
  - **Medios:** SEC-03 (OTP mock sin puerta por ambiente), SEC-04 (enumeración de datos de terceros) y SEC-05 (política de contraseña débil).
  - **Bajos:** SEC-06 a SEC-09.
- Se definieron 15 comprobaciones reproducibles. Tres requieren acceso al código o a la ruta del archivo de datos antes de ejecutarse.

**Qué no quedó cubierto**
- La implementación del Backend: inyección SQL real, hash, filtro de logs, saneo de errores 422 y configuración. Esto exige revisar `app/*.py`.
- Cualquier resultado de ejecución: ninguna prueba, escaneo o petición se realizó. Ningún hallazgo está confirmado dinámicamente y ninguna corrección está validada.
- Dependencias y secretos con herramientas automáticas (C-11 y C-12).
- Infraestructura, TLS, CORS y cabeceras del servidor estático.
- Los controles de retención y eliminación, fuera de alcance por la historia.

**Siguiente paso recomendado:** entregar el código del Backend para confirmar o descartar SEC-01, SEC-02 y SEC-06. Ejecutar C-01 a C-08, y ejecutar las suites de Backend y QA registrando su salida real. Las correcciones de SEC-01, SEC-02 y SEC-03 deberían resolverse antes de cualquier despliegue fuera de desarrollo y pruebas.