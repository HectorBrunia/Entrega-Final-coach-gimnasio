from datetime import date
from types import SimpleNamespace
from uuid import UUID, uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from langgraph.types import Command, Interrupt

from app.domain.modelos import (
    DiaRutina, Ejercicio, EjercicioPlanificado, EntrenoRegistro, Lesion, Nivel, Perfil, Rutina,
)
from app.llm import MSG_CONFIGURACION, MSG_TRANSITORIO, LLMNoDisponible
from app.main import crear_app

UID = "00000000-0000-0000-0000-000000000001"


_CATALOGO = {
    "sentadilla": Ejercicio(
        id="sentadilla", nombre="Sentadilla", musculo_primario="cuadriceps",
        musculos_secundarios=[], equipo="barbell", nivel=Nivel.principiante, instrucciones=["x"]),
    "press_militar": Ejercicio(
        id="press_militar", nombre="Press militar", musculo_primario="shoulders",
        musculos_secundarios=[], equipo="barbell", nivel=Nivel.principiante, instrucciones=["x"]),
}


def _catalogo() -> dict[str, Ejercicio]:
    return _CATALOGO  # mismo objeto: el indice de bloqueos se cachea por catalogo


class RepoFalso:
    def __init__(self):
        self.entrenos: list[EntrenoRegistro] = []
        self.perfiles: dict[UUID, Perfil] = {}
        self.rutinas: dict[UUID, Rutina] = {}
        self.lesiones: dict[UUID, list[Lesion]] = {}
        self.exclusiones: dict[UUID, list[str]] = {}
        self.llamadas = 0

    async def crear_usuario(self) -> UUID:
        self.llamadas += 1
        return UUID(UID)

    async def obtener_perfil(self, usuario_id):
        self.llamadas += 1
        return self.perfiles.get(usuario_id)

    async def rutina_actual(self, usuario_id):
        self.llamadas += 1
        return self.rutinas.get(usuario_id)

    async def lesiones_activas(self, usuario_id):
        self.llamadas += 1
        return [l for l in self.lesiones.get(usuario_id, []) if l.activa]

    async def exclusiones_activas(self, usuario_id):
        self.llamadas += 1
        return list(self.exclusiones.get(usuario_id, []))

    async def registrar_entreno(self, entreno):
        self.llamadas += 1
        self.entrenos.append(entreno)


class GrafoFalso:
    def __init__(self, salida=None, error=None, pausado=False, valores=None):
        self.salida = salida if salida is not None else {"respuesta": "Hola"}
        self.error = error
        self.pausado = pausado
        self.valores = valores or {}
        self.invocaciones: list[tuple] = []

    async def ainvoke(self, entrada, config):
        self.invocaciones.append((entrada, config))
        if self.error:
            raise self.error
        return self.salida

    async def aget_state(self, config):
        # forma de StateSnapshot: una pausa HITL tiene interrupciones pendientes
        return SimpleNamespace(
            next=("hitl",) if self.pausado else (),
            interrupts=(Interrupt(value={"motivo": "dolor_agudo"}),) if self.pausado else (),
            values=self.valores,
        )


def _cliente(app):
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://t")


def _entreno(ejercicio_id="sentadilla"):
    return {"fecha": "2026-10-01", "ejercicio_id": ejercicio_id, "series": 3,
            "repeticiones": 8, "peso_kg": 20, "rpe": 7, "notas": None}


@pytest.mark.asyncio
async def test_registro_entreno_con_ejercicio_inexistente_devuelve_422():
    repo = RepoFalso()
    app = crear_app(grafo=GrafoFalso(), repo=repo, catalogo=_catalogo())
    async with _cliente(app) as c:
        r = await c.post("/usuarios/00000000-0000-0000-0000-000000000001/entrenos",
                         json={"fecha": "2026-10-01", "ejercicio_id": "no_existe", "series": 3,
                               "repeticiones": 8, "peso_kg": 20, "rpe": 7, "notas": None})
    assert r.status_code == 422
    assert "no_existe" in r.text
    assert repo.llamadas == 0  # se valida contra el catalogo antes de tocar la BD


