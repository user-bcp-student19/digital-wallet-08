# Requisitos de la validación biométrica real (futura, NO implementada)

Contrato para una entrega posterior (CA-11). En esta entrega solo existe el flujo mock
(`POST /wallets/{wallet_id}/profile/identity/mock-verification`), disponible únicamente con
`APP_ENV` = `development` o `testing`.

- Fotografías de ambas caras del DNI, máximo 2 MB cada una.
- Video de 5 a 10 segundos grabado con el celular, máximo 10 MB.
- Los metadatos del video deben indicar que fue grabado en los últimos 10 minutos.
- Se debe indicar al usuario que las imágenes sean nítidas.
- El usuario debe aceptar los términos y condiciones de tratamiento de datos personales (CA-10).
- Los datos personales y biométricos no se envían a analítica ni se registran en logs.
