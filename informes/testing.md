# Entrega de pruebas: HU 01 Onboarding Wallet, alcance CA-01

Fecha de elaboración: 2026-10-30. Ninguna prueba fue ejecutada. No hubo acceso a un entorno, un navegador ni al Wallet mock. Todo "resultado" de este documento es **esperado**, derivado de la lectura del código del backend. Los resultados observados están vacíos.

Estructura de archivos propuesta, sin tocar `app/`, `tests/` ni `pytest.ini`:

```
testing_report.md
qa/karate/karate-config.js
qa/karate/features/helpers/start-session.feature
qa/karate/features/helpers/register-user.feature
qa/karate/features/onboarding-session.feature
qa/karate/features/username-validation.feature
qa/karate/features/registration-metrics.feature
qa/selenium/requirements-e2e.txt
qa/selenium/locators.json
qa/selenium/conftest.py
qa/selenium/test_ca01_onboarding_ui.py
```

Las pruebas Selenium están fuera de `tests/` a propósito. `pytest.ini` define `testpaths = tests`, así que `pytest` no recoge `qa/selenium` salvo que se indique la ruta explícitamente.

---

## 1. `testing_report.md`

````markdown
# Testing Report — HU 01 Onboarding de usuario billetera digital (Wallet)

- Fecha: 2026-10-30
- Alcance de criterios recibido: **solo CA-01** (Inicio y seguimiento).
- Estado global: **NO EJECUTADO** (no existe salida real de ninguna ejecución).
- Convención: "Resultado esperado" = derivado del código/especificación. "Resultado observado" = salida real de una ejecución; hoy **vacío** en todas las pruebas.

## 1. Fuentes analizadas

| Fuente | Disponible | Observación |
|---|---|---|
| Historia de usuario HU 01 (CA-01..CA-13) | Sí | Solo CA-01 fue indicado como criterio a verificar. |
| Especificaciones adicionales (respuestas 1–10) | Sí | Resp. 7: la medición de tiempo termina **al responder el registro**. Resp. 2: sin token, auth fuera de alcance. Resp. 10: idempotencia fuera de alcance. |
| Código del backend FastAPI (`app/`) y pruebas pytest (`tests/`) | Sí | Contrato inferido del código (routers/schemas). No se entregó un archivo OpenAPI. |
| Frontend Angular | **Solo lista de archivos** | No hay contenido de componentes, rutas, plantillas ni `proxy.conf.json`. |
| Contrato del Wallet mock externo (grupo 8) | Solo las URL de la HU | El propio README del backend indica que cuerpo y respuesta de `POST /kyc/verifications` y `GET /wallets/{id}` son supuestos. |
| Proyecto Karate / Selenium preexistente | **No existe** | No hay `pom.xml`, runner ni suite Selenium. Se propone una estructura mínima en `qa/`. |

## 2. Brechas de información (PENDIENTES)

| ID | Brecha | Impacto | Qué se necesita |
|---|---|---|---|
| P-01 | Contenido del frontend desconocido (selectores, rutas, mensajes de validación, momento en que se envía cada paso, momento en que se crea la sesión). | Las pruebas Selenium no pueden fijar selectores reales. `qa/selenium/locators.json` está con valores `null` y las pruebas se **saltan** (skip) con la etiqueta PENDIENTE hasta completarlo. | Plantillas HTML de `onboarding.component.ts` o `data-testid`/IDs estables; ruta de onboarding en `app.routes.ts`; URL/puerto del `ng serve`. |
| P-02 | Contrato del Wallet mock no verificado (campos de `POST /kyc/verifications`). | Los escenarios etiquetados `@wallet` dependen de que el registro (`POST /v1/users`) devuelva 201. | Confirmar que `WALLET_BASE_URL=https://bcp-wallet-mock.yefri.workers.dev/groups/8` es correcto (httpx concatena el path base con `/kyc/verifications`; no probado) y el esquema real de `Kyc`. |
| P-03 | No hay endpoint de consulta (GET) de la sesión de onboarding ni de borrado de usuarios/sesiones/wallets. | El estado de sesión solo se infiere por las respuestas de `steps` y `users`. La limpieza de wallets en el Wallet externo no está definida. | Contrato de limpieza del Wallet mock (si existe). |
| P-04 | Versión de Karate y JDK a usar no definida en el proyecto. | El comando usa la variable `KARATE_JAR`; el JAR y su versión deben ser acordados. | Decisión del equipo (se propone el JAR *standalone* para no agregar Maven/Gradle). |
| P-05 | Texto/forma exacta de los mensajes de validación en UI y del feedback "disponible / no disponible". | Las pruebas UI verifican **presencia y cambio** de feedback, no el texto exacto. | Textos esperados del diseño. |
| P-06 | CA-01 dice que el tiempo "inicia cuando la pantalla de onboarding es visible". El backend toma `started_at` al recibir `POST /onboarding/sessions`. | Que la UI llame al endpoint exactamente al hacerse visible la pantalla solo es verificable por UI (UI-01) y requiere P-01. | Confirmar con frontend en qué evento (init del componente, `AfterViewInit`, etc.) se llama. |
| P-07 | Criterios CA-02…CA-13 no fueron solicitados como alcance de esta tarea. | No se diseñó cobertura para ellos (ver §8). | Solicitud de ampliación de alcance. |

## 3. Descomposición de CA-01

| Sub-criterio | Texto |
|---|---|
| CA-01.a | La medición del tiempo de registro inicia cuando la pantalla de onboarding es visible. |
| CA-01.b | El sistema registra el tiempo (inicio, fin y duración; el fin es la respuesta del registro, según resp. 7). |
| CA-01.c | El sistema registra los pasos completados. |
| CA-01.d | Los campos muestran el resultado de su validación mientras el usuario ingresa cada valor. |

## 4. Matriz de trazabilidad

| Sub-criterio | Pruebas Karate (API) | Pruebas Selenium (UI / integración) | Existentes pytest (referencia, no ejecutadas) |
|---|---|---|---|
| CA-01.a | KAR-S01, KAR-S02, KAR-S03 | UI-01 | `test_start_session_returns_201` |
| CA-01.b | KAR-M01, KAR-M02, KAR-M03, KAR-M04 | — (INT-01 pendiente, ver §7) | `test_register_success` (métricas) |
| CA-01.c | KAR-S04…KAR-S14, KAR-M01, KAR-M02 | UI-04 (integración UI→API) | `test_register_step_records_only_names`, `test_all_step_names_are_accepted`, `test_invalid_step_is_400_without_echo`, `test_step_on_completed_session_is_409` |
| CA-01.d | KAR-U01…KAR-U07 (contrato que soporta la validación en vivo), KAR-M05…KAR-M08 | UI-02, UI-03, UI-05 | `test_available_username`, `test_invalid_username_is_400`, `test_invalid_names_is_400`, `test_weak_value_is_400_without_echo` |

