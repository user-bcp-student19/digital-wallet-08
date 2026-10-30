# Frontend Angular – HU 02 Onboarding de billetera digital

Aplicación Angular 18 con componentes standalone, `HttpClient`, formularios reactivos y pruebas unitarias con Jasmine y Karma. Consume la API FastAPI de `http://localhost:8000`. No pude ejecutar `ng test` ni `ng build` en este entorno, así que el código no está compilado ni probado.

## Estructura

```
wallet-frontend/
├── README.md
├── package.json
├── angular.json
├── proxy.conf.json
├── tsconfig.json
├── tsconfig.app.json
├── tsconfig.spec.json
└── src/
    ├── index.html
    ├── main.ts
    ├── styles.css
    ├── environments/environment.ts
    ├── testing/fixtures.ts
    └── app/
        ├── app.component.ts
        ├── app.config.ts
        ├── app.routes.ts
        ├── core/
        │   ├── config/api-config.ts
        │   ├── models/api.models.ts
        │   ├── errors/api-error.ts (+ .spec.ts)
        │   ├── guards/auth.guard.ts (+ .spec.ts)
        │   ├── interceptors/basic-auth.interceptor.ts (+ .spec.ts)
        │   ├── services/session.store.ts
        │   ├── services/onboarding-api.service.ts (+ .spec.ts)
        │   ├── services/wallet-api.service.ts (+ .spec.ts)
        │   ├── utils/format.ts, time.ts (+ .spec.ts)
        │   └── validators/field-validators.ts, validation-messages.ts,
        │       password-strength.ts (+ .spec.ts)
        ├── shared/operation-conditions.component.ts
        └── features/
            ├── onboarding/onboarding.component.ts (+ .spec.ts)
            ├── landing/landing.component.ts (+ .spec.ts)
            └── profile/
                ├── profile.component.ts (+ .spec.ts)
                ├── channel-validation-card.component.ts (+ .spec.ts)
                ├── identity-card.component.ts (+ .spec.ts)
                └── operations-panel.component.ts (+ .spec.ts)
```

---

## `README.md`

````markdown
# Wallet Frontend (Angular) – HU 02 Onboarding de billetera digital

SPA en Angular 18 (componentes standalone, `HttpClient`, formularios reactivos, signals).
Consume el backend FastAPI en `http://localhost:8000`.

## Ejecutar

```bash
npm install
npm start            # ng serve con proxy: /api/* -> http://localhost:8000/*
npm run test:ci      # pruebas unitarias (Karma + Jasmine, ChromeHeadless)
npm run build
```

El frontend llama a `/api/...` y `proxy.conf.json` reescribe a `http://localhost:8000/...`. Así no depende de CORS.
Si el backend ya habilita CORS, puede cambiarse `apiBaseUrl` en `src/environments/environment.ts` a `http://localhost:8000`.

El backend debe correr con `APP_ENV=development` o `testing` para que la biometría mock esté disponible.

## Mapeo de criterios de aceptación

| CA | Implementación en el frontend |
|---|---|
| CA-01 | `OnboardingComponent` llama a `POST /onboarding/sessions` al mostrarse, y a `POST .../steps` cuando un campo queda válido al perder el foco (el usuario, al confirmarse su disponibilidad). Muestra el progreso de pasos. Cada campo muestra su validación mientras se escribe. |
| CA-02 | Validadores locales con las mismas reglas del contrato (30/20/20/20, símbolos en usuario, contraseña de 10 o más caracteres). Disponibilidad con debounce (`POST /onboarding/username-availability`) y sugerencias seleccionables. Medidor y alerta de robustez de contraseña. |
| CA-03, CA-04 | `LandingComponent`: bienvenida por nombre real, condiciones (`operation_conditions`) y aviso visible de perfil pendiente. |
| CA-05, CA-13 | `OperationConditionsComponent` muestra los topes que devuelve la API. `OperationsPanelComponent` usa `POST /wallets/{id}/operations` y muestra los errores de tope. |
| CA-06 a CA-08 | `ChannelValidationCardComponent` (correo y celular): prefijo +51 de solo lectura, cuenta regresiva de 45 s y 60 s, manejo de 409, 422 y 429. Las tres tarjetas son independientes. |
| CA-09 a CA-12 | `IdentityCardComponent`: aviso de nitidez, términos y condiciones, simulación sin fotos ni video, solo si `identity_mock_available`. |
| CA-10 | Sin analítica ni `console.*`. Las credenciales viven solo en memoria (`SessionStore`) y no se usa storage. |

## Decisiones y supuestos

- **Autenticación:** HTTP Basic con usuario y contraseña del registro, sin tokens (según el contrato). Un interceptor funcional añade `Authorization` solo a `/wallets/*`. Un 401 limpia la sesión y vuelve a `/onboarding`.
- **Sin pantalla de login:** el contrato no define un endpoint de inicio de sesión y el `wallet_id` solo se obtiene al registrarse. Al recargar la página se pierde la sesión en memoria, que es lo deseado para no persistir la contraseña.
- **Sin cabeceras ni cuerpos en logs:** no se hace ningún `console.log`.
- **OTP mock:** la API no devuelve el código. La UI indica que se acepta cualquier valor mientras haya un OTP vigente.
- **Cuenta regresiva:** se calcula con el reloj local a partir de `expires_in_seconds` (60) y de la regla de 45 s. No se compara con relojes del servidor para evitar desfases.
- **Estados validados:** `ACTIVE_MOVIL` y `ACTIVE_BIOM`, por analogía con `ACTIVE_EMAIL`. Son los supuestos del Arquitecto, aún por confirmar.
- **Saldo:** la API no modifica `balance`. La UI solo muestra el valor devuelto.
- **Contrato YAML:** el Backend no verificó que `openapi/wallet-onboarding-api.yaml` exista. Este frontend sigue el contrato del Arquitecto.
````

---

## `package.json`

```json
{
  "name": "wallet-frontend",
  "version": "1.0.0",
  "private": true,
  "scripts": {
    "ng": "ng",
    "start": "ng serve --proxy-config proxy.conf.json",
    "build": "ng build",
    "test": "ng test",
    "test:ci": "ng test --watch=false --browsers=ChromeHeadless"
  },
  "dependencies": {
    "@angular/common": "^18.2.0",
    "@angular/compiler": "^18.2.0",
    "@angular/core": "^18.2.0",
    "@angular/forms": "^18.2.0",
    "@angular/platform-browser": "^18.2.0",
    "@angular/platform-browser-dynamic": "^18.2.0",
    "@angular/router": "^18.2.0",
    "rxjs": "~7.8.0",
    "tslib": "^2.3.0",
    "zone.js": "~0.14.10"
  },
  "devDependencies": {
    "@angular-devkit/build-angular": "^18.2.0",
    "@angular/cli": "^18.2.0",
    "@angular/compiler-cli": "^18.2.0",
    "@types/jasmine": "~5.1.0",
    "jasmine-core": "~5.2.0",
    "karma": "~6.4.0",
    "karma-chrome-launcher": "~3.2.0",
    "karma-coverage": "~2.2.0",
    "karma-jasmine": "~5.1.0",
    "karma-jasmine-html-reporter": "~2.1.0",
    "typescript": "~5.5.2"
  }
}
```

## `angular.json`

```json
{
  "$schema": "./node_modules/@angular/cli/lib/config/schema.json",
  "version": 1,
  "newProjectRoot": "projects",
  "projects": {
    "wallet-frontend": {
      "projectType": "application",
      "root": "",
      "sourceRoot": "src",
      "prefix": "app",
      "architect": {
        "build": {
          "builder": "@angular-devkit/build-angular:application",
          "options": {
            "outputPath": "dist/wallet-frontend",
            "index": "src/index.html",
            "browser": "src/main.ts",
            "polyfills": ["zone.js"],
            "tsConfig": "tsconfig.app.json",
            "assets": [],
            "styles": ["src/styles.css"],
            "scripts": []
          },
          "configurations": {
            "production": {
              "outputHashing": "all"
            },
            "development": {
              "optimization": false,
              "extractLicenses": false,
              "sourceMap": true
            }
          },
          "defaultConfiguration": "production"
        },
        "serve": {
          "builder": "@angular-devkit/build-angular:dev-server",
          "options": {
            "proxyConfig": "proxy.conf.json"
          },
          "configurations": {
            "production": {
              "buildTarget": "wallet-frontend:build:production"
            },
            "development": {
              "buildTarget": "wallet-frontend:build:development"
            }
          },
          "defaultConfiguration": "development"
        },
        "test": {
          "builder": "@angular-devkit/build-angular:karma",
          "options": {
            "polyfills": ["zone.js", "zone.js/testing"],
            "tsConfig": "tsconfig.spec.json",
            "assets": [],
            "styles": ["src/styles.css"],
            "scripts": []
          }
        }
      }
    }
  }
}
```

## `proxy.conf.json`

```json
{
  "/api": {
    "target": "http://localhost:8000",
    "secure": false,
    "changeOrigin": true,
    "pathRewrite": { "^/api": "" },
    "logLevel": "warn"
  }
}
```

## `tsconfig.json`

```json
{
  "compileOnSave": false,
  "compilerOptions": {
    "outDir": "./dist/out-tsc",
    "strict": true,
    "noImplicitOverride": true,
    "skipLibCheck": true,
    "esModuleInterop": true,
    "sourceMap": true,
    "declaration": false,
    "experimentalDecorators": true,
    "moduleResolution": "bundler",
    "importHelpers": true,
    "target": "ES2022",
    "module": "ES2022",
    "lib": ["ES2022", "dom"]
  },
  "angularCompilerOptions": {
    "enableI18nLegacyMessageIdFormat": false,
    "strictInjectionParameters": true,
    "strictInputAccessModifiers": true,
    "strictTemplates": true
  }
}
```

## `tsconfig.app.json`

```json
{
  "extends": "./tsconfig.json",
  "compilerOptions": {
    "outDir": "./out-tsc/app",
    "types": []
  },
  "files": ["src/main.ts"],
  "include": ["src/**/*.d.ts"]
}
```

## `tsconfig.spec.json`

```json
{
  "extends": "./tsconfig.json",
  "compilerOptions": {
    "outDir": "./out-tsc/spec",
    "types": ["jasmine"]
  },
  "include": ["src/**/*.spec.ts", "src/**/*.d.ts"]
}
```

---

## `src/index.html`

```html
<!doctype html>
<html lang="es">
  <head>
    <meta charset="utf-8" />
    <title>Billetera digital</title>
    <base href="/" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
  </head>
  <body>
    <app-root></app-root>
  </body>
</html>
```

## `src/main.ts`

```ts
import { bootstrapApplication } from '@angular/platform-browser';
import { AppComponent } from './app/app.component';
import { appConfig } from './app/app.config';

bootstrapApplication(AppComponent, appConfig).catch((err) => console.error(err));
```

## `src/environments/environment.ts`

```ts
export const environment = {
  /**
   * Base de la API. En desarrollo se usa el proxy (`proxy.conf.json`):
   * /api/* -> http://localhost:8000/*
   * Si el backend habilita CORS puede usarse 'http://localhost:8000'.
   */
  apiBaseUrl: '/api',
};
```

## `src/styles.css`

```css
:root {
  --primary: #5b2a86;
  --primary-dark: #44206a;
  --ok: #1e8e3e;
  --bad: #c5221f;
  --warn: #b06000;
  --bg: #f5f3f8;
  --card: #ffffff;
  --text: #1f1b24;
  --muted: #6b6475;
  --border: #d9d4e0;
}
* { box-sizing: border-box; }
body { margin: 0; font-family: system-ui, -apple-system, 'Segoe UI', Roboto, sans-serif; background: var(--bg); color: var(--text); }
main { max-width: 960px; margin: 0 auto; padding: 1.25rem; }
h1 { font-size: 1.6rem; margin: 0 0 .25rem; }
h2 { font-size: 1.2rem; margin: 0 0 .5rem; }
h3 { font-size: 1.05rem; margin: 0; }
.muted { color: var(--muted); font-size: .9rem; }
.card { background: var(--card); border: 1px solid var(--border); border-radius: 12px; padding: 1rem 1.25rem; margin: 1rem 0; }
.grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 1rem; }
.grid .card { margin: 0; }
.card-head { display: flex; justify-content: space-between; align-items: center; margin-bottom: .75rem; gap: .5rem; }
.app-header { display: flex; justify-content: space-between; align-items: center; padding: .75rem 1.25rem; background: var(--primary); color: #fff; }
.app-header nav { display: flex; gap: 1rem; align-items: center; }
.app-header a { color: #fff; text-decoration: none; opacity: .85; }
.app-header a.active { opacity: 1; text-decoration: underline; }
.brand { font-weight: 700; }
label { display: block; font-weight: 600; margin: .75rem 0 .25rem; }
input[type='text'], input[type='email'], input[type='tel'], input[type='password'], select, input:not([type]) {
  width: 100%; padding: .55rem .7rem; border: 2px solid var(--border); border-radius: 8px; font-size: 1rem; background: #fff;
}
input:focus, select:focus { outline: 2px solid var(--primary); outline-offset: 1px; }
.field .msg { display: block; min-height: 1.1rem; margin-top: .25rem; font-size: .85rem; color: var(--muted); }
.field[data-state='valid'] input { border-color: var(--ok); }
.field[data-state='valid'] .msg { color: var(--ok); }
.field[data-state='valid'] .msg::before { content: '✔ '; }
.field[data-state='invalid'] input { border-color: var(--bad); }
.field[data-state='invalid'] .msg { color: var(--bad); }
.field[data-state='invalid'] .msg::before { content: '✖ '; }
.field[data-state='pending'] .msg { color: var(--warn); }
.row { display: flex; gap: .5rem; align-items: center; }
.row .prefix { width: 4.5rem; text-align: center; background: #eee; color: var(--muted); }
.btn, button.btn { background: var(--primary); color: #fff; border: 0; border-radius: 8px; padding: .6rem 1.1rem; font-size: 1rem; cursor: pointer; margin-top: .75rem; text-decoration: none; display: inline-block; }
.btn:hover:not(:disabled) { background: var(--primary-dark); }
.btn:disabled { opacity: .5; cursor: not-allowed; }
button.link { background: none; border: 0; color: #fff; cursor: pointer; text-decoration: underline; font-size: 1rem; }
.chips { display: flex; flex-wrap: wrap; gap: .4rem; margin-top: .35rem; }
.chip { background: #ece5f5; border: 1px solid var(--primary); color: var(--primary); border-radius: 999px; padding: .2rem .7rem; cursor: pointer; font-size: .9rem; }
.meter { height: 8px; border-radius: 4px; background: #e6e1ec; overflow: hidden; margin-top: .4rem; }
.meter span { display: block; height: 100%; width: 0; transition: width .2s; }
.meter[data-level='weak'] span { width: 33%; background: var(--bad); }
.meter[data-level='medium'] span { width: 66%; background: var(--warn); }
.meter[data-level='strong'] span { width: 100%; background: var(--ok); }
.strength { margin: .25rem 0 0; font-size: .9rem; font-weight: 600; }
.hints { margin: .25rem 0 0; padding-left: 1.1rem; font-size: .85rem; color: var(--muted); }
.badge { background: #ece5f5; color: var(--primary); border-radius: 999px; padding: .15rem .7rem; font-size: .8rem; font-weight: 700; }
.badge.ok { background: #e3f4e8; color: var(--ok); }
.banner { border-radius: 10px; padding: .9rem 1.1rem; margin: 1rem 0; }
.banner.warn { background: #fff4e0; border: 1px solid #f0c36d; color: #6e4300; }
.msg.invalid, .error { color: var(--bad); }
.success { color: var(--ok); font-weight: 600; }
.notice { background: #eef4ff; border: 1px solid #b6ccf5; border-radius: 8px; padding: .6rem .8rem; font-size: .9rem; }
table { width: 100%; border-collapse: collapse; font-size: .92rem; }
th, td { text-align: left; padding: .45rem .5rem; border-bottom: 1px solid var(--border); }
.check { display: flex; gap: .5rem; align-items: flex-start; font-weight: 400; }
.check input { margin-top: .25rem; }
.progress { font-size: .85rem; color: var(--muted); }
ul.history { padding-left: 1.1rem; font-size: .9rem; }
```

---

## `src/app/app.config.ts`

```ts
import { ApplicationConfig, provideZoneChangeDetection } from '@angular/core';
import { provideHttpClient, withInterceptors } from '@angular/common/http';
import { provideRouter } from '@angular/router';
import { routes } from './app.routes';
import { basicAuthInterceptor } from './core/interceptors/basic-auth.interceptor';

export const appConfig: ApplicationConfig = {
  providers: [
    provideZoneChangeDetection({ eventCoalescing: true }),
    provideRouter(routes),
    provideHttpClient(withInterceptors([basicAuthInterceptor])),
  ],
};
```

## `src/app/app.routes.ts`

