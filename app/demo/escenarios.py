"""Conversacion narrada del modo demo (cinco escenarios) sobre el grafo real.

Real: el grafo LangGraph compilado (`construir_grafo`), los nodos, las guardas deterministas,
las reglas de seguridad por zona, el detector de dolor y de urgencia toracica, el catalogo
`data/catalogo/exercises.json`, las guias `data/guias/*.md` y la busqueda hibrida (Qdrant en
modo `:memory:`). Simulado: el LLM (salidas estructuradas fijas por paso), la persistencia (en
memoria) y los codificadores de embeddings (deterministas).
"""

import warnings
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from uuid import UUID

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command
from qdrant_client import AsyncQdrantClient

from app.agentes.checkpointer import serializador_estado
from app.agentes.estado import (
    AnalisisMensaje, DecisionSupervisor, LesionReportada, PerfilParcial, PlanPropuesto,
    RespuestaConversacion,
)
from app.agentes.grafo import config_hilo, construir_grafo
from app.agentes.nodos import AVISO_MEDICO, MOTIVO_PECHO, detectar_dolor_pecho, texto_pausa
from app.catalogo.cargador import cargar_catalogo
from app.demo.dobles import (
    DensoDeterminista, DispersoDeterminista, LLMGuionado, RepositorioMemoria,
)
from app.domain.modelos import Lesion, Nivel, Rutina
from app.rag.ingesta import Documento, documento_desde_ejercicio, documentos_desde_guias, ingerir
from app.rag.recuperador import FiltrosBusqueda, buscar
from app.safety.reglas import ids_bloqueados, indice_bloqueo, validar_reglas_contra_catalogo
from app.settings import Settings

RAIZ = Path(__file__).resolve().parents[2]
CATALOGO_PATH = RAIZ / "data" / "catalogo" / "exercises.json"
GUIAS_DIR = RAIZ / "data" / "guias"

TITULO = (
    "MODO DEMO — LLM simulado; la lógica del grafo, el catálogo y las reglas de seguridad "
    "son reales"
)
LINEA_FINAL_OK = "DEMO COMPLETADA: 5/5 escenarios correctos (sin Docker, sin red y sin clave de Gemini)"

FUENTE = ["guia:tecnica_basica"]

# Rotulos de cada respuesta del coach en la narracion.
ORIGEN_REAL = "real"  # texto determinista del sistema real (plantillas, rutina formateada, 112)
ORIGEN_SIMULADO = "LLM simulado"  # texto escrito por el LLM guionado


def _dia(nombre: str, *ids: str) -> dict:
    return {"nombre": nombre, "ejercicios": [
        {"ejercicio_id": i, "series": 3, "repeticiones": "8-12", "descanso_seg": 90,
         "fuentes": FUENTE} for i in ids]}


def _plan(*dias: dict) -> PlanPropuesto:
    return PlanPropuesto.model_validate({"dias": list(dias)})


# Plan inicial (3 dias, barra y mancuernas): todos los ids existen en el catalogo real.
PLAN_INICIAL = _plan(
    _dia("Día 1 - Pierna y empuje", "Barbell_Squat", "Barbell_Bench_Press_-_Medium_Grip", "Crunches"),
    _dia("Día 2 - Tracción y pierna", "Bent_Over_Barbell_Row", "Dumbbell_Lunges", "Dumbbell_Bicep_Curl"),
    _dia("Día 3 - Hombro y cadera", "Standing_Military_Press", "Barbell_Hip_Thrust", "Hammer_Curls"),
)
# Propuesta que el LLM simulado hace con la lesion de hombro: incluye un press de hombro.
PLAN_CON_RIESGO = _plan(
    _dia("Día 1 - Pierna", "Dumbbell_Lunges", "Barbell_Hip_Thrust", "Crunches"),
    _dia("Día 2 - Brazos y hombro", "Dumbbell_Shoulder_Press", "Dumbbell_Bicep_Curl"),
    _dia("Día 3 - Pierna y brazos", "Dumbbell_Step_Ups", "Hammer_Curls", "Barbell_Curl"),
)
# Segunda propuesta, tras el rechazo de seguridad.
PLAN_SEGURO = _plan(
    _dia("Día 1 - Pierna", "Dumbbell_Lunges", "Barbell_Hip_Thrust", "Crunches"),
    _dia("Día 2 - Brazos", "Dumbbell_Bicep_Curl", "Hammer_Curls"),
    _dia("Día 3 - Pierna y brazos", "Dumbbell_Step_Ups", "Barbell_Curl"),
)