Corrección propuesta mencionada en la entrega del backend: `StepName` se define con la API funcional de `Enum`. Las pruebas generan los valores de contraseña en tiempo de ejecución. Se cubre con KAR-S04 (los 5 nombres de paso son aceptados), KAR-S07/S08/S09 (valores inválidos rechazados) y las pruebas pytest existentes. Estado: **NO VERIFICADA** (sin ejecución).

## 5. Catálogo de pruebas, resultados esperados y estado

Todos los estados son **NO EJECUTADO**. Resultado observado: **—** (sin evidencia).
Etiqueta `@wallet` = requiere que el Wallet mock responda 201 al crear la wallet.

### 5.1 Karate — `qa/karate/features/onboarding-session.feature`

| ID | Caso (tipo) | Método y ruta | Resultado esperado | Estado |
|---|---|---|---|---|
| KAR-S01 | Inicio de sesión (positivo) | POST `/v1/onboarding/sessions` | 201; `{session_id: uuid, status: "OPEN", started_at: ISO con offset -05:00, completed_steps: []}`; Content-Type JSON | NO EJECUTADO |
| KAR-S02 | `started_at` cercano a la hora real (borde, `@local-clock`) | ídem | `started_at` dentro de ±60 s del reloj del cliente (válido solo si cliente y servidor comparten reloj) | NO EJECUTADO |
| KAR-S03 | Unicidad de sesiones (positivo) | POST ×2 | Dos `session_id` distintos | NO EJECUTADO |
| KAR-S04 | Registro de cada paso válido (positivo, outline ×5: NAMES, PATERNAL_SURNAME, MATERNAL_SURNAME, USERNAME, PASSWORD) | POST `/v1/onboarding/sessions/{id}/steps` | 200; `status: "OPEN"`; `completed_steps == [<paso>]` | NO EJECUTADO |
| KAR-S05 | Orden y duplicados (borde) | steps: USERNAME, NAMES, NAMES | 200 en las 3; `completed_steps == ["USERNAME","NAMES"]` (sin duplicar) | NO EJECUTADO |
| KAR-S06 | Los 5 pasos (positivo) | steps ×5 | Último `completed_steps` con 5 elementos | NO EJECUTADO |
| KAR-S07 | Paso inválido (negativo) | `{"step":"PASO_XYZ"}` | 400; `code: VALIDATION_ERROR`; `details[0].field == "step"`; `trace_id` presente; el valor enviado no aparece en la respuesta | NO EJECUTADO |
| KAR-S08 | Paso ausente (negativo) | `{}` | 400; `VALIDATION_ERROR`; `details[0].issue == "REQUIRED"` | NO EJECUTADO |
| KAR-S09 | Paso en minúsculas (borde/negativo) | `{"step":"names"}` | 400; `VALIDATION_ERROR` | NO EJECUTADO |
| KAR-S10 | Paso inválido no altera estado | inválido y luego NAMES | Tras el 400, NAMES responde 200 con `completed_steps == ["NAMES"]` | NO EJECUTADO |
| KAR-S11 | Campo extra con dato personal (negativo/privacidad) | `{"step":"NAMES","value":"Juan"}` | 200; la respuesta no contiene "Juan"; `completed_steps == ["NAMES"]` | NO EJECUTADO |
| KAR-S12 | Sesión inexistente (negativo) | UUID aleatorio | 404; `{code: NOT_FOUND, message, trace_id}` | NO EJECUTADO |
| KAR-S13 | ID de sesión mal formado (borde) | `no-es-uuid` | 404; `NOT_FOUND` (comportamiento documentado en el README) | NO EJECUTADO |
| KAR-S14 | Paso sobre sesión completada (negativo, `@wallet`) | registro exitoso y luego step | 409; `SESSION_ALREADY_COMPLETED` | NO EJECUTADO |

### 5.2 Karate — `qa/karate/features/username-validation.feature`

Soporta la "validación mientras el usuario ingresa" (CA-01.d). Aplica las reglas de CA-02 como datos de entrada.

| ID | Caso (tipo) | Resultado esperado | Estado |
|---|---|---|---|
| KAR-U01 | Usuario disponible (positivo) | 200; `{username, available: true, suggestions: []}` | NO EJECUTADO |
| KAR-U02a | Usuarios válidos en el límite (outline: 1 carácter, 20 caracteres, con símbolos `a_b.c-1`) | 200; `available: true` | NO EJECUTADO |
| KAR-U02b | Usuarios inválidos (outline: con espacio → `INVALID_USERNAME`; solo dígitos → `INVALID_USERNAME`; 21 caracteres → `TOO_LONG`) | 400; `VALIDATION_ERROR`; `details[0].field == "username"`; `details[0].issue` según caso; el valor no se devuelve | NO EJECUTADO |
| KAR-U02c | Usuario vacío (borde) | 400; `details[0].issue == "TOO_SHORT"` | NO EJECUTADO |
| KAR-U03 | Usuario ausente (negativo) | 400; `issue == "REQUIRED"` | NO EJECUTADO |
| KAR-U04 | Nombres inválidos (`Juan1`; 31 letras) | 400; `field == "names"`; `INVALID_CHARACTERS` / `TOO_LONG` | NO EJECUTADO |
| KAR-U05 | Apellidos inválidos (con espacio; 21 letras) | 400; `field == "paternal_surname"`; `INVALID_CHARACTERS` / `TOO_LONG` | NO EJECUTADO |
| KAR-U06 | Nombres con tilde y espacio, y límites válidos (30 / 20 letras) (positivo) | 200 | NO EJECUTADO |
| KAR-U07 | Usuario no disponible, comparación sin distinguir mayúsculas (`@wallet`) | 200; `available: false`; 1 a 5 sugerencias; cada una coincide con `[A-Za-z0-9]{1,20}`; sin repetidas; ninguna igual al usuario pedido | NO EJECUTADO |

### 5.3 Karate — `qa/karate/features/registration-metrics.feature`

| ID | Caso (tipo) | Resultado esperado | Estado |
|---|---|---|---|
| KAR-M01 | Registro tras 2 pasos (positivo, `@wallet`) | 201; `registration_metrics` con `session_id` igual al de la sesión; `started_at` igual al de `POST /sessions`; `completed_at >= started_at`; `duration_ms >= 0` y coherente con la resta de fechas (±2 ms); `duration_ms` ≤ tiempo medido por el cliente (+100 ms); `completed_steps == ["NAMES","USERNAME"]`; la contraseña no aparece en la respuesta | NO EJECUTADO |
| KAR-M02 | Registro sin pasos (borde, `@wallet`) | 201; `completed_steps == []`; `duration_ms >= 0` (comportamiento observado en código; la HU no exige pasos obligatorios) | NO EJECUTADO |
| KAR-M03 | Reutilizar sesión ya completada (negativo, `@wallet`) | 409; `SESSION_ALREADY_COMPLETED` | NO EJECUTADO |
| KAR-M04 | Registro rechazado por contraseña débil no cierra la sesión y no llama al Wallet (negativo) | 400; `details[0] == {field: "password", issue: "PASSWORD_WEAK"}`; el valor no se devuelve; luego `POST steps` sobre la misma sesión → 200 | NO EJECUTADO |
| KAR-M05 | Contraseña corta (borde) | 400; `issue == "TOO_SHORT"` | NO EJECUTADO |
| KAR-M06 | Sesión inexistente en registro (negativo) | 404; `NOT_FOUND` | NO EJECUTADO |
| KAR-M07 | Cuerpo vacío (negativo) | 400; algún `details[].issue == "REQUIRED"` | NO EJECUTADO |
| KAR-M08 | `session_id` con formato inválido en el cuerpo (negativo) | 400; `field == "session_id"`; `issue == "INVALID_UUID"` | NO EJECUTADO |