@pytest.mark.asyncio
async def test_registro_entreno_valido_201():
    repo = RepoFalso()
    app = crear_app(grafo=GrafoFalso(), repo=repo, catalogo=_catalogo())
    async with _cliente(app) as c:
        r = await c.post(f"/usuarios/{UID}/entrenos", json=_entreno())
    assert r.status_code == 201
    assert repo.entrenos[0].usuario_id == UUID(UID)
    assert repo.entrenos[0].fecha == date(2026, 10, 1)


@pytest.mark.asyncio
async def test_entrenos_sin_catalogo_devuelve_503():
    repo = RepoFalso()
    app = crear_app(grafo=GrafoFalso(), repo=repo, catalogo=None)
    async with _cliente(app) as c:
        r = await c.post(f"/usuarios/{UID}/entrenos", json=_entreno())
    assert r.status_code == 503
    assert "atálogo" in r.json()["detail"]
    assert repo.llamadas == 0


@pytest.mark.asyncio
async def test_crear_usuario_devuelve_201_con_id():
    app = crear_app(grafo=GrafoFalso(), repo=RepoFalso(), catalogo=_catalogo())
    async with _cliente(app) as c:
        r = await c.post("/usuarios", json={})
    assert r.status_code == 201
    assert r.json() == {"id": UID}


@pytest.mark.asyncio
async def test_chat_camino_feliz():
    grafo = GrafoFalso({"respuesta": "Plan listo"})
    app = crear_app(grafo=grafo, repo=RepoFalso(), catalogo=_catalogo())
    async with _cliente(app) as c:
        r = await c.post("/chat", json={"usuario_id": UID, "mensaje": "Armame una rutina"})
    assert r.status_code == 200
    assert r.json() == {"respuesta": "Plan listo", "requiere_humano": False, "thread_id": UID}
    entrada, config = grafo.invocaciones[0]
    assert config["configurable"]["thread_id"] == UID
    assert entrada["mensaje"] == "Armame una rutina"


@pytest.mark.asyncio
async def test_chat_con_interrupcion_marca_requiere_humano():
    salida = {"__interrupt__": [Interrupt(value={"motivo": "dolor_agudo", "ejercicio": "press_banca",
                                                  "mensaje": "me duele"})]}
    app = crear_app(grafo=GrafoFalso(salida), repo=RepoFalso(), catalogo=_catalogo())
    async with _cliente(app) as c:
        r = await c.post("/chat", json={"usuario_id": UID, "mensaje": "me duele"})
    assert r.status_code == 200
    cuerpo = r.json()
    assert cuerpo["requiere_humano"] is True
    assert cuerpo["respuesta"]
    assert cuerpo["thread_id"] == UID


@pytest.mark.asyncio
async def test_chat_con_llm_no_disponible_devuelve_503():
    app = crear_app(grafo=GrafoFalso(error=LLMNoDisponible("429 secreto interno")),
                    repo=RepoFalso(), catalogo=_catalogo())
    async with _cliente(app) as c:
        r = await c.post("/chat", json={"usuario_id": UID, "mensaje": "hola"})
    assert r.status_code == 503
    assert "secreto" not in r.text
    assert "Traceback" not in r.text


def _grafo_con_llm_que_falla(monkeypatch, error):
    """Grafo LangGraph real cuyo nodo llama a Gemini (parcheado) con reintentos minimos."""
    from langchain_google_genai import ChatGoogleGenerativeAI
    from langgraph.checkpoint.memory import MemorySaver
    from langgraph.graph import END, START, StateGraph
    from typing_extensions import TypedDict

    from app.llm import crear_llm
    from app.settings import Settings

    async def _falso(self, messages, stop=None, run_manager=None, **kwargs):
        raise error

    monkeypatch.setattr(ChatGoogleGenerativeAI, "_agenerate", _falso)
    cfg = Settings(
        database_url="postgresql+asyncpg://x:x@localhost/x", redis_url="redis://x",
        qdrant_url="http://x", qdrant_collection="c", google_api_key="k", gemini_model="m",
        gemini_rpm=6000, phoenix_collector_endpoint="http://x", embedding_model="e")
    llm = crear_llm(cfg, reintentos=1, espera_base=0.0)

    class Estado(TypedDict, total=False):
        respuesta: str

    async def nodo(_estado):
        return {"respuesta": (await llm.ainvoke("hola")).content}

    g = StateGraph(Estado)
    g.add_node("evaluador", nodo)
    g.add_edge(START, "evaluador")
    g.add_edge("evaluador", END)
    return g.compile(checkpointer=MemorySaver())