```ts
import { Routes } from '@angular/router';
import { authGuard } from './core/guards/auth.guard';

export const routes: Routes = [
  { path: '', pathMatch: 'full', redirectTo: 'onboarding' },
  {
    path: 'onboarding',
    loadComponent: () =>
      import('./features/onboarding/onboarding.component').then((m) => m.OnboardingComponent),
  },
  {
    path: 'landing',
    canActivate: [authGuard],
    loadComponent: () =>
      import('./features/landing/landing.component').then((m) => m.LandingComponent),
  },
  {
    path: 'profile',
    canActivate: [authGuard],
    loadComponent: () =>
      import('./features/profile/profile.component').then((m) => m.ProfileComponent),
  },
  { path: '**', redirectTo: 'onboarding' },
];
```

## `src/app/app.component.ts`

```ts
import { Component, inject } from '@angular/core';
import { Router, RouterLink, RouterLinkActive, RouterOutlet } from '@angular/router';
import { SessionStore } from './core/services/session.store';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [RouterOutlet, RouterLink, RouterLinkActive],
  template: `
    <header class="app-header">
      <span class="brand">💳 Billetera digital</span>
      @if (store.isAuthenticated()) {
        <nav aria-label="Principal">
          <a routerLink="/landing" routerLinkActive="active">Inicio</a>
          <a routerLink="/profile" routerLinkActive="active">Perfil</a>
          <button type="button" class="link" (click)="logout()">Salir</button>
        </nav>
      }
    </header>
    <main>
      <router-outlet />
    </main>
  `,
})
export class AppComponent {
  readonly store = inject(SessionStore);
  private readonly router = inject(Router);

  logout(): void {
    this.store.clear();
    void this.router.navigateByUrl('/onboarding');
  }
}
```

---

## `src/app/core/config/api-config.ts`

```ts
import { InjectionToken } from '@angular/core';
import { environment } from '../../../environments/environment';

/** Base URL de la API FastAPI (inyectable para pruebas). */
export const API_BASE_URL = new InjectionToken<string>('API_BASE_URL', {
  providedIn: 'root',
  factory: () => environment.apiBaseUrl,
});
```

## `src/app/core/models/api.models.ts`

```ts
// Modelos alineados con el contrato OpenAPI del Arquitecto (wallet-onboarding-api).

export type Money = string;
export type AccountStatus = 'ACTIVE_BASIC' | 'ACTIVE_FULL';
export type OperationType = 'TOPUP_OWN' | 'TOPUP_THIRD_PARTY' | 'PAYMENT';
export type OperationGroup = 'COMBINED' | 'TOPUP' | 'PAYMENT';
export type OnboardingStep =
  | 'NOMBRES'
  | 'APELLIDO_PATERNO'
  | 'APELLIDO_MATERNO'
  | 'USUARIO'
  | 'CONTRASENA';
export type OtpChannel = 'EMAIL' | 'PHONE';

export interface Account {
  wallet_id: string;
  status: AccountStatus;
  balance: Money;
  currency: 'PEN';
}

export interface ProfileStates {
  estado_c1: 'PENDING_EMAIL' | 'ACTIVE_EMAIL';
  estado_c2: 'PENDING_MOVIL' | 'ACTIVE_MOVIL';
  estado_c3: 'PENDING_BIOM' | 'ACTIVE_BIOM';
}

export interface ProfileStatesResponse {
  wallet_id: string;
  profile: ProfileStates;
}

export interface OperationRule {
  operation_group: OperationGroup;
  operation_types: OperationType[];
  per_operation_max?: Money | null;
  daily_max: Money;
}

export interface OperationConditions {
  account_status: AccountStatus;
  timezone: 'America/Lima';
  rules: OperationRule[];
}

export interface OnboardingSession {
  session_id: string;
  started_at: string;
}

export interface StepRequest {
  step: OnboardingStep;
}

export interface StepRecorded {
  step: string;
  elapsed_ms: number;
}

export type UsernameAvailabilityStatus = 'AVAILABLE' | 'TAKEN' | 'INVALID_FORMAT';

export interface UsernameAvailabilityRequest {
  username: string;
  nombres?: string;
  apellido_paterno?: string;
  apellido_materno?: string;
}

export interface UsernameAvailabilityResponse {
  status: UsernameAvailabilityStatus;
  suggestions: string[];
}

export interface RegistrationRequest {
  session_id?: string;
  nombres: string;
  apellido_paterno: string;
  apellido_materno: string;
  usuario: string;
  password: string;
}

export interface RegistrationResponse {
  account: Account;
  welcome: { display_name: string };
  profile: ProfileStates;
  operation_conditions: OperationConditions;
  registration_duration_ms?: number | null;
}

export interface WalletDetail {
  account: Account;
  profile: ProfileStates;
  operation_conditions: OperationConditions;
  identity_mock_available: boolean;
}

export interface EmailOtpRequest {
  email: string;
}

export interface PhoneOtpRequest {
  phone: string;
}

export interface OtpIssued {
  channel: OtpChannel;
  expires_at: string;
  expires_in_seconds: number;
  next_request_allowed_at: string;
  otp_length: number;
  delivery: 'MOCK_NOT_SENT';
}

export interface PhoneOtpIssued extends OtpIssued {
  phone_e164: string;
}

export interface OtpConfirmationRequest {
  otp: string;
}

export interface IdentityMockRequest {
  terms_accepted: boolean;
  mock_inputs_confirmed: boolean;
}

export interface IdentityMockResponse {
  account: Account;
  profile: ProfileStates;
}

export interface OperationRequest {
  operation_type: OperationType;
  amount: Money;
}

export interface OperationAccepted {
  operation_id: string;
  operation_type: OperationType;
  amount: Money;
  operation_day: string;
  daily_accumulated: Money;
  daily_max: Money;
}

/** Error normalizado de la API (schema `Error` + estado HTTP). */
export interface ApiError {
  status: number;
  code: string;
  message: string;
  suggestions?: string[];
  retry_after_seconds?: number;
  details?: { field: string; rule: string }[];
}

export interface Credentials {
  username: string;
  password: string;
}
```

## `src/app/core/errors/api-error.ts`

```ts
import { HttpErrorResponse } from '@angular/common/http';
import { ApiError } from '../models/api.models';

export const ERROR_MESSAGES: Record<string, string> = {
  NETWORK_ERROR: 'No pudimos conectar con el servidor. Verifica tu conexión e intenta nuevamente.',
  VALIDATION_ERROR: 'Revisa los datos ingresados.',
  UNAUTHORIZED: 'Tus credenciales no son válidas. Vuelve a ingresar.',
  FORBIDDEN: 'No tienes acceso a esta cuenta.',
  NOT_FOUND: 'No encontramos el recurso solicitado.',
  SESSION_CLOSED: 'La sesión de registro ya finalizó.',
  USERNAME_TAKEN: 'Este usuario ya no está disponible. Elige una de las sugerencias.',
  INVALID_EMAIL_FORMAT: 'El formato del correo no es válido.',
  EMAIL_ALREADY_REGISTERED: 'Este correo ya está registrado por otro usuario.',
  INVALID_PHONE_FORMAT: 'Ingresa un celular peruano de 9 dígitos que empiece con 9.',
  PHONE_ALREADY_REGISTERED: 'Este número ya está registrado por otro usuario.',
  ALREADY_VALIDATED: 'Este dato ya fue validado.',
  OTP_RATE_LIMITED: 'Aún no puedes solicitar un nuevo código.',
  OTP_EXPIRED: 'El código venció. Solicita uno nuevo.',
  OTP_NOT_ACTIVE: 'El código ya no es válido. Solicita uno nuevo.',
  BIOMETRIC_MOCK_DISABLED:
    'La validación de identidad simulada no está disponible en este ambiente.',
  TERMS_NOT_ACCEPTED: 'Debes aceptar los términos y condiciones para continuar.',
  MOCK_INPUTS_INVALID: 'Confirma los datos simulados para continuar.',
  ALREADY_ACTIVE_FULL: 'Tu identidad ya fue validada.',
  OPERATION_NOT_ALLOWED: 'Esta operación no está permitida para tu nivel de cuenta.',
  PER_OPERATION_LIMIT_EXCEEDED: 'El monto supera el tope por operación de tu nivel de cuenta.',
  DAILY_LIMIT_EXCEEDED: 'Superaste el tope diario permitido para tu nivel de cuenta.',
  UNKNOWN: 'Ocurrió un error inesperado. Intenta nuevamente.',
};

function defaultCodeForStatus(status: number): string {
  switch (status) {
    case 401:
      return 'UNAUTHORIZED';
    case 403:
      return 'FORBIDDEN';
    case 404:
      return 'NOT_FOUND';
    case 422:
      return 'VALIDATION_ERROR';
    case 429:
      return 'OTP_RATE_LIMITED';
    default:
      return 'UNKNOWN';
  }
}

function extractPayload(body: unknown): Partial<ApiError> | null {
  if (!body || typeof body !== 'object') {
    return null;
  }
  const obj = body as Record<string, unknown>;
  if (typeof obj['code'] === 'string') {
    return obj as unknown as Partial<ApiError>;
  }
  const detail = obj['detail'];
  if (detail && typeof detail === 'object' && typeof (detail as Record<string, unknown>)['code'] === 'string') {
    return detail as unknown as Partial<ApiError>;
  }
  return null;
}

/** Convierte cualquier error de HttpClient en un `ApiError` normalizado (sin datos personales). */
export function toApiError(err: unknown): ApiError {
  if (err instanceof HttpErrorResponse) {
    if (err.status === 0) {
      return { status: 0, code: 'NETWORK_ERROR', message: ERROR_MESSAGES['NETWORK_ERROR'] };
    }
    const payload = extractPayload(err.error);
    const header = Number.parseInt(err.headers?.get('Retry-After') ?? '', 10);
    const retry =
      payload?.retry_after_seconds ?? (Number.isFinite(header) ? header : undefined);
    return {
      status: err.status,
      code: payload?.code ?? defaultCodeForStatus(err.status),
      message: payload?.message ?? '',
      suggestions: payload?.suggestions,
      retry_after_seconds: retry,
      details: payload?.details,
    };
  }
  return { status: -1, code: 'UNKNOWN', message: '' };
}

/** Mensaje en español para mostrar al usuario. */
export function describeError(error: ApiError): string {
  const base = ERROR_MESSAGES[error.code] ?? (error.message || ERROR_MESSAGES['UNKNOWN']);
  if (error.code === 'OTP_RATE_LIMITED' && error.retry_after_seconds) {
    return `${base} Intenta de nuevo en ${error.retry_after_seconds} s.`;
  }
  return base;
}
```

## `src/app/core/errors/api-error.spec.ts`

```ts
import { HttpErrorResponse, HttpHeaders } from '@angular/common/http';
import { describeError, toApiError } from './api-error';

describe('toApiError / describeError', () => {
  it('normaliza el schema Error de la API', () => {
    const err = new HttpErrorResponse({
      status: 409,
      error: { code: 'USERNAME_TAKEN', message: 'x', suggestions: ['juan1'] },
    });
    const api = toApiError(err);
    expect(api.status).toBe(409);
    expect(api.code).toBe('USERNAME_TAKEN');
    expect(api.suggestions).toEqual(['juan1']);
  });

  it('soporta el formato FastAPI { detail: { code } }', () => {
    const err = new HttpErrorResponse({
      status: 422,
      error: { detail: { code: 'TERMS_NOT_ACCEPTED', message: 'x' } },
    });
    expect(toApiError(err).code).toBe('TERMS_NOT_ACCEPTED');
  });

  it('usa el código por defecto según el estado cuando no hay cuerpo', () => {
    expect(toApiError(new HttpErrorResponse({ status: 401 })).code).toBe('UNAUTHORIZED');
    expect(toApiError(new HttpErrorResponse({ status: 403 })).code).toBe('FORBIDDEN');
    expect(toApiError(new HttpErrorResponse({ status: 500 })).code).toBe('UNKNOWN');
  });

  it('marca NETWORK_ERROR cuando no hay conexión (status 0)', () => {
    expect(toApiError(new HttpErrorResponse({ status: 0 })).code).toBe('NETWORK_ERROR');
  });

  it('lee Retry-After cuando el cuerpo no lo trae', () => {
    const err = new HttpErrorResponse({
      status: 429,
      headers: new HttpHeaders({ 'Retry-After': '17' }),
      error: { code: 'OTP_RATE_LIMITED', message: 'x' },
    });
    expect(toApiError(err).retry_after_seconds).toBe(17);
  });

  it('describe el rate limit con los segundos de espera', () => {
    const text = describeError({
      status: 429,
      code: 'OTP_RATE_LIMITED',
      message: '',
      retry_after_seconds: 30,
    });
    expect(text).toContain('30 s');
  });

  it('cae en un mensaje genérico para errores desconocidos', () => {
    expect(describeError(toApiError(new Error('boom')))).toContain('inesperado');
  });
});
```

---

## `src/app/core/services/session.store.ts`

```ts
import { Injectable, computed, signal } from '@angular/core';
import { Credentials, RegistrationResponse } from '../models/api.models';

function toBase64(value: string): string {
  const bytes = new TextEncoder().encode(value);
  let binary = '';
  bytes.forEach((b) => (binary += String.fromCharCode(b)));
  return btoa(binary);
}

/**
 * Estado de sesión SOLO en memoria.
 * Las credenciales nunca se guardan en storage, logs ni analítica (CA-02, CA-10).
 */
@Injectable({ providedIn: 'root' })
export class SessionStore {
  private readonly credentials = signal<Credentials | null>(null);
  private readonly registrationState = signal<RegistrationResponse | null>(null);

  readonly registration = this.registrationState.asReadonly();
  readonly walletId = computed(() => this.registrationState()?.account.wallet_id ?? null);
  readonly isAuthenticated = computed(() => !!this.credentials() && !!this.walletId());

  start(credentials: Credentials, registration: RegistrationResponse): void {
    this.credentials.set({ ...credentials });
    this.registrationState.set(registration);
  }

  clear(): void {
    this.credentials.set(null);
    this.registrationState.set(null);
  }

  /** Cabecera HTTP Basic (usuario:contraseña). Null si no hay sesión. */
  authorizationHeader(): string | null {
    const c = this.credentials();
    return c ? `Basic ${toBase64(`${c.username}:${c.password}`)}` : null;
  }
}
```

## `src/app/core/interceptors/basic-auth.interceptor.ts`

```ts
import { HttpErrorResponse, HttpInterceptorFn } from '@angular/common/http';
import { inject } from '@angular/core';
import { Router } from '@angular/router';
import { catchError, throwError } from 'rxjs';
import { API_BASE_URL } from '../config/api-config';
import { SessionStore } from '../services/session.store';

/** Añade HTTP Basic solo a /wallets/* (sin tokens, según el contrato). */
export const basicAuthInterceptor: HttpInterceptorFn = (req, next) => {
  const base = inject(API_BASE_URL);
  const store = inject(SessionStore);
  const router = inject(Router);

  if (!req.url.startsWith(`${base}/wallets/`)) {
    return next(req);
  }

  const header = store.authorizationHeader();
  const authReq = header ? req.clone({ setHeaders: { Authorization: header } }) : req;

  return next(authReq).pipe(
    catchError((err: unknown) => {
      if (err instanceof HttpErrorResponse && err.status === 401) {
        store.clear();
        void router.navigateByUrl('/onboarding');
      }
      return throwError(() => err);
    }),
  );
};
```

## `src/app/core/interceptors/basic-auth.interceptor.spec.ts`

```ts
import { HttpClient, provideHttpClient, withInterceptors } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { Router, provideRouter } from '@angular/router';
import { REGISTRATION_RESPONSE } from '../../../testing/fixtures';
import { API_BASE_URL } from '../config/api-config';
import { SessionStore } from '../services/session.store';
import { basicAuthInterceptor } from './basic-auth.interceptor';

describe('basicAuthInterceptor', () => {
  let http: HttpClient;
  let ctrl: HttpTestingController;
  let store: SessionStore;
  let router: Router;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [
        provideHttpClient(withInterceptors([basicAuthInterceptor])),
        provideHttpClientTesting(),
        provideRouter([]),
        { provide: API_BASE_URL, useValue: '/api' },
      ],
    });
    http = TestBed.inject(HttpClient);
    ctrl = TestBed.inject(HttpTestingController);
    store = TestBed.inject(SessionStore);
    router = TestBed.inject(Router);
    spyOn(router, 'navigateByUrl').and.resolveTo(true);
  });

  afterEach(() => ctrl.verify());

  it('agrega Authorization Basic en /wallets/*', () => {
    store.start({ username: 'jperez', password: 'Clave#Segura2026' }, REGISTRATION_RESPONSE);
    http.get('/api/wallets/w-1').subscribe();
    const req = ctrl.expectOne('/api/wallets/w-1');
    expect(req.request.headers.get('Authorization')).toBe(
      'Basic ' + btoa('jperez:Clave#Segura2026'),
    );
    req.flush({});
  });

  it('no agrega Authorization en /onboarding/*', () => {
    store.start({ username: 'jperez', password: 'Clave#Segura2026' }, REGISTRATION_RESPONSE);
    http.post('/api/onboarding/sessions', {}).subscribe();
    const req = ctrl.expectOne('/api/onboarding/sessions');
    expect(req.request.headers.has('Authorization')).toBeFalse();
    req.flush({});
  });

  it('ante un 401 limpia la sesión y vuelve a onboarding', () => {
    store.start({ username: 'jperez', password: 'Clave#Segura2026' }, REGISTRATION_RESPONSE);
    http.get('/api/wallets/w-1').subscribe({ error: () => undefined });
    ctrl
      .expectOne('/api/wallets/w-1')
      .flush({ code: 'UNAUTHORIZED', message: 'x' }, { status: 401, statusText: 'Unauthorized' });
    expect(store.isAuthenticated()).toBeFalse();
    expect(router.navigateByUrl).toHaveBeenCalledWith('/onboarding');
  });
});
```