### 5.4 Selenium — `qa/selenium/test_ca01_onboarding_ui.py`

Bloqueadas hasta completar `locators.json` (P-01). Mientras tanto se saltan con mensaje PENDIENTE, y un skip **no** equivale a pasar.

| ID | Caso | Resultado esperado | Estado |
|---|---|---|---|
| UI-01 | Al hacerse visible la pantalla de onboarding se crea la sesión (CA-01.a) | Elemento marcador visible y, en ≤5 s, exactamente una petición `POST …/onboarding/sessions` en el log de red | NO EJECUTADO |
| UI-02 | Validación en vivo por campo (nombres, apellido paterno, apellido materno, usuario) sin perder foco ni enviar | Tras escribir un valor inválido aparece feedback no vacío; tras escribir uno válido el feedback cambia (otro texto o desaparece) | NO EJECUTADO |
| UI-03 | Límites de longitud (nombres 31, apellido paterno 21, usuario 21) | El campo trunca al máximo, o se muestra feedback de error | NO EJECUTADO |
| UI-04 | Integración UI→API de pasos: al completar el campo de nombres y salir del foco | Se envía `POST …/steps` con cuerpo cuyas únicas claves son `step` y `step == "NAMES"`; el valor escrito no viaja en el cuerpo | NO EJECUTADO |
| UI-05 | Integración UI→API de disponibilidad de usuario | Se envía `POST …/usernames/availability-checks` con el `username` escrito y el feedback del campo es no vacío | NO EJECUTADO |

## 6. Pruebas pytest existentes (referencia)

El backend incluye `tests/` con `TestClient` y un doble del Wallet. **No fueron ejecutadas** en este trabajo. Comando: `pytest`. Estado: NO EJECUTADO.

## 7. Integración UI↔API pendiente

| ID | Caso | Bloqueo |
|---|---|---|
| INT-01 | Enviar el formulario completo desde la UI y verificar que `POST /v1/users` devuelve 201 con `registration_metrics` consistentes con los pasos enviados | Requiere P-01 (selector de botón de envío y campos), P-02 (Wallet mock operativo) y lectura del cuerpo de respuesta (CDP `Network.getResponseBody`) o un hook de la app. Marcada **PENDIENTE**, sin código. |

## 8. Cobertura fuera del alcance solicitado

CA-02 a CA-13 no están diseñadas aquí (P-07). Los escenarios de este reporte tocan reglas de CA-02 solo como datos de entrada de CA-01.d. No se verificaron contadores diarios ni operaciones de pago/recarga: el README del backend indica que no están implementados en esta HU.

## 9. Observaciones del análisis de código (no son resultados de prueba)

- `started_at` es el instante en que el servidor procesa `POST /onboarding/sessions`, no el instante en que la pantalla es visible (P-06).
- La API no impone orden ni obligatoriedad de pasos; `completed_steps` conserva el orden de primera finalización y no repite pasos.
- No hay `GET` de sesión; la verificación de estado es indirecta.
- Sin idempotencia (fuera de alcance, resp. 10): reintentar un registro fallido tras crear la wallet puede dejar wallets huérfanas en el Wallet externo.

## 10. Requisitos previos

| Requisito | Detalle |
|---|---|
| Python 3.12 | Coincide con el `Dockerfile` del proyecto. |
| Dependencias backend | `pip install -r requirements.txt` |
| JDK + Karate | JAR *standalone* de Karate (versión a acordar, P-04). Variable `KARATE_JAR`. |
| Chrome + Selenium | Google Chrome instalado. `pip install -r qa/selenium/requirements-e2e.txt` (Selenium Manager resuelve el driver; requiere acceso de red la primera vez). |
| Node/npm | Solo para levantar el frontend Angular; los scripts exactos de `package.json` no se conocen. |
| Red | Acceso a `https://bcp-wallet-mock.yefri.workers.dev` para los escenarios `@wallet`. |

Variables de entorno del backend para las pruebas:
- `APP_ENV=test`
- `WALLET_BASE_URL=https://bcp-wallet-mock.yefri.workers.dev/groups/8` (supuesto P-02)

Variables de las pruebas:
- Karate: `-DbaseUrl=http://localhost:8000/v1` (valor por defecto del config)
- Selenium: `FRONTEND_URL` (obligatoria, sin valor por defecto), `ONBOARDING_PATH` (opcional, ruta relativa), `E2E_HEADLESS` (por defecto `true`)

## 11. Comandos

### 11.1 Preparar y levantar el backend (Linux/macOS)

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

export APP_ENV=test
export WALLET_BASE_URL="https://bcp-wallet-mock.yefri.workers.dev/groups/8"
nohup uvicorn app.main:app --port 8000 > /tmp/wallet-api.log 2>&1 &
echo $! > /tmp/wallet-api.pid

# Comprobación (esperado: 200)
curl -s -o /dev/null -w "%{http_code}\n" http://localhost:8000/openapi.json
```

### 11.2 Karate (API)

```bash
export KARATE_JAR=/ruta/a/karate-<version>.jar   # PENDIENTE P-04
cd qa/karate

# Suite completa (requiere Wallet mock operativo)
java -DbaseUrl=http://localhost:8000/v1 -jar "$KARATE_JAR" -o target/karate features

# Solo escenarios que NO dependen del Wallet mock
java -DbaseUrl=http://localhost:8000/v1 -jar "$KARATE_JAR" -t "~@wallet" -o target/karate features

# Solo escenarios que dependen del Wallet mock
java -DbaseUrl=http://localhost:8000/v1 -jar "$KARATE_JAR" -t "@wallet" -o target/karate features
```

Los helpers llevan la etiqueta `@ignore` y no deben ejecutarse solos. Reporte HTML en `qa/karate/target/karate/`. Verificar las opciones del JAR con `java -jar "$KARATE_JAR" --help`.

### 11.3 Selenium (UI)

```bash
pip install -r qa/selenium/requirements-e2e.txt

# Frontend (PENDIENTE P-01: confirmar scripts de package.json y puerto)
npm install
npm start    # supuesto

