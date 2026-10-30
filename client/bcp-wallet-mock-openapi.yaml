openapi: 3.0.3
info:
  title: Wallet mock W1–W6
  version: 0.3.0
  description: Mock Wallet W1–W6. Importes enteros en céntimos PEN. Estado en
    memoria. Sin autenticación. Contrato local; cloud ajusta servidores a los
    ocho grupos. Respuestas y efectos documentados por operación.
servers:
  - url: http://127.0.0.1:8787
paths:
  /health:
    get:
      summary: Salud
      responses:
        "200":
          description: Consulta o repetición
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/Health"
          headers:
            X-Mock-Latency-Ms:
              description: Demora simulada aplicada, en milisegundos.
              schema:
                type: integer
                minimum: 0
                maximum: 5000
        "400":
          description: Campos o X-Mock-Latency-Ms inválidos.
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/Error"
          headers:
            X-Mock-Latency-Ms:
              description: Demora simulada aplicada, en milisegundos.
              schema:
                type: integer
                minimum: 0
                maximum: 5000
      tags:
        - Servicio y grupos
      description: Comprueba disponibilidad y almacenamiento en memoria. No modifica
        datos. El servicio raíz remoto incluye enlaces a grupos y OpenAPI; la
        URL del grupo informa su entorno.
      operationId: getHealth
      parameters:
        - name: X-Mock-Latency-Ms
          in: header
          required: false
          description: "Demora simulada por solicitud, en milisegundos. Entero de 0 a
            5000, predeterminado 0. Se aplica antes de enviar la respuesta,
            también en errores; no cambia el escenario ni retrasa otras
            solicitudes. Valor inválido: 400 INVALID_MOCK_LATENCY antes de
            ejecutar la operación."
          schema:
            type: integer
            minimum: 0
            maximum: 5000
            default: 0
          example: 1000
        - name: latency
          in: query
          required: false
          description: Latencia de la URL, entero de 0 a 5000 ms. El header
            X-Mock-Latency-Ms tiene prioridad si se envían ambos. Ambos valores
            deben ser válidos.
          schema:
            type: integer
            minimum: 0
            maximum: 5000
            default: 0
          example: 1000
  /scenarios:
    get:
      summary: Escenarios disponibles
      responses:
        "200":
          description: Consulta o repetición
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/Scenarios"
          headers:
            X-Mock-Latency-Ms:
              description: Demora simulada aplicada, en milisegundos.
              schema:
                type: integer
                minimum: 0
                maximum: 5000
        "400":
          description: Campos o X-Mock-Latency-Ms inválidos.
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/Error"
          headers:
            X-Mock-Latency-Ms:
              description: Demora simulada aplicada, en milisegundos.
              schema:
                type: integer
                minimum: 0
                maximum: 5000
      tags:
        - Servicio y grupos
      description: Lista las opciones exactas de scenario para KYC, pagos y
        alteraciones del reporte. No avanza escenarios ni modifica datos.
      operationId: getScenarios
      parameters:
        - name: X-Mock-Latency-Ms
          in: header
          required: false
          description: "Demora simulada por solicitud, en milisegundos. Entero de 0 a
            5000, predeterminado 0. Se aplica antes de enviar la respuesta,
            también en errores; no cambia el escenario ni retrasa otras
            solicitudes. Valor inválido: 400 INVALID_MOCK_LATENCY antes de
            ejecutar la operación."
          schema:
            type: integer
            minimum: 0
            maximum: 5000
            default: 0
          example: 1000
        - name: latency
          in: query
          required: false
          description: Latencia de la URL, entero de 0 a 5000 ms. El header
            X-Mock-Latency-Ms tiene prioridad si se envían ambos. Ambos valores
            deben ser válidos.
          schema:
            type: integer
            minimum: 0
            maximum: 5000
            default: 0
          example: 1000
  /openapi.json:
    get:
      summary: Este contrato
      responses:
        "200":
          description: Consulta o repetición
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/OpenApi"
          headers:
            X-Mock-Latency-Ms:
              description: Demora simulada aplicada, en milisegundos.
              schema:
                type: integer
                minimum: 0
                maximum: 5000
        "400":
          description: Campos o X-Mock-Latency-Ms inválidos.
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/Error"
          headers:
            X-Mock-Latency-Ms:
              description: Demora simulada aplicada, en milisegundos.
              schema:
                type: integer
                minimum: 0
                maximum: 5000
      tags:
        - Servicio y grupos
      description: Devuelve este contrato. En cloud, el contrato raíz ofrece ocho
        servidores y el contrato del grupo ofrece solo su URL. Importa el del
        grupo en Postman o Swagger.
      operationId: getOpenapi.Json
      parameters:
        - name: X-Mock-Latency-Ms
          in: header
          required: false
          description: "Demora simulada por solicitud, en milisegundos. Entero de 0 a
            5000, predeterminado 0. Se aplica antes de enviar la respuesta,
            también en errores; no cambia el escenario ni retrasa otras
            solicitudes. Valor inválido: 400 INVALID_MOCK_LATENCY antes de
            ejecutar la operación."
          schema:
            type: integer
            minimum: 0
            maximum: 5000
            default: 0
          example: 1000
        - name: latency
          in: query
          required: false
          description: Latencia de la URL, entero de 0 a 5000 ms. El header
            X-Mock-Latency-Ms tiene prioridad si se envían ambos. Ambos valores
            deben ser válidos.
          schema:
            type: integer
            minimum: 0
            maximum: 5000
            default: 0
          example: 1000
  /kyc/verifications:
    post:
      summary: Crear wallet con KYC simulado
      responses:
        "201":
          description: Creado
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/Kyc"
          headers:
            X-Mock-Latency-Ms:
              description: Demora simulada aplicada, en milisegundos.
              schema:
                type: integer
                minimum: 0
                maximum: 5000
        "400":
          description: Entrada inválida
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/Error"
          headers:
            X-Mock-Latency-Ms:
              description: Demora simulada aplicada, en milisegundos.
              schema:
                type: integer
                minimum: 0
                maximum: 5000
        "413":
          description: Cuerpo mayor a 65536 bytes.
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/Error"
          headers:
            X-Mock-Latency-Ms:
              description: Demora simulada aplicada, en milisegundos.
              schema:
                type: integer
                minimum: 0
                maximum: 5000
        "429":
          description: "Solo cloud: GROUP_LIMIT_RESET_REQUIRED. Reinicia el grupo."
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/Error"
          headers:
            X-Mock-Latency-Ms:
              description: Demora simulada aplicada, en milisegundos.
              schema:
                type: integer
                minimum: 0
                maximum: 5000
        "503":
          description: Proveedor no disponible
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/Error"
          headers:
            X-Mock-Latency-Ms:
              description: Demora simulada aplicada, en milisegundos.
              schema:
                type: integer
                minimum: 0
                maximum: 5000
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                documentType:
                  type: string
                  enum:
                    - TEST
                  minLength: 1
                  maxLength: 200
                  description: Solo TEST. No enviar documentos reales.
                document:
                  type: string
                  pattern: ^TEST-
                  minLength: 1
                  maxLength: 200
                  description: Documento ficticio con prefijo TEST-.
                scenario:
                  type: string
                  enum:
                    - APPROVED
                    - REJECTED
                    - MANUAL_REVIEW
                    - UNAVAILABLE
                  minLength: 1
                  maxLength: 200
                  description: Escenario del proveedor simulado. Predeterminado APPROVED.
                  default: APPROVED
              required:
                - documentType
                - document
            example:
              documentType: TEST
              document: TEST-001
              scenario: APPROVED
      tags:
        - W1 · Registro y activación
      description: Crea una verificación y una wallet con saldo cero. APPROVED, valor
        predeterminado, activa; REJECTED rechaza; MANUAL_REVIEW deja PENDING y
        abre soporte. UNAVAILABLE devuelve 503 KYC_UNAVAILABLE sin crear wallet.
        Solo documentType TEST y document con prefijo TEST-. No evita altas
        repetidas.
      operationId: postKycVerifications
      parameters:
        - name: X-Mock-Latency-Ms
          in: header
          required: false
          description: "Demora simulada por solicitud, en milisegundos. Entero de 0 a
            5000, predeterminado 0. Se aplica antes de enviar la respuesta,
            también en errores; no cambia el escenario ni retrasa otras
            solicitudes. Valor inválido: 400 INVALID_MOCK_LATENCY antes de
            ejecutar la operación."
          schema:
            type: integer
            minimum: 0
            maximum: 5000
            default: 0
          example: 1000
        - name: latency
          in: query
          required: false
          description: Latencia de la URL, entero de 0 a 5000 ms. El header
            X-Mock-Latency-Ms tiene prioridad si se envían ambos. Ambos valores
            deben ser válidos.
          schema:
            type: integer
            minimum: 0
            maximum: 5000
            default: 0
          example: 1000
  /kyc/verifications/{id}:
    get:
      summary: Consultar KYC
      responses:
        "200":
          description: Consulta o repetición
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/Kyc"
          headers:
            X-Mock-Latency-Ms:
              description: Demora simulada aplicada, en milisegundos.
              schema:
                type: integer
                minimum: 0
                maximum: 5000
        "400":
          description: Campos o X-Mock-Latency-Ms inválidos.
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/Error"
          headers:
            X-Mock-Latency-Ms:
              description: Demora simulada aplicada, en milisegundos.
              schema:
                type: integer
                minimum: 0
                maximum: 5000
        "404":
          description: No existe
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/Error"
          headers:
            X-Mock-Latency-Ms:
              description: Demora simulada aplicada, en milisegundos.
              schema:
                type: integer
                minimum: 0
                maximum: 5000
      parameters:
        - in: path
          name: id
          required: true
          schema:
            type: string
          description: ID del recurso nombrado en la ruta. En /control/provider usa el ID
            del pago.
        - name: X-Mock-Latency-Ms
          in: header
          required: false
          description: "Demora simulada por solicitud, en milisegundos. Entero de 0 a
            5000, predeterminado 0. Se aplica antes de enviar la respuesta,
            también en errores; no cambia el escenario ni retrasa otras
            solicitudes. Valor inválido: 400 INVALID_MOCK_LATENCY antes de
            ejecutar la operación."
          schema:
            type: integer
            minimum: 0
            maximum: 5000
            default: 0
          example: 1000
        - name: latency
          in: query
          required: false
          description: Latencia de la URL, entero de 0 a 5000 ms. El header
            X-Mock-Latency-Ms tiene prioridad si se envían ambos. Ambos valores
            deben ser válidos.
          schema:
            type: integer
            minimum: 0
            maximum: 5000
            default: 0
          example: 1000
      tags:
        - W1 · Registro y activación
      description: Consulta la verificación por su ID kyc, distinto al wallet_id.
        Devuelve 404 NOT_FOUND si no existe en el grupo.
      operationId: getKycVerificationsByid
  /kyc/verifications/{id}/decision:
    post:
      summary: Resolver revisión humana
      responses:
        "200":
          description: Consulta o repetición
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/Kyc"
          headers:
            X-Mock-Latency-Ms:
              description: Demora simulada aplicada, en milisegundos.
              schema:
                type: integer
                minimum: 0
                maximum: 5000
        "400":
          description: Entrada inválida
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/Error"
          headers:
            X-Mock-Latency-Ms:
              description: Demora simulada aplicada, en milisegundos.
              schema:
                type: integer
                minimum: 0
                maximum: 5000
        "404":
          description: No existe
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/Error"
          headers:
            X-Mock-Latency-Ms:
              description: Demora simulada aplicada, en milisegundos.
              schema:
                type: integer
                minimum: 0
                maximum: 5000
        "409":
          description: Conflicto de estado, saldo o idempotencia
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/Error"
          headers:
            X-Mock-Latency-Ms:
              description: Demora simulada aplicada, en milisegundos.
              schema:
                type: integer
                minimum: 0
                maximum: 5000
        "413":
          description: Cuerpo mayor a 65536 bytes.
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/Error"
          headers:
            X-Mock-Latency-Ms:
              description: Demora simulada aplicada, en milisegundos.
              schema:
                type: integer
                minimum: 0
                maximum: 5000
        "429":
          description: "Solo cloud: GROUP_LIMIT_RESET_REQUIRED. Reinicia el grupo."
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/Error"
          headers:
            X-Mock-Latency-Ms:
              description: Demora simulada aplicada, en milisegundos.
              schema:
                type: integer
                minimum: 0
                maximum: 5000
      parameters:
        - in: path
          name: id
          required: true
          schema:
            type: string
          description: ID del recurso nombrado en la ruta. En /control/provider usa el ID
            del pago.
        - name: X-Mock-Latency-Ms
          in: header
          required: false
          description: "Demora simulada por solicitud, en milisegundos. Entero de 0 a
            5000, predeterminado 0. Se aplica antes de enviar la respuesta,
            también en errores; no cambia el escenario ni retrasa otras
            solicitudes. Valor inválido: 400 INVALID_MOCK_LATENCY antes de
            ejecutar la operación."
          schema:
            type: integer
            minimum: 0
            maximum: 5000
            default: 0
          example: 1000
        - name: latency
          in: query
          required: false
          description: Latencia de la URL, entero de 0 a 5000 ms. El header
            X-Mock-Latency-Ms tiene prioridad si se envían ambos. Ambos valores
            deben ser válidos.
          schema:
            type: integer
            minimum: 0
            maximum: 5000
            default: 0
          example: 1000
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                decision:
                  type: string
                  enum:
                    - ACTIVE
                    - REJECTED
                  minLength: 1
                  maxLength: 200
                  description: Decisión final del operador sobre la verificación.
              required:
                - decision
            example:
              decision: ACTIVE
      tags:
        - W1 · Registro y activación
      description: "Decide ACTIVE o REJECTED sobre una verificación PENDING, actualiza
        su wallet y resuelve su caso de soporte. Repetir la misma decisión
        devuelve 200; cambiar una decisión final devuelve 409 DECISION_CONFLICT.
        Decisión inválida: 400 INVALID_DECISION."
      operationId: postKycVerificationsByidDecision
  /wallets/{id}:
    get:
      summary: Saldo contable, reservado y disponible
      responses:
        "200":
          description: Consulta o repetición
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/Wallet"
          headers:
            X-Mock-Latency-Ms:
              description: Demora simulada aplicada, en milisegundos.
              schema:
                type: integer
                minimum: 0
                maximum: 5000
        "400":
          description: Campos o X-Mock-Latency-Ms inválidos.
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/Error"
          headers:
            X-Mock-Latency-Ms:
              description: Demora simulada aplicada, en milisegundos.
              schema:
                type: integer
                minimum: 0
                maximum: 5000
        "404":
          description: No existe
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/Error"
          headers:
            X-Mock-Latency-Ms:
              description: Demora simulada aplicada, en milisegundos.
              schema:
                type: integer
                minimum: 0
                maximum: 5000
      parameters:
        - in: path
          name: id
          required: true
          schema:
            type: string
          description: ID del recurso nombrado en la ruta. En /control/provider usa el ID
            del pago.
        - name: X-Mock-Latency-Ms
          in: header
          required: false
          description: "Demora simulada por solicitud, en milisegundos. Entero de 0 a
            5000, predeterminado 0. Se aplica antes de enviar la respuesta,
            también en errores; no cambia el escenario ni retrasa otras
            solicitudes. Valor inválido: 400 INVALID_MOCK_LATENCY antes de
            ejecutar la operación."
          schema:
            type: integer
            minimum: 0
            maximum: 5000
            default: 0
          example: 1000
        - name: latency
          in: query
          required: false
          description: Latencia de la URL, entero de 0 a 5000 ms. El header
            X-Mock-Latency-Ms tiene prioridad si se envían ambos. Ambos valores
            deben ser válidos.
          schema:
            type: integer
            minimum: 0
            maximum: 5000
            default: 0
          example: 1000
      tags:
        - W1 · Registro y activación
      description: "Consulta estado y saldos en céntimos. available = balance -
        reserved. Solo los pagos PENDING reservan saldo. wallet-demo empieza
        ACTIVE con 100000. Wallet inexistente: 404 NOT_FOUND."
      operationId: getWalletsByid
  /payments:
    post:
      summary: Crear pago de contacto o comercio
      responses:
        "200":
          description: Consulta o repetición
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/Payment"
          headers:
            X-Mock-Latency-Ms:
              description: Demora simulada aplicada, en milisegundos.
              schema:
                type: integer
                minimum: 0
                maximum: 5000
        "202":
          description: Pendiente; completar mediante evento
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/Payment"
          headers:
            X-Mock-Latency-Ms:
              description: Demora simulada aplicada, en milisegundos.
              schema:
                type: integer
                minimum: 0
                maximum: 5000
        "400":
          description: Entrada inválida
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/Error"
          headers:
            X-Mock-Latency-Ms:
              description: Demora simulada aplicada, en milisegundos.
              schema:
                type: integer
                minimum: 0
                maximum: 5000
        "404":
          description: No existe
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/Error"
          headers:
            X-Mock-Latency-Ms:
              description: Demora simulada aplicada, en milisegundos.
              schema:
                type: integer
                minimum: 0
                maximum: 5000
        "409":
          description: Conflicto de estado, saldo o idempotencia
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/Error"
          headers:
            X-Mock-Latency-Ms:
              description: Demora simulada aplicada, en milisegundos.
              schema:
                type: integer
                minimum: 0
                maximum: 5000
        "410":
          description: QR vencido
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/Error"
          headers:
            X-Mock-Latency-Ms:
              description: Demora simulada aplicada, en milisegundos.
              schema:
                type: integer
                minimum: 0
                maximum: 5000
        "413":
          description: Cuerpo mayor a 65536 bytes.
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/Error"
          headers:
            X-Mock-Latency-Ms:
              description: Demora simulada aplicada, en milisegundos.
              schema:
                type: integer
                minimum: 0
                maximum: 5000
        "429":
          description: "Solo cloud: GROUP_LIMIT_RESET_REQUIRED. Reinicia el grupo."
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/Error"
          headers:
            X-Mock-Latency-Ms:
              description: Demora simulada aplicada, en milisegundos.
              schema:
                type: integer
                minimum: 0
                maximum: 5000
        "503":
          description: Proveedor no disponible
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/Error"
          headers:
            X-Mock-Latency-Ms:
              description: Demora simulada aplicada, en milisegundos.
              schema:
                type: integer
                minimum: 0
                maximum: 5000
        "504":
          description: Respuesta perdida después de procesar
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/Error"
          headers:
            X-Mock-Latency-Ms:
              description: Demora simulada aplicada, en milisegundos.
              schema:
                type: integer
                minimum: 0
                maximum: 5000
      parameters:
        - in: header
          name: Idempotency-Key
          required: true
          schema:
            type: string
            minLength: 1
            maxLength: 200
          description: Clave única por wallet. Reutiliza la misma clave y contenido al
            reintentar.
        - name: X-Mock-Latency-Ms
          in: header
          required: false
          description: "Demora simulada por solicitud, en milisegundos. Entero de 0 a
            5000, predeterminado 0. Se aplica antes de enviar la respuesta,
            también en errores; no cambia el escenario ni retrasa otras
            solicitudes. Valor inválido: 400 INVALID_MOCK_LATENCY antes de
            ejecutar la operación."
          schema:
            type: integer
            minimum: 0
            maximum: 5000
            default: 0
          example: 1000
        - name: latency
          in: query
          required: false
          description: Latencia de la URL, entero de 0 a 5000 ms. El header
            X-Mock-Latency-Ms tiene prioridad si se envían ambos. Ambos valores
            deben ser válidos.
          schema:
            type: integer
            minimum: 0
            maximum: 5000
            default: 0
          example: 1000
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                walletId:
                  type: string
                  minLength: 1
                  maxLength: 200
                  description: ID de wallet. Para pagos con fondos usa wallet-demo.
                recipient:
                  type: string
                  enum:
                    - contact-demo
                    - merchant-demo
                  minLength: 1
                  maxLength: 200
                  description: Destinatario externo de prueba.
                amountCents:
                  type: integer
                  minimum: 1
                  maximum: 100000000
                  description: Importe en céntimos de PEN. 1500 = S/ 15.00.
                currency:
                  type: string
                  enum:
                    - PEN
                  minLength: 1
                  maxLength: 200
                  description: Solo PEN. Predeterminado PEN.
                  default: PEN
                scenario:
                  type: string
                  enum:
                    - APPROVED
                    - REJECTED
                    - PENDING
                    - DELAYED_APPROVAL
                    - TIMEOUT_AFTER_PROCESSING
                    - PROVIDER_ERROR
                  minLength: 1
                  maxLength: 200
                  description: Escenario del proveedor simulado. Predeterminado APPROVED.
                  default: APPROVED
                qrId:
                  type: string
                  description: ID del QR creado en este grupo. Opcional, valida comercio, monto y
                    vigencia.
                  nullable: true
              required:
                - walletId
                - recipient
                - amountCents
            example:
              walletId: wallet-demo
              recipient: contact-demo
              amountCents: 1500
              currency: PEN
              scenario: APPROVED
      tags:
        - W2 · Pago a contacto
      description: "Crea una intención PENDING y reserva saldo; responde 202. Requiere
        Idempotency-Key de 1 a 200 caracteres, única por wallet. Misma clave y
        contenido devuelve 200 con el pago actual; contenido distinto devuelve
        409 IDEMPOTENCY_CONFLICT. APPROVED y REJECTED generan evento; PENDING y
        DELAYED_APPROVAL esperan control manual. TIMEOUT_AFTER_PROCESSING
        devuelve 504 con paymentId, pero ya creó el pago y el proveedor lo
        aprobó. PROVIDER_ERROR devuelve 503 sin operación ni reserva. Confirma
        por callback o /resolve. Moneda predeterminada PEN, escenario APPROVED.
        409 WALLET_NOT_ACTIVE o INSUFFICIENT_FUNDS; 404 por wallet, destinatario
        o QR inexistente; 410 QR_EXPIRED; 409 QR_PAYMENT_MISMATCH si difieren
        comercio o monto fijo. Solo se permiten contact-demo y merchant-demo.
        qrId es opcional: sin él, el pago es directo."
      operationId: postPayments
    get:
      summary: Historial filtrado por walletId
      responses:
        "200":
          description: Consulta o repetición
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: "#/components/schemas/Payment"
          headers:
            X-Mock-Latency-Ms:
              description: Demora simulada aplicada, en milisegundos.
              schema:
                type: integer
                minimum: 0
                maximum: 5000
        "400":
          description: Campos o X-Mock-Latency-Ms inválidos.
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/Error"
          headers:
            X-Mock-Latency-Ms:
              description: Demora simulada aplicada, en milisegundos.
              schema:
                type: integer
                minimum: 0
                maximum: 5000
      parameters:
        - in: query
          name: walletId
          schema:
            type: string
            default: wallet-demo
          description: Wallet del historial, predeterminada wallet-demo.
        - name: X-Mock-Latency-Ms
          in: header
          required: false
          description: "Demora simulada por solicitud, en milisegundos. Entero de 0 a
            5000, predeterminado 0. Se aplica antes de enviar la respuesta,
            también en errores; no cambia el escenario ni retrasa otras
            solicitudes. Valor inválido: 400 INVALID_MOCK_LATENCY antes de
            ejecutar la operación."
          schema:
            type: integer
            minimum: 0
            maximum: 5000
            default: 0
          example: 1000
        - name: latency
          in: query
          required: false
          description: Latencia de la URL, entero de 0 a 5000 ms. El header
            X-Mock-Latency-Ms tiene prioridad si se envían ambos. Ambos valores
            deben ser válidos.
          schema:
            type: integer
            minimum: 0
            maximum: 5000
            default: 0
          example: 1000
      tags:
        - W2 · Pago a contacto
      description: Lista el historial de una wallet. walletId es opcional y vale
        wallet-demo por defecto. Una wallet sin pagos o inexistente produce [].
        Sin paginación ni filtros de fechas. No lista todas las wallets del
        grupo.
      operationId: getPayments
  /payments/{id}:
    get:
      summary: Consultar pago
      responses:
        "200":
          description: Consulta o repetición
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/Payment"
          headers:
            X-Mock-Latency-Ms:
              description: Demora simulada aplicada, en milisegundos.
              schema:
                type: integer
                minimum: 0
                maximum: 5000
        "400":
          description: Campos o X-Mock-Latency-Ms inválidos.
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/Error"
          headers:
            X-Mock-Latency-Ms:
              description: Demora simulada aplicada, en milisegundos.
              schema:
                type: integer
                minimum: 0
                maximum: 5000
        "404":
          description: No existe
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/Error"
          headers:
            X-Mock-Latency-Ms:
              description: Demora simulada aplicada, en milisegundos.
              schema:
                type: integer
                minimum: 0
                maximum: 5000
      parameters:
        - in: path
          name: id
          required: true
          schema:
            type: string
          description: ID del recurso nombrado en la ruta. En /control/provider usa el ID
            del pago.
        - name: X-Mock-Latency-Ms
          in: header
          required: false
          description: "Demora simulada por solicitud, en milisegundos. Entero de 0 a
            5000, predeterminado 0. Se aplica antes de enviar la respuesta,
            también en errores; no cambia el escenario ni retrasa otras
            solicitudes. Valor inválido: 400 INVALID_MOCK_LATENCY antes de
            ejecutar la operación."
          schema:
            type: integer
            minimum: 0
            maximum: 5000
            default: 0
          example: 1000
        - name: latency
          in: query
          required: false
          description: Latencia de la URL, entero de 0 a 5000 ms. El header
            X-Mock-Latency-Ms tiene prioridad si se envían ambos. Ambos valores
            deben ser válidos.
          schema:
            type: integer
            minimum: 0
            maximum: 5000
            default: 0
          example: 1000
      tags:
        - W2 · Pago a contacto
      description: "Consulta el estado local del pago. No consulta al proveedor ni
        confirma eventos. Pago inexistente: 404 NOT_FOUND."
      operationId: getPaymentsByid
  /payments/{id}/receipt:
    get:
      summary: Comprobante de pago exitoso o reversado
      responses:
        "200":
          description: Consulta o repetición
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/Receipt"
          headers:
            X-Mock-Latency-Ms:
              description: Demora simulada aplicada, en milisegundos.
              schema:
                type: integer
                minimum: 0
                maximum: 5000
        "400":
          description: Campos o X-Mock-Latency-Ms inválidos.
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/Error"
          headers:
            X-Mock-Latency-Ms:
              description: Demora simulada aplicada, en milisegundos.
              schema:
                type: integer
                minimum: 0
                maximum: 5000
        "404":
          description: No existe
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/Error"
          headers:
            X-Mock-Latency-Ms:
              description: Demora simulada aplicada, en milisegundos.
              schema:
                type: integer
                minimum: 0
                maximum: 5000
        "409":
          description: Conflicto de estado, saldo o idempotencia
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/Error"
          headers:
            X-Mock-Latency-Ms:
              description: Demora simulada aplicada, en milisegundos.
              schema:
                type: integer
                minimum: 0
                maximum: 5000
      parameters:
        - in: path
          name: id
          required: true
          schema:
            type: string
          description: ID del recurso nombrado en la ruta. En /control/provider usa el ID
            del pago.
        - name: X-Mock-Latency-Ms
          in: header
          required: false
          description: "Demora simulada por solicitud, en milisegundos. Entero de 0 a
            5000, predeterminado 0. Se aplica antes de enviar la respuesta,
            también en errores; no cambia el escenario ni retrasa otras
            solicitudes. Valor inválido: 400 INVALID_MOCK_LATENCY antes de
            ejecutar la operación."
          schema:
            type: integer
            minimum: 0
            maximum: 5000
            default: 0
          example: 1000
        - name: latency
          in: query
          required: false
          description: Latencia de la URL, entero de 0 a 5000 ms. El header
            X-Mock-Latency-Ms tiene prioridad si se envían ambos. Ambos valores
            deben ser válidos.
          schema:
            type: integer
            minimum: 0
            maximum: 5000
            default: 0
          example: 1000
      tags:
        - W2 · Pago a contacto
      description: "Obtiene el comprobante cuando el pago está SUCCEEDED o REVERSED.
        En PENDING o REJECTED devuelve 409 RECEIPT_NOT_READY. No genera PDF.
        Pago inexistente: 404."
      operationId: getPaymentsByidReceipt
  /provider/payments/{id}:
    get:
      summary: Consultar fuente del proveedor
      responses:
        "200":
          description: Consulta o repetición
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/ProviderPayment"
          headers:
            X-Mock-Latency-Ms:
              description: Demora simulada aplicada, en milisegundos.
              schema:
                type: integer
                minimum: 0
                maximum: 5000
        "400":
          description: Campos o X-Mock-Latency-Ms inválidos.
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/Error"
          headers:
            X-Mock-Latency-Ms:
              description: Demora simulada aplicada, en milisegundos.
              schema:
                type: integer
                minimum: 0
                maximum: 5000
        "404":
          description: No existe
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/Error"
          headers:
            X-Mock-Latency-Ms:
              description: Demora simulada aplicada, en milisegundos.
              schema:
                type: integer
                minimum: 0
                maximum: 5000
      parameters:
        - in: path
          name: id
          required: true
          schema:
            type: string
          description: ID del recurso nombrado en la ruta. En /control/provider usa el ID
            del pago.
        - name: X-Mock-Latency-Ms
          in: header
          required: false
          description: "Demora simulada por solicitud, en milisegundos. Entero de 0 a
            5000, predeterminado 0. Se aplica antes de enviar la respuesta,
            también en errores; no cambia el escenario ni retrasa otras
            solicitudes. Valor inválido: 400 INVALID_MOCK_LATENCY antes de
            ejecutar la operación."
          schema:
            type: integer
            minimum: 0
            maximum: 5000
            default: 0
          example: 1000
        - name: latency
          in: query
          required: false
          description: Latencia de la URL, entero de 0 a 5000 ms. El header
            X-Mock-Latency-Ms tiene prioridad si se envían ambos. Ambos valores
            deben ser válidos.
          schema:
            type: integer
            minimum: 0
            maximum: 5000
            default: 0
          example: 1000
      tags:
        - W2 · Pago a contacto
      description: "Consulta el estado del proveedor simulado usando el mismo ID del
        pago. Puede diferir del estado local si falta el callback. No aplica el
        resultado a la wallet. ID inexistente: 404."
      operationId: getProviderPaymentsByid
  /reversals/{id}:
    get:
      summary: Consultar reverso
      responses:
        "200":
          description: Consulta o repetición
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/Reversal"
          headers:
            X-Mock-Latency-Ms:
              description: Demora simulada aplicada, en milisegundos.
              schema:
                type: integer
                minimum: 0
                maximum: 5000
        "400":
          description: Campos o X-Mock-Latency-Ms inválidos.
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/Error"
          headers:
            X-Mock-Latency-Ms:
              description: Demora simulada aplicada, en milisegundos.
              schema:
                type: integer
                minimum: 0
                maximum: 5000
        "404":
          description: No existe
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/Error"
          headers:
            X-Mock-Latency-Ms:
              description: Demora simulada aplicada, en milisegundos.
              schema:
                type: integer
                minimum: 0
                maximum: 5000
      parameters:
        - in: path
          name: id
          required: true
          schema:
            type: string
          description: ID del recurso nombrado en la ruta. En /control/provider usa el ID
            del pago.
        - name: X-Mock-Latency-Ms
          in: header
          required: false
          description: "Demora simulada por solicitud, en milisegundos. Entero de 0 a
            5000, predeterminado 0. Se aplica antes de enviar la respuesta,
            también en errores; no cambia el escenario ni retrasa otras
            solicitudes. Valor inválido: 400 INVALID_MOCK_LATENCY antes de
            ejecutar la operación."
          schema:
            type: integer
            minimum: 0
            maximum: 5000
            default: 0
          example: 1000
        - name: latency
          in: query
          required: false
          description: Latencia de la URL, entero de 0 a 5000 ms. El header
            X-Mock-Latency-Ms tiene prioridad si se envían ambos. Ambos valores
            deben ser válidos.
          schema:
            type: integer
            minimum: 0
            maximum: 5000
            default: 0
          example: 1000
      tags:
        - W5 · Fallas y reversos
      description: "Consulta usando el ID rev del reverso. PENDING espera confirmación
        y SUCCEEDED significa saldo devuelto. No usar el ID pay del pago en esta
        ruta. Inexistente: 404."
      operationId: getReversalsByid
  /payments/{id}/resolve:
    post:
      summary: Consultar proveedor y resolver o escalar
      responses:
        "200":
          description: Consulta o repetición
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/Payment"
          headers:
            X-Mock-Latency-Ms:
              description: Demora simulada aplicada, en milisegundos.
              schema:
                type: integer
                minimum: 0
                maximum: 5000
        "202":
          description: Pendiente; completar mediante evento
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/PendingResolution"
          headers:
            X-Mock-Latency-Ms:
              description: Demora simulada aplicada, en milisegundos.
              schema:
                type: integer
                minimum: 0
                maximum: 5000
        "400":
          description: JSON o campos inválidos.
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/Error"
          headers:
            X-Mock-Latency-Ms:
              description: Demora simulada aplicada, en milisegundos.
              schema:
                type: integer
                minimum: 0
                maximum: 5000
        "404":
          description: No existe
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/Error"
          headers:
            X-Mock-Latency-Ms:
              description: Demora simulada aplicada, en milisegundos.
              schema:
                type: integer
                minimum: 0
                maximum: 5000
        "409":
          description: Conflicto de estado, saldo o idempotencia
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/Error"
          headers:
            X-Mock-Latency-Ms:
              description: Demora simulada aplicada, en milisegundos.
              schema:
                type: integer
                minimum: 0
                maximum: 5000
        "413":
          description: Cuerpo mayor a 65536 bytes.
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/Error"
          headers:
            X-Mock-Latency-Ms:
              description: Demora simulada aplicada, en milisegundos.
              schema:
                type: integer
                minimum: 0
                maximum: 5000
        "429":
          description: "Solo cloud: GROUP_LIMIT_RESET_REQUIRED. Reinicia el grupo."
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/Error"
          headers:
            X-Mock-Latency-Ms:
              description: Demora simulada aplicada, en milisegundos.
              schema:
                type: integer
                minimum: 0
                maximum: 5000
      parameters:
        - in: path
          name: id
          required: true
          schema:
            type: string
          description: ID del recurso nombrado en la ruta. En /control/provider usa el ID
            del pago.
        - name: X-Mock-Latency-Ms
          in: header
          required: false
          description: "Demora simulada por solicitud, en milisegundos. Entero de 0 a
            5000, predeterminado 0. Se aplica antes de enviar la respuesta,
            también en errores; no cambia el escenario ni retrasa otras
            solicitudes. Valor inválido: 400 INVALID_MOCK_LATENCY antes de
            ejecutar la operación."
          schema:
            type: integer
            minimum: 0
            maximum: 5000
            default: 0
          example: 1000
        - name: latency
          in: query
          required: false
          description: Latencia de la URL, entero de 0 a 5000 ms. El header
            X-Mock-Latency-Ms tiene prioridad si se envían ambos. Ambos valores
            deben ser válidos.
          schema:
            type: integer
            minimum: 0
            maximum: 5000
            default: 0
          example: 1000
      requestBody:
        required: false
        content:
          application/json:
            schema:
              type: object
              properties: {}
              required: []
            example: {}
      tags:
        - W5 · Fallas y reversos
      description: "Consulta al proveedor sin crear otro cobro. Si sigue PENDING
        devuelve 202 con escalated:true y abre un único caso de soporte. Si ya
        terminó, aplica el resultado y devuelve 200 con el pago. Repetir
        conserva el resultado. También puede completar un reverso pendiente. No
        requiere cuerpo ni Idempotency-Key. Pago inexistente: 404."
      operationId: postPaymentsByidResolve
  /payments/{id}/reversals:
    post:
      summary: Reverso completo, único por pago
      responses:
        "200":
          description: Consulta o repetición
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/Reversal"
          headers:
            X-Mock-Latency-Ms:
              description: Demora simulada aplicada, en milisegundos.
              schema:
                type: integer
                minimum: 0
                maximum: 5000
        "202":
          description: Pendiente; completar mediante evento
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/Reversal"
          headers:
            X-Mock-Latency-Ms:
              description: Demora simulada aplicada, en milisegundos.
              schema:
                type: integer
                minimum: 0
                maximum: 5000
        "400":
          description: JSON o campos inválidos.
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/Error"
          headers:
            X-Mock-Latency-Ms:
              description: Demora simulada aplicada, en milisegundos.
              schema:
                type: integer
                minimum: 0
                maximum: 5000
        "404":
          description: No existe
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/Error"
          headers:
            X-Mock-Latency-Ms:
              description: Demora simulada aplicada, en milisegundos.
              schema:
                type: integer
                minimum: 0
                maximum: 5000
        "409":
          description: Conflicto de estado, saldo o idempotencia
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/Error"
          headers:
            X-Mock-Latency-Ms:
              description: Demora simulada aplicada, en milisegundos.
              schema:
                type: integer
                minimum: 0
                maximum: 5000
        "413":
          description: Cuerpo mayor a 65536 bytes.
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/Error"
          headers:
            X-Mock-Latency-Ms:
              description: Demora simulada aplicada, en milisegundos.
              schema:
                type: integer
                minimum: 0
                maximum: 5000
        "429":
          description: "Solo cloud: GROUP_LIMIT_RESET_REQUIRED. Reinicia el grupo."
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/Error"
          headers:
            X-Mock-Latency-Ms:
              description: Demora simulada aplicada, en milisegundos.
              schema:
                type: integer
                minimum: 0
                maximum: 5000
      parameters:
        - in: path
          name: id
          required: true
          schema:
            type: string
          description: ID del recurso nombrado en la ruta. En /control/provider usa el ID
            del pago.
        - name: X-Mock-Latency-Ms
          in: header
          required: false
          description: "Demora simulada por solicitud, en milisegundos. Entero de 0 a
            5000, predeterminado 0. Se aplica antes de enviar la respuesta,
            también en errores; no cambia el escenario ni retrasa otras
            solicitudes. Valor inválido: 400 INVALID_MOCK_LATENCY antes de
            ejecutar la operación."
          schema:
            type: integer
            minimum: 0
            maximum: 5000
            default: 0
          example: 1000
        - name: latency
          in: query
          required: false
          description: Latencia de la URL, entero de 0 a 5000 ms. El header
            X-Mock-Latency-Ms tiene prioridad si se envían ambos. Ambos valores
            deben ser válidos.
          schema:
            type: integer
            minimum: 0
            maximum: 5000
            default: 0
          example: 1000
      requestBody:
        required: false
        content:
          application/json:
            schema:
              type: object
              properties: {}
              required: []
            example: {}
      tags:
        - W5 · Fallas y reversos
      description: "Solicita un reverso completo de un pago SUCCEEDED. Devuelve 202
        con reverso PENDING, cambia el proveedor a REVERSED y crea el evento
        REVERSED. Hasta confirmar, la wallet conserva el cargo. Repetir devuelve
        200 con el mismo reverso. Otro estado inicial: 409
        PAYMENT_NOT_REVERSIBLE. Pago inexistente: 404. No requiere cuerpo ni
        Idempotency-Key."
      operationId: postPaymentsByidReversals
  /qrs:
    post:
      summary: Generar payload QR de prueba
      responses:
        "201":
          description: Creado
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/Qr"
          headers:
            X-Mock-Latency-Ms:
              description: Demora simulada aplicada, en milisegundos.
              schema:
                type: integer
                minimum: 0
                maximum: 5000
        "400":
          description: Entrada inválida
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/Error"
          headers:
            X-Mock-Latency-Ms:
              description: Demora simulada aplicada, en milisegundos.
              schema:
                type: integer
                minimum: 0
                maximum: 5000
        "404":
          description: No existe
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/Error"
          headers:
            X-Mock-Latency-Ms:
              description: Demora simulada aplicada, en milisegundos.
              schema:
                type: integer
                minimum: 0
                maximum: 5000
        "413":
          description: Cuerpo mayor a 65536 bytes.
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/Error"
          headers:
            X-Mock-Latency-Ms:
              description: Demora simulada aplicada, en milisegundos.
              schema:
                type: integer
                minimum: 0
                maximum: 5000
        "429":
          description: "Solo cloud: GROUP_LIMIT_RESET_REQUIRED. Reinicia el grupo."
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/Error"
          headers:
            X-Mock-Latency-Ms:
              description: Demora simulada aplicada, en milisegundos.
              schema:
                type: integer
                minimum: 0
                maximum: 5000
      requestBody:
        required: false
        content:
          application/json:
            schema:
              type: object
              properties:
                merchantId:
                  type: string
                  enum:
                    - merchant-demo
                  minLength: 1
                  maxLength: 200
                  description: Comercio de prueba. Predeterminado merchant-demo.
                amountCents:
                  type: integer
                  minimum: 1
                  maximum: 100000000
                  nullable: true
                  description: Importe en céntimos de PEN. 1500 = S/ 15.00.
                expiresInSeconds:
                  type: integer
                  minimum: 0
                  maximum: 86400
                  default: 300
                  description: Vigencia en segundos. 0 vence inmediatamente.
              required: []
            example:
              merchantId: merchant-demo
              amountCents: 2200
              expiresInSeconds: 300
      tags:
        - W3 · Pago QR comercio
      description: "Crea texto qrmock:ID para merchant-demo. Sin amountCents o con
        null, el monto es abierto. Con monto, el pago debe respetarlo.
        expiresInSeconds predeterminado 300, rango entero 0..86400; 0 vence
        inmediatamente. Comercio desconocido: 404 MERCHANT_NOT_FOUND; TTL
        inválido: 400 INVALID_TTL. No genera imagen ni valida EMVCo."
      operationId: postQrs
      parameters:
        - name: X-Mock-Latency-Ms
          in: header
          required: false
          description: "Demora simulada por solicitud, en milisegundos. Entero de 0 a
            5000, predeterminado 0. Se aplica antes de enviar la respuesta,
            también en errores; no cambia el escenario ni retrasa otras
            solicitudes. Valor inválido: 400 INVALID_MOCK_LATENCY antes de
            ejecutar la operación."
          schema:
            type: integer
            minimum: 0
            maximum: 5000
            default: 0
          example: 1000
        - name: latency
          in: query
          required: false
          description: Latencia de la URL, entero de 0 a 5000 ms. El header
            X-Mock-Latency-Ms tiene prioridad si se envían ambos. Ambos valores
            deben ser válidos.
          schema:
            type: integer
            minimum: 0
            maximum: 5000
            default: 0
          example: 1000
  /qrs/resolve:
    post:
      summary: Resolver payload local
      responses:
        "200":
          description: Consulta o repetición
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/ResolvedQr"
          headers:
            X-Mock-Latency-Ms:
              description: Demora simulada aplicada, en milisegundos.
              schema:
                type: integer
                minimum: 0
                maximum: 5000
        "400":
          description: Entrada inválida
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/Error"
          headers:
            X-Mock-Latency-Ms:
              description: Demora simulada aplicada, en milisegundos.
              schema:
                type: integer
                minimum: 0
                maximum: 5000
        "404":
          description: No existe
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/Error"
          headers:
            X-Mock-Latency-Ms:
              description: Demora simulada aplicada, en milisegundos.
              schema:
                type: integer
                minimum: 0
                maximum: 5000
        "410":
          description: QR vencido
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/Error"
          headers:
            X-Mock-Latency-Ms:
              description: Demora simulada aplicada, en milisegundos.
              schema:
                type: integer
                minimum: 0
                maximum: 5000
        "413":
          description: Cuerpo mayor a 65536 bytes.
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/Error"
          headers:
            X-Mock-Latency-Ms:
              description: Demora simulada aplicada, en milisegundos.
              schema:
                type: integer
                minimum: 0
                maximum: 5000
        "429":
          description: "Solo cloud: GROUP_LIMIT_RESET_REQUIRED. Reinicia el grupo."
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/Error"
          headers:
            X-Mock-Latency-Ms:
              description: Demora simulada aplicada, en milisegundos.
              schema:
                type: integer
                minimum: 0
                maximum: 5000
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                payload:
                  type: string
                  minLength: 1
                  maxLength: 200
                  description: Texto qrmock:ID devuelto por POST /qrs.
              required:
                - payload
            example:
              payload: qrmock:REEMPLAZAR_ID_QR
      tags:
        - W3 · Pago QR comercio
      description: Resuelve el payload y devuelve comercio y monto, null si abierto.
        No crea pagos. 400 INVALID_QR por formato desconocido; 404 NOT_FOUND por
        ID desconocido; 410 QR_EXPIRED por vencimiento. Usa el ID devuelto al
        crear el QR como qrId del pago.
      operationId: postQrsResolve
      parameters:
        - name: X-Mock-Latency-Ms
          in: header
          required: false
          description: "Demora simulada por solicitud, en milisegundos. Entero de 0 a
            5000, predeterminado 0. Se aplica antes de enviar la respuesta,
            también en errores; no cambia el escenario ni retrasa otras
            solicitudes. Valor inválido: 400 INVALID_MOCK_LATENCY antes de
            ejecutar la operación."
          schema:
            type: integer
            minimum: 0
            maximum: 5000
            default: 0
          example: 1000
        - name: latency
          in: query
          required: false
          description: Latencia de la URL, entero de 0 a 5000 ms. El header
            X-Mock-Latency-Ms tiene prioridad si se envían ambos. Ambos valores
            deben ser válidos.
          schema:
            type: integer
            minimum: 0
            maximum: 5000
            default: 0
          example: 1000
  /callbacks/payments:
    post:
      summary: Consumir evento conocido del proveedor local
      responses:
        "200":
          description: Consulta o repetición
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/Callback"
          headers:
            X-Mock-Latency-Ms:
              description: Demora simulada aplicada, en milisegundos.
              schema:
                type: integer
                minimum: 0
                maximum: 5000
        "400":
          description: Entrada inválida
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/Error"
          headers:
            X-Mock-Latency-Ms:
              description: Demora simulada aplicada, en milisegundos.
              schema:
                type: integer
                minimum: 0
                maximum: 5000
        "404":
          description: No existe
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/Error"
          headers:
            X-Mock-Latency-Ms:
              description: Demora simulada aplicada, en milisegundos.
              schema:
                type: integer
                minimum: 0
                maximum: 5000
        "409":
          description: Conflicto de estado, saldo o idempotencia
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/Error"
          headers:
            X-Mock-Latency-Ms:
              description: Demora simulada aplicada, en milisegundos.
              schema:
                type: integer
                minimum: 0
                maximum: 5000
        "413":
          description: Cuerpo mayor a 65536 bytes.
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/Error"
          headers:
            X-Mock-Latency-Ms:
              description: Demora simulada aplicada, en milisegundos.
              schema:
                type: integer
                minimum: 0
                maximum: 5000
        "429":
          description: "Solo cloud: GROUP_LIMIT_RESET_REQUIRED. Reinicia el grupo."
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/Error"
          headers:
            X-Mock-Latency-Ms:
              description: Demora simulada aplicada, en milisegundos.
              schema:
                type: integer
                minimum: 0
                maximum: 5000
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                eventId:
                  type: string
                  minLength: 1
                  maxLength: 200
                  description: ID evt de un evento devuelto por GET /control/events.
              required:
                - eventId
            example:
              eventId: REEMPLAZAR_ID_EVENTO
      tags:
        - W4 · Idempotencia y callbacks
      description: "Entrega un evento existente mediante eventId. Primera entrega:
        duplicate:false y payment; repetición del mismo evento: solo
        duplicate:true. El éxito descuenta saldo y crea dos asientos; rechazo
        libera reserva; reverso devuelve saldo y compensa asientos. Una
        aprobación tardía de un pago ya REVERSED se acepta sin cambiar saldo ni
        estado. Evento inexistente: 404; transición incompatible: 409
        INVALID_STATE_TRANSITION. No verifica firmas ni recibe payloads
        externos."
      operationId: postCallbacksPayments
      parameters:
        - name: X-Mock-Latency-Ms
          in: header
          required: false
          description: "Demora simulada por solicitud, en milisegundos. Entero de 0 a
            5000, predeterminado 0. Se aplica antes de enviar la respuesta,
            también en errores; no cambia el escenario ni retrasa otras
            solicitudes. Valor inválido: 400 INVALID_MOCK_LATENCY antes de
            ejecutar la operación."
          schema:
            type: integer
            minimum: 0
            maximum: 5000
            default: 0
          example: 1000
        - name: latency
          in: query
          required: false
          description: Latencia de la URL, entero de 0 a 5000 ms. El header
            X-Mock-Latency-Ms tiene prioridad si se envían ambos. Ambos valores
            deben ser válidos.
          schema:
            type: integer
            minimum: 0
            maximum: 5000
            default: 0
          example: 1000
  /control/events:
    get:
      summary: Eventos con contador de entrega
      responses:
        "200":
          description: Consulta o repetición
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: "#/components/schemas/Event"
          headers:
            X-Mock-Latency-Ms:
              description: Demora simulada aplicada, en milisegundos.
              schema:
                type: integer
                minimum: 0
                maximum: 5000
        "400":
          description: Campos o X-Mock-Latency-Ms inválidos.
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/Error"
          headers:
            X-Mock-Latency-Ms:
              description: Demora simulada aplicada, en milisegundos.
              schema:
                type: integer
                minimum: 0
                maximum: 5000
      tags:
        - Controles del mock
      description: Lista eventos de todos los pagos del grupo, incluidos los
        entregados. Filtra en tu cliente por payment_id y target, y usa id como
        eventId. No hay envío automático de webhooks.
      operationId: getControlEvents
      parameters:
        - name: X-Mock-Latency-Ms
          in: header
          required: false
          description: "Demora simulada por solicitud, en milisegundos. Entero de 0 a
            5000, predeterminado 0. Se aplica antes de enviar la respuesta,
            también en errores; no cambia el escenario ni retrasa otras
            solicitudes. Valor inválido: 400 INVALID_MOCK_LATENCY antes de
            ejecutar la operación."
          schema:
            type: integer
            minimum: 0
            maximum: 5000
            default: 0
          example: 1000
        - name: latency
          in: query
          required: false
          description: Latencia de la URL, entero de 0 a 5000 ms. El header
            X-Mock-Latency-Ms tiene prioridad si se envían ambos. Ambos valores
            deben ser válidos.
          schema:
            type: integer
            minimum: 0
            maximum: 5000
            default: 0
          example: 1000
  /ledger:
    get:
      summary: Asientos de partida doble
      responses:
        "200":
          description: Consulta o repetición
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: "#/components/schemas/LedgerEntry"
          headers:
            X-Mock-Latency-Ms:
              description: Demora simulada aplicada, en milisegundos.
              schema:
                type: integer
                minimum: 0
                maximum: 5000
        "400":
          description: Campos o X-Mock-Latency-Ms inválidos.
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/Error"
          headers:
            X-Mock-Latency-Ms:
              description: Demora simulada aplicada, en milisegundos.
              schema:
                type: integer
                minimum: 0
                maximum: 5000
      tags:
        - W6 · Conciliación
      description: Lista asientos de partida doble del grupo. Incluye dos asientos
        FUNDING de la semilla. PAYMENT resta a la wallet y suma a clearing;
        REVERSAL hace lo contrario. No modifica saldos.
      operationId: getLedger
      parameters:
        - name: X-Mock-Latency-Ms
          in: header
          required: false
          description: "Demora simulada por solicitud, en milisegundos. Entero de 0 a
            5000, predeterminado 0. Se aplica antes de enviar la respuesta,
            también en errores; no cambia el escenario ni retrasa otras
            solicitudes. Valor inválido: 400 INVALID_MOCK_LATENCY antes de
            ejecutar la operación."
          schema:
            type: integer
            minimum: 0
            maximum: 5000
            default: 0
          example: 1000
        - name: latency
          in: query
          required: false
          description: Latencia de la URL, entero de 0 a 5000 ms. El header
            X-Mock-Latency-Ms tiene prioridad si se envían ambos. Ambos valores
            deben ser válidos.
          schema:
            type: integer
            minimum: 0
            maximum: 5000
            default: 0
          example: 1000
  /support/cases:
    get:
      summary: Casos abiertos y resueltos
      responses:
        "200":
          description: Consulta o repetición
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: "#/components/schemas/SupportCase"
          headers:
            X-Mock-Latency-Ms:
              description: Demora simulada aplicada, en milisegundos.
              schema:
                type: integer
                minimum: 0
                maximum: 5000
        "400":
          description: Campos o X-Mock-Latency-Ms inválidos.
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/Error"
          headers:
            X-Mock-Latency-Ms:
              description: Demora simulada aplicada, en milisegundos.
              schema:
                type: integer
                minimum: 0
                maximum: 5000
      tags:
        - W5 · Fallas y reversos
      description: Lista casos OPEN y RESOLVED por revisión KYC o resultado de pago
        pendiente. La decisión KYC o confirmación del pago resuelve el caso. No
        envía notificaciones externas ni ofrece edición directa.
      operationId: getSupportCases
      parameters:
        - name: X-Mock-Latency-Ms
          in: header
          required: false
          description: "Demora simulada por solicitud, en milisegundos. Entero de 0 a
            5000, predeterminado 0. Se aplica antes de enviar la respuesta,
            también en errores; no cambia el escenario ni retrasa otras
            solicitudes. Valor inválido: 400 INVALID_MOCK_LATENCY antes de
            ejecutar la operación."
          schema:
            type: integer
            minimum: 0
            maximum: 5000
            default: 0
          example: 1000
        - name: latency
          in: query
          required: false
          description: Latencia de la URL, entero de 0 a 5000 ms. El header
            X-Mock-Latency-Ms tiene prioridad si se envían ambos. Ambos valores
            deben ser válidos.
          schema:
            type: integer
            minimum: 0
            maximum: 5000
            default: 0
          example: 1000
  /settlements:
    get:
      summary: Reporte simulado completo, sin corte diario
      responses:
        "200":
          description: Consulta o repetición
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: "#/components/schemas/ProviderPayment"
          headers:
            X-Mock-Latency-Ms:
              description: Demora simulada aplicada, en milisegundos.
              schema:
                type: integer
                minimum: 0
                maximum: 5000
        "400":
          description: Campos o X-Mock-Latency-Ms inválidos.
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/Error"
          headers:
            X-Mock-Latency-Ms:
              description: Demora simulada aplicada, en milisegundos.
              schema:
                type: integer
                minimum: 0
                maximum: 5000
      tags:
        - W6 · Conciliación
      description: Devuelve el reporte completo del proveedor con las alteraciones
        configuradas en /control/settlements. Incluye pagos pendientes,
        rechazados y reversados. No concilia ni cambia la wallet.
      operationId: getSettlements
      parameters:
        - name: X-Mock-Latency-Ms
          in: header
          required: false
          description: "Demora simulada por solicitud, en milisegundos. Entero de 0 a
            5000, predeterminado 0. Se aplica antes de enviar la respuesta,
            también en errores; no cambia el escenario ni retrasa otras
            solicitudes. Valor inválido: 400 INVALID_MOCK_LATENCY antes de
            ejecutar la operación."
          schema:
            type: integer
            minimum: 0
            maximum: 5000
            default: 0
          example: 1000
        - name: latency
          in: query
          required: false
          description: Latencia de la URL, entero de 0 a 5000 ms. El header
            X-Mock-Latency-Ms tiene prioridad si se envían ambos. Ambos valores
            deben ser válidos.
          schema:
            type: integer
            minimum: 0
            maximum: 5000
            default: 0
          example: 1000
  /reconciliations/incidents:
    get:
      summary: Historial de incidencias
      responses:
        "200":
          description: Consulta o repetición
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: "#/components/schemas/Incident"
          headers:
            X-Mock-Latency-Ms:
              description: Demora simulada aplicada, en milisegundos.
              schema:
                type: integer
                minimum: 0
                maximum: 5000
        "400":
          description: Campos o X-Mock-Latency-Ms inválidos.
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/Error"
          headers:
            X-Mock-Latency-Ms:
              description: Demora simulada aplicada, en milisegundos.
              schema:
                type: integer
                minimum: 0
                maximum: 5000
      tags:
        - W6 · Conciliación
      description: Lista incidencias OPEN y RESOLVED del último proceso de
        conciliación. La misma combinación de recurso y motivo conserva ID en
        ejecuciones posteriores. Solo POST /reconciliations recalcula su estado.
      operationId: getReconciliationsIncidents
      parameters:
        - name: X-Mock-Latency-Ms
          in: header
          required: false
          description: "Demora simulada por solicitud, en milisegundos. Entero de 0 a
            5000, predeterminado 0. Se aplica antes de enviar la respuesta,
            también en errores; no cambia el escenario ni retrasa otras
            solicitudes. Valor inválido: 400 INVALID_MOCK_LATENCY antes de
            ejecutar la operación."
          schema:
            type: integer
            minimum: 0
            maximum: 5000
            default: 0
          example: 1000
        - name: latency
          in: query
          required: false
          description: Latencia de la URL, entero de 0 a 5000 ms. El header
            X-Mock-Latency-Ms tiene prioridad si se envían ambos. Ambos valores
            deben ser válidos.
          schema:
            type: integer
            minimum: 0
            maximum: 5000
            default: 0
          example: 1000
  /control/events/{id}/deliver:
    post:
      summary: Entregar o repetir evento local
      responses:
        "200":
          description: Consulta o repetición
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/Callback"
          headers:
            X-Mock-Latency-Ms:
              description: Demora simulada aplicada, en milisegundos.
              schema:
                type: integer
                minimum: 0
                maximum: 5000
        "400":
          description: JSON o campos inválidos.
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/Error"
          headers:
            X-Mock-Latency-Ms:
              description: Demora simulada aplicada, en milisegundos.
              schema:
                type: integer
                minimum: 0
                maximum: 5000
        "404":
          description: No existe
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/Error"
          headers:
            X-Mock-Latency-Ms:
              description: Demora simulada aplicada, en milisegundos.
              schema:
                type: integer
                minimum: 0
                maximum: 5000
        "409":
          description: Conflicto de estado, saldo o idempotencia
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/Error"
          headers:
            X-Mock-Latency-Ms:
              description: Demora simulada aplicada, en milisegundos.
              schema:
                type: integer
                minimum: 0
                maximum: 5000
        "413":
          description: Cuerpo mayor a 65536 bytes.
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/Error"
          headers:
            X-Mock-Latency-Ms:
              description: Demora simulada aplicada, en milisegundos.
              schema:
                type: integer
                minimum: 0
                maximum: 5000
        "429":
          description: "Solo cloud: GROUP_LIMIT_RESET_REQUIRED. Reinicia el grupo."
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/Error"
          headers:
            X-Mock-Latency-Ms:
              description: Demora simulada aplicada, en milisegundos.
              schema:
                type: integer
                minimum: 0
                maximum: 5000
      parameters:
        - in: path
          name: id
          required: true
          schema:
            type: string
          description: ID del recurso nombrado en la ruta. En /control/provider usa el ID
            del pago.
        - name: X-Mock-Latency-Ms
          in: header
          required: false
          description: "Demora simulada por solicitud, en milisegundos. Entero de 0 a
            5000, predeterminado 0. Se aplica antes de enviar la respuesta,
            también en errores; no cambia el escenario ni retrasa otras
            solicitudes. Valor inválido: 400 INVALID_MOCK_LATENCY antes de
            ejecutar la operación."
          schema:
            type: integer
            minimum: 0
            maximum: 5000
            default: 0
          example: 1000
        - name: latency
          in: query
          required: false
          description: Latencia de la URL, entero de 0 a 5000 ms. El header
            X-Mock-Latency-Ms tiene prioridad si se envían ambos. Ambos valores
            deben ser válidos.
          schema:
            type: integer
            minimum: 0
            maximum: 5000
            default: 0
          example: 1000
      requestBody:
        required: false
        content:
          application/json:
            schema:
              type: object
              properties: {}
              required: []
            example: {}
      tags:
        - Controles del mock
      description: Entrega el evento por ID evt de la ruta. Equivale a POST
        /callbacks/payments con eventId. No requiere cuerpo. Repetir es seguro;
        404 si no existe; 409 si la transición es incompatible.
      operationId: postControlEventsByidDeliver
  /control/provider/{id}/complete:
    post:
      summary: Finalizar proveedor pendiente y encolar evento
      responses:
        "200":
          description: Consulta o repetición
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/EventCreated"
          headers:
            X-Mock-Latency-Ms:
              description: Demora simulada aplicada, en milisegundos.
              schema:
                type: integer
                minimum: 0
                maximum: 5000
        "400":
          description: Entrada inválida
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/Error"
          headers:
            X-Mock-Latency-Ms:
              description: Demora simulada aplicada, en milisegundos.
              schema:
                type: integer
                minimum: 0
                maximum: 5000
        "404":
          description: No existe
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/Error"
          headers:
            X-Mock-Latency-Ms:
              description: Demora simulada aplicada, en milisegundos.
              schema:
                type: integer
                minimum: 0
                maximum: 5000
        "409":
          description: Conflicto de estado, saldo o idempotencia
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/Error"
          headers:
            X-Mock-Latency-Ms:
              description: Demora simulada aplicada, en milisegundos.
              schema:
                type: integer
                minimum: 0
                maximum: 5000
        "413":
          description: Cuerpo mayor a 65536 bytes.
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/Error"
          headers:
            X-Mock-Latency-Ms:
              description: Demora simulada aplicada, en milisegundos.
              schema:
                type: integer
                minimum: 0
                maximum: 5000
        "429":
          description: "Solo cloud: GROUP_LIMIT_RESET_REQUIRED. Reinicia el grupo."
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/Error"
          headers:
            X-Mock-Latency-Ms:
              description: Demora simulada aplicada, en milisegundos.
              schema:
                type: integer
                minimum: 0
                maximum: 5000
      parameters:
        - in: path
          name: id
          required: true
          schema:
            type: string
          description: ID del recurso nombrado en la ruta. En /control/provider usa el ID
            del pago.
        - name: X-Mock-Latency-Ms
          in: header
          required: false
          description: "Demora simulada por solicitud, en milisegundos. Entero de 0 a
            5000, predeterminado 0. Se aplica antes de enviar la respuesta,
            también en errores; no cambia el escenario ni retrasa otras
            solicitudes. Valor inválido: 400 INVALID_MOCK_LATENCY antes de
            ejecutar la operación."
          schema:
            type: integer
            minimum: 0
            maximum: 5000
            default: 0
          example: 1000
        - name: latency
          in: query
          required: false
          description: Latencia de la URL, entero de 0 a 5000 ms. El header
            X-Mock-Latency-Ms tiene prioridad si se envían ambos. Ambos valores
            deben ser válidos.
          schema:
            type: integer
            minimum: 0
            maximum: 5000
            default: 0
          example: 1000
      requestBody:
        required: false
        content:
          application/json:
            schema:
              type: object
              properties:
                status:
                  type: string
                  enum:
                    - SUCCEEDED
                    - REJECTED
                  minLength: 1
                  maxLength: 200
                  description: Resultado del proveedor. Predeterminado SUCCEEDED.
              required: []
            example:
              status: SUCCEEDED
      tags:
        - Controles del mock
      description: "Finaliza un proveedor PENDING usando el ID pay del pago. status
        puede ser SUCCEEDED, valor predeterminado, o REJECTED. Devuelve eventId
        para entregar después. No confirma la wallet automáticamente. Si ya
        terminó: 409 PROVIDER_ALREADY_FINAL; estado inválido: 400
        INVALID_STATUS; ID inexistente: 404."
      operationId: postControlProviderByidComplete
  /control/settlements:
    post:
      summary: Alterar reporte sin modificar wallet ni ledger
      responses:
        "200":
          description: Consulta o repetición
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/Configured"
          headers:
            X-Mock-Latency-Ms:
              description: Demora simulada aplicada, en milisegundos.
              schema:
                type: integer
                minimum: 0
                maximum: 5000
        "400":
          description: Entrada inválida
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/Error"
          headers:
            X-Mock-Latency-Ms:
              description: Demora simulada aplicada, en milisegundos.
              schema:
                type: integer
                minimum: 0
                maximum: 5000
        "404":
          description: No existe
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/Error"
          headers:
            X-Mock-Latency-Ms:
              description: Demora simulada aplicada, en milisegundos.
              schema:
                type: integer
                minimum: 0
                maximum: 5000
        "409":
          description: Conflicto de estado, saldo o idempotencia
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/Error"
          headers:
            X-Mock-Latency-Ms:
              description: Demora simulada aplicada, en milisegundos.
              schema:
                type: integer
                minimum: 0
                maximum: 5000
        "413":
          description: Cuerpo mayor a 65536 bytes.
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/Error"
          headers:
            X-Mock-Latency-Ms:
              description: Demora simulada aplicada, en milisegundos.
              schema:
                type: integer
                minimum: 0
                maximum: 5000
        "429":
          description: "Solo cloud: GROUP_LIMIT_RESET_REQUIRED. Reinicia el grupo."
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/Error"
          headers:
            X-Mock-Latency-Ms:
              description: Demora simulada aplicada, en milisegundos.
              schema:
                type: integer
                minimum: 0
                maximum: 5000
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                paymentId:
                  type: string
                  minLength: 1
                  maxLength: 200
                  description: ID pay del pago; para ORPHAN usa un ID nuevo.
                mode:
                  type: string
                  enum:
                    - MISSING
                    - AMOUNT
                    - DUPLICATE
                    - ORPHAN
                    - CLEAR
                  minLength: 1
                  maxLength: 200
                  description: Alteración del reporte. CLEAR restaura la fila original.
                amountCents:
                  type: integer
                  minimum: 1
                  maximum: 100000000
                  description: Importe en céntimos de PEN. 1500 = S/ 15.00. Obligatorio para
                    AMOUNT y ORPHAN.
              required:
                - paymentId
                - mode
            example:
              paymentId: REEMPLAZAR_ID_PAGO
              mode: AMOUNT
              amountCents: 1600
      tags:
        - Controles del mock
      description: "Configura una sola alteración por paymentId, reemplazando la
        anterior. AMOUNT exige amountCents; MISSING omite fila; DUPLICATE
        duplica fila; los tres exigen pago existente. ORPHAN exige ID nuevo y
        amountCents, o 409 PROVIDER_ALREADY_EXISTS. CLEAR elimina la alteración
        aunque no exista. Modo inválido: 400 INVALID_MODE. No modifica
        proveedor, wallet ni ledger; solo el reporte."
      operationId: postControlSettlements
      parameters:
        - name: X-Mock-Latency-Ms
          in: header
          required: false
          description: "Demora simulada por solicitud, en milisegundos. Entero de 0 a
            5000, predeterminado 0. Se aplica antes de enviar la respuesta,
            también en errores; no cambia el escenario ni retrasa otras
            solicitudes. Valor inválido: 400 INVALID_MOCK_LATENCY antes de
            ejecutar la operación."
          schema:
            type: integer
            minimum: 0
            maximum: 5000
            default: 0
          example: 1000
        - name: latency
          in: query
          required: false
          description: Latencia de la URL, entero de 0 a 5000 ms. El header
            X-Mock-Latency-Ms tiene prioridad si se envían ambos. Ambos valores
            deben ser válidos.
          schema:
            type: integer
            minimum: 0
            maximum: 5000
            default: 0
          example: 1000
  /reconciliations:
    post:
      summary: Comparar fuentes y actualizar incidencias
      responses:
        "200":
          description: Consulta o repetición
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/Reconciliation"
          headers:
            X-Mock-Latency-Ms:
              description: Demora simulada aplicada, en milisegundos.
              schema:
                type: integer
                minimum: 0
                maximum: 5000
        "400":
          description: JSON o campos inválidos.
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/Error"
          headers:
            X-Mock-Latency-Ms:
              description: Demora simulada aplicada, en milisegundos.
              schema:
                type: integer
                minimum: 0
                maximum: 5000
        "413":
          description: Cuerpo mayor a 65536 bytes.
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/Error"
          headers:
            X-Mock-Latency-Ms:
              description: Demora simulada aplicada, en milisegundos.
              schema:
                type: integer
                minimum: 0
                maximum: 5000
        "429":
          description: "Solo cloud: GROUP_LIMIT_RESET_REQUIRED. Reinicia el grupo."
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/Error"
          headers:
            X-Mock-Latency-Ms:
              description: Demora simulada aplicada, en milisegundos.
              schema:
                type: integer
                minimum: 0
                maximum: 5000
      requestBody:
        required: false
        content:
          application/json:
            schema:
              type: object
              properties: {}
              required: []
            example: {}
      tags:
        - W6 · Conciliación
      description: Compara todos los pagos del grupo con reporte, ledger y saldos.
        Devuelve MATCHED con differences:[] o DIFFERENCES con incidencias OPEN.
        Detecta faltantes, duplicados, montos, estados, asientos y balances.
        Repetir no duplica incidencias. Corregir la causa y volver a ejecutar
        marca las anteriores RESOLVED. No mueve dinero ni corrige saldos. No
        requiere cuerpo.
      operationId: postReconciliations
      parameters:
        - name: X-Mock-Latency-Ms
          in: header
          required: false
          description: "Demora simulada por solicitud, en milisegundos. Entero de 0 a
            5000, predeterminado 0. Se aplica antes de enviar la respuesta,
            también en errores; no cambia el escenario ni retrasa otras
            solicitudes. Valor inválido: 400 INVALID_MOCK_LATENCY antes de
            ejecutar la operación."
          schema:
            type: integer
            minimum: 0
            maximum: 5000
            default: 0
          example: 1000
        - name: latency
          in: query
          required: false
          description: Latencia de la URL, entero de 0 a 5000 ms. El header
            X-Mock-Latency-Ms tiene prioridad si se envían ambos. Ambos valores
            deben ser válidos.
          schema:
            type: integer
            minimum: 0
            maximum: 5000
            default: 0
          example: 1000
  /control/reset:
    post:
      summary: Borrar datos locales y reponer semilla
      responses:
        "200":
          description: Consulta o repetición
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/Reset"
          headers:
            X-Mock-Latency-Ms:
              description: Demora simulada aplicada, en milisegundos.
              schema:
                type: integer
                minimum: 0
                maximum: 5000
        "400":
          description: JSON o campos inválidos.
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/Error"
          headers:
            X-Mock-Latency-Ms:
              description: Demora simulada aplicada, en milisegundos.
              schema:
                type: integer
                minimum: 0
                maximum: 5000
        "413":
          description: Cuerpo mayor a 65536 bytes.
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/Error"
          headers:
            X-Mock-Latency-Ms:
              description: Demora simulada aplicada, en milisegundos.
              schema:
                type: integer
                minimum: 0
                maximum: 5000
      requestBody:
        required: false
        content:
          application/json:
            schema:
              type: object
              properties: {}
              required: []
            example: {}
      tags:
        - Controles del mock
      description: Borra TODOS los datos del grupo y repone wallet-demo con 100000 y
        dos asientos de apertura. Elimina KYC, pagos, QRs, claves, eventos,
        reversos, soporte e incidencias. Afecta a todos los integrantes del
        grupo. No afecta otros grupos ni cambia su URL. Sin cuerpo. Funciona
        incluso al alcanzar el límite cloud.
      operationId: postControlReset
      parameters:
        - name: X-Mock-Latency-Ms
          in: header
          required: false
          description: "Demora simulada por solicitud, en milisegundos. Entero de 0 a
            5000, predeterminado 0. Se aplica antes de enviar la respuesta,
            también en errores; no cambia el escenario ni retrasa otras
            solicitudes. Valor inválido: 400 INVALID_MOCK_LATENCY antes de
            ejecutar la operación."
          schema:
            type: integer
            minimum: 0
            maximum: 5000
            default: 0
          example: 1000
        - name: latency
          in: query
          required: false
          description: Latencia de la URL, entero de 0 a 5000 ms. El header
            X-Mock-Latency-Ms tiene prioridad si se envían ambos. Ambos valores
            deben ser válidos.
          schema:
            type: integer
            minimum: 0
            maximum: 5000
            default: 0
          example: 1000