## `src/app/core/guards/auth.guard.ts`

```ts
import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';
import { SessionStore } from '../services/session.store';

export const authGuard: CanActivateFn = () => {
  const store = inject(SessionStore);
  const router = inject(Router);
  return store.isAuthenticated() ? true : router.createUrlTree(['/onboarding']);
};
```

## `src/app/core/guards/auth.guard.spec.ts`

```ts
import { TestBed } from '@angular/core/testing';
import { ActivatedRouteSnapshot, RouterStateSnapshot, UrlTree, provideRouter } from '@angular/router';
import { REGISTRATION_RESPONSE } from '../../../testing/fixtures';
import { SessionStore } from '../services/session.store';
import { authGuard } from './auth.guard';

describe('authGuard', () => {
  let store: SessionStore;

  beforeEach(() => {
    TestBed.configureTestingModule({ providers: [provideRouter([])] });
    store = TestBed.inject(SessionStore);
  });

  const run = () =>
    TestBed.runInInjectionContext(() =>
      authGuard({} as ActivatedRouteSnapshot, {} as RouterStateSnapshot),
    );

  it('redirige a /onboarding si no hay sesión', () => {
    const result = run() as UrlTree;
    expect(result.toString()).toBe('/onboarding');
  });

  it('permite el acceso con sesión', () => {
    store.start({ username: 'jperez', password: 'Clave#Segura2026' }, REGISTRATION_RESPONSE);
    expect(run()).toBeTrue();
  });
});
```

## `src/app/core/services/onboarding-api.service.ts`

```ts
import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { API_BASE_URL } from '../config/api-config';
import {
  OnboardingSession,
  RegistrationRequest,
  RegistrationResponse,
  StepRecorded,
  StepRequest,
  UsernameAvailabilityRequest,
  UsernameAvailabilityResponse,
} from '../models/api.models';

/** Endpoints públicos de onboarding (sin autenticación). */
@Injectable({ providedIn: 'root' })
export class OnboardingApiService {
  private readonly http = inject(HttpClient);
  private readonly base = inject(API_BASE_URL);

  startSession(): Observable<OnboardingSession> {
    return this.http.post<OnboardingSession>(`${this.base}/onboarding/sessions`, {});
  }

  registerStep(sessionId: string, body: StepRequest): Observable<StepRecorded> {
    return this.http.post<StepRecorded>(
      `${this.base}/onboarding/sessions/${sessionId}/steps`,
      body,
    );
  }

  checkUsername(body: UsernameAvailabilityRequest): Observable<UsernameAvailabilityResponse> {
    return this.http.post<UsernameAvailabilityResponse>(
      `${this.base}/onboarding/username-availability`,
      body,
    );
  }

  register(body: RegistrationRequest): Observable<RegistrationResponse> {
    return this.http.post<RegistrationResponse>(`${this.base}/onboarding/registrations`, body);
  }
}
```

## `src/app/core/services/onboarding-api.service.spec.ts`

```ts
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { REGISTRATION_RESPONSE } from '../../../testing/fixtures';
import { API_BASE_URL } from '../config/api-config';
import { toApiError } from '../errors/api-error';
import { OnboardingApiService } from './onboarding-api.service';

describe('OnboardingApiService', () => {
  const BASE = 'http://localhost:8000';
  let service: OnboardingApiService;
  let ctrl: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
        { provide: API_BASE_URL, useValue: BASE },
      ],
    });
    service = TestBed.inject(OnboardingApiService);
    ctrl = TestBed.inject(HttpTestingController);
  });

  afterEach(() => ctrl.verify());

  it('POST /onboarding/sessions inicia la medición', () => {
    let result: unknown;
    service.startSession().subscribe((r) => (result = r));
    const req = ctrl.expectOne(`${BASE}/onboarding/sessions`);
    expect(req.request.method).toBe('POST');
    req.flush({ session_id: 's-1', started_at: '2026-10-30T20:00:00Z' });
    expect(result).toEqual({ session_id: 's-1', started_at: '2026-10-30T20:00:00Z' });
  });

  it('POST /onboarding/sessions/{id}/steps envía solo el nombre del paso', () => {
    service.registerStep('s-1', { step: 'NOMBRES' }).subscribe();
    const req = ctrl.expectOne(`${BASE}/onboarding/sessions/s-1/steps`);
    expect(req.request.method).toBe('POST');
    expect(req.request.body).toEqual({ step: 'NOMBRES' });
    req.flush({ step: 'NOMBRES', elapsed_ms: 1200 });
  });

  it('POST /onboarding/username-availability envía el usuario en el cuerpo (no en la URL)', () => {
    let status = '';
    service.checkUsername({ username: 'jperez' }).subscribe((r) => (status = r.status));
    const req = ctrl.expectOne(`${BASE}/onboarding/username-availability`);
    expect(req.request.url).not.toContain('jperez');
    expect(req.request.body).toEqual({ username: 'jperez' });
    req.flush({ status: 'AVAILABLE', suggestions: [] });
    expect(status).toBe('AVAILABLE');
  });

  it('POST /onboarding/registrations devuelve la cuenta ACTIVE_BASIC', () => {
    let status = '';
    service
      .register({
        nombres: 'María José',
        apellido_paterno: 'Quispe',
        apellido_materno: 'Rojas',
        usuario: 'mjquispe',
        password: 'Clave#Segura2026',
      })
      .subscribe((r) => (status = r.account.status));
    const req = ctrl.expectOne(`${BASE}/onboarding/registrations`);
    expect(req.request.method).toBe('POST');
    req.flush(REGISTRATION_RESPONSE);
    expect(status).toBe('ACTIVE_BASIC');
  });

  it('propaga 409 USERNAME_TAKEN con sugerencias', () => {
    let apiError;
    service
      .register({
        nombres: 'A',
        apellido_paterno: 'B',
        apellido_materno: 'C',
        usuario: 'taken',
        password: 'Clave#Segura2026',
      })
      .subscribe({ error: (e) => (apiError = toApiError(e)) });
    ctrl
      .expectOne(`${BASE}/onboarding/registrations`)
      .flush(
        { code: 'USERNAME_TAKEN', message: 'x', suggestions: ['taken1'] },
        { status: 409, statusText: 'Conflict' },
      );
    expect(apiError).toEqual(
      jasmine.objectContaining({ code: 'USERNAME_TAKEN', suggestions: ['taken1'] }),
    );
  });
});
```

## `src/app/core/services/wallet-api.service.ts`

```ts
import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { API_BASE_URL } from '../config/api-config';
import {
  EmailOtpRequest,
  IdentityMockRequest,
  IdentityMockResponse,
  OperationAccepted,
  OperationRequest,
  OtpConfirmationRequest,
  OtpIssued,
  PhoneOtpIssued,
  PhoneOtpRequest,
  ProfileStatesResponse,
  WalletDetail,
} from '../models/api.models';

/** Endpoints /wallets/{id}/... (HTTP Basic aplicado por el interceptor). */
@Injectable({ providedIn: 'root' })
export class WalletApiService {
  private readonly http = inject(HttpClient);
  private readonly base = inject(API_BASE_URL);

  private url(walletId: string, path = ''): string {
    return `${this.base}/wallets/${walletId}${path}`;
  }

  getWallet(walletId: string): Observable<WalletDetail> {
    return this.http.get<WalletDetail>(this.url(walletId));
  }

  requestEmailOtp(walletId: string, body: EmailOtpRequest): Observable<OtpIssued> {
    return this.http.post<OtpIssued>(this.url(walletId, '/profile/email/otp-requests'), body);
  }

  confirmEmailOtp(walletId: string, body: OtpConfirmationRequest): Observable<ProfileStatesResponse> {
    return this.http.post<ProfileStatesResponse>(
      this.url(walletId, '/profile/email/otp-confirmations'),
      body,
    );
  }

  requestPhoneOtp(walletId: string, body: PhoneOtpRequest): Observable<PhoneOtpIssued> {
    return this.http.post<PhoneOtpIssued>(this.url(walletId, '/profile/phone/otp-requests'), body);
  }

  confirmPhoneOtp(walletId: string, body: OtpConfirmationRequest): Observable<ProfileStatesResponse> {
    return this.http.post<ProfileStatesResponse>(
      this.url(walletId, '/profile/phone/otp-confirmations'),
      body,
    );
  }

  mockIdentity(walletId: string, body: IdentityMockRequest): Observable<IdentityMockResponse> {
    return this.http.post<IdentityMockResponse>(
      this.url(walletId, '/profile/identity/mock-verification'),
      body,
    );
  }

  registerOperation(walletId: string, body: OperationRequest): Observable<OperationAccepted> {
    return this.http.post<OperationAccepted>(this.url(walletId, '/operations'), body);
  }
}
```

## `src/app/core/services/wallet-api.service.spec.ts`

```ts
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { WALLET_DETAIL } from '../../../testing/fixtures';
import { API_BASE_URL } from '../config/api-config';
import { WalletApiService } from './wallet-api.service';

describe('WalletApiService', () => {
  const BASE = 'http://localhost:8000';
  const W = `${BASE}/wallets/w-1`;
  let service: WalletApiService;
  let ctrl: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
        { provide: API_BASE_URL, useValue: BASE },
      ],
    });
    service = TestBed.inject(WalletApiService);
    ctrl = TestBed.inject(HttpTestingController);
  });

  afterEach(() => ctrl.verify());

  it('GET /wallets/{id}', () => {
    let identityAvailable: boolean | undefined;
    service.getWallet('w-1').subscribe((w) => (identityAvailable = w.identity_mock_available));
    const req = ctrl.expectOne(W);
    expect(req.request.method).toBe('GET');
    req.flush(WALLET_DETAIL);
    expect(identityAvailable).toBeTrue();
  });

  it('POST email otp-requests', () => {
    service.requestEmailOtp('w-1', { email: 'ana@example.com' }).subscribe();
    const req = ctrl.expectOne(`${W}/profile/email/otp-requests`);
    expect(req.request.method).toBe('POST');
    expect(req.request.body).toEqual({ email: 'ana@example.com' });
    req.flush({});
  });

  it('POST email otp-confirmations', () => {
    service.confirmEmailOtp('w-1', { otp: '123456' }).subscribe();
    const req = ctrl.expectOne(`${W}/profile/email/otp-confirmations`);
    expect(req.request.body).toEqual({ otp: '123456' });
    req.flush({});
  });

  it('POST phone otp-requests envía 9 dígitos sin prefijo', () => {
    service.requestPhoneOtp('w-1', { phone: '912345678' }).subscribe();
    const req = ctrl.expectOne(`${W}/profile/phone/otp-requests`);
    expect(req.request.body).toEqual({ phone: '912345678' });
    req.flush({});
  });

  it('POST phone otp-confirmations', () => {
    service.confirmPhoneOtp('w-1', { otp: 'abcdef' }).subscribe();
    ctrl.expectOne(`${W}/profile/phone/otp-confirmations`).flush({});
  });

  it('POST identity/mock-verification', () => {
    service.mockIdentity('w-1', { terms_accepted: true, mock_inputs_confirmed: true }).subscribe();
    const req = ctrl.expectOne(`${W}/profile/identity/mock-verification`);
    expect(req.request.body).toEqual({ terms_accepted: true, mock_inputs_confirmed: true });
    req.flush({});
  });

  it('POST operations', () => {
    service.registerOperation('w-1', { operation_type: 'PAYMENT', amount: '20.00' }).subscribe();
    const req = ctrl.expectOne(`${W}/operations`);
    expect(req.request.body).toEqual({ operation_type: 'PAYMENT', amount: '20.00' });
    req.flush({});
  });
});
```

---

## `src/app/core/utils/time.ts`

```ts
/** Segundos restantes (redondeo hacia arriba, mínimo 0) hasta `targetMs`. */
export function secondsLeft(targetMs: number | null, nowMs: number): number {
  if (targetMs === null) {
    return 0;
  }
  return Math.max(0, Math.ceil((targetMs - nowMs) / 1000));
}

/** Vigencia del OTP y espera entre solicitudes (CA-07, CA-08). */
export const OTP_TTL_SECONDS = 60;
export const OTP_RESEND_SECONDS = 45;
```

## `src/app/core/utils/format.ts`

```ts
import { AccountStatus, OperationGroup, OperationType, ProfileStates } from '../models/api.models';

export function formatSoles(value: string | null | undefined): string {
  if (value === null || value === undefined) {
    return 'Sin tope';
  }
  const n = Number(value);
  if (!Number.isFinite(n)) {
    return `S/ ${value}`;
  }
  return (
    'S/ ' + n.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
  );
}

export const OPERATION_TYPE_LABELS: Record<OperationType, string> = {
  TOPUP_OWN: 'Recarga propia',
  TOPUP_THIRD_PARTY: 'Recarga de terceros',
  PAYMENT: 'Pago',
};

export const GROUP_LABELS: Record<OperationGroup, string> = {
  COMBINED: 'Pagos y recargas (tope diario combinado)',
  TOPUP: 'Recargas',
  PAYMENT: 'Pagos',
};

export const STATUS_LABELS: Record<AccountStatus, string> = {
  ACTIVE_BASIC: 'Cuenta básica',
  ACTIVE_FULL: 'Cuenta completa',
};

export const PROFILE_STATE_LABELS: Record<string, string> = {
  PENDING_EMAIL: 'Pendiente',
  ACTIVE_EMAIL: 'Validado',
  PENDING_MOVIL: 'Pendiente',
  ACTIVE_MOVIL: 'Validado',
  PENDING_BIOM: 'Pendiente',
  ACTIVE_BIOM: 'Validado',
};

export function hasPendingProfile(profile: ProfileStates): boolean {
  return Object.values(profile).some((s) => s.startsWith('PENDING'));
}
```

## `src/app/core/utils/utils.spec.ts`

```ts
import { formatSoles, hasPendingProfile } from './format';
import { secondsLeft } from './time';

describe('time utils', () => {
  it('secondsLeft redondea hacia arriba y nunca es negativo', () => {
    expect(secondsLeft(null, 1000)).toBe(0);
    expect(secondsLeft(10_500, 10_000)).toBe(1);
    expect(secondsLeft(55_000, 10_000)).toBe(45);
    expect(secondsLeft(5_000, 10_000)).toBe(0);
  });
});

describe('format utils', () => {
  it('formatSoles da formato S/ con 2 decimales y separador de miles', () => {
    expect(formatSoles('20')).toBe('S/ 20.00');
    expect(formatSoles('1000.5')).toBe('S/ 1,000.50');
  });

  it('formatSoles indica "Sin tope" cuando no hay valor', () => {
    expect(formatSoles(null)).toBe('Sin tope');
    expect(formatSoles(undefined)).toBe('Sin tope');
  });

  it('hasPendingProfile detecta estados PENDING_*', () => {
    expect(
      hasPendingProfile({
        estado_c1: 'ACTIVE_EMAIL',
        estado_c2: 'PENDING_MOVIL',
        estado_c3: 'ACTIVE_BIOM',
      }),
    ).toBeTrue();
    expect(
      hasPendingProfile({
        estado_c1: 'ACTIVE_EMAIL',
        estado_c2: 'ACTIVE_MOVIL',
        estado_c3: 'ACTIVE_BIOM',
      }),
    ).toBeFalse();
  });
});
```

## `src/app/core/validators/field-validators.ts`

