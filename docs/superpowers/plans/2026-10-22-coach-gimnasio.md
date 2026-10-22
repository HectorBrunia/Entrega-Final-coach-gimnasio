# Coach de gimnasio con IA: Plan de implementación

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Construir un coach de entrenamiento conversacional con RAG híbrido, Supervisor de agentes en LangGraph, API FastAPI async, persistencia y trazas en Phoenix, levantable con `docker compose up`.

**Architecture:** FastAPI delega cada mensaje a un grafo LangGraph con un Supervisor y cinco nodos especialistas. El estado del grafo se persiste en Redis (checkpointer). Los datos de dominio (perfiles, lesiones, rutinas, entrenos) van a Postgres. El conocimiento (ejercicios y guías) se recupera de Qdrant con búsqueda híbrida. Las reglas de seguridad son un filtro determinista, no una decisión del LLM.

**Tech Stack:** Python 3.12+, FastAPI, Pydantic v2, LangGraph, langgraph-checkpoint-redis, LangChain, Gemini (`langchain-google-genai`), Qdrant (`qdrant-client`), sentence-transformers, SQLAlchemy 2 async + asyncpg, Alembic, Redis Stack, Arize Phoenix + OpenInference, pytest + pytest-asyncio, Docker Compose.

**Spec:** [docs/superpowers/specs/2026-10-19-coach-gimnasio-design.md](../specs/2026-10-19-coach-gimnasio-design.md)

## Global Constraints

- Python 3.12 o superior.
- Todo el I/O (LLM, Postgres, Redis, Qdrant, HTTP) es `async`. Prohibido `requests` dentro de funciones `async def`; usar `httpx` o SDKs async.
- Ningún ID de modelo, índice, colección, URL ni clave en el código. Todo sale de variables de entorno cargadas en `app/settings.py`.
- Todas las entradas y salidas de la API y de las herramientas de los agentes se validan con modelos Pydantic v2.
- `langgraph>=1.0`, `langgraph-checkpoint-redis>=0.1`, `fastapi>=0.115`, `pydantic>=2.7`.
- Redis Stack (módulos JSON y Search) requerido por el checkpointer.
- Cada respuesta con recomendaciones incluye el aviso: "Esto no es un diagnóstico médico."
- El dolor agudo activa la pausa HITL; el sistema no genera más recomendaciones para ese ejercicio.
- Las imágenes Docker y las dependencias se fijan a una versión concreta.

## Review Focus

1. **Lesión reportada a mitad de conversación con una rutina ya generada.** Esperado: la rutina se revalida y los ejercicios bloqueados se retiran antes de responder. Prueba en Task 8.
2. **El filtro de seguridad deja cero ejercicios disponibles.** Esperado: respuesta explícita que pide consultar a un profesional, sin rutina vacía ni error 500. Prueba en Task 4.
3. **Límite de tasa de Gemini (HTTP 429).** Esperado: reintento con espera y, si se agota, respuesta de error controlada con código 503. Prueba en Task 8.
4. **Reinicio de Redis en medio de una conversación.** Esperado: la conversación retoma desde el último checkpoint guardado. Prueba en Task 8.
5. **Registro de entreno con un `ejercicio_id` que no existe en el catálogo.** Esperado: error 422 con mensaje claro, no 500. Prueba en Task 9.

---

### Task 1: Scaffolding, configuración y compose base

**Files:**
- Create: `pyproject.toml`
- Create: `app/__init__.py`
- Create: `app/settings.py`
- Create: `.env.example`
- Create: `.gitignore`
- Create: `docker-compose.yml`
- Test: `tests/test_settings.py`

**Interfaces:**
- Consumes: nada.
- Produces: `Settings` (pydantic-settings) con los campos `database_url: str`, `redis_url: str`, `qdrant_url: str`, `qdrant_collection: str`, `google_api_key: SecretStr`, `gemini_model: str`, `gemini_rpm: int`, `phoenix_collector_endpoint: str`, `max_reintentos_seguridad: int` (por defecto 2), `embedding_model: str`. Función `get_settings() -> Settings` cacheada.

- [ ] **Step 1: Escribir la prueba que falla**

```python
# tests/test_settings.py
import pytest
from pydantic import ValidationError
from app.settings import Settings

def test_carga_desde_entorno(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://u:p@localhost/db")
    monkeypatch.setenv("REDIS_URL", "redis://localhost:6379/0")
    monkeypatch.setenv("QDRANT_URL", "http://localhost:6333")
    monkeypatch.setenv("QDRANT_COLLECTION", "ejercicios")
    monkeypatch.setenv("GOOGLE_API_KEY", "x")
    monkeypatch.setenv("GEMINI_MODEL", "gemini-test")
    monkeypatch.setenv("GEMINI_RPM", "14")
    monkeypatch.setenv("PHOENIX_COLLECTOR_ENDPOINT", "http://localhost:6006/v1/traces")
    monkeypatch.setenv("EMBEDDING_MODEL", "modelo-test")
    s = Settings()
    assert s.gemini_rpm == 14
    assert s.max_reintentos_seguridad == 2

def test_falla_sin_variable_obligatoria(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    with pytest.raises(ValidationError):
        Settings(_env_file=None)
```