export FRONTEND_URL=http://localhost:4200   # supuesto: confirmar
export E2E_HEADLESS=true
# Completar primero qa/selenium/locators.json
pytest qa/selenium -v
```

### 11.4 Pruebas unitarias/API existentes (referencia)

```bash
pytest
```

### 11.5 Limpieza

```bash
# Detener backend (los datos son en memoria y desaparecen al detenerlo)
kill "$(cat /tmp/wallet-api.pid)" && rm -f /tmp/wallet-api.pid /tmp/wallet-api.log

# Detener el frontend con Ctrl+C en su terminal

# Reportes y cachés de prueba
rm -rf qa/karate/target qa/selenium/__pycache__ .pytest_cache

# Opcional: entorno virtual
deactivate && rm -rf .venv
```

Las wallets creadas en el Wallet mock externo por los escenarios `@wallet` **no tienen operación de borrado conocida** (P-03). Quedan en el servicio externo y deben identificarse con el `user_id` de la referencia externa (`external_reference`).

## 12. Datos de prueba sintéticos

| Dato | Valor / generación |
|---|---|
| Usuario único | `qa` + 12 caracteres hex aleatorios (14 caracteres) generado en `karate-config.js` |
| Contraseña válida | `Aa1` + 12 hex aleatorios (generada en ejecución, sin literales en el repositorio) |
| Contraseña débil | 12 letras `a` generadas con `'a'.repeat(12)` |
| Contraseña corta | `'A1'.repeat(3)` (6 caracteres) |
| Nombres | `Juan Carlos`, `José María` |
| Apellidos | `Perez`, `Rojas` |
| UUID inexistente | `6f1b1c1e-0000-4000-8000-000000000000` |
| Nombre de 30 letras | `Abcdefghijklmnopqrstuvwxyzabcd` |
| Apellido de 20 letras | `Abcdefghijklmnopqrst` |

No se usan datos personales reales, correos, celulares ni fotos de DNI.

## 13. Resumen de estado

| Conjunto | Pruebas | Estado |
|---|---|---|
| Karate onboarding-session | 14 IDs (KAR-S01…S14) | NO EJECUTADO |
| Karate username-validation | 9 IDs (KAR-U01…U07 con sub-casos) | NO EJECUTADO |
| Karate registration-metrics | 8 IDs (KAR-M01…M08) | NO EJECUTADO |
| Selenium | 5 IDs (UI-01…UI-05) | NO EJECUTADO (bloqueadas por P-01) |
| Integración INT-01 | 1 | PENDIENTE (sin código) |
| pytest existente | suite completa | NO EJECUTADO |
| Corrección `StepName`/contraseñas sin literales | — | NO VERIFICADA |

Resultados observados: ninguno. Este reporte debe actualizarse con la salida real (`qa/karate/target/karate/`, salida de `pytest`) antes de marcar cualquier prueba como ejecutada o aprobada.

## 14. Limitaciones de este entregable

- Los archivos `.feature` y Python no fueron ejecutados ni validados sintácticamente contra una versión concreta de Karate o Selenium. Pueden requerir ajustes menores en la primera corrida.
- Las aserciones de UI son estructurales (presencia/cambio de feedback), no de texto, hasta resolver P-05.
- `postData` de las peticiones puede no estar disponible en el log de rendimiento de Chrome; en ese caso UI-04 y UI-05 se marcan como inconclusas (skip), no como aprobadas.
````

---

## 2. Karate

### `qa/karate/karate-config.js`

```javascript
function fn() {
  var UUID = Java.type('java.util.UUID');
  var System = Java.type('java.lang.System');

  function hex(n) {
    return ('' + UUID.randomUUID()).replace(/-/g, '').substring(0, n);
  }

  var baseUrl = karate.properties['baseUrl'] || System.getenv('API_BASE_URL') || 'http://localhost:8000/v1';

  karate.configure('connectTimeout', 10000);
  // El registro llama al Wallet mock externo (timeouts del backend: 2 s conexión, 5 s lectura).
  karate.configure('readTimeout', 30000);

  return {
    baseUrl: baseUrl,
    unknownUuid: '6f1b1c1e-0000-4000-8000-000000000000',
    // Usuario sintético: 14 caracteres, con letras, sin símbolos ni espacios.
    uniqueUsername: function () { return 'qa' + hex(12); },
    // Valor sintético válido: >= 10 caracteres con letras y números, generado en ejecución.
    validPassword: function () { return 'Aa1' + hex(12); },
    // Valor sintético débil: 12 letras, sin números.
    weakPassword: function () { return 'a'.repeat(12); },
    // Valor sintético corto: 6 caracteres.
    shortPassword: function () { return 'A1'.repeat(3); },
    distinctCount: function (list) {
      var seen = {};
      var n = karate.sizeOf(list);
      for (var i = 0; i < n; i++) { seen[list[i]] = true; }
      return Object.keys(seen).length;
    }
  };
}
```

### `qa/karate/features/helpers/start-session.feature`

```gherkin
@ignore
Feature: Helper - iniciar sesión de onboarding

  Scenario: Inicia sesión
    Given url baseUrl
    And path 'onboarding', 'sessions'
    When method post
    Then status 201
    * def sessionId = response.session_id
    * def startedAt = response.started_at
```

### `qa/karate/features/helpers/register-user.feature`

```gherkin
@ignore
Feature: Helper - registrar usuario (no valida el código de estado)

  # Argumentos: sessionId (obligatorio), username (opcional), overrides (opcional, mapa de campos del cuerpo)
  Scenario: Registra usuario
    * def username = karate.get('username') || uniqueUsername()
    * def overrides = karate.get('overrides') || {}
    * def base = { session_id: '#(sessionId)', names: 'Juan Carlos', paternal_surname: 'Perez', maternal_surname: 'Rojas', username: '#(username)', password: '#(validPassword())' }
    * def body = karate.merge(base, overrides)
    * def pw = body.password
    Given url baseUrl
    And path 'users'
    And request body
    When method post