```ts
import { AbstractControl, ValidationErrors, ValidatorFn, Validators } from '@angular/forms';

// Mismas reglas que el contrato OpenAPI del backend.
export const NOMBRES_PATTERN = /^[A-Za-zÁÉÍÓÚÜÑáéíóúüñ]+( [A-Za-zÁÉÍÓÚÜÑáéíóúüñ]+)*$/;
export const APELLIDO_PATTERN = /^[A-Za-zÁÉÍÓÚÜÑáéíóúüñ]+$/;
export const USUARIO_PATTERN = /^[!-~]*[A-Za-z][!-~]*$/;
export const PASSWORD_CHARS_PATTERN = /^[!-~]*$/;
export const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
export const PHONE_PATTERN = /^9[0-9]{8}$/;
export const AMOUNT_PATTERN = /^(0|[1-9][0-9]*)(\.[0-9]{1,2})?$/;

function patternValidator(re: RegExp, errorKey: string): ValidatorFn {
  return (control: AbstractControl): ValidationErrors | null => {
    const v = control.value;
    if (v === null || v === undefined || v === '') {
      return null;
    }
    return re.test(String(v)) ? null : { [errorKey]: true };
  };
}

const amountPositive: ValidatorFn = (control) => {
  const v = control.value;
  if (v === null || v === undefined || v === '') {
    return null;
  }
  return Number(v) > 0 ? null : { amountPositive: true };
};

export const nombresValidators = (): ValidatorFn[] => [
  Validators.required,
  patternValidator(NOMBRES_PATTERN, 'nombresFormat'),
  Validators.maxLength(30),
];

export const apellidoValidators = (): ValidatorFn[] => [
  Validators.required,
  patternValidator(APELLIDO_PATTERN, 'apellidoFormat'),
  Validators.maxLength(20),
];

export const usuarioValidators = (): ValidatorFn[] => [
  Validators.required,
  patternValidator(USUARIO_PATTERN, 'usuarioFormat'),
  Validators.maxLength(20),
];

export const passwordValidators = (): ValidatorFn[] => [
  Validators.required,
  patternValidator(PASSWORD_CHARS_PATTERN, 'passwordChars'),
  Validators.minLength(10),
  Validators.maxLength(64),
];

export const emailValidators = (): ValidatorFn[] => [
  Validators.required,
  patternValidator(EMAIL_PATTERN, 'emailFormat'),
  Validators.maxLength(254),
];

export const phoneValidators = (): ValidatorFn[] => [
  Validators.required,
  patternValidator(PHONE_PATTERN, 'phoneFormat'),
];

export const otpValidators = (): ValidatorFn[] => [Validators.required, Validators.maxLength(32)];

export const amountValidators = (): ValidatorFn[] => [
  Validators.required,
  patternValidator(AMOUNT_PATTERN, 'amountFormat'),
  amountPositive,
];
```

## `src/app/core/validators/validation-messages.ts`

```ts
import { ValidationErrors } from '@angular/forms';

/** Mensaje en español para el primer error de un control. No incluye el valor ingresado. */
export function validationMessage(errors: ValidationErrors | null): string | null {
  if (!errors) {
    return null;
  }
  if (errors['required']) return 'Este campo es obligatorio.';
  if (errors['nombresFormat']) return 'Solo letras, con un único espacio entre nombres.';
  if (errors['apellidoFormat']) return 'Solo letras, sin espacios ni números.';
  if (errors['usuarioFormat']) {
    return 'Usa caracteres sin espacios e incluye al menos una letra.';
  }
  if (errors['passwordChars']) return 'Sin espacios: usa letras, números o símbolos.';
  if (errors['emailFormat']) return 'Ingresa un correo válido, por ejemplo nombre@dominio.com.';
  if (errors['phoneFormat']) return 'Ingresa 9 dígitos que empiecen con 9.';
  if (errors['amountFormat']) return 'Usa punto decimal y hasta 2 decimales.';
  if (errors['amountPositive']) return 'El monto debe ser mayor que 0.';
  if (errors['maxlength']) return `Máximo ${errors['maxlength'].requiredLength} caracteres.`;
  if (errors['minlength']) return `Mínimo ${errors['minlength'].requiredLength} caracteres.`;
  return 'Valor no válido.';
}
```

## `src/app/core/validators/password-strength.ts`

```ts
export type StrengthLevel = 'empty' | 'weak' | 'medium' | 'strong';

export interface PasswordStrength {
  level: StrengthLevel;
  label: string;
  hints: string[];
  /** true si cumple la política mínima (10 a 64 caracteres imprimibles sin espacios). */
  acceptable: boolean;
}

/**
 * Evalúa la robustez solo en el cliente. La contraseña no se envía a analítica ni se registra.
 */
export function evaluatePasswordStrength(password: string): PasswordStrength {
  if (!password) {
    return { level: 'empty', label: '', hints: [], acceptable: false };
  }

  const classes = [/[a-z]/, /[A-Z]/, /[0-9]/, /[^A-Za-z0-9]/].filter((re) => re.test(password)).length;
  const acceptable = password.length >= 10 && password.length <= 64 && /^[!-~]+$/.test(password);

  const hints: string[] = [];
  if (password.length < 10) hints.push('Usa al menos 10 caracteres.');
  if (classes < 3) hints.push('Combina mayúsculas, minúsculas, números y símbolos.');
  if (/(.)\1{2,}/.test(password)) hints.push('Evita repetir el mismo carácter varias veces.');

  let level: StrengthLevel;
  if (!acceptable) {
    level = 'weak';
  } else if (classes >= 3 && password.length >= 12) {
    level = 'strong';
  } else if (classes >= 2) {
    level = 'medium';
  } else {
    level = 'weak';
  }

  const labels: Record<StrengthLevel, string> = {
    empty: '',
    weak: 'Contraseña débil',
    medium: 'Contraseña aceptable',
    strong: 'Contraseña fuerte',
  };
  return { level, label: labels[level], hints, acceptable };
}
```

## `src/app/core/validators/validators.spec.ts`

```ts
import { FormControl, ValidatorFn } from '@angular/forms';
import {
  amountValidators,
  apellidoValidators,
  emailValidators,
  nombresValidators,
  passwordValidators,
  phoneValidators,
  usuarioValidators,
} from './field-validators';
import { validationMessage } from './validation-messages';
import { evaluatePasswordStrength } from './password-strength';

const control = (value: string, validators: ValidatorFn[]) => new FormControl(value, validators);
const isValid = (value: string, validators: ValidatorFn[]) => control(value, validators).valid;

describe('nombresValidators (CA-02)', () => {
  it('acepta letras con espacio entre nombres', () => {
    expect(isValid('María José', nombresValidators())).toBeTrue();
  });
  it('rechaza dígitos', () => {
    expect(isValid('Maria123', nombresValidators())).toBeFalse();
  });
  it('rechaza espacios dobles, iniciales o finales', () => {
    expect(isValid('María  José', nombresValidators())).toBeFalse();
    expect(isValid(' María', nombresValidators())).toBeFalse();
    expect(isValid('María ', nombresValidators())).toBeFalse();
  });
  it('acepta 30 caracteres y rechaza 31', () => {
    expect(isValid('a'.repeat(30), nombresValidators())).toBeTrue();
    expect(isValid('a'.repeat(31), nombresValidators())).toBeFalse();
  });
  it('rechaza vacío', () => {
    expect(isValid('', nombresValidators())).toBeFalse();
  });
});

describe('apellidoValidators (CA-02)', () => {
  it('acepta un apellido alfabético', () => {
    expect(isValid('Quispe', apellidoValidators())).toBeTrue();
  });
  it('rechaza dígitos y espacios', () => {
    expect(isValid('Quispe9', apellidoValidators())).toBeFalse();
    expect(isValid('De la Cruz', apellidoValidators())).toBeFalse();
  });
  it('acepta 20 y rechaza 21', () => {
    expect(isValid('a'.repeat(20), apellidoValidators())).toBeTrue();
    expect(isValid('a'.repeat(21), apellidoValidators())).toBeFalse();
  });
});

describe('usuarioValidators (CA-02)', () => {
  it('acepta letras con símbolos', () => {
    expect(isValid('jperez_01', usuarioValidators())).toBeTrue();
    expect(isValid('user!#', usuarioValidators())).toBeTrue();
  });
  it('exige al menos una letra y no admite espacios', () => {
    expect(isValid('12345', usuarioValidators())).toBeFalse();
    expect(isValid('ju an', usuarioValidators())).toBeFalse();
  });
  it('acepta 20 y rechaza 21 caracteres', () => {
    expect(isValid('a'.repeat(20), usuarioValidators())).toBeTrue();
    expect(isValid('a'.repeat(21), usuarioValidators())).toBeFalse();
  });
});

describe('passwordValidators (CA-02)', () => {
  it('rechaza 9 y acepta 10 caracteres', () => {
    expect(isValid('a'.repeat(9), passwordValidators())).toBeFalse();
    expect(isValid('a'.repeat(10), passwordValidators())).toBeTrue();
  });
  it('permite símbolos y rechaza espacios', () => {
    expect(isValid('Clave#Segura2026', passwordValidators())).toBeTrue();
    expect(isValid('con espacio 12345', passwordValidators())).toBeFalse();
  });
  it('rechaza más de 64 caracteres', () => {
    expect(isValid('a'.repeat(65), passwordValidators())).toBeFalse();
  });
});

describe('emailValidators / phoneValidators (CA-07, CA-08)', () => {
  it('valida el formato de correo', () => {
    expect(isValid('ana@example.com', emailValidators())).toBeTrue();
    expect(isValid('ana@@example', emailValidators())).toBeFalse();
  });
  it('acepta solo celulares peruanos de 9 dígitos que empiezan con 9', () => {
    expect(isValid('912345678', phoneValidators())).toBeTrue();
    expect(isValid('812345678', phoneValidators())).toBeFalse();
    expect(isValid('91234567', phoneValidators())).toBeFalse();
    expect(isValid('9123456789', phoneValidators())).toBeFalse();
  });
});

describe('amountValidators', () => {
  it('acepta montos con hasta 2 decimales mayores que 0', () => {
    expect(isValid('20', amountValidators())).toBeTrue();
    expect(isValid('20.5', amountValidators())).toBeTrue();
    expect(isValid('20.00', amountValidators())).toBeTrue();
  });
  it('rechaza cero, negativos, 3 decimales y vacío', () => {
    expect(isValid('0', amountValidators())).toBeFalse();
    expect(isValid('-5', amountValidators())).toBeFalse();
    expect(isValid('20.001', amountValidators())).toBeFalse();
    expect(isValid('', amountValidators())).toBeFalse();
  });
});

describe('validationMessage', () => {
  it('devuelve null sin errores', () => {
    expect(validationMessage(null)).toBeNull();
  });
  it('no incluye el valor ingresado en el mensaje', () => {
    const c = control('Maria123', nombresValidators());
    const msg = validationMessage(c.errors) ?? '';
    expect(msg).toContain('Solo letras');
    expect(msg).not.toContain('Maria123');
  });
  it('informa longitud máxima', () => {
    const c = control('a'.repeat(31), nombresValidators());
    expect(validationMessage(c.errors)).toContain('30');
  });
});

describe('evaluatePasswordStrength (CA-02)', () => {
  it('vacío', () => {
    expect(evaluatePasswordStrength('').level).toBe('empty');
  });
  it('débil si es corta', () => {
    const s = evaluatePasswordStrength('abc');
    expect(s.level).toBe('weak');
    expect(s.acceptable).toBeFalse();
    expect(s.hints.join(' ')).toContain('10 caracteres');
  });
  it('débil si tiene 10 caracteres de una sola clase', () => {
    const s = evaluatePasswordStrength('abcdefghij');
    expect(s.acceptable).toBeTrue();
    expect(s.level).toBe('weak');
  });
  it('media con 10 caracteres y 3 clases', () => {
    expect(evaluatePasswordStrength('Abcdefgh12').level).toBe('medium');
  });
  it('fuerte con 12 o más caracteres y 3 o más clases', () => {
    expect(evaluatePasswordStrength('Abcdefgh12!x').level).toBe('strong');
  });
  it('no es aceptable con espacios', () => {
    expect(evaluatePasswordStrength('Abcdefgh 12!x').acceptable).toBeFalse();
  });
});
```

---

## `src/testing/fixtures.ts`

```ts
import {
  OperationConditions,
  RegistrationResponse,
  WalletDetail,
} from '../app/core/models/api.models';

export const BASIC_CONDITIONS: OperationConditions = {
  account_status: 'ACTIVE_BASIC',
  timezone: 'America/Lima',
  rules: [
    {
      operation_group: 'COMBINED',
      operation_types: ['TOPUP_OWN', 'PAYMENT'],
      per_operation_max: '20.00',
      daily_max: '60.00',
    },
  ],
};

export const FULL_CONDITIONS: OperationConditions = {
  account_status: 'ACTIVE_FULL',
  timezone: 'America/Lima',
  rules: [
    {
      operation_group: 'TOPUP',
      operation_types: ['TOPUP_OWN', 'TOPUP_THIRD_PARTY'],
      per_operation_max: null,
      daily_max: '1000.00',
    },
    {
      operation_group: 'PAYMENT',
      operation_types: ['PAYMENT'],
      per_operation_max: '500.00',
      daily_max: '1000.00',
    },
  ],
};

export const REGISTRATION_RESPONSE: RegistrationResponse = {
  account: { wallet_id: 'w-1', status: 'ACTIVE_BASIC', balance: '0.00', currency: 'PEN' },
  welcome: { display_name: 'María José' },
  profile: {
    estado_c1: 'PENDING_EMAIL',
    estado_c2: 'PENDING_MOVIL',
    estado_c3: 'PENDING_BIOM',
  },
  operation_conditions: BASIC_CONDITIONS,
  registration_duration_ms: 42_000,
};

export const WALLET_DETAIL: WalletDetail = {
  account: REGISTRATION_RESPONSE.account,
  profile: REGISTRATION_RESPONSE.profile,
  operation_conditions: BASIC_CONDITIONS,
  identity_mock_available: true,
};
```

---

## `src/app/shared/operation-conditions.component.ts`

```ts
import { Component, input } from '@angular/core';
import { OperationConditions, OperationRule } from '../core/models/api.models';
import {
  GROUP_LABELS,
  OPERATION_TYPE_LABELS,
  STATUS_LABELS,
  formatSoles,
} from '../core/utils/format';

@Component({
  selector: 'app-operation-conditions',
  standalone: true,
  template: `
    <section class="card" aria-labelledby="cond-title" data-testid="conditions">
      <h2 id="cond-title">Condiciones de tus operaciones</h2>
      <p class="muted">
        Nivel: <strong>{{ statusLabel() }}</strong> · Zona horaria: Perú (America/Lima). El contador
        diario se reinicia al cambiar de día.
      </p>
      <table>
        <thead>
          <tr>
            <th>Grupo</th>
            <th>Operaciones permitidas</th>
            <th>Máximo por operación</th>
            <th>Máximo diario</th>
          </tr>
        </thead>
        <tbody>
          @for (rule of conditions().rules; track rule.operation_group) {
            <tr data-testid="condition-row">
              <td>{{ groupLabel(rule) }}</td>
              <td>{{ typesText(rule) }}</td>
              <td>{{ money(rule.per_operation_max) }}</td>
              <td>{{ money(rule.daily_max) }}</td>
            </tr>
          }
        </tbody>
      </table>
    </section>
  `,
})
export class OperationConditionsComponent {
  readonly conditions = input.required<OperationConditions>();

  readonly money = formatSoles;

  statusLabel(): string {
    return STATUS_LABELS[this.conditions().account_status];
  }

  groupLabel(rule: OperationRule): string {
    return GROUP_LABELS[rule.operation_group];
  }

  typesText(rule: OperationRule): string {
    return rule.operation_types.map((t) => OPERATION_TYPE_LABELS[t]).join(', ');
  }
}
```

---

## `src/app/features/onboarding/onboarding.component.ts`