@dataclass
class ResultadoDemo:
    comprobaciones: list[tuple[str, bool]] = field(default_factory=list)
    respuestas: dict[str, str] = field(default_factory=dict)
    retirados_por_lesion: list[str] = field(default_factory=list)
    rechazados_por_seguridad: list[str] = field(default_factory=list)
    llamadas_llm: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return bool(self.comprobaciones) and all(v for _, v in self.comprobaciones)


def _ids(rutina: Rutina | None) -> list[str]:
    return [p.ejercicio_id for d in (rutina.dias if rutina else []) for p in d.ejercicios]


class _Narrador:
    def __init__(self, escribir: Callable[[str], Any], resultado: ResultadoDemo):
        self.escribir = escribir
        self.r = resultado

    def __call__(self, texto: str = "") -> None:
        self.escribir(texto)

    def seccion(self, titulo: str) -> None:
        self("")
        self("-" * 78)
        self(titulo)
        self("-" * 78)

    def usuario(self, texto: str) -> None:
        self(f"\nUsuario > {texto}")

    def coach(self, texto: str, origen: str = ORIGEN_REAL) -> None:
        """Respuesta al usuario. `origen` dice si el texto lo escribio el LLM simulado o si es
        una salida determinista real (plantillas, rutina formateada, filtro, 112)."""
        lineas = texto.splitlines() or [""]
        prefijo = f"Coach [{origen}] > "
        self(f"{prefijo}{lineas[0]}")
        for linea in lineas[1:]:
            self(f"{' ' * len(prefijo)}{linea}")

    def guion(self, esquemas: list[str]) -> None:
        if esquemas:
            self(f"  [{ORIGEN_SIMULADO}] salidas guionadas que pidió el grafo: {', '.join(esquemas)}")

    def comprobar(self, descripcion: str, valor: bool) -> None:
        self.r.comprobaciones.append((descripcion, bool(valor)))
        self(f"  [{'OK' if valor else 'FALLO'}] {descripcion}")


def _respuesta(salida: dict) -> tuple[str, bool]:
    """Texto que veria el usuario por la API (misma logica que POST /chat)."""
    interrupciones = salida.get("__interrupt__")
    if interrupciones:
        valor = getattr(interrupciones[0], "value", interrupciones[0])
        motivo = valor.get("motivo") if isinstance(valor, dict) else None
        return texto_pausa(motivo), True
    return salida.get("respuesta") or "", False


