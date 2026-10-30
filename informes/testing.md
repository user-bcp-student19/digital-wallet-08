# Entrega de pruebas – HU 01 Onboarding Wallet (alcance: CA-01)

Este documento contiene los archivos solicitados, completos. No se ejecutó ninguna prueba, servicio ni comando. Todo estado es **NO EJECUTADO**.

## Estructura propuesta

El proyecto no trae infraestructura de QA. Los archivos nuevos se agregan en `wallet-api/qa/`, sin modificar `app/`.

```
wallet-api/
└── qa/
    ├── testing_report.md
    ├── karate/
    │   ├── pom.xml
    │   └── src/test/
    │       ├── java/onboarding/OnboardingRunner.java
    │       └── resources/
    │           ├── karate-config.js
    │           └── karate/
    │               ├── common/start-session.feature
    │               ├── data/account-valid.json
    │               └── onboarding/
    │                   ├── session-lifecycle.feature
    │                   ├── username-validation.feature
    │                   ├── account-field-validation.feature
    │                   └── onboarding-account-integration.feature
    └── selenium/
        ├── requirements-qa.txt
        ├── locators.example.json
        ├── pytest.ini
        ├── support.py
        ├── conftest.py
        └── test_onboarding_ca01_ui.py
```

---

# 1. `qa/testing_report.md`

````markdown
# Testing Report – HU 01 Onboarding de usuario, billetera digital (Wallet)

Fecha del informe: 2026-10-30
Alcance de esta entrega: **CA-01 (Inicio y seguimiento)**
Estado global: **NO EJECUTADO**. No existe salida real de ejecución de ninguna prueba.

## 1. Fuentes y alcance

| Fuente | Estado |
|---|---|
| Historia de usuario (CA-01 a CA-13 en la descripción) | Recibida |
| Lista "Criterios de aceptación" de la tarea | Solo contiene CA-01 |
| Contrato e implementación del backend (FastAPI) | Recibido como código y README. **No** se recibió el OpenAPI generado |
| Especificación del frontend (pantallas, rutas, selectores, eventos) | **NO RECIBIDA** |
| Contrato externo `bcp-wallet-mock` (grupo 8) | Recibido truncado (lo indica el propio backend) |
| Ejecución del backend o de pruebas | **No hay evidencia** (el backend declara "No ejecuté el código ni las pruebas") |

**Decisión de alcance.** Se diseñan pruebas completas para CA-01. CA-02 a CA-13 aparecen en la descripción de la HU, pero no en la lista de criterios a verificar. Solo se tocan de forma auxiliar, y se indica en la matriz:

- La validación por campo del backend (CA-02), porque CA-01 exige mostrar el resultado de la validación mientras se escribe.
- La creación de cuenta (CA-03), porque el paso `ACCOUNT_CREATED` y el cierre `LANDING_VISIBLE` pertenecen al seguimiento de CA-01.

Los demás criterios quedan **sin diseñar en esta entrega** (sección 8).

## 2. Descomposición de CA-01

| Id | Sub-criterio |
|---|---|
| CA-01-A | La medición del tiempo de registro inicia cuando la pantalla de onboarding es visible |
| CA-01-B | El sistema registra el tiempo (inicio, fin, duración) |
| CA-01-C | El sistema registra los pasos completados |
| CA-01-D | Los campos muestran el resultado de su validación mientras el usuario ingresa cada valor |

## 3. Contrato de backend bajo prueba

Se extrajo del código recibido. Todas las rutas van bajo `/v1`.

| Método y ruta | Autenticación | Respuestas esperadas (según código) |
|---|---|---|
| `POST /v1/onboarding/sessions` | Ninguna (sin `require_bearer`) | 201 `OnboardingSession` |
| `POST /v1/onboarding/sessions/{sessionId}/steps` | Ninguna | 200 `OnboardingSession`; 400 `INVALID_FIELD`; 404 `NOT_FOUND`; 409 `SESSION_CLOSED` |
| `GET /v1/usernames/availability` | Ninguna | 200 `UsernameAvailability`; 400 `INVALID_FIELD` |
| `POST /v1/accounts` (auxiliar) | Ninguna | 201; 400; 409 `USERNAME_TAKEN`; 502/504 (servicio externo) |

Esquemas y reglas:

- `OnboardingSession`: `sessionId` (UUID), `startedAt`, `completedSteps[]`, `completed`, `endedAt` (null mientras esté abierta), `durationMs` (null mientras esté abierta).
- Pasos permitidos: `PERSONAL_DATA_COMPLETED`, `CREDENTIALS_COMPLETED`, `ACCOUNT_CREATED`, `LANDING_VISIBLE`.
- `LANDING_VISIBLE` cierra la sesión y calcula `durationMs`. Un paso posterior responde 409.
- Los pasos repetidos no se duplican.
- Un `sessionId` malformado en la ruta responde 404 `NOT_FOUND`, no 400 (README, punto 5).
- El tiempo lo calcula el servidor con su reloj, no el cliente.
- Errores: `{code, message, fields?, traceId}`. Cabecera `X-Trace-Id` en todas las respuestas.
- `username`: 1 a 20 caracteres ASCII imprimibles sin espacio, con al menos una letra.
- `firstNames`: máximo 30 caracteres alfabéticos, con espacios entre palabras.
- `paternalSurname` y `maternalSurname`: máximo 20 caracteres alfabéticos.
- `password`: 8 a 64 caracteres.

## 4. Brechas de información y riesgos (pendientes)

| Id | Brecha | Qué se necesita |
|---|---|---|
| G-01 | **No hay especificación de frontend.** Se desconocen la URL de la pantalla, los selectores, cómo se representa el resultado de validación y qué acción dispara cada paso. | URL de onboarding, identificadores estables (por ejemplo `data-testid`) y descripción de estados de validación. Con eso se completa `locators.json` |
| G-02 | No existe `GET` de sesión. El estado solo se lee mutando (registrar paso). | Confirmar si se agregará un endpoint de lectura. Hasta entonces, las comprobaciones usan la respuesta del `POST` |
| G-03 | Se desconoce qué acción de UI dispara cada paso y si `CREDENTIALS_COMPLETED` y `PERSONAL_DATA_COMPLETED` son pantallas distintas | Flujo de pantallas del frontend |
| G-04 | "Inicia cuando la pantalla es visible" es del cliente. El servidor mide desde que recibe el `POST`, y la latencia entre visibilidad y llamada no está especificada | Definir la tolerancia aceptable y quién emite el evento |
| G-05 | No hay endpoint de robustez de contraseña. El único control del backend es la longitud 8–64 | Regla de robustez y dónde se evalúa (probablemente solo frontend) |
| G-06 | Códigos de error `SESSION_CLOSED` y `NOT_FOUND` figuran como "no listados en el contrato" (README, punto 4) | Confirmar su inclusión en el OpenAPI |
| G-07 | `LANDING_VISIBLE` puede registrarse sin pasos previos y cierra la sesión (lectura estática del código) | Confirmar si debe exigirse orden de pasos. **No hay prueba** de este comportamiento hasta definirlo |
| G-08 | El contrato externo está truncado. Las pruebas que crean cuentas dependen de campos supuestos del KYC | Contrato completo de `bcp-wallet-mock` |
| G-09 | Los wallets creados en el servicio externo no tienen endpoint de baja (README, punto 7) | No se pueden limpiar. Ver sección 7 |
| G-10 | Las dependencias de QA (Karate, Selenium, Maven, Java) no existen en el proyecto | Confirmar herramientas y versiones. Las propuestas están en `pom.xml` y `requirements-qa.txt` |
| G-11 | Aviso de verificación de ejecución: no se sabe si el backend arranca. `Annotated[Username, Query()]` combina `Field(json_schema_extra)` y `Query` y no se validó | Ejecutar el humo (sección 6, paso 3) antes del resto |