def _error_503():
    from langchain_google_genai.chat_models import GoogleAPIError
    return GoogleAPIError(code=503, response_json={"error": {"status": "UNAVAILABLE",
                          "message": "high demand secreto"}}, response=None)


def _error_401():
    from langchain_google_genai.chat_models import GoogleAuthenticationError
    return GoogleAuthenticationError("401 UNAUTHENTICATED api key secreto")


@pytest.mark.asyncio
@pytest.mark.parametrize("fabrica,mensaje", [
    (_error_503, MSG_TRANSITORIO), (_error_401, MSG_CONFIGURACION),
    (lambda: __import__("httpx").ReadTimeout("secreto"), MSG_TRANSITORIO)])
async def test_chat_con_error_del_proveedor_en_nodo_devuelve_503_claro(
        monkeypatch, fabrica, mensaje):
    grafo = _grafo_con_llm_que_falla(monkeypatch, fabrica())
    app = crear_app(grafo=grafo, repo=RepoFalso(), catalogo=_catalogo())
    async with _cliente(app) as c:
        r = await c.post("/chat", json={"usuario_id": UID, "mensaje": "hola"})
    assert r.status_code == 503
    assert r.json() == {"detail": mensaje}
    assert "secreto" not in r.text


@pytest.mark.asyncio
@pytest.mark.parametrize("motivo,mensaje", [
    ("transitorio", MSG_TRANSITORIO), ("permanente", MSG_CONFIGURACION)])
async def test_reanudar_con_llm_no_disponible_devuelve_503_claro(motivo, mensaje):
    grafo = GrafoFalso(error=LLMNoDisponible("detalle secreto", motivo=motivo), pausado=True)
    app = crear_app(grafo=grafo, repo=RepoFalso(), catalogo=_catalogo())
    async with _cliente(app) as c:
        r = await c.post(f"/hitl/{UID}/reanudar", json={"revision": "aprobar"})
    assert r.status_code == 503
    assert r.json() == {"detail": mensaje}


@pytest.mark.asyncio
async def test_chat_sin_grafo_devuelve_503():
    app = crear_app(grafo=None, repo=RepoFalso(), catalogo=_catalogo())
    async with _cliente(app) as c:
        r = await c.post("/chat", json={"usuario_id": UID, "mensaje": "hola"})
    assert r.status_code == 503


@pytest.mark.asyncio
async def test_perfil_de_usuario_desconocido_devuelve_404():
    app = crear_app(grafo=GrafoFalso(), repo=RepoFalso(), catalogo=_catalogo())
    async with _cliente(app) as c:
        r = await c.get(f"/usuarios/{uuid4()}/perfil")
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_perfil_existente_y_rutina_actual():
    repo = RepoFalso()
    uid = UUID(UID)
    repo.perfiles[uid] = Perfil(usuario_id=uid, objetivo="masa", dias_disponibles=4,
                                equipo=["mancuernas"], nivel=Nivel.principiante)
    app = crear_app(grafo=GrafoFalso(), repo=repo, catalogo=_catalogo())
    async with _cliente(app) as c:
        p = await c.get(f"/usuarios/{UID}/perfil")
        rut = await c.get(f"/usuarios/{UID}/rutinas/actual")
    assert p.status_code == 200 and p.json()["dias_disponibles"] == 4
    assert rut.status_code == 404


@pytest.mark.asyncio
async def test_rutina_actual_existente():
    repo = RepoFalso()
    uid = UUID(UID)
    repo.rutinas[uid] = Rutina(usuario_id=uid, version=2, dias=[])
    app = crear_app(grafo=GrafoFalso(), repo=repo, catalogo=_catalogo())
    async with _cliente(app) as c:
        r = await c.get(f"/usuarios/{UID}/rutinas/actual")
    assert r.status_code == 200 and r.json()["version"] == 2