```

### `qa/karate/features/onboarding-session.feature`

```gherkin
@CA-01
Feature: CA-01 - Sesión de onboarding y registro de pasos completados

  Background:
    * url baseUrl

  @positive @KAR-S01
  Scenario: KAR-S01 Iniciar sesión devuelve 201 con el esquema esperado
    Given path 'onboarding', 'sessions'
    When method post
    Then status 201
    And match header Content-Type contains 'application/json'
    And match response ==
    """
    {
      session_id: '#uuid',
      status: 'OPEN',
      started_at: '#regex .+-05:00$',
      completed_steps: '#[0]'
    }
    """

  @boundary @local-clock @KAR-S02
  Scenario: KAR-S02 started_at es cercano a la hora real (solo si cliente y servidor comparten reloj)
    * def System = Java.type('java.lang.System')
    * def OffsetDateTime = Java.type('java.time.OffsetDateTime')
    Given path 'onboarding', 'sessions'
    When method post
    Then status 201
    * def nowMs = System.currentTimeMillis()
    * def startedMs = OffsetDateTime.parse(response.started_at).toInstant().toEpochMilli()
    * assert Math.abs(nowMs - startedMs) < 60000

  @positive @KAR-S03
  Scenario: KAR-S03 Cada sesión tiene identificador distinto
    * def a = call read('helpers/start-session.feature')
    * def b = call read('helpers/start-session.feature')
    * assert a.sessionId != b.sessionId

  @positive @KAR-S04
  Scenario Outline: KAR-S04 Registrar el paso <step> lo agrega a completed_steps
    * def sess = call read('helpers/start-session.feature')
    Given path 'onboarding', 'sessions', sess.sessionId, 'steps'
    And request { step: '<step>' }
    When method post
    Then status 200
    And match response.status == 'OPEN'
    And match response.session_id == sess.sessionId
    And match response.completed_steps == ['<step>']

    Examples:
      | step             |
      | NAMES            |
      | PATERNAL_SURNAME |
      | MATERNAL_SURNAME |
      | USERNAME         |
      | PASSWORD         |

  @boundary @KAR-S05
  Scenario: KAR-S05 Conserva el orden de finalización y no duplica pasos
    * def sess = call read('helpers/start-session.feature')
    Given path 'onboarding', 'sessions', sess.sessionId, 'steps'
    And request { step: 'USERNAME' }
    When method post
    Then status 200
    Given path 'onboarding', 'sessions', sess.sessionId, 'steps'
    And request { step: 'NAMES' }
    When method post
    Then status 200
    Given path 'onboarding', 'sessions', sess.sessionId, 'steps'
    And request { step: 'NAMES' }
    When method post
    Then status 200
    And match response.completed_steps == ['USERNAME', 'NAMES']

  @positive @KAR-S06
  Scenario: KAR-S06 Se registran los cinco pasos del formulario
    * def sess = call read('helpers/start-session.feature')
    * def steps = ['NAMES', 'PATERNAL_SURNAME', 'MATERNAL_SURNAME', 'USERNAME', 'PASSWORD']
    * def last = null
    * def send =
    """
    function(step) {
      var res = karate.call('helpers/post-step.feature', { sessionId: sess.sessionId, step: step });
      return res.response;
    }
    """
    * def results = karate.map(steps, send)
    * match karate.sizeOf(results) == 5
    * match results[4].completed_steps == steps

  @negative @KAR-S07
  Scenario: KAR-S07 Paso inválido devuelve 400 sin eco del valor
    * def sess = call read('helpers/start-session.feature')
    Given path 'onboarding', 'sessions', sess.sessionId, 'steps'
    And request { step: 'PASO_XYZ' }
    When method post
    Then status 400
    And match response contains { code: 'VALIDATION_ERROR', message: '#string', trace_id: '#string' }
    And match response.details[0].field == 'step'
    And assert karate.pretty(response).indexOf('PASO_XYZ') == -1

  @negative @KAR-S08
  Scenario: KAR-S08 Paso ausente devuelve 400 REQUIRED
    * def sess = call read('helpers/start-session.feature')
    Given path 'onboarding', 'sessions', sess.sessionId, 'steps'
    And request {}
    When method post
    Then status 400
    And match response.code == 'VALIDATION_ERROR'
    And match response.details[0] == { field: 'step', issue: 'REQUIRED' }

  @boundary @negative @KAR-S09
  Scenario: KAR-S09 Paso en minúsculas se rechaza
    * def sess = call read('helpers/start-session.feature')
    Given path 'onboarding', 'sessions', sess.sessionId, 'steps'
    And request { step: 'names' }
    When method post
    Then status 400
    And match response.code == 'VALIDATION_ERROR'

  @negative @KAR-S10
  Scenario: KAR-S10 Un paso inválido no altera el estado de la sesión
    * def sess = call read('helpers/start-session.feature')
    Given path 'onboarding', 'sessions', sess.sessionId, 'steps'
    And request { step: 'PASO_XYZ' }
    When method post
    Then status 400
    Given path 'onboarding', 'sessions', sess.sessionId, 'steps'
    And request { step: 'NAMES' }
    When method post
    Then status 200
    And match response.completed_steps == ['NAMES']

  @negative @privacy @KAR-S11
  Scenario: KAR-S11 Solo se registran nombres de paso, no valores ingresados
    * def sess = call read('helpers/start-session.feature')
    Given path 'onboarding', 'sessions', sess.sessionId, 'steps'
    And request { step: 'NAMES', value: 'Juan' }
    When method post
    Then status 200
    And match response.completed_steps == ['NAMES']
    And assert karate.pretty(response).indexOf('Juan') == -1

  @negative @KAR-S12
  Scenario: KAR-S12 Sesión inexistente devuelve 404
    Given path 'onboarding', 'sessions', unknownUuid, 'steps'
    And request { step: 'NAMES' }
    When method post
    Then status 404
    And match response == { code: 'NOT_FOUND', message: '#string', trace_id: '#string' }

  @boundary @negative @KAR-S13
  Scenario: KAR-S13 Identificador de sesión mal formado devuelve 404
    Given path 'onboarding', 'sessions', 'no-es-uuid', 'steps'
    And request { step: 'NAMES' }
    When method post
    Then status 404
    And match response.code == 'NOT_FOUND'

  @wallet @negative @KAR-S14
  Scenario: KAR-S14 No se pueden registrar pasos en una sesión ya completada
    * def sess = call read('helpers/start-session.feature')
    * def reg = call read('helpers/register-user.feature') { sessionId: '#(sess.sessionId)' }
    * match reg.responseStatus == 201
    Given path 'onboarding', 'sessions', sess.sessionId, 'steps'
    And request { step: 'NAMES' }
    When method post
    Then status 409
    And match response.code == 'SESSION_ALREADY_COMPLETED'
```

KAR-S06 usa un helper adicional que debe existir para que el escenario funcione:

### `qa/karate/features/helpers/post-step.feature`

```gherkin
@ignore
Feature: Helper - registrar un paso

  # Argumentos: sessionId, step
  Scenario: Registra paso
    Given url baseUrl
    And path 'onboarding', 'sessions', sessionId, 'steps'
    And request { step: '#(step)' }
    When method post
    Then status 200