- [ ] **Step 2: Ejecutar la prueba y verificar que falla**

Run: `pytest tests/test_settings.py -v`
Expected: FAIL con `ModuleNotFoundError: No module named 'app.settings'`

- [ ] **Step 3: Implementar `Settings` en `app/settings.py`**

Clase `Settings(BaseSettings)` con los campos de Interfaces. `google_api_key` como `SecretStr`. `max_reintentos_seguridad` con valor por defecto `2`. `get_settings()` decorada con `functools.lru_cache`.

Crear `pyproject.toml` con las dependencias de Global Constraints. `docker-compose.yml` con servicios `postgres` (imagen fija `postgres:16`), `redis` (imagen fija `redis/redis-stack:7.4.0-v3`), `qdrant` (imagen fija `qdrant/qdrant:v1.12.4`) y `phoenix` (imagen fija `arizephoenix/phoenix:version-6.0.0`). Verificar la versión vigente de cada imagen al implementar y fijarla. `.env.example` lista cada variable de `Settings` con comentario.

- [ ] **Step 4: Ejecutar la prueba y verificar que pasa**

Run: `pytest tests/test_settings.py -v`
Expected: 2 passed

- [ ] **Step 5: Validar el compose**

Run: `docker compose config --quiet`
Expected: sin salida y código de salida 0

- [ ] **Step 6: Inicializar git y comitear**

```bash
git init
git add .
git commit -m "chore: scaffolding, configuración y compose base"
```

---

### Task 2: Modelos de dominio

**Files:**
- Create: `app/domain/__init__.py`
- Create: `app/domain/modelos.py`
- Test: `tests/test_modelos.py`

**Interfaces:**
- Consumes: nada.
- Produces: `Nivel` (enum: `principiante`, `intermedio`, `avanzado`); `Perfil(usuario_id: UUID, objetivo: str, dias_disponibles: int, equipo: list[str], nivel: Nivel)`; `Lesion(zona: str, severidad: Literal["leve","moderada","grave"], activa: bool)`; `Ejercicio(id: str, nombre: str, musculo_primario: str, musculos_secundarios: list[str], equipo: str, nivel: Nivel, instrucciones: list[str])`; `EntrenoRegistro(usuario_id: UUID, fecha: date, ejercicio_id: str, series: int, repeticiones: int, peso_kg: float, rpe: int, notas: str | None)`; `Rutina(usuario_id: UUID, version: int, dias: list[DiaRutina])`; `DiaRutina(nombre: str, ejercicios: list[EjercicioPlanificado])`; `EjercicioPlanificado(ejercicio_id: str, series: int, repeticiones: str, descanso_seg: int, fuentes: list[str])`.

- [ ] **Step 1: Escribir las pruebas que fallan**

```python
# tests/test_modelos.py
import pytest
from pydantic import ValidationError
from app.domain.modelos import Perfil, EntrenoRegistro, Nivel
from uuid import uuid4
from datetime import date

def test_perfil_rechaza_dias_fuera_de_rango():
    with pytest.raises(ValidationError):
        Perfil(usuario_id=uuid4(), objetivo="masa", dias_disponibles=8, equipo=[], nivel=Nivel.principiante)

def test_entreno_rechaza_rpe_fuera_de_rango():
    with pytest.raises(ValidationError):
        EntrenoRegistro(usuario_id=uuid4(), fecha=date(2026,10,1), ejercicio_id="press_banca",
                        series=3, repeticiones=8, peso_kg=20, rpe=11, notas=None)

def test_nivel_rechaza_valor_desconocido():
    with pytest.raises(ValidationError):
        Perfil(usuario_id=uuid4(), objetivo="masa", dias_disponibles=3, equipo=[], nivel="experto")
```

- [ ] **Step 2: Ejecutar las pruebas y verificar que fallan**

Run: `pytest tests/test_modelos.py -v`
Expected: FAIL con `ModuleNotFoundError`

- [ ] **Step 3: Implementar los modelos en `app/domain/modelos.py`**

Usar los nombres y tipos de Interfaces. `dias_disponibles` con `Field(ge=1, le=7)`. `rpe` con `Field(ge=1, le=10)`. `series` y `repeticiones` con `ge=1`. `peso_kg` con `ge=0`.

- [ ] **Step 4: Ejecutar las pruebas y verificar que pasan**

Run: `pytest tests/test_modelos.py -v`
Expected: 3 passed

- [ ] **Step 5: Comitear**

```bash
git add app/domain tests/test_modelos.py
git commit -m "feat: modelos de dominio con validación Pydantic"
```

---

### Task 3: Cargador del catálogo de ejercicios

**Files:**
- Create: `app/catalogo/__init__.py`
- Create: `app/catalogo/cargador.py`
- Create: `tests/fixtures/catalogo_muestra.json`
- Test: `tests/test_cargador.py`