@pytest.mark.asyncio
async def test_rutina_actual_incluye_nombres_de_ejercicios():
    repo = RepoFalso()
    uid = UUID(UID)
    plan = EjercicioPlanificado(ejercicio_id="sentadilla", series=3, repeticiones="8-10",
                                descanso_seg=90, fuentes=["catalogo"])
    repo.rutinas[uid] = Rutina(usuario_id=uid, version=1,
                               dias=[DiaRutina(nombre="Día 1", ejercicios=[plan])])
    app = crear_app(grafo=GrafoFalso(), repo=repo, catalogo=_catalogo())
    async with _cliente(app) as c:
        r = await c.get(f"/usuarios/{UID}/rutinas/actual")
    assert r.status_code == 200 and r.json()["nombres"] == {"sentadilla": "Sentadilla"}


@pytest.mark.asyncio
async def test_raiz_sirve_el_chat_web_sin_tapar_la_api():
    app = crear_app(grafo=GrafoFalso(), repo=RepoFalso(), catalogo=_catalogo())
    async with _cliente(app) as c:
        raiz = await c.get("/")
        js = await c.get("/chat.js")
        docs = await c.get("/docs")
        usuario = await c.post("/usuarios", json={})
    assert raiz.status_code == 200 and "Coach de gimnasio" in raiz.text
    assert js.status_code == 200 and "/rutinas/actual" in js.text
    assert docs.status_code == 200 and "swagger" in docs.text.lower()
    assert usuario.status_code == 201


@pytest.mark.asyncio
async def test_reanudar_invoca_el_grafo_con_command_resume():
    grafo = GrafoFalso({"respuesta": "Consulta a un profesional"}, pausado=True)
    app = crear_app(grafo=grafo, repo=RepoFalso(), catalogo=_catalogo())
    async with _cliente(app) as c:
        r = await c.post(f"/hitl/{UID}/reanudar", json={"revision": "revisado"})
    assert r.status_code == 200
    assert r.json() == {"respuesta": "Consulta a un profesional", "requiere_humano": False,
                        "thread_id": UID}
    entrada, config = grafo.invocaciones[0]
    assert isinstance(entrada, Command) and entrada.resume == "revisado"
    assert config["configurable"]["thread_id"] == UID


@pytest.mark.asyncio
async def test_reanudar_sin_pausa_devuelve_409():
    grafo = GrafoFalso(pausado=False)
    app = crear_app(grafo=grafo, repo=RepoFalso(), catalogo=_catalogo())
    async with _cliente(app) as c:
        r = await c.post(f"/hitl/{UID}/reanudar", json={"revision": "ok"})
    assert r.status_code == 409
    assert grafo.invocaciones == []


async def _ok():
    return None


async def _falla():
    raise RuntimeError("password=hunter2 en postgres://interno")


@pytest.mark.asyncio
async def test_health_todo_ok():
    app = crear_app(grafo=GrafoFalso(), repo=RepoFalso(), catalogo=_catalogo(),
                    comprobaciones={"postgres": _ok, "redis": _ok, "qdrant": _ok})
    async with _cliente(app) as c:
        r = await c.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok",
                        "servicios": {"postgres": "ok", "redis": "ok", "qdrant": "ok"}}


@pytest.mark.asyncio
async def test_health_con_un_servicio_caido_devuelve_503_sin_detalles():
    app = crear_app(grafo=GrafoFalso(), repo=RepoFalso(), catalogo=_catalogo(),
                    comprobaciones={"postgres": _ok, "redis": _falla, "qdrant": _ok})
    async with _cliente(app) as c:
        r = await c.get("/health")
    assert r.status_code == 503
    cuerpo = r.json()
    assert cuerpo["status"] == "degradado"
    assert cuerpo["servicios"] == {"postgres": "ok", "redis": "error", "qdrant": "ok"}
    assert "hunter2" not in r.text


def test_importar_app_no_requiere_variables_de_entorno():
    import app.main as m
    assert m.app.title


# --- Lifespan (se ejecuta de verdad con lifespan_context) -----------------------------

from contextlib import asynccontextmanager  # noqa: E402

import app.main as main_mod  # noqa: E402
from app.main import Constructores  # noqa: E402
from tests.conftest import Settings  # noqa: E402


