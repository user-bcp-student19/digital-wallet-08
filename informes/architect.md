# Informe de diseño - HU 01 Onboarding de usuario billetera digital

## 1. Resumen y alcance

**Resumen.** Se diseña el API local de onboarding de la wallet. Cubre:
- Registro de la cuenta básica `ACTIVE_BASIC`, con creación de la wallet en el proveedor externo `bcp-wallet-mock` (grupo 8).
- Medición del tiempo y de los pasos del registro.
- Complemento del perfil (correo, celular y biometría mock).
- Topes por estado de cuenta (`ACTIVE_BASIC` / `ACTIVE_FULL`).

**Dentro del alcance**
- Sesión de onboarding y registro de pasos (sin valores ingresados).
- Disponibilidad de usuario con sugerencias.
- Registro y creación de wallet (`POST /groups/8/kyc/verifications`).
- Landing: estado, saldo (`GET /groups/8/wallets/{wallet_id}`), límites y uso diario.
- OTP mock de correo y celular, con vigencia de 60 s, cooldown de 45 s, invalidación del OTP previo y 3 intentos.
- Biometría mock solo en dev y test, que lleva la cuenta a `ACTIVE_FULL`.
- Parametrización de topes y reglas de zona horaria America/Lima.

**Fuera de alcance** (según el Issue y las respuestas adicionales)
- Biometría real y carga de fotos o video del DNI (CA-11 queda como requisito futuro).
- Envío real de SMS y correo.
- Generación de tokens.
- Idempotencia del registro.
- Retención y eliminación de datos, y texto y versión de términos y condiciones.

**Decisiones clave**
- Importes en céntimos enteros, igual que el contrato externo.
- Autenticación HTTP Basic para los endpoints posteriores al registro (supuesto S1).
- La disponibilidad de usuario usa POST para evitar datos en la query string, que suele quedar en logs de proxies.
- El OTP nunca se devuelve en las respuestas. Es un servicio mock interno, porque no existe contrato OTP en `client/openapi`.
- La contraseña se almacena solo como hash con un algoritmo adaptativo (Argon2id o bcrypt). Nunca se registra ni se envía a analítica.
- El middleware de logging y analítica aplica una lista de redacción sobre password, correo, celular, nombres y OTP.

## 2. Componentes y responsabilidades

| Componente | Responsabilidad |
|---|---|
| App Wallet (cliente) | Pantallas de onboarding, landing y perfil. Dispara la sesión al ser visible. Muestra la validación en vivo de cada campo y la robustez de la contraseña. Muestra el aviso de perfil pendiente. |
| Capa HTTP | Valida contrato y esquemas, aplica AuthN Basic y la coincidencia `user_id` con el usuario autenticado, mapea errores y redacta logs y analítica. |
| Onboarding Service | Crea la sesión, registra pasos únicos y calcula `duration_ms` al emitir la respuesta del registro. |
| User Service | Reglas de nombres, apellidos y usuario. Disponibilidad y sugerencias sin símbolos. Política de contraseña (mínimo 10) y hash. Alta con reserva de usuario único. |
| Account Service | Orquesta la creación de cuenta `ACTIVE_BASIC` con saldo 0, guarda `wallet_id`, compone la landing (saldo del proveedor, límites, uso) y gestiona la transición a `ACTIVE_FULL`. |
| Limits Service | Resuelve topes parametrizables según el estado y lleva el contador diario en America/Lima con reinicio por hora del servidor. Expone la función de validación para las futuras operaciones de pago y recarga. |
| Profile Service | Mantiene los flags independientes de correo, celular y biometría. Valida formato y unicidad de correo y celular. |
| OTP Service (mock interno) | Genera OTP de 6 caracteres, vigencia 60 s, cooldown 45 s, invalida los anteriores y limita a 3 intentos. No envía ni expone el valor. Con el mock activo acepta cualquier valor de 6 caracteres si hay un OTP vigente. |
| Biometric Mock Service | Solo en dev y test (ambiente por configuración). Verifica los inputs (aceptación de términos) y marca la biometría como activa. No procesa imágenes ni video. |
| Wallet Gateway | Adaptador del proveedor externo. Define timeouts (mayores que 5 s, por la latencia simulable del mock), mapea errores y no propaga el header de latencia. |
| Configuración | Topes por estado, ambiente, TTL y cooldown de OTP, intentos, timeouts. |
| Persistencia | Usuarios, hash de contraseña, perfil, OTP (almacenados con hash), sesiones de onboarding, contadores diarios. |

