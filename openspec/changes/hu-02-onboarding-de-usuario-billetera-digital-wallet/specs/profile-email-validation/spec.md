## ADDED Requirements

### Requirement: Estados complementarios del perfil
El sistema SHALL mantener en el perfil tres estados complementarios independientes, con sus valores iniciales: `ESTADO_C1` = `PENDING_EMAIL`, `ESTADO_C2` = `PENDING_MOVIL` y `ESTADO_C3` = `PENDING_BIOM`. El usuario SHALL poder completar las validaciones de correo, celular e identidad en cualquier orden y a su requerimiento.

#### Scenario: Estados iniciales tras el registro
- **WHEN** se crea una cuenta nueva
- **THEN** el perfil tiene `ESTADO_C1` = `PENDING_EMAIL`, `ESTADO_C2` = `PENDING_MOVIL` y `ESTADO_C3` = `PENDING_BIOM`

#### Scenario: Validaciones en cualquier orden
- **WHEN** el usuario completa primero la validación de celular y después la de correo
- **THEN** el sistema acepta ambas validaciones sin exigir un orden
- **AND** cada estado cambia de forma independiente

### Requirement: Formato y unicidad del correo
El sistema SHALL validar el formato del correo electrónico y MUST rechazar un correo que ya esté registrado por otro usuario.

#### Scenario: Correo con formato válido y no registrado
- **WHEN** el usuario ingresa "ana@example.com" y ningún otro usuario lo tiene registrado
- **THEN** el sistema acepta el correo y permite solicitar el OTP

#### Scenario: Correo con formato inválido
- **WHEN** el usuario ingresa "ana@@example"
- **THEN** el sistema rechaza el correo por formato inválido

#### Scenario: Correo ya registrado por otro usuario
- **WHEN** el usuario ingresa un correo que pertenece a otro usuario
- **THEN** el sistema rechaza el correo por estar ya registrado

### Requirement: OTP de correo con servicio mock
El sistema SHALL validar el correo mediante un OTP de 6 caracteres con una vigencia de 60 segundos, generado por un servicio mock. El envío real del correo queda fuera de alcance: el sistema genera el OTP y continúa. El mock SHALL confirmar cualquier valor ingresado mientras exista un OTP vigente para ese correo.

#### Scenario: Generación del OTP sin envío real
- **WHEN** el usuario solicita el OTP para un correo válido
- **THEN** el sistema genera un OTP de 6 caracteres con vigencia de 60 segundos mediante el servicio mock
- **AND** no se envía ningún correo real
- **AND** el flujo continúa a la confirmación del OTP

#### Scenario: Confirmación del OTP vigente
- **WHEN** el usuario ingresa cualquier valor de OTP dentro de los 60 segundos de vigencia
- **THEN** el sistema confirma el OTP
- **AND** `ESTADO_C1` cambia de `PENDING_EMAIL` a `ACTIVE_EMAIL`

#### Scenario: OTP vencido
- **WHEN** el usuario ingresa un valor de OTP después de 60 segundos desde su generación
- **THEN** el sistema rechaza la confirmación
- **AND** `ESTADO_C1` permanece en `PENDING_EMAIL`

### Requirement: Frecuencia e invalidación de OTP de correo
El sistema SHALL permitir solicitar un OTP de correo cada 45 segundos, y la generación de un OTP nuevo MUST invalidar los anteriores.

#### Scenario: Solicitud antes de 45 segundos
- **WHEN** el usuario solicita un nuevo OTP de correo antes de que transcurran 45 segundos desde la solicitud anterior
- **THEN** el sistema rechaza la solicitud y no genera un OTP nuevo

#### Scenario: Solicitud después de 45 segundos
- **WHEN** el usuario solicita un nuevo OTP de correo cuando han transcurrido 45 segundos o más desde la solicitud anterior
- **THEN** el sistema genera un OTP nuevo

#### Scenario: OTP nuevo invalida los anteriores
- **WHEN** se genera un OTP nuevo para el mismo correo
- **THEN** los OTP generados antes quedan invalidados
- **AND** una confirmación contra un OTP invalidado no cambia `ESTADO_C1`
