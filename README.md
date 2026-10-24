# Coach de gimnasio con IA

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

## Arranque en un comando

Requisitos: Docker con Docker Compose v2 y una API key de Google AI Studio (Gemini). En Linux o
macOS hace falta `curl`; en Windows basta PowerShell (o Git Bash para `run.sh`).

```bash
bash run.sh          # Linux, macOS o Git Bash
```

```powershell
powershell -ExecutionPolicy Bypass -File .\run.ps1    # Windows PowerShell
```

En Windows la política de ejecución por defecto (`Restricted`) impide lanzar `.\run.ps1`
directamente; el comando de arriba la omite solo para ese proceso, sin cambiar la
configuración del sistema. Desde Git Bash también sirve `bash run.sh`.

La primera ejecución copia `.env.example` a `.env` y se detiene: completa `GOOGLE_API_KEY` y
`GEMINI_MODEL` en `.env` y vuelve a ejecutar el mismo comando. Después el script:

1. `docker compose up -d --build --wait`: construye la imagen de la API y levanta `api`,
   `postgres`, `redis`, `qdrant` y `phoenix`. La API arranca cuando Postgres, Redis y Qdrant
   pasan su healthcheck.
2. `alembic upgrade head` dentro del contenedor `api`.
3. `python scripts/ingerir.py` dentro del contenedor `api`: ingiere el catálogo y las guías en
   Qdrant. La primera vez descarga los modelos de embeddings (quedan en el volumen
   `modelos_cache`).
4. Espera a que `GET /health` responda 200 (180 s como máximo; si no, muestra qué servicio está
   degradado y el final del log de la API).

Al terminar:

| Servicio | URL |
|---|---|
| API (OpenAPI) | http://localhost:8000/docs |
| Salud | http://localhost:8000/health |
| Phoenix (trazas) | http://localhost:6006 |

Volver a ejecutar el script es seguro: las migraciones ya aplicadas no se repiten y la ingesta
no recodifica nada si el corpus no cambió. Para detener los servicios: `docker compose stop`.

Qdrant usa la imagen `v1.20.0` (alineada con `qdrant-client` 1.20.0) y el volumen
`qdrant_data_v1_20`. El almacenamiento de versiones anteriores (`v1.12.4`, volumen
`qdrant_data`) no se puede abrir con `v1.20`, así que no se reutiliza. Su contenido es
derivado: el script vuelve a crear la colección y la ingiere. Si te quedó el volumen
antiguo, puedes borrarlo a mano cuando quieras con
`docker volume rm coach-gimnasio_qdrant_data`.

El mismo `.env` sirve para el compose y para ejecutar en local: dentro del contenedor `api`,
`docker-compose.yml` sustituye las URLs de `localhost` por los nombres de los servicios
(`postgres`, `redis`, `qdrant`, `phoenix`). La variable `COACH_ENV_FILE` permite usar otro
archivo de entorno en lugar de `.env`.

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
`gemini-2.5-flash-lite`) por los límites del plan gratuito; comprueba en Google AI Studio qué
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
| 6 pruebas de sistema con traza | [tests/sistema/test_escenarios.py](tests/sistema/test_escenarios.py): onboarding, ajuste semanal, lesión activa, lesión nueva, dolor agudo con pausa y reanudación y pregunta fuera de alcance; cada una comprueba que su traza llegó a Phoenix |
| README y diagrama | Este archivo (diagrama Mermaid del grafo) |
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

## Pruebas

Instalación local (Python 3.12 o superior):

```bash
python -m venv .venv
.venv/bin/pip install -e ".[dev]"      # Windows: .venv\Scripts\pip install -e ".[dev]"
pytest                                  # unitarias; excluye las de sistema
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
stack completo de docker: 6 pruebas pasadas (onboarding, ajuste semanal, lesión activa, lesión
nueva, dolor agudo con pausa y reanudación, fuera de alcance), cada una con su traza en Phoenix.

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