### Observaciones de revisión estática (no son resultados de ejecución)

1. En `tests/test_onboarding_flow.py` se afirma `assert "short" not in bad.text`. Pydantic v2 suele nombrar la regla de longitud mínima `string_too_short`. El handler devuelve ese valor en `fields[].rule`, así que la aserción podría fallar por una coincidencia de texto, no por un eco de la contraseña. **Por verificar al ejecutar `pytest`.** Las pruebas Karate de este informe usan valores centinela que no coinciden con nombres de reglas.
2. La versión de `main.py` entregada tenía líneas confusas y el backend las corrigió con un bloque aparte. Verificar que el archivo final tenga solo `get_app()`.

## 5. Matriz de trazabilidad

Estado de todas las filas: **NO EJECUTADO**. Columna "Observado": ninguno.

### 5.1 Pruebas de API (Karate)

| Id prueba | Sub-criterio | Tipo | Archivo / escenario | Resultado esperado | Observado | Estado |
|---|---|---|---|---|---|---|
| TC-API-01 | CA-01-A | Positivo, contrato | session-lifecycle: iniciar sesión | 201. Cuerpo exacto: `sessionId` UUID, `startedAt` ISO UTC, `completedSteps` vacío, `completed` false, `endedAt` null, `durationMs` null. Cabecera `X-Trace-Id` presente | — | NO EJECUTADO |
| TC-API-02 | CA-01-A | Borde | session-lifecycle: dos sesiones | Dos `sessionId` distintos | — | NO EJECUTADO |
| TC-API-03 | CA-01-A | Contrato (autenticación) | session-lifecycle: sin `Authorization` | 201 sin cabecera de autenticación (según código) | — | NO EJECUTADO |
| TC-API-04 | CA-01-B | Negativo (integridad) | session-lifecycle: cliente intenta fijar `startedAt` y `completed` | 201. `startedAt` lo fija el servidor, `completed` false, `completedSteps` vacío | — | NO EJECUTADO |
| TC-API-05 | CA-01-A | Negativo (método) | session-lifecycle: `GET` sobre `/onboarding/sessions` | 405 `METHOD_NOT_ALLOWED` con esquema `Error` | — | NO EJECUTADO |
| TC-API-06 | CA-01-C | Positivo | session-lifecycle: primer paso | 200. `completedSteps == [PERSONAL_DATA_COMPLETED]`, `completed` false | — | NO EJECUTADO |
| TC-API-07 | CA-01-C | Positivo, borde | session-lifecycle: acumulación e idempotencia | Pasos en orden de registro, sin duplicar el repetido | — | NO EJECUTADO |
| TC-API-08 | CA-01-C | Borde | session-lifecycle: aislamiento entre sesiones | Pasos de A no aparecen en B | — | NO EJECUTADO |
| TC-API-09 | CA-01-B | Positivo | session-lifecycle: cierre con `LANDING_VISIBLE` tras espera de 1,5 s | 200. `completed` true, `endedAt` ISO ≥ `startedAt`, 1500 ≤ `durationMs` < 60000, `durationMs` coherente con `endedAt − startedAt` (±5 ms) | — | NO EJECUTADO |
| TC-API-10 | CA-01-B/C | Negativo | session-lifecycle: paso en sesión cerrada | 409 `SESSION_CLOSED` (repetir `LANDING_VISIBLE` y paso distinto) | — | NO EJECUTADO |
| TC-API-11 | CA-01-C | Negativo | session-lifecycle: paso inválido (3 valores) | 400 `INVALID_FIELD`, `fields` con campo `step`. El valor enviado no se refleja | — | NO EJECUTADO |
| TC-API-12 | CA-01-C | Negativo | session-lifecycle: cuerpo inválido (`{}`, `null`, número) | 400 `INVALID_FIELD`, campo `step` | — | NO EJECUTADO |
| TC-API-13 | CA-01-C | Negativo | session-lifecycle: sesión inexistente | 404 `NOT_FOUND`. `traceId` del cuerpo igual a `X-Trace-Id` | — | NO EJECUTADO |
| TC-API-14 | CA-01-C | Negativo | session-lifecycle: `sessionId` malformado | 404 `NOT_FOUND` (README, punto 5) | — | NO EJECUTADO |
| TC-API-20 | CA-01-D (CA-02) | Positivo | username-validation: usuario libre | 200 exacto `{username, available:true}` sin `suggestions` | — | NO EJECUTADO |
| TC-API-21 | CA-01-D (CA-02) | Borde | username-validation: 20 caracteres | 200, `available` true | — | NO EJECUTADO |
| TC-API-22 | CA-01-D (CA-02) | Positivo | username-validation: símbolos `. _ - !` | 200, `available` true | — | NO EJECUTADO |
| TC-API-23 | CA-01-D (CA-02) | Negativo | username-validation: sin letras, 21 caracteres, con espacio | 400 `INVALID_FIELD`, campo `username` | — | NO EJECUTADO |
| TC-API-24 | CA-01-D | Negativo | username-validation: falta `username` | 400 `INVALID_FIELD`, campo `username` | — | NO EJECUTADO |
| TC-API-25 | CA-01-D | Borde | username-validation: `username` vacío | 400 `INVALID_FIELD` (el cliente podría omitir el parámetro vacío; igual debe dar 400) | — | NO EJECUTADO |
| TC-API-26 | CA-01-D (CA-02) | Negativo | username-validation: nombres opcionales inválidos | 400, el campo correspondiente figura en `fields` | — | NO EJECUTADO |
| TC-API-27 | CA-01-D (CA-02) | Borde | username-validation: 30 y 20 caracteres válidos | 200 | — | NO EJECUTADO |
| TC-API-28 | CA-01-D (CA-02) | Integración externa | username-validation: usuario ocupado (@requires-external) | Tras crear cuenta: `available` false, 1 a 3 `suggestions` alfanuméricas ≤20, ninguna igual al usuario. Un segundo alta da 409 `USERNAME_TAKEN` con sugerencias | — | NO EJECUTADO |
| TC-API-30 | CA-01-D (CA-02) | Negativo | account-field-validation: campo inválido (5 casos) | 400 `INVALID_FIELD`, el campo figura en `fields`, el valor centinela no se refleja | — | NO EJECUTADO |
| TC-API-31 | CA-01-D | Negativo | account-field-validation: cuerpo vacío | 400, `fields` incluye los 5 campos obligatorios | — | NO EJECUTADO |
| TC-API-40 | CA-01-B/C (CA-03) | Integración (@requires-external) | onboarding-account-integration | `completedSteps == [PERSONAL_DATA_COMPLETED, ACCOUNT_CREATED, LANDING_VISIBLE]`, `completed` true, `durationMs` ≥ 0. La respuesta de cuenta no contiene contraseña | — | NO EJECUTADO |
| TC-API-41 | CA-01-C | Borde (@requires-external) | onboarding-account-integration: `onboardingSessionId` inexistente | Cuenta creada (201). El seguimiento es de mejor esfuerzo y no rompe el alta | — | NO EJECUTADO |