Los componentes de SMS, correo y biometría real se muestran en el diagrama solo como puntos de extensión futuros.

## 3. APIs externas de `client/openapi` utilizadas

Archivo: `bcp-wallet-mock-openapi.yaml` (Wallet mock W1–W6 v0.3.0). Base: `https://bcp-wallet-mock.yefri.workers.dev/groups/8`.

| Operación externa | Uso | Mapeo local |
|---|---|---|
| `POST /kyc/verifications` | Crear la wallet con KYC simulado en el registro (CA-03). | 201 Kyc pasa a 201 de `/onboarding/registrations` con `wallet_id`. 400 y 413 pasan a 502 `WALLET_PROVIDER_REJECTED`. Timeout o 5xx pasan a 503 o 504. |
| `GET /wallets/{wallet_id}` (indicada en el Issue) | Obtener el saldo para la landing (CA-03). | 200 pasa a `balance_cents` en `/users/{user_id}/account`. 404 pasa a 502 `WALLET_NOT_FOUND_IN_PROVIDER`. Otros errores pasan a 502, 503 o 504. |

No se usan `/health`, `/scenarios` ni `/openapi.json` en el flujo funcional. El contrato recibido está truncado: no se ve el esquema de solicitud de Kyc, el de respuesta Kyc, el de la wallet, ni las respuestas posteriores a 413. El mapeo anterior es el diseño propuesto y debe confirmarse contra el contrato completo.

## 4. Trazabilidad de criterios de aceptación

| CA | Componente que lo resuelve | Endpoint o mecanismo |
|---|---|---|
| CA-01 | Onboarding Service y cliente | `POST /onboarding/sessions`, `POST /onboarding/sessions/{id}/steps`. La validación en vivo se hace en el cliente. La disponibilidad de usuario se valida en el servidor. |
| CA-02 | User Service, cliente y esquemas OpenAPI | Patrones y longitudes en `Nombres`, `Apellido`, `Username` y `Password`. `POST /onboarding/username-availability`. La robustez de la contraseña se alerta en el cliente y se aplica mínimo 10 en el servidor. La contraseña no se registra (Capa HTTP). |
| CA-03 | Account Service y Wallet Gateway | `POST /onboarding/registrations` crea la wallet con `POST /groups/8/kyc/verifications` y devuelve `ACTIVE_BASIC`, saldo 0, `wallet_id` y `welcome_name`. El saldo se consulta con `GET /groups/8/wallets/{wallet_id}` vía `GET /users/{id}/account`. `duration_ms` cierra la medición (Q7). |
| CA-04 | Account Service y cliente | `profile_completion_pending` y `Profile.pending_items`. |
| CA-05 | Limits Service y Configuración | `AccountLimits` y `DailyUsage` en `GET /users/{id}/account`. Topes de 2000 por operación y 6000 combinados diarios, parametrizables. Contador por día en America/Lima. |
| CA-06 | Profile Service | `GET /users/{id}/profile`. Flags independientes y sin orden obligatorio, con valores iniciales `PENDING_EMAIL`, `PENDING_MOVIL` y `PENDING_BIOM`. |
| CA-07 | Profile Service y OTP Service | `email/otp-requests` y `email/otp-verifications`. Formato y unicidad (409), vigencia 60 s (410), cooldown 45 s (429), OTP nuevo invalida los previos, `ACTIVE_EMAIL` al validar. OTP mock sin envío. |
| CA-08 | Profile Service y OTP Service | `phone/otp-requests` y `phone/otp-verifications`. Móvil peruano `^9[0-9]{8}$`, prefijo +51 fijo, mismas reglas de OTP. |
| CA-09 | Biometric Mock Service | `POST /users/{id}/biometrics/mock-verifications`. Solo dev y test (404 en otros ambientes). Sin verificación biométrica real. |
| CA-10 | Capa HTTP, Biometric Mock y Persistencia | `terms_accepted` obligatorio. Redacción de logs y analítica. El mock no recibe fotos ni video. Los controles de retención y eliminación están fuera de alcance (respuesta Q8). |
| CA-11 | Documentado, sin implementación | Requisito para la futura integración real: DNI de ambas caras hasta 2 MB, video de 5 a 10 s hasta 10 MB, nitidez y metadato de grabación en los últimos 10 min. No hay endpoint en esta entrega. |
| CA-12 | Account Service y Biometric Mock | La verificación mock exitosa lleva la cuenta a `ACTIVE_FULL`. |
| CA-13 | Limits Service y Configuración | `AccountLimits` para `ACTIVE_FULL`: recargas propias y de terceros hasta 100000 diarios, pagos hasta 50000 por operación y 100000 diarios, con reinicio en America/Lima. |