```

### `qa/karate/features/username-validation.feature`

```gherkin
@CA-01 @CA-01.d
Feature: CA-01.d - Contrato que soporta la validación de campos mientras el usuario escribe

  Background:
    * url baseUrl

  @positive @KAR-U01
  Scenario: KAR-U01 Usuario disponible
    * def u = uniqueUsername()
    Given path 'usernames', 'availability-checks'
    And request { username: '#(u)' }
    When method post
    Then status 200
    And match response == { username: '#(u)', available: true, suggestions: '#[0]' }

  @boundary @positive @KAR-U02a
  Scenario Outline: KAR-U02a Usuario válido en el límite: <username>
    Given path 'usernames', 'availability-checks'
    And request { username: '<username>' }
    When method post
    Then status 200
    And match response.username == '<username>'
    And match response.available == true

    Examples:
      | username             |
      | a                    |
      | abcdefghij0123456789 |
      | a_b.c-1              |

  @negative @boundary @KAR-U02b
  Scenario Outline: KAR-U02b Usuario inválido: <username> -> <issue>
    Given path 'usernames', 'availability-checks'
    And request { username: '<username>' }
    When method post
    Then status 400
    And match response.code == 'VALIDATION_ERROR'
    And match response.details[0] == { field: 'username', issue: '<issue>' }
    And assert karate.pretty(response).indexOf('<username>') == -1

    Examples:
      | username              | issue            |
      | con espacio           | INVALID_USERNAME |
      | 1234                  | INVALID_USERNAME |
      | abcdefghij01234567890 | TOO_LONG         |

  @negative @boundary @KAR-U02c
  Scenario: KAR-U02c Usuario vacío
    Given path 'usernames', 'availability-checks'
    And request { username: '' }
    When method post
    Then status 400
    And match response.details[0] == { field: 'username', issue: 'TOO_SHORT' }

  @negative @KAR-U03
  Scenario: KAR-U03 Usuario ausente
    Given path 'usernames', 'availability-checks'
    And request { names: 'Juan' }
    When method post
    Then status 400
    And match response.details[0] == { field: 'username', issue: 'REQUIRED' }

  @negative @boundary @KAR-U04
  Scenario Outline: KAR-U04 Nombres inválidos -> <issue>
    * def u = uniqueUsername()
    Given path 'usernames', 'availability-checks'
    And request { username: '#(u)', names: '<names>' }
    When method post
    Then status 400
    And match response.details[0] == { field: 'names', issue: '<issue>' }

    Examples:
      | names                           | issue              |
      | Juan1                           | INVALID_CHARACTERS |
      | Abcdefghijklmnopqrstuvwxyzabcde | TOO_LONG           |

  @negative @boundary @KAR-U05
  Scenario Outline: KAR-U05 Apellido paterno inválido -> <issue>
    * def u = uniqueUsername()
    Given path 'usernames', 'availability-checks'
    And request { username: '#(u)', paternal_surname: '<surname>' }
    When method post
    Then status 400
    And match response.details[0] == { field: 'paternal_surname', issue: '<issue>' }

    Examples:
      | surname                | issue              |
      | Pe rez                 | INVALID_CHARACTERS |
      | Abcdefghijklmnopqrstu  | TOO_LONG           |

  @positive @boundary @KAR-U06
  Scenario: KAR-U06 Nombres con tilde y espacio, y apellidos en el límite
    * def u = uniqueUsername()
    Given path 'usernames', 'availability-checks'
    And request { username: '#(u)', names: 'José María', paternal_surname: 'Abcdefghijklmnopqrst', maternal_surname: 'Rojas' }
    When method post
    Then status 200
    And match response.available == true

  @wallet @positive @KAR-U07
  Scenario: KAR-U07 Usuario no disponible (sin distinguir mayúsculas) devuelve sugerencias sin símbolos
    * def sess = call read('helpers/start-session.feature')
    * def taken = uniqueUsername()
    * def reg = call read('helpers/register-user.feature') { sessionId: '#(sess.sessionId)', username: '#(taken)' }
    * match reg.responseStatus == 201
    * def requested = taken.toUpperCase()
    Given path 'usernames', 'availability-checks'
    And request { username: '#(requested)', names: 'Juan Carlos', paternal_surname: 'Perez', maternal_surname: 'Rojas' }
    When method post
    Then status 200
    And match response.available == false
    And assert karate.sizeOf(response.suggestions) >= 1 && karate.sizeOf(response.suggestions) <= 5
    And match each response.suggestions == '#regex [A-Za-z0-9]{1,20}'
    And assert distinctCount(response.suggestions) == karate.sizeOf(response.suggestions)
    * def same = karate.filter(response.suggestions, function(s){ return s.toLowerCase() == taken.toLowerCase() })
    * assert karate.sizeOf(same) == 0
```

### `qa/karate/features/registration-metrics.feature`

```gherkin
@CA-01 @CA-01.b
Feature: CA-01.b/c - Registro del tiempo y de los pasos completados al finalizar el registro

  Background:
    * url baseUrl
    * def System = Java.type('java.lang.System')
    * def OffsetDateTime = Java.type('java.time.OffsetDateTime')
    * def epochMs = function(s) { return OffsetDateTime.parse(s).toInstant().toEpochMilli(); }

  @wallet @positive @KAR-M01
  Scenario: KAR-M01 El registro devuelve métricas coherentes con la sesión y los pasos
    * def t0 = System.currentTimeMillis()
    * def sess = call read('helpers/start-session.feature')
    * def sid = sess.sessionId
    Given path 'onboarding', 'sessions', sid, 'steps'
    And request { step: 'NAMES' }
    When method post
    Then status 200
    Given path 'onboarding', 'sessions', sid, 'steps'
    And request { step: 'USERNAME' }
    When method post
    Then status 200
    * def reg = call read('helpers/register-user.feature') { sessionId: '#(sid)' }
    * def t1 = System.currentTimeMillis()
    * match reg.responseStatus == 201
    * def m = reg.response.registration_metrics
    * match m ==
    """
    {
      session_id: '#(sid)',
      started_at: '#string',
      completed_at: '#string',
      duration_ms: '#number? _ >= 0',
      completed_steps: ['NAMES', 'USERNAME']
    }
    """
    * match m.started_at == sess.startedAt
    * def startedMs = epochMs(m.started_at)
    * def completedMs = epochMs(m.completed_at)
    * assert completedMs >= startedMs
    * assert Math.abs((completedMs - startedMs) - m.duration_ms) <= 2
    * assert m.duration_ms <= (t1 - t0) + 100
    * assert karate.pretty(reg.response).indexOf(reg.pw) == -1

  @wallet @boundary @KAR-M02
  Scenario: KAR-M02 Registro sin pasos previos devuelve completed_steps vacío
    * def sess = call read('helpers/start-session.feature')
    * def reg = call read('helpers/register-user.feature') { sessionId: '#(sess.sessionId)' }
    * match reg.responseStatus == 201
    * match reg.response.registration_metrics.completed_steps == []
    * match reg.response.registration_metrics.duration_ms == '#number? _ >= 0'

  @wallet @negative @KAR-M03
  Scenario: KAR-M03 No se puede registrar dos veces con la misma sesión
    * def sess = call read('helpers/start-session.feature')
    * def first = call read('helpers/register-user.feature') { sessionId: '#(sess.sessionId)' }
    * match first.responseStatus == 201
    * def second = call read('helpers/register-user.feature') { sessionId: '#(sess.sessionId)' }
    * match second.responseStatus == 409
    * match second.response.code == 'SESSION_ALREADY_COMPLETED'

  @negative @KAR-M04
  Scenario: KAR-M04 Un registro rechazado por contraseña débil no cierra la sesión ni llama al Wallet
    * def sess = call read('helpers/start-session.feature')
    * def weak = weakPassword()
    * def reg = call read('helpers/register-user.feature') { sessionId: '#(sess.sessionId)', overrides: { password: '#(weak)' } }
    * match reg.responseStatus == 400
    * match reg.response.code == 'VALIDATION_ERROR'
    * match reg.response.details[0] == { field: 'password', issue: 'PASSWORD_WEAK' }
    * assert karate.pretty(reg.response).indexOf(weak) == -1
    Given path 'onboarding', 'sessions', sess.sessionId, 'steps'
    And request { step: 'NAMES' }
    When method post
    Then status 200
    And match response.status == 'OPEN'

  @negative @boundary @KAR-M05
  Scenario: KAR-M05 Contraseña demasiado corta
    * def sess = call read('helpers/start-session.feature')
    * def shortPw = shortPassword()
    * def reg = call read('helpers/register-user.feature') { sessionId: '#(sess.sessionId)', overrides: { password: '#(shortPw)' } }
    * match reg.responseStatus == 400
    * match reg.response.details[0].field == 'password'
    * match reg.response.details[0].issue == 'TOO_SHORT'
    * assert karate.pretty(reg.response).indexOf(shortPw) == -1

  @negative @KAR-M06
  Scenario: KAR-M06 Registro con sesión inexistente devuelve 404
    * def reg = call read('helpers/register-user.feature') { sessionId: '#(unknownUuid)' }
    * match reg.responseStatus == 404
    * match reg.response.code == 'NOT_FOUND'

  @negative @KAR-M07
  Scenario: KAR-M07 Cuerpo vacío devuelve 400 con campos REQUIRED
    Given path 'users'
    And request {}
    When method post
    Then status 400
    And match response.code == 'VALIDATION_ERROR'
    And match each response.details contains { issue: 'REQUIRED' }

  @negative @KAR-M08
  Scenario: KAR-M08 session_id con formato inválido en el cuerpo
    * def reg = call read('helpers/register-user.feature') { sessionId: 'no-es-uuid' }
    * match reg.responseStatus == 400
    * match reg.response.details[0] == { field: 'session_id', issue: 'INVALID_UUID' }
