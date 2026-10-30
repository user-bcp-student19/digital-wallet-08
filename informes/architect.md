# Informe de diseño: HU 01 Onboarding de usuario, billetera digital

## 1. Resumen y alcance

**Resumen.** La solución es una API local que orquesta el onboarding. Mide el tiempo de registro y valida los datos. Verifica la disponibilidad del usuario y crea la cuenta `ACTIVE_BASIC` con una wallet real del Wallet mock del grupo 8. También gestiona el perfil complementario (correo, celular y biometría mock) hasta `ACTIVE_FULL`, y expone los límites por nivel.

**Dentro del alcance**
- Sesión y métricas de onboarding (CA-01).
- Validaciones de campos y disponibilidad de usuario con sugerencias (CA-02).
- Registro y creación de wallet vía `POST /kyc/verifications`. Consulta de saldo vía `GET /wallets/{wallet_id}` (CA-03).
- Aviso de perfil pendiente (CA-04) y límites parametrizables por estado (CA-05, CA-13).
- Validación de correo y celular con OTP mock interno (CA-06, CA-07, CA-08).
- Biometría mock solo en dev/test, que lleva a `ACTIVE_FULL` (CA-09, CA-12).
- Controles de PII: sin logs ni analítica con datos del cliente, y aceptación de términos en el paso biométrico (CA-10).

**Fuera del alcance**
- Envío real de correo o SMS.
- Biometría real, subida de fotos del DNI y video. Los requisitos de CA-11 se documentan para una entrega futura, sin endpoints.
- Generación de tokens y login.
- Retención y eliminación de datos, y texto y versión de los términos y condiciones.
- Idempotencia del registro.

**Requisitos de CA-11 para la futura biometría real (sin implementación ahora)**
- Fotos de ambas caras del DNI, de hasta 2 MB cada una.
- Video de 5 a 10 s, de hasta 10 MB.
- Aviso al usuario de que las imágenes sean nítidas.
- Metadatos del video con grabación en los últimos 10 minutos.

## 2. Componentes y responsabilidades

| Componente | Responsabilidad |
|---|---|
| App cliente (Onboarding, Landing, Perfil) | Valida formatos en vivo. Indica el inicio visible de la pantalla. Muestra bienvenida, condiciones y aviso de perfil pendiente. |
| Sesión y Métricas de Onboarding | Crea la sesión con `started_at` del servidor y registra los pasos (solo nombres de paso, sin valores). Calcula la duración al cierre del registro. |
| Disponibilidad y Sugerencias de Usuario | Valida el formato y la disponibilidad del usuario. Genera sugerencias alfanuméricas sin símbolos a partir de nombres, apellidos y números. |
| Registro de Usuario | Valida el payload y la política de contraseña (mínimo 10 caracteres, letras y números, símbolos permitidos). Guarda la contraseña con hash. Orquesta la creación de la wallet y persiste la cuenta `ACTIVE_BASIC` con saldo 0. Devuelve bienvenida, límites y aviso. |
| Wallet Gateway | Único punto que llama al Wallet mock (`POST /kyc/verifications`, `GET /wallets/{wallet_id}`). Aplica timeouts y traduce errores a 502 o 504, según la tabla de mapeo del contrato. |
| Perfil y Estados | Mantiene `account_status` y los flags C1, C2 y C3, que son independientes. Devuelve el perfil y los límites vigentes. |
| OTP Mock interno | Genera un OTP de 6 caracteres con vigencia de 60 s. Aplica el intervalo de 45 s entre solicitudes y la invalidación del OTP anterior. Controla 3 intentos. No envía nada y, en el mock, acepta cualquier código de 6 caracteres vigente. |
| Biometría Mock | Disponible solo en dev/test mediante feature flag por ambiente. Exige `accepted_terms`, no procesa archivos y pasa la cuenta a `ACTIVE_FULL`. |
| Política de Límites | Mantiene los topes parametrizables por estado, en configuración y no en código. Zona horaria `America/Lima`, con reinicio diario según la hora del servidor. Es consultada por los flujos de pago y recarga. |
| Observabilidad con redacción | Logs y métricas sin PII ni contraseñas. Solo trazas técnicas, pasos y duraciones. |
| Persistencia local | Usuarios, sesiones, OTP, estados y configuración de límites. |