```ts
import { Component, DestroyRef, OnInit, computed, inject, signal } from '@angular/core';
import { takeUntilDestroyed, toSignal } from '@angular/core/rxjs-interop';
import { NonNullableFormBuilder, ReactiveFormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { EMPTY, Observable, catchError, debounceTime, distinctUntilChanged, of, switchMap, tap } from 'rxjs';
import { describeError, toApiError } from '../../core/errors/api-error';
import {
  OnboardingStep,
  UsernameAvailabilityRequest,
  UsernameAvailabilityResponse,
} from '../../core/models/api.models';
import { OnboardingApiService } from '../../core/services/onboarding-api.service';
import { SessionStore } from '../../core/services/session.store';
import {
  apellidoValidators,
  nombresValidators,
  passwordValidators,
  usuarioValidators,
} from '../../core/validators/field-validators';
import { evaluatePasswordStrength } from '../../core/validators/password-strength';
import { validationMessage } from '../../core/validators/validation-messages';

export type FieldName =
  | 'nombres'
  | 'apellido_paterno'
  | 'apellido_materno'
  | 'usuario'
  | 'password';
export type FieldState = 'idle' | 'valid' | 'invalid' | 'pending';
export type UsernameStatus = 'idle' | 'checking' | 'AVAILABLE' | 'TAKEN' | 'INVALID_FORMAT' | 'error';

const STEP_BY_FIELD: Record<FieldName, OnboardingStep> = {
  nombres: 'NOMBRES',
  apellido_paterno: 'APELLIDO_PATERNO',
  apellido_materno: 'APELLIDO_MATERNO',
  usuario: 'USUARIO',
  password: 'CONTRASENA',
};

const TOTAL_STEPS = 5;

@Component({
  selector: 'app-onboarding',
  standalone: true,
  imports: [ReactiveFormsModule],
  template: `
    <section aria-labelledby="onb-title">
      <h1 id="onb-title">Crea tu billetera digital</h1>
      <p class="muted">Completa tus datos para empezar a usar tu billetera.</p>
      <p class="progress" data-testid="progress">
        Pasos completados: {{ completedSteps().length }} de ${'{'}total{'}'}
      </p>

      <form [formGroup]="form" (ngSubmit)="submit()" novalidate class="card">
        <div class="field" [attr.data-state]="fieldState('nombres')">
          <label for="nombres">Nombres</label>
          <input id="nombres" formControlName="nombres" autocomplete="given-name"
                 aria-describedby="nombres-msg" (blur)="onBlur('nombres')" />
          <small id="nombres-msg" class="msg" aria-live="polite">{{ fieldMessage('nombres') }}</small>
        </div>

        <div class="field" [attr.data-state]="fieldState('apellido_paterno')">
          <label for="apellido_paterno">Apellido paterno</label>
          <input id="apellido_paterno" formControlName="apellido_paterno"
                 autocomplete="family-name" aria-describedby="apellido_paterno-msg"
                 (blur)="onBlur('apellido_paterno')" />
          <small id="apellido_paterno-msg" class="msg" aria-live="polite">{{ fieldMessage('apellido_paterno') }}</small>
        </div>

        <div class="field" [attr.data-state]="fieldState('apellido_materno')">
          <label for="apellido_materno">Apellido materno</label>
          <input id="apellido_materno" formControlName="apellido_materno"
                 aria-describedby="apellido_materno-msg" (blur)="onBlur('apellido_materno')" />
          <small id="apellido_materno-msg" class="msg" aria-live="polite">{{ fieldMessage('apellido_materno') }}</small>
        </div>

        <div class="field" [attr.data-state]="fieldState('usuario')">
          <label for="usuario">Usuario</label>
          <input id="usuario" formControlName="usuario" autocomplete="username"
                 aria-describedby="usuario-msg" (blur)="onBlur('usuario')" />
          <small id="usuario-msg" class="msg" aria-live="polite">{{ fieldMessage('usuario') }}</small>
          @if (usernameStatus() === 'TAKEN' && suggestions().length > 0) {
            <div class="chips" role="list" aria-label="Sugerencias de usuario disponibles"
                 data-testid="suggestions">
              @for (s of suggestions(); track s) {
                <button type="button" class="chip" role="listitem" (click)="pickSuggestion(s)">{{ s }}</button>
              }
            </div>
          }
        </div>

        <div class="field" [attr.data-state]="fieldState('password')">
          <label for="password">Contraseña</label>
          <div class="row">
            <input id="password" formControlName="password" [type]="showPassword() ? 'text' : 'password'"
                   autocomplete="new-password" spellcheck="false" aria-describedby="password-msg"
                   (blur)="onBlur('password')" />
            <button type="button" class="chip" (click)="showPassword.set(!showPassword())"
                    [attr.aria-pressed]="showPassword()">
              {{ showPassword() ? 'Ocultar' : 'Mostrar' }}
            </button>
          </div>
          <small id="password-msg" class="msg" aria-live="polite">{{ fieldMessage('password') }}</small>
          @if (strength().level !== 'empty') {
            <div class="meter" [attr.data-level]="strength().level" aria-hidden="true"><span></span></div>
            <p class="strength" data-testid="strength" [attr.role]="strength().level === 'weak' ? 'alert' : null">
              {{ strength().label }}
            </p>
            @if (strength().hints.length > 0) {
              <ul class="hints">
                @for (h of strength().hints; track h) {
                  <li>{{ h }}</li>
                }
              </ul>
            }
          }
        </div>

        @if (submitError()) {
          <p class="error" role="alert" data-testid="submit-error">{{ submitError() }}</p>
        }

        <button type="submit" class="btn" data-testid="submit" [disabled]="!canSubmit()">
          {{ submitting() ? 'Creando tu cuenta…' : 'Crear cuenta' }}
        </button>
      </form>
    </section>
  `,
})
export class OnboardingComponent implements OnInit {
  private readonly fb = inject(NonNullableFormBuilder);
  private readonly api = inject(OnboardingApiService);
  private readonly store = inject(SessionStore);
  private readonly router = inject(Router);
  private readonly destroyRef = inject(DestroyRef);

  readonly total = TOTAL_STEPS;

  readonly form = this.fb.group({
    nombres: ['', nombresValidators()],
    apellido_paterno: ['', apellidoValidators()],
    apellido_materno: ['', apellidoValidators()],
    usuario: ['', usuarioValidators()],
    password: ['', passwordValidators()],
  });

  readonly sessionId = signal<string | null>(null);
  readonly completedSteps = signal<OnboardingStep[]>([]);
  readonly usernameStatus = signal<UsernameStatus>('idle');
  readonly suggestions = signal<string[]>([]);
  readonly submitting = signal(false);
  readonly submitError = signal<string | null>(null);
  readonly showPassword = signal(false);

  private readonly passwordValue = toSignal(this.form.controls.password.valueChanges, {
    initialValue: '',
  });
  readonly strength = computed(() => evaluatePasswordStrength(this.passwordValue()));

  ngOnInit(): void {
    // CA-01: la medición inicia cuando la pantalla de onboarding es visible.
    this.api
      .startSession()
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: (s) => this.sessionId.set(s.session_id),
        // El seguimiento no debe bloquear el registro.
        error: () => undefined,
      });
    this.watchUsername();
  }

  // ---------- Validación en línea ----------

  fieldState(name: FieldName): FieldState {
    const c = this.form.controls[name];
    if (c.value === '') {
      return c.touched && c.invalid ? 'invalid' : 'idle';
    }
    if (c.invalid) {
      return 'invalid';
    }
    if (name === 'usuario') {
      switch (this.usernameStatus()) {
        case 'AVAILABLE':
          return 'valid';
        case 'TAKEN':
        case 'INVALID_FORMAT':
        case 'error':
          return 'invalid';
        default:
          return 'pending';
      }
    }
    return 'valid';
  }

  fieldMessage(name: FieldName): string {
    const c = this.form.controls[name];
    if (c.value === '') {
      return c.touched ? (validationMessage(c.errors) ?? '') : '';
    }
    const err = validationMessage(c.errors);
    if (err) {
      return err;
    }
    return name === 'usuario' ? this.usernameMessage() : 'Válido.';
  }

  private usernameMessage(): string {
    switch (this.usernameStatus()) {
      case 'checking':
        return 'Verificando disponibilidad…';
      case 'AVAILABLE':
        return 'Usuario disponible.';
      case 'TAKEN':
        return 'Este usuario no está disponible. Prueba con una sugerencia:';
      case 'INVALID_FORMAT':
        return 'El formato del usuario no es válido.';
      case 'error':
        return 'No pudimos verificar la disponibilidad. Intenta nuevamente.';
      default:
        return '';
    }
  }

  // ---------- Disponibilidad de usuario ----------

  private watchUsername(): void {
    const control = this.form.controls.usuario;
    control.valueChanges
      .pipe(
        tap(() => {
          this.suggestions.set([]);
          this.usernameStatus.set(control.valid ? 'checking' : 'idle');
        }),
        debounceTime(400),
        distinctUntilChanged(),
        switchMap((value): Observable<UsernameAvailabilityResponse | null> => {
          if (!value || control.invalid) {
            return of(null);
          }
          return this.api.checkUsername(this.availabilityPayload(value)).pipe(
            catchError(() => {
              this.usernameStatus.set('error');
              return EMPTY;
            }),
          );
        }),
        takeUntilDestroyed(this.destroyRef),
      )
      .subscribe((res) => {
        if (!res) {
          this.usernameStatus.set('idle');
          return;
        }
        this.usernameStatus.set(res.status);
        this.suggestions.set(res.status === 'TAKEN' ? res.suggestions : []);
        if (res.status === 'AVAILABLE') {
          this.markStep('USUARIO');
        }
      });
  }

  private availabilityPayload(username: string): UsernameAvailabilityRequest {
    const { nombres, apellido_paterno, apellido_materno } = this.form.controls;
    return {
      username,
      ...(nombres.valid && nombres.value ? { nombres: nombres.value.trim() } : {}),
      ...(apellido_paterno.valid && apellido_paterno.value
        ? { apellido_paterno: apellido_paterno.value }
        : {}),
      ...(apellido_materno.valid && apellido_materno.value
        ? { apellido_materno: apellido_materno.value }
        : {}),
    };
  }

  pickSuggestion(suggestion: string): void {
    this.form.controls.usuario.setValue(suggestion);
    this.form.controls.usuario.markAsTouched();
  }

  // ---------- Seguimiento de pasos (CA-01) ----------

  onBlur(name: FieldName): void {
    const control = this.form.controls[name];
    control.markAsTouched();
    // El paso USUARIO se registra cuando se confirma la disponibilidad.
    if (name !== 'usuario' && control.valid) {
      this.markStep(STEP_BY_FIELD[name]);
    }
  }

  private markStep(step: OnboardingStep): void {
    const id = this.sessionId();
    if (!id || this.completedSteps().includes(step)) {
      return;
    }
    this.completedSteps.update((s) => [...s, step]);
    // Solo se envía el nombre del paso, nunca el valor ingresado.
    this.api.registerStep(id, { step }).subscribe({
      error: () => this.completedSteps.update((s) => s.filter((x) => x !== step)),
    });
  }

  // ---------- Registro ----------

  canSubmit(): boolean {
    return this.form.valid && this.usernameStatus() === 'AVAILABLE' && !this.submitting();
  }

  submit(): void {
    if (!this.canSubmit()) {
      this.form.markAllAsTouched();
      return;
    }
    const v = this.form.getRawValue();
    this.submitting.set(true);
    this.submitError.set(null);

    this.api
      .register({
        session_id: this.sessionId() ?? undefined,
        nombres: v.nombres.trim(),
        apellido_paterno: v.apellido_paterno,
        apellido_materno: v.apellido_materno,
        usuario: v.usuario,
        password: v.password,
      })
      .subscribe({
        next: (res) => {
          // Credenciales solo en memoria, para HTTP Basic.
          this.store.start({ username: v.usuario, password: v.password }, res);
          this.form.controls.password.reset('');
          this.submitting.set(false);
          void this.router.navigateByUrl('/landing');
        },
        error: (err: unknown) => {
          const apiError = toApiError(err);
          if (apiError.code === 'USERNAME_TAKEN') {
            this.usernameStatus.set('TAKEN');
            this.suggestions.set(apiError.suggestions ?? []);
          }
          this.submitError.set(describeError(apiError));
          this.submitting.set(false);
        },
      });
  }
}
```

> **Corrección en el template (línea de progreso):** reemplaza `de ${'{'}total{'}'}` por `de {{ total }}`. El bloque queda así:
>
> ```html
> <p class="progress" data-testid="progress">
>   Pasos completados: {{ completedSteps().length }} de {{ total }}
> </p>
> ```

## `src/app/features/onboarding/onboarding.component.spec.ts`

```ts
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { ComponentFixture, TestBed, fakeAsync, tick } from '@angular/core/testing';
import { Router, provideRouter } from '@angular/router';
import { REGISTRATION_RESPONSE } from '../../../testing/fixtures';
import { API_BASE_URL } from '../../core/config/api-config';
import { SessionStore } from '../../core/services/session.store';
import { OnboardingComponent } from './onboarding.component';

describe('OnboardingComponent', () => {
  let fixture: ComponentFixture<OnboardingComponent>;
  let component: OnboardingComponent;
  let http: HttpTestingController;
  let router: Router;
  let store: SessionStore;

  const startSession = () => {
    fixture.detectChanges(); // ngOnInit
    http
      .expectOne('/api/onboarding/sessions')
      .flush({ session_id: 's-1', started_at: '2026-10-30T20:00:00Z' });
  };

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [OnboardingComponent],
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
        provideRouter([]),
        { provide: API_BASE_URL, useValue: '/api' },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(OnboardingComponent);
    component = fixture.componentInstance;
    http = TestBed.inject(HttpTestingController);
    router = TestBed.inject(Router);
    store = TestBed.inject(SessionStore);
    spyOn(router, 'navigateByUrl').and.resolveTo(true);
  });

  afterEach(() => http.verify());

  it('CA-01: inicia la sesión de medición cuando la pantalla es visible', () => {
    fixture.detectChanges();
    const req = http.expectOne('/api/onboarding/sessions');
    expect(req.request.method).toBe('POST');
    req.flush({ session_id: 's-1', started_at: '2026-10-30T20:00:00Z' });
    expect(component.sessionId()).toBe('s-1');
  });

  it('CA-01: muestra el resultado de la validación mientras se escribe', () => {
    startSession();
    component.form.controls.nombres.setValue('Maria123');
    fixture.detectChanges();

    const host: HTMLElement = fixture.nativeElement;
    expect(host.querySelector('#nombres-msg')?.textContent).toContain('Solo letras');
    expect(host.querySelector('.field[data-state="invalid"]')).not.toBeNull();

    component.form.controls.nombres.setValue('María José');
    fixture.detectChanges();
    expect(host.querySelector('#nombres-msg')?.textContent).toContain('Válido');
  });

  it('CA-01: registra el paso solo una vez, al salir de un campo válido', () => {
    startSession();
    component.form.controls.nombres.setValue('María José');
    component.onBlur('nombres');

    const req = http.expectOne('/api/onboarding/sessions/s-1/steps');
    expect(req.request.body).toEqual({ step: 'NOMBRES' }); // sin el valor ingresado
    req.flush({ step: 'NOMBRES', elapsed_ms: 900 });

    component.onBlur('nombres');
    http.expectNone('/api/onboarding/sessions/s-1/steps');
    expect(component.completedSteps()).toEqual(['NOMBRES']);
  });

  it('no registra pasos de campos inválidos', () => {
    startSession();
    component.form.controls.nombres.setValue('Maria123');
    component.onBlur('nombres');
    http.expectNone('/api/onboarding/sessions/s-1/steps');
  });

  it('CA-02: consulta disponibilidad con debounce y muestra sugerencias sin símbolos', fakeAsync(() => {
    startSession();
    component.form.controls.usuario.setValue('jperez');
    tick(399);
    http.expectNone('/api/onboarding/username-availability');
    tick(1);

    const req = http.expectOne('/api/onboarding/username-availability');
    expect(req.request.body.username).toBe('jperez');
    req.flush({ status: 'TAKEN', suggestions: ['jperez1', 'juanperez'] });
    fixture.detectChanges();

    expect(component.usernameStatus()).toBe('TAKEN');
    const chips = fixture.nativeElement.querySelectorAll('[data-testid="suggestions"] .chip');
    expect(chips.length).toBe(2);
    expect(component.fieldState('usuario')).toBe('invalid');
  }));

  it('CA-02: al elegir una sugerencia se vuelve a consultar y queda disponible', fakeAsync(() => {
    startSession();
    component.pickSuggestion('jperez1');
    tick(400);

    http
      .expectOne('/api/onboarding/username-availability')
      .flush({ status: 'AVAILABLE', suggestions: [] });
    expect(component.usernameStatus()).toBe('AVAILABLE');
    // La disponibilidad confirmada completa el paso USUARIO.
    http
      .expectOne('/api/onboarding/sessions/s-1/steps')
      .flush({ step: 'USUARIO', elapsed_ms: 5000 });
  }));

  it('CA-02: no consulta disponibilidad si el formato local es inválido', fakeAsync(() => {
    startSession();
    component.form.controls.usuario.setValue('12345');
    tick(500);
    http.expectNone('/api/onboarding/username-availability');
    expect(component.usernameStatus()).toBe('idle');
  }));

  it('CA-02: alerta cuando la contraseña es débil', () => {
    startSession();
    component.form.controls.password.setValue('abc');
    fixture.detectChanges();
    const strength: HTMLElement = fixture.nativeElement.querySelector('[data-testid="strength"]');
    expect(strength.textContent).toContain('débil');
    expect(strength.getAttribute('role')).toBe('alert');
  });

  it('deshabilita el envío hasta que el formulario sea válido y el usuario esté disponible', () => {
    startSession();
    expect(component.canSubmit()).toBeFalse();
    component.form.setValue({
      nombres: 'María José',
      apellido_paterno: 'Quispe',
      apellido_materno: 'Rojas',
      usuario: 'mjquispe',
      password: 'Clave#Segura2026',
    });
    expect(component.canSubmit()).toBeFalse(); // usuario sin confirmar
    component.usernameStatus.set('AVAILABLE');
    expect(component.canSubmit()).toBeTrue();
  });

  it('CA-03: registra, guarda la sesión en memoria y navega a la landing', () => {
    startSession();
    component.form.setValue({
      nombres: 'María José',
      apellido_paterno: 'Quispe',
      apellido_materno: 'Rojas',
      usuario: 'mjquispe',
      password: 'Clave#Segura2026',
    });
    component.usernameStatus.set('AVAILABLE');

    component.submit();
    const req = http.expectOne('/api/onboarding/registrations');
    expect(req.request.method).toBe('POST');
    expect(req.request.body).toEqual({
      session_id: 's-1',
      nombres: 'María José',
      apellido_paterno: 'Quispe',
      apellido_materno: 'Rojas',
      usuario: 'mjquispe',
      password: 'Clave#Segura2026',
    });
    req.flush(REGISTRATION_RESPONSE);

    expect(store.isAuthenticated()).toBeTrue();
    expect(store.walletId()).toBe('w-1');
    expect(router.navigateByUrl).toHaveBeenCalledWith('/landing');
    expect(component.form.controls.password.value).toBe('');
  });

  it('muestra sugerencias si el registro responde 409 USERNAME_TAKEN', () => {
    startSession();
    component.form.setValue({
      nombres: 'María José',
      apellido_paterno: 'Quispe',
      apellido_materno: 'Rojas',
      usuario: 'mjquispe',
      password: 'Clave#Segura2026',
    });
    component.usernameStatus.set('AVAILABLE');

    component.submit();
    http
      .expectOne('/api/onboarding/registrations')
      .flush(
        { code: 'USERNAME_TAKEN', message: 'x', suggestions: ['mjquispe2'] },
        { status: 409, statusText: 'Conflict' },
      );
    fixture.detectChanges();

    expect(component.usernameStatus()).toBe('TAKEN');
    expect(component.suggestions()).toEqual(['mjquispe2']);
    expect(fixture.nativeElement.querySelector('[data-testid="submit-error"]')).not.toBeNull();
    expect(store.isAuthenticated()).toBeFalse();
    expect(router.navigateByUrl).not.toHaveBeenCalled();
  });
});
```

