## ADDED Requirements

### Requirement: Medición de tiempo y pasos del registro
El sistema SHALL iniciar la medición del tiempo de registro cuando la pantalla de onboarding es visible, SHALL registrar el tiempo y los pasos completados, y SHALL finalizar la medición cuando concluye la respuesta del registro.

#### Scenario: Inicio de la medición al mostrar la pantalla
- **WHEN** la pantalla de onboarding pasa a ser visible para el usuario
- **THEN** el sistema inicia la medición del tiempo de registro

#### Scenario: Registro de pasos completados
- **WHEN** el usuario completa un paso del onboarding
- **THEN** el sistema registra el paso completado junto con el tiempo transcurrido

#### Scenario: Fin de la medición al terminar la respuesta del registro
- **WHEN** el registro finaliza y concluye la respuesta del registro
- **THEN** el sistema finaliza la medición y registra el tiempo total de registro

### Requirement: Validación en línea de los campos
El sistema MUST mostrar el resultado de la validación de cada campo mientras el usuario ingresa su valor.

#### Scenario: Resultado de validación visible durante la escritura
- **WHEN** el usuario escribe un valor en cualquier campo de la pantalla de registro
- **THEN** el campo muestra el resultado de su validación (válido o inválido) sin esperar al envío del formulario

### Requirement: Validación de nombres
El sistema SHALL aceptar en el campo Nombres solo caracteres alfabéticos, con espacios permitidos entre letras y una longitud máxima de 30 caracteres.

#### Scenario: Nombres válidos con espacio entre letras
- **WHEN** el usuario ingresa "María José" en Nombres
- **THEN** el campo se marca como válido

#### Scenario: Nombres con caracteres no alfabéticos
- **WHEN** el usuario ingresa "Maria123" en Nombres
- **THEN** el campo se marca como inválido

#### Scenario: Nombres que exceden la longitud máxima
- **WHEN** el usuario ingresa un valor alfabético de 31 caracteres en Nombres
- **THEN** el campo se marca como inválido

### Requirement: Validación de apellido paterno y materno
El sistema SHALL aceptar en Apellido paterno y en Apellido materno solo caracteres alfabéticos con una longitud máxima de 20 caracteres.

#### Scenario: Apellido válido
- **WHEN** el usuario ingresa "Quispe" en Apellido paterno
- **THEN** el campo se marca como válido

#### Scenario: Apellido con caracteres no alfabéticos
- **WHEN** el usuario ingresa "Quispe9" en Apellido materno
- **THEN** el campo se marca como inválido

#### Scenario: Apellido que excede la longitud máxima
- **WHEN** el usuario ingresa un valor alfabético de 21 caracteres en Apellido paterno
- **THEN** el campo se marca como inválido

### Requirement: Validación y disponibilidad del usuario
El sistema SHALL aceptar en Usuario caracteres alfabéticos, que pueden incluir símbolos, con una longitud máxima de 20 caracteres, y MUST validar que el usuario esté disponible.

#### Scenario: Usuario válido y disponible
- **WHEN** el usuario ingresa un nombre de usuario válido que no está registrado por otra cuenta
- **THEN** el campo se marca como válido y disponible

#### Scenario: Usuario que excede la longitud máxima
- **WHEN** el usuario ingresa un nombre de usuario de 21 caracteres
- **THEN** el campo se marca como inválido

#### Scenario: Usuario no disponible
- **WHEN** el usuario ingresa un nombre de usuario que ya está registrado
- **THEN** el campo indica que el usuario no está disponible

### Requirement: Sugerencias de usuario disponibles
Cuando el usuario ingresado no está disponible, el sistema SHALL mostrar sugerencias de usuario disponibles basadas en nombres, apellidos y números, sin símbolos.

#### Scenario: Sugerencias ante un usuario no disponible
- **WHEN** el usuario ingresa un nombre de usuario no disponible
- **THEN** el sistema muestra una o más sugerencias construidas con nombres, apellidos y números
- **AND** ninguna sugerencia contiene símbolos
- **AND** todas las sugerencias están disponibles

### Requirement: Robustez de la contraseña
El sistema SHALL exigir una contraseña de mínimo 10 caracteres alfanuméricos, SHALL permitir símbolos, MUST validar su robustez y MUST alertar al usuario sobre su nivel de robustez.

#### Scenario: Contraseña robusta
- **WHEN** el usuario ingresa una contraseña de 10 o más caracteres alfanuméricos, con o sin símbolos
- **THEN** el campo se marca como válido

#### Scenario: Contraseña demasiado corta
- **WHEN** el usuario ingresa una contraseña de menos de 10 caracteres
- **THEN** el campo se marca como inválido y se alerta al usuario sobre su robustez insuficiente

### Requirement: Creación de cuenta básica
Al finalizar el registro, el sistema SHALL crear una cuenta digital con saldo inicial de S/0, estado `ACTIVE_BASIC` y un `wallet_id` válido.

#### Scenario: Registro exitoso crea la cuenta
- **WHEN** el usuario completa el registro con todos los datos válidos
- **THEN** el sistema crea una cuenta con saldo S/0 y estado `ACTIVE_BASIC`
- **AND** la cuenta tiene un `wallet_id` válido

### Requirement: Landing de bienvenida
Tras el registro exitoso, el sistema SHALL presentar la landing, SHALL dar la bienvenida al usuario por su nombre real y SHALL mostrar las condiciones de las operaciones permitidas.

#### Scenario: Landing posterior al registro
- **WHEN** el registro finaliza con éxito
- **THEN** el sistema presenta la landing con un saludo que contiene el nombre real del usuario
- **AND** la landing muestra las condiciones de las operaciones permitidas

### Requirement: Aviso de perfil pendiente
La landing MUST incluir un mensaje visible que invite al usuario a completar los datos de su perfil.

#### Scenario: Mensaje de perfil pendiente visible
- **WHEN** se presenta la landing a un usuario recién registrado
- **THEN** la landing muestra un mensaje visible para completar los datos del perfil