### 5.2 Pruebas de interfaz e integración UI+API (Selenium)

Todas exigen `locators.json` completo (G-01).

| Id prueba | Sub-criterio | Tipo | Archivo / función | Resultado esperado | Observado | Estado |
|---|---|---|---|---|---|---|
| TC-UI-01 | CA-01-A | Positivo | test_onboarding_ca01_ui: `test_ui_01_*` | Con la pantalla visible, el navegador emite exactamente un `POST …/onboarding/sessions` | — | NO EJECUTADO |
| TC-UI-02 | CA-01-C | Positivo | `test_ui_02_*` | Con datos válidos y continuar, se emite `POST …/sessions/{id}/steps` con `step` del enum. Los pasos usan un mismo `sessionId` | — | NO EJECUTADO |
| TC-UI-03 | CA-01-D | Positivo/negativo (5 campos) | `test_ui_03_*` | Al escribir un valor inválido, el campo muestra resultado de validación **sin salir del campo**. Con un valor válido, el resultado cambia | — | NO EJECUTADO |
| TC-UI-04 | CA-01-D | Positivo | `test_ui_04_*` | Al escribir el usuario, se emite `GET …/usernames/availability?username=…` sin otra acción del usuario | — | NO EJECUTADO |
| TC-INT-01 | CA-01-A/B/C | Integración UI+API | `test_int_01_*` | Con el `sessionId` generado por la UI, `POST LANDING_VISIBLE` por API da 200, `completed` true, `durationMs` ≥ 0 y `completedSteps` con los pasos enviados por la UI | — | NO EJECUTADO |

### 5.3 Verificación manual

| Id | Sub-criterio | Verificación | Resultado esperado | Observado | Estado |
|---|---|---|---|---|---|
| TC-SEC-01 | CA-01-D (relacionado con CA-02) | Tras ejecutar las pruebas, buscar en el log del servidor las contraseñas sintéticas | 0 coincidencias de `S3cret!pass` y de los centinelas | — | NO EJECUTADO |

## 6. Comandos (preparación y ejecución)

Ver sección 7 (comandos) y sección 8 (datos) de este informe.

## 7. Comandos exactos

### 7.1 Requisitos previos

- Python 3.11 o superior (según el backend).
- JDK 17 o superior y Maven 3.9 o superior (nuevos en el proyecto, para Karate).
- Google Chrome. Selenium ≥ 4.6 resuelve el driver con Selenium Manager, lo que requiere acceso a internet.
- Acceso de red a `https://bcp-wallet-mock.yefri.workers.dev` solo para las pruebas `@requires-external`.
- Para los TC-UI/TC-INT: `locators.json` completo (G-01).

### 7.2 Preparar y arrancar el backend (terminal 1)

```bash
cd wallet-api
python -m venv .venv
source .venv/bin/activate            # Windows: .venv\Scripts\activate
pip install -r requirements.txt
WALLET_ENV=test WALLET_DB_PATH=./qa-test.db WALLET_OTP_FIXED_CODE=123456 \
  uvicorn app.main:get_app --factory --port 8080 2>&1 | tee qa-server.log
```

### 7.3 Humo (terminal 2). Resuelve la brecha G-11

```bash
curl -s -i -X POST http://localhost:8080/v1/onboarding/sessions
curl -s -i "http://localhost:8080/v1/usernames/availability?username=qa.humo"
```

### 7.4 Karate (API)

```bash
cd wallet-api/qa/karate
# Solo pruebas sin servicio externo:
WALLET_API_BASE_URL=http://localhost:8080 \
  mvn -B test -Dtest=OnboardingRunner -Dkarate.env=test -Dkarate.options="--tags ~@requires-external"
# Todas, incluidas las que crean cuentas en el servicio externo:
WALLET_API_BASE_URL=http://localhost:8080 \
  mvn -B test -Dtest=OnboardingRunner -Dkarate.env=test
```

El reporte se genera en `target/karate-reports/karate-summary.html`.

### 7.5 Selenium (UI e integración)

```bash
cd wallet-api/qa/selenium
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-qa.txt
cp locators.example.json locators.json      # completar todos los "PENDIENTE"
API_BASE_URL=http://localhost:8080 HEADLESS=true UI_TIMEOUT_S=10 \
  pytest -v --junitxml=report-ui.xml
```

Si falta `locators.json` o contiene "PENDIENTE", las pruebas se omiten (`SKIPPED`) con motivo explícito. **Omitida no equivale a pasada.**

### 7.6 Verificación de logs (TC-SEC-01)

```bash
cd wallet-api
grep -c "S3cret!pass" qa-server.log     # esperado: 0
grep -c "Zq9!x" qa-server.log           # esperado: 0
```

### 7.7 Limpieza

```bash
# detener el backend (Ctrl+C en la terminal 1) o:
pkill -f "uvicorn app.main:get_app"
cd wallet-api
rm -f qa-test.db qa-server.log
rm -rf qa/karate/target
rm -rf qa/selenium/.pytest_cache qa/selenium/report-ui.xml qa/selenium/locators.json
```

**Limitación:** los wallets creados en `bcp-wallet-mock` por las pruebas `@requires-external` no se pueden eliminar (G-09). Se identifican por los nombres sintéticos de la sección 8.

## 8. Datos de prueba sintéticos

| Dato | Valor | Uso |
|---|---|---|
| Nombres | `Ana María` | Cuentas válidas |
| Apellido paterno / materno | `Quispe` / `Rojas` | Cuentas válidas |
| Contraseña válida | `S3cret!pass` | Alta de cuentas. No es una credencial real |
| Usuario | `qa` + hex de `System.nanoTime()` (≤ 20 caracteres) | Único por ejecución |
| Centinelas inválidos | `Ana123`, `Quispe9`, `Rojas1`, `12345`, `Zq9!x` | TC-API-30. Deben ser rechazados y no reflejarse |
| Textos de 31 / 21 caracteres | `Aaaaaaaaaa…` generados en el escenario | Pruebas de borde |

No se usan datos personales reales, DNI, fotos ni video.

