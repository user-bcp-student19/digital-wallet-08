# Propuesta: HU 02 - Onboarding de usuario billetera digital (Wallet)

## Why
Las personas naturales que realizan compras, pagos y recargas de montos pequeños necesitan crear una cuenta de billetera digital con un flujo de onboarding sencillo. Después deben poder completar su perfil (correo, celular, identidad) para subir de nivel de validación y operar con los límites que corresponden a ese nivel.

La entrega permite iniciar operaciones con una cuenta básica (`ACTIVE_BASIC`) y probar el recorrido completo hasta `ACTIVE_FULL`. Para ello se usan servicios mock de OTP y de biometría, porque el envío real de SMS y correo y la validación biométrica real quedan para entregas posteriores.

## What Changes
- Se agrega el registro de onboarding con los campos nombres, apellido paterno, apellido materno, usuario (con disponibilidad y sugerencias) y contraseña. Incluye validación en línea y medición del tiempo y de los pasos completados.
- Al finalizar el registro se crea una cuenta con saldo S/0, estado `ACTIVE_BASIC` y `wallet_id` válido. Se muestra la landing con bienvenida por nombre real, condiciones de operación y aviso de perfil pendiente.
- Se agregan los límites operativos por estado (`ACTIVE_BASIC` y `ACTIVE_FULL`), parametrizables, con día calendario en zona horaria de Perú según la hora del servidor.
- Se agrega la pantalla de perfil con tres estados complementarios independientes, completables en cualquier orden:
  - `ESTADO_C1` (correo): `PENDING_EMAIL` pasa a `ACTIVE_EMAIL`.
  - `ESTADO_C2` (celular): `PENDING_MOVIL`.
  - `ESTADO_C3` (identidad): `PENDING_BIOM`.
- Se agrega la validación de correo y de celular (prefijo +51 fijo, 9 dígitos que empiezan con 9) mediante OTP de 6 caracteres. El OTP vence a los 60 s, se puede pedir uno nuevo cada 45 s y cada OTP nuevo invalida los anteriores. La generación y el "envío" son simulados con un mock.
- Se agrega el flujo mock de biometría, disponible solo en desarrollo y pruebas. Verifica inputs sin procesar datos biométricos reales y lleva la cuenta a `ACTIVE_FULL`.
- Se agregan las reglas de protección de datos personales: aceptación de términos y condiciones, y exclusión de datos personales y contraseña de analítica y logs.
- Se documentan los requisitos para la futura biometría real (DNI ≤ 2 MB por cara, video de 5 a 10 s ≤ 10 MB, grabado en los últimos 10 minutos). No se implementan en esta entrega.

### Supuestos y decisiones tomadas de las aclaraciones del Issue
- Los S/60 diarios de `ACTIVE_BASIC` son un tope combinado de pagos y recargas. En `ACTIVE_FULL` las recargas (S/1,000 diarios) y los pagos (S/1,000 diarios) tienen cada uno su propio tope diario. No hay tope por operación para recargas en `ACTIVE_FULL`.
- Contraseña: mínimo 10 caracteres alfanuméricos. Se permiten símbolos y se alerta sobre su robustez.
- No se fija una longitud mínima para el usuario, porque el Issue no la define.
- OTP de 6 caracteres. Como el mock acepta cualquier valor, se interpreta que "cualquier valor se confirma" mientras exista un OTP vigente (no vencido ni invalidado) para ese destino. Así siguen siendo verificables la vigencia de 60 s y la invalidación por regeneración. El límite de intentos fallidos no se especifica porque el mock confirma cualquier valor.
- El estado validado de `ESTADO_C2` se nombra `ACTIVE_MOVIL` por analogía con `ACTIVE_EMAIL`. El Issue no lo nombra explícitamente y queda por confirmar.
- Las validaciones de correo, celular e identidad son flags independientes. Ninguna es prerrequisito de otra, ni de `ACTIVE_FULL`.
- La medición del tiempo de registro termina cuando concluye la respuesta del registro, no cuando la landing se pinta en el cliente.
- Fuera de alcance:
  - Generación de tokens de autenticación (la autenticación es por usuario y contraseña).
  - Idempotencia del registro.
  - Periodos de retención, procesos de eliminación y texto o versión de los términos y condiciones.
  - Envío real de SMS y correo.
  - Biometría real.

## Capabilities

### New Capabilities
- `wallet-onboarding-registration`: Registro de onboarding con validación de campos en línea, disponibilidad y sugerencias de usuario, medición de tiempo y pasos, creación de cuenta `ACTIVE_BASIC` con `wallet_id`, y landing con bienvenida, condiciones y aviso de perfil pendiente.
- `wallet-operation-limits`: Topes parametrizables por operación y diarios para recargas y pagos en `ACTIVE_BASIC` y `ACTIVE_FULL`, con corte diario en zona horaria de Perú según la hora del servidor.
- `profile-email-validation`: Validación de correo electrónico (formato, unicidad y OTP mock con vigencia, frecuencia e invalidación) y transición de `ESTADO_C1`.
- `profile-phone-validation`: Validación de celular peruano (prefijo +51 fijo, formato, unicidad y OTP mock con vigencia, frecuencia e invalidación) y transición de `ESTADO_C2`.
- `biometric-mock-activation`: Flujo mock de biometría solo en desarrollo y pruebas, transición a `ACTIVE_FULL`, y requisitos documentados para la futura biometría real.
- `personal-data-protection`: Aceptación de términos y condiciones para el tratamiento de datos personales y exclusión de datos personales y contraseña de analítica y logs.

### Modified Capabilities

## Impact
- **Backend:** nuevos servicios de registro, cuentas y wallets, perfil, OTP mock, biometría mock y control de límites. Se requiere un almacén de parámetros de topes y estados de cuenta y perfil. No existen contratos en `client/openapi`, por lo que se deberán definir en la implementación.
- **Frontend:** pantalla de onboarding con validación en línea, landing y pantalla de perfil con los flujos de correo, celular e identidad (mock).
- **Observabilidad y seguridad:** instrumentación de tiempo y pasos de registro sin datos personales. Las contraseñas y los datos personales no se envían a analítica ni a logs.
- **Ambientes:** el flujo mock de biometría se habilita solo en desarrollo y pruebas.
- **Dependencias futuras:** proveedores reales de SMS, correo y biometría (entregas posteriores).
