## ADDED Requirements

### Requirement: Alcance de la biometría en esta entrega
El sistema MUST NOT integrar ni ejecutar validación biométrica real en esta entrega. El sistema SHALL ofrecer un flujo visual de validación de identidad con los cambios de estado correspondientes.

#### Scenario: Sin verificación biométrica real
- **WHEN** el usuario recorre el flujo de validación de identidad
- **THEN** el sistema no invoca ningún proveedor de biometría real
- **AND** no realiza verificaciones biométricas reales

### Requirement: Disponibilidad del flujo mock solo en desarrollo y pruebas
El sistema SHALL habilitar el flujo mock de biometría únicamente en los ambientes de desarrollo y pruebas.

#### Scenario: Flujo mock en ambiente de desarrollo o pruebas
- **WHEN** el usuario inicia la validación de identidad en un ambiente de desarrollo o pruebas
- **THEN** el sistema ofrece el flujo mock de biometría

#### Scenario: Flujo mock en otros ambientes
- **WHEN** el usuario intenta iniciar el flujo mock en un ambiente distinto de desarrollo y pruebas
- **THEN** el sistema no habilita el flujo mock ni permite alcanzar `ACTIVE_FULL` por esa vía

### Requirement: Comportamiento del flujo mock
El flujo mock SHALL verificar únicamente los inputs recibidos y continuar, sin realizar verificaciones biométricas reales. El flujo mock SHALL usar datos simulados y MUST NOT requerir cargar ni procesar fotografías reales del DNI ni videos biométricos.

#### Scenario: Flujo mock con datos simulados
- **WHEN** el usuario ejecuta el flujo mock con inputs simulados válidos
- **THEN** el sistema verifica los inputs y continúa
- **AND** no solicita ni procesa fotografías del DNI ni videos biométricos reales

### Requirement: Activación completa simulada
Al simular una validación biométrica exitosa en el flujo mock, el sistema SHALL llevar la cuenta al estado `ACTIVE_FULL` y SHALL habilitar las operaciones de nivel `ACTIVE_FULL`. La validación de correo y la de celular son flags distintos y no son prerrequisito de la validación de identidad ni de `ACTIVE_FULL`.

#### Scenario: Validación mock exitosa
- **WHEN** el usuario completa con éxito el flujo mock de biometría
- **THEN** la cuenta pasa del estado `ACTIVE_BASIC` a `ACTIVE_FULL`
- **AND** `ESTADO_C3` deja de ser `PENDING_BIOM`
- **AND** la cuenta queda habilitada para las operaciones y topes de nivel `ACTIVE_FULL`

#### Scenario: Activación sin correo ni celular validados
- **WHEN** el usuario completa con éxito el flujo mock de biometría sin haber validado correo ni celular
- **THEN** la cuenta alcanza `ACTIVE_FULL`
- **AND** `ESTADO_C1` y `ESTADO_C2` conservan sus valores previos

#### Scenario: Recorrido completo
- **WHEN** un usuario se registra, valida correo, valida celular y completa el flujo mock de biometría
- **THEN** la cuenta termina en estado `ACTIVE_FULL` con los tres estados complementarios validados

### Requirement: Requisitos documentados para la biometría real futura
Los requisitos de la validación biométrica real MUST quedar documentados como contrato para una entrega posterior y MUST NOT implementarse en esta entrega: fotografías de ambas caras del DNI de máximo 2 MB cada una, video de 5 a 10 segundos grabado con el celular de máximo 10 MB, y verificación de que los metadatos del video indican una grabación de los últimos 10 minutos. La pantalla de identidad SHALL indicar al usuario que las imágenes deben ser nítidas.

#### Scenario: Indicación de nitidez en la pantalla de identidad
- **WHEN** el usuario accede a la pantalla de validación de identidad
- **THEN** la pantalla indica que las imágenes deben ser nítidas

#### Scenario: Requisitos de documentos no aplicados en el flujo mock
- **WHEN** el usuario completa el flujo mock
- **THEN** el sistema no valida tamaños de archivo, duración de video ni metadatos de grabación, porque esa validación real queda fuera de esta entrega
