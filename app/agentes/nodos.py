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
    ZONA_OTRA,
    ZONAS_GENERICAS,
    AnalisisMensaje,
    DecisionSupervisor,
    EstadoCoach,
    LesionReportada,
    PlanPropuesto,
)
from app.domain.equipo import EQUIPO_SIEMPRE_DISPONIBLE
from app.domain.modelos import DiaRutina, Ejercicio, Lesion, Perfil, Rutina
from app.herramientas.esquemas import EntradaVolumen
from app.herramientas.funciones import (
    EjercicioDesconocido,
    consultar_historial,
    validar_plan,
    volumen_semanal,
)
from app.persistencia.repositorios import RepositorioDominio
from app.rag.ingesta import Documento
from app.rag.recuperador import FiltrosBusqueda
from app.safety.reglas import (
    REGLAS_LESION,
    IndiceBloqueo,
    ZonaLesionDesconocida,
    filtrar_por_lesiones,
    ids_bloqueados,
    indice_bloqueo,
)

logger = logging.getLogger(__name__)

Buscador = Callable[[str, FiltrosBusqueda], Awaitable[list[Documento]]]

AVISO_MEDICO = "Esto no es un diagnóstico médico."

# Lexico de dolor (raices y frases, sobre texto normalizado: sin mayusculas ni tildes). Una
# coincidencia en el mensaje ACTUAL basta para pausar a revision humana, diga lo que diga el
# LLM. Criterio amplio a proposito: ante la duda, escalar. Reportar una lesion ("me lesione
# ...") NO es senal de dolor agudo: va por la ruta de lesiones (registro + bloqueo por zona).
# Urgencia toracica (motivo dolor_pecho: plantilla fija con 112 y atencion medica inmediata).
# 1) Dificultad para respirar, por si sola:
PATRONES_RESPIRACION: tuple[str, ...] = (
    r"\bme ahog\w*",                          # me ahogo, me ahogaba
    r"\bno puedo respirar\b",                 # no puedo respirar (bien)
    r"\bme cuesta respirar\b",                # me cuesta respirar
    r"\bme falta el aire\b",                  # me falta el aire
    r"\bfalta (?:de )?aire\b",                # falta de aire
)
_PATRONES_RESPIRACION = tuple(re.compile(p) for p in PATRONES_RESPIRACION)
# 2) Zona toracica mencionada junto con cualquiera de estas senales (en el mismo mensaje):
_ZONA_PECHO = re.compile(r"\b(?:pecho|torax|toracic\w*)\b")
PATRONES_SENAL_PECHO: tuple[str, ...] = (
    r"\bdol(?:or|i|e)\w*|\bduel(?:e|en)\b",   # dolor, me duele
    r"\bpresi\w*",                            # presion en el pecho
    r"\bopresi\w*",                           # opresion
    r"\boprim\w*",                            # se me oprime
    r"\bapriet\w*|\baprieta\w*",              # me aprieta, apretado
    r"\bard(?:e|en|er|or|ia|io|iendo|ido|ida)\w*",  # arde, ardor
    r"\bpinch\w*",                            # pincha, pinchazo
    r"\bpunz\w*",                             # punzada
    r"\bpeso en\b",                           # peso en el pecho
)
_PATRONES_SENAL_PECHO = tuple(re.compile(p) for p in PATRONES_SENAL_PECHO)

