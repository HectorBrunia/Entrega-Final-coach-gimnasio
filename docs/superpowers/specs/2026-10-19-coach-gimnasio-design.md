# Coach de gimnasio con IA: diseño

**Fecha:** 2026-10-19
**Estado:** borrador para revisión
**Proyecto:** entrega final, AI Engineering

## 1. Objetivo

Un coach de entrenamiento conversacional que:

1. Crea un perfil del usuario (objetivo, días disponibles, equipo, lesiones).
2. Genera una rutina personalizada, con cada recomendación respaldada por una fuente citada.
3. Registra los entrenos del usuario y ajusta la progresión, explicando el motivo.

El sistema debe demostrar los requisitos de la rúbrica: RAG, agentes con Supervisor, API profesional, persistencia, validación con Pydantic, observabilidad y despliegue local con un comando.

## 2. Alcance

**Incluido**
- Onboarding por conversación y perfil persistente.
- Generación de rutina semanal.
- Registro de entrenos y ajuste semanal de la progresión.
- Filtro de seguridad por lesiones.
- Escalamiento a un profesional ante dolor agudo (human-in-the-loop).
- Trazas en Phoenix de cada paso del grafo.

**Excluido (no-objetivos)**
- Diagnóstico médico. El sistema lo declara explícitamente en cada respuesta relevante.
- Nutrición y suplementación.
- Interfaz gráfica propia. La interacción es vía API y documentación OpenAPI.
- Autenticación multiusuario de producción. Se usa un identificador de usuario simple.
- CI/CD y despliegue en la nube, que la rúbrica no evalúa.

## 3. Arquitectura

```
Cliente (HTTP)
   │
   ▼
FastAPI (async, Pydantic en entradas y salidas)
   │
   ▼
Supervisor (LangGraph) ──────────────────────────────────────────┐
   ├─► Evaluador    → extrae y actualiza el perfil               │
   ├─► Programador  → RAG híbrido (Qdrant) → arma la rutina      │
   ├─► Progreso     → lee historial (Postgres) → decide progresión│
   ├─► Seguridad    → filtro determinista de lesiones             │
   │                   └─ si falla, devuelve al Programador       │
   ├─► Pausa HITL   → dolor agudo: pausa y recomienda profesional │
   └─► Síntesis     → respuesta final con citas ──► END          │
                                                                 │
Checkpointer: Redis (estado del grafo por thread_id) ◄───────────┘
Persistencia de dominio: Postgres (usuarios, perfiles, entrenos, rutinas)
Vectores: Qdrant (ejercicios y guías)
Trazas: Phoenix (OpenInference sobre LangChain/LangGraph)
LLM: Gemini (con límite de tasa configurable)
```

**Decisión:** el checkpointer de LangGraph usa Redis, como en la pre-entrega de M7. Postgres guarda los datos de dominio, que tienen que consultarse y reportarse fuera del grafo. Son dos responsabilidades distintas.

## 4. Componentes

Cada unidad tiene una responsabilidad clara y se puede probar de forma aislada.

| Unidad | Responsabilidad | Depende de |
|---|---|---|
| `api/` | Rutas FastAPI, validación de entrada y salida | Servicios de dominio, grafo |
| `graph/` | Definición del Supervisor y los nodos | Agentes, checkpointer |
| `agents/` | Lógica de cada especialista | Herramientas, LLM |
| `tools/` | Funciones con esquemas Pydantic (volumen semanal, historial, búsqueda) | Repositorios, RAG |
| `rag/` | Ingesta y recuperación híbrida sobre Qdrant | Qdrant, embeddings |
| `safety/` | Reglas deterministas de contraindicaciones | Catálogo de ejercicios |
| `domain/` | Modelos Pydantic de perfil, rutina y entreno | Ninguna |
| `repositories/` | Acceso async a Postgres | SQLAlchemy async o asyncpg |
| `observability/` | Configuración de Phoenix y OpenInference | Ninguna |

## 5. Modelo de datos (Postgres)

- **usuarios** (`id`, `creado_en`)
- **perfiles** (`usuario_id`, `objetivo`, `dias_disponibles`, `equipo`, `nivel`, `actualizado_en`)
- **lesiones** (`usuario_id`, `zona`, `severidad`, `activa`, `registrada_en`)
- **rutinas** (`id`, `usuario_id`, `version`, `contenido` JSONB, `creada_en`)
- **entrenos** (`id`, `usuario_id`, `fecha`, `ejercicio_id`, `series`, `repeticiones`, `peso_kg`, `rpe`, `notas`)

**Decisiones:**
- `ejercicio_id` apunta al identificador del catálogo (free-exercise-db), no a una tabla propia del catálogo. Los metadatos del ejercicio viven en el catálogo versionado en el repo.
- Las rutinas se guardan versionadas. Así el ajuste nunca borra la rutina anterior, y las trazas pueden comparar versiones.
- Las migraciones se gestionan con Alembic.

## 6. Datos y RAG

**Catálogo de ejercicios**
- Fuente: free-exercise-db (GitHub). **Pendiente:** verificar la licencia antes de incluirlo en el repo público.
- Metadatos usados por el filtro de seguridad y por la búsqueda: músculo primario y secundarios, equipo, nivel, categoría e instrucciones.
- Se ingiere una vez al levantar el proyecto. Los vectores van a Qdrant y los metadatos quedan como payload.