```

---

## 3. Selenium (Python + pytest)

### `qa/selenium/requirements-e2e.txt`

```text
selenium>=4.10,<5
```

### `qa/selenium/locators.json`

Todos los valores están pendientes de completar con selectores CSS reales (P-01). Con `null` las pruebas correspondientes se saltan con mensaje PENDIENTE.

```json
{
  "_comment": "PENDIENTE P-01: completar con selectores CSS reales del frontend Angular (no se conocen: solo se recibió la lista de archivos). null = prueba omitida.",
  "onboarding_screen_marker": null,
  "names_input": null,
  "names_feedback": null,
  "paternal_surname_input": null,
  "paternal_surname_feedback": null,
  "maternal_surname_input": null,
  "maternal_surname_feedback": null,
  "username_input": null,
  "username_feedback": null
}
```

### `qa/selenium/conftest.py`

```python
"""Fixtures Selenium para CA-01. Sin valores por defecto inventados: lo desconocido se marca PENDIENTE."""
from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Callable, Dict, List, Optional

import pytest
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

LOCATORS_FILE = Path(__file__).parent / "locators.json"


def _require_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        pytest.skip(f"PENDIENTE: variable de entorno {name} no definida")
    return value


class NetLog:
    """Acumula las peticiones de red observadas por Chrome (log 'performance')."""

    def __init__(self, driver: webdriver.Chrome) -> None:
        self._driver = driver
        self.requests: List[Dict[str, Optional[str]]] = []

    def poll(self) -> List[Dict[str, Optional[str]]]:
        for entry in self._driver.get_log("performance"):
            try:
                message = json.loads(entry["message"])["message"]
            except (ValueError, KeyError):
                continue
            if message.get("method") != "Network.requestWillBeSent":
                continue
            request = message.get("params", {}).get("request", {})
            self.requests.append(
                {
                    "method": request.get("method"),
                    "url": request.get("url"),
                    "post_data": request.get("postData"),
                }
            )
        return self.requests

    def find(self, method: str, url_suffix: str) -> List[Dict[str, Optional[str]]]:
        self.poll()
        return [
            r
            for r in self.requests
            if r["method"] == method and (r["url"] or "").split("?")[0].endswith(url_suffix)
        ]

    def wait_for(
        self,
        method: str,
        url_suffix: str,
        timeout: float = 5.0,
        predicate: Optional[Callable[[Dict[str, Optional[str]]], bool]] = None,
    ) -> List[Dict[str, Optional[str]]]:
        deadline = time.time() + timeout
        while True:
            found = self.find(method, url_suffix)
            if predicate is not None:
                found = [r for r in found if predicate(r)]
            if found or time.time() >= deadline:
                return found
            time.sleep(0.2)


@pytest.fixture(scope="session")
def frontend_url() -> str:
    return _require_env("FRONTEND_URL").rstrip("/")


@pytest.fixture(scope="session")
def onboarding_path() -> str:
    return os.getenv("ONBOARDING_PATH", "").strip()


@pytest.fixture(scope="session")
def _locators() -> Dict[str, Optional[str]]:
    data = json.loads(LOCATORS_FILE.read_text(encoding="utf-8"))
    return {k: v for k, v in data.items() if not k.startswith("_")}


@pytest.fixture
def loc(_locators):
    def _get(name: str) -> str:
        value = _locators.get(name)
        if not value:
            pytest.skip(f"PENDIENTE: selector '{name}' no definido en qa/selenium/locators.json")
        return value

    return _get


@pytest.fixture
def driver():
    options = Options()
    if os.getenv("E2E_HEADLESS", "true").strip().lower() in {"1", "true", "yes", "on"}:
        options.add_argument("--headless=new")
    options.add_argument("--window-size=1280,900")
    options.set_capability("goog:loggingPrefs", {"performance": "ALL"})
    drv = webdriver.Chrome(options=options)
    try:
        drv.get_log("performance")  # descarta el buffer inicial
        yield drv
    finally:
        drv.quit()


@pytest.fixture
def net(driver) -> NetLog:
    return NetLog(driver)
```

### `qa/selenium/test_ca01_onboarding_ui.py`

```python
"""CA-01 - Pruebas de interfaz e integración UI->API para el onboarding.

Resultados esperados (no observados). Los selectores están pendientes en locators.json.
Las aserciones de feedback son estructurales (presencia/cambio), no de texto (P-05).
"""
from __future__ import annotations

import json
import secrets

import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

WAIT_S = 10