PATRONES_DOLOR: tuple[str, ...] = (
    r"\bdol(?:or|i|e)\w*",        # dolor, dolores, dolia, dolio, doliendo, doler (no "dolar")
    r"\bduel(?:e|en|a|an)\b",     # duele, duelen (no "duelo")
    r"\badolor\w*",               # adolorido
    r"\bmolest\w*",               # molestia, me molesta (falso positivo aceptado: "te molesta si")
    r"\btiron\w*",                # tiron, tirones
    r"\bme (?:tira|tiran|tiraba|esta tirando)\b",  # me tira el gemelo (no "tirar mas peso")
    r"\bpinch\w*",                # pinchazo, pincha
    r"\bard(?:e|en|er|or|ia|io|iendo|ido|ida)\w*",  # arde, ardor, ardiendo (no "ardilla")
    r"\bpunz\w*",                 # punzada, punzante
    r"\bcalambre\w*",             # calambre(s)
    r"\blastim\w*",               # me lastime
    r"\bhormigue\w*",             # hormigueo
    r"\bme (?:quema|queman|quemaba)\b",  # me quema el hombro (no "quemar grasa")
    r"\bquemazon\w*",             # quemazon
    r"\binflam\w*",               # se me inflamo, inflamacion (no "antiinflamatorio")
    r"\bhinch\w*",                # hinchada, hinchazon
    r"\btorc[ie]\w*",             # me torci, torcido, torcedura
    r"\besguin\w*",               # esguince, me esguince
    r"\bdesgarr\w*",              # desgarro, me desgarre
    r"\blux[ao]\w*",              # luxacion, se me luxo
    r"\bdislo(?:c|qu)\w*",        # dislocacion, me disloque
    r"\bse me (?:ha )?salido\b|\bse me salio\b",  # se me salio el hombro
    r"\bfractur\w*",              # fractura
    r"\brompi\w*",                # me rompi (no "rotacion")
    r"\bse (?:me )?(?:ha )?(?:rompio|roto)\b",    # algo se rompio
    r"\bchasquid\w*",             # chasquido
    r"\bcruj\w*",                 # crujio, crujido
    r"\bresent\w*|\bresient\w*",  # me resenti, me resiente
    r"\blatigazo\w*",             # latigazo
    r"\bescuec\w*|\bescoc\w*",    # me escuece
    r"\bsensacion (?:rara|extrana)\b",  # sensacion rara en el hombro
    r"\bme fastidia\w*",          # me fastidia la rodilla
    r"\bme (?:jodi|he jodido)\b", # me jodi la espalda
    r"\bmare(?:o|os|e|ado|ada|ando)\b",  # mareo, me maree (senal de alarma)
    r"\bentumec\w*",              # entumecido
    r"\bse me (?:ha )?bloquea(?:do)?\b|\bse me bloqueo\b",  # se me bloqueo la espalda
    r"\bme (?:esta|estan) matando\b",  # la rodilla me esta matando
    r"\bme hice dano\b",          # me hice dano
    r"\bno (?:me )?puedo (?:mover|levantar|apoyar|doblar|estirar|agachar|girar)\w*",
    r"\bse me (?:durmio|duerme|duermen|durmieron)\b",  # se me durmio la mano
    r"\bopresi\w*",               # opresion (en cualquier zona)
    r"\bme ca(?:i|igo|ido)\b|\bme he caido\b",  # me cai, me he caido
    r"\bsangr(?:a|an|ando|ado|o)\b",  # me sangra (no "sangre")
    r"\bme (?:ha )?cedi(?:o|do)\b",   # me cedio el hombro
    r"\bme falla(?:n|ba)? (?:la|el|las|los) (?:rodilla|tobillo|hombro|espalda|muneca|codo|"
    r"cadera|pierna|brazo|rodillas|tobillos|hombros)s?\b",  # me falla la rodilla (no "la tecnica")
    r"\b(?:me )?he roto\b",       # me he roto el dedo
    r"\bretorc[ie]\w*",           # me retorci el tobillo
    r"\bhecho polvo\b",           # me he hecho polvo la rodilla (tambien cansancio: fallo seguro)
    r"\bfatal de (?:la|el|las|los|mi|mis)\b",  # fatal de la rodilla
)
_PATRONES_DOLOR = tuple(re.compile(p) for p in PATRONES_DOLOR)

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

# Plantillas fijas por motivo de la pausa HITL (sin LLM). "otro" cubre escalado_supervisor y
# cualquier motivo futuro: nunca se afirma dolor agudo si no se detecto.
MOTIVO_DOLOR = "dolor_agudo"
MOTIVO_PECHO = "dolor_pecho"
MOTIVO_ZONA = "zona_sin_regla"

_URGENCIA = (
    "Busca atención médica inmediata: llama a emergencias (112) o acude a urgencias. "
    "No sigas entrenando."
)

_PAUSA = {
    MOTIVO_PECHO: (
        f"Conversación pausada para revisión humana: reportaste dolor u opresión en el pecho. "
        f"{_URGENCIA}"
    ),
    MOTIVO_DOLOR: (
        "Conversación pausada para revisión humana: reportaste dolor agudo. Detén ese "
        "ejercicio y consulta a un profesional de la salud."
    ),
    MOTIVO_ZONA: (
        "Conversación pausada para revisión humana: registraste una lesión en una zona que no "
        "puedo evaluar de forma segura. No entrenes esa zona y consulta a un profesional de la salud."
    ),
    "otro": (
        "Conversación pausada para revisión humana. Mientras tanto, si tienes dudas sobre tu "
        "estado de salud, consulta a un profesional."
    ),
}