**Guías de conocimiento**
- Textos propios, escritos a partir de fuentes abiertas: técnica, progresión (series, repeticiones, descanso), periodización básica y consideraciones por zona de lesión.
- Se citan con su fuente. No se copia texto literal de las fuentes.
- Son el corpus que justifica el RAG híbrido. El catálogo, por sí solo, podría consultarse con filtros.

**Recuperación híbrida**
- Búsqueda densa (embeddings) y dispersa (BM25 o sparse vectors de Qdrant), fusionadas en el servidor.
- Filtros por metadatos: equipo disponible, nivel, grupo muscular.
- Embeddings con `sentence-transformers` ejecutados en un hilo aparte para no bloquear el event loop.

## 7. Seguridad

**Principio:** el LLM nunca es la última línea de defensa en lesiones.

- Cada zona de lesión tiene un conjunto de ejercicios bloqueados, definido como regla estructurada (por ejemplo, `zona: hombro_derecho` bloquea `press_militar`, `elevaciones_frontales`).
- El filtro se aplica **antes** de que el Programador elija ejercicios y de nuevo al validar el plan final.
- Si una rutina contiene un ejercicio bloqueado, el Seguridad la rechaza y el Programador la rehace. Hay un máximo de reintentos. Si se agota, el sistema responde que no puede generar un plan seguro y sugiere consultar a un profesional.
- Si el usuario reporta **dolor agudo, o dolor que empeora durante un ejercicio**, el grafo entra en pausa HITL, no genera más recomendaciones de ese ejercicio y recomienda atención profesional.
- Cada respuesta con recomendaciones incluye un aviso de que no es diagnóstico médico.

## 8. Contrato de la API

Todas las entradas y salidas se validan con modelos Pydantic.

| Método | Ruta | Propósito |
|---|---|---|
| POST | `/usuarios` | Crea un usuario |
| POST | `/chat` | Envía un mensaje al coach (`thread_id` = usuario) |
| GET | `/usuarios/{id}/perfil` | Consulta el perfil |
| POST | `/usuarios/{id}/entrenos` | Registra un entreno |
| GET | `/usuarios/{id}/rutinas/actual` | Consulta la rutina vigente |
| POST | `/hitl/{thread_id}/reanudar` | Reanuda una conversación pausada |
| GET | `/health` | Estado de Postgres, Redis y Qdrant |

La documentación OpenAPI se genera automáticamente y se revisa con ejemplos de cada modelo.

## 9. Observabilidad

- Phoenix recibe las trazas por OpenTelemetry con instrumentación de OpenInference para LangChain y LangGraph.
- Cada traza muestra el nodo del Supervisor, cada recuperación del RAG con sus documentos, cada llamada al LLM y cada herramienta.
- Los registros de la aplicación incluyen `thread_id` y `usuario_id` para correlacionar con las trazas.

## 10. Evaluación

**Pruebas de sistema (mínimo 5, con traza en Phoenix)**
1. Onboarding completo: el perfil se extrae y la rutina respeta los días disponibles.
2. Ajuste semanal: el historial cambia la progresión y la explicación cita la guía.
3. Lesión activa: ningún ejercicio bloqueado aparece en la rutina.
4. Dolor agudo: el grafo pausa, no recomienda más ese ejercicio y pide atención profesional.
5. Pregunta fuera de alcance: el sistema rechaza con cortesía y no inventa.

**Golden set**
- Casos con respuesta esperada para medir la recuperación (qué documentos deben aparecer) y el filtro de seguridad (qué ejercicios nunca deben aparecer).
- El filtro de seguridad se prueba con pruebas unitarias deterministas, independientes del LLM.

## 11. Despliegue

`docker compose up` levanta:
- `api` (FastAPI)
- `worker` (si se usa cola para tareas largas; ver riesgos)
- `postgres`
- `redis` (checkpointer)
- `qdrant`
- `phoenix`

Un script `run.sh` (o `run.ps1` para Windows) ejecuta migraciones, ingesta del catálogo y arranque. Las credenciales van en `.env`, con un `.env.example` documentado.

Todas las versiones de imágenes Docker y dependencias se fijan, para que el proyecto sea reproducible.

## 12. Riesgos

| Riesgo | Mitigación |
|---|---|
| Límite del plan gratuito de Gemini | Límite de tasa configurable, caché de respuestas de ingesta, pocas llamadas por flujo |
| Licencia del catálogo | Verificar antes de incluir; si no es compatible, usar solo texto propio |
| Tiempo de reescritura al pasar a Qdrant | Fase inicial con un solo índice de prueba; el RAG se entrega antes de optimizar |
| Alcance excesivo | Lo excluido en la sección 2 queda fuera de la primera versión |
| Calidad de las guías | Escritas a partir de fuentes citadas y revisadas por una persona |

## 13. Decisiones tomadas

- Phoenix para observabilidad (sin cuentas externas).
- Qdrant como vector store (búsqueda híbrida nativa y cliente async).
- Catálogo de free-exercise-db más guías propias.
- Postgres local en Docker para el historial de entrenos.
- Redis como checkpointer de LangGraph.
- Gemini como LLM.

## 14. Pendiente antes de implementar

- Verificar la licencia de free-exercise-db.
- Definir las zonas de lesión y los ejercicios bloqueados por zona (lista inicial).
- Escribir las primeras guías propias con sus fuentes.
- Decidir si la cola de tareas (worker) es necesaria o si basta con procesar en línea. Por defecto, no se agrega.