## 9. Criterios y pruebas fuera de esta entrega (pendientes)

- **CA-02 completo** (reglas de cada campo en la UI, sugerencias en pantalla, robustez de contraseña, no envío a analítica).
- **CA-03 a CA-13**: cuenta básica y su saldo, topes, OTP de correo y de celular, biometría mock, consentimiento, activación completa.

Cada uno necesita su propia traza. Para diseñarlas se requiere que se incluyan en la lista de criterios a verificar. Para CA-03 (wallet_id y saldo) además hace falta el contrato completo de `bcp-wallet-mock`.

## 10. Resumen de estado

| Conjunto | Pruebas | Ejecutadas | Estado |
|---|---|---|---|
| Karate sin servicio externo | 20 (TC-API-01 a 14, 20 a 27, 30, 31) | 0 | NO EJECUTADO |
| Karate con servicio externo | 3 (TC-API-28, 40, 41) | 0 | NO EJECUTADO |
| Selenium UI | 4 | 0 | NO EJECUTADO |
| Integración UI+API | 1 | 0 | NO EJECUTADO |
| Manual | 1 | 0 | NO EJECUTADO |

Ninguna corrección se marca como verificada.
````

---

# 2. Karate (API)

### `qa/karate/pom.xml`

Versiones propuestas, no existentes en el proyecto (G-10).

```xml
<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 http://maven.apache.org/xsd/maven-4.0.0.xsd">
  <modelVersion>4.0.0</modelVersion>

  <groupId>pe.wallet.qa</groupId>
  <artifactId>wallet-karate</artifactId>
  <version>0.1.0</version>
  <packaging>jar</packaging>

  <properties>
    <maven.compiler.source>17</maven.compiler.source>
    <maven.compiler.target>17</maven.compiler.target>
    <project.build.sourceEncoding>UTF-8</project.build.sourceEncoding>
    <karate.version>1.4.1</karate.version>
  </properties>

  <dependencies>
    <dependency>
      <groupId>com.intuit.karate</groupId>
      <artifactId>karate-junit5</artifactId>
      <version>${karate.version}</version>
      <scope>test</scope>
    </dependency>
  </dependencies>

  <build>
    <plugins>
      <plugin>
        <groupId>org.apache.maven.plugins</groupId>
        <artifactId>maven-surefire-plugin</artifactId>
        <version>3.2.5</version>
        <configuration>
          <argLine>-Dfile.encoding=UTF-8</argLine>
        </configuration>
      </plugin>
    </plugins>
  </build>
</project>
```

### `qa/karate/src/test/java/onboarding/OnboardingRunner.java`

```java
package onboarding;

import com.intuit.karate.junit5.Karate;

class OnboardingRunner {

    @Karate.Test
    Karate onboarding() {
        return Karate.run("classpath:karate/onboarding");
    }
}
```

### `qa/karate/src/test/resources/karate-config.js`

```javascript
function fn() {
  var env = karate.env || 'local';
  karate.log('karate.env =', env);
  var baseUrl = java.lang.System.getenv('WALLET_API_BASE_URL') || 'http://localhost:8080';
  return {
    baseUrl: baseUrl
  };
}
```

### `qa/karate/src/test/resources/karate/data/account-valid.json`

```json
{
  "firstNames": "Ana María",
  "paternalSurname": "Quispe",
  "maternalSurname": "Rojas",
  "username": "REPLACE_AT_RUNTIME",
  "password": "S3cret!pass"
}
```

### `qa/karate/src/test/resources/karate/common/start-session.feature`

```gherkin
@ignore
Feature: Helper - inicia una sesión de onboarding

  Scenario: iniciar sesión
    Given url baseUrl
    And path 'v1', 'onboarding', 'sessions'
    When method post
    Then status 201
    * def sid = response.sessionId
    * def startedAt = response.startedAt
```

### `qa/karate/src/test/resources/karate/onboarding/session-lifecycle.feature`

