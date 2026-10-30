## ADDED Requirements

### Requirement: Formato, prefijo y unicidad del celular
El sistema SHALL aceptar solo números de celular peruanos de 9 dígitos que empiecen con 9, SHALL aplicar el prefijo predeterminado +51 sin permitir editarlo, y MUST rechazar un número que ya esté registrado por otro usuario.

#### Scenario: Celular válido y no registrado
- **WHEN** el usuario ingresa "912345678" y ningún otro usuario lo tiene registrado
- **THEN** el sistema acepta el número con el prefijo +51 y permite solicitar el OTP

#### Scenario: Celular con formato inválido
- **WHEN** el usuario ingresa un número que no tiene 9 dígitos o no empieza con 9
- **THEN** el sistema rechaza el número por formato inválido

#### Scenario: Prefijo no editable
- **WHEN** el usuario intenta modificar el prefijo +51 en la pantalla de perfil
- **THEN** el sistema mantiene el prefijo +51 sin cambios

#### Scenario: Celular ya registrado por otro usuario
- **WHEN** el usuario ingresa un número que pertenece a otro usuario
- **THEN** el sistema rechaza el número por estar ya registrado

### Requirement: OTP de celular con servicio mock
El sistema SHALL validar el celular mediante un OTP de 6 caracteres con una vigencia de 60 segundos, generado por un servicio mock. El envío real de SMS queda fuera de alcance: el sistema genera el OTP y continúa. El mock SHALL confirmar cualquier valor ingresado mientras exista un OTP vigente para ese número.

#### Scenario: Generación del OTP sin envío real de SMS
- **WHEN** el usuario solicita el OTP para un celular válido
- **THEN** el sistema genera un OTP de 6 caracteres con vigencia de 60 segundos mediante el servicio mock
- **AND** no se envía ningún SMS real
- **AND** el flujo continúa a la confirmación del OTP

#### Scenario: Confirmación del OTP vigente
- **WHEN** el usuario ingresa cualquier valor de OTP dentro de los 60 segundos de vigencia
- **THEN** el sistema confirma el OTP
- **AND** `ESTADO_C2` cambia de `PENDING_MOVIL` a su estado validado (`ACTIVE_MOVIL`)

#### Scenario: OTP vencido
- **WHEN** el usuario ingresa un valor de OTP después de 60 segundos desde su generación
- **THEN** el sistema rechaza la confirmación
- **AND** `ESTADO_C2` permanece en `PENDING_MOVIL`

### Requirement: Frecuencia e invalidación de OTP de celular
El sistema SHALL permitir solicitar un OTP de celular cada 45 segundos, y la generación de un OTP nuevo MUST invalidar los anteriores.

#### Scenario: Solicitud antes de 45 segundos
- **WHEN** el usuario solicita un nuevo OTP de celular antes de que transcurran 45 segundos desde la solicitud anterior
- **THEN** el sistema rechaza la solicitud y no genera un OTP nuevo

#### Scenario: Solicitud después de 45 segundos
- **WHEN** el usuario solicita un nuevo OTP de celular cuando han transcurrido 45 segundos o más desde la solicitud anterior
- **THEN** el sistema genera un OTP nuevo

#### Scenario: OTP nuevo invalida los anteriores
- **WHEN** se genera un OTP nuevo para el mismo celular
- **THEN** los OTP generados antes quedan invalidados
- **AND** una confirmación contra un OTP invalidado no cambia `ESTADO_C2`