def _cfg() -> Settings:
    return Settings(
        database_url="postgresql+asyncpg://x:x@localhost/x", redis_url="redis://localhost:6379/0",
        qdrant_url="http://localhost:6333", qdrant_collection="c", google_api_key="x",
        gemini_model="x", gemini_rpm=1, phoenix_collector_endpoint="http://localhost:6006",
        embedding_model="m",
    )


class MotorFalso:
    def __init__(self):
        self.liberado = False

    async def dispose(self):
        self.liberado = True


def _ctor_que_falla_en_checkpointer(motor=None):
    @asynccontextmanager
    async def checkpointer(_url):
        raise ConnectionError("redis://usuario:secreto@host caido")
        yield  # pragma: no cover

    async def grafo(*a, **k):
        raise AssertionError("no debe construirse sin checkpointer")

    return Constructores(motor=lambda _u: motor or MotorFalso(), checkpointer=checkpointer,
                         grafo=grafo)


@pytest.mark.asyncio
async def test_lifespan_no_sobrescribe_dependencias_inyectadas():
    grafo, repo, catalogo = GrafoFalso(), RepoFalso(), _catalogo()

    def prohibido(*a, **k):
        raise AssertionError("no debe construirse nada")

    app = crear_app(_cfg(), grafo=grafo, repo=repo, catalogo=catalogo,
                    constructores=Constructores(motor=prohibido, checkpointer=prohibido,
                                                grafo=prohibido))
    async with app.router.lifespan_context(app):
        assert app.state.grafo is grafo
        assert app.state.repo is repo
        assert app.state.catalogo is catalogo


@pytest.mark.asyncio
async def test_lifespan_con_checkpointer_caido_arranca_degradado():
    async def redis_caido():
        raise ConnectionError("secreto")

    app = crear_app(_cfg(), repo=RepoFalso(), catalogo=_catalogo(),
                    comprobaciones={"postgres": _ok, "redis": redis_caido, "qdrant": _ok},
                    constructores=_ctor_que_falla_en_checkpointer())
    async with app.router.lifespan_context(app):
        assert app.state.grafo is None
        async with _cliente(app) as c:
            chat = await c.post("/chat", json={"usuario_id": UID, "mensaje": "hola"})
            reanudar = await c.post(f"/hitl/{UID}/reanudar", json={"revision": "ok"})
            salud = await c.get("/health")
    assert chat.status_code == 503 and reanudar.status_code == 503
    assert "secreto" not in chat.text
    assert salud.status_code == 503
    assert salud.json()["servicios"] == {"postgres": "ok", "redis": "error", "qdrant": "ok"}


@pytest.mark.asyncio
async def test_lifespan_construye_grafo_y_libera_el_motor_al_cerrar():
    motor = MotorFalso()
    cerrado = []

    @asynccontextmanager
    async def checkpointer(_url):
        yield "saver"
        cerrado.append(True)

    async def grafo(cfg, repo, saver, *, catalogo):
        assert saver == "saver"
        return GrafoFalso()

    app = crear_app(_cfg(), catalogo=_catalogo(),
                    constructores=Constructores(motor=lambda _u: motor, checkpointer=checkpointer,
                                                grafo=grafo))
    async with app.router.lifespan_context(app):
        assert isinstance(app.state.grafo, GrafoFalso)
        assert app.state.repo is not None
        assert not motor.liberado
    assert motor.liberado and cerrado


@pytest.mark.asyncio
async def test_lifespan_sin_poder_construir_el_motor_arranca_y_rutas_dan_503():
    def motor_roto(_url):
        raise OSError("sin driver")

    app = crear_app(_cfg(), catalogo=_catalogo(),
                    constructores=Constructores(motor=motor_roto))
    async with app.router.lifespan_context(app):
        async with _cliente(app) as c:
            r = await c.get(f"/usuarios/{UID}/perfil")
    assert r.status_code == 503


class ErrorFatalDePrueba(Exception):
    pass


