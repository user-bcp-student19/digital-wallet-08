## Resumen y alcance

La propuesta cubre el registro de una cuenta `ACTIVE_BASIC`, la consulta del saldo del wallet, el seguimiento del onboarding, la gestión de estados complementarios del perfil y las simulaciones de OTP y biometría. Las políticas de operación se entregan como límites configurables por estado.

El API local integra el Wallet mock para crear y consultar el wallet. No se implementan pagos ni recargas, el envío real de correo o SMS, ni la verificación biométrica real. Tampoco se implementa carga o procesamiento de documentos o videos.

Los importes del contrato local se expresan en céntimos de PEN. Así, S/20 equivale a `2000`, S/60 a `6000`, S/500 a `50000` y S/1,000 a `100000`.

## Componentes y responsabilidades

- **Aplicación web o móvil:** inicia la medición cuando la pantalla es visible, muestra validaciones en tiempo real y presenta la landing. La validación sintáctica inmediata de campos puede ejecutarse en el cliente; el servidor vuelve a validar al registrar.
- **API local de onboarding:** expone el contrato, valida solicitudes, registra pasos y coordina la creación de la cuenta.
- **Servicio de registro y perfil:** persiste la cuenta, el wallet_id, los estados del perfil y la duración del registro.
- **Adaptador Wallet:** llama al endpoint de creación KYC y consulta el saldo antes de completar el alta.
- **Servicio OTP mock:** genera OTP con vigencia de 60 segundos, intervalo mínimo de 45 segundos e invalida el OTP anterior. No envía correo ni SMS.
- **Servicio de límites:** obtiene los topes configurables de acuerdo con `ACTIVE_BASIC` o `ACTIVE_FULL`, usando la zona horaria `America/Lima`.
- **Persistencia y controles de privacidad:** protege los datos de cuenta y perfil y registra el progreso sin incluir contraseñas ni datos personales en logs o analítica.
- **Simulación biométrica:** disponible solo en desarrollo y pruebas; comprueba el consentimiento y no procesa documentos, fotografías, videos ni biometría real.

## APIs externas de `client/openapi`

El Issue especifica el Wallet mock del grupo 8:

- `POST https://bcp-wallet-mock.yefri.workers.dev/groups/8/kyc/verifications`: creación del wallet mediante KYC simulado.
- `GET https://bcp-wallet-mock.yefri.workers.dev/groups/8/wallets/{wallet_id}`: consulta del saldo del wallet.

El contrato visible `bcp-wallet-mock-openapi.yaml` indica OpenAPI 3.0.3, importes enteros en céntimos PEN y una respuesta `201` del endpoint KYC referenciada como `Kyc`. El fragmento proporcionado termina antes de mostrar los esquemas completos y el contrato de consulta de wallet. Por ello, el mapeo local expresa la correspondencia semántica (`walletId` y `balanceMinor`), pero no afirma nombres de propiedades externas que no aparecen en el material recibido. Se requiere el contrato completo para fijar esos mapeos con exactitud.

No se identifican contratos OpenAPI para servicios externos de OTP, correo, SMS o biometría. En esta entrega, OTP y biometría son mocks locales; los envíos reales y la biometría real quedan fuera de alcance.

## Trazabilidad de criterios de aceptación