**Interfaces:**
- Consumes: `Ejercicio`, `Nivel` de Task 2.
- Produces: `cargar_catalogo(ruta: Path) -> list[Ejercicio]`. Lanza `CatalogoInvalido` si un registro no cumple el modelo.

- [ ] **Step 1: Crear el fixture y la prueba que falla**

`tests/fixtures/catalogo_muestra.json` con tres ejercicios en el formato de free-exercise-db (campos `id`, `name`, `primaryMuscles`, `secondaryMuscles`, `equipment`, `level`, `instructions`). Incluir un ejercicio con `equipment: null` y otro con nivel en mayúsculas.

```python
# tests/test_cargador.py
from pathlib import Path
from app.catalogo.cargador import cargar_catalogo
FIXTURE = Path(__file__).parent / "fixtures" / "catalogo_muestra.json"

def test_carga_tres_ejercicios_normalizados():
    ejercicios = cargar_catalogo(FIXTURE)
    assert len(ejercicios) == 3
    assert all(e.nivel in {"principiante","intermedio","avanzado"} for e in ejercicios)

def test_equipo_nulo_se_normaliza_a_cuerpo():
    ejercicios = cargar_catalogo(FIXTURE)
    assert any(e.equipo == "cuerpo" for e in ejercicios)
```

- [ ] **Step 2: Ejecutar la prueba y verificar que falla**

Run: `pytest tests/test_cargador.py -v`
Expected: FAIL con `ModuleNotFoundError`

- [ ] **Step 3: Implementar `cargar_catalogo` en `app/catalogo/cargador.py`**

Leer el JSON con `json.loads`. Mapear los campos del formato fuente a `Ejercicio`. Normalizar `level` a minúsculas. Reemplazar `equipment` nulo por `"cuerpo"`. Convertir cada registro inválido en `CatalogoInvalido` con el `id` del ejercicio en el mensaje.

- [ ] **Step 4: Ejecutar la prueba y verificar que pasa**

Run: `pytest tests/test_cargador.py -v`
Expected: 2 passed

- [ ] **Step 5: Comitear**

```bash
git add app/catalogo tests/test_cargador.py tests/fixtures
git commit -m "feat: cargador del catálogo de ejercicios"
```

---

### Task 4: Filtro de seguridad por lesiones

**Files:**
- Create: `app/safety/__init__.py`
- Create: `app/safety/reglas.py`
- Test: `tests/test_seguridad.py`

**Interfaces:**
- Consumes: `Ejercicio`, `Lesion` de Task 2.
- Produces: `REGLAS_LESION: dict[str, frozenset[str]]` que mapea zona (por ejemplo `hombro_derecho`) a los `ejercicio_id` bloqueados. `FiltroResultado(permitidos: list[Ejercicio], bloqueados: list[tuple[str, str]])` donde cada bloqueado es `(ejercicio_id, zona)`. `filtrar_por_lesiones(ejercicios: list[Ejercicio], lesiones: list[Lesion]) -> FiltroResultado`. Solo considera lesiones con `activa=True`.

- [ ] **Step 1: Escribir las pruebas que fallan**

```python
# tests/test_seguridad.py
from app.safety.reglas import filtrar_por_lesiones
from app.domain.modelos import Ejercicio, Lesion, Nivel

def _ej(id_):
    return Ejercicio(id=id_, nombre=id_, musculo_primario="hombro", musculos_secundarios=[],
                     equipo="mancuernas", nivel=Nivel.principiante, instrucciones=[])

def test_hombro_derecho_bloquea_press_militar():
    res = filtrar_por_lesiones([_ej("press_militar"), _ej("curl_biceps")],
                               [Lesion(zona="hombro_derecho", severidad="moderada", activa=True)])
    assert [e.id for e in res.permitidos] == ["curl_biceps"]
    assert ("press_militar", "hombro_derecho") in res.bloqueados

def test_lesion_inactiva_no_bloquea():
    res = filtrar_por_lesiones([_ej("press_militar")],
                               [Lesion(zona="hombro_derecho", severidad="leve", activa=False)])
    assert len(res.permitidos) == 1

def test_sin_permitidos_devuelve_lista_vacia_sin_error():
    res = filtrar_por_lesiones([_ej("press_militar")],
                               [Lesion(zona="hombro_derecho", severidad="grave", activa=True)])
    assert res.permitidos == []
```

- [ ] **Step 2: Ejecutar las pruebas y verificar que fallan**

Run: `pytest tests/test_seguridad.py -v`
Expected: FAIL con `ModuleNotFoundError`

- [ ] **Step 3: Implementar `reglas.py`**

Definir `REGLAS_LESION` con al menos `hombro_derecho` y `hombro_izquierdo` (bloquean `press_militar`, `elevaciones_frontales`). Mantener la lista pequeña y explícita; las reglas completas se curan en el pendiente de la especificación. `filtrar_por_lesiones` une las zonas activas y separa permitidos de bloqueados.

- [ ] **Step 4: Ejecutar las pruebas y verificar que pasan**