@pytest.mark.asyncio
async def test_error_fatal_de_arranque_detiene_el_lifespan(monkeypatch):
    monkeypatch.setattr(main_mod, "ERRORES_FATALES_ARRANQUE", (ErrorFatalDePrueba,))

    @asynccontextmanager
    async def checkpointer(_url):
        raise ErrorFatalDePrueba("config invalida")
        yield  # pragma: no cover

    app = crear_app(_cfg(), repo=RepoFalso(), catalogo=_catalogo(),
                    constructores=Constructores(checkpointer=checkpointer))
    with pytest.raises(ErrorFatalDePrueba):
        async with app.router.lifespan_context(app):
            pass  # pragma: no cover


@pytest.mark.asyncio
async def test_reglas_invalidas_contra_el_catalogo_detienen_el_arranque(tmp_path):
    from app.safety.reglas import ReglasInvalidas

    # Catalogo sin ningun ejercicio de hombro, rodilla ni lumbar: las zonas no bloquean nada.
    ruta = tmp_path / "catalogo.json"
    ruta.write_text(
        '[{"id": "Wrist_Curl", "name": "Wrist Curl", "primaryMuscles": ["forearms"],'
        ' "secondaryMuscles": [], "equipment": "dumbbell", "level": "beginner",'
        ' "instructions": ["x"]}]',
        encoding="utf-8",
    )

    def prohibido(*a, **k):
        raise AssertionError("no debe construirse el grafo con reglas invalidas")

    cfg = _cfg().model_copy(update={"catalogo_path": ruta})
    app = crear_app(cfg, repo=RepoFalso(),
                    constructores=Constructores(checkpointer=prohibido, grafo=prohibido))
    with pytest.raises(ReglasInvalidas, match="hombro_derecho"):
        async with app.router.lifespan_context(app):
            pass  # pragma: no cover


@pytest.mark.asyncio
async def test_lifespan_con_catalogo_real_valida_las_reglas_y_arranca():
    from pathlib import Path

    ruta = Path(__file__).resolve().parent.parent / "data" / "catalogo" / "exercises.json"
    cfg = _cfg().model_copy(update={"catalogo_path": ruta})

    def prohibido(*a, **k):
        raise AssertionError("no debe construirse nada")

    app = crear_app(cfg, grafo=GrafoFalso(), repo=RepoFalso(),
                    constructores=Constructores(motor=prohibido, checkpointer=prohibido,
                                                grafo=prohibido))
    async with app.router.lifespan_context(app):
        assert len(app.state.catalogo) == 876


def test_settings_catalogo_path_por_defecto_es_el_catalogo_real():
    from pathlib import Path

    assert _cfg().catalogo_path == Path("data/catalogo/exercises.json")


def test_reglas_invalidas_es_error_fatal_de_arranque():
    from app.safety.reglas import ReglasInvalidas

    assert ReglasInvalidas in main_mod.ERRORES_FATALES_ARRANQUE


# --- I1: /chat no anula una pausa HITL pendiente ---------------------------------------

@pytest.mark.asyncio
async def test_chat_sobre_hilo_en_pausa_devuelve_409_y_no_invoca_el_grafo():
    grafo = GrafoFalso(pausado=True)
    app = crear_app(grafo=grafo, repo=RepoFalso(), catalogo=_catalogo())
    async with _cliente(app) as c:
        r = await c.post("/chat", json={"usuario_id": UID, "mensaje": "dame una rutina"})
    assert r.status_code == 409
    assert f"/hitl/{UID}/reanudar" in r.json()["detail"]
    assert grafo.invocaciones == []


@pytest.mark.asyncio
async def test_chat_sobre_hilo_que_fallo_a_mitad_no_es_una_pausa():
    # un turno que fallo deja `next` sin interrupciones: /chat sigue funcionando
    class GrafoConTareaPendiente(GrafoFalso):
        async def aget_state(self, config):
            return SimpleNamespace(next=("supervisor",), interrupts=(), values={})

    grafo = GrafoConTareaPendiente({"respuesta": "Hola"})
    app = crear_app(grafo=grafo, repo=RepoFalso(), catalogo=_catalogo())
    async with _cliente(app) as c:
        r = await c.post("/chat", json={"usuario_id": UID, "mensaje": "hola"})
    assert r.status_code == 200 and len(grafo.invocaciones) == 1


# --- M-b: plantilla de pausa segun el motivo ---------------------------------------------