_TRAS_REVISION = {
    MOTIVO_PECHO: (
        "Reportaste dolor u opresión en el pecho{sobre}. " + _URGENCIA.replace("{", "{{")
        + " Un profesional de la salud debe valorarte antes de volver a entrenar."
    ),
    MOTIVO_DOLOR: (
        "Reportaste dolor agudo{sobre}. Detén el ejercicio y consulta a un profesional "
        "(médico o fisioterapeuta) antes de continuar. No voy a recomendarte más ese ejercicio."
    ),
    MOTIVO_ZONA: (
        "Registraste una lesión en una zona que no puedo evaluar de forma segura. "
        "Antes de seguir entrenando, consulta a un profesional (médico o fisioterapeuta)."
    ),
    "otro": (
        "Tu consulta fue revisada. Por precaución, antes de seguir entrenando consulta a un "
        "profesional (médico o fisioterapeuta) sobre lo que describiste."
    ),
}


def _normalizar(texto: str) -> str:
    sin_tildes = unicodedata.normalize("NFKD", texto)
    sin_tildes = "".join(c for c in sin_tildes if not unicodedata.combining(c))
    return " ".join(sin_tildes.lower().replace("_", " ").split())


def _senal_lexico(texto_norm: str) -> bool:
    return any(p.search(texto_norm) for p in _PATRONES_DOLOR)


def detectar_dolor_pecho(mensaje: str) -> bool:
    """Urgencia toracica: dificultad para respirar, o pecho/torax junto con una senal de dolor,
    presion u opresion (o cualquier senal del lexico) en el mismo mensaje. Fallo seguro: el
    dolor puede estar en otra zona del mensaje ("flexiones de pecho... me arden los brazos")."""
    texto = _normalizar(mensaje)
    if any(p.search(texto) for p in _PATRONES_RESPIRACION):
        return True
    if not _ZONA_PECHO.search(texto):
        return False
    return any(p.search(texto) for p in _PATRONES_SENAL_PECHO) or _senal_lexico(texto)


def detectar_dolor_agudo(mensaje: str) -> bool:
    """Chequeo determinista: una senal del lexico de dolor (o la urgencia toracica) basta para
    escalar."""
    return _senal_lexico(_normalizar(mensaje)) or detectar_dolor_pecho(mensaje)


def es_zona_pecho(zona: str | None) -> bool:
    return bool(zona) and _ZONA_PECHO.search(_normalizar(zona)) is not None


CITA_MIN_PALABRAS = 2
CITA_MIN_CARACTERES = 8


def cita_en_mensaje(cita: str | None, mensaje: str) -> bool:
    """La cita del LLM (al menos 2 palabras y 8 caracteres tras normalizar) aparece
    literalmente, como palabras completas, en el mensaje actual."""
    cita_norm = " ".join(re.sub(r"[^\w\s]", " ", _normalizar(cita or "")).split())
    texto = " ".join(re.sub(r"[^\w\s]", " ", _normalizar(mensaje)).split())
    if len(cita_norm.split()) < CITA_MIN_PALABRAS or len(cita_norm) < CITA_MIN_CARACTERES:
        return False
    return _contiene(texto, cita_norm)