```gherkin
@api @ca-01
Feature: CA-01 - Sesión de onboarding (inicio de medición, tiempo y pasos completados)
  Contrato bajo prueba (según código backend, sin ejecutar):
    POST /v1/onboarding/sessions
    POST /v1/onboarding/sessions/{sessionId}/steps

  Background:
    * url baseUrl
    * def isIso = function(s){ return typeof s == 'string' && /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?Z$/.test(s) }
    * def newUuid = function(){ return '' + java.util.UUID.randomUUID() }
    * def Thread = Java.type('java.lang.Thread')
    * def startSession = read('classpath:karate/common/start-session.feature')

  @TC-API-01 @positive @contract
  Scenario: TC-API-01 Inicia sesión de onboarding y devuelve el esquema esperado
    Given path 'v1', 'onboarding', 'sessions'
    When method post
    Then status 201
    And match response ==
      """
      {
        sessionId: '#uuid',
        startedAt: '#? isIso(_)',
        completedSteps: [],
        completed: false,
        endedAt: null,
        durationMs: null
      }
      """
    And match header X-Trace-Id == '#notnull'

  @TC-API-02 @edge
  Scenario: TC-API-02 Dos sesiones consecutivas son independientes
    * def a = call startSession
    * def b = call startSession
    * match a.sid != b.sid
    * match a.startedAt == '#? isIso(_)'
    * match b.startedAt == '#? isIso(_)'

  @TC-API-03 @contract @auth
  Scenario: TC-API-03 Iniciar sesión no exige cabecera Authorization (según código)
    Given path 'v1', 'onboarding', 'sessions'
    And header Accept = 'application/json'
    When method post
    Then status 201
    And match response.completed == false

  @TC-API-04 @negative @integrity
  Scenario: TC-API-04 El cliente no puede fijar startedAt ni el estado de la sesión
    Given path 'v1', 'onboarding', 'sessions'
    And request { startedAt: '2000-01-01T00:00:00Z', completedSteps: ['LANDING_VISIBLE'], completed: true }
    When method post
    Then status 201
    And match response.startedAt != '2000-01-01T00:00:00Z'
    And match response.startedAt == '#? isIso(_)'
    And match response.completedSteps == []
    And match response.completed == false

  @TC-API-05 @negative @method
  Scenario: TC-API-05 GET sobre /onboarding/sessions responde 405 con esquema Error
    Given path 'v1', 'onboarding', 'sessions'
    When method get
    Then status 405
    And match response contains { code: 'METHOD_NOT_ALLOWED', message: '#string', traceId: '#string' }

  @TC-API-06 @positive
  Scenario: TC-API-06 Registra el primer paso completado
    * def s = call startSession
    Given path 'v1', 'onboarding', 'sessions', s.sid, 'steps'
    And request { step: 'PERSONAL_DATA_COMPLETED' }
    When method post
    Then status 200
    And match response.sessionId == s.sid
    And match response.completedSteps == ['PERSONAL_DATA_COMPLETED']
    And match response.completed == false
    And match response.endedAt == null
    And match response.durationMs == null

  @TC-API-07 @positive @edge
  Scenario: TC-API-07 Los pasos se acumulan en orden y un paso repetido no se duplica
    * def s = call startSession
    * def stepUrl = ['v1', 'onboarding', 'sessions', s.sid, 'steps']

    Given path 'v1', 'onboarding', 'sessions', s.sid, 'steps'
    And request { step: 'PERSONAL_DATA_COMPLETED' }
    When method post
    Then status 200

    Given path 'v1', 'onboarding', 'sessions', s.sid, 'steps'
    And request { step: 'CREDENTIALS_COMPLETED' }
    When method post
    Then status 200
    And match response.completedSteps == ['PERSONAL_DATA_COMPLETED', 'CREDENTIALS_COMPLETED']

    Given path 'v1', 'onboarding', 'sessions', s.sid, 'steps'
    And request { step: 'PERSONAL_DATA_COMPLETED' }
    When method post
    Then status 200
    And match response.completedSteps == ['PERSONAL_DATA_COMPLETED', 'CREDENTIALS_COMPLETED']
    And match response.completed == false

  @TC-API-08 @edge
  Scenario: TC-API-08 Los pasos de una sesión no aparecen en otra
    * def a = call startSession
    * def b = call startSession

    Given path 'v1', 'onboarding', 'sessions', a.sid, 'steps'
    And request { step: 'PERSONAL_DATA_COMPLETED' }
    When method post
    Then status 200

    Given path 'v1', 'onboarding', 'sessions', b.sid, 'steps'
    And request { step: 'CREDENTIALS_COMPLETED' }
    When method post
    Then status 200
    And match response.completedSteps == ['CREDENTIALS_COMPLETED']

  @TC-API-09 @positive @timing
  Scenario: TC-API-09 LANDING_VISIBLE cierra la sesión y calcula la duración
    * def s = call startSession
    * eval Thread.sleep(1500)

    Given path 'v1', 'onboarding', 'sessions', s.sid, 'steps'
    And request { step: 'LANDING_VISIBLE' }
    When method post
    Then status 200
    And match response.completed == true
    And match response.completedSteps contains 'LANDING_VISIBLE'
    And match response.startedAt == s.startedAt
    And match response.endedAt == '#? isIso(_)'
    And match response.durationMs == '#? _ >= 1500 && _ < 60000'
    * def delta = new Date(response.endedAt).getTime() - new Date(s.startedAt).getTime()
    * assert delta >= 0
    * assert Math.abs(delta - response.durationMs) <= 5

  @TC-API-10 @negative
  Scenario: TC-API-10 No se aceptan pasos sobre una sesión cerrada
    * def s = call startSession

    Given path 'v1', 'onboarding', 'sessions', s.sid, 'steps'
    And request { step: 'LANDING_VISIBLE' }
    When method post
    Then status 200

    Given path 'v1', 'onboarding', 'sessions', s.sid, 'steps'
    And request { step: 'LANDING_VISIBLE' }
    When method post
    Then status 409
    And match response contains { code: 'SESSION_CLOSED', message: '#string', traceId: '#string' }

    Given path 'v1', 'onboarding', 'sessions', s.sid, 'steps'
    And request { step: 'PERSONAL_DATA_COMPLETED' }
    When method post
    Then status 409
    And match response.code == 'SESSION_CLOSED'

  @TC-API-11 @negative
  Scenario Outline: TC-API-11 Paso inválido '<step>' devuelve 400 sin reflejar el valor
    * def s = call startSession
    Given path 'v1', 'onboarding', 'sessions', s.sid, 'steps'
    And request { step: '<step>' }
    When method post
    Then status 400
    And match response contains { code: 'INVALID_FIELD', message: '#string', traceId: '#string' }
    And match response.fields[*].field contains 'step'
    And match karate.toString(response) !contains '<step>'

    Examples:
      | step                    |
      | UNKNOWN_STEP            |
      | personal_data_completed |
      | LANDING VISIBLE         |

  @TC-API-12 @negative
  Scenario Outline: TC-API-12 Cuerpo inválido <body> devuelve 400 con campo step
    * def s = call startSession
    * def body = <body>
    Given path 'v1', 'onboarding', 'sessions', s.sid, 'steps'
    And request body
    When method post
    Then status 400
    And match response.code == 'INVALID_FIELD'
    And match response.fields[*].field contains 'step'

    Examples:
      | body          |
      | {}            |
      | { step: null }|
      | { step: 123 } |

  @TC-API-13 @negative
  Scenario: TC-API-13 Sesión inexistente devuelve 404 NOT_FOUND
    * def unknownId = newUuid()
    Given path 'v1', 'onboarding', 'sessions', unknownId, 'steps'
    And request { step: 'PERSONAL_DATA_COMPLETED' }
    When method post
    Then status 404
    And match response contains { code: 'NOT_FOUND', message: '#string', traceId: '#string' }
    And match header X-Trace-Id == response.traceId

  @TC-API-14 @negative
  Scenario: TC-API-14 sessionId malformado devuelve 404 NOT_FOUND (README punto 5)
    Given path 'v1', 'onboarding', 'sessions', 'no-es-un-uuid', 'steps'
    And request { step: 'PERSONAL_DATA_COMPLETED' }
    When method post
    Then status 404
    And match response contains { code: 'NOT_FOUND', message: '#string', traceId: '#string' }
```

### `qa/karate/src/test/resources/karate/onboarding/username-validation.feature`