Run: `pytest tests/test_seguridad.py -v`
Expected: 3 passed

- [ ] **Step 5: Comitear**

```bash
git add app/safety tests/test_seguridad.py
git commit -m "feat: filtro determinista de seguridad por lesiones"
```

---

### Task 5: Repositorios de Postgres y migración inicial

**Files:**
- Create: `app/persistencia/__init__.py`
- Create: `app/persistencia/tablas.py`
- Create: `app/persistencia/repositorios.py`
- Create: `alembic.ini`, `migrations/env.py`, `migrations/versions/0001_inicial.py`
- Test: `tests/test_repositorios.py` (integración, requiere el servicio `postgres` del compose)

**Interfaces:**
- Consumes: `Perfil`, `Lesion`, `Rutina`, `EntrenoRegistro`, `DiaRutina` de Task 2; `Settings.database_url` de Task 1.
- Produces: `crear_motor(url: str) -> AsyncEngine`; clase `RepositorioDominio` con `__init__(self, sesion_factory: async_sessionmaker)` y métodos async: `guardar_perfil(perfil: Perfil) -> None`, `obtener_perfil(usuario_id: UUID) -> Perfil | None`, `agregar_lesion(usuario_id: UUID, lesion: Lesion) -> None`, `lesiones_activas(usuario_id: UUID) -> list[Lesion]`, `guardar_rutina(rutina: Rutina) -> None` (la versión la asigna el repositorio), `rutina_actual(usuario_id: UUID) -> Rutina | None`, `registrar_entreno(entreno: EntrenoRegistro) -> None`, `historial(usuario_id: UUID, limite: int) -> list[EntrenoRegistro]`.

- [ ] **Step 1: Escribir la prueba de integración que falla**

```python
# tests/test_repositorios.py
import pytest
from uuid import uuid4
from app.persistencia.repositorios import RepositorioDominio
from app.domain.modelos import Perfil, Nivel

pytestmark = pytest.mark.integracion

@pytest.mark.asyncio
async def test_guardar_y_obtener_perfil(sesion_factory):
    repo = RepositorioDominio(sesion_factory)
    uid = uuid4()
    await repo.guardar_perfil(Perfil(usuario_id=uid, objetivo="masa", dias_disponibles=4,
                                     equipo=["mancuernas"], nivel=Nivel.principiante))
    perfil = await repo.obtener_perfil(uid)
    assert perfil is not None and perfil.dias_disponibles == 4
```

`sesion_factory` es un fixture en `tests/conftest.py` que crea el motor desde `Settings.database_url`, corre `alembic upgrade head` y limpia las tablas al final.

- [ ] **Step 2: Ejecutar la prueba y verificar que falla**

Run: `docker compose up -d postgres && pytest tests/test_repositorios.py -v -m integracion`
Expected: FAIL con `ModuleNotFoundError: No module named 'app.persistencia'`

- [ ] **Step 3: Implementar tablas, repositorio y migración**

En `tablas.py` declarar las tablas de la especificación (sección 5) con SQLAlchemy 2 (`Mapped`, `mapped_column`). `rutinas.contenido` como `JSONB`. Índice único `(usuario_id, version)` en `rutinas`. En `repositorios.py` implementar los métodos de Interfaces usando `async with sesion_factory() as s`. `guardar_rutina` calcula `version = max(version)+1` dentro de la misma transacción.

Generar la migración con `alembic revision --autogenerate -m inicial` y revisarla antes de comitear.

- [ ] **Step 4: Ejecutar la prueba y verificar que pasa**

Run: `pytest tests/test_repositorios.py -v -m integracion`
Expected: 1 passed

- [ ] **Step 5: Comitear**

```bash
git add app/persistencia migrations alembic.ini tests/test_repositorios.py tests/conftest.py
git commit -m "feat: repositorios async de Postgres y migración inicial"
```

---

### Task 6: RAG híbrido sobre Qdrant

**Files:**
- Create: `app/rag/__init__.py`
- Create: `app/rag/ingesta.py`
- Create: `app/rag/recuperador.py`
- Create: `data/guias/*.md` (guías propias, al menos tres: técnica, progresión, consideraciones por zona)
- Test: `tests/test_rag.py` (requiere el servicio `qdrant`)

**Interfaces:**
- Consumes: `Ejercicio` de Task 2 y `cargar_catalogo` de Task 3; `Settings.qdrant_url`, `qdrant_collection`, `embedding_model` de Task 1.
- Produces: `async def ingerir(documentos: list[Documento], settings: Settings) -> None` y `async def buscar(consulta: str, filtros: FiltrosBusqueda, k: int, settings: Settings) -> list[Documento]`, con `Documento(id: str, texto: str, fuente: str, metadatos: dict[str, str])` y `FiltrosBusqueda(equipo: str | None, nivel: Nivel | None, musculo: str | None)`. Los embeddings se calculan con `asyncio.to_thread`.

- [ ] **Step 1: Escribir la prueba que falla**