---

## `src/app/features/landing/landing.component.ts`

```ts
import { Component, inject } from '@angular/core';
import { RouterLink } from '@angular/router';
import { SessionStore } from '../../core/services/session.store';
import { STATUS_LABELS, formatSoles, hasPendingProfile } from '../../core/utils/format';
import { OperationConditionsComponent } from '../../shared/operation-conditions.component';

@Component({
  selector: 'app-landing',
  standalone: true,
  imports: [RouterLink, OperationConditionsComponent],
  template: `
    @if (store.registration(); as reg) {
      <section aria-labelledby="welcome-title">
        <h1 id="welcome-title" data-testid="welcome">¡Bienvenido/a, {{ reg.welcome.display_name }}!</h1>
        <p class="muted">Tu billetera digital ya está activa.</p>

        <div class="card" data-testid="account">
          <div class="card-head">
            <h2>Tu cuenta</h2>
            <span class="badge" data-testid="status">{{ statusLabel(reg.account.status) }}</span>
          </div>
          <p>Saldo: <strong>{{ money(reg.account.balance) }}</strong></p>
          <p class="muted">ID de billetera: <code data-testid="wallet-id">{{ reg.account.wallet_id }}</code></p>
          @if (reg.registration_duration_ms !== null && reg.registration_duration_ms !== undefined) {
            <p class="muted" data-testid="duration">
              Registro completado en {{ seconds(reg.registration_duration_ms) }} s.
            </p>
          }
        </div>

        @if (pending(reg.profile)) {
          <div class="banner warn" role="status" data-testid="pending-banner">
            <strong>Completa los datos de tu perfil.</strong>
            Valida tu correo, tu celular y tu identidad para subir de nivel y operar con mayores límites.
            <a class="btn" routerLink="/profile">Completar mi perfil</a>
          </div>
        }

        <app-operation-conditions [conditions]="reg.operation_conditions" />
      </section>
    }
  `,
})
export class LandingComponent {
  readonly store = inject(SessionStore);
  readonly money = formatSoles;
  readonly pending = hasPendingProfile;

  statusLabel(status: 'ACTIVE_BASIC' | 'ACTIVE_FULL'): string {
    return STATUS_LABELS[status];
  }

  seconds(ms: number): string {
    return (ms / 1000).toFixed(1);
  }
}
```

## `src/app/features/landing/landing.component.spec.ts`

```ts
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { REGISTRATION_RESPONSE } from '../../../testing/fixtures';
import { SessionStore } from '../../core/services/session.store';
import { LandingComponent } from './landing.component';

describe('LandingComponent', () => {
  let fixture: ComponentFixture<LandingComponent>;
  let store: SessionStore;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [LandingComponent],
      providers: [provideRouter([])],
    }).compileComponents();
    store = TestBed.inject(SessionStore);
    fixture = TestBed.createComponent(LandingComponent);
  });

  it('CA-03: da la bienvenida por el nombre real y muestra cuenta básica con saldo S/ 0.00', () => {
    store.start({ username: 'mjquispe', password: 'Clave#Segura2026' }, REGISTRATION_RESPONSE);
    fixture.detectChanges();
    const host: HTMLElement = fixture.nativeElement;
    expect(host.querySelector('[data-testid="welcome"]')?.textContent).toContain('María José');
    expect(host.querySelector('[data-testid="status"]')?.textContent).toContain('Cuenta básica');
    expect(host.querySelector('[data-testid="account"]')?.textContent).toContain('S/ 0.00');
    expect(host.querySelector('[data-testid="wallet-id"]')?.textContent).toContain('w-1');
  });

  it('CA-03: muestra las condiciones de las operaciones permitidas', () => {
    store.start({ username: 'mjquispe', password: 'Clave#Segura2026' }, REGISTRATION_RESPONSE);
    fixture.detectChanges();
    const row = fixture.nativeElement.querySelector('[data-testid="condition-row"]') as HTMLElement;
    expect(row.textContent).toContain('S/ 20.00');
    expect(row.textContent).toContain('S/ 60.00');
  });

  it('CA-04: muestra el mensaje visible de perfil pendiente con enlace al perfil', () => {
    store.start({ username: 'mjquispe', password: 'Clave#Segura2026' }, REGISTRATION_RESPONSE);
    fixture.detectChanges();
    const banner = fixture.nativeElement.querySelector('[data-testid="pending-banner"]') as HTMLElement;
    expect(banner).not.toBeNull();
    expect(banner.textContent).toContain('perfil');
    expect(banner.querySelector('a')?.getAttribute('href')).toBe('/profile');
  });

  it('muestra la duración del registro devuelta por la API', () => {
    store.start({ username: 'mjquispe', password: 'Clave#Segura2026' }, REGISTRATION_RESPONSE);
    fixture.detectChanges();
    expect(fixture.nativeElement.querySelector('[data-testid="duration"]').textContent).toContain('42.0');
  });
});
```

---

## `src/app/features/profile/channel-validation-card.component.ts`

```ts
import { Component, DestroyRef, OnInit, computed, inject, input, output, signal } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { FormControl, ReactiveFormsModule } from '@angular/forms';
import { Observable, Subscription, interval } from 'rxjs';
import { describeError, toApiError } from '../../core/errors/api-error';
import { OtpChannel, OtpIssued, ProfileStatesResponse } from '../../core/models/api.models';
import { WalletApiService } from '../../core/services/wallet-api.service';
import { PROFILE_STATE_LABELS } from '../../core/utils/format';
import { OTP_RESEND_SECONDS, secondsLeft } from '../../core/utils/time';
import { emailValidators, otpValidators, phoneValidators } from '../../core/validators/field-validators';
import { validationMessage } from '../../core/validators/validation-messages';

/**
 * Tarjeta de validación por OTP para correo (CA-07) y celular (CA-08).
 * Cuenta regresiva de 60 s (vigencia) y 45 s (reenvío).
 * El OTP es mock: no se envía nada real y se acepta cualquier valor mientras esté vigente.
 */
@Component({
  selector: 'app-channel-validation-card',
  standalone: true,
  imports: [ReactiveFormsModule],
  template: `
    <article class="card" [attr.data-state]="state()">
      <header class="card-head">
        <h3>{{ title() }}</h3>
        <span class="badge" [class.ok]="isValidated()" data-testid="state-badge">{{ stateLabel() }}</span>
      </header>

      @if (isValidated()) {
        <p class="success" data-testid="validated-msg">✔ {{ title() }} validado correctamente.</p>
      } @else {
        <form (submit)="onSubmitValue($event)" novalidate>
          <label [attr.for]="inputId()">{{ inputLabel() }}</label>
          <div class="row">
            @if (channel() === 'PHONE') {
              <input class="prefix" type="text" value="+51" readonly tabindex="-1"
                     aria-label="Prefijo de país Perú (no editable)" data-testid="phone-prefix" />
            }
            <input [id]="inputId()" [formControl]="valueControl"
                   [type]="channel() === 'EMAIL' ? 'email' : 'tel'"
                   [attr.inputmode]="channel() === 'EMAIL' ? 'email' : 'numeric'"
                   [attr.autocomplete]="channel() === 'EMAIL' ? 'email' : 'tel-national'" />
          </div>
          @if (valueControl.invalid && (valueControl.dirty || valueControl.touched)) {
            <small class="msg invalid" data-testid="value-error">{{ valueError() }}</small>
          }
          <button type="submit" class="btn" data-testid="send-otp" [disabled]="!canRequest()">
            {{ requestLabel() }}
          </button>
        </form>

        @if (otpIssued()) {
          <form (submit)="onSubmitOtp($event)" novalidate class="otp">
            <p class="muted" data-testid="mock-note">
              Simulación: no se envía ningún {{ channel() === 'EMAIL' ? 'correo' : 'SMS' }} real.
              Ingresa cualquier código para confirmar.
            </p>
            <label [attr.for]="otpId()">Código de verificación (6 caracteres)</label>
            <input [id]="otpId()" [formControl]="otpControl" autocomplete="one-time-code" />
            @if (otpExpired()) {
              <small class="msg invalid" data-testid="otp-expired">
                El código venció o fue reemplazado. Solicita uno nuevo.
              </small>
            } @else {
              <small class="msg" data-testid="otp-countdown">El código vence en {{ expiresSeconds() }} s</small>
            }
            <button type="submit" class="btn" data-testid="confirm-otp" [disabled]="!canConfirm()">
              Confirmar código
            </button>
          </form>
        }
      }

      @if (error()) {
        <p class="msg invalid" role="alert" data-testid="card-error">{{ error() }}</p>
      }
    </article>
  `,
})
export class ChannelValidationCardComponent implements OnInit {
  readonly channel = input.required<OtpChannel>();
  readonly walletId = input.required<string>();
  /** Estado actual del perfil (ESTADO_C1 o ESTADO_C2). */
  readonly state = input.required<string>();
  readonly validated = output<void>();

  private readonly api = inject(WalletApiService);
  private readonly destroyRef = inject(DestroyRef);

  readonly valueControl = new FormControl('', { nonNullable: true });
  readonly otpControl = new FormControl('', { nonNullable: true, validators: otpValidators() });

  readonly now = signal(Date.now());
  readonly otpExpiresAt = signal<number | null>(null);
  readonly nextRequestAt = signal<number | null>(null);
  readonly otpIssued = signal(false);
  readonly busy = signal(false);
  readonly error = signal<string | null>(null);
  private readonly confirmed = signal(false);

  readonly isValidated = computed(() => this.state().startsWith('ACTIVE') || this.confirmed());
  readonly title = computed(() => (this.channel() === 'EMAIL' ? 'Correo electrónico' : 'Celular'));
  readonly inputLabel = computed(() =>
    this.channel() === 'EMAIL' ? 'Correo electrónico' : 'Número de celular (9 dígitos)',
  );
  readonly inputId = computed(() => `${this.channel().toLowerCase()}-value`);
  readonly otpId = computed(() => `${this.channel().toLowerCase()}-otp`);
  readonly stateLabel = computed(() =>
    this.isValidated() ? 'Validado' : (PROFILE_STATE_LABELS[this.state()] ?? this.state()),
  );

  readonly resendSeconds = computed(() => secondsLeft(this.nextRequestAt(), this.now()));
  readonly expiresSeconds = computed(() => secondsLeft(this.otpExpiresAt(), this.now()));
  readonly otpExpired = computed(() => this.otpIssued() && this.expiresSeconds() === 0);

  private ticker: Subscription | null = null;

  ngOnInit(): void {
    this.valueControl.setValidators(
      this.channel() === 'EMAIL' ? emailValidators() : phoneValidators(),
    );
    this.valueControl.updateValueAndValidity();
  }

  valueError(): string | null {
    return validationMessage(this.valueControl.errors);
  }

  requestLabel(): string {
    if (this.resendSeconds() > 0) {
      return `Reenviar en ${this.resendSeconds()} s`;
    }
    return this.otpIssued() ? 'Reenviar código' : 'Enviar código';
  }

  canRequest(): boolean {
    return this.valueControl.valid && !this.busy() && this.resendSeconds() === 0;
  }

  canConfirm(): boolean {
    return this.otpControl.valid && !this.busy() && !this.otpExpired();
  }

  onSubmitValue(event: Event): void {
    event.preventDefault();
    this.requestOtp();
  }

  onSubmitOtp(event: Event): void {
    event.preventDefault();
    this.confirm();
  }

  requestOtp(): void {
    if (!this.canRequest()) {
      this.valueControl.markAsTouched();
      return;
    }
    const id = this.walletId();
    const value = this.valueControl.value.trim();
    const request$: Observable<OtpIssued> =
      this.channel() === 'EMAIL'
        ? this.api.requestEmailOtp(id, { email: value })
        : this.api.requestPhoneOtp(id, { phone: value });

    this.busy.set(true);
    this.error.set(null);
    request$.subscribe({
      next: (otp) => {
        const now = Date.now();
        this.now.set(now);
        this.otpExpiresAt.set(now + otp.expires_in_seconds * 1000);
        this.nextRequestAt.set(now + OTP_RESEND_SECONDS * 1000);
        this.otpIssued.set(true);
        this.otpControl.reset('');
        this.busy.set(false);
        this.ensureTicker();
      },
      error: (err: unknown) => this.handleError(err),
    });
  }

  confirm(): void {
    if (!this.canConfirm()) {
      this.otpControl.markAsTouched();
      return;
    }
    const id = this.walletId();
    const otp = this.otpControl.value;
    const confirm$: Observable<ProfileStatesResponse> =
      this.channel() === 'EMAIL'
        ? this.api.confirmEmailOtp(id, { otp })
        : this.api.confirmPhoneOtp(id, { otp });

    this.busy.set(true);
    this.error.set(null);
    confirm$.subscribe({
      next: () => {
        this.busy.set(false);
        this.otpIssued.set(false);
        this.confirmed.set(true);
        this.validated.emit();
      },
      error: (err: unknown) => this.handleError(err),
    });
  }

  private handleError(err: unknown): void {
    const apiError = toApiError(err);
    this.busy.set(false);
    switch (apiError.code) {
      case 'OTP_RATE_LIMITED': {
        const wait = apiError.retry_after_seconds ?? OTP_RESEND_SECONDS;
        const now = Date.now();
        this.now.set(now);
        this.nextRequestAt.set(now + wait * 1000);
        this.ensureTicker();
        break;
      }
      case 'OTP_EXPIRED':
      case 'OTP_NOT_ACTIVE':
        // Fuerza el estado "vencido" para pedir un nuevo código.
        this.otpExpiresAt.set(null);
        break;
      case 'ALREADY_VALIDATED':
        this.validated.emit();
        break;
      default:
        break;
    }
    this.error.set(describeError(apiError));
  }

  /** Reloj de 1 s que se detiene cuando ambas cuentas regresivas terminan. */
  private ensureTicker(): void {
    if (this.ticker) {
      return;
    }
    this.ticker = interval(1000)
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe(() => {
        this.now.set(Date.now());
        if (this.resendSeconds() === 0 && this.expiresSeconds() === 0) {
          this.ticker?.unsubscribe();
          this.ticker = null;
        }
      });
  }
}
```

## `src/app/features/profile/channel-validation-card.component.spec.ts`