def _open_onboarding(driver, frontend_url, onboarding_path, loc) -> None:
    marker = loc("onboarding_screen_marker")
    driver.get(frontend_url + onboarding_path)
    WebDriverWait(driver, WAIT_S).until(EC.visibility_of_element_located((By.CSS_SELECTOR, marker)))


def _type(driver, selector: str, value: str) -> None:
    element = WebDriverWait(driver, WAIT_S).until(EC.visibility_of_element_located((By.CSS_SELECTOR, selector)))
    element.clear()
    element.send_keys(value)  # sin enviar el formulario y sin quitar el foco


def _feedback(driver, selector: str) -> str:
    elements = driver.find_elements(By.CSS_SELECTOR, selector)
    return " ".join(e.text.strip() for e in elements if e.is_displayed()).strip()


def _until_feedback(driver, selector: str, predicate, timeout: float = 5.0) -> str:
    WebDriverWait(driver, timeout).until(lambda d: predicate(_feedback(d, selector)))
    return _feedback(driver, selector)


# ---------------------------------------------------------------------------
# UI-01 (CA-01.a)
# ---------------------------------------------------------------------------
def test_ui01_session_created_when_onboarding_visible(driver, net, frontend_url, onboarding_path, loc):
    _open_onboarding(driver, frontend_url, onboarding_path, loc)
    created = net.wait_for("POST", "/onboarding/sessions", timeout=5)
    assert len(created) == 1, f"Se esperaba 1 POST /onboarding/sessions, se observaron {len(created)}"


# ---------------------------------------------------------------------------
# UI-02 (CA-01.d) validación en vivo
# ---------------------------------------------------------------------------
LIVE_CASES = [
    pytest.param("names", "Juan1", "Juan Carlos", id="names"),
    pytest.param("paternal_surname", "Pe rez", "Perez", id="paternal_surname"),
    pytest.param("maternal_surname", "Rojas9", "Rojas", id="maternal_surname"),
    pytest.param("username", "con espacio", "qa_" + secrets.token_hex(4), id="username"),
]


@pytest.mark.parametrize("field,invalid,valid", LIVE_CASES)
def test_ui02_live_validation_feedback(driver, frontend_url, onboarding_path, loc, field, invalid, valid):
    input_sel = loc(f"{field}_input")
    feedback_sel = loc(f"{field}_feedback")
    _open_onboarding(driver, frontend_url, onboarding_path, loc)

    _type(driver, input_sel, invalid)
    invalid_feedback = _until_feedback(driver, feedback_sel, lambda text: text != "")
    assert invalid_feedback != "", "No se mostró feedback para un valor inválido mientras se escribe"

    _type(driver, input_sel, valid)
    valid_feedback = _until_feedback(driver, feedback_sel, lambda text: text != invalid_feedback)
    assert valid_feedback != invalid_feedback, "El feedback no cambió al ingresar un valor válido"


# ---------------------------------------------------------------------------
# UI-03 (CA-01.d) límites de longitud
# ---------------------------------------------------------------------------
LENGTH_CASES = [
    pytest.param("names", 30, id="names-30"),
    pytest.param("paternal_surname", 20, id="paternal_surname-20"),
    pytest.param("username", 20, id="username-20"),
]


@pytest.mark.parametrize("field,maximum", LENGTH_CASES)
def test_ui03_length_limit_truncates_or_reports(driver, frontend_url, onboarding_path, loc, field, maximum):
    input_sel = loc(f"{field}_input")
    feedback_sel = loc(f"{field}_feedback")
    _open_onboarding(driver, frontend_url, onboarding_path, loc)

    _type(driver, input_sel, "a" * (maximum + 1))
    element = driver.find_element(By.CSS_SELECTOR, input_sel)

    def limited_or_reported(d) -> bool:
        value = d.find_element(By.CSS_SELECTOR, input_sel).get_attribute("value") or ""
        return len(value) <= maximum or _feedback(d, feedback_sel) != ""

    WebDriverWait(driver, 5).until(limited_or_reported)
    value = element.get_attribute("value") or ""
    assert len(value) <= maximum or _feedback(driver, feedback_sel) != ""


# ---------------------------------------------------------------------------
# UI-04 (CA-01.c) integración UI -> API: pasos completados
# ---------------------------------------------------------------------------
def test_ui04_step_sent_without_typed_values(driver, net, frontend_url, onboarding_path, loc):
    input_sel = loc("names_input")
    _open_onboarding(driver, frontend_url, onboarding_path, loc)
    typed = "Juan Carlos"
    _type(driver, input_sel, typed)
    driver.find_element(By.CSS_SELECTOR, input_sel).send_keys(Keys.TAB)  # sale del campo

    sent = net.wait_for("POST", "/steps", timeout=5)
    if not sent:
        pytest.fail("No se observó ningún POST .../steps tras completar el campo de nombres "
                    "(si la UI envía el paso en otro evento, ver P-01)")
    if any(r["post_data"] is None for r in sent):
        pytest.skip("INCONCLUSO: Chrome no expuso postData en el log de red")

    bodies = [json.loads(r["post_data"]) for r in sent]
    assert any(body.get("step") == "NAMES" for body in bodies)
    for request, body in zip(sent, bodies):
        assert set(body.keys()) == {"step"}, f"El cuerpo del paso contiene claves extra: {sorted(body.keys())}"
        assert typed not in request["post_data"]


# ---------------------------------------------------------------------------
# UI-05 (CA-01.d) integración UI -> API: disponibilidad de usuario
# ---------------------------------------------------------------------------
def test_ui05_username_availability_call_and_feedback(driver, net, frontend_url, onboarding_path, loc):
    input_sel = loc("username_input")
    feedback_sel = loc("username_feedback")
    _open_onboarding(driver, frontend_url, onboarding_path, loc)
    username = "qa" + secrets.token_hex(4)
    _type(driver, input_sel, username)

    sent = net.wait_for("POST", "/usernames/availability-checks", timeout=5)
    assert sent, "No se observó POST /usernames/availability-checks al escribir el usuario"
    if any(r["post_data"] is None for r in sent):
        pytest.skip("INCONCLUSO: Chrome no expuso postData en el log de red")
    assert any(json.loads(r["post_data"]).get("username") == username for r in sent)
    assert _until_feedback(driver, feedback_sel, lambda text: text != "") != ""
```

---

## 4. Notas finales

- Faltan por completar P-01 (selectores del frontend), P-02 (contrato del Wallet mock) y P-04 (versión de Karate). Sin ellos, los escenarios `@wallet` y toda la suite Selenium no son ejecutables.
- Estado de cada prueba: **NO EJECUTADO**. No se declara ninguna prueba como aprobada ni ninguna corrección como verificada.
- INT-01 (formulario completo desde la UI) queda pendiente por no conocer el frontend.
- Las rutas, esquemas y códigos HTTP de los escenarios Karate salen de la lectura del código del backend (`routers/`, `schemas/`, `errors.py`). No hay un OpenAPI formal entregado contra el cual compararlos.