```python
# tests/test_rag.py
import pytest
from app.rag.recuperador import buscar, FiltrosBusqueda
from app.settings import get_settings

pytestmark = pytest.mark.integracion

@pytest.mark.asyncio
async def test_filtro_por_equipo_excluye_otros_equipos(coleccion_prueba):
    res = await buscar("empuje de pecho", FiltrosBusqueda(equipo="mancuernas", nivel=None, musculo=None),
                       k=5, settings=get_settings())
    assert res and all(d.metadatos["equipo"] == "mancuernas" for d in res)
```

`coleccion_prueba` es un fixture en `tests/conftest.py` que ingiere `tests/fixtures/catalogo_muestra.json` en una colección temporal y la borra al final.

- [ ] **Step 2: Ejecutar la prueba y verificar que falla**

Run: `docker compose up -d qdrant && pytest tests/test_rag.py -v -m integracion`
Expected: FAIL con `ModuleNotFoundError`

- [ ] **Step 3: Implementar ingesta y recuperación**

`ingesta.py`: crea la colección si no existe, calcula embeddings densos y dispersos (BM25 o sparse vectors) y sube los puntos con el texto y los metadatos como payload. `recuperador.py`: busca con fusión de ambos rankings en el servidor y aplica `FiltrosBusqueda` como condiciones de payload. `AsyncQdrantClient` para todo el I/O.

Escribir las guías de `data/guias/` a partir de fuentes abiertas, resumidas con sus citas. No copiar texto literal.

- [ ] **Step 4: Ejecutar la prueba y verificar que pasa**

Run: `pytest tests/test_rag.py -v -m integracion`
Expected: 1 passed

- [ ] **Step 5: Comitear**

```bash
git add app/rag data/guias tests/test_rag.py tests/conftest.py
git commit -m "feat: RAG híbrido sobre Qdrant y guías propias"
```

---

### Task 7: Herramientas de los agentes con esquemas Pydantic

**Files:**
- Create: `app/herramientas/__init__.py`
- Create: `app/herramientas/esquemas.py`
- Create: `app/herramientas/funciones.py`
- Test: `tests/test_herramientas.py`

**Interfaces:**
- Consumes: `RepositorioDominio` de Task 5; `buscar` y `FiltrosBusqueda` de Task 6; `filtrar_por_lesiones` de Task 4; `Rutina` de Task 2.
- Produces: `EntradaVolumen(rutina: Rutina, catalogo: dict[str, Ejercicio])` y `SalidaVolumen(series_por_musculo: dict[str, int])`; `volumen_semanal(entrada: EntradaVolumen) -> SalidaVolumen`; `async def consultar_historial(repo, usuario_id: UUID, limite: int) -> list[EntrenoRegistro]`; `async def validar_plan(rutina: Rutina, lesiones: list[Lesion], catalogo: dict[str, Ejercicio]) -> list[str]` (devuelve los `ejercicio_id` bloqueados, vacío si el plan es seguro); `async def buscar_conocimiento(consulta: str, filtros: FiltrosBusqueda) -> list[Documento]`.

- [ ] **Step 1: Escribir las pruebas que fallan**

```python
# tests/test_herramientas.py
from uuid import uuid4
from app.herramientas.funciones import volumen_semanal, validar_plan
from app.herramientas.esquemas import EntradaVolumen
from app.domain.modelos import Rutina, DiaRutina, EjercicioPlanificado, Lesion

def test_volumen_suma_series_por_musculo():
    # Dos ejercicios de pecho de 3 series cada uno suman 6 series para "pecho"
    rutina = Rutina(usuario_id=uuid4(), version=1, dias=[
        DiaRutina(nombre="A", ejercicios=[
            EjercicioPlanificado(ejercicio_id="press_banca", series=3, repeticiones="8-10",
                                 descanso_seg=90, fuentes=["guia_tecnica"]),
            EjercicioPlanificado(ejercicio_id="aperturas", series=3, repeticiones="10-12",
                                 descanso_seg=60, fuentes=["guia_tecnica"]),
        ])])
    catalogo = {"press_banca": Ejercicio(id="press_banca", nombre="Press banca", musculo_primario="pecho",
                                         musculos_secundarios=[], equipo="mancuernas",
                                         nivel=Nivel.principiante, instrucciones=[]),
                "aperturas": Ejercicio(id="aperturas", nombre="Aperturas", musculo_primario="pecho",
                                       musculos_secundarios=[], equipo="mancuernas",
                                       nivel=Nivel.principiante, instrucciones=[])}
    assert volumen_semanal(EntradaVolumen(rutina=rutina, catalogo=catalogo)).series_por_musculo == {"pecho": 6}

async def test_validar_plan_detecta_ejercicio_bloqueado():
    rutina = Rutina(usuario_id=uuid4(), version=1, dias=[
        DiaRutina(nombre="A", ejercicios=[EjercicioPlanificado(
            ejercicio_id="press_militar", series=3, repeticiones="8-10",
            descanso_seg=90, fuentes=["guia_tecnica"])])])
    catalogo = {"press_militar": Ejercicio(id="press_militar", nombre="Press militar",
                                           musculo_primario="hombro", musculos_secundarios=[],
                                           equipo="mancuernas", nivel=Nivel.intermedio, instrucciones=[])}
    bloqueados = await validar_plan(rutina,
                                    [Lesion(zona="hombro_derecho", severidad="moderada", activa=True)],
                                    catalogo=catalogo)
    assert bloqueados == ["press_militar"]
```