tags:
  - name: Servicio y grupos
    description: Disponibilidad, contrato OpenAPI y URLs fijas de los ocho grupos.
  - name: W1 · Registro y activación
    description: Crear cuentas de prueba, consultar KYC y resolver la revisión humana.
  - name: W2 · Pago a contacto
    description: Crear pagos, consultar su resultado, historial y comprobante.
      También se usa al confirmar pagos QR.
  - name: W3 · Pago QR comercio
    description: Generar y resolver QR de prueba antes de crear el pago en W2.
  - name: W4 · Idempotencia y callbacks
    description: Entregar eventos o repetirlos sin duplicar cargos. Los reintentos
      de creación se prueban con Idempotency-Key en POST /payments de W2.
  - name: W5 · Fallas y reversos
    description: Consultar resultados inciertos, simular reversos y revisar casos de
      soporte.
  - name: W6 · Conciliación
    description: Comparar wallet, proveedor y ledger; consultar incidencias y asientos.
  - name: Controles del mock
    description: Avanzar el proveedor, entregar eventos, alterar reportes y
      reiniciar los datos. Afectan solo al grupo actual.
components:
  schemas:
    Error:
      type: object
      properties:
        error:
          type: string
          description: Código estable del error.
        processed:
          type: boolean
        paymentId:
          type: string
          description: Pago creado aunque la respuesta sea 504.
        status:
          type: string
          enum:
            - PENDING
            - SUCCEEDED
            - REJECTED
            - REVERSED
      required:
        - error
    Health:
      type: object
      properties:
        status:
          type: string
          enum:
            - ok
        storage:
          type: string
          enum:
            - memory
        environment:
          type: string
        startedAt:
          type: string
        service:
          type: string
        groups:
          type: string
        openapi:
          type: string
      required:
        - status
        - storage
    Scenarios:
      type: object
      properties:
        kyc:
          type: array
          items:
            type: string
        payments:
          type: array
          items:
            type: string
        settlements:
          type: array
          items:
            type: string
      required:
        - kyc
        - payments
        - settlements
    Kyc:
      type: object
      properties:
        id:
          type: string
          description: ID de verificación KYC.
        wallet_id:
          type: string
          description: ID de la wallet creada.
        scenario:
          type: string
          enum:
            - APPROVED
            - REJECTED
            - MANUAL_REVIEW
        status:
          type: string
          enum:
            - ACTIVE
            - PENDING
            - REJECTED
      required:
        - id
        - wallet_id
        - scenario
        - status
    Wallet:
      type: object
      properties:
        id:
          type: string
        status:
          type: string
          enum:
            - ACTIVE
            - PENDING
            - REJECTED
        balance:
          type: integer
          description: Saldo contable en céntimos.
        reserved:
          type: integer
          description: Suma de pagos PENDING en céntimos.
        available:
          type: integer
          description: balance menos reserved.
        currency:
          type: string
          enum:
            - PEN
      required:
        - id
        - status
        - balance
        - reserved
        - available
        - currency
    Payment:
      type: object
      properties:
        id:
          type: string
        wallet_id:
          type: string
        recipient:
          type: string
          enum:
            - contact-demo
            - merchant-demo
        amount:
          type: integer
          description: Importe entero en céntimos de PEN.
          minimum: 1
          maximum: 100000000
        status:
          type: string
          enum:
            - PENDING
            - SUCCEEDED
            - REJECTED
            - REVERSED
        scenario:
          type: string
        idem:
          type: string
          description: Clave de idempotencia recibida.
        fingerprint:
          description: Dato interno. Array en Python, texto JSON del mismo array en cloud.
            No usar para construir la interfaz.
          oneOf:
            - type: array
              items:
                nullable: true
            - type: string
      required:
        - id
        - wallet_id
        - recipient
        - amount
        - status
        - scenario
        - idem
        - fingerprint
    ProviderPayment:
      type: object
      properties:
        id:
          type: string
          description: Mismo ID que el pago de la wallet.
        amount:
          type: integer
          description: Importe entero en céntimos de PEN.
          minimum: 1
          maximum: 100000000
        status:
          type: string
          enum:
            - PENDING
            - SUCCEEDED
            - REJECTED
            - REVERSED
      required:
        - id
        - amount
        - status
    Receipt:
      type: object
      properties:
        receiptId:
          type: string
        paymentId:
          type: string
        amountCents:
          type: integer
          description: Importe entero en céntimos de PEN.
          minimum: 1
          maximum: 100000000
        currency:
          type: string
          enum:
            - PEN
        recipient:
          type: string
        status:
          type: string
          enum:
            - SUCCEEDED
            - REVERSED
      required:
        - receiptId
        - paymentId
        - amountCents
        - currency
        - recipient
        - status
    Reversal:
      type: object
      properties:
        id:
          type: string
          description: ID del reverso, distinto al ID del pago.
        payment_id:
          type: string
        status:
          type: string
          enum:
            - PENDING
            - SUCCEEDED
      required:
        - id
        - payment_id
        - status
    PendingResolution:
      type: object
      properties:
        status:
          type: string
          enum:
            - PENDING
        escalated:
          type: boolean
          enum:
            - true
      required:
        - status
        - escalated
    Qr:
      type: object
      properties:
        id:
          type: string
        payload:
          type: string
          description: Texto qrmock:ID para codificar en QR.
        amountCents:
          type: integer
          description: Importe entero en céntimos de PEN.
          minimum: 1
          maximum: 100000000
          nullable: true
        currency:
          type: string
          enum:
            - PEN
      required:
        - id
        - payload
        - amountCents
        - currency
    ResolvedQr:
      type: object
      properties:
        merchantId:
          type: string
        merchantName:
          type: string
        amountCents:
          type: integer
          description: Importe entero en céntimos de PEN.
          minimum: 1
          maximum: 100000000
          nullable: true
        currency:
          type: string
          enum:
            - PEN
      required:
        - merchantId
        - merchantName
        - amountCents
        - currency
    Callback:
      type: object
      properties:
        duplicate:
          type: boolean
        payment:
          $ref: "#/components/schemas/Payment"
      required:
        - duplicate
    Event:
      type: object
      properties:
        id:
          type: string
          description: Usar como eventId o en /control/events/{id}/deliver.
        payment_id:
          type: string
        target:
          type: string
          enum:
            - SUCCEEDED
            - REJECTED
            - REVERSED
        delivered:
          type: integer
          description: 0 antes de procesar; 1 después. Repetir no lo incrementa.
      required:
        - id
        - payment_id
        - target
        - delivered
    LedgerEntry:
      type: object
      properties:
        id:
          type: integer
        operation:
          type: string
          description: ID del pago o opening para la semilla.
        kind:
          type: string
          enum:
            - FUNDING
            - PAYMENT
            - REVERSAL
        account:
          type: string
          description: ID de wallet, funding o clearing.
        amount:
          type: integer
          description: Movimiento con signo en céntimos. Cada par suma cero.
      required:
        - id
        - operation
        - kind
        - account
        - amount
    SupportCase:
      type: object
      properties:
        id:
          type: string
        resource:
          type: string
          description: ID de KYC o pago que requiere atención.
        reason:
          type: string
          enum:
            - KYC_REVIEW
            - UNKNOWN_PAYMENT_RESULT
            - PROVIDER_PENDING
        status:
          type: string
          enum:
            - OPEN
            - RESOLVED
      required:
        - id
        - resource
        - reason
        - status
    Incident:
      type: object
      properties:
        id:
          type: string
        payment_id:
          type: string
          description: ID del recurso afectado. Puede ser una wallet para BALANCE_MISMATCH.
        reason:
          type: string
          enum:
            - DUPLICATE_PROVIDER
            - MISSING_WALLET
            - MISSING_PROVIDER
            - AMOUNT_MISMATCH
            - STATUS_MISMATCH
            - LEDGER_MISMATCH
            - LEDGER_UNBALANCED
            - BALANCE_MISMATCH
        status:
          type: string
          enum:
            - OPEN
            - RESOLVED
      required:
        - id
        - payment_id
        - reason
        - status
    Reconciliation:
      type: object
      properties:
        status:
          type: string
          enum:
            - MATCHED
            - DIFFERENCES
        differences:
          type: array
          items:
            $ref: "#/components/schemas/Incident"
      required:
        - status
        - differences
    EventCreated:
      type: object
      properties:
        eventId:
          type: string
      required:
        - eventId
    Configured:
      type: object
      properties:
        configured:
          type: boolean
      required:
        - configured
    Reset:
      type: object
      properties:
        reset:
          type: boolean
      required:
        - reset
    OpenApi:
      type: object
      properties:
        openapi:
          type: string
        info:
          type: object
        paths:
          type: object
        servers:
          type: array
          items:
            type: object
      required:
        - openapi
        - info
        - paths
        - servers
  parameters:
    MockLatency:
      name: X-Mock-Latency-Ms
      in: header
      required: false
      description: "Demora simulada por solicitud, en milisegundos. Entero de 0 a
        5000, predeterminado 0. Se aplica antes de enviar la respuesta, también
        en errores; no cambia el escenario ni retrasa otras solicitudes. Valor
        inválido: 400 INVALID_MOCK_LATENCY antes de ejecutar la operación."
      schema:
        type: integer
        minimum: 0
        maximum: 5000
        default: 0
      example: 1000
    MockLatencyQuery:
      name: latency
      in: query
      required: false
      description: Latencia de la URL, entero de 0 a 5000 ms. El header
        X-Mock-Latency-Ms tiene prioridad si se envían ambos. Ambos valores
        deben ser válidos.
      schema:
        type: integer
        minimum: 0
        maximum: 5000
        default: 0
      example: 1000