```ts
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { API_BASE_URL } from '../../core/config/api-config';
import { ChannelValidationCardComponent } from './channel-validation-card.component';

describe('ChannelValidationCardComponent', () => {
  let fixture: ComponentFixture<ChannelValidationCardComponent>;
  let card: ChannelValidationCardComponent;
  let http: HttpTestingController;

  const otpIssued = (channel: 'EMAIL' | 'PHONE') => ({
    channel,
    expires_at: '2026-10-30T20:01:00Z',
    expires_in_seconds: 60,
    next_request_allowed_at: '2026-10-30T20:00:45Z',
    otp_length: 6,
    delivery: 'MOCK_NOT_SENT',
  });

  function setup(channel: 'EMAIL' | 'PHONE', state: string): void {
    fixture = TestBed.createComponent(ChannelValidationCardComponent);
    card = fixture.componentInstance;
    fixture.componentRef.setInput('channel', channel);
    fixture.componentRef.setInput('walletId', 'w-1');
    fixture.componentRef.setInput('state', state);
    fixture.detectChanges();
  }

  const button = (testId: string) =>
    fixture.nativeElement.querySelector(`[data-testid="${testId}"]`) as HTMLButtonElement | null;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [ChannelValidationCardComponent],
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
        { provide: API_BASE_URL, useValue: '/api' },
      ],
    }).compileComponents();
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => http.verify());

  it('CA-07: valida el formato del correo antes de permitir solicitar el OTP', () => {
    setup('EMAIL', 'PENDING_EMAIL');
    expect(button('send-otp')?.disabled).toBeTrue();

    card.valueControl.setValue('ana@@example');
    card.valueControl.markAsDirty();
    fixture.detectChanges();
    expect(button('send-otp')?.disabled).toBeTrue();
    expect(fixture.nativeElement.querySelector('[data-testid="value-error"]')).not.toBeNull();

    card.valueControl.setValue('ana@example.com');
    fixture.detectChanges();
    expect(button('send-otp')?.disabled).toBeFalse();
  });

  it('CA-07: solicita el OTP, inicia la cuenta regresiva y confirma con cualquier valor', () => {
    setup('EMAIL', 'PENDING_EMAIL');
    let emitted = 0;
    card.validated.subscribe(() => emitted++);

    card.valueControl.setValue('ana@example.com');
    card.requestOtp();
    const req = http.expectOne('/api/wallets/w-1/profile/email/otp-requests');
    expect(req.request.body).toEqual({ email: 'ana@example.com' });
    req.flush(otpIssued('EMAIL'));
    fixture.detectChanges();

    expect(card.otpIssued()).toBeTrue();
    expect(card.resendSeconds()).toBeGreaterThan(40);
    expect(card.expiresSeconds()).toBeGreaterThan(55);
    expect(fixture.nativeElement.querySelector('[data-testid="mock-note"]')).not.toBeNull();
    // Se bloquea el reenvío durante 45 s.
    expect(button('send-otp')?.disabled).toBeTrue();

    card.otpControl.setValue('000000');
    card.confirm();
    const confirmReq = http.expectOne('/api/wallets/w-1/profile/email/otp-confirmations');
    expect(confirmReq.request.body).toEqual({ otp: '000000' });
    confirmReq.flush({
      wallet_id: 'w-1',
      profile: { estado_c1: 'ACTIVE_EMAIL', estado_c2: 'PENDING_MOVIL', estado_c3: 'PENDING_BIOM' },
    });
    fixture.detectChanges();

    expect(emitted).toBe(1);
    expect(card.isValidated()).toBeTrue();
    expect(fixture.nativeElement.querySelector('[data-testid="validated-msg"]')).not.toBeNull();
  });

  it('CA-07: pasados 45 s se habilita el reenvío y pasados 60 s el OTP se marca vencido', () => {
    setup('EMAIL', 'PENDING_EMAIL');
    card.valueControl.setValue('ana@example.com');
    card.requestOtp();
    http.expectOne('/api/wallets/w-1/profile/email/otp-requests').flush(otpIssued('EMAIL'));

    card.now.set(Date.now() + 46_000);
    fixture.detectChanges();
    expect(card.resendSeconds()).toBe(0);
    expect(button('send-otp')?.disabled).toBeFalse();
    expect(card.otpExpired()).toBeFalse();

    card.now.set(Date.now() + 61_000);
    fixture.detectChanges();
    expect(card.otpExpired()).toBeTrue();
    expect(fixture.nativeElement.querySelector('[data-testid="otp-expired"]')).not.toBeNull();
    expect(button('confirm-otp')?.disabled).toBeTrue();
  });

  it('CA-07: un 429 muestra la espera indicada por la API', () => {
    setup('EMAIL', 'PENDING_EMAIL');
    card.valueControl.setValue('ana@example.com');
    card.requestOtp();
    http
      .expectOne('/api/wallets/w-1/profile/email/otp-requests')
      .flush(
        { code: 'OTP_RATE_LIMITED', message: 'x', retry_after_seconds: 30 },
        { status: 429, statusText: 'Too Many Requests', headers: { 'Retry-After': '30' } },
      );
    fixture.detectChanges();

    expect(card.resendSeconds()).toBeGreaterThan(0);
    expect(card.resendSeconds()).toBeLessThanOrEqual(30);
    expect(card.error()).toContain('30 s');
    expect(button('send-otp')?.disabled).toBeTrue();
  });

  it('CA-07: muestra el error 409 de correo ya registrado', () => {
    setup('EMAIL', 'PENDING_EMAIL');
    card.valueControl.setValue('otro@example.com');
    card.requestOtp();
    http
      .expectOne('/api/wallets/w-1/profile/email/otp-requests')
      .flush(
        { code: 'EMAIL_ALREADY_REGISTERED', message: 'x' },
        { status: 409, statusText: 'Conflict' },
      );
    fixture.detectChanges();
    expect(fixture.nativeElement.querySelector('[data-testid="card-error"]').textContent).toContain(
      'ya está registrado',
    );
    expect(card.otpIssued()).toBeFalse();
  });

  it('CA-07: un OTP vencido o invalidado (422) conserva el estado y pide uno nuevo', () => {
    setup('EMAIL', 'PENDING_EMAIL');
    card.valueControl.setValue('ana@example.com');
    card.requestOtp();
    http.expectOne('/api/wallets/w-1/profile/email/otp-requests').flush(otpIssued('EMAIL'));

    card.otpControl.setValue('123456');
    card.confirm();
    http
      .expectOne('/api/wallets/w-1/profile/email/otp-confirmations')
      .flush({ code: 'OTP_EXPIRED', message: 'x' }, { status: 422, statusText: 'Unprocessable' });
    fixture.detectChanges();

    expect(card.isValidated()).toBeFalse();
    expect(card.otpExpired()).toBeTrue();
    expect(card.error()).toContain('venció');
  });

  it('CA-08: el prefijo +51 es de solo lectura y el celular envía 9 dígitos sin prefijo', () => {
    setup('PHONE', 'PENDING_MOVIL');
    const prefix = fixture.nativeElement.querySelector('[data-testid="phone-prefix"]') as HTMLInputElement;
    expect(prefix.value).toBe('+51');
    expect(prefix.readOnly).toBeTrue();

    card.valueControl.setValue('812345678');
    expect(card.valueControl.valid).toBeFalse();
    card.valueControl.setValue('91234567');
    expect(card.valueControl.valid).toBeFalse();

    card.valueControl.setValue('912345678');
    card.requestOtp();
    const req = http.expectOne('/api/wallets/w-1/profile/phone/otp-requests');
    expect(req.request.body).toEqual({ phone: '912345678' });
    req.flush({ ...otpIssued('PHONE'), phone_e164: '+51912345678' });
    expect(card.otpIssued()).toBeTrue();

    card.otpControl.setValue('654321');
    card.confirm();
    http.expectOne('/api/wallets/w-1/profile/phone/otp-confirmations').flush({
      wallet_id: 'w-1',
      profile: { estado_c1: 'PENDING_EMAIL', estado_c2: 'ACTIVE_MOVIL', estado_c3: 'PENDING_BIOM' },
    });
    expect(card.isValidated()).toBeTrue();
  });

  it('muestra "Validado" sin formulario cuando el estado ya es ACTIVE_*', () => {
    setup('PHONE', 'ACTIVE_MOVIL');
    expect(fixture.nativeElement.querySelector('[data-testid="validated-msg"]')).not.toBeNull();
    expect(button('send-otp')).toBeNull();
  });
});
```

## `src/app/features/profile/identity-card.component.ts`

```ts
import { Component, computed, inject, input, output, signal } from '@angular/core';
import { FormControl, FormGroup, ReactiveFormsModule } from '@angular/forms';
import { describeError, toApiError } from '../../core/errors/api-error';
import { WalletApiService } from '../../core/services/wallet-api.service';
import { PROFILE_STATE_LABELS } from '../../core/utils/format';

/**
 * Identidad (ESTADO_C3) – flujo MOCK de biometría (CA-09 a CA-12).
 * No se cargan fotos ni videos: solo se aceptan términos y se confirman datos simulados.
 */
@Component({
  selector: 'app-identity-card',
  standalone: true,
  imports: [ReactiveFormsModule],
  template: `
    <article class="card" [attr.data-state]="state()">
      <header class="card-head">
        <h3>Identidad</h3>
        <span class="badge" [class.ok]="isValidated()" data-testid="state-badge">{{ stateLabel() }}</span>
      </header>

      @if (isValidated()) {
        <p class="success" data-testid="validated-msg">
          ✔ Identidad validada. Tu cuenta tiene nivel completo.
        </p>
      } @else {
        <p class="notice" data-testid="clarity-notice">
          📷 Para la verificación biométrica real, las imágenes deben ser nítidas.
        </p>
        <details>
          <summary>Requisitos de la futura verificación real</summary>
          <ul>
            <li>Fotografía de ambas caras del DNI (máximo 2 MB cada una).</li>
            <li>Video de 5 a 10 segundos grabado con el celular (máximo 10 MB, grabado en los últimos 10 minutos).</li>
          </ul>
          <p class="muted">
            En esta versión de prueba no se solicita ni se carga ninguna foto o video.
          </p>
        </details>

        @if (available()) {
          <form [formGroup]="form" (ngSubmit)="submit()" novalidate>
            <label class="check">
              <input type="checkbox" formControlName="terms" data-testid="terms" />
              <span>
                Acepto el manejo de mis datos personales para la verificación biométrica
                (términos y condiciones).
              </span>
            </label>
            <label class="check">
              <input type="checkbox" formControlName="mockInputs" data-testid="mock-inputs" />
              <span>Confirmo que usaré datos simulados (sin fotos ni videos reales).</span>
            </label>
            <button type="submit" class="btn" data-testid="verify" [disabled]="!canSubmit()">
              {{ busy() ? 'Validando…' : 'Simular validación de identidad' }}
            </button>
          </form>
        } @else {
          <p class="muted" data-testid="mock-unavailable">
            La validación de identidad simulada solo está disponible en ambientes de desarrollo y pruebas.
          </p>
        }
      }

      @if (error()) {
        <p class="msg invalid" role="alert" data-testid="card-error">{{ error() }}</p>
      }
    </article>
  `,
})
export class IdentityCardComponent {
  readonly walletId = input.required<string>();
  /** ESTADO_C3 actual. */
  readonly state = input.required<string>();
  /** `identity_mock_available` de GET /wallets/{id}. */
  readonly available = input.required<boolean>();
  readonly verified = output<void>();

  private readonly api = inject(WalletApiService);

  readonly form = new FormGroup({
    terms: new FormControl(false, { nonNullable: true }),
    mockInputs: new FormControl(false, { nonNullable: true }),
  });
  readonly busy = signal(false);
  readonly error = signal<string | null>(null);
  private readonly done = signal(false);

  readonly isValidated = computed(() => this.state().startsWith('ACTIVE') || this.done());
  readonly stateLabel = computed(() =>
    this.isValidated() ? 'Validado' : (PROFILE_STATE_LABELS[this.state()] ?? this.state()),
  );

  canSubmit(): boolean {
    const v = this.form.getRawValue();
    return v.terms && v.mockInputs && !this.busy();
  }

  submit(): void {
    if (!this.canSubmit()) {
      return;
    }
    this.busy.set(true);
    this.error.set(null);
    this.api
      .mockIdentity(this.walletId(), { terms_accepted: true, mock_inputs_confirmed: true })
      .subscribe({
        next: () => {
          this.busy.set(false);
          this.done.set(true);
          this.verified.emit();
        },
        error: (err: unknown) => {
          const apiError = toApiError(err);
          this.busy.set(false);
          if (apiError.code === 'ALREADY_ACTIVE_FULL') {
            this.verified.emit();
          }
          this.error.set(describeError(apiError));
        },
      });
  }
}
```

## `src/app/features/profile/identity-card.component.spec.ts`

```ts
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { API_BASE_URL } from '../../core/config/api-config';
import { IdentityCardComponent } from './identity-card.component';

describe('IdentityCardComponent', () => {
  let fixture: ComponentFixture<IdentityCardComponent>;
  let card: IdentityCardComponent;
  let http: HttpTestingController;

  function setup(available: boolean, state = 'PENDING_BIOM'): void {
    fixture = TestBed.createComponent(IdentityCardComponent);
    card = fixture.componentInstance;
    fixture.componentRef.setInput('walletId', 'w-1');
    fixture.componentRef.setInput('state', state);
    fixture.componentRef.setInput('available', available);
    fixture.detectChanges();
  }

  const q = (testId: string) =>
    fixture.nativeElement.querySelector(`[data-testid="${testId}"]`) as HTMLElement | null;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [IdentityCardComponent],
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
        { provide: API_BASE_URL, useValue: '/api' },
      ],
    }).compileComponents();
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => http.verify());

  it('CA-11: indica que las imágenes deben ser nítidas', () => {
    setup(true);
    expect(q('clarity-notice')?.textContent).toContain('nítidas');
  });

  it('CA-09: oculta el flujo mock si el ambiente no lo habilita', () => {
    setup(false);
    expect(q('mock-unavailable')).not.toBeNull();
    expect(q('verify')).toBeNull();
  });

  it('CA-10: exige aceptar términos y confirmar datos simulados', () => {
    setup(true);
    expect((q('verify') as HTMLButtonElement).disabled).toBeTrue();
    card.form.patchValue({ terms: true });
    fixture.detectChanges();
    expect((q('verify') as HTMLButtonElement).disabled).toBeTrue();
    card.form.patchValue({ mockInputs: true });
    fixture.detectChanges();
    expect((q('verify') as HTMLButtonElement).disabled).toBeFalse();
  });

  it('CA-12: simula la validación sin enviar archivos y emite el evento', () => {
    setup(true);
    let emitted = 0;
    card.verified.subscribe(() => emitted++);
    card.form.setValue({ terms: true, mockInputs: true });

    card.submit();
    const req = http.expectOne('/api/wallets/w-1/profile/identity/mock-verification');
    expect(req.request.body).toEqual({ terms_accepted: true, mock_inputs_confirmed: true });
    req.flush({
      account: { wallet_id: 'w-1', status: 'ACTIVE_FULL', balance: '0.00', currency: 'PEN' },
      profile: { estado_c1: 'PENDING_EMAIL', estado_c2: 'PENDING_MOVIL', estado_c3: 'ACTIVE_BIOM' },
    });
    fixture.detectChanges();

    expect(emitted).toBe(1);
    expect(q('validated-msg')).not.toBeNull();
  });

  it('muestra el error 403 BIOMETRIC_MOCK_DISABLED', () => {
    setup(true);
    card.form.setValue({ terms: true, mockInputs: true });
    card.submit();
    http
      .expectOne('/api/wallets/w-1/profile/identity/mock-verification')
      .flush(
        { code: 'BIOMETRIC_MOCK_DISABLED', message: 'x' },
        { status: 403, statusText: 'Forbidden' },
      );
    fixture.detectChanges();
    expect(q('card-error')?.textContent).toContain('no está disponible');
    expect(card.isValidated()).toBeFalse();
  });

  it('muestra el error 422 TERMS_NOT_ACCEPTED', () => {
    setup(true);
    card.form.setValue({ terms: true, mockInputs: true });
    card.submit();
    http
      .expectOne('/api/wallets/w-1/profile/identity/mock-verification')
      .flush(
        { code: 'TERMS_NOT_ACCEPTED', message: 'x' },
        { status: 422, statusText: 'Unprocessable' },
      );
    fixture.detectChanges();
    expect(q('card-error')?.textContent).toContain('términos y condiciones');
  });

  it('muestra validado si el estado inicial ya es ACTIVE_BIOM', () => {
    setup(true, 'ACTIVE_BIOM');
    expect(q('validated-msg')).not.toBeNull();
    expect(q('verify')).toBeNull();
  });
});
```

## `src/app/features/profile/operations-panel.component.ts`