```gherkin
@api @ca-01 @ca-02-support
Feature: CA-01-D - Validación por campo mientras se escribe (soporte backend: disponibilidad de usuario)
  Contrato bajo prueba: GET /v1/usernames/availability

  Background:
    * url baseUrl
    * def uniqueUser = function(){ return 'qa' + java.lang.Long.toHexString(java.lang.System.nanoTime()) }
    * def repeat = function(ch, n){ var s = ''; for (var i = 0; i < n; i++) s += ch; return s }
    * def validAccount = read('classpath:karate/data/account-valid.json')

  @TC-API-20 @positive
  Scenario: TC-API-20 Usuario libre devuelve available=true sin sugerencias
    * def u = uniqueUser()
    Given path 'v1', 'usernames', 'availability'
    And param username = u
    When method get
    Then status 200
    And match response == { username: '#(u)', available: true }

  @TC-API-21 @edge
  Scenario: TC-API-21 Usuario de exactamente 20 caracteres es aceptado
    * def u = (uniqueUser() + 'zzzzzzzzzzzzzzzzzzzz').substring(0, 20)
    * assert u.length == 20
    Given path 'v1', 'usernames', 'availability'
    And param username = u
    When method get
    Then status 200
    And match response.available == true

  @TC-API-22 @positive
  Scenario Outline: TC-API-22 Usuario con símbolo '<prefix>' es aceptado
    * def u = '<prefix>' + uniqueUser().substring(0, 10)
    Given path 'v1', 'usernames', 'availability'
    And param username = u
    When method get
    Then status 200
    And match response == { username: '#(u)', available: true }

    Examples:
      | prefix |
      | qa.    |
      | qa_    |
      | qa-    |
      | qa!    |

  @TC-API-23 @negative
  Scenario Outline: TC-API-23 Usuario inválido ('<motivo>') devuelve 400
    Given path 'v1', 'usernames', 'availability'
    And param username = '<valor>'
    When method get
    Then status 400
    And match response contains { code: 'INVALID_FIELD', message: '#string', traceId: '#string' }
    And match response.fields[*].field contains 'username'

    Examples:
      | motivo       | valor                  |
      | sin letras   | 12345                  |
      | 21 caracteres| aaaaaaaaaaaaaaaaaaaaa  |
      | con espacio  | con espacio            |

  @TC-API-24 @negative
  Scenario: TC-API-24 Falta el parámetro username
    Given path 'v1', 'usernames', 'availability'
    When method get
    Then status 400
    And match response.code == 'INVALID_FIELD'
    And match response.fields[*].field contains 'username'

  @TC-API-25 @edge
  Scenario: TC-API-25 Parámetro username vacío
    Given path 'v1', 'usernames', 'availability'
    And param username = ''
    When method get
    Then status 400
    And match response.code == 'INVALID_FIELD'

  @TC-API-26 @negative
  Scenario Outline: TC-API-26 Parámetro opcional <param> inválido devuelve 400
    Given path 'v1', 'usernames', 'availability'
    And param username = uniqueUser()
    And param <param> = '<valor>'
    When method get
    Then status 400
    And match response.code == 'INVALID_FIELD'
    And match response.fields[*].field contains '<param>'

    Examples:
      | param           | valor                           |
      | firstNames      | Ana123                          |
      | paternalSurname | Quispe9                         |
      | maternalSurname | Rojas 1                         |
      | firstNames      | Aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa |
      | paternalSurname | Aaaaaaaaaaaaaaaaaaaaa           |

  @TC-API-27 @edge
  Scenario: TC-API-27 Parámetros opcionales en el límite máximo válido
    * def first30 = repeat('A', 30)
    * def last20 = repeat('B', 20)
    Given path 'v1', 'usernames', 'availability'
    And param username = uniqueUser()
    And param firstNames = first30
    And param paternalSurname = last20
    And param maternalSurname = last20
    When method get
    Then status 200
    And match response.available == true

  @TC-API-28 @integration @requires-external
  Scenario: TC-API-28 Usuario ocupado: available=false con sugerencias alfanuméricas
    * def u = uniqueUser()
    * def body = validAccount
    * set body.username = u

    Given path 'v1', 'accounts'
    And request body
    When method post
    Then status 201

    Given path 'v1', 'usernames', 'availability'
    And param username = u.toUpperCase()
    And param firstNames = 'Ana'
    And param paternalSurname = 'Quispe'
    When method get
    Then status 200
    And match response.available == false
    And assert response.suggestions.length > 0 && response.suggestions.length <= 3
    And match each response.suggestions == '#regex ^[A-Za-z0-9]{1,20}$'
    And match response.suggestions !contains u

    Given path 'v1', 'accounts'
    And request body
    When method post
    Then status 409
    And match response.code == 'USERNAME_TAKEN'
    And assert response.suggestions.length > 0
```

### `qa/karate/src/test/resources/karate/onboarding/account-field-validation.feature`

```gherkin
@api @ca-01 @ca-02-support
Feature: CA-01-D - Resultado de validación por campo en el alta (POST /v1/accounts, solo casos rechazados)
  Estos escenarios no crean datos: la validación de esquema ocurre antes de llamar al servicio externo.

  Background:
    * url baseUrl
    * def validAccount = read('classpath:karate/data/account-valid.json')
    * def uniqueUser = function(){ return 'qa' + java.lang.Long.toHexString(java.lang.System.nanoTime()) }

  @TC-API-30 @negative
  Scenario Outline: TC-API-30 Campo <field> inválido devuelve 400 y no refleja el valor
    * def body = validAccount
    * set body.username = uniqueUser()
    * set body.<field> = '<value>'
    Given path 'v1', 'accounts'
    And request body
    When method post
    Then status 400
    And match response contains { code: 'INVALID_FIELD', message: '#string', traceId: '#string' }
    And match response.fields[*].field contains '<field>'
    And match karate.toString(response) !contains '<value>'

    Examples:
      | field           | value   |
      | firstNames      | Ana123  |
      | paternalSurname | Quispe9 |
      | maternalSurname | Rojas1  |
      | username        | 12345   |
      | password        | Zq9!x   |

  @TC-API-31 @negative
  Scenario: TC-API-31 Cuerpo vacío lista todos los campos obligatorios
    Given path 'v1', 'accounts'
    And request {}
    When method post
    Then status 400
    And match response.code == 'INVALID_FIELD'
    And match response.fields[*].field contains ['firstNames', 'paternalSurname', 'maternalSurname', 'username', 'password']
```

### `qa/karate/src/test/resources/karate/onboarding/onboarding-account-integration.feature`

```gherkin
@api @integration @requires-external @ca-01
Feature: CA-01-B/C - Seguimiento de onboarding de extremo a extremo (sesión + alta de cuenta)
  Estos escenarios crean cuentas reales en bcp-wallet-mock (sin endpoint de baja, brecha G-09).

  Background:
    * url baseUrl
    * def isIso = function(s){ return typeof s == 'string' && /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?Z$/.test(s) }
    * def uniqueUser = function(){ return 'qa' + java.lang.Long.toHexString(java.lang.System.nanoTime()) }
    * def newUuid = function(){ return '' + java.util.UUID.randomUUID() }
    * def startSession = read('classpath:karate/common/start-session.feature')
    * def validAccount = read('classpath:karate/data/account-valid.json')

  @TC-API-40
  Scenario: TC-API-40 Sesión + paso de datos + alta de cuenta + landing registra los pasos y la duración
    * def s = call startSession

    Given path 'v1', 'onboarding', 'sessions', s.sid, 'steps'
    And request { step: 'PERSONAL_DATA_COMPLETED' }
    When method post
    Then status 200

    * def body = validAccount
    * set body.username = uniqueUser()
    * set body.onboardingSessionId = s.sid
    Given path 'v1', 'accounts'
    And request body
    When method post
    Then status 201
    And match response.status == 'ACTIVE_BASIC'
    And match response.balanceCents == 0
    And match response.walletId == '#string'
    And match response.firstNames == 'Ana María'
    And match response !contains { password: '#notnull' }
    And match karate.toString(response) !contains 'S3cret!pass'

    Given path 'v1', 'onboarding', 'sessions', s.sid, 'steps'
    And request { step: 'LANDING_VISIBLE' }
    When method post
    Then status 200
    And match response.completedSteps == ['PERSONAL_DATA_COMPLETED', 'ACCOUNT_CREATED', 'LANDING_VISIBLE']
    And match response.completed == true
    And match response.endedAt == '#? isIso(_)'
    And match response.durationMs == '#? _ >= 0'

  @TC-API-41 @edge
  Scenario: TC-API-41 Un onboardingSessionId inexistente no impide crear la cuenta
    * def body = validAccount
    * set body.username = uniqueUser()
    * set body.onboardingSessionId = newUuid()
    Given path 'v1', 'accounts'
    And request body
    When method post
    Then status 201
    And match response.status == 'ACTIVE_BASIC'
```