**Valores por defecto de la Política de Límites (en céntimos)**

| Estado | Por operación | Diario |
|---|---|---|
| `ACTIVE_BASIC` | 2000 en pagos y recargas | 6000 combinado entre pagos y recargas |
| `ACTIVE_FULL` | Pagos 50000. Recargas sin tope | Pagos 100000. Recargas 100000. Admite recargas de terceros |

## 3. APIs externas de `client/openapi` utilizadas

Archivo: `bcp-wallet-mock-openapi.yaml` (Wallet mock W1–W6 v0.3.0). Está configurado con base `https://bcp-wallet-mock.yefri.workers.dev/groups/8`. El contrato local usa `http://127.0.0.1:8787`, y la base debe ser configurable por ambiente.

| Operación externa | Uso | Mapeo local |
|---|---|---|
| `POST /kyc/verifications` | Crea la wallet en el registro (CA-03) | 201 → 201 local con `wallet_id`. 400 y 413 → 502 `EXTERNAL_BAD_REQUEST`, porque el cuerpo lo genera el sistema. Timeout → 504. Otros errores → 502 |
| `GET /wallets/{wallet_id}` | Obtiene el saldo (CA-03) | 200 → `WalletBalance`. 404 → 404 `WALLET_NOT_FOUND`. 400 → 502. Timeout → 504 |
| `/health`, `/scenarios`, `/openapi.json` | No se usan en el flujo. `/health` podría servir como chequeo de dependencia | Ninguno |

**Limitación.** El extracto del contrato recibido está truncado. No se ven el esquema `Kyc`, el cuerpo de la solicitud de `POST /kyc/verifications`, el contrato completo de `GET /wallets/{wallet_id}` ni los demás códigos de respuesta. Los nombres de campo (`wallet_id`, saldo) y los códigos externos adicionales deben confirmarse contra el archivo completo. No se inventaron campos del cuerpo externo.

## 4. Trazabilidad de criterios de aceptación

| CA | Componente / endpoint que lo resuelve |
|---|---|
| CA-01 | Sesión y Métricas: `POST /onboarding/sessions`, `POST /onboarding/sessions/{id}/steps`. La validación en vivo está en la app y en `POST /usernames/availability-checks`. |
| CA-02 | Registro de Usuario: `RegisterUserRequest` (patrones y longitudes). Disponibilidad y Sugerencias: `/usernames/availability-checks` y 409 con `suggestions`. La contraseña es `writeOnly`, con hash, y Observabilidad la excluye. |
| CA-03 | `POST /users` (Registro + Wallet Gateway → `POST /kyc/verifications`). Devuelve `wallet_id`, `ACTIVE_BASIC`, saldo 0, bienvenida por nombre y límites. `registration_metrics` cierra la medición. `GET /users/{id}/wallet` → `GET /wallets/{wallet_id}`. |
| CA-04 | `profile_pending_notice` en el registro y en el perfil. |
| CA-05 | Política de Límites: `limits` (`COMBINED`: 2000 por operación y 6000 diarios). Topes parametrizables, `America/Lima`. |
| CA-06 | Perfil y Estados: `GET /users/{id}/profile`. Estados iniciales `PENDING_EMAIL`, `PENDING_MOVIL` y `PENDING_BIOM`, en cualquier orden. |
| CA-07 | `POST /users/{id}/email-verification` y `/email-verification/confirm`, con OTP Mock. Cubre formato, unicidad (409), vigencia de 60 s, 45 s entre solicitudes (429), invalidación del OTP previo y paso a `ACTIVE_EMAIL`. |
| CA-08 | `POST /users/{id}/mobile-verification` y `/mobile-verification/confirm`. Patrón `^9[0-9]{8}$`, prefijo `+51` fijo, mismas reglas de OTP. |
| CA-09 | Biometría Mock: `POST /users/{id}/biometric-verification/mock`. Solo dev/test (403 en otros ambientes). Sin verificación real. |
| CA-10 | `accepted_terms` en el paso biométrico. Sin PII en logs ni analítica (Observabilidad). Datos personales fuera de la URL (POST con cuerpo). El mock no recibe fotos ni video. Retención y eliminación: fuera de alcance. |
| CA-11 | No se implementa. Requisitos registrados en la sección 1 para la entrega futura. |
| CA-12 | El mock deja `account_status = ACTIVE_FULL` y aplica los límites FULL. |
| CA-13 | Política de Límites: `SEPARATE`, pagos 50000 por operación y 100000 diarios, recargas 100000 diarios, `allows_third_party_recharges: true`. |