Completar en la implementación los `...` con un `Ejercicio` real del fixture de Task 3 y la prueba de volumen con la rutina exacta.

- [ ] **Step 2: Ejecutar las pruebas y verificar que fallan**

Run: `pytest tests/test_herramientas.py -v`
Expected: FAIL con `ModuleNotFoundError`

- [ ] **Step 3: Implementar herramientas y esquemas**

Cada herramienta recibe y devuelve modelos Pydantic, nunca diccionarios sueltos. `validar_plan` reutiliza `filtrar_por_lesiones` de Task 4 para no duplicar reglas.

- [ ] **Step 4: Ejecutar las pruebas y verificar que pasan**

Run: `pytest tests/test_herramientas.py -v`
Expected: 2 passed

- [ ] **Step 5: Comitear**

```bash
git add app/herramientas tests/test_herramientas.py
git commit -m "feat: herramientas de agentes con esquemas Pydantic"
```

---

### Task 8: Agentes y grafo LangGraph con checkpointer

**Files:**
- Create: `app/agentes/__init__.py`
- Create: `app/agentes/estado.py`
- Create: `app/agentes/nodos.py`
- Create: `app/agentes/grafo.py`
- Create: `app/llm.py`
- Test: `tests/test_grafo.py`

**Interfaces:**
- Consumes: herramientas de Task 7; `RepositorioDominio` de Task 5; `Settings` de Task 1; `filtrar_por_lesiones` de Task 4.
- Produces: `EstadoCoach(TypedDict)` con `usuario_id: UUID`, `mensaje: str`, `perfil: Perfil | None`, `rutina: Rutina | None`, `bloqueados: list[str]`, `intentos_seguridad: int`, `respuesta: str | None`, `requiere_humano: bool`. `async def construir_grafo(settings: Settings, repo: RepositorioDominio, checkpointer: BaseCheckpointSaver) -> CompiledStateGraph`. Nodos: `evaluador`, `programador`, `progreso`, `seguridad`, `hitl`, `sintesis`, con una función `supervisor` que decide la ruta. `app/llm.py` expone `crear_llm(settings) -> BaseChatModel` (Gemini) con limitador de tasa y reintentos por HTTP 429.

- [ ] **Step 1: Escribir las pruebas que fallan**

```python
# tests/test_grafo.py
import pytest
from app.agentes.grafo import ruta_seguridad

def test_plan_con_bloqueados_vuelve_al_programador_hasta_el_limite():
    estado = {"bloqueados": ["press_militar"], "intentos_seguridad": 0}
    assert ruta_seguridad(estado, max_intentos=2) == "programador"

def test_agota_reintentos_y_responde_sin_plan_seguro():
    estado = {"bloqueados": ["press_militar"], "intentos_seguridad": 2}
    assert ruta_seguridad(estado, max_intentos=2) == "sintesis"

def test_dolor_agudo_pasa_a_humano():
    estado = {"bloqueados": [], "intentos_seguridad": 0, "requiere_humano": True}
    assert ruta_seguridad(estado, max_intentos=2) == "hitl"
```

- [ ] **Step 2: Ejecutar las pruebas y verificar que fallan**

Run: `pytest tests/test_grafo.py -v`
Expected: FAIL con `ModuleNotFoundError`

- [ ] **Step 3: Implementar el grafo**

`ruta_seguridad` es una función pura y se prueba sin LLM. El grafo usa `StateGraph(EstadoCoach)`, compila con `checkpointer=AsyncRedisSaver` y el `thread_id` = `str(usuario_id)`. El nodo `hitl` usa `interrupt()`. `crear_llm` aplica reintentos con espera exponencial ante HTTP 429 y el límite `gemini_rpm`.

Antes de comitear, agregar una prueba de integración que construya el grafo con un LLM falso (stub que devuelve un plan fijo) y confirme que el `thread_id` persiste el estado al reiniciar el checkpointer.

- [ ] **Step 4: Ejecutar las pruebas y verificar que pasan**

Run: `pytest tests/test_grafo.py -v`
Expected: 3 passed

- [ ] **Step 5: Comitear**

```bash
git add app/agentes app/llm.py tests/test_grafo.py
git commit -m "feat: supervisor LangGraph con checkpointer Redis y HITL"
```

---

### Task 9: API FastAPI con contratos Pydantic

**Files:**
- Create: `app/api/__init__.py`
- Create: `app/api/esquemas.py`
- Create: `app/api/rutas.py`
- Create: `app/main.py`
- Test: `tests/test_api.py`