---

# 3. Selenium (UI e integración UI+API)

El proyecto no recibió especificación de frontend (G-01). Los selectores y la URL **no se inventan**: se leen de `locators.json`, y las pruebas se omiten mientras contenga `PENDIENTE`.

### `qa/selenium/requirements-qa.txt`

```text
selenium>=4.20
pytest>=8.0
httpx>=0.27
```

### `qa/selenium/pytest.ini`

```ini
[pytest]
addopts = -ra
markers =
    ui: pruebas de interfaz (requieren locators.json completo)
    integration: pruebas UI+API
```

### `qa/selenium/locators.example.json`

Copiar a `locators.json` y reemplazar cada `PENDIENTE` con datos reales del frontend. `by` admite: `css`, `xpath`, `id`, `name`.

```json
{
  "onboarding_url": "PENDIENTE",
  "onboarding_screen": { "by": "PENDIENTE", "value": "PENDIENTE" },
  "continue_button": { "by": "PENDIENTE", "value": "PENDIENTE" },
  "fields": {
    "first_names": {
      "input": { "by": "PENDIENTE", "value": "PENDIENTE" },
      "feedback": { "by": "PENDIENTE", "value": "PENDIENTE" }
    },
    "paternal_surname": {
      "input": { "by": "PENDIENTE", "value": "PENDIENTE" },
      "feedback": { "by": "PENDIENTE", "value": "PENDIENTE" }
    },
    "maternal_surname": {
      "input": { "by": "PENDIENTE", "value": "PENDIENTE" },
      "feedback": { "by": "PENDIENTE", "value": "PENDIENTE" }
    },
    "username": {
      "input": { "by": "PENDIENTE", "value": "PENDIENTE" },
      "feedback": { "by": "PENDIENTE", "value": "PENDIENTE" }
    },
    "password": {
      "input": { "by": "PENDIENTE", "value": "PENDIENTE" },
      "feedback": { "by": "PENDIENTE", "value": "PENDIENTE" }
    }
  }
}
```

### `qa/selenium/support.py`

```python
"""Utilidades de las pruebas UI de CA-01. No contienen selectores ni URLs del frontend."""
from __future__ import annotations

import json
import os
import re
import time
from typing import Any, Callable
from urllib.parse import parse_qs, urlparse

from selenium.webdriver.common.by import By

PENDING = "PENDIENTE"
BY_MAP = {"css": By.CSS_SELECTOR, "xpath": By.XPATH, "id": By.ID, "name": By.NAME}

# Pasos permitidos por el contrato del backend (schemas.OnboardingStepName).
STEP_ENUM = {
    "PERSONAL_DATA_COMPLETED",
    "CREDENTIALS_COMPLETED",
    "ACCOUNT_CREATED",
    "LANDING_VISIBLE",
}
SESSIONS_PATH_RE = re.compile(r"/onboarding/sessions$")
STEPS_PATH_RE = re.compile(r"/onboarding/sessions/([0-9a-fA-F-]{36})/steps$")
AVAILABILITY_PATH_RE = re.compile(r"/usernames/availability$")


def timeout_s() -> float:
    return float(os.getenv("UI_TIMEOUT_S", "10"))


def find_pending(node: Any, path: str = "") -> list[str]:
    """Devuelve las rutas de claves que todavía valen PENDIENTE."""
    found: list[str] = []
    if isinstance(node, dict):
        for key, value in node.items():
            found += find_pending(value, f"{path}.{key}" if path else key)
    elif node == PENDING:
        found.append(path)
    return found


def by_tuple(spec: dict) -> tuple[str, str]:
    return BY_MAP[spec["by"]], spec["value"]


def locate(driver, spec: dict):
    return driver.find_element(*by_tuple(spec))


class NetworkRecorder:
    """Acumula las peticiones de red del navegador (Chrome, log 'performance')."""

    def __init__(self, driver) -> None:
        self._driver = driver
        self.events: list[dict] = []

    def poll(self) -> None:
        for entry in self._driver.get_log("performance"):
            message = json.loads(entry["message"])["message"]
            if message.get("method") != "Network.requestWillBeSent":
                continue
            request = message["params"]["request"]
            parsed = urlparse(request["url"])
            self.events.append(
                {
                    "method": request["method"],
                    "url": request["url"],
                    "path": parsed.path,
                    "query": parse_qs(parsed.query),
                    "post_data": request.get("postData"),
                }
            )

    def wait_for(self, predicate: Callable[[dict], bool], timeout: float | None = None) -> list[dict]:
        deadline = time.time() + (timeout if timeout is not None else timeout_s())
        while True:
            self.poll()
            matches = [e for e in self.events if predicate(e)]
            if matches:
                return matches
            if time.time() > deadline:
                return []
            time.sleep(0.2)

    def count(self, predicate: Callable[[dict], bool]) -> int:
        self.poll()
        return len([e for e in self.events if predicate(e)])


def is_session_start(event: dict) -> bool:
    return event["method"] == "POST" and bool(SESSIONS_PATH_RE.search(event["path"]))


def is_step(event: dict) -> bool:
    return event["method"] == "POST" and bool(STEPS_PATH_RE.search(event["path"]))
```

### `qa/selenium/conftest.py`

```python
import json
import os
import pathlib

import pytest
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from support import NetworkRecorder, by_tuple, find_pending, timeout_s


@pytest.fixture(scope="session")
def locators():
    path = pathlib.Path(os.getenv("UI_LOCATORS_FILE", "locators.json"))
    if not path.exists():
        pytest.skip(
            "PENDIENTE: falta locators.json (brecha G-01: no se recibió la especificación del frontend). "
            "Copiar locators.example.json y completarlo."
        )
    data = json.loads(path.read_text(encoding="utf-8"))
    pending = find_pending(data)
    if pending:
        pytest.skip("PENDIENTE: valores sin completar en locators.json: " + ", ".join(pending))
    return data


@pytest.fixture
def driver(locators):
    options = Options()
    if os.getenv("HEADLESS", "true").lower() != "false":
        options.add_argument("--headless=new")
    options.add_argument("--window-size=1280,900")
    options.set_capability("goog:loggingPrefs", {"performance": "ALL"})
    drv = webdriver.Chrome(options=options)
    yield drv
    drv.quit()


@pytest.fixture
def onboarding(driver, locators):
    """Abre la pantalla de onboarding y espera a que sea visible. Devuelve (driver, recorder, locators)."""
    recorder = NetworkRecorder(driver)
    driver.get(locators["onboarding_url"])
    WebDriverWait(driver, timeout_s()).until(
        EC.visibility_of_element_located(by_tuple(locators["onboarding_screen"]))
    )
    return driver, recorder, locators
```