async def ejecutar_demo(escribir: Callable[[str], Any] = print) -> ResultadoDemo:
    warnings.filterwarnings("ignore", message="Payload indexes have no effect")
    resultado = ResultadoDemo()
    n = _Narrador(escribir, resultado)

    n("=" * 78)
    n(TITULO)
    n("=" * 78)

    settings = Settings(
        _env_file=None, google_api_key="", gemini_model="", qdrant_collection="demo",
        catalogo_path=CATALOGO_PATH, guias_dir=GUIAS_DIR, max_reintentos_seguridad=2,
    )
    catalogo = {e.id: e for e in cargar_catalogo(CATALOGO_PATH)}
    validar_reglas_contra_catalogo(catalogo)
    indice = indice_bloqueo(catalogo)

    # RAG: catalogo + guias reales en Qdrant en memoria con codificadores deterministas
    cliente = AsyncQdrantClient(location=":memory:")
    denso, disperso = DensoDeterminista(), DispersoDeterminista()
    guias = documentos_desde_guias(GUIAS_DIR)
    documentos = [documento_desde_ejercicio(e) for e in catalogo.values()] + guias
    await ingerir(documentos, settings, cliente=cliente, denso=denso, disperso=disperso)
    recuperados: list[Documento] = []

    async def buscador(consulta: str, filtros: FiltrosBusqueda) -> list[Documento]:
        docs = await buscar(consulta, filtros, 5, settings, cliente=cliente, denso=denso,
                            disperso=disperso)
        recuperados[:] = docs
        return docs

    n(f"Catálogo real: {len(catalogo)} ejercicios ({CATALOGO_PATH.relative_to(RAIZ).as_posix()})")
    n(f"RAG: {len(documentos)} documentos ({len(guias)} fragmentos de guías) en Qdrant :memory:")
    n("Grafo: LangGraph compilado con checkpointer en memoria; repositorio en memoria.")

    repo = RepositorioMemoria()
    llm = LLMGuionado()
    grafo = await construir_grafo(
        settings, repo, InMemorySaver(serde=serializador_estado()),
        catalogo=catalogo, llm=llm, buscador=buscador,
    )
    uid: UUID = await repo.crear_usuario()
    cfg = config_hilo(uid)

    async def turno(mensaje: str, origen: str = ORIGEN_REAL, **guion: list) -> tuple[str, bool, dict]:
        llm.programar(**guion)
        n.usuario(mensaje)
        previas = len(llm.llamadas)
        salida = await grafo.ainvoke({"usuario_id": uid, "mensaje": mensaje}, cfg)
        n.guion(llm.llamadas[previas:])
        texto, pausa = _respuesta(salida)
        n.coach(texto, origen)
        if "PlanPropuesto" in llm.llamadas[previas:] and "Tu rutina" in texto:
            n("  (los ejercicios los propuso el LLM simulado; el formato, el catálogo y el filtro "
              "de seguridad son reales)")
        return texto, pausa, salida

    async def reanudar(revision: str) -> str:
        n(f"\nRevisor humano > {revision}   (POST /hitl/{{thread_id}}/reanudar)")
        salida = await grafo.ainvoke(Command(resume=revision), cfg)
        texto, _ = _respuesta(salida)
        n.coach(texto)
        return texto

    # --- 1. Onboarding en dos mensajes -> rutina con ids del catalogo ---------------------
    n.seccion("Escenario 1: onboarding repartido en dos mensajes -> rutina del catálogo")
    texto, _, _ = await turno(
        "Hola, quiero ganar masa muscular y puedo entrenar 3 días por semana",
        AnalisisMensaje=[AnalisisMensaje(perfil=PerfilParcial(objetivo="hipertrofia",
                                                               dias_disponibles=3))],
        DecisionSupervisor=[DecisionSupervisor(destino="sintesis")],
    )
    n.comprobar("perfil incompleto: plantilla fija que pide lo que falta (sin plan)",
                "Me falta saber" in texto and await repo.rutina_actual(uid) is None)
    texto, _, _ = await turno(
        "Soy principiante y entreno con barra y mancuernas",
        AnalisisMensaje=[AnalisisMensaje(perfil=PerfilParcial(
            nivel=Nivel.principiante, equipo=["barra", "mancuernas"]))],
        DecisionSupervisor=[DecisionSupervisor(destino="programador")],
        PlanPropuesto=[PLAN_INICIAL],
    )
    resultado.respuestas["rutina_inicial"] = texto
    rutina = await repo.rutina_actual(uid)
    n(f"  RAG: {len(recuperados)} documentos recuperados para el programador "
      f"({', '.join(sorted({d.fuente for d in recuperados}))})")
    n.comprobar("perfil completo guardado y rutina v1 guardada en el repositorio",
                await repo.obtener_perfil(uid) is not None and rutina is not None
                and rutina.version == 1)
    n.comprobar("todos los ejercicios de la rutina existen en el catálogo real",
                bool(_ids(rutina)) and all(i in catalogo for i in _ids(rutina)))
    n.comprobar("la respuesta lleva el aviso médico", texto.endswith(AVISO_MEDICO))

    # --- 2. Lesion activa de hombro -> filtro determinista ---------------------------------
    n.seccion("Escenario 2: lesión activa de hombro -> rutina sin ejercicios bloqueados")
    lesion = Lesion(zona="hombro_derecho", severidad="moderada", activa=True)
    prohibidos = ids_bloqueados([lesion], indice)
    n(f"Regla de seguridad 'hombro_derecho': bloquea {len(prohibidos)} de {len(catalogo)} "
      "ejercicios del catálogo.")
    antes = _ids(await repo.rutina_actual(uid))
    texto, _, _ = await turno(
        "Ayer me lesioné el hombro derecho, el fisio dice que es moderado",
        AnalisisMensaje=[AnalisisMensaje(lesiones_nuevas=[
            LesionReportada(zona="hombro_derecho", severidad="moderada")])],
    )
    despues = _ids(await repo.rutina_actual(uid))
    retirados = [i for i in antes if i not in despues]
    resultado.retirados_por_lesion = retirados
    n(f"  Retirados por el filtro determinista: {', '.join(retirados)}")
    n.comprobar("se retiraron exactamente los ejercicios que bloquea la regla",
                set(retirados) == {i for i in antes if i in prohibidos} and bool(retirados))
    n.comprobar("la rutina vigente no contiene ejercicios bloqueados",
                bool(despues) and not set(despues) & prohibidos)

    texto, _, salida = await turno(
        "Hazme una rutina nueva teniendo en cuenta el hombro",
        AnalisisMensaje=[AnalisisMensaje()],
        DecisionSupervisor=[DecisionSupervisor(destino="programador")],
        PlanPropuesto=[PLAN_CON_RIESGO, PLAN_SEGURO],
    )
    propuestos = [p.ejercicio_id for d in PLAN_CON_RIESGO.dias for p in d.ejercicios]
    rechazados = [i for i in propuestos if i in prohibidos]
    resultado.rechazados_por_seguridad = rechazados
    final = _ids(await repo.rutina_actual(uid))
    n(f"  El LLM simulado propuso {', '.join(rechazados)}: el nodo de seguridad rechazó el plan "
      f"y el programador lo rehízo (reintentos de seguridad: {salida.get('intentos_seguridad')}).")
    n.comprobar("el plan con riesgo no llegó al usuario ni al repositorio",
                bool(rechazados) and not set(final) & prohibidos
                and not any(catalogo[i].nombre in texto for i in rechazados))

    # --- 3. Dolor agudo -> pausa HITL -> reanudar ------------------------------------------
    n.seccion("Escenario 3: dolor agudo -> pausa para revisión humana -> reanudar")
    texto, pausa, _ = await turno(
        "Al hacer las zancadas con mancuernas noté un pinchazo en la rodilla",
        AnalisisMensaje=[AnalisisMensaje(
            dolor_agudo=True, ejercicio_con_dolor="Dumbbell_Lunges", zona_dolor="rodilla",
            cita_dolor="noté un pinchazo en la rodilla")],
    )
    n.comprobar("la conversación queda pausada (interrupt de LangGraph)", pausa)
    n.comprobar("el ejercicio con dolor se retiró de la rutina antes de la pausa",
                "Dumbbell_Lunges" not in _ids(await repo.rutina_actual(uid))
                and "Dumbbell_Lunges" in await repo.exclusiones_activas(uid))
    texto = await reanudar("Revisado por el entrenador: seguir sin zancadas y consultar al fisio")
    resultado.respuestas["tras_revision"] = texto
    n.comprobar("tras la revisión se deriva a un profesional", "profesional" in texto)

    # --- 4. Dolor en el pecho -> plantilla 112 ---------------------------------------------
    n.seccion("Escenario 4: dolor en el pecho -> urgencia (112)")
    mensaje = "Siento una opresión en el pecho y me cuesta respirar"
    n(f"Detector determinista de urgencia torácica: {detectar_dolor_pecho(mensaje)} "
      "(no depende del LLM, que aquí no marca nada)")
    texto, pausa, _ = await turno(mensaje, AnalisisMensaje=[AnalisisMensaje()])
    resultado.respuestas["pecho"] = texto
    n.comprobar("plantilla fija de urgencia con el 112 y pausa HITL",
                pausa and "112" in texto and texto == texto_pausa(MOTIVO_PECHO))
    await reanudar("Usuario contactado; derivado a urgencias")

    # --- 5. Fuera de alcance -> sin plan -----------------------------------------------------
    n.seccion("Escenario 5: pregunta fuera de alcance -> sin plan")
    versiones = len(repo.rutinas.get(uid, []))
    texto, pausa, _ = await turno(
        "¿Quién ganó el Mundial de fútbol de 2022?", ORIGEN_SIMULADO,
        AnalisisMensaje=[AnalisisMensaje()],
        DecisionSupervisor=[DecisionSupervisor(destino="sintesis")],
        RespuestaConversacion=[RespuestaConversacion(
            texto="Eso queda fuera de lo que puedo ayudarte: soy un coach de gimnasio. Si "
                  "quieres, pregúntame por tu entrenamiento.",
            contiene_ejercicios=False)],
    )
    resultado.respuestas["fuera_de_alcance"] = texto
    n.comprobar("responde sin plan y no guarda ninguna rutina nueva",
                not pausa and "Tu rutina" not in texto
                and len(repo.rutinas.get(uid, [])) == versiones)

    await cliente.close()
    resultado.llamadas_llm = list(llm.llamadas)
    n.comprobar("el guion del LLM simulado se consumió completo", not llm.pendientes())

    n("")
    n("=" * 78)
    total = len(resultado.comprobaciones)
    correctas = sum(v for _, v in resultado.comprobaciones)
    n(f"Comprobaciones: {correctas}/{total}")
    n(LINEA_FINAL_OK if resultado.ok else "DEMO CON FALLOS: revisa las comprobaciones marcadas FALLO")
    return resultado
