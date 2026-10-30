# Trabajar en equipo

## Crear el repositorio del equipo

El líder crea el repositorio en su cuenta personal desde esta plantilla:

```sh
gh repo create crewai --template NTTData-Academy/crewai --public --clone
```

Agrega a tus compañeros como colaboradores con permiso de escritura en el repo del equipo.
Los demás integrantes clonan ese mismo repo:

```sh
gh repo clone <CAPTAIN>/crewai
cd crewai
```

## Repartir los archivos

Anota un responsable por archivo. Cada persona edita su propio agente. Consulta la tabla de responsabilidades, entregables y puntos de partida en [Mejora tu agente](MEJORA_TU_AGENTE.md#de-dónde-partir-según-tu-rol). Solo el equipo de siete añade Datos y persistencia.

- `agents/architect.py`: responsable pendiente. Define la solución y el contrato de API.
- `agents/backend.py`: responsable pendiente. Implementa el backend.
- `agents/frontend.py`: responsable pendiente. Implementa el frontend.
- `agents/testing.py`: responsable pendiente. Diseña las pruebas y sus comandos de ejecución.
- `agents/security.py`: responsable pendiente. Revisa riesgos y propone correcciones verificables.
- `agents/chapter.py`: responsable pendiente. Revisa todas las entregas y emite el veredicto final.

## Registrar responsables para el dashboard

Copia `team.example.json` a `team.json`, reemplaza los seis valores por usuarios reales de GitHub distintos y publica ese archivo en `main`. El dashboard lee `roles` para asociar cada agente con su responsable. Los nombres de ejemplo no son participantes.

## Entregar un cambio

1. Acuerden un requerimiento y sus criterios de aceptación.
2. Crea tu rama, por ejemplo `git switch -c agents/backend`.
3. Edita las instrucciones de tu agente en su archivo. Coordina los cambios de contratos con el arquitecto.
4. Ejecuta `python tools/verify.py`.
5. Publica tu rama y abre un PR hacia `main` del repo del líder. No envíes el PR al template de la organización.
6. Pide a un compañero que revise el cambio antes de integrarlo.

Una persona ejecuta el pipeline integrado desde `main`. El equipo participa en las aprobaciones
humanas y aporta feedback en cada etapa. Cada integrante conserva su propia `.env`, autenticación
y entorno virtual. No compartan checkpoints entre ejecuciones de distintas computadoras.

Los agentes generan texto y archivos. El agente de pruebas propone tests y comandos;
una persona los ejecuta y adjunta la salida real al PR. Un informe del modelo no demuestra que las pruebas pasaron.

## Equipo de siete (solo CrewAI)

El grupo de siete añade un responsable de **Datos y persistencia**, que edita
únicamente `agents/data.py` y entrega su propio PR. Los equipos de seis mantienen
sus seis roles. En `team.json`, solo el equipo de siete añade `"data": "usuario-real"`
dentro de `roles`, con un usuario distinto de los otros responsables.

Antes de iniciar un flujo nuevo, el líder del equipo de siete configura
`CREWAI_INCLUDE_DATA=true` en su `.env`. El orden será Especificación OpenSpec → Arquitectura → Datos y
persistencia → Backend → Frontend → Pruebas → Seguridad → Chapter. Cada etapa
mantiene aprobación, rechazo y reintento humanos. Especificación escribe
`openspec/changes/<feature>/proposal.md` y `specs/<capacidad>/spec.md`; Arquitectura
escribe `design.md`, `tasks.md` y `openapi.yaml` en ese mismo cambio. Datos produce
`openspec/changes/<feature>/reports/data_spec.md` y propuestas SQL en `openspec/changes/<feature>/code/db/`; no ejecuta migraciones. Backend usa ese contrato: escribe código FastAPI en `openspec/changes/<feature>/code/backend/app/` y pruebas en `code/backend/tests/`, ejecuta pytest y corrige hasta que pasen (bucle de retroalimentación en `crew/dev_loop.py`, máximo 12 iteraciones). Frontend usa el mismo bucle con perfil propio: escribe Angular en `code/frontend/` sin `ng new`, consume solo los endpoints listados del backend y debe dejar en verde `npm install`, `ng build` y `ng test` (máximo 20 iteraciones; `ng test` requiere Chrome). Su informe `reports/backend_spec.md` o `reports/frontend_spec.md` indica si las compuertas quedaron en verde; Chapter lo revisa.
Al aprobar una etapa de código, las tareas de `tasks.md` de esa etapa se marcan `- [x]` solo si las compuertas están en verde. Las secciones se identifican por la etiqueta `[backend]`, `[frontend]` o `[testing]` del encabezado. Para regenerar etapas ya aprobadas usa `python main.py --redo frontend` (o una lista separada por comas); se regenera la etapa indicada y todas las posteriores, y las anteriores se reutilizan sin volver a llamar al modelo. Los participantes mejoran las instrucciones iniciales de su agente.Por defecto la variable es `false`. Un checkpoint de seis etapas no se reutiliza
en el flujo de siete ni viceversa: conserva la carpeta `output/` con otro nombre
antes de cambiar el modo. No borres evidencia previa para cambiar de flujo.