| Criterio | Componente que lo resuelve |
|---|---|
| **CA-01** Inicio al hacerse visible, duración y pasos | Aplicación inicia `POST /v1/onboarding/sessions` al mostrar la pantalla; la API persiste `visibleAt`, pasos y finalización. Las validaciones se muestran en la aplicación mientras se ingresan los campos. |
| **CA-02** Datos, disponibilidad de usuario y contraseña | Aplicación y API validan nombres y apellidos; `POST /v1/onboarding/usernames/availability` comprueba disponibilidad y devuelve sugerencias. La contraseña se envía solo al registro, es write-only y se excluye de logs y analítica. |
| **CA-03** Cuenta básica, wallet, saldo, landing y bienvenida | Servicio de registro y adaptador Wallet crean el wallet, consultan saldo y persisten cuenta `ACTIVE_BASIC`. La respuesta local incluye wallet_id, saldo, nombre real y duración. |
| **CA-04** Aviso de perfil pendiente | La respuesta de registro incluye estados pendientes y `profileCompletionRequired`; la aplicación presenta el aviso en la landing. |
| **CA-05** Operaciones y límites `ACTIVE_BASIC` | Servicio de límites entrega topes configurables: hasta S/20 por operación y S/60 diarios para pagos y recargas, con reinicio según hora de Perú. La ejecución de pagos y recargas no forma parte de este contrato. |
| **CA-06** Validaciones de perfil en cualquier orden | Endpoints de correo y celular son independientes. El perfil inicia con `PENDING_EMAIL`, `PENDING_MOVIL` y `PENDING_BIOM`. |
| **CA-07** Correo y OTP | Endpoint de OTP comprueba formato y unicidad, aplica vigencia y cadencia, y el endpoint de verificación activa `ACTIVE_EMAIL`. No se envía correo real. |
| **CA-08** Celular y OTP | Endpoint de celular aplica prefijo fijo `+51`, unicidad, vigencia y cadencia; el endpoint de verificación actualiza el perfil. No se envía SMS real. |
| **CA-09** Biometría mock | Endpoint de simulación, habilitado en desarrollo y pruebas, no realiza verificaciones biométricas reales. |
| **CA-10** Consentimiento y privacidad | El endpoint mock requiere aceptación de términos. La arquitectura excluye datos personales de analítica y logs y contempla controles de acceso, retención y eliminación. |
| **CA-11** Requisitos para futura integración | No se implementan cargas de DNI o video. Los tamaños, duración, nitidez y metadatos indicados se reservan para la integración futura. |
| **CA-12** Activación simulada completa | La simulación exitosa cambia la cuenta local a `ACTIVE_FULL` y devuelve los límites de ese estado. |
| **CA-13** Límites `ACTIVE_FULL` | El servicio de límites informa recargas propias y de terceros hasta S/1,000 diarios, y pagos hasta S/500 por operación y S/1,000 diarios, con reinicio según hora de Perú. La ejecución de las operaciones no está incluida. |

## Supuestos y preguntas pendientes

- El fragmento OpenAPI del Wallet mock está incompleto. Se requiere el archivo íntegro para determinar los campos exactos de creación, el identificador de wallet y la respuesta de saldo.
- Se interpreta que los S/60 diarios de `ACTIVE_BASIC` aplican por separado a pagos y recargas; debe confirmarse si el tope es combinado. También debe confirmarse si ambos tipos comparten el máximo de S/20 por operación.
- No se define un máximo por operación para recargas `ACTIVE_FULL`; el contrato no lo inventa.
- El Issue no especifica el nombre del estado activo de celular ni el estado de perfil posterior a la simulación biométrica. Se debe acordar el vocabulario de esos estados.
- El Issue no fija una política concreta de robustez de contraseña ni las reglas detalladas de validación del celular; deben definirse antes de implementar esas validaciones.
- Como el envío de correo y SMS está fuera de alcance, se asume que el OTP de prueba podrá obtenerse de forma segura en desarrollo/pruebas. El contrato permite `debugCode` solo en esos ambientes; debe acordarse el mecanismo definitivo.
- No se especifica autenticación ni autorización para las operaciones locales por cuenta. Debe definirse antes de exponer los endpoints fuera de entornos controlados.
- Deben concretarse retención, eliminación, controles de acceso y manejo de fallos parciales. En particular, si se crea el wallet pero falla la consulta de saldo, falta definir recuperación, idempotencia y conciliación.
- Los límites se devuelven como política; no se añaden endpoints de pagos o recargas porque no están descritos en el alcance del API de onboarding.

<<<FIN>>>