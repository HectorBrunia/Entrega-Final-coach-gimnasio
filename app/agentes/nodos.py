"""Nodos del grafo del coach.

Principio (spec 7): el LLM nunca es la ultima linea de defensa en lesiones. Todas las
decisiones de seguridad (dolor agudo, zonas sin regla, ejercicios bloqueados) son
deterministas y se evaluan antes o despues del LLM, nunca solo por el LLM.
"""

import logging
import re
import unicodedata
from collections.abc import Awaitable, Callable
from uuid import UUID

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langgraph.types import interrupt

from app.agentes.estado import (
    AnalisisMensaje,
    DecisionSupervisor,
    EstadoCoach,
    PlanPropuesto,
)
from app.domain.modelos import DiaRutina, Ejercicio, Lesion, Perfil, Rutina
from app.herramientas.funciones import consultar_historial, validar_plan
from app.persistencia.repositorios import RepositorioDominio
from app.rag.ingesta import Documento
from app.rag.recuperador import FiltrosBusqueda
from app.safety.reglas import REGLAS_LESION, ZonaLesionDesconocida, filtrar_por_lesiones

logger = logging.getLogger(__name__)

Buscador = Callable[[str, FiltrosBusqueda], Awaitable[list[Documento]]]

AVISO_MEDICO = "Esto no es un diagnóstico médico."

# Frases que por si solas disparan la pausa HITL (comparacion sin mayusculas ni tildes).
PALABRAS_DOLOR_AGUDO: tuple[str, ...] = (
    "dolor agudo",
    "dolor fuerte",
    "dolor intenso",
    "pinchazo",
    "me duele mucho",
    "dolor que empeora",
    "empeora el dolor",
    "duele cada vez mas",
)

MAX_CANDIDATOS = 40
HISTORIAL_PROMPT = 6

MSG_SIN_PLAN_SEGURO = (
    "No puedo generar un plan seguro con tus lesiones actuales. Te recomiendo consultar "
    "a un profesional (médico, fisioterapeuta o entrenador certificado) antes de continuar."
)
MSG_FALLO_PLAN = "No pude generar un plan en este momento. Inténtalo de nuevo en unos minutos."
MSG_RESPUESTA_INSEGURA = (
    "Prefiero no responder a eso con recomendaciones concretas porque podrían no ser seguras "
    "con tus lesiones o molestias actuales. Si quieres, puedo armarte una rutina validada."
)


def _normalizar(texto: str) -> str:
    sin_tildes = unicodedata.normalize("NFKD", texto)
    sin_tildes = "".join(c for c in sin_tildes if not unicodedata.combining(c))
    return " ".join(sin_tildes.lower().replace("_", " ").split())


_PALABRAS_NORM = tuple(_normalizar(p) for p in PALABRAS_DOLOR_AGUDO)


def detectar_dolor_agudo(mensaje: str) -> bool:
    """Chequeo determinista: basta con una frase de la lista para escalar a humano."""
    texto = _normalizar(mensaje)
    return any(p in texto for p in _PALABRAS_NORM)


def _contiene(texto_norm: str, frase_norm: str) -> bool:
    return bool(frase_norm) and re.search(rf"\b{re.escape(frase_norm)}\b", texto_norm) is not None


def _ids_rutina(rutina: Rutina) -> list[str]:
    return list(dict.fromkeys(p.ejercicio_id for d in rutina.dias for p in d.ejercicios))


def _quitar_ejercicios(rutina: Rutina, quitar: set[str]) -> Rutina:
    dias = [
        DiaRutina(nombre=d.nombre, ejercicios=[p for p in d.ejercicios if p.ejercicio_id not in quitar])
        for d in rutina.dias
    ]
    return rutina.model_copy(update={"dias": [d for d in dias if d.ejercicios]})


def _con_aviso(texto: str) -> str:
    return f"{texto.rstrip()}\n\n{AVISO_MEDICO}"