**Interfaces:**
- Consumes: `construir_grafo` de Task 8; `RepositorioDominio` de Task 5; modelos de Task 2; `Settings` de Task 1.
- Produces: modelos de entrada y salida (`CrearUsuarioEntrada`, `MensajeEntrada`, `MensajeSalida`, `RegistroEntrenoEntrada`, `RutinaSalida`, `ReanudarEntrada`, `EstadoSalud`); `app: FastAPI` con las rutas de la especificación (sección 8). `GET /health` consulta Postgres, Redis y Qdrant.

- [ ] **Step 1: Escribir las pruebas que fallan**

```python
# tests/test_api.py
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app

@pytest.mark.asyncio
async def test_registro_entreno_con_ejercicio_inexistente_devuelve_422():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as c:
        r = await c.post("/usuarios/00000000-0000-0000-0000-000000000001/entrenos",
                         json={"fecha": "2026-10-01", "ejercicio_id": "no_existe", "series": 3,
                               "repeticiones": 8, "peso_kg": 20, "rpe": 7, "notas": None})
    assert r.status_code == 422
```

- [ ] **Step 2: Ejecutar la prueba y verificar que falla**

Run: `pytest tests/test_api.py -v`
Expected: FAIL con `ModuleNotFoundError: No module named 'app.main'`

- [ ] **Step 3: Implementar la API**

Cada ruta recibe y devuelve modelos de `app/api/esquemas.py`. Un manejador de excepciones convierte `CatalogoInvalido`, ejercicio desconocido y errores de tasa de Gemini en las respuestas de Review Focus (422, 503). `/chat` invoca el grafo con `thread_id = str(usuario_id)`. Para las rutas de consulta usar `RepositorioDominio`.

- [ ] **Step 4: Ejecutar la prueba y verificar que pasa**

Run: `pytest tests/test_api.py -v`
Expected: 1 passed

- [ ] **Step 5: Comitear**

```bash
git add app/api app/main.py tests/test_api.py
git commit -m "feat: API FastAPI con contratos Pydantic"
```

---

### Task 10: Observabilidad con Phoenix

**Files:**
- Create: `app/observabilidad.py`
- Modify: `app/main.py` (llamar a la configuración en el arranque)
- Test: `tests/test_observabilidad.py`

**Interfaces:**
- Consumes: `Settings.phoenix_collector_endpoint` de Task 1.
- Produces: `configurar_trazas(settings: Settings) -> None`. Registra el `TracerProvider` de OpenTelemetry y `LangChainInstrumentor` de OpenInference. Es idempotente.

- [ ] **Step 1: Escribir la prueba que falla**

```python
# tests/test_observabilidad.py
from app.observabilidad import configurar_trazas
from app.settings import get_settings

def test_configurar_trazas_es_idempotente():
    s = get_settings()
    configurar_trazas(s)
    configurar_trazas(s)  # no debe lanzar ni duplicar instrumentación
```

- [ ] **Step 2: Ejecutar la prueba y verificar que falla**

Run: `pytest tests/test_observabilidad.py -v`
Expected: FAIL con `ModuleNotFoundError`

- [ ] **Step 3: Implementar y conectar al arranque**

Instalar `arize-phoenix-otel` y `openinference-instrumentation-langchain`. En `app/main.py`, llamar `configurar_trazas(get_settings())` dentro del `lifespan` de FastAPI.

- [ ] **Step 4: Ejecutar la prueba y verificar que pasa**

Run: `pytest tests/test_observabilidad.py -v`
Expected: 1 passed

- [ ] **Step 5: Comitear**

```bash
git add app/observabilidad.py app/main.py tests/test_observabilidad.py
git commit -m "feat: trazas con Phoenix y OpenInference"
```

---

### Task 11: Pruebas de sistema, golden set y evaluación

**Files:**
- Create: `tests/sistema/test_escenarios.py`
- Create: `evaluacion/golden_set.json`
- Create: `evaluacion/evaluar.py`

**Interfaces:**
- Consumes: API de Task 9 y grafo de Task 8.
- Produces: cinco pruebas de sistema marcadas `sistema`, cada una con su traza en Phoenix. `evaluar.py` mide recuperación (documentos esperados en el top-k) y el filtro de seguridad (ningún ejercicio prohibido en la rutina final) y escribe un resumen en `evaluacion/resultados.json`.

- [ ] **Step 1: Escribir las cinco pruebas que fallan**

Cada prueba corresponde a un escenario de la especificación (sección 10): onboarding completo, ajuste semanal, lesión activa, dolor agudo y pregunta fuera de alcance. Ejemplo para la lesión activa:

```python
# tests/sistema/test_escenarios.py
import pytest
pytestmark = pytest.mark.sistema

@pytest.mark.asyncio
async def test_lesion_activa_no_muestra_press_militar(cliente, usuario_con_hombro_lesionado):
    r = await cliente.post("/chat", json={"usuario_id": usuario_con_hombro_lesionado,
                                          "mensaje": "Dame una rutina de hombro para 3 días"})
    assert r.status_code == 200
    assert "press_militar" not in r.json()["respuesta"]
```