@pytest.mark.asyncio
@pytest.mark.parametrize("motivo, esperado, prohibido", [
    ("dolor_agudo", "dolor agudo", None),
    ("zona_sin_regla", "zona que no puedo evaluar", "dolor agudo"),
    ("escalado_supervisor", "revisión humana", "dolor agudo"),
])
async def test_plantilla_de_pausa_segun_el_motivo(motivo, esperado, prohibido):
    salida = {"__interrupt__": [Interrupt(value={"motivo": motivo, "ejercicio": None,
                                                  "mensaje": "x"})]}
    app = crear_app(grafo=GrafoFalso(salida), repo=RepoFalso(), catalogo=_catalogo())
    async with _cliente(app) as c:
        r = await c.post("/chat", json={"usuario_id": UID, "mensaje": "x"})
    texto = r.json()["respuesta"]
    assert esperado in texto
    assert texto.endswith("Esto no es un diagnóstico médico.")
    if prohibido:
        assert prohibido not in texto.lower()
        assert "Detén ese ejercicio" not in texto


# --- I2 / M-c: GET /rutinas/actual nunca sirve una rutina insegura -----------------------

def _rutina(*ids: str) -> Rutina:
    return Rutina(usuario_id=UUID(UID), version=3, dias=[DiaRutina(nombre="A", ejercicios=[
        EjercicioPlanificado(ejercicio_id=i, series=3, repeticiones="8", descanso_seg=60,
                             fuentes=[]) for i in ids])])


@pytest.mark.asyncio
async def test_rutina_actual_en_revision_devuelve_409():
    repo = RepoFalso()
    repo.rutinas[UUID(UID)] = _rutina("sentadilla")
    app = crear_app(grafo=GrafoFalso(pausado=True), repo=repo, catalogo=_catalogo())
    async with _cliente(app) as c:
        r = await c.get(f"/usuarios/{UID}/rutinas/actual")
    assert r.status_code == 409
    assert "revisión" in r.json()["detail"]


@pytest.mark.asyncio
async def test_rutina_actual_con_ejercicio_bloqueado_por_lesion_activa_devuelve_409():
    repo = RepoFalso()
    repo.rutinas[UUID(UID)] = _rutina("press_militar", "sentadilla")
    repo.lesiones[UUID(UID)] = [Lesion(zona="hombro_derecho", severidad="leve", activa=True)]
    app = crear_app(grafo=GrafoFalso(), repo=repo, catalogo=_catalogo())
    async with _cliente(app) as c:
        r = await c.get(f"/usuarios/{UID}/rutinas/actual")
    assert r.status_code == 409
    assert "press_militar" not in r.text


@pytest.mark.asyncio
async def test_rutina_actual_con_ejercicio_excluido_por_dolor_devuelve_409():
    repo = RepoFalso()
    repo.rutinas[UUID(UID)] = _rutina("sentadilla")
    grafo = GrafoFalso(valores={"ejercicios_excluidos": ["sentadilla"]})
    app = crear_app(grafo=grafo, repo=repo, catalogo=_catalogo())
    async with _cliente(app) as c:
        r = await c.get(f"/usuarios/{UID}/rutinas/actual")
    assert r.status_code == 409


@pytest.mark.asyncio
async def test_rutina_actual_segura_con_lesion_en_otra_zona_se_sirve():
    repo = RepoFalso()
    repo.rutinas[UUID(UID)] = _rutina("press_militar")
    repo.lesiones[UUID(UID)] = [Lesion(zona="tobillo", severidad="leve", activa=True)]
    app = crear_app(grafo=GrafoFalso(), repo=repo, catalogo=_catalogo())
    async with _cliente(app) as c:
        r = await c.get(f"/usuarios/{UID}/rutinas/actual")
    # la zona sin regla se cubre con la pausa HITL (409 mientras esta pendiente), no aqui
    assert r.status_code == 200


@pytest.mark.asyncio
async def test_rutina_actual_sin_grafo_falla_cerrado_con_503():
    repo = RepoFalso()
    repo.rutinas[UUID(UID)] = _rutina("sentadilla")
    app = crear_app(grafo=None, repo=repo, catalogo=_catalogo())
    async with _cliente(app) as c:
        r = await c.get(f"/usuarios/{UID}/rutinas/actual")
    assert r.status_code == 503
