"""Infraestructura de las pruebas de sistema: stack real (docker compose) + Gemini real.

Se omiten (skip) con un motivo claro, y sin mostrar secretos, si falta GOOGLE_API_KEY, si
TEST_DATABASE_URL no es segura o si algun servicio (Postgres, Redis, Qdrant, Phoenix) no
responde. Usan la base de pruebas (`*_test`) y una coleccion de Qdrant propia
(`<QDRANT_COLLECTION>_test`), nunca las de la aplicacion. Las trazas son reales: cada
escenario abre un span raiz `sistema.<escenario>` y comprueba que llega a Phoenix.
"""

import asyncio
import json
import os
import subprocess
import sys
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from urllib.parse import urlparse
from uuid import UUID, uuid4

import httpx
import pytest
import pytest_asyncio
from httpx import ASGITransport
from sqlalchemy import text

from app.domain.modelos import Lesion, Nivel, Perfil
from app.settings import Settings
from tests.conftest import RAIZ
from tests.guarda_bd import resolver_url_pruebas, url_sin_credenciales

SUFIJO_COLECCION_PRUEBAS = "_test"
TIMEOUT_SERVICIO_SEG = 3.0
NOMBRE_TRACER = "coach-gimnasio.sistema"
EQUIPO_GIMNASIO = ["barbell", "dumbbell", "cable", "machine", "cuerpo"]


# --- Precondiciones -------------------------------------------------------------------

MSG_SIN_CLAVE = (
    "GOOGLE_API_KEY no configurada: las pruebas de sistema usan Gemini real. Define la "
    "variable (o anadela a .env) y ejecuta `pytest tests/sistema -m sistema`."
)


def _settings_o_motivo() -> tuple[Settings | None, str | None]:
    """Settings completas (entorno o .env) o el motivo del skip; nunca incluye valores."""
    from pydantic import ValidationError

    try:
        settings = Settings()
    except ValidationError as exc:
        faltan = sorted({str(e["loc"][0]).upper() for e in exc.errors()})
        if "GOOGLE_API_KEY" in faltan:
            return None, MSG_SIN_CLAVE
        return None, f"Configuracion incompleta para las pruebas de sistema (faltan: {', '.join(faltan)})"
    if not settings.google_api_key.get_secret_value().strip():
        return None, MSG_SIN_CLAVE
    return settings, None


async def _servicios_caidos(settings: Settings, url_bd: str) -> list[str]:
    from redis.asyncio import from_url

    from app.persistencia.repositorios import crear_motor

    async def postgres() -> None:
        motor = crear_motor(url_bd)
        try:
            async with motor.connect() as conn:
                await conn.execute(text("SELECT 1"))
        finally:
            await motor.dispose()

    async def redis() -> None:
        cliente = from_url(settings.redis_url)
        try:
            await cliente.ping()
        finally:
            await cliente.aclose()

    async def http_ok(url: str) -> None:
        async with httpx.AsyncClient(timeout=TIMEOUT_SERVICIO_SEG) as http:
            r = await http.get(url)
            if r.status_code >= 500:
                raise RuntimeError(r.status_code)

    comprobaciones = {
        f"postgres ({url_sin_credenciales(url_bd)})": postgres(),
        "redis": redis(),
        "qdrant": http_ok(f"{settings.qdrant_url.rstrip('/')}/healthz"),
        "phoenix": http_ok(_base_phoenix(settings)),
    }
    caidos = []
    resultados = await asyncio.gather(
        *(asyncio.wait_for(c, TIMEOUT_SERVICIO_SEG) for c in comprobaciones.values()),
        return_exceptions=True,
    )
    for nombre, res in zip(comprobaciones, resultados):
        if isinstance(res, BaseException):
            caidos.append(nombre)
    return caidos


def _base_phoenix(settings: Settings) -> str:
    u = urlparse(settings.phoenix_collector_endpoint)
    return f"{u.scheme}://{u.netloc}"


async def _vaciar_bd(url_bd: str) -> None:
    from app.persistencia.repositorios import crear_motor
    from app.persistencia.tablas import Base

    motor = crear_motor(url_bd)
    try:
        async with motor.begin() as conn:
            tablas = ", ".join(t.name for t in Base.metadata.sorted_tables)
            await conn.execute(text(f"TRUNCATE {tablas} RESTART IDENTITY CASCADE"))
    finally:
        await motor.dispose()


@pytest.fixture(scope="session")
def entorno_sistema():
    """Settings para el stack de pruebas: BD `*_test` y coleccion `<coleccion>_test` ingerida."""
    settings, motivo = _settings_o_motivo()
    if motivo:
        pytest.skip(motivo)
    url_bd, motivo = resolver_url_pruebas(os.environ)
    if url_bd is None:
        pytest.skip(motivo)
    caidos = asyncio.run(_servicios_caidos(settings, url_bd))
    if caidos:
        pytest.skip(
            f"Servicios no disponibles para las pruebas de sistema: {', '.join(caidos)}. "
            "Levantalos con `docker compose up -d`."
        )

    migracion = subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        cwd=RAIZ, capture_output=True, text=True, env={**os.environ, "DATABASE_URL": url_bd},
    )
    if migracion.returncode != 0:
        pytest.fail(f"alembic upgrade head fallo en la base de pruebas:\n{migracion.stderr[-2000:]}")

    cfg = settings.model_copy(update={
        "database_url": url_bd,
        "qdrant_collection": settings.qdrant_collection + SUFIJO_COLECCION_PRUEBAS,
    })
    from scripts.ingerir import ingerir_corpus

    asyncio.run(ingerir_corpus(cfg))  # idempotente: solo recodifica si el corpus cambio
    yield cfg
    asyncio.run(_vaciar_bd(url_bd))