## 5. Supuestos

1. El contador diario de `ACTIVE_BASIC` combina pagos y recargas (respuesta 1). En `ACTIVE_FULL` no hay tope por operación para recargas. Los contadores diarios de pagos y recargas son independientes, y esto se confirma en la pregunta 8.
2. No hay token ni login en esta entrega. Los endpoints se identifican por `user_id` (UUID).
3. Contraseña: mínimo 10 caracteres con letras y números, y se permiten símbolos. Se interpreta que "alfanuméricos" fija el mínimo y no prohíbe símbolos (CA-02).
4. La validación en vivo de formato la hace el cliente y el servidor revalida. La disponibilidad de usuario es la única validación en vivo contra el servidor.
5. La medición de tiempo termina al generar la respuesta del registro (`completed_at` y `duration_ms`).
6. OTP: 6 caracteres, 60 s de vigencia, 45 s entre solicitudes. "3 opciones" se interpreta como 3 intentos fallidos, y al agotarlos se bloquea ese OTP (423). El mock acepta cualquier código de 6 caracteres vigente.
7. El OTP nunca se devuelve en la respuesta y no existe servicio OTP externo.
8. Unicidad de correo y celular: se compara contra los ya registrados por otros usuarios, normalizados y sin distinguir mayúsculas.
9. Cada validación es un flag independiente. La biometría mock pasa a `ACTIVE_FULL` sin exigir correo ni celular validados (respuesta 9).
10. Los nombres `ACTIVE_MOVIL` y `ACTIVE_BIOM` son supuestos por analogía con `ACTIVE_EMAIL`.
11. El saldo inicial es 0 por definición de CA-03. El saldo real se consulta aparte en `GET /users/{id}/wallet`.
12. Los topes se guardan en configuración, en céntimos, y se exponen por nivel.
13. Sin idempotencia (respuesta 10). Un fallo de persistencia tras crear la wallet puede dejar una wallet huérfana en el externo. Se acepta como riesgo del MVP.

## 6. Preguntas pendientes

1. ¿Puede entregarse el archivo OpenAPI externo completo? Faltan el esquema `Kyc`, el cuerpo de `POST /kyc/verifications`, `GET /wallets/{wallet_id}` y los códigos restantes.
2. ¿Quién aplica los topes de CA-05 y CA-13 en pagos y recargas? Esos endpoints no están en los contratos visibles, y esta entrega solo expone `limits` y la Política de Límites.
3. ¿La sesión de onboarding debe expirar? ¿Cuál es el tiempo máximo y qué pasa si el registro falla y se reintenta?
4. ¿Cuál es la longitud mínima del usuario y qué símbolos están permitidos? Además, ¿cuántas sugerencias debe devolverse (se asumió un máximo de 5)?
5. ¿Los nombres finales de ESTADO_C2 y ESTADO_C3 son `ACTIVE_MOVIL` y `ACTIVE_BIOM`?
6. ¿Qué "inputs" verifica la biometría mock (por ejemplo número de DNI)? Solo se incluye `accepted_terms`.
7. ¿La aceptación de términos también se exige en el registro, dado que ya se recolectan datos personales, o solo en el paso biométrico?
8. ¿Los topes diarios de pagos y recargas de `ACTIVE_FULL` son contadores independientes?
9. ¿Cómo se protegen los endpoints de perfil y verificación sin token? El riesgo es que cualquiera que conozca un `user_id` pueda operar.
10. ¿Cómo se configura el ambiente dev/test que habilita la biometría mock (variable de entorno o feature flag)?
11. Si el Wallet mock devuelve un saldo distinto de 0 tras la creación, ¿cuál prevalece?

<<<FIN>>>