## 5. Supuestos y preguntas pendientes

**Supuestos adoptados**
- **S1.** La autenticación posterior al registro es HTTP Basic (usuario y password), porque no hay tokens (Q2). El registro y los endpoints de `/onboarding` son públicos.
- **S2.** Cada validación (correo, celular, biometría) es un flag independiente (Q9). `ACTIVE_FULL` se alcanza solo con la biometría mock, sin exigir correo ni celular validados.
- **S3.** "Solo tiene 3 opciones" para el OTP se interpreta como 3 intentos. Al agotarlos se debe solicitar un OTP nuevo (429 `OTP_ATTEMPTS_EXCEEDED`).
- **S4.** Con el mock de OTP activo, cualquier valor de 6 caracteres se confirma, pero se exige un OTP vigente (60 s). Un OTP vencido o invalidado responde 410.
- **S5.** La política de contraseña es mínimo 10 caracteres (Q3). Se admiten símbolos según CA-02.
- **S6.** Los nombres de los estados `ACTIVE_MOVIL` y `ACTIVE_BIOM` son supuestos por analogía con `ACTIVE_EMAIL`.
- **S7.** El límite diario de `ACTIVE_BASIC` es combinado (Q1). Para `ACTIVE_FULL` se asume tope diario separado por tipo (pagos 100000, recargas 100000) y sin tope por operación en recargas.
- **S8.** Un fallo del proveedor tras reservar el usuario libera la reserva. Sin idempotencia (Q10) un reintento tras timeout puede crear una wallet huérfana en el proveedor. Se acepta como riesgo del MVP.
- **S9.** El ambiente dev y test se determina por configuración. En cualquier otro ambiente la ruta de biometría mock responde 404.
- **S10.** Los 128 caracteres máximos de contraseña son un límite técnico propio.

**Preguntas pendientes**
1. Contrato externo truncado: ¿cuál es el cuerpo de solicitud de `POST /kyc/verifications` y qué datos del usuario se pueden enviar al mock sin violar CA-10? ¿Cuál es el esquema de respuesta Kyc, en particular el nombre del campo de `wallet_id` y su estado KYC?
2. ¿Cuál es el esquema de `GET /groups/8/wallets/{wallet_id}` y cuáles son sus respuestas de error (saldo y campos)?
3. ¿Los escenarios del mock (`/scenarios`) pueden devolver KYC rechazado o pendiente? Hoy no se mapea ese caso.
4. CA-05 y CA-13 exigen aplicar los topes en pagos y recargas, pero el contrato visible no incluye endpoints de pago ni recarga. ¿Se implementan en otra HU? Este diseño solo expone límites y uso, y deja la función de validación en Limits Service.
5. CA-02: ¿cuál es el mínimo de longitud y el conjunto de símbolos permitidos para el usuario? ¿Se permiten dígitos en el usuario? Además hay tensión entre "permite símbolos" (CA-02) y "alfanuméricos" (Q3) para la contraseña.
6. ¿Qué inputs debe verificar el mock biométrico además de la aceptación de términos? ¿Cómo se denomina el estado de biometría validada?
7. ¿Se espera que `ACTIVE_FULL` quede condicionado en producción a correo y celular validados? El diseño actual dice que no (S2).
8. ¿El tope diario de `ACTIVE_FULL` es separado por tipo (supuesto S7) o combinado?
9. ¿Cuál es la vigencia de la sesión de onboarding y qué ocurre si el usuario abandona? Hoy no hay expiración definida.
10. ¿El tiempo de registro y los pasos se exponen a alguna herramienta de métricas? Si es así, solo sin datos personales.

<<<FIN>>>