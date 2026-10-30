## ADDED Requirements

### Requirement: Aceptación de términos y condiciones para datos personales
El sistema SHALL exigir que el usuario acepte los términos y condiciones sobre el manejo de sus datos personales para la verificación biométrica antes de continuar con la validación de identidad, y SHALL registrar dicha aceptación.

#### Scenario: Aceptación antes de la validación de identidad
- **WHEN** el usuario acepta los términos y condiciones en la pantalla de identidad
- **THEN** el sistema registra la aceptación y permite continuar con la validación de identidad

#### Scenario: Sin aceptación
- **WHEN** el usuario intenta continuar con la validación de identidad sin aceptar los términos y condiciones
- **THEN** el sistema no permite continuar

### Requirement: Exclusión de datos personales de analítica y logs
El sistema MUST NOT enviar datos personales del cliente a herramientas de analítica ni registrarlos en logs. La contraseña MUST NOT enviarse a analítica ni registrarse en logs.

#### Scenario: Contraseña excluida de analítica y logs
- **WHEN** el usuario ingresa o envía su contraseña durante el registro
- **THEN** la contraseña no aparece en ningún evento de analítica ni en ningún log

#### Scenario: Datos personales excluidos de analítica y logs
- **WHEN** el usuario completa registro, correo, celular o identidad
- **THEN** los eventos de analítica y los logs no contienen nombres, apellidos, correo, celular ni datos de identidad
- **AND** los eventos de medición de tiempo y pasos no incluyen datos personales

### Requirement: Controles de acceso, protección, retención y eliminación
El sistema SHALL contar con controles de acceso y protección sobre los datos personales almacenados. Los periodos de retención, los procesos de eliminación y el texto y versión de los términos y condiciones quedan fuera del alcance de esta entrega.

#### Scenario: Acceso restringido a datos personales
- **WHEN** un actor sin autorización intenta acceder a los datos personales de un usuario
- **THEN** el sistema deniega el acceso

#### Scenario: Retención y eliminación no definidas en esta entrega
- **WHEN** se revisa el alcance de esta entrega
- **THEN** no se exige implementar periodos de retención ni procesos de eliminación de datos personales