Escribir las otras cuatro con la misma estructura, cada una con su aserción sobre la respuesta o el estado del grafo.

- [ ] **Step 2: Ejecutar las pruebas y verificar que fallan**

Run: `docker compose up -d && pytest tests/sistema -v -m sistema`
Expected: FAIL (el sistema todavía no está ensamblado de punta a punta)

- [ ] **Step 3: Implementar el golden set y el script de evaluación**

`golden_set.json` con al menos 10 casos: consulta, documentos esperados y ejercicios prohibidos. `evaluar.py` es un script async que recorre el golden set, llama a `buscar` y al grafo, y escribe el resumen.

- [ ] **Step 4: Ejecutar las pruebas y verificar que pasan**

Run: `pytest tests/sistema -v -m sistema && python evaluacion/evaluar.py`
Expected: 5 passed y `resultados.json` generado. Confirmar en Phoenix que cada prueba tiene su traza.

- [ ] **Step 5: Comitear**

```bash
git add tests/sistema evaluacion
git commit -m "test: escenarios de sistema, golden set y evaluación"
```

---

### Task 12: Documentación y arranque con un comando

**Files:**
- Create: `README.md`
- Create: `run.sh`
- Create: `run.ps1`

**Interfaces:**
- Consumes: todo lo anterior.
- Produces: README con diagrama Mermaid del grafo, instrucciones de arranque y descripción de las guías. `run.sh` y `run.ps1` ejecutan `docker compose up -d`, las migraciones de Alembic, la ingesta del catálogo y las guías, y luego arrancan la API.

- [ ] **Step 1: Verificar el arranque con la documentación vacía**

Run: `docker compose down -v && bash run.sh` (o `./run.ps1` en Windows)
Expected: el compose levanta, las migraciones corren y `GET /health` responde 200.

- [ ] **Step 2: Escribir el README**

Secciones: qué hace el coach, arquitectura, diagrama Mermaid del grafo (Supervisor, Evaluador, Programador, Progreso, Seguridad, HITL, Síntesis), requisitos de la rúbrica con enlace a cada parte, arranque en un comando, cómo ver las trazas en Phoenix, aviso de no diagnóstico médico y licencias de las fuentes.

- [ ] **Step 3: Verificar el README**

Run: `curl -s http://localhost:8000/health`
Expected: `{"status":"ok", ...}` y el diagrama renderiza en el visor de Markdown.

- [ ] **Step 4: Comitear**

```bash
git add README.md run.sh run.ps1
git commit -m "docs: README con diagrama del grafo y arranque en un comando"
```

---

## Self-Review

**1. Cobertura de la especificación**
- Sección 3 (arquitectura) → Tasks 8, 9, 10.
- Sección 4 (componentes) → Tasks 1 a 10 mapean una unidad cada una.
- Sección 5 (modelo de datos) → Task 5.
- Sección 6 (datos y RAG) → Tasks 3 y 6.
- Sección 7 (seguridad) → Tasks 4, 7 y 8.
- Sección 8 (API) → Task 9.
- Sección 9 (observabilidad) → Task 10.
- Sección 10 (evaluación) → Task 11.
- Sección 11 (despliegue) → Tasks 1 y 12.
- Sección 14 (pendientes) → Tasks 3 y 4 (licencia y reglas), Task 6 (guías).

**2. Consistencia de tipos**
- `Ejercicio`, `Lesion`, `Rutina` y `FiltrosBusqueda` se definen una vez y se usan con los mismos nombres en las tareas siguientes.
- `filtrar_por_lesiones` (Task 4) es la única implementación de reglas; `validar_plan` (Task 7) la reutiliza.

**3. Review Focus**
Los cinco casos tienen prueba asignada: Task 8 (dos casos), Task 4, Task 9 y Task 8 (límite de tasa y reinicio de Redis, con la prueba de persistencia).

**4. Proporción**
Las tareas dan firmas, pruebas y comandos, no el cuerpo de las funciones. Las pruebas de Task 7 tienen `...` en los puntos donde el implementador completa con datos del fixture, y eso está indicado en el texto.

**Nota:** Task 1 incluye `git init`, porque la carpeta del proyecto todavía no es un repositorio. Eso se hace con tu aprobación al ejecutar el plan.

---

Plan completo guardado en [docs/superpowers/plans/2026-10-22-coach-gimnasio.md](coach-gimnasio/docs/superpowers/plans/2026-10-22-coach-gimnasio.md).

Son 12 tareas con dependencias entre sí, y un error en el filtro de seguridad tendría costo alto. Por eso recomiendo **subagent-driven**: un agente implementa cada tarea y otro la revisa antes de avanzar. Eso da una revisión independiente del filtro de seguridad y de los contratos entre tareas.

La alternativa es **native**: yo implemento todo en esta sesión y al final se revisa el conjunto completo. Es más barato y rápido, pero la revisión llega solo al final.

¿Revisas el plan y eliges el método de ejecución?

