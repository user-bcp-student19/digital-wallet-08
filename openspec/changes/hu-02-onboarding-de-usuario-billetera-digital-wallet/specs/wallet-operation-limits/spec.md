## ADDED Requirements

### Requirement: Operaciones permitidas en ACTIVE_BASIC
La cuenta en estado `ACTIVE_BASIC` SHALL poder recibir recargas propias y realizar pagos, y MUST rechazar las recargas de terceros.

#### Scenario: Recarga propia en ACTIVE_BASIC
- **WHEN** una cuenta `ACTIVE_BASIC` solicita una recarga propia dentro de los topes
- **THEN** el sistema acepta la recarga

#### Scenario: Pago en ACTIVE_BASIC
- **WHEN** una cuenta `ACTIVE_BASIC` solicita un pago dentro de los topes
- **THEN** el sistema acepta el pago

#### Scenario: Recarga de terceros en ACTIVE_BASIC
- **WHEN** una cuenta `ACTIVE_BASIC` recibe una recarga de un tercero
- **THEN** el sistema rechaza la operación

### Requirement: Tope por operación en ACTIVE_BASIC
El sistema MUST rechazar toda operación de pago o recarga de una cuenta `ACTIVE_BASIC` cuyo monto supere el tope por operación, de S/20 por defecto.

#### Scenario: Operación en el límite exacto
- **WHEN** una cuenta `ACTIVE_BASIC` solicita una operación de S/20
- **THEN** el sistema acepta la operación, siempre que no supere el tope diario

#### Scenario: Operación que supera el tope por operación
- **WHEN** una cuenta `ACTIVE_BASIC` solicita una operación de S/20.01
- **THEN** el sistema rechaza la operación por exceder el tope por operación

### Requirement: Tope diario combinado en ACTIVE_BASIC
El sistema SHALL aplicar a una cuenta `ACTIVE_BASIC` un tope diario combinado de S/60 por defecto para la suma de pagos y recargas.

#### Scenario: Suma combinada que alcanza el tope
- **WHEN** una cuenta `ACTIVE_BASIC` acumula S/40 en pagos y recargas en el día y solicita una operación de S/20
- **THEN** el sistema acepta la operación y el acumulado diario queda en S/60

#### Scenario: Suma combinada que excede el tope
- **WHEN** una cuenta `ACTIVE_BASIC` acumula S/60 en pagos y recargas en el día y solicita una operación adicional
- **THEN** el sistema rechaza la operación por exceder el tope diario combinado

#### Scenario: Pagos y recargas comparten el mismo acumulado
- **WHEN** una cuenta `ACTIVE_BASIC` realiza recargas por S/40 y luego solicita un pago de S/20 y después otro pago de S/1 en el mismo día
- **THEN** el pago de S/20 se acepta
- **AND** el pago de S/1 se rechaza

### Requirement: Topes parametrizables
Los topes por operación y diarios MUST ser parametrizables y no estar fijados en el código, incluidos los del estado `ACTIVE_BASIC`.

#### Scenario: Cambio de parámetro de tope
- **WHEN** se modifica el parámetro del tope por operación de `ACTIVE_BASIC` a otro valor
- **THEN** el sistema aplica el nuevo valor a las operaciones posteriores sin cambios de código

### Requirement: Operaciones permitidas y topes en ACTIVE_FULL
La cuenta en estado `ACTIVE_FULL` SHALL poder recibir recargas propias y de terceros hasta un máximo de S/1,000 diarios, y SHALL poder realizar pagos de hasta S/500 por operación y S/1,000 diarios. No existe tope por operación para recargas.

#### Scenario: Recarga de tercero en ACTIVE_FULL
- **WHEN** una cuenta `ACTIVE_FULL` recibe una recarga de un tercero dentro del tope diario
- **THEN** el sistema acepta la recarga

#### Scenario: Recarga grande sin tope por operación
- **WHEN** una cuenta `ACTIVE_FULL` sin recargas previas en el día recibe una recarga de S/1,000
- **THEN** el sistema acepta la recarga

#### Scenario: Recarga que excede el tope diario
- **WHEN** una cuenta `ACTIVE_FULL` acumula S/1,000 en recargas en el día y recibe una recarga adicional
- **THEN** el sistema rechaza la recarga por exceder el tope diario

#### Scenario: Pago en el límite por operación
- **WHEN** una cuenta `ACTIVE_FULL` solicita un pago de S/500
- **THEN** el sistema acepta el pago, siempre que no supere el tope diario

#### Scenario: Pago que excede el tope por operación
- **WHEN** una cuenta `ACTIVE_FULL` solicita un pago de S/500.01
- **THEN** el sistema rechaza el pago por exceder el tope por operación

#### Scenario: Pago que excede el tope diario
- **WHEN** una cuenta `ACTIVE_FULL` acumula S/1,000 en pagos en el día y solicita un pago adicional
- **THEN** el sistema rechaza el pago por exceder el tope diario

### Requirement: Día de operación en zona horaria de Perú
El sistema MUST calcular el día de los contadores diarios con la zona horaria de Perú y la hora del servidor, y MUST reiniciar los contadores al cambio de día en esa zona horaria.

#### Scenario: Reinicio del contador al cambiar de día
- **WHEN** la hora del servidor, en zona horaria de Perú, cruza la medianoche
- **THEN** el acumulado diario de la cuenta se reinicia a S/0

#### Scenario: Operaciones de días distintos no se acumulan
- **WHEN** una cuenta alcanzó su tope diario el día anterior y solicita una operación válida el día siguiente (hora de Perú)
- **THEN** el sistema acepta la operación