### `qa/selenium/test_onboarding_ca01_ui.py`

```python
"""Pruebas UI e integración UI+API para CA-01 (HU 01 Onboarding Wallet).

Las pruebas dependen de locators.json (brecha G-01). Estado de esta suite: NO EJECUTADO.
"""
from __future__ import annotations

import json
import os
import uuid

import httpx
import pytest
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait

from support import (
    AVAILABILITY_PATH_RE,
    STEP_ENUM,
    STEPS_PATH_RE,
    is_session_start,
    is_step,
    locate,
    timeout_s,
)

pytestmark = pytest.mark.ui

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8080")

# (campo, valor válido, valor inválido). Fuente: reglas de CA-02 y esquemas del backend.
FIELD_CASES = [
    ("first_names", "Ana María", "Ana123"),
    ("paternal_surname", "Quispe", "Quispe9"),
    ("maternal_surname", "Rojas", "Roj@s"),
    ("username", lambda: "qa" + uuid.uuid4().hex[:10], "12345"),
    ("password", "S3cret!pass", "Zq9!x"),
]


def clear_input(element) -> None:
    # Se simula edición de teclado para disparar los eventos de entrada del campo.
    element.send_keys(Keys.CONTROL, "a")
    element.send_keys(Keys.BACKSPACE)


def feedback_text(driver, locators, field: str) -> str:
    return locate(driver, locators["fields"][field]["feedback"]).text.strip()


def fill_valid_form(driver, locators) -> str:
    """Llena los 5 campos con datos sintéticos válidos. Devuelve el usuario generado."""
    username = "qa" + uuid.uuid4().hex[:10]
    values = {
        "first_names": "Ana María",
        "paternal_surname": "Quispe",
        "maternal_surname": "Rojas",
        "username": username,
        "password": "S3cret!pass",
    }
    for field, value in values.items():
        locate(driver, locators["fields"][field]["input"]).send_keys(value)
    return username


# ------------------------------------------------------------------ TC-UI-01
def test_ui_01_session_starts_when_onboarding_screen_is_visible(onboarding):
    """CA-01-A. Esperado: exactamente un POST .../onboarding/sessions con la pantalla visible."""
    _, recorder, _ = onboarding
    matches = recorder.wait_for(is_session_start)
    assert matches, "No se observó POST .../onboarding/sessions al mostrarse la pantalla"
    assert recorder.count(is_session_start) == 1, "Se emitió más de una sesión al cargar la pantalla"


# ------------------------------------------------------------------ TC-UI-02
def test_ui_02_completed_step_is_sent_to_backend(onboarding):
    """CA-01-C. Esperado: POST .../sessions/{id}/steps con un step del enum, siempre en la misma sesión."""
    driver, recorder, locators = onboarding
    fill_valid_form(driver, locators)
    locate(driver, locators["continue_button"]).click()

    steps = recorder.wait_for(is_step)
    assert steps, "No se observó ningún POST de paso completado tras continuar"
    session_ids = set()
    for event in steps:
        body = json.loads(event["post_data"] or "{}")
        assert body.get("step") in STEP_ENUM, f"Paso fuera del contrato: {body}"
        session_ids.add(STEPS_PATH_RE.search(event["path"]).group(1))
    assert len(session_ids) == 1, f"Los pasos usaron sesiones distintas: {session_ids}"


# ------------------------------------------------------------------ TC-UI-03
@pytest.mark.parametrize("field,valid,invalid", FIELD_CASES, ids=[c[0] for c in FIELD_CASES])
def test_ui_03_field_shows_validation_result_while_typing(onboarding, field, valid, invalid):
    """CA-01-D. Esperado: el resultado aparece sin salir del campo y cambia con un valor válido."""
    driver, _, locators = onboarding
    valid_value = valid() if callable(valid) else valid
    input_el = locate(driver, locators["fields"][field]["input"])

    input_el.send_keys(invalid)
    WebDriverWait(driver, timeout_s()).until(lambda d: feedback_text(d, locators, field) != "")
    invalid_text = feedback_text(driver, locators, field)
    assert driver.switch_to.active_element == input_el, "El resultado debía mostrarse sin salir del campo"

    clear_input(input_el)
    input_el.send_keys(valid_value)
    WebDriverWait(driver, timeout_s()).until(lambda d: feedback_text(d, locators, field) != invalid_text)


# ------------------------------------------------------------------ TC-UI-04
def test_ui_04_username_availability_is_checked_while_typing(onboarding):
    """CA-01-D. Esperado: GET .../usernames/availability?username=<valor> sin otra acción del usuario."""
    driver, recorder, locators = onboarding
    username = "qa" + uuid.uuid4().hex[:10]
    locate(driver, locators["fields"]["username"]["input"]).send_keys(username)

    def matches_username(event: dict) -> bool:
        return (
            event["method"] == "GET"
            and bool(AVAILABILITY_PATH_RE.search(event["path"]))
            and username in event["query"].get("username", [])
        )

    assert recorder.wait_for(matches_username), "No se consultó la disponibilidad del usuario al escribir"


# ------------------------------------------------------------------ TC-INT-01
@pytest.mark.integration
def test_int_01_ui_session_is_tracked_by_backend(onboarding):
    """CA-01-A/B/C. Usa el sessionId de la UI y cierra la sesión por API."""
    driver, recorder, locators = onboarding
    fill_valid_form(driver, locators)
    locate(driver, locators["continue_button"]).click()

    steps = recorder.wait_for(is_step)
    assert steps, "La UI no registró ningún paso"
    session_id = STEPS_PATH_RE.search(steps[0]["path"]).group(1)
    ui_steps = {json.loads(e["post_data"] or "{}").get("step") for e in steps}

    response = httpx.post(
        f"{API_BASE_URL}/v1/onboarding/sessions/{session_id}/steps",
        json={"step": "LANDING_VISIBLE"},
        timeout=10,
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["sessionId"] == session_id
    assert data["completed"] is True
    assert isinstance(data["durationMs"], int) and data["durationMs"] >= 0
    assert ui_steps.issubset(set(data["completedSteps"]))
```

---

## Resumen operativo

- **Estado de todas las pruebas: NO EJECUTADO.** No hay resultados observados, y ninguna corrección se marca como verificada.
- **Karate** (24 pruebas: 20 sin servicio externo y 4 que lo requieren, incluidas las de integración API) se puede ejecutar ya con los comandos de la sección 7.4. Primero hay que levantar el backend y confirmar el humo (sección 7.3).
- **Selenium** (5 pruebas, incluida 1 de integración UI+API) está **bloqueado** hasta recibir la especificación del frontend (G-01). Mientras tanto se omite con motivo explícito, sin marcarse como pasado.
- **Pendientes de definición:** G-01 a G-11 (sección 4 del informe), CA-02 a CA-13 sin diseñar, y el contrato completo de `bcp-wallet-mock` para las pruebas que crean cuentas.