def _slug(texto: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", _normalizar(texto)).strip("_")


def expandir_lesion(reportada: LesionReportada) -> list[Lesion]:
    """Zona reportada -> lesiones a guardar. Sin lado -> ambos lados; "otra" -> zona sin regla
    ("otra_<descripcion>"), que falla cerrado (HITL) como cualquier zona desconocida."""
    datos = {"severidad": reportada.severidad, "activa": reportada.activa}
    if reportada.zona in ZONAS_GENERICAS:
        return [Lesion(zona=z, **datos) for z in ZONAS_GENERICAS[reportada.zona]]
    if reportada.zona == ZONA_OTRA:
        detalle = _slug(reportada.descripcion or "")
        return [Lesion(zona=f"{ZONA_OTRA}_{detalle}" if detalle else ZONA_OTRA, **datos)]
    return [Lesion(zona=reportada.zona, **datos)]


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


def texto_pausa(motivo: str | None) -> str:
    """Mensaje al usuario mientras la conversacion espera la revision humana."""
    return _con_aviso(_PAUSA.get(motivo or "", _PAUSA["otro"]))


def texto_tras_revision(motivo: str | None, sobre: str = "") -> str:
    plantilla = _TRAS_REVISION.get(motivo or "", _TRAS_REVISION["otro"])
    return _con_aviso(plantilla.format(sobre=sobre))


def _tiene_ejercicios(rutina: Rutina | None) -> bool:
    return rutina is not None and any(d.ejercicios for d in rutina.dias)


class Nodos:
    def __init__(
        self,
        repo: RepositorioDominio,
        catalogo: dict[str, Ejercicio],
        llm: BaseChatModel,
        buscador: Buscador,
        indice: IndiceBloqueo | None = None,
    ):
        self.repo = repo
        self.catalogo = catalogo
        # zona -> ids bloqueados, precalculado una vez: el filtro en cada turno son busquedas
        # en conjuntos y no bloquea el event loop
        self.indice = indice or indice_bloqueo(catalogo)
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
        return set(ids_bloqueados(lesiones, self.indice)) | set(excluidos)

    def _nombre(self, ejercicio_id: str) -> str:
        ej = self.catalogo.get(ejercicio_id)
        return ej.nombre if ej else ejercicio_id

    async def _guardar_sin(self, uid: UUID, rutina: Rutina, quitar: set[str]) -> Rutina | None:
        """Guarda una version de `rutina` sin `quitar` y devuelve la vigente.

        Idempotente: si no hay nada que quitar no guarda. Nunca guarda una rutina vacia: si
        quedaria sin ejercicios devuelve None y no guarda (la vigente insegura no se sirve:
        seguridad la rehace y GET /rutinas/actual la rechaza).
        """
        if not set(quitar) & set(_ids_rutina(rutina)):
            return rutina
        depurada = _quitar_ejercicios(rutina, set(quitar))
        if not _tiene_ejercicios(depurada):
            return None
        await self.repo.guardar_rutina(depurada)
        return await self.repo.rutina_actual(uid)

    async def _excluidos(self, estado: EstadoCoach) -> list[str]:
        """Ejercicios excluidos por dolor. Fuente de verdad: el repositorio (Postgres); la lista
        del checkpoint es solo una cache del turno y se une por si acaso."""
        persistidos = await self.repo.exclusiones_activas(estado["usuario_id"])
        return list(dict.fromkeys([*persistidos, *(estado.get("ejercicios_excluidos") or [])]))

    @staticmethod
    def _historial(estado: EstadoCoach) -> list[BaseMessage]:
        return list(estado.get("mensajes") or [])[-HISTORIAL_PROMPT:]

    # --- evaluador --------------------------------------------------------------

    async def evaluador(self, estado: EstadoCoach) -> dict:
        uid: UUID = estado["usuario_id"]
        mensaje = estado["mensaje"]
        perfil = await self.repo.obtener_perfil(uid)
        rutina = await self.repo.rutina_actual(uid)
        previas = await self.repo.lesiones_activas(uid)
        dolor_por_palabra = detectar_dolor_agudo(mensaje)

        analisis: AnalisisMensaje | None = None
        try:
            analisis = await self._analizar.ainvoke(self._prompt_evaluador(estado, perfil, previas))
        except Exception:
            # sin LLM (429 agotado u otro fallo) no se puede analizar, pero el dolor agudo
            # detectado por palabra clave no puede perderse: se escala igual a humano
            if not dolor_por_palabra:
                raise
            logger.warning("Fallo el LLM del evaluador; se escala a humano por palabra clave de dolor")
        analisis = analisis or AnalisisMensaje()

        perfil = await self._actualizar_perfil(uid, perfil, analisis)
        nuevas, cambios = await self._registrar_lesiones(uid, previas, analisis.lesiones_nuevas)
        lesiones = await self.repo.lesiones_activas(uid) if (nuevas or cambios) else previas
        lesion_nueva = any(l.activa for l in nuevas)

        # Lesion nueva: se retira YA de la rutina persistida lo que bloquean sus zonas conocidas,
        # antes de cualquier pausa HITL (que puede no reanudarse nunca). Las zonas sin regla no
        # se pueden depurar: se escalan a humano y GET /rutinas/actual responde 409 mientras tanto.
        retirados: list[str] = []
        if lesion_nueva and rutina is not None:
            quitar = ids_bloqueados(lesiones, self.indice, solo_conocidas=True)
            retirados = [i for i in _ids_rutina(rutina) if i in quitar]
            depurada = await self._guardar_sin(uid, rutina, set(retirados))
            if depurada is None:
                retirados = []  # no se guardo (quedaria vacia): seguridad la rechaza y se rehace
            else:
                rutina = depurada

        persistidos = await self.repo.exclusiones_activas(uid)
        excluidos = list(dict.fromkeys([*persistidos, *(estado.get("ejercicios_excluidos") or [])]))
        for heredado in (e for e in excluidos if e not in persistidos):
            # exclusion que solo vivia en un checkpoint anterior: pasa a ser dato de dominio
            await self.repo.agregar_exclusion(uid, heredado)
        dolor, ejercicio, pecho = self._dolor_del_mensaje(mensaje, analisis, dolor_por_palabra)
        if dolor:
            if ejercicio in self.catalogo:
                # dato de dominio: sobrevive a un reinicio del hilo (regla E)
                await self.repo.agregar_exclusion(uid, ejercicio)
                if ejercicio not in excluidos:
                    excluidos.append(ejercicio)
                # Se retira ya de la rutina persistida (antes de la pausa HITL), para que no
                # se siga sirviendo aunque la pausa nunca se reanude. Idempotente: si ya no
                # esta, no se guarda otra version. Sin ejercicio identificado no se toca.
                if rutina is not None:
                    rutina = await self._guardar_sin(uid, rutina, {ejercicio}) or rutina

        return {
            "perfil": perfil,
            "lesiones": lesiones,
            "rutina": rutina,
            "bloqueados": [],
            "intentos_seguridad": 0,
            "rutina_nueva": False,
            "plan_validado": False,
            "fallo_plan": False,
            "retirados": retirados,
            "volumen": None,
            "lesion_nueva": lesion_nueva,
            "requiere_humano": dolor,
            # dolor_pecho gana a cualquier otro motivo (las demas guardas no lo sobrescriben
            # porque requiere_humano ya esta activo)
            "motivo_humano": (MOTIVO_PECHO if pecho else MOTIVO_DOLOR) if dolor else None,
            "ejercicio_con_dolor": (ejercicio or analisis.ejercicio_con_dolor) if dolor else None,
            "ejercicios_excluidos": excluidos,
            "explicacion": "",
            "siguiente": None,
            "respuesta": None,
            "mensajes": [HumanMessage(content=mensaje)],
        }

    def _dolor_del_mensaje(
        self, mensaje: str, analisis: AnalisisMensaje, por_lexico: bool
    ) -> tuple[bool, str | None, bool]:
        """Decide de forma determinista si el mensaje ACTUAL reporta dolor que escala a humano.
        Devuelve (escala, ejercicio, es_urgencia_toracica).

        - senal del lexico de dolor en el mensaje actual: escala siempre, aunque el ejercicio ya
          este excluido (dolor renovado);
        - dolor marcado por el LLM: escala solo si su `cita_dolor` aparece en el mensaje actual
          (verificado aqui). Sin cita o con una cita que no esta en el mensaje, ese dolor viene
          del historial: no escala y se registra en el log.
        """
        llm_valido = analisis.dolor_agudo and cita_en_mensaje(analisis.cita_dolor, mensaje)
        if analisis.dolor_agudo and not llm_valido:
            logger.info(
                "Dolor marcado por el LLM sin cita en el mensaje actual (viene del historial): "
                "no se escala (cita=%r)", analisis.cita_dolor,
            )
        if not (por_lexico or llm_valido):
            return False, None, False
        ejercicio = self._resolver_ejercicio(analisis.ejercicio_con_dolor) or self._ejercicio_en_texto(
            mensaje
        )
        # urgencia toracica: por el detector determinista sobre el mensaje, o por el LLM con cita
        # verificada cuya zona es el pecho (o cuya cita ya es toracica)
        pecho = detectar_dolor_pecho(mensaje) or (
            llm_valido and (es_zona_pecho(analisis.zona_dolor)
                            or detectar_dolor_pecho(analisis.cita_dolor or ""))
        )
        return True, ejercicio, pecho

    async def _registrar_lesiones(
        self, uid: UUID, previas: list[Lesion], reportadas: list[LesionReportada]
    ) -> tuple[list[Lesion], list[Lesion]]:
        """Guarda las lesiones reportadas. Devuelve (nuevas, actualizadas).

        Una zona (normalizada) con una lesion activa no es nueva: no se inserta otra fila. Si
        la severidad cambia, se actualiza la existente (nunca se descarta en silencio).
        """
        activas = {_normalizar(l.zona): l for l in previas if l.activa}
        nuevas: list[Lesion] = []
        actualizadas: list[Lesion] = []
        for reportada in reportadas:
            for lesion in expandir_lesion(reportada):
                existente = activas.get(_normalizar(lesion.zona))
                if existente is None:
                    await self.repo.agregar_lesion(uid, lesion)
                    activas[_normalizar(lesion.zona)] = lesion
                    nuevas.append(lesion)
                elif lesion.activa and lesion.severidad != existente.severidad:
                    await self.repo.actualizar_severidad_lesion(uid, existente.zona, lesion.severidad)
                    logger.info("Lesion en %s: severidad %s -> %s", existente.zona,
                                existente.severidad, lesion.severidad)
                    existente = existente.model_copy(update={"severidad": lesion.severidad})
                    activas[_normalizar(lesion.zona)] = existente
                    actualizadas.append(existente)
                elif not lesion.activa:
                    logger.info("Lesion en %s reportada como no activa: se mantiene activa "
                                "(no se da de alta por el LLM)", existente.zona)
        return nuevas, actualizadas

    def _prompt_evaluador(
        self, estado: EstadoCoach, perfil: Perfil | None, lesiones: list[Lesion] | None = None
    ) -> list[BaseMessage]:
        zonas = ", ".join([*sorted(REGLAS_LESION), *ZONAS_GENERICAS, ZONA_OTRA])
        registradas = ", ".join(sorted({l.zona for l in lesiones or []})) or "ninguna"
        sistema = (
            "Eres el evaluador de un coach de gimnasio. Extrae SOLO del ultimo mensaje del "
            "usuario: datos de perfil (objetivo, dias_disponibles 1-7, equipo, nivel), lesiones "
            f"nuevas (zona, una de: {zonas}; usa hombro o rodilla si no dice el lado y otra, con "
            "descripcion, para cualquier otra zona), y si reporta dolor agudo "
            "o dolor que empeora durante un ejercicio (dolor_agudo) y en que ejercicio. "
            "Los mensajes anteriores son solo contexto: dolor_agudo, ejercicio_con_dolor, "
            "cita_dolor y lesiones_nuevas se extraen solo del ultimo mensaje. Si dolor_agudo es "
            "true, copia en cita_dolor el fragmento literal del ultimo mensaje donde reporta el "
            "dolor. Si el ultimo mensaje no reporta dolor, dolor_agudo es false aunque el "
            "historial lo mencione; si no reporta una lesion, lesiones_nuevas queda vacia. No "
            f"repitas lesiones ya registradas (zonas activas: {registradas}) salvo que cambie su "
            "severidad. "
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
            return {"siguiente": "hitl", "requiere_humano": True, "motivo_humano": MOTIVO_ZONA}
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

        excluidos = set(await self._excluidos(estado)) | set(previos)
        try:
            permitidos = filtrar_por_lesiones(
                list(self.catalogo.values()), estado.get("lesiones") or [], self.indice
            )
        except ZonaLesionDesconocida:
            return {**base, "requiere_humano": True, "motivo_humano": MOTIVO_ZONA}

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
        rutina = Rutina(usuario_id=estado["usuario_id"], version=1, dias=plan.dias) if plan else None
        if not _tiene_ejercicios(rutina):
            return {**base, "rutina": None, "fallo_plan": True}
        return {**base, "rutina": rutina, "rutina_nueva": True, "plan_validado": False,
                "explicacion": plan.explicacion, "volumen": self._volumen(rutina)}

    def _volumen(self, rutina: Rutina) -> dict[str, int] | None:
        """Series semanales por musculo primario (herramienta volumen_semanal, determinista)."""
        try:
            entrada = EntradaVolumen(rutina=rutina, catalogo=self.catalogo)
            return volumen_semanal(entrada).series_por_musculo
        except EjercicioDesconocido:
            return None  # id fuera del catalogo: seguridad bloquea el plan y se rehace

    @staticmethod
    def _candidatos(
        perfil: Perfil, permitidos: list[Ejercicio], excluidos: set[str], documentos: list[Documento]
    ) -> list[Ejercicio]:
        utiles = [e for e in permitidos if e.id not in excluidos]
        # Perfil.equipo ya esta en el vocabulario del catalogo (app.domain.equipo); el peso
        # corporal no necesita equipo. Sin equipo declarado no se filtra.
        equipo = set(perfil.equipo)
        if equipo:
            equipo.add(EQUIPO_SIEMPRE_DISPONIBLE)
        con_equipo = [e for e in utiles if not equipo or e.equipo in equipo] or utiles
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
        excluidos = await self._excluidos(estado)
        try:
            bloqueados = await self._bloqueados(rutina, lesiones, excluidos)
        except ZonaLesionDesconocida:
            return {"requiere_humano": True, "motivo_humano": MOTIVO_ZONA, "plan_validado": False}

        if bloqueados and not estado.get("rutina_nueva"):
            # Rutina ya persistida que deja de ser segura (p. ej. lesion nueva): se retiran
            # los ejercicios bloqueados de forma determinista y se guarda la nueva version.
            # Si no queda ningun ejercicio no se guarda una version vacia: se rehace el plan.
            depurada = _quitar_ejercicios(rutina, set(bloqueados))
            if _tiene_ejercicios(depurada) and not await self._bloqueados(
                depurada, lesiones, excluidos
            ):
                await self.repo.guardar_rutina(depurada)
                actual = await self.repo.rutina_actual(estado["usuario_id"])
                return {"rutina": actual, "bloqueados": [], "plan_validado": True,
                        "rutina_nueva": False, "retirados": bloqueados}

        if bloqueados:
            return {"bloqueados": bloqueados, "plan_validado": False}

        if not _tiene_ejercicios(rutina):  # nunca se guarda ni se valida una rutina vacia
            return {"rutina": None, "bloqueados": [], "plan_validado": False, "fallo_plan": True}
        if estado.get("rutina_nueva"):
            await self.repo.guardar_rutina(rutina)
            rutina = await self.repo.rutina_actual(estado["usuario_id"])
        return {"rutina": rutina, "bloqueados": [], "plan_validado": True, "rutina_nueva": False}

    async def _bloqueados(self, rutina: Rutina, lesiones: list[Lesion], excluidos: list[str]) -> list[str]:
        bloqueados = await validar_plan(rutina, lesiones, self.catalogo, self.indice)
        extra = [i for i in _ids_rutina(rutina) if i in excluidos and i not in bloqueados]
        return bloqueados + extra

    # --- HITL ---------------------------------------------------------------------

    async def hitl(self, estado: EstadoCoach) -> dict:
        motivo = estado.get("motivo_humano") or MOTIVO_DOLOR
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
        if rutina is not None:
            # defensa en profundidad: ademas de los excluidos por dolor, lo que bloquean las
            # lesiones activas con regla (idempotente; nunca deja una version vacia)
            quitar = set(await self._excluidos(estado)) | ids_bloqueados(
                estado.get("lesiones") or [], self.indice, solo_conocidas=True
            )
            rutina = await self._guardar_sin(uid, rutina, quitar) or rutina

        sobre = f" con {self._nombre(ejercicio)}" if ejercicio in self.catalogo else ""
        texto = texto_tras_revision(motivo, sobre)
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
            if _tiene_ejercicios(estado["rutina"]):
                texto = self._formatear_rutina(estado)
            else:  # nunca se muestra una rutina vacia como "Tu rutina"
                texto = MSG_SIN_PLAN_SEGURO
                cambios["rutina"] = None
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
        volumen = estado.get("volumen")
        if volumen:
            resumen = ", ".join(
                f"{musculo} {series}"
                for musculo, series in sorted(volumen.items(), key=lambda kv: (-kv[1], kv[0]))
            )
            lineas.append(f"\nVolumen semanal (series por músculo principal): {resumen}.")
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