# --- Trazas reales ----------------------------------------------------------------------

@pytest.fixture(autouse=True)
def _sin_exportar_trazas():
    """Anula el fixture autouse del conftest raiz: aqui las trazas van al Phoenix real."""
    yield


@asynccontextmanager
async def traza_escenario(nombre: str) -> AsyncIterator[str]:
    """Span raiz `sistema.<nombre>`; los spans de la API y del grafo cuelgan de el.

    Devuelve el trace_id (hex) para buscarlo en Phoenix. En Phoenix: proyecto
    `coach-gimnasio`, filtro `name == 'sistema.<nombre>'` o etiqueta `escenario`.
    """
    from openinference.instrumentation import using_attributes
    from opentelemetry import trace

    sesion = f"sistema-{nombre}-{uuid4().hex[:8]}"
    atributos = {"escenario": nombre, "session.id": sesion, "tipo_prueba": "sistema"}
    try:
        with (
            trace.get_tracer(NOMBRE_TRACER).start_as_current_span(
                f"sistema.{nombre}", attributes=atributos
            ) as span,
            using_attributes(session_id=sesion, tags=["sistema", nombre],
                             metadata={"escenario": nombre}),
        ):
            yield format(span.get_span_context().trace_id, "032x")
    finally:
        # fuera del `with`: el span raiz ya termino y se exporta con el flush
        proveedor = trace.get_tracer_provider()
        if hasattr(proveedor, "force_flush"):
            proveedor.force_flush()


async def comprobar_traza_en_phoenix(settings: Settings, nombre: str, trace_id: str) -> None:
    """Falla si el span raiz del escenario no aparece en Phoenix (API GraphQL) en ~15 s."""
    condicion = f"name == 'sistema.{nombre}' and trace_id == '{trace_id}'"
    consulta = (
        "{ projects { edges { node { name spans(first: 1, filterCondition: "
        + json.dumps(condicion)
        + ") { edges { node { context { traceId } } } } } } } }"
    )
    url = f"{_base_phoenix(settings)}/graphql"
    vistos: set[str] = set()
    async with httpx.AsyncClient(timeout=5) as http:
        for _ in range(15):
            r = await http.post(url, json={"query": consulta})
            if r.status_code == 200 and "errors" not in r.json():
                for p in r.json()["data"]["projects"]["edges"]:
                    vistos |= {e["node"]["context"]["traceId"] for e in p["node"]["spans"]["edges"]}
                if trace_id in vistos:
                    return
            await asyncio.sleep(1)
    pytest.fail(f"La traza del escenario '{nombre}' ({trace_id}) no llego a Phoenix")


# --- Aplicacion y cliente ---------------------------------------------------------------

@pytest_asyncio.fixture
async def app_sistema(entorno_sistema):
    from app.main import crear_app

    app = crear_app(entorno_sistema)
    async with app.router.lifespan_context(app):
        if app.state.grafo is None or app.state.repo is None:
            pytest.fail("La app arranco degradada (sin grafo o sin repositorio): revisa los logs")
        yield app


@pytest_asyncio.fixture
async def cliente(app_sistema):
    from opentelemetry.propagate import inject

    async def _propagar_contexto(request: httpx.Request) -> None:
        # El span HTTP del servidor toma el padre de la cabecera `traceparent`; sin ella cada
        # peticion abriria una traza nueva en vez de colgar del span del escenario.
        inject(request.headers)

    async with httpx.AsyncClient(
        transport=ASGITransport(app=app_sistema), base_url="http://sistema",
        event_hooks={"request": [_propagar_contexto]},
    ) as c:
        yield c


@pytest.fixture
def repo(app_sistema):
    return app_sistema.state.repo


@pytest.fixture
def catalogo(app_sistema):
    return app_sistema.state.catalogo


async def crear_usuario(cliente: httpx.AsyncClient) -> str:
    r = await cliente.post("/usuarios")
    assert r.status_code == 201, r.text
    return r.json()["id"]


async def registrar_perfil(repo, usuario_id: str, *, dias: int = 3, nivel: Nivel = Nivel.intermedio) -> None:
    await repo.guardar_perfil(Perfil(
        usuario_id=UUID(usuario_id), objetivo="fuerza e hipertrofia", dias_disponibles=dias,
        equipo=EQUIPO_GIMNASIO, nivel=nivel,
    ))


@pytest_asyncio.fixture
async def usuario_con_hombro_lesionado(cliente, repo) -> str:
    """Usuario creado por la API, con perfil completo y lesion activa de hombro derecho."""
    usuario_id = await crear_usuario(cliente)
    await registrar_perfil(repo, usuario_id)
    await repo.agregar_lesion(
        UUID(usuario_id), Lesion(zona="hombro_derecho", severidad="moderada", activa=True)
    )
    return usuario_id
