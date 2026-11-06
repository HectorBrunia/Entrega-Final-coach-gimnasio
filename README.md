# Coach de gimnasio con IA

Una API FastAPI asíncrona recibe cada mensaje y lo pasa a un grafo de LangGraph donde un
Supervisor enruta entre nodos especialistas (Evaluador, Programador, Progreso, Seguridad, HITL y
Síntesis). Ninguna rutina llega al usuario sin pasar por `seguridad`, una capa determinista
(sin LLM) que filtra los ejercicios contraindicados por lesión y, ante la duda, falla cerrado y
pausa la conversación para revisión humana: el LLM nunca es la última línea de defensa. El
Programador arma las rutinas con un RAG híbrido (denso + BM25) sobre Qdrant, con fusión RRF en
el servidor. Postgres guarda los datos de dominio (perfiles, lesiones, entrenos, rutinas
versionadas) y Redis guarda el estado de la conversación como checkpointer del grafo; cada
petición deja su traza en Phoenix. Todo se levanta con un comando (`docker compose up -d`,
`bash run.sh` o `run.ps1`), incluso sin `.env` ni clave; y `python scripts/demo.py` muestra el
grafo funcionando sin Docker (ver [Guía rápida para la corrección](#guía-rápida-para-la-corrección)).

Coach de entrenamiento conversacional. A través de una API HTTP:

1. Construye el perfil del usuario conversando (objetivo, días disponibles, equipo, nivel y lesiones).
2. Genera una rutina semanal con ejercicios del catálogo, apoyada en guías recuperadas con RAG.
3. Registra los entrenos y ajusta la progresión a partir del historial.
4. Filtra de forma determinista los ejercicios contraindicados por lesión y, ante dolor agudo,
   pausa la conversación para revisión humana (HITL).

> **Aviso:** el coach no hace diagnósticos médicos. Las respuestas con recomendaciones incluyen
> el aviso «Esto no es un diagnóstico médico.» Ante dolor, lesión o enfermedad, consulta a un
> profesional sanitario.

No incluye interfaz gráfica: se usa desde la documentación OpenAPI (`/docs`) o cualquier cliente HTTP.

## Guía rápida para la corrección

Tres caminos, de menor a mayor requisito. Ninguno necesita tocar código. La clave de Gemini
**no** está en el repositorio: sin ella todo arranca y solo el coach conversacional responde
503 explicando qué falta configurar.

### A. Sin Docker ni clave (≈ 6-7 minutos: ~5 de instalación)

Requisito: Python 3.12 (la versión verificada; 3.13 no está verificada). Instala solo
dependencias de PyPI (torch en su build CPU, desde el índice extra que declara
`requirements.txt`); al ejecutar no descarga modelos ni usa la red.

Linux / macOS:

```bash
python3 -m venv .venv                  # Debian/Ubuntu: si falla, sudo apt install python3-venv
source .venv/bin/activate
pip install -r requirements-dev.txt
pytest -m "not sistema and not integracion"
python scripts/demo.py
```

Windows (PowerShell o cmd):

```powershell
py -3.12 -m venv .venv
.venv\Scripts\activate                 # PowerShell con política Restricted: Set-ExecutionPolicy -Scope Process Bypass
pip install -r requirements-dev.txt
pytest -m "not sistema and not integracion"
python scripts/demo.py
```

En Windows, clona en una ruta corta (p. ej. `C:\coach`): torch instala archivos con rutas muy
largas y, si la compatibilidad con rutas largas de Windows está desactivada, `pip` falla con
`OSError: [Errno 2] No such file or directory`. El entorno ocupa unos 3 GB en disco.

Resultado esperado (todos los comandos con el entorno virtual activado):

- `pytest -m "not sistema and not integracion"`: `906 passed, 20 deselected` (≈ 1 min). Las 20
  deseleccionadas son 13 de integración (necesitan Postgres/Redis del stack) y 7 de sistema
  (necesitan el stack y la clave de Gemini).
- `pytest` a secas: `906 passed, 13 skipped, 7 deselected` (algunos avisos de librerías son normales). Excluye por defecto las de sistema (7 deseleccionadas) y las de
  integración se omiten solas sin los servicios (`TEST_DATABASE_URL` sin definir, Redis
  inaccesible).
- `python scripts/demo.py`: conversación narrada en cinco escenarios bajo el título
  «MODO DEMO — LLM simulado; la lógica del grafo, el catálogo y las reglas de seguridad son
  reales», con código de salida 0 y última línea:
  `DEMO COMPLETADA: 5/5 escenarios correctos (sin Docker, sin red y sin clave de Gemini)`.
  Usa el grafo LangGraph compilado real, el catálogo real (876 ejercicios), las reglas de
  seguridad reales y el RAG sobre las guías reales en Qdrant en memoria; solo el LLM (salidas
  fijas por paso), la persistencia y los embeddings son simulados
  ([app/demo/](app/demo/)). Cada respuesta va rotulada `Coach [real]` (texto determinista del
  sistema: plantillas, rutina formateada, filtro de seguridad, 112) o `Coach [LLM simulado]`
  (texto guionado), y cada turno lista las salidas guionadas que pidió el grafo. Escenarios: (1) onboarding en dos mensajes → rutina con ids del
  catálogo; (2) lesión de hombro → el filtro determinista retira 4 ejercicios y rechaza un
  press de hombro propuesto; (3) dolor agudo → pausa HITL → reanudación; (4) dolor en el
  pecho → plantilla de urgencia con el 112; (5) pregunta fuera de alcance → sin plan.

### B. Con Docker, sin clave (≈ 8-10 minutos la primera vez; después ≈ 1-2 minutos)

Requisito: Docker con Compose v2.24 o superior. No hace falta `.env`.

```bash
docker compose up -d                   # o: bash run.sh   /   powershell -ExecutionPolicy Bypass -File .\run.ps1
curl http://localhost:8000/health
```

`docker compose up -d` construye la imagen, levanta Postgres, Redis, Qdrant y Phoenix, ejecuta
el servicio `init` (migraciones de Alembic + ingesta del catálogo y las guías en Qdrant; la
la imagen de la API ocupa ~2,4 GB y la primera vez se descargan además ~0,5 GB de modelos de embeddings) y arranca la API
cuando `init` termina. Respuesta esperada de `/health` (HTTP 200):

```json
{"status":"ok","servicios":{"postgres":"ok","redis":"ok","qdrant":"ok"},"llm":"no_configurado"}
```

- http://localhost:8000/docs abre la documentación OpenAPI.
- `curl -X POST http://localhost:8000/usuarios` → 201 `{"id":"<uuid>"}`; perfil, entrenos y
  rutina responden con normalidad.
- `POST /chat` (y `/hitl/{id}/reanudar`) → 503
  `{"detail":"Falta configurar GOOGLE_API_KEY (y GEMINI_MODEL) en .env para usar el coach conversacional"}`.

Si algún puerto (8000, 5432, 6379, 6333, 6006) está ocupado: `API_PORT=18000 docker compose up -d`
(también `POSTGRES_PORT`, `REDIS_PORT`, `QDRANT_PORT`, `PHOENIX_PORT`), o descomenta
`API_PORT=...` en `.env` (lo leen compose y `run.sh`/`run.ps1`). `run.sh` sin `.env` lo
copia desde `.env.example`, avisa de que falta la clave y sigue. Para detener y borrar todo:
`docker compose down -v`.

### C. Con Docker y clave de Gemini (flujo completo)

```bash
cp .env.example .env                   # Windows: copy .env.example .env
# editar .env: GOOGLE_API_KEY=<tu clave de Google AI Studio> y GEMINI_MODEL=gemini-3.5-flash-lite
bash run.sh                            # o: docker compose up -d   (si ya estaba levantado, recrea la api con la clave)
curl http://localhost:8000/health      # ... "llm":"configurado"
```

Flujo conversacional (detalle en [Ejemplo de uso](#ejemplo-de-uso)): `POST /usuarios`, luego
`POST /chat` con `{"usuario_id": "<uuid>", "mensaje": "Tengo 3 días, mancuernas y barra, quiero
ganar fuerza; soy principiante"}` → rutina validada con ejercicios del catálogo y el aviso
médico. Pruebas de sistema contra el stack y Gemini reales (consumen cuota):

```bash
export TEST_DATABASE_URL=postgresql+asyncpg://coach:coach@localhost:5432/coach_test
pytest tests/sistema -m sistema -v
```

La evidencia de esas pruebas (capturas de las trazas en Phoenix) está en
[docs/evidencia/](docs/evidencia/) y se describe en
[Evidencia: trazas de las pruebas de sistema](#evidencia-trazas-de-las-pruebas-de-sistema).

## Arranque en un comando

Requisitos: Docker con Docker Compose v2.24 o superior. La API key de Google AI Studio (Gemini)
es opcional para arrancar (sin ella `/chat` y `/hitl` responden 503 explicando qué falta). Para
`run.sh` en Linux o macOS hace falta `curl`; en Windows basta PowerShell (o Git Bash).

```bash
docker compose up -d   # cualquier sistema; con o sin .env
bash run.sh            # Linux, macOS o Git Bash: lo mismo y además espera a /health
```

```powershell
powershell -ExecutionPolicy Bypass -File .\run.ps1    # Windows PowerShell
```

En Windows la política de ejecución por defecto (`Restricted`) impide lanzar `.\run.ps1`
directamente; el comando de arriba la omite solo para ese proceso, sin cambiar la
configuración del sistema.

`docker compose up -d` basta desde un clon limpio:

1. Construye la imagen de la API (dependencias de `requirements.txt`, torch CPU) y levanta
   `postgres`, `redis`, `qdrant` y `phoenix`; los tres primeros con healthcheck.
2. Ejecuta el servicio de una sola vez `init` (misma imagen): `alembic upgrade head` y
   `python scripts/ingerir.py`, que ingiere el catálogo y las guías en Qdrant (idempotente). La
   primera vez descarga los modelos de embeddings (quedan en el volumen `modelos_cache`). Si la
   ingesta fallara (p. ej. sin red), lo avisa en su log y la API arranca igual sin RAG; se
   reintenta con `docker compose run --rm init`. Un fallo de las migraciones sí detiene el arranque.
3. Arranca `api` cuando `init` terminó bien (`service_completed_successfully`).

`.env` es opcional (`env_file` con `required: false`): todo lo que no es secreto tiene valor por
defecto. `run.sh` / `run.ps1` hacen lo mismo y además: si no existe `.env` lo copian desde
`.env.example`; si faltan `GOOGLE_API_KEY` o `GEMINI_MODEL` muestran un aviso y continúan; y
esperan a que `GET /health` responda 200 (300 s como máximo; si no, muestran qué servicio está
degradado y el final de los logs de `init` y `api`). Con la clave ya configurada, vuelve a
ejecutar el mismo comando para recrear la API con ella.

Al terminar:

| Servicio | URL |
|---|---|
| Chat web | http://localhost:8000/ |
| API (OpenAPI) | http://localhost:8000/docs |
| Salud | http://localhost:8000/health |
| Phoenix (trazas) | http://localhost:6006 |

Volver a ejecutar el comando es seguro: las migraciones ya aplicadas no se repiten y la ingesta
no recodifica nada si el corpus no cambió. Para detener los servicios: `docker compose stop`.

Qdrant usa la imagen `v1.20.0` (alineada con `qdrant-client` 1.20.0) y el volumen
`qdrant_data_v1_20`. El almacenamiento de versiones anteriores (`v1.12.4`, volumen
`qdrant_data`) no se puede abrir con `v1.20`, así que no se reutiliza. Su contenido es
derivado: el servicio `init` vuelve a crear la colección y la ingiere. Si te quedó el volumen
antiguo, puedes borrarlo a mano cuando quieras con
`docker volume rm coach-gimnasio_qdrant_data`.

El mismo `.env` sirve para el compose y para ejecutar en local: dentro del contenedor `api`,
`docker-compose.yml` sustituye las URLs de `localhost` por los nombres de los servicios
(`postgres`, `redis`, `qdrant`, `phoenix`). La variable `COACH_ENV_FILE` permite usar otro
archivo de entorno en lugar de `.env`, y `API_PORT`, `POSTGRES_PORT`, `REDIS_PORT`,
`QDRANT_PORT` y `PHOENIX_PORT` cambian los puertos del host.

### Chat web

En http://localhost:8000/ hay un chat mínimo para hablar con el coach desde el navegador
(`app/web/`: HTML, CSS y JavaScript sin dependencias ni compilación, servido por la misma API).
Crea el usuario automáticamente y lo recuerda en el navegador; "Nueva conversación" empieza con
un usuario nuevo. Cuando la respuesta incluye una rutina, la muestra como tablas por día a partir
de `GET /usuarios/{id}/rutinas/actual`, que incluye `nombres` (id del catálogo → nombre legible).
Si el coach pausa la conversación por dolor, aparece un aviso; la reanudación sigue siendo por
la API (`POST /hitl/{thread_id}/reanudar`).

### Ejemplo de uso

```bash
curl -X POST http://localhost:8000/usuarios                       # -> {"id": "<uuid>"}
curl -X POST http://localhost:8000/chat -H "Content-Type: application/json" \
  -d '{"usuario_id": "<uuid>", "mensaje": "Tengo 3 días, mancuernas y barra, quiero ganar fuerza"}'
curl -X POST http://localhost:8000/usuarios/<uuid>/entrenos -H "Content-Type: application/json" \
  -d '{"fecha": "2026-10-20", "ejercicio_id": "Barbell_Squat", "series": 3, "repeticiones": 8, "peso_kg": 60, "rpe": 7}'
curl http://localhost:8000/usuarios/<uuid>/rutinas/actual
```

`ejercicio_id` es el id del catálogo (`data/catalogo/exercises.json`); un id desconocido
responde 422.

`GET /usuarios/{id}/rutinas/actual` responde:

- 404 si el usuario aún no tiene rutina.
- 409 mientras hay una pausa HITL pendiente ("rutina en revisión").
- 409 si la rutina guardada contiene un ejercicio bloqueado por una lesión activa o excluido
  por dolor.
- 503 si el grafo o Redis no están disponibles. Sin el estado de la conversación no se puede
  saber si hay una revisión pendiente, así que falla cerrado.

El equipo del perfil se guarda con el vocabulario del catálogo (`barbell`, `dumbbell`,
`machine`, `cable`, `kettlebells`, `bands`, `cuerpo`, …): los sinónimos en español
("barra", "mancuernas", "máquinas", "poleas", "peso corporal", …) se traducen al validar el
perfil ([app/domain/equipo.py](app/domain/equipo.py)) y un equipo desconocido se ignora con
un aviso en el log. Así el filtro por equipo del programador acota de verdad los candidatos.

### Elección del modelo

`GEMINI_MODEL` es configurable. Se recomienda un modelo *flash-lite* (por ejemplo
`gemini-3.5-flash-lite`, el usado en las pruebas de sistema) por los límites del plan gratuito; comprueba en Google AI Studio qué
modelos tiene disponibles tu clave. `GEMINI_RPM` (14 por defecto) limita las peticiones por
minuto. Ante errores transitorios del proveedor (HTTP 429 y 5xx como 503 UNAVAILABLE) la
llamada se reintenta con espera exponencial ([app/llm.py](app/llm.py)); `LLM_REINTENTOS` (3),
`LLM_ESPERA_BASE` (2 s) y `LLM_ESPERA_MAX` (20 s) lo configuran. Si los reintentos se agotan,
`/chat` y `/hitl` responden 503 ("servicio del modelo saturado o caído"). Un error permanente
(clave o modelo inválidos, 4xx) no se reintenta y responde 503 ("error de configuración del
modelo"). En ambos casos el detalle va al log, nunca a la respuesta, y la API sigue en servicio.

Los modelos del RAG también salen del entorno: `EMBEDDING_MODEL` (embeddings densos) y
`BM25_MODELO` (BM25 disperso de fastembed, `Qdrant/bm25` por defecto, con `BM25_IDIOMA`).

## Arquitectura

```
Cliente HTTP ──► FastAPI (async, Pydantic) ──► Grafo LangGraph (Supervisor + especialistas)
                                                 │
   Postgres: usuarios, perfiles, lesiones, entrenos, rutinas versionadas (SQLAlchemy async + Alembic)
   Redis:    checkpointer del grafo por thread_id (= usuario_id), con AOF
   Qdrant:   catálogo y guías; búsqueda híbrida densa + BM25 con fusión RRF en el servidor
   Phoenix:  trazas OpenTelemetry con instrumentación OpenInference de LangChain/LangGraph
   Gemini:   LLM con límite de tasa y reintentos ante 429
```

| Carpeta | Contenido |
|---|---|
| [app/api](app/api) | Rutas FastAPI y esquemas Pydantic de entrada y salida |
| [app/agentes](app/agentes) | Grafo, nodos, estado y checkpointer de Redis |
| [app/herramientas](app/herramientas) | Funciones con esquemas Pydantic: búsqueda de conocimiento, historial, validación del plan, volumen semanal |
| [app/rag](app/rag) | Codificadores (sentence-transformers y BM25 de fastembed), ingesta y recuperación híbrida |
| [app/safety](app/safety) | Reglas deterministas de bloqueo por zona de lesión |
| [app/persistencia](app/persistencia) | Tablas y repositorio async de Postgres |
| [app/domain](app/domain) | Modelos de dominio (perfil, lesión, rutina, entreno, ejercicio) |
| [app/observabilidad.py](app/observabilidad.py) | Registro de Phoenix e instrumentación |
| [migrations](migrations) | Migraciones de Alembic |
| [scripts](scripts) | Ingesta, verificación de trazas, verificación de persistencia en Redis, revisión de bloqueos |
| [evaluacion](evaluacion) | Golden set, script de evaluación y resultados |

## De dónde sale cada pieza

Este proyecto ensambla y refactoriza las pre-entregas del curso; no reutiliza su dominio
(políticas internas de una empresa ficticia), sino sus patrones.

| Pre-entrega | Dónde vive ahora | Qué cambió y por qué |
|---|---|---|
| Unified Async LLM Client (cliente async) | [app/llm.py](app/llm.py) | Se conservan los reintentos con espera exponencial y la clasificación de errores del proveedor (transitorios 429/5xx/red frente a permanentes 4xx), ahora sobre `ChatGoogleGenerativeAI` de LangChain para que el grafo y las trazas lo usen tal cual. Se suma un limitador de tasa (`InMemoryRateLimiter`, `GEMINI_RPM`) por el plan gratuito. No se trajeron el multiproveedor (OpenAI/Anthropic), el fallback entre proveedores ni el streaming: solo se usa Gemini. |
| validated-extraction-pipeline (cadenas LCEL con contratos Pydantic) | [app/agentes/estado.py](app/agentes/estado.py), [app/agentes/nodos.py](app/agentes/nodos.py), [app/herramientas](app/herramientas) | El patrón `with_structured_output` + modelo Pydantic pasa a cada llamada al LLM (`AnalisisMensaje`, `DecisionSupervisor`, `PlanPropuesto`, `RespuestaConversacion`). Las herramientas validan entradas y salidas con `pydantic.validate_call`. El `with_retry` de la cadena lo reemplaza la política de reintentos de `app/llm.py`. |
| Sistema de recuperación semántica local (RAG, pre-entrega 3) y Sistema RAG escalable con Pinecone (pre-entrega 4) | [app/rag](app/rag), [scripts/ingerir.py](scripts/ingerir.py), [evaluacion](evaluacion) | Chroma y luego Pinecone + BM25 en memoria (`EnsembleRetriever`) se reemplazan por Qdrant con vectores densos y dispersos (BM25 de fastembed) en la misma colección y fusión RRF en el servidor, con `AsyncQdrantClient` y filtros por metadatos. Corre en docker sin cuentas externas. La evaluación con golden set se mantiene, con hit rate@5 y MRR@5 en lugar de Precision@5/Recall@5, y suma casos de seguridad. |
| Agente de razonamiento cíclico con memoria persistente (Módulo 5) | [app/agentes/checkpointer.py](app/agentes/checkpointer.py) | El checkpointer por `thread_id` pasa de `AsyncSqliteSaver` a `AsyncRedisSaver` (vía la pre-entrega 7), con Redis en modo AOF y un serializador propio que conserva los modelos Pydantic y los `UUID` del estado. El bucle ReAct en el que el LLM elige herramientas libremente no se trajo: aquí el enrutamiento lo decide el Supervisor con guardas deterministas. |
| Orquestador multi-agente especializado (Módulo 6) | [app/agentes](app/agentes) | Se mantiene la topología jerárquica: Supervisor con guardas deterministas alrededor del LLM y especialistas que no se hablan entre sí. El validador determinista del M6 pasa a ser el nodo `seguridad` (filtro de lesiones de [app/safety](app/safety)), con el mismo bucle de reparación acotado hacia el especialista. La tool RAG del investigador pasa a ser `buscar_conocimiento`, que usa el Programador. El analista con su calculadora no tiene equivalente. |
| API de producción y monitoreo activo (Módulo 7) | [app/api](app/api), [app/main.py](app/main.py), [app/observabilidad.py](app/observabilidad.py) | Se mantienen FastAPI async, el checkpointer `AsyncRedisSaver`, el HITL con `interrupt()` y reanudación por endpoint, y `GET /health` (ahora comprueba Postgres, Redis y Qdrant, y la app arranca degradada en vez de caerse). LangSmith se reemplaza por Phoenix local. La cola Arq, el worker y el estado de jobs en Redis no se trajeron (ver decisiones). |

## Decisiones de arquitectura

- **Qdrant en lugar de Pinecone.** Búsqueda híbrida densa + dispersa nativa con RRF en el
  servidor, cliente async y ejecución local en docker sin cuenta. Contra: hay que operar el
  servicio y fijar la versión de la imagen al cliente (ver arranque).
- **Phoenix en lugar de LangSmith.** Autoalojado en el compose, sin cuenta ni claves, con
  OpenTelemetry + OpenInference. Contra: no trae el costo por ejecución ni los paneles de
  LangSmith, y las trazas viven en el volumen local.
- **Postgres para el dominio, Redis para la conversación.** Perfiles, lesiones, entrenos y
  rutinas se consultan fuera del grafo (API, evaluación), así que van a tablas con migraciones;
  el estado del grafo por `thread_id` va al checkpointer. Contra: dos almacenes que mantener
  coherentes (por ejemplo, la rutina guardada y una pausa HITL pendiente).
- **Capa de seguridad determinista y falla cerrado.** El filtro por zona de lesión se aplica
  antes de elegir candidatos y otra vez en `seguridad`; una zona sin regla, el dolor agudo o un
  síntoma cardiaco van a HITL. Una señal del LLM solo cuenta si cita literalmente el mensaje
  actual. Contra: reglas amplias que bloquean de más y pausas por falsos positivos.
- **Nada de planes en texto libre.** Solo el camino `programador` → `seguridad` entrega
  rutinas; si la respuesta de la Síntesis parece una prescripción, se sustituye por un mensaje
  fijo (guarda por regex más la marca estructurada del LLM). Contra: alguna respuesta inocua
  se reemplaza.
- **Gemini flash-lite con límite de tasa y reintentos.** Pensado para el plan gratuito:
  `GEMINI_RPM` y espera exponencial ante 429/5xx; si se agotan, la API responde 503 y sigue en
  servicio. Contra: latencia mayor bajo carga y un solo proveedor.
- **Sin cola ni worker.** El spec lo dejó fuera por defecto: cada turno de `/chat` se procesa
  en línea y la pausa larga (HITL) ya la resuelve el checkpointer. Contra: una petición ocupa
  la conexión mientras el grafo corre.
- **Rutinas versionadas.** Cada ajuste crea una versión nueva (`usuario_id`, `version` únicos)
  en lugar de pisar la anterior, para poder comparar versiones. Contra: la tabla crece con el
  historial.
- **Dependencias inyectables.** `crear_app` recibe el grafo, el repositorio y las
  comprobaciones de salud; `construir_grafo` y `Nodos` reciben el LLM, el buscador y el
  checkpointer. Las pruebas usan dobles y `InMemorySaver` sin servicios reales. Contra: más
  parámetros en el arranque.

## Grafo de agentes

Definido en [app/agentes/grafo.py](app/agentes/grafo.py); los nodos están en
[app/agentes/nodos.py](app/agentes/nodos.py).

```mermaid
flowchart TD
    START([START]) --> evaluador
    evaluador["Evaluador<br/>extrae perfil y lesiones,<br/>detecta dolor agudo"] --> supervisor
    supervisor{"Supervisor<br/>guardas deterministas + LLM"}
    supervisor -->|rutina nueva o cambio| programador
    supervisor -->|ajuste según entrenos| progreso
    supervisor -->|"revisar rutina actual<br/>o lesión nueva con rutina"| seguridad
    supervisor -->|"preguntas generales,<br/>datos que faltan, fuera de alcance"| sintesis
    supervisor -->|"dolor agudo, zona sin regla<br/>o escalado del LLM"| hitl
    programador["Programador<br/>RAG híbrido + candidatos ya filtrados"] --> seguridad
    progreso["Progreso<br/>historial de entrenos"] --> seguridad
    seguridad{"Seguridad<br/>filtro determinista de lesiones"}
    seguridad -->|"ejercicios bloqueados y<br/>intentos < MAX_REINTENTOS_SEGURIDAD"| programador
    seguridad -->|"plan válido, o reintentos agotados<br/>(responde que no hay plan seguro)"| sintesis
    seguridad -->|requiere humano| hitl
    hitl["HITL<br/>interrupt(): pausa hasta<br/>POST /hitl/{thread_id}/reanudar"] --> END([END])
    sintesis["Síntesis<br/>respuesta final con aviso médico"] --> END
```

Detalles que el diagrama resume:

- El Evaluador es siempre el primer nodo. Si detecta dolor agudo (por palabra clave o por el
  LLM), retira ese ejercicio de la rutina guardada antes de la pausa.
- El Supervisor aplica guardas antes y después del LLM: si hace falta revisión humana o hay una
  lesión en una zona sin regla, va a HITL; sin perfil no se programa; sin rutina, `progreso` pasa
  a `programador` y `seguridad` a `sintesis`.
- Todo plan nuevo o ajustado pasa por Seguridad antes de guardarse. Seguridad evalúa primero
  `requiere_humano`, luego los bloqueados. El bucle Seguridad → Programador está acotado por
  `MAX_REINTENTOS_SEGURIDAD` (2 por defecto) y cada invocación tiene un límite de 25 pasos.
- Si el mensaje registra una lesión nueva en una zona con regla, el Evaluador retira en ese
  mismo turno, antes de cualquier pausa, los ejercicios que esa zona bloquea de la rutina
  guardada. Nunca se guarda una rutina vacía: si no queda ningún ejercicio seguro se rehace el
  plan o se responde que no hay un plan seguro y que consulte a un profesional.
- HITL usa `interrupt()` de LangGraph: el estado queda en el checkpointer de Redis y la
  conversación se reanuda con `POST /hitl/{thread_id}/reanudar`. Mientras la pausa está
  pendiente, `POST /chat` responde 409 (no la anula) y `GET /usuarios/{id}/rutinas/actual`
  responde 409 "rutina en revisión". Esa ruta también responde 409 si la rutina guardada tiene
  un ejercicio bloqueado por las lesiones activas o excluido por dolor. El mensaje de la pausa
  depende del motivo (dolor agudo, zona sin regla u otro) y sale de plantillas fijas.

## Requisitos de la rúbrica

| Requisito | Dónde se cumple |
|---|---|
| RAG | [app/rag](app/rag): búsqueda híbrida en Qdrant (embeddings densos de sentence-transformers + BM25 disperso de fastembed, fusión RRF en el servidor, filtros por metadatos). Corpus: catálogo y guías propias en [data/guias](data/guias). Ingesta: [scripts/ingerir.py](scripts/ingerir.py) |
| Agentes con Supervisor | [app/agentes/grafo.py](app/agentes/grafo.py): Supervisor que enruta a Evaluador, Programador, Progreso, Seguridad, HITL y Síntesis (diagrama arriba) |
| API | [app/api/rutas.py](app/api/rutas.py): `POST /usuarios`, `POST /chat`, `GET /usuarios/{id}/perfil`, `POST /usuarios/{id}/entrenos`, `GET /usuarios/{id}/rutinas/actual`, `POST /hitl/{thread_id}/reanudar`, `GET /health`; OpenAPI con ejemplos en `/docs` |
| Asincronía | Rutas `async`, SQLAlchemy async (asyncpg), `AsyncRedisSaver`, `AsyncQdrantClient`, llamadas al LLM con `ainvoke`; los embeddings corren en un hilo aparte (`en_hilo` en [app/rag/codificadores.py](app/rag/codificadores.py)); el filtro de seguridad usa un índice zona → ids bloqueados que se calcula una vez, fuera del event loop ([app/safety/reglas.py](app/safety/reglas.py)) |
| Checkpointer | [app/agentes/checkpointer.py](app/agentes/checkpointer.py): `AsyncRedisSaver` con serializador que conserva los tipos del estado; Redis con AOF y volumen ([docker-compose.yml](docker-compose.yml)); comprobación de reinicio con [scripts/verificar_persistencia_redis.py](scripts/verificar_persistencia_redis.py) |
| Pydantic | Esquemas de la API ([app/api/esquemas.py](app/api/esquemas.py)), modelos de dominio ([app/domain/modelos.py](app/domain/modelos.py)), herramientas validadas en tiempo de ejecución con `pydantic.validate_call` (entradas y salidas, [app/herramientas/funciones.py](app/herramientas/funciones.py); `volumen_semanal` resume las series por músculo de cada rutina nueva), salidas estructuradas del LLM y configuración con pydantic-settings ([app/settings.py](app/settings.py)) |
| Observabilidad | [app/observabilidad.py](app/observabilidad.py): Phoenix + OpenInference; cada petición a `/chat` y `/hitl/.../reanudar` abre un span con `thread_id` y `usuario_id`, del que cuelgan los spans del grafo y del LLM |
| 7 pruebas de sistema con traza | [tests/sistema/test_escenarios.py](tests/sistema/test_escenarios.py): onboarding (en un mensaje y repartido en dos), ajuste semanal, lesión activa, lesión nueva, dolor agudo con pausa y reanudación y pregunta fuera de alcance; cada una comprueba que su traza llegó a Phoenix |
| README y diagrama | Este archivo: diagrama Mermaid del grafo, [De dónde sale cada pieza](#de-dónde-sale-cada-pieza) y [Decisiones de arquitectura](#decisiones-de-arquitectura) |
| Despliegue local con un comando | [run.sh](run.sh) / [run.ps1](run.ps1), [docker-compose.yml](docker-compose.yml) y [Dockerfile](Dockerfile); imágenes y dependencias con versión fija |

## Seguridad

- Las reglas de [app/safety/reglas.py](app/safety/reglas.py) bloquean ejercicios por zona
  (`hombro_derecho`, `hombro_izquierdo`, `rodilla_derecha`, `rodilla_izquierda`, `zona_lumbar`)
  según músculos, patrones de nombre e ids explícitos. Solo aplican las lesiones activas.
- El filtro se aplica antes de que el Programador elija candidatos y otra vez en Seguridad. El
  LLM nunca es la última línea de defensa.
- Una lesión en una zona sin regla escala a HITL (falla cerrado). Al arrancar, la API valida
  las reglas contra el catálogo y no arranca si no encajan.
- La lista completa de bloqueos por zona está en
  [docs/revision/bloqueos-por-zona.md](docs/revision/bloqueos-por-zona.md) (generada con
  `scripts/generar_revision_bloqueos.py`).

## Trazas en Phoenix

Abre http://localhost:6006 y entra en el proyecto `coach-gimnasio`. Cada llamada a `/chat`
aparece como un span raíz `chat` (y `hitl_reanudar` al reanudar) con los atributos
`thread_id` y `usuario_id`; la sesión de Phoenix es el `thread_id`. Debajo están los nodos del
grafo, las llamadas a Gemini y la búsqueda de conocimiento. Los logs de la API incluyen el
mismo `thread_id` para correlacionarlos (`docker compose logs api`).

`python scripts/verificar_trazas.py` (desde el host) genera una traza con un LLM simulado y
comprueba en Phoenix que llegó.

### Evidencia: trazas de las pruebas de sistema

Capturas del dashboard de Phoenix tomadas tras ejecutar `pytest tests/sistema -m sistema` contra
Gemini real. Cada prueba envuelve sus llamadas en un span raíz `sistema.<escenario>` con los
atributos `escenario` y `tipo_prueba`, así que su árbol completo (API → LangGraph → nodos →
llamadas al LLM con sus tokens) se ve en una sola traza.

| Captura | Escenario que prueba |
|---|---|
| [Proyecto](docs/evidencia/00-proyecto-trazas.png) | Vista general del proyecto: total de trazas, tokens y latencias P50/P99 |
| [Onboarding en un mensaje](docs/evidencia/01-onboarding-completo.png) | Perfil completo en un mensaje y rutina validada |
| [Onboarding en dos mensajes](docs/evidencia/02-onboarding-dos-mensajes.png) | Perfil repartido en dos mensajes: plantilla fija de datos faltantes y, en el segundo, la rutina validada |
| [Ajuste semanal](docs/evidencia/03-ajuste-semanal.png) | Entrenos registrados y ajuste de la progresión citando guías |
| [Lesión activa](docs/evidencia/04-lesion-activa.png) | Lesión de hombro activa: ningún ejercicio bloqueado en la rutina guardada |
| [Dolor agudo](docs/evidencia/05-dolor-agudo.png) | Dolor agudo: pausa HITL y reanudación por `/hitl/{thread_id}/reanudar` |
| [Lesión nueva](docs/evidencia/06-lesion-nueva.png) | Lesión reportada a mitad de conversación: se retiran sus ejercicios de la rutina guardada |
| [Fuera de alcance](docs/evidencia/07-fuera-de-alcance.png) | Pregunta fuera de alcance: rechazo sin plan |

Algunas trazas figuran con estado `ERROR` porque las pruebas comprueban a propósito respuestas
4xx esperadas: el `GET` del perfil devuelve 404 mientras el perfil está incompleto y el de la
rutina devuelve 409 durante una pausa HITL. Son comportamientos correctos, no fallos.

Phoenix registra los tokens de cada llamada al LLM (columna *total tokens*), pero no el costo:
no tiene configurado el precio de Gemini.

## Pruebas

Instalación local (Python 3.12, la versión verificada; ver la
[Guía rápida para la corrección](#guía-rápida-para-la-corrección) para Windows). Todos los
comandos `pytest` de esta sección suponen el entorno virtual activado:

```bash
python3 -m venv .venv
source .venv/bin/activate                         # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
pytest -m "not sistema and not integracion"       # unitarias, sin servicios ni clave
pytest                                            # además intenta las de integración (se omiten sin servicios)
```

Las pruebas de integración de repositorios necesitan `TEST_DATABASE_URL` (una base cuyo nombre
termine en `_test`; el compose crea `coach_test`) y se omiten si no está definida.

### Pruebas de sistema (con tu propia clave)

Usan el stack real del compose y Gemini real, así que consumen cuota de tu clave:

```bash
bash run.sh   # o powershell -ExecutionPolicy Bypass -File .\run.ps1: deja el stack levantado
export TEST_DATABASE_URL=postgresql+asyncpg://coach:coach@localhost:5432/coach_test
pytest tests/sistema -m sistema -v
```

En PowerShell: `$env:TEST_DATABASE_URL = "postgresql+asyncpg://coach:coach@localhost:5432/coach_test"`.

Leen `GOOGLE_API_KEY` y `GEMINI_MODEL` de `.env` (las URLs de `localhost` de `.env.example`
sirven tal cual). Usan la base `coach_test` y la colección `<QDRANT_COLLECTION>_test`, nunca las
de la aplicación. Si falta la clave o algún servicio, se omiten con el motivo.

Para ver sus trazas: en Phoenix, proyecto `coach-gimnasio`, filtra por
`name == 'sistema.<escenario>'` (por ejemplo `sistema.onboarding_completo`; los escenarios son `onboarding_completo`,
`ajuste_semanal`, `lesion_activa`, `lesion_nueva`, `dolor_agudo` y `fuera_de_alcance`) o por la etiqueta
`sistema`. Cada prueba falla si su traza no llega a Phoenix en unos 15 s.

## Evaluación

`python evaluacion/evaluar.py` (desde el host, con el stack levantado y la ingesta hecha) evalúa
el [golden set](evaluacion/golden_set.json) y escribe
[evaluacion/resultados.json](evaluacion/resultados.json). Resultados actuales
(2026-10-22, k = 5, embeddings `paraphrase-multilingual-MiniLM-L12-v2`):

| Parte | Resultado |
|---|---|
| Recuperación | 13 casos, 12 aciertos: hit rate@5 = 0,923, MRR@5 = 0,769 (falla R12) |
| Seguridad determinista | 5 casos: 0 violaciones, 0 sobrebloqueos, 0 ids fuera del catálogo |
| Seguridad del grafo | 5 casos, 5 rutinas generadas: 0 violaciones, 0 respuestas sin aviso (Gemini real, modelo `gemini-3.5-flash-lite`) |

La seguridad del grafo pide rutinas reales a Gemini y comprueba que la rutina guardada no
contiene ejercicios bloqueados; se ejecuta cuando están configuradas `GOOGLE_API_KEY` y
`TEST_DATABASE_URL`, y consume la cuota de tu clave.

### Resultados de las pruebas de sistema

`pytest tests/sistema -m sistema` contra Gemini real (modelo `gemini-3.5-flash-lite`) con el
stack completo de docker: 7 pruebas pasadas (onboarding en un mensaje, onboarding repartido en
dos mensajes, ajuste semanal, lesión activa, lesión nueva, dolor agudo con pausa y reanudación,
fuera de alcance), cada una con su traza en Phoenix.

## Fuentes y licencias

- **Catálogo de ejercicios:** [free-exercise-db](https://github.com/yuhonas/free-exercise-db),
  876 ejercicios, dominio público (Unlicense). Copia de la licencia en
  [data/catalogo/LICENSE-free-exercise-db.txt](data/catalogo/LICENSE-free-exercise-db.txt).
- **Guías** ([data/guias](data/guias)): resúmenes originales redactados para este proyecto a
  partir de fuentes abiertas que cada guía cita; no reproducen texto de las fuentes.

## Limitaciones conocidas

- **Reglas de seguridad deliberadamente amplias.** Ante la duda se bloquea; por ejemplo, con
  hombro lesionado quedan bloqueados 612 de 876 ejercicios. El listado completo por zona está en
  [docs/revision/bloqueos-por-zona.md](docs/revision/bloqueos-por-zona.md) y fue revisado por el
  autor: el criterio conservador es intencional (mejor prevenir que curar).
- **Detección de dolor agudo y síntomas cardiacos limitada.** Se basa en un léxico determinista
  en español (raíces y frases sobre el mensaje actual) y, como segunda red, en el LLM, cuya
  señal solo cuenta si cita literalmente el mensaje actual. No reconoce todas las formas de
  describir un síntoma. El coach no es un dispositivo médico ni sustituye una valoración
  profesional. Los síntomas cardiacos se clasifican en tres niveles: (1) síntomas inequívocos
  (dolor, presión o pesadez en el pecho, dificultad respiratoria grave, desmayo o pérdida de
  conocimiento, sudor frío, palpitaciones, brazo izquierdo dormido) pausan con un mensaje fijo
  que indica llamar al 112; (2) el LLM puede marcar otros síntomas (`sintoma_cardiaco`, con cita
  literal del mensaje) y también dan ese mensaje; (3) términos ambiguos de entrenamiento
  (frecuencia cardiaca, «sin aliento» al hablar de mejorar el fondo, pecho cargado de agujetas)
  nunca dan el 112 por sí solos y solo pausan si van con una señal de dolor. Por eso un sinónimo
  raro que el léxico no reconoce depende del LLM. Los falsos positivos (pausas de más ante
  frases inocuas) son deliberados.