class Nodos:
    def __init__(
        self,
        repo: RepositorioDominio,
        catalogo: dict[str, Ejercicio],
        llm: BaseChatModel,
        buscador: Buscador,
    ):
        self.repo = repo
        self.catalogo = catalogo
        self.llm = llm
        self.buscador = buscador
        self._analizar = llm.with_structured_output(AnalisisMensaje)
        self._decidir = llm.with_structured_output(DecisionSupervisor)
        self._planificar = llm.with_structured_output(PlanPropuesto)

    # --- utilidades -----------------------------------------------------------

    def _resolver_ejercicio(self, nombre: str | None) -> str | None:
        if not nombre:
            return None
        if nombre in self.catalogo:
            return nombre
        objetivo = _normalizar(nombre)
        for ej in self.catalogo.values():
            if objetivo in (_normalizar(ej.id), _normalizar(ej.nombre)):
                return ej.id
        return self._ejercicio_en_texto(nombre)

    def _ejercicio_en_texto(self, texto: str) -> str | None:
        norm = _normalizar(texto)
        encontrados = [
            (len(frase), ej.id)
            for ej in self.catalogo.values()
            for frase in {_normalizar(ej.id), _normalizar(ej.nombre)}
            if _contiene(norm, frase)
        ]
        return max(encontrados)[1] if encontrados else None

    def _menciona(self, texto: str, ids: set[str]) -> bool:
        norm = _normalizar(texto)
        for i in ids:
            frases = {_normalizar(i)}
            if i in self.catalogo:
                frases.add(_normalizar(self.catalogo[i].nombre))
            if any(_contiene(norm, f) for f in frases):
                return True
        return False

    def _prohibidos(self, lesiones: list[Lesion], excluidos: list[str]) -> set[str]:
        """Ids que no pueden recomendarse. Propaga ZonaLesionDesconocida."""
        res = filtrar_por_lesiones(list(self.catalogo.values()), lesiones)
        return {i for i, _ in res.bloqueados} | set(excluidos)

    def _nombre(self, ejercicio_id: str) -> str:
        ej = self.catalogo.get(ejercicio_id)
        return ej.nombre if ej else ejercicio_id

    @staticmethod
    def _historial(estado: EstadoCoach) -> list[BaseMessage]:
        return list(estado.get("mensajes") or [])[-HISTORIAL_PROMPT:]

    # --- evaluador --------------------------------------------------------------

    async def evaluador(self, estado: EstadoCoach) -> dict:
        uid: UUID = estado["usuario_id"]
        mensaje = estado["mensaje"]
        perfil = await self.repo.obtener_perfil(uid)
        rutina = await self.repo.rutina_actual(uid)
        dolor_por_palabra = detectar_dolor_agudo(mensaje)

        analisis: AnalisisMensaje | None = None
        try:
            analisis = await self._analizar.ainvoke(self._prompt_evaluador(estado, perfil))
        except Exception:
            # sin LLM (429 agotado u otro fallo) no se puede analizar, pero el dolor agudo
            # detectado por palabra clave no puede perderse: se escala igual a humano
            if not dolor_por_palabra:
                raise
            logger.warning("Fallo el LLM del evaluador; se escala a humano por palabra clave de dolor")
        analisis = analisis or AnalisisMensaje()

        perfil = await self._actualizar_perfil(uid, perfil, analisis)
        for lesion in analisis.lesiones_nuevas:
            await self.repo.agregar_lesion(uid, lesion)
        lesiones = await self.repo.lesiones_activas(uid)

        dolor = dolor_por_palabra or analisis.dolor_agudo
        ejercicio = None
        excluidos = list(estado.get("ejercicios_excluidos") or [])
        if dolor:
            ejercicio = self._resolver_ejercicio(analisis.ejercicio_con_dolor) or self._ejercicio_en_texto(
                mensaje
            )
            if ejercicio in self.catalogo and ejercicio not in excluidos:
                excluidos.append(ejercicio)

        return {
            "perfil": perfil,
            "lesiones": lesiones,
            "rutina": rutina,
            "bloqueados": [],
            "intentos_seguridad": 0,
            "rutina_nueva": False,
            "plan_validado": False,
            "fallo_plan": False,
            "retirados": [],
            "lesion_nueva": any(l.activa for l in analisis.lesiones_nuevas),
            "requiere_humano": dolor,
            "motivo_humano": "dolor_agudo" if dolor else None,
            "ejercicio_con_dolor": ejercicio or analisis.ejercicio_con_dolor,
            "ejercicios_excluidos": excluidos,
            "explicacion": "",
            "siguiente": None,
            "respuesta": None,
            "mensajes": [HumanMessage(content=mensaje)],
        }

    def _prompt_evaluador(self, estado: EstadoCoach, perfil: Perfil | None) -> list[BaseMessage]:
        zonas = ", ".join(sorted(REGLAS_LESION))
        sistema = (
            "Eres el evaluador de un coach de gimnasio. Extrae del ultimo mensaje del usuario: "
            "datos de perfil (objetivo, dias_disponibles 1-7, equipo, nivel), lesiones nuevas "
            f"(zona en formato snake_case, por ejemplo: {zonas}), y si reporta dolor agudo o "
            "dolor que empeora durante un ejercicio (dolor_agudo) y en que ejercicio. "
            "Deja vacio lo que no se mencione. "
            f"Perfil actual: {perfil.model_dump_json() if perfil else 'ninguno'}."
        )
        return [SystemMessage(content=sistema), *self._historial(estado), HumanMessage(content=estado["mensaje"])]

    async def _actualizar_perfil(
        self, uid: UUID, perfil: Perfil | None, analisis: AnalisisMensaje
    ) -> Perfil | None:
        parcial = analisis.perfil
        if parcial is None:
            return perfil
        cambios = parcial.model_dump(exclude_none=True)
        if not cambios:
            return perfil
        base = perfil.model_dump() if perfil else {"usuario_id": uid}
        datos = {**base, **cambios}
        try:
            nuevo = Perfil.model_validate(datos)
        except ValueError:
            return perfil  # perfil incompleto: se pedira el resto en la respuesta
        await self.repo.guardar_perfil(nuevo)
        return nuevo

    # --- supervisor -------------------------------------------------------------

    async def supervisor(self, estado: EstadoCoach) -> dict:
        # Guardas deterministas: corren antes del LLM y no se pueden saltar.
        if estado.get("requiere_humano"):
            return {"siguiente": "hitl"}
        try:
            filtrar_por_lesiones([], estado.get("lesiones") or [])
        except ZonaLesionDesconocida:
            return {"siguiente": "hitl", "requiere_humano": True, "motivo_humano": "zona_sin_regla"}
        if estado.get("lesion_nueva") and estado.get("rutina") is not None:
            return {"siguiente": "seguridad"}

        decision = await self._decidir.ainvoke(self._prompt_supervisor(estado))
        destino = decision.destino if decision else "sintesis"

        # Guardas posteriores: el LLM no puede pedir algo imposible o inseguro.
        if destino == "hitl":
            return {"siguiente": "hitl", "requiere_humano": True, "motivo_humano": "escalado_supervisor"}
        if destino in ("programador", "progreso") and estado.get("perfil") is None:
            destino = "sintesis"
        elif destino == "progreso" and estado.get("rutina") is None:
            destino = "programador"
        elif destino == "seguridad" and estado.get("rutina") is None:
            destino = "sintesis"
        return {"siguiente": destino}

    def _prompt_supervisor(self, estado: EstadoCoach) -> list[BaseMessage]:
        sistema = (
            "Eres el supervisor de un coach de gimnasio. Elige el siguiente paso:\n"
            "- programador: el usuario pide una rutina nueva o cambiarla.\n"
            "- progreso: el usuario quiere ajustar la rutina segun sus entrenos registrados.\n"
            "- seguridad: el usuario quiere ver o revisar su rutina actual.\n"
            "- sintesis: preguntas generales, saludos, datos que faltan o temas fuera de alcance.\n"
            "- hitl: el usuario describe una situacion medica que requiere revision humana.\n"
            f"Perfil: {'completo' if estado.get('perfil') else 'incompleto'}. "
            f"Rutina vigente: {'si' if estado.get('rutina') else 'no'}."
        )
        return [SystemMessage(content=sistema), *self._historial(estado), HumanMessage(content=estado["mensaje"])]

    # --- programador y progreso ---------------------------------------------------

    async def programador(self, estado: EstadoCoach) -> dict:
        return await self._proponer(estado, contexto_extra="")

    async def progreso(self, estado: EstadoCoach) -> dict:
        historial = await consultar_historial(self.repo, estado["usuario_id"], 20)
        lineas = [
            f"{e.fecha} {e.ejercicio_id}: {e.series}x{e.repeticiones} {e.peso_kg} kg RPE {e.rpe}"
            for e in historial
        ]
        rutina = estado.get("rutina")
        contexto = (
            "Ajusta la progresion de la rutina vigente segun el historial.\n"
            f"Rutina vigente: {rutina.model_dump_json() if rutina else 'ninguna'}\n"
            "Historial reciente:\n" + ("\n".join(lineas) or "sin entrenos registrados")
        )
        return await self._proponer(estado, contexto_extra=contexto)

    async def _proponer(self, estado: EstadoCoach, contexto_extra: str) -> dict:
        previos = list(estado.get("bloqueados") or [])
        intentos = estado.get("intentos_seguridad", 0) + (1 if previos else 0)
        base = {"intentos_seguridad": intentos, "bloqueados": [], "rutina_nueva": False}
        perfil = estado.get("perfil")
        if perfil is None:
            return {**base, "rutina": None, "fallo_plan": True}

        excluidos = set(estado.get("ejercicios_excluidos") or []) | set(previos)
        try:
            permitidos = filtrar_por_lesiones(list(self.catalogo.values()), estado.get("lesiones") or [])
        except ZonaLesionDesconocida:
            return {**base, "requiere_humano": True, "motivo_humano": "zona_sin_regla"}

        consulta = f"rutina {perfil.objetivo} nivel {perfil.nivel.value} {' '.join(perfil.equipo)}"
        try:
            documentos = await self.buscador(consulta, FiltrosBusqueda(nivel=perfil.nivel))
        except Exception:
            logger.exception("Fallo la busqueda de conocimiento; se programa sin documentos")
            documentos = []

        candidatos = self._candidatos(perfil, permitidos.permitidos, excluidos, documentos)
        plan = await self._planificar.ainvoke(
            self._prompt_programador(estado, perfil, candidatos, documentos, previos, contexto_extra)
        )
        if plan is None or not plan.dias:
            return {**base, "rutina": None, "fallo_plan": True}
        rutina = Rutina(usuario_id=estado["usuario_id"], version=1, dias=plan.dias)
        return {**base, "rutina": rutina, "rutina_nueva": True, "plan_validado": False,
                "explicacion": plan.explicacion}

    @staticmethod
    def _candidatos(
        perfil: Perfil, permitidos: list[Ejercicio], excluidos: set[str], documentos: list[Documento]
    ) -> list[Ejercicio]:
        utiles = [e for e in permitidos if e.id not in excluidos]
        equipo = {_normalizar(x) for x in perfil.equipo}
        con_equipo = [e for e in utiles if _normalizar(e.equipo) in equipo] or utiles
        orden_rag = {d.id: i for i, d in enumerate(documentos)}
        con_equipo.sort(key=lambda e: orden_rag.get(e.id, len(orden_rag)))
        return con_equipo[:MAX_CANDIDATOS]

    def _prompt_programador(
        self,
        estado: EstadoCoach,
        perfil: Perfil,
        candidatos: list[Ejercicio],
        documentos: list[Documento],
        previos: list[str],
        contexto_extra: str,
    ) -> list[BaseMessage]:
        lista = "\n".join(f"- {e.id}: {e.nombre} ({e.musculo_primario})" for e in candidatos)
        guias = "\n".join(f"[{d.id}] ({d.fuente}) {d.texto[:400]}" for d in documentos if d.fuente != "catalogo")
        sistema = (
            "Eres el programador de rutinas de un coach de gimnasio. Arma una rutina con "
            f"exactamente {perfil.dias_disponibles} dias para el objetivo '{perfil.objetivo}', "
            f"nivel {perfil.nivel.value}. Usa SOLO ejercicio_id de esta lista:\n{lista}\n"
            "En 'fuentes' de cada ejercicio cita los ids de las guias usadas. En 'explicacion' "
            "justifica brevemente el plan citando las guias.\n"
            f"Guias:\n{guias or 'ninguna'}"
        )
        if previos:
            sistema += f"\nEl plan anterior fue rechazado por seguridad. NO uses: {', '.join(previos)}."
        if contexto_extra:
            sistema += "\n" + contexto_extra
        return [SystemMessage(content=sistema), HumanMessage(content=estado["mensaje"])]

    # --- seguridad --------------------------------------------------------------

    async def seguridad(self, estado: EstadoCoach) -> dict:
        if estado.get("requiere_humano"):
            return {"plan_validado": False}
        rutina = estado.get("rutina")
        if rutina is None:
            return {"bloqueados": [], "plan_validado": False}
        lesiones = estado.get("lesiones") or []
        excluidos = estado.get("ejercicios_excluidos") or []
        try:
            bloqueados = await self._bloqueados(rutina, lesiones, excluidos)
        except ZonaLesionDesconocida:
            return {"requiere_humano": True, "motivo_humano": "zona_sin_regla", "plan_validado": False}

        if bloqueados and not estado.get("rutina_nueva"):
            # Rutina ya persistida que deja de ser segura (p. ej. lesion nueva): se retiran
            # los ejercicios bloqueados de forma determinista y se guarda la nueva version.
            depurada = _quitar_ejercicios(rutina, set(bloqueados))
            if not await self._bloqueados(depurada, lesiones, excluidos):
                await self.repo.guardar_rutina(depurada)
                actual = await self.repo.rutina_actual(estado["usuario_id"])
                return {"rutina": actual, "bloqueados": [], "plan_validado": True,
                        "rutina_nueva": False, "retirados": bloqueados}

        if bloqueados:
            return {"bloqueados": bloqueados, "plan_validado": False}

        if estado.get("rutina_nueva"):
            await self.repo.guardar_rutina(rutina)
            rutina = await self.repo.rutina_actual(estado["usuario_id"])
        return {"rutina": rutina, "bloqueados": [], "plan_validado": True, "rutina_nueva": False}

    async def _bloqueados(self, rutina: Rutina, lesiones: list[Lesion], excluidos: list[str]) -> list[str]:
        bloqueados = await validar_plan(rutina, lesiones, self.catalogo)
        extra = [i for i in _ids_rutina(rutina) if i in excluidos and i not in bloqueados]
        return bloqueados + extra

    # --- HITL ---------------------------------------------------------------------

    async def hitl(self, estado: EstadoCoach) -> dict:
        motivo = estado.get("motivo_humano") or "dolor_agudo"
        ejercicio = estado.get("ejercicio_con_dolor")
        # Antes de interrupt() no hay efectos: el nodo se re-ejecuta completo al reanudar.
        revision = interrupt({
            "motivo": motivo,
            "ejercicio": ejercicio,
            "mensaje": estado.get("mensaje"),
        })
        logger.info("HITL reanudado (motivo=%s): %s", motivo, revision)

        uid = estado["usuario_id"]
        rutina = await self.repo.rutina_actual(uid)
        excluidos = set(estado.get("ejercicios_excluidos") or [])
        if rutina is not None and excluidos & set(_ids_rutina(rutina)):
            await self.repo.guardar_rutina(_quitar_ejercicios(rutina, excluidos))
            rutina = await self.repo.rutina_actual(uid)

        if motivo == "zona_sin_regla":
            texto = (
                "Registraste una lesión en una zona que no puedo evaluar de forma segura. "
                "Antes de seguir entrenando, consulta a un profesional (médico o fisioterapeuta)."
            )
        else:
            sobre = f" con {self._nombre(ejercicio)}" if ejercicio in self.catalogo else ""
            texto = (
                f"Reportaste dolor agudo{sobre}. Detén el ejercicio y consulta a un profesional "
                "(médico o fisioterapeuta) antes de continuar. No voy a recomendarte más ese ejercicio."
            )
        texto = _con_aviso(texto)
        return {
            "respuesta": texto,
            "rutina": rutina,
            "plan_validado": False,
            "requiere_humano": False,
            "mensajes": [AIMessage(content=texto)],
        }

    # --- sintesis -------------------------------------------------------------------

    async def sintesis(self, estado: EstadoCoach) -> dict:
        cambios: dict = {}
        if estado.get("bloqueados"):
            # reintentos agotados: nunca se entrega un plan con ejercicios bloqueados
            texto = MSG_SIN_PLAN_SEGURO
            cambios["rutina"] = None
        elif estado.get("plan_validado") and estado.get("rutina") is not None:
            texto = self._formatear_rutina(estado)
        elif estado.get("fallo_plan"):
            texto = MSG_FALLO_PLAN
        else:
            texto = await self._conversar(estado)
        texto = _con_aviso(texto)
        return {**cambios, "respuesta": texto, "mensajes": [AIMessage(content=texto)]}

    def _formatear_rutina(self, estado: EstadoCoach) -> str:
        rutina: Rutina = estado["rutina"]
        lineas: list[str] = []
        retirados = estado.get("retirados") or []
        if retirados:
            n = len(retirados)
            lineas.append(
                f"Retiré {n} ejercicio{'s' if n > 1 else ''} de tu rutina por tu lesión."
            )
        lineas.append(f"Tu rutina (versión {rutina.version}):")
        fuentes: list[str] = []
        for dia in rutina.dias:
            lineas.append(f"\n{dia.nombre}")
            for p in dia.ejercicios:
                lineas.append(
                    f"- {self._nombre(p.ejercicio_id)}: {p.series} x {p.repeticiones}, "
                    f"descanso {p.descanso_seg} s"
                )
                fuentes.extend(f for f in p.fuentes if f not in fuentes)
        explicacion = estado.get("explicacion") or ""
        try:
            prohibidos = self._prohibidos(estado.get("lesiones") or [], estado.get("ejercicios_excluidos") or [])
        except ZonaLesionDesconocida:
            prohibidos = None
        if explicacion and prohibidos is not None and not self._menciona(explicacion, prohibidos):
            lineas.append(f"\n{explicacion}")
        if fuentes:
            lineas.append(f"\nFuentes: {', '.join(fuentes)}")
        return "\n".join(lineas)

    async def _conversar(self, estado: EstadoCoach) -> str:
        lesiones = estado.get("lesiones") or []
        excluidos = estado.get("ejercicios_excluidos") or []
        try:
            prohibidos = self._prohibidos(lesiones, excluidos)
        except ZonaLesionDesconocida:
            return MSG_RESPUESTA_INSEGURA
        perfil = estado.get("perfil")
        sistema = (
            "Eres un coach de gimnasio. Responde en español, breve y sin inventar. Si la pregunta "
            "esta fuera del entrenamiento, rechaza con cortesia. Si falta el perfil, pide objetivo, "
            "dias disponibles, equipo y nivel. No des diagnosticos medicos.\n"
            f"Perfil: {perfil.model_dump_json() if perfil else 'incompleto'}.\n"
            f"Lesiones activas: {', '.join(l.zona for l in lesiones) or 'ninguna'}.\n"
            f"Nunca recomiendes: {', '.join(sorted(prohibidos)) or 'nada en particular'}."
        )
        mensajes = [SystemMessage(content=sistema), *self._historial(estado),
                    HumanMessage(content=estado["mensaje"])]
        respuesta = await self.llm.ainvoke(mensajes)
        texto = respuesta.text if isinstance(respuesta, AIMessage) else str(respuesta.content)
        # salvaguarda determinista: el texto libre no puede recomendar ejercicios prohibidos
        if self._menciona(texto, prohibidos):
            return MSG_RESPUESTA_INSEGURA
        return texto