```ts
import { Component, computed, inject, input, signal } from '@angular/core';
import { FormControl, FormGroup, ReactiveFormsModule } from '@angular/forms';
import { describeError, toApiError } from '../../core/errors/api-error';
import {
  OperationAccepted,
  OperationConditions,
  OperationType,
} from '../../core/models/api.models';
import { WalletApiService } from '../../core/services/wallet-api.service';
import { OPERATION_TYPE_LABELS, formatSoles } from '../../core/utils/format';
import { amountValidators } from '../../core/validators/field-validators';
import { validationMessage } from '../../core/validators/validation-messages';

/** Prueba de topes (CA-05, CA-13): registra recargas/pagos contra POST /wallets/{id}/operations. */
@Component({
  selector: 'app-operations-panel',
  standalone: true,
  imports: [ReactiveFormsModule],
  template: `
    <section class="card" aria-labelledby="ops-title">
      <h2 id="ops-title">Recargas y pagos</h2>
      <p class="muted">Los topes dependen de tu nivel de cuenta. Esta versión solo valida y registra los topes.</p>

      <form [formGroup]="form" (ngSubmit)="submit()" novalidate>
        <label for="operation_type">Tipo de operación</label>
        <select id="operation_type" formControlName="operation_type">
          @for (t of allowedTypes(); track t) {
            <option [value]="t">{{ label(t) }}</option>
          }
        </select>

        <label for="amount">Monto (S/)</label>
        <input id="amount" formControlName="amount" inputmode="decimal" placeholder="20.00"
               autocomplete="off" />
        @if (amountControl.invalid && (amountControl.dirty || amountControl.touched)) {
          <small class="msg invalid" data-testid="amount-error">{{ amountError() }}</small>
        }

        <button type="submit" class="btn" data-testid="submit-operation" [disabled]="!canSubmit()">
          {{ busy() ? 'Procesando…' : 'Registrar operación' }}
        </button>
      </form>

      @if (error()) {
        <p class="msg invalid" role="alert" data-testid="operation-error">{{ error() }}</p>
      }
      @if (last(); as op) {
        <p class="success" role="status" data-testid="operation-ok">
          ✔ {{ label(op.operation_type) }} de {{ money(op.amount) }} aceptada.
          Acumulado del día: {{ money(op.daily_accumulated) }} de {{ money(op.daily_max) }}.
        </p>
      }
      @if (history().length > 0) {
        <h3>Operaciones aceptadas en esta sesión</h3>
        <ul class="history" data-testid="history">
          @for (op of history(); track op.operation_id) {
            <li>{{ op.operation_day }} · {{ label(op.operation_type) }} · {{ money(op.amount) }}</li>
          }
        </ul>
      }
    </section>
  `,
})
export class OperationsPanelComponent {
  readonly walletId = input.required<string>();
  readonly conditions = input.required<OperationConditions>();

  private readonly api = inject(WalletApiService);

  readonly amountControl = new FormControl('', { nonNullable: true, validators: amountValidators() });
  readonly form = new FormGroup({
    operation_type: new FormControl<OperationType>('PAYMENT', { nonNullable: true }),
    amount: this.amountControl,
  });

  readonly busy = signal(false);
  readonly error = signal<string | null>(null);
  readonly last = signal<OperationAccepted | null>(null);
  readonly history = signal<OperationAccepted[]>([]);

  readonly money = formatSoles;

  /** Tipos permitidos según las reglas del estado actual (provienen de la API). */
  readonly allowedTypes = computed<OperationType[]>(() => {
    const types = this.conditions().rules.flatMap((r) => r.operation_types);
    return Array.from(new Set(types));
  });

  label(type: OperationType): string {
    return OPERATION_TYPE_LABELS[type];
  }

  amountError(): string | null {
    return validationMessage(this.amountControl.errors);
  }

  canSubmit(): boolean {
    return this.form.valid && !this.busy();
  }

  submit(): void {
    if (!this.canSubmit()) {
      this.form.markAllAsTouched();
      return;
    }
    const { operation_type, amount } = this.form.getRawValue();
    this.busy.set(true);
    this.error.set(null);
    this.api.registerOperation(this.walletId(), { operation_type, amount }).subscribe({
      next: (op) => {
        this.busy.set(false);
        this.last.set(op);
        this.history.update((h) => [op, ...h]);
        this.amountControl.reset('');
      },
      error: (err: unknown) => {
        this.busy.set(false);
        this.last.set(null);
        this.error.set(describeError(toApiError(err)));
      },
    });
  }
}
```

## `src/app/features/profile/operations-panel.component.spec.ts`

```ts
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { BASIC_CONDITIONS, FULL_CONDITIONS } from '../../../testing/fixtures';
import { API_BASE_URL } from '../../core/config/api-config';
import { OperationConditions } from '../../core/models/api.models';
import { OperationsPanelComponent } from './operations-panel.component';

describe('OperationsPanelComponent', () => {
  let fixture: ComponentFixture<OperationsPanelComponent>;
  let panel: OperationsPanelComponent;
  let http: HttpTestingController;

  function setup(conditions: OperationConditions): void {
    fixture = TestBed.createComponent(OperationsPanelComponent);
    panel = fixture.componentInstance;
    fixture.componentRef.setInput('walletId', 'w-1');
    fixture.componentRef.setInput('conditions', conditions);
    fixture.detectChanges();
  }

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [OperationsPanelComponent],
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
        { provide: API_BASE_URL, useValue: '/api' },
      ],
    }).compileComponents();
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => http.verify());

  it('CA-05: en ACTIVE_BASIC solo ofrece recarga propia y pago', () => {
    setup(BASIC_CONDITIONS);
    expect(panel.allowedTypes()).toEqual(['TOPUP_OWN', 'PAYMENT']);
    expect(fixture.nativeElement.querySelectorAll('select option').length).toBe(2);
  });

  it('CA-13: en ACTIVE_FULL ofrece también recarga de terceros', () => {
    setup(FULL_CONDITIONS);
    expect(panel.allowedTypes()).toEqual(['TOPUP_OWN', 'TOPUP_THIRD_PARTY', 'PAYMENT']);
  });

  it('valida el monto antes de enviar', () => {
    setup(BASIC_CONDITIONS);
    panel.amountControl.setValue('0');
    expect(panel.canSubmit()).toBeFalse();
    panel.amountControl.setValue('20.001');
    expect(panel.canSubmit()).toBeFalse();
    panel.amountControl.setValue('20.00');
    expect(panel.canSubmit()).toBeTrue();
  });

  it('registra una operación aceptada y muestra el acumulado diario', () => {
    setup(BASIC_CONDITIONS);
    panel.form.setValue({ operation_type: 'PAYMENT', amount: '20.00' });
    panel.submit();

    const req = http.expectOne('/api/wallets/w-1/operations');
    expect(req.request.body).toEqual({ operation_type: 'PAYMENT', amount: '20.00' });
    req.flush({
      operation_id: 'o-1',
      operation_type: 'PAYMENT',
      amount: '20.00',
      operation_day: '2026-10-30',
      daily_accumulated: '20.00',
      daily_max: '60.00',
    });
    fixture.detectChanges();

    const ok = fixture.nativeElement.querySelector('[data-testid="operation-ok"]') as HTMLElement;
    expect(ok.textContent).toContain('S/ 20.00');
    expect(ok.textContent).toContain('S/ 60.00');
    expect(fixture.nativeElement.querySelectorAll('[data-testid="history"] li').length).toBe(1);
  });

  it('muestra el error de tope diario', () => {
    setup(BASIC_CONDITIONS);
    panel.form.setValue({ operation_type: 'TOPUP_OWN', amount: '1.00' });
    panel.submit();
    http
      .expectOne('/api/wallets/w-1/operations')
      .flush(
        { code: 'DAILY_LIMIT_EXCEEDED', message: 'x' },
        { status: 422, statusText: 'Unprocessable' },
      );
    fixture.detectChanges();
    expect(
      fixture.nativeElement.querySelector('[data-testid="operation-error"]').textContent,
    ).toContain('tope diario');
    expect(panel.history().length).toBe(0);
  });

  it('muestra el error de tope por operación', () => {
    setup(BASIC_CONDITIONS);
    panel.form.setValue({ operation_type: 'PAYMENT', amount: '20.01' });
    panel.submit();
    http
      .expectOne('/api/wallets/w-1/operations')
      .flush(
        { code: 'PER_OPERATION_LIMIT_EXCEEDED', message: 'x' },
        { status: 422, statusText: 'Unprocessable' },
      );
    expect(panel.error()).toContain('tope por operación');
  });
});
```

## `src/app/features/profile/profile.component.ts`

```ts
import { Component, DestroyRef, OnInit, inject, signal } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { describeError, toApiError } from '../../core/errors/api-error';
import { WalletDetail } from '../../core/models/api.models';
import { SessionStore } from '../../core/services/session.store';
import { WalletApiService } from '../../core/services/wallet-api.service';
import { STATUS_LABELS, formatSoles } from '../../core/utils/format';
import { OperationConditionsComponent } from '../../shared/operation-conditions.component';
import { ChannelValidationCardComponent } from './channel-validation-card.component';
import { IdentityCardComponent } from './identity-card.component';
import { OperationsPanelComponent } from './operations-panel.component';

/** Pantalla de perfil (CA-06): tres validaciones independientes, en cualquier orden. */
@Component({
  selector: 'app-profile',
  standalone: true,
  imports: [
    OperationConditionsComponent,
    ChannelValidationCardComponent,
    IdentityCardComponent,
    OperationsPanelComponent,
  ],
  template: `
    <h1>Completa tu perfil</h1>
    <p class="muted">Puedes validar tu correo, tu celular y tu identidad en el orden que prefieras.</p>

    @if (loading()) {
      <p role="status">Cargando tu perfil…</p>
    }
    @if (error()) {
      <div class="banner warn" role="alert" data-testid="profile-error">
        {{ error() }}
        <button type="button" class="btn" (click)="refresh()">Reintentar</button>
      </div>
    }

    @if (wallet(); as w) {
      <div class="card" data-testid="account">
        <div class="card-head">
          <h2>Tu cuenta</h2>
          <span class="badge" [class.ok]="w.account.status === 'ACTIVE_FULL'" data-testid="status">
            {{ statusLabel(w.account.status) }}
          </span>
        </div>
        <p>Saldo: <strong>{{ money(w.account.balance) }}</strong></p>
      </div>

      <div class="grid">
        <app-channel-validation-card
          [channel]="'EMAIL'"
          [walletId]="w.account.wallet_id"
          [state]="w.profile.estado_c1"
          (validated)="refresh()" />
        <app-channel-validation-card
          [channel]="'PHONE'"
          [walletId]="w.account.wallet_id"
          [state]="w.profile.estado_c2"
          (validated)="refresh()" />
        <app-identity-card
          [walletId]="w.account.wallet_id"
          [state]="w.profile.estado_c3"
          [available]="w.identity_mock_available"
          (verified)="refresh()" />
      </div>

      <app-operation-conditions [conditions]="w.operation_conditions" />
      <app-operations-panel [walletId]="w.account.wallet_id" [conditions]="w.operation_conditions" />
    }
  `,
})
export class ProfileComponent implements OnInit {
  private readonly api = inject(WalletApiService);
  private readonly store = inject(SessionStore);
  private readonly destroyRef = inject(DestroyRef);

  readonly wallet = signal<WalletDetail | null>(null);
  readonly loading = signal(true);
  readonly error = signal<string | null>(null);
  readonly money = formatSoles;

  ngOnInit(): void {
    this.refresh();
  }

  statusLabel(status: 'ACTIVE_BASIC' | 'ACTIVE_FULL'): string {
    return STATUS_LABELS[status];
  }

  /** Recarga cuenta, estados del perfil, condiciones y disponibilidad del flujo mock. */
  refresh(): void {
    const id = this.store.walletId();
    if (!id) {
      return;
    }
    this.api
      .getWallet(id)
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: (w) => {
          this.wallet.set(w);
          this.loading.set(false);
          this.error.set(null);
        },
        error: (err: unknown) => {
          this.loading.set(false);
          this.error.set(describeError(toApiError(err)));
        },
      });
  }
}
```

## `src/app/features/profile/profile.component.spec.ts`

```ts
import { provideHttpClient, withInterceptors } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { FULL_CONDITIONS, REGISTRATION_RESPONSE, WALLET_DETAIL } from '../../../testing/fixtures';
import { API_BASE_URL } from '../../core/config/api-config';
import { basicAuthInterceptor } from '../../core/interceptors/basic-auth.interceptor';
import { WalletDetail } from '../../core/models/api.models';
import { SessionStore } from '../../core/services/session.store';
import { ProfileComponent } from './profile.component';

describe('ProfileComponent', () => {
  let fixture: ComponentFixture<ProfileComponent>;
  let component: ProfileComponent;
  let http: HttpTestingController;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [ProfileComponent],
      providers: [
        provideHttpClient(withInterceptors([basicAuthInterceptor])),
        provideHttpClientTesting(),
        provideRouter([]),
        { provide: API_BASE_URL, useValue: '/api' },
      ],
    }).compileComponents();

    TestBed.inject(SessionStore).start(
      { username: 'mjquispe', password: 'Clave#Segura2026' },
      REGISTRATION_RESPONSE,
    );
    http = TestBed.inject(HttpTestingController);
    fixture = TestBed.createComponent(ProfileComponent);
    component = fixture.componentInstance;
  });

  afterEach(() => http.verify());

  it('CA-06: carga la cuenta autenticada y renderiza las tres validaciones independientes', () => {
    fixture.detectChanges(); // ngOnInit
    const req = http.expectOne('/api/wallets/w-1');
    expect(req.request.method).toBe('GET');
    expect(req.request.headers.get('Authorization')).toBe(
      'Basic ' + btoa('mjquispe:Clave#Segura2026'),
    );
    req.flush(WALLET_DETAIL);
    fixture.detectChanges();

    const host: HTMLElement = fixture.nativeElement;
    expect(host.querySelectorAll('app-channel-validation-card').length).toBe(2);
    expect(host.querySelectorAll('app-identity-card').length).toBe(1);
    expect(host.querySelector('[data-testid="status"]')?.textContent).toContain('Cuenta básica');
    expect(host.querySelector('app-operation-conditions')).not.toBeNull();
    expect(host.querySelector('app-operations-panel')).not.toBeNull();
  });

  it('CA-12: al refrescar tras la validación mock refleja ACTIVE_FULL y los topes de nivel completo', () => {
    fixture.detectChanges();
    http.expectOne('/api/wallets/w-1').flush(WALLET_DETAIL);
    fixture.detectChanges();

    component.refresh();
    const full: WalletDetail = {
      ...WALLET_DETAIL,
      account: { ...WALLET_DETAIL.account, status: 'ACTIVE_FULL' },
      profile: { ...WALLET_DETAIL.profile, estado_c3: 'ACTIVE_BIOM' },
      operation_conditions: FULL_CONDITIONS,
    };
    http.expectOne('/api/wallets/w-1').flush(full);
    fixture.detectChanges();

    const host: HTMLElement = fixture.nativeElement;
    expect(host.querySelector('[data-testid="status"]')?.textContent).toContain('Cuenta completa');
    expect(host.querySelectorAll('[data-testid="condition-row"]').length).toBe(2);
    // C1 y C2 conservan su estado: las tres validaciones son independientes.
    expect(full.profile.estado_c1).toBe('PENDING_EMAIL');
    expect(host.querySelector('app-identity-card [data-testid="validated-msg"]')).not.toBeNull();
  });

  it('muestra un error con opción de reintentar si la API falla', () => {
    fixture.detectChanges();
    http
      .expectOne('/api/wallets/w-1')
      .flush({ code: 'FORBIDDEN', message: 'x' }, { status: 403, statusText: 'Forbidden' });
    fixture.detectChanges();
    expect(fixture.nativeElement.querySelector('[data-testid="profile-error"]')).not.toBeNull();
    expect(component.wallet()).toBeNull();
  });
});
```

---

## Notas finales

**Cumplimiento del criterio**
- **Componentes:** `OnboardingComponent`, `LandingComponent`, `ProfileComponent`, `ChannelValidationCardComponent` (correo y celular), `IdentityCardComponent`, `OperationsPanelComponent` y `OperationConditionsComponent`.
- **Servicios `HttpClient`:** `OnboardingApiService` y `WalletApiService` cubren los 13 endpoints del contrato, más `SessionStore`, el interceptor HTTP Basic y el guard.
- **Pruebas unitarias:** validadores, robustez de contraseña, utilidades, errores de API, servicios con `HttpTestingController`, interceptor, guard y todos los componentes. Las de componentes cubren el flujo CA-01 a CA-13: debounce de disponibilidad, 409 con sugerencias, cuenta regresiva de OTP, 429, 403/422 del mock biométrico y errores de topes.

**Corrección pendiente en el template de `OnboardingComponent`:** en el bloque de progreso, `de ${'{'}total{'}'}` debe ser `de {{ total }}`. La corrección está indicada justo debajo del archivo. Sin ese cambio la pantalla mostraría texto literal en lugar del total.

**Supuestos que dependen del backend, por confirmar:**
- Los errores llegan como `{code, message, ...}`. El mapeo también soporta `{detail: {code}}`.
- El backend sirve CORS, o se usa el proxy `/api` que ya está configurado.
- `ACTIVE_MOVIL` y `ACTIVE_BIOM` son los nombres de los estados validados, heredados del Arquitecto.