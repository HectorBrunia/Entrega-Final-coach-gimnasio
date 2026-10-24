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
    PerfilParcial,
    PlanPropuesto,
    RespuestaConversacion,
)
from app.llm import LLMNoDisponible
from app.domain.equipo import EQUIPO_SIEMPRE_DISPONIBLE, describir_equipo, normalizar_equipo
from app.domain.modelos import (
    DiaRutina, Ejercicio, EjercicioPlanificado, Lesion, Perfil, PerfilBorrador, Rutina,
    nombre_dia_valido, repeticiones_validas,
)
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
# Cualquier copia del aviso (con o sin tildes, mayusculas o punto) que traiga un texto: el LLM
# lo copia del historial. Se quita antes de anadir el unico aviso final.
_AVISO_EXISTENTE = re.compile(
    r"[\s(\[¡«\"']*esto\s+no\s+es\s+un\s+diagn[oó]stico\s+m[eé]dico\s*[.!;,]?[ \t]*[)\]»\"']?\s*",
    re.IGNORECASE,
)

# Triaje de urgencia cardiaca en tres niveles (regla K). Todo sobre el mensaje ACTUAL
# normalizado (sin tildes ni mayusculas).
#  Nivel 1 (112 determinista, `detectar_dolor_pecho`): solo sintomas inequivocos, sin depender
#    del contexto y tolerantes a intensificadores entre palabras ("presion muy fuerte en el
#    pecho", "me cuesta mucho respirar").
#  Nivel 2 (112 por el LLM): campo estructurado `sintoma_cardiaco` con cita verificada en el
#    mensaje actual (red semantica para sinonimos que el lexico no cubre). Ver
#    `Nodos._dolor_del_mensaje`.
#  Nivel 3 (terminos ambiguos de entrenamiento, `termino_cardiaco_ambiguo`): "el corazon me
#    late rapido en el HIIT", "sin aliento, quiero mejorar mi fondo", "pecho cargado de
#    agujetas". Nunca dan 112 por si solos; pausan (plantilla generica) solo si hay ademas una
#    senal del lexico de dolor, o si el LLM los marca como sintoma (entonces nivel 2: 112).

# Zona toracica (tambien la usa es_zona_pecho para la zona que reporta el LLM).
_ZONA_PECHO = re.compile(
    r"\b(?:pecho|torax|toracic\w*|coraz\w*|estern\w*|costill\w*|torso|pectoral\w*)\b"
)
# Zona toracica para el nivel 1 (sin "pectoral": musculo; su dolor pausa como dolor agudo).
_ZONA_TORACICA_N1 = re.compile(r"^(?:pecho|torax|toracic\w*|coraz\w*|estern\w*|costill\w*|torso)$")
# Menciones de pecho como grupo muscular o ejercicio ("press de pecho", "rutina de pecho",
# "entrenar pecho"): se enmascaran antes de buscar la zona del sintoma.
_PECHO_EJERCICIO = re.compile(
    r"\b(?:press|aperturas?|flexiones|fondos|rutina|dia|ejercicios?|entrenar|entreno|maquina|"
    r"cruces|pullover|series?)(?: (?:de|para|en|inclinado|declinado|plano))* (?:el |los )?"
    r"(?:pecho|pectoral\w*|torax)\b"
)
# Sintomas que, cerca de la zona toracica (hasta 4 palabras entre medias), son 112.
_SINTOMA_TORACICO = re.compile(
    r"^(?:dol(?:or|ores|ia|io|iendo)|duel(?:e|en)|presion|presiona|oprim\w*|"
    r"opresi\w*|aprieta\w*|apretad[oa]s?|pesadez|pesad[oa]|ardor|ard(?:e|en|ia|io|iendo)|"
    r"quema(?:n|ba)?|quemazon|punzad\w*|punzante|pinchazo\w*|pinch(?:a|an|aba)|tirantez|nudo|"
    r"elefante)$"
)
# Palabras que no pueden quedar entre la zona y el sintoma (contexto de entrenamiento:
# "agarre apretado en el press de pecho").
_HUECO_PROHIBIDO = frozenset({
    "press", "banca", "aperturas", "apertura", "flexiones", "fondos", "rutina", "ejercicio",
    "ejercicios", "series", "serie", "kg", "agarre", "barra", "mancuernas", "maquina", "peso",
    "entreno", "entrenar", "repeticiones",
})
MAX_HUECO_SINTOMA = 4
# Dolor explicito con zona toracica en el mismo mensaje: 112 aunque este lejos ("me duele la
# espalda entre los omoplatos y el pecho"). Las palabras de dolor nunca se degradan.
_DOLOR_EXPLICITO = re.compile(r"\bdol(?:or|ores|i|io|ia|iendo|er)\b|\bduel(?:e|en)\b")
# Nivel 1 por si solos (inequivocos, sin depender del contexto).
PATRONES_URGENCIA: tuple[str, ...] = (
    r"\bme ahog\w*|\bahogo\b|\bahogando\b",   # me ahogo, siento ahogo
    r"\basfixi\w*",                            # me asfixio, asfixia
    r"\bno puedo respirar\b(?! bien)",         # no puedo respirar ("... bien": ver degradables)
    r"\bme cuesta (?:mucho |muchisimo |bastante |demasiado |un monton )?respirar\b",
    r"\b(?:respiro|respirar|respirando) con (?:mucha )?dificultad\b"
    r"|\bdificultad (?:para|al) respirar\b",  # respiro con dificultad
    r"\bno me entra (?:el )?aire\b",           # no me entra el aire
    r"\bsin respiracion\b",                    # me he quedado sin respiracion
    r"\bhiperventil\w*",                       # estoy hiperventilando
    r"\b(?:ataque|crisis) de asma\b",          # ataque de asma
    r"\bpalpitacion\w*",                       # palpitaciones
    r"\btaquicardi\w*|\barritmi\w*",           # taquicardia, arritmia
    r"\bdesmay\w*",                            # me desmayo, me voy a desmayar
    r"\bperd\w* (?:el )?conocimiento\b",       # perdi / he perdido el conocimiento
    r"\bdesvanec\w*|\bdesvanezc\w*",           # casi me desvanezco
    r"\bsud\w* frio\w*",                       # sudor frio, sudando frio, sudores frios
    r"\bopresi\w*",                            # opresion (casi siempre toracica)
    r"\belefante en el pecho\b",               # como un elefante en el pecho
    r"\b(?:siento|noto|tengo) (?:un |mucho |muchisimo |como un )?peso en el (?:pecho|torax)\b",
)
_PATRONES_URGENCIA = tuple(re.compile(p) for p in PATRONES_URGENCIA)
# Corazon con una cualidad anormal (no la frecuencia, que es nivel 3): nivel 1.
_CORAZON = re.compile(r"\bcoraz\w*|\bpulso\b")
_CORAZON_ANORMAL = re.compile(
    r"\bdesboc\w*|\ba saltos\b|\birregular\w*|\bdescontrolad\w*|\bse me (?:para|paro|sale|salia)\b"
    r"|\bun vuelco\b|\braro\b|\bextrano\b"
)
# Dificultad respiratoria que en una frase de tecnica o de mejorar la forma fisica es nivel 3
# ("me quedo sin aliento subiendo escaleras, quiero mejorar mi fondo"); si no, nivel 1.
PATRONES_RESPIRACION_DEGRADABLE: tuple[str, ...] = (
    r"\bme falta (?:mucho |muchisimo |un poco )?(?:el )?(?:aire|aliento)\b",
    r"\bfalta (?:de )?(?:aire|aliento)\b",
    r"\bsin aliento\b",
    r"\bno recupero (?:el )?aliento\b",
    r"\bme falta la respiracion\b",
    r"\bno puedo respirar bien\b",
    r"\brespiro mal\b|\bno respiro bien\b",
    r"\b(?:no puedo|me cuesta) coger (?:el )?aire\b",
)
_PATRONES_RESPIRACION_DEGRADABLE = tuple(re.compile(p) for p in PATRONES_RESPIRACION_DEGRADABLE)
# Contexto de tecnica o de mejorar la forma fisica (sin "reposo": "me falta el aire incluso en
# reposo" es una urgencia).
_CONTEXTO_ENTRENAMIENTO = re.compile(
    r"\bmejor(?:ar|o|e|ando)\b|\btecnica\b|\bfondo\b|\bresistencia\b|\bcardio\b"
    r"|\bhiit\b|\bseries?\b|\bzonas?\b"
)
# Nivel 3: terminos ambiguos de entrenamiento (nunca 112 por si solos).
_FRECUENCIA_CARDIACA = re.compile(
    r"\blat(?:e|en|ia|ir|iendo|ido|idos)\b|\bacelerad\w*|\bva a mil\b|\brapid\w*|\bpulsacion\w*"
)
_PECHO_CARGADO = re.compile(r"\b(?:pecho|torax) (?:muy )?cargado\b|\bcargado el pecho\b|\bagujetas\b")
# Brazo izquierdo dormido, con hormigueo o dolor: nivel 1.
_BRAZO_IZQUIERDO = re.compile(r"\bbrazo izquierdo\b")
_SENAL_BRAZO = re.compile(r"\bdorm\w*|\bduerm\w*|\badormec\w*|\bentumec\w*|\bhormigue\w*")

# Lexico de dolor (raices y frases, sobre texto normalizado: sin mayusculas ni tildes). Una
# coincidencia en el mensaje ACTUAL basta para pausar a revision humana, diga lo que diga el
# LLM. Criterio amplio a proposito: ante la duda, escalar. Reportar una lesion ("me lesione
# ...") NO es senal de dolor agudo: va por la ruta de lesiones (registro + bloqueo por zona).
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
    r"\bse me nubl\w*",           # se me nubla la vista (presincope: pausa generica; el LLM puede subirla a 112)
    r"\bveo (?:puntos negros|borroso|las estrellas|estrellas)\b",  # veo puntos negros
)
_PATRONES_DOLOR = tuple(re.compile(p) for p in PATRONES_DOLOR)

MAX_CANDIDATOS = 40
HISTORIAL_PROMPT = 6

MSG_SIN_PLAN_SEGURO = (
    "No puedo generar un plan seguro con tus lesiones actuales. Te recomiendo consultar "
    "a un profesional (médico, fisioterapeuta o entrenador certificado) antes de continuar."
)
MSG_FALLO_PLAN = "No pude generar un plan en este momento. Inténtalo de nuevo en unos minutos."
# Spec 7: solo el camino programador -> seguridad entrega rutinas. Si el texto libre de la
# sintesis parece una prescripcion, se sustituye por uno de estos mensajes fijos.
MSG_PIDE_RUTINA = (
    "Las rutinas te las preparo solo con ejercicios de mi catálogo y revisadas por mi filtro "
    "de seguridad. Si quieres un plan, escríbeme \"dame una rutina\" y te lo armo."
)
MSG_PLAN_TRAS_PERFIL = (
    "Te prepararé el plan en cuanto tenga tu perfil completo (objetivo, días disponibles, "
    "equipo y nivel), con ejercicios de mi catálogo revisados por mi filtro de seguridad."
)

# Datos del perfil, en el orden en que se piden: (campo, etiqueta para el usuario, ayuda).
CAMPOS_PERFIL: tuple[tuple[str, str, str], ...] = (
    ("objetivo", "objetivo", "p. ej. fuerza, hipertrofia o perder grasa"),
    ("dias_disponibles", "días disponibles", "cuántos días por semana puedes entrenar"),
    ("equipo", "equipo", "p. ej. barra, mancuernas, máquinas, poleas o peso corporal"),
    ("nivel", "nivel", "principiante, intermedio o avanzado"),
)

# Senales de que un texto libre prescribe entrenamiento (sobre cada linea normalizada: sin
# tildes ni mayusculas). Criterio amplio a proposito: los falsos positivos se aceptan (el texto
# se sustituye por un mensaje fijo); es la primera de dos redes independientes (la otra es la
# marca `contiene_ejercicios` de la salida estructurada del LLM).
_NUM = r"(?:\d+|una?|uno|dos|tres|cuatro|cinco|seis|siete|ocho|nueve|diez|doce|quince|veinte)"
_DIAS_SEMANA = (r"(?:lunes|martes|miercoles|jueves|viernes|sabado|domingo|"
                r"monday|tuesday|wednesday|thursday|friday|saturday|sunday)")
_PRESCRIPCION = re.compile(
    r"\b\d+\s*[x×]\s*\d+"                                    # 4x10, 3 x 8, 1920x1080
    r"|(?:^|[\s,;(])[x×]\s*\d+\b"                            # sentadilla x10
    rf"|\b{_NUM}\s*(?:series|sets?|rondas?|vueltas?|circuitos?)\b"  # 4 series, 3 sets
    r"|\b\d+\s*veces\s*\d+"                                  # 3 veces 45 segundos
    r"|\b(?:repeticion(?:es)?|reps?|repes?|sets?|series de|rondas? de|vueltas? de|circuitos?"
    r"|amrap|emom|tabata)\b"
    r"|\b\d+(?:[.,]\d+)?\s*(?:kg|kilos?|lbs?|libras)\b"      # 60 kg
    r"|%\s*(?:de\s*)?(?:tu\s*)?1?\s*rm\b|\brpe\s*\d|\brir\s*\d"
    r"|\|.*\b(?:series|ejercicios?|carga|descanso)\b.*\|"    # tabla markdown
)
_ENCABEZADO_DIA = re.compile(
    r"^[\W_]*(?:(?:dia|day|sesion|session|semana|week|bloque|entreno|workout)\s*"
    r"(?:\d+|[a-f]|uno|dos|tres|cuatro|cinco|primer[oa]?|segund[oa]|tercer[oa]?)\b"
    rf"|{_DIAS_SEMANA}\b\s*(?:[:\-–(]|[\W_]*$))"
)
# Vineta: 1-4 simbolos (guion, asterisco, emoji, ✅...) o un numero con punto/parentesis.
_VINETA = re.compile(r"^\s*(?:[^\w\s]{1,4}|\d+\s*[.)-])\s*\w")
_LISTA_EN_LINEA = re.compile(r"(?:^|\s)\d+\s*[.)]\s+\w")
_EJERCICIOS = (
    r"(?:press|sentadill\w*|squat\w*|peso muerto|deadlift\w*|remo\w*|rows?|dominad\w*|"
    r"pull ?ups?|chin ?ups?|jalon\w*|curl\w*|extension\w*|zancad\w*|lunges?|hip thrust\w*|"
    r"fondos|dips?|elevacion\w*|aperturas?|flexion\w*|push ?ups?|plancha\w*|planks?|prensa|"
    r"gemelos?|triceps|biceps|burpees?|crunch\w*|abdominal\w*|face ?pull|swing\w*|"
    r"thrusters?|kettlebells?|step ?ups?|bulgar\w*|goblet|romanian|rumano|puente de gluteo\w*|"
    r"glute bridge|cargada\w*|arranque|clean|snatch|box jumps?|saltos? al cajon|wall balls?|"
    r"mountain climbers?|escalador\w*|jumping jacks?|pullover|pec deck|hack|patada\w*)"
)
_NOMBRE_EJERCICIO = re.compile(rf"\b{_EJERCICIOS}\b")
_CARDIO = r"(?:cinta|bici\w*|eliptica|remo|comba|cardio|carrera|correr|nadar|natacion|spinning|escaladora)"
# Patrones de una sola linea sin necesitar nombre de ejercicio (ronda 2).
_PRESCRIPCION_EXTRA = re.compile(
    r"\btandas?\b"
    r"|\b\d+\s*por\s*\d+\b"                                     # 4 por 10
    r"|\b\d+\s*/\s*\d+\b"                                       # 4/8
    r"|\ba\s+\d+\s*-\s*\d+\b"                                   # a 8-10
    r"|\b\d+\s*(?:s|seg\w*|segundos?)\b.*\b(?:descans\w*|off|pausa|recupera\w*)\b"
    r"|\bon\b.*\boff\b"                                         # 30 s on / 30 s off
    rf"|\b\d+\s*min\w*\s+de\s+{_CARDIO}\b"                       # 10 minutos de cinta
    r"|(?:^|[\s.;,])(?:upper|lower|torso|pierna|piernas|empuje|tiron|push|pull|legs|full ?body"
    r"|cuerpo completo|tren superior|tren inferior)\s*:"           # Upper: / Empuje:
    r"|\b(?:primer[ao]?|segund[ao]|tercer[ao]?|cuart[ao])\s+(?:sesion|dia|semana|entreno|rutina)\s*:"
)
# Patrones que solo cuentan si la linea nombra un ejercicio.
_PRESCRIPCION_CON_EJERCICIO = re.compile(
    rf"\b{_NUM}\s+{_EJERCICIOS}\b"                                # 50 flexiones
    r"|\b\d+\s+de\s+\d+\b"                                       # 5 de 5
    r"|\b(?:sube|subir|baja|bajar|pon|usa|carga|mete)\s+(?:a\s+|unos?\s+|hasta\s+)?\d+(?:[.,]\d+)?\b"
    r"|\b(?:haz|hazlo|realiza|recomiendo|sugiero|prueba|incluye|anade|agrega|prioriza)\b"
)
# Indicacion o calendario junto a varios ejercicios en prosa ("haz sentadilla y press...").
_INDICACION = re.compile(
    r"\b(?:haz|hazlo|haga|realiza|incluye|anade|agrega|empieza|comienza|prueba|alterna|combina|"
    r"recomiendo|propongo|sugiero|sugerencia|te dejo|idea|manana|deberias|puedes hacer|"
    r"por semana|primer dia|segundo dia|para (?:gluteos?|pecho|espalda|piernas?|hombros?|"
    r"brazos|biceps|triceps|core|abdomen)|"
    rf"{_DIAS_SEMANA})\b"
)
MIN_VINETAS_EJERCICIO = 2
MIN_EJERCICIOS_EN_PROSA = 2

MSG_RESPUESTA_INSEGURA = (
    "Prefiero no responder a eso con recomendaciones concretas porque podrían no ser seguras "
    "con tus lesiones o molestias actuales. Si quieres, puedo armarte una rutina validada."
)

# Plantillas fijas por motivo de la pausa HITL (sin LLM). "otro" cubre escalado_supervisor y
# cualquier motivo futuro: nunca se afirma dolor agudo si no se detecto.
MOTIVO_DOLOR = "dolor_agudo"
MOTIVO_PECHO = "dolor_pecho"
MOTIVO_ZONA = "zona_sin_regla"

# No afirma lo que dijo el usuario: el 112 tambien salta por el LLM (nivel 2) o por sintomas
# que no son dolor (falta de aire, desmayo, palpitaciones).
_URGENCIA = (
    "Lo que describes puede ser un síntoma que requiere atención médica urgente. Si tienes "
    "dolor u opresión en el pecho, dificultad para respirar o te sientes a punto de desmayarte, "
    "llama al 112 ahora. No sigas entrenando."
)

_PAUSA = {
    MOTIVO_PECHO: f"Conversación pausada para revisión humana. {_URGENCIA}",
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
        "Tu consulta fue revisada. " + _URGENCIA.replace("{", "{{")
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


def _palabras_sin_ejercicio(texto_norm: str) -> list[str]:
    """Palabras del mensaje con las menciones de pecho como ejercicio enmascaradas."""
    return re.sub(r"[^\w\s]", " ", _PECHO_EJERCICIO.sub(" ejercicio ", texto_norm)).split()


def _sintoma_cerca_de_zona(palabras: list[str]) -> bool:
    """Zona toracica y un sintoma toracico a <= MAX_HUECO_SINTOMA palabras (en cualquier orden),
    sin palabras de entrenamiento entre medias."""
    for i, palabra in enumerate(palabras):
        if not _ZONA_TORACICA_N1.match(palabra):
            continue
        inicio = max(0, i - MAX_HUECO_SINTOMA - 1)
        fin = min(len(palabras), i + MAX_HUECO_SINTOMA + 2)
        for j in range(inicio, fin):
            if j == i or not _SINTOMA_TORACICO.match(palabras[j]):
                continue
            if not _HUECO_PROHIBIDO.intersection(palabras[min(i, j) + 1:max(i, j)]):
                return True
    return False


def _respiracion_grave(texto_norm: str) -> bool:
    """Dificultad respiratoria degradable: nivel 1 salvo en una frase de tecnica o forma fisica."""
    return any(p.search(texto_norm) for p in _PATRONES_RESPIRACION_DEGRADABLE) and not (
        _CONTEXTO_ENTRENAMIENTO.search(texto_norm)
    )


def detectar_dolor_pecho(mensaje: str) -> bool:
    """Nivel 1 del triaje (112 determinista): sintoma toracico o cardiaco inequivoco en el
    mensaje actual. True si hay:
    - una urgencia por si sola: ahogo, asfixia, no puedo respirar, me cuesta (mucho) respirar,
      respiro con dificultad, no me entra el aire, palpitaciones, taquicardia, desmayo, perdida
      de conocimiento, sudor frio, opresion, peso en el pecho...;
    - falta de aire o aliento fuera de una frase de tecnica o de mejorar la forma fisica;
    - brazo izquierdo dormido, con hormigueo o dolor;
    - corazon con una cualidad anormal (desbocado, a saltos, irregular, se me para / sale);
    - zona toracica con dolor explicito en el mensaje, o con un sintoma toracico (presion,
      pesadez, ardor, punzada, aprieta...) cerca, aunque haya intensificadores entre medias.
    Los terminos ambiguos de entrenamiento (frecuencia cardiaca, sin aliento al mejorar el
    fondo, pecho cargado) no cuentan: son nivel 3. El pecho como ejercicio ("press de pecho")
    no es zona del sintoma."""
    texto = _normalizar(mensaje)
    if any(p.search(texto) for p in _PATRONES_URGENCIA) or _respiracion_grave(texto):
        return True
    if _BRAZO_IZQUIERDO.search(texto) and (_SENAL_BRAZO.search(texto) or _senal_lexico(texto)):
        return True
    if _CORAZON.search(texto) and _CORAZON_ANORMAL.search(texto):
        return True
    palabras = _palabras_sin_ejercicio(texto)
    if any(_ZONA_TORACICA_N1.match(p) for p in palabras) and _DOLOR_EXPLICITO.search(" ".join(palabras)):
        return True
    return _sintoma_cerca_de_zona(palabras)


def termino_cardiaco_ambiguo(mensaje: str) -> bool:
    """Nivel 3: terminos de entrenamiento que pueden sonar a sintoma (frecuencia cardiaca, falta
    de aliento en una frase de tecnica o forma fisica, pecho cargado / agujetas). Nunca dan 112
    por si solos; solo pausan si hay ademas una senal del lexico de dolor."""
    texto = _normalizar(mensaje)
    corazon = bool(_CORAZON.search(texto) and _FRECUENCIA_CARDIACA.search(texto))
    respiracion = any(p.search(texto) for p in _PATRONES_RESPIRACION_DEGRADABLE)
    return corazon or respiracion or bool(_PECHO_CARGADO.search(texto))


def detectar_dolor_agudo(mensaje: str) -> bool:
    """Chequeo determinista: una senal del lexico de dolor (o la urgencia toracica) basta para
    escalar."""
    return _senal_lexico(_normalizar(mensaje)) or detectar_dolor_pecho(mensaje)


def es_zona_pecho(zona: str | None) -> bool:
    """Zona del dolor que reporta el LLM: toracica/cardiaca (o brazo izquierdo)."""
    if not zona:
        return False
    texto = _normalizar(zona)
    return bool(_ZONA_PECHO.search(texto) or _BRAZO_IZQUIERDO.search(texto))


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
    """Anade el aviso medico exactamente una vez, al final (quita las copias que ya traiga)."""
    def _quitar(m: re.Match) -> str:
        return "\n\n" if "\n" in m.group(0) else " "

    limpio = _AVISO_EXISTENTE.sub(_quitar, texto)
    limpio = re.sub(r"[ \t]+([.,;:!?)\]])", r"\1", limpio)  # sin espacio antes de puntuacion
    limpio = re.sub(r"[ \t]{2,}", " ", limpio)
    limpio = re.sub(r"[ \t]*\n[ \t]*", "\n", limpio)
    limpio = re.sub(r"\n{3,}", "\n\n", limpio).strip()
    return f"{limpio}\n\n{AVISO_MEDICO}"


def parece_prescripcion(texto: str) -> bool:
    """Guarda determinista sobre el texto libre: True si parece un plan o una prescripcion
    (series x repeticiones, "repeticiones"/"reps"/"series de", encabezados "Día 1"/"Day 1"
    o 3+ lineas de lista que nombran ejercicios). Criterio amplio a proposito: ante la duda,
    el texto se sustituye por un mensaje fijo."""
    lineas = [_normalizar(l) for l in texto.splitlines()]
    if any(_PRESCRIPCION.search(l) or _PRESCRIPCION_EXTRA.search(l) or _ENCABEZADO_DIA.search(l)
           for l in lineas):
        return True
    if any(_PRESCRIPCION_CON_EJERCICIO.search(l) and _NOMBRE_EJERCICIO.search(l) for l in lineas):
        return True
    if any(len(_LISTA_EN_LINEA.findall(l)) >= 2 and _NOMBRE_EJERCICIO.search(l) for l in lineas):
        return True  # 1. Bulgaras 2. Goblet 3. Romanian
    vinetas = [l for l in lineas if _VINETA.match(l) and _NOMBRE_EJERCICIO.search(l)]
    if len(vinetas) >= MIN_VINETAS_EJERCICIO:
        return True
    todo = " ".join(lineas)
    nombres = {m.group(0) for m in _NOMBRE_EJERCICIO.finditer(todo)}
    return len(nombres) >= MIN_EJERCICIOS_EN_PROSA and bool(_INDICACION.search(todo))


_PREFIJO_GUIA_LIBRE = re.compile(r"^gu[ií]a[\s:_-]*", re.IGNORECASE)


def normalizar_fuentes(fuentes: list[str], guias: frozenset[str]) -> list[str]:
    """Lleva cada fuente citada por el LLM a una fuente canonica de guia ("guia:<nombre>") de
    las guias cargadas: canonica tal cual; id de trozo "<nombre>#<seccion>" -> su guia; nombre
    suelto ("progresion", "guia progresion") -> su guia. Lo que no corresponde a ninguna guia
    real se descarta (y se registra). Sin duplicados, en orden."""
    resultado: list[str] = []
    for fuente in fuentes:
        bruto = (fuente or "").strip()
        nombre = bruto.split("#", 1)[0].strip()
        candidatos = [nombre, _PREFIJO_GUIA_LIBRE.sub("", nombre).strip()]
        canonica = next((f"guia:{c}" for c in candidatos if c and f"guia:{c}" in guias), None)
        if canonica is None:
            if bruto:
                logger.info("Fuente descartada (no es una guia cargada): %r", bruto[:100])
            continue
        if canonica not in resultado:
            resultado.append(canonica)
    return resultado


def _con_fuentes_canonicas(dias: list[DiaRutina], guias: frozenset[str]) -> list[DiaRutina]:
    """Dias del dominio (no los modelos de propuesta) con las fuentes normalizadas."""
    return [
        DiaRutina(nombre=d.nombre, ejercicios=[
            EjercicioPlanificado(**{**p.model_dump(), "fuentes": normalizar_fuentes(p.fuentes, guias)})
            for p in d.ejercicios
        ])
        for d in dias
    ]
MAX_OBJETIVO_MOSTRADO = 80


def objetivo_mostrable(objetivo: str) -> str:
    """Objetivo (texto extraido por el LLM) acotado para mostrarlo: una linea, como mucho
    MAX_OBJETIVO_MOSTRADO caracteres y nunca con forma de prescripcion."""
    texto = " ".join(objetivo.split())[:MAX_OBJETIVO_MOSTRADO]
    return texto if texto and not parece_prescripcion(texto) else "el que me indicaste"


def explicacion_plan(perfil: Perfil, dias: int, entrenos: int | None = None) -> str:
    """Explicacion fija de la rutina, solo con datos que controla el sistema: el perfil, los
    dias del plan y, si viene del agente de progreso, cuantos entrenos se consideraron."""
    lineas = [
        f"Plan de {dias} día{'s' if dias != 1 else ''} para tu objetivo "
        f"({objetivo_mostrable(perfil.objetivo)}), nivel {perfil.nivel.value}, con ejercicios "
        "de mi catálogo revisados por mi filtro de seguridad."
    ]
    if entrenos is not None:
        lineas.append(
            f"Ajusté la progresión según tus {entrenos} entrenos registrados más recientes."
            if entrenos else
            "Aún no tienes entrenos registrados: la progresión parte de tu rutina actual."
        )
    return " ".join(lineas)


def texto_perfil_incompleto(borrador: PerfilBorrador | None) -> str:
    """Plantilla fija (sin LLM) para un perfil incompleto: lo que ya se sabe y lo que falta."""
    datos = {k: v for k, v in (borrador or PerfilBorrador()) if v not in (None, [], "")}
    if "equipo" in datos:
        datos["equipo"] = describir_equipo(datos["equipo"])
    if "nivel" in datos:
        datos["nivel"] = datos["nivel"].value
    if "objetivo" in datos:
        datos["objetivo"] = objetivo_mostrable(datos["objetivo"])
    sabidos = [f"- {etiqueta}: {datos[campo]}" for campo, etiqueta, _ in CAMPOS_PERFIL if campo in datos]
    faltan = [f"- {etiqueta} ({ayuda})" for campo, etiqueta, ayuda in CAMPOS_PERFIL if campo not in datos]
    lineas = ["Para prepararte una rutina segura necesito completar tu perfil."]
    if sabidos:
        lineas += ["", "Lo que ya sé:", *sabidos]
    lineas += ["", "Me falta saber:", *faltan, "",
               "Cuando me lo digas, te preparo la rutina con ejercicios de mi catálogo."]
    return "\n".join(lineas)


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
        fuentes_guia: frozenset[str] = frozenset(),
    ):
        self.repo = repo
        # fuentes canonicas ("guia:<nombre>") de las guias cargadas: las unicas citables
        self.fuentes_guia = frozenset(fuentes_guia)
        self.catalogo = catalogo
        # zona -> ids bloqueados, precalculado una vez: el filtro en cada turno son busquedas
        # en conjuntos y no bloquea el event loop
        self.indice = indice or indice_bloqueo(catalogo)
        self.llm = llm
        self.buscador = buscador
        self._analizar = llm.with_structured_output(AnalisisMensaje)
        self._decidir = llm.with_structured_output(DecisionSupervisor)
        self._planificar = llm.with_structured_output(PlanPropuesto)
        self._responder = llm.with_structured_output(RespuestaConversacion)

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
        # borrador del onboarding (Postgres): solo mientras no hay perfil completo
        borrador = None if perfil else await self.repo.obtener_perfil_borrador(uid)
        rutina = await self.repo.rutina_actual(uid)
        previas = await self.repo.lesiones_activas(uid)
        dolor_por_palabra = detectar_dolor_agudo(mensaje)

        analisis: AnalisisMensaje | None = None
        try:
            analisis = await self._analizar.ainvoke(
                self._prompt_evaluador(estado, perfil, previas, borrador=borrador))
        except Exception:
            # sin LLM (429 agotado u otro fallo) no se puede analizar, pero el dolor agudo
            # detectado por palabra clave no puede perderse: se escala igual a humano
            if not dolor_por_palabra:
                raise
            logger.warning("Fallo el LLM del evaluador; se escala a humano por palabra clave de dolor")
        analisis = analisis or AnalisisMensaje()

        perfil, borrador, completado = await self._actualizar_perfil(uid, perfil, borrador, analisis)
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
            "perfil_borrador": borrador,
            "perfil_completado": completado,
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
        # nivel 2 del triaje: sintoma cardiaco marcado por el LLM con cita verificada -> 112
        llm_cardiaco = analisis.sintoma_cardiaco and cita_en_mensaje(analisis.cita_sintoma, mensaje)
        if analisis.sintoma_cardiaco and not llm_cardiaco:
            logger.info(
                "Sintoma cardiaco marcado por el LLM sin cita en el mensaje actual: se ignora "
                "(cita=%r)", analisis.cita_sintoma,
            )
        if termino_cardiaco_ambiguo(mensaje) and not (llm_cardiaco or detectar_dolor_pecho(mensaje)):
            # nivel 3: termino ambiguo de entrenamiento; nunca 112 por si solo (pausa generica
            # solo si hay senal de dolor o dolor del LLM con cita)
            logger.info("Termino cardiaco ambiguo sin sintoma confirmado: sin urgencia 112")
        if not (por_lexico or llm_valido or llm_cardiaco):
            return False, None, False
        ejercicio = self._resolver_ejercicio(analisis.ejercicio_con_dolor) or self._ejercicio_en_texto(
            mensaje
        )
        # urgencia toracica: por el detector determinista sobre el mensaje, o por el LLM con cita
        # verificada cuya zona es el pecho (o cuya cita ya es toracica)
        pecho = detectar_dolor_pecho(mensaje) or llm_cardiaco or (
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
        self, estado: EstadoCoach, perfil: Perfil | None, lesiones: list[Lesion] | None = None,
        borrador: PerfilBorrador | None = None,
    ) -> list[BaseMessage]:
        zonas = ", ".join([*sorted(REGLAS_LESION), *ZONAS_GENERICAS, ZONA_OTRA])
        registradas = ", ".join(sorted({l.zona for l in lesiones or []})) or "ninguna"
        sistema = (
            "Eres el evaluador de un coach de gimnasio. Datos de perfil (objetivo, "
            "dias_disponibles 1-7, equipo, nivel): en 'perfil' van SOLO los que el usuario da en "
            "el ultimo mensaje (sustituyen a los guardados); en 'perfil_historial' los que dio "
            "en mensajes anteriores del historial (solo completan datos que falten, nunca "
            "sustituyen a los guardados). Del ultimo mensaje del usuario extrae SOLO: lesiones "
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
            "sintoma_cardiaco es true solo si el ultimo mensaje describe un sintoma propio, "
            "actual o reciente, que puede ser una urgencia cardiaca o respiratoria: dolor, "
            "presion, pesadez u opresion en el pecho; falta de aire o ahogo anormal; corazon "
            "desbocado, irregular o que late sin motivo; desmayo o sensacion de ir a desmayarse; "
            "sudor frio; dolor que se irradia al brazo izquierdo, cuello o mandibula. Es false "
            "para la charla de entrenamiento: zonas o frecuencia cardiaca, pulso en reposo, "
            "corazon acelerado normal por el ejercicio, tecnica de respiracion, mejorar el fondo "
            "o la resistencia, agujetas o pecho cargado por el entreno, ejercicios de pecho. Si es "
            "true, copia en cita_sintoma el fragmento literal del ultimo mensaje que lo describe. "
            "Deja vacio lo que no se mencione. "
            f"Perfil actual: {perfil.model_dump_json() if perfil else 'ninguno'}. "
            "Perfil en construccion (datos ya guardados): "
            f"{borrador.model_dump_json(exclude_none=True) if borrador else 'ninguno'}."
        )
        return [SystemMessage(content=sistema), *self._historial(estado), HumanMessage(content=estado["mensaje"])]

    @staticmethod
    def _cambios_perfil(parcial: PerfilParcial | None) -> dict:
        """Datos de perfil de una salida del evaluador, limpios. El equipo se normaliza al
        vocabulario del catalogo; si queda vacio (todo desconocido) cuenta como dato que falta."""
        if parcial is None:
            return {}
        cambios = {k: v for k, v in parcial if v is not None}
        if "equipo" in cambios:
            equipo = normalizar_equipo(cambios["equipo"])
            if equipo:
                cambios["equipo"] = equipo
            else:
                del cambios["equipo"]
        if "objetivo" in cambios and not cambios["objetivo"].strip():
            del cambios["objetivo"]
        return cambios

    async def _actualizar_perfil(
        self, uid: UUID, perfil: Perfil | None, borrador: PerfilBorrador | None,
        analisis: AnalisisMensaje,
    ) -> tuple[Perfil | None, PerfilBorrador | None, bool]:
        """Perfil incremental. Devuelve (perfil, borrador, completado_en_este_turno).

        Con perfil completo, los datos nuevos lo actualizan. Sin el, se fusionan con el
        borrador persistido en Postgres (los posteriores sustituyen a los anteriores): si el
        resultado valida como `Perfil` se guarda (y el repositorio borra el borrador en la
        misma transaccion); si no, se guarda el borrador ampliado, que sobrevive a reinicios
        del proceso y del hilo.
        """
        # Precedencia: mensaje actual > guardado > historial (el historial solo rellena huecos).
        actuales = self._cambios_perfil(analisis.perfil)
        del_historial = self._cambios_perfil(analisis.perfil_historial)
        if perfil is not None:
            if not actuales:
                return perfil, None, False
            try:
                nuevo = Perfil.model_validate({**perfil.model_dump(), **actuales})
            except ValueError:
                return perfil, None, False
            if nuevo != perfil:  # sin cambios reales no se reescribe
                await self.repo.guardar_perfil(nuevo)
            return nuevo, None, False

        previos = {k: v for k, v in (borrador or PerfilBorrador()) if v is not None}
        datos = {**del_historial, **previos, **actuales}
        if datos == previos:
            return None, borrador, False
        try:
            nuevo = Perfil.model_validate({"usuario_id": uid, **datos})
        except ValueError:
            nuevo = None  # incompleto: se guarda el borrador y se pide el resto
        if nuevo is None or not nuevo.equipo:
            nuevo_borrador = PerfilBorrador.model_validate(datos)
            await self.repo.guardar_perfil_borrador(uid, nuevo_borrador)
            return None, nuevo_borrador, False
        await self.repo.guardar_perfil(nuevo)
        return nuevo, None, True

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
        if (destino == "sintesis" and estado.get("perfil_completado")
                and estado.get("rutina") is None):
            # el usuario acaba de terminar el onboarding y aun no tiene rutina: se programa en
            # este mismo turno, venga de donde venga la sintesis (sintesis o seguridad sin rutina)
            destino = "programador"
        return {"siguiente": destino}

    def _prompt_supervisor(self, estado: EstadoCoach) -> list[BaseMessage]:
        sistema = (
            "Eres el supervisor de un coach de gimnasio. Elige el siguiente paso:\n"
            "- programador: el usuario pide una rutina nueva o cambiarla.\n"
            "- progreso: el usuario quiere ajustar la rutina segun sus entrenos registrados.\n"
            "- seguridad: el usuario quiere ver o revisar su rutina actual.\n"
            "- sintesis: preguntas generales, saludos, datos que faltan o temas fuera de alcance.\n"
            "- hitl: el usuario describe una situacion medica que requiere revision humana.\n"
            f"Perfil: {'completo' if estado.get('perfil') else 'incompleto'}"
            f"{' (completado en este mensaje)' if estado.get('perfil_completado') else ''}. "
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
        return await self._proponer(estado, contexto_extra=contexto, entrenos=len(historial))

    async def _proponer(
        self, estado: EstadoCoach, contexto_extra: str, entrenos: int | None = None
    ) -> dict:
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
        try:
            plan = await self._planificar.ainvoke(
                self._prompt_programador(estado, perfil, candidatos, documentos, previos, contexto_extra)
            )
        except ValueError:
            # propuesta con forma invalida (ValidationError / OutputParserException): el plan se
            # rechaza y nunca se muestra; el turno responde MSG_FALLO_PLAN
            logger.warning("Propuesta del programador invalida: se rechaza", exc_info=True)
            plan = None
        rutina = Rutina(
            usuario_id=estado["usuario_id"], version=1,
            dias=_con_fuentes_canonicas(plan.dias, self.fuentes_guia),
        ) if plan else None
        if not _tiene_ejercicios(rutina):
            return {**base, "rutina": None, "fallo_plan": True}
        return {**base, "rutina": rutina, "rutina_nueva": True, "plan_validado": False,
                # explicacion determinista (spec 7): nunca texto libre del LLM junto a la rutina
                "explicacion": explicacion_plan(perfil, len(rutina.dias), entrenos),
                "volumen": self._volumen(rutina)}

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
            "En 'fuentes' de cada ejercicio cita las guias usadas, solo con estas fuentes: "
            f"{', '.join(sorted(self.fuentes_guia)) or 'ninguna'}.\n"
            "Cada 'repeticiones' es un numero o un rango N-M (p. ej. 8 o 8-10). Cada 'nombre' "
            "de dia es corto (maximo 40 caracteres, una linea), p. ej. 'Día 1 - Torso', sin "
            "series, cargas ni indicaciones.\n"
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
        elif estado.get("perfil") is None:
            # sin perfil completo no hay LLM de texto libre: plantilla fija con lo que falta
            texto = texto_perfil_incompleto(estado.get("perfil_borrador"))
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
        for n, dia in enumerate(rutina.dias, 1):
            # los campos que se muestran tal cual se sanean (rutinas guardadas antes de validar)
            lineas.append(f"\n{dia.nombre if nombre_dia_valido(dia.nombre) else f'Día {n}'}")
            for p in dia.ejercicios:
                dosis = (f"{p.series} x {p.repeticiones}" if repeticiones_validas(p.repeticiones)
                         else f"{p.series} series")
                lineas.append(f"- {self._nombre(p.ejercicio_id)}: {dosis}, descanso {p.descanso_seg} s")
                # solo fuentes canonicas de guias cargadas
                fuentes.extend(f for f in normalizar_fuentes(p.fuentes, self.fuentes_guia)
                               if f not in fuentes)
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

    def _prompt_conversar(self, estado: EstadoCoach, prohibidos: set[str]) -> list[BaseMessage]:
        lesiones = estado.get("lesiones") or []
        perfil = estado.get("perfil")
        sistema = (
            "Eres un coach de gimnasio. Responde en español, breve y sin inventar. Si la pregunta "
            "esta fuera del entrenamiento, rechaza con cortesia. Si falta el perfil, pide objetivo, "
            "dias disponibles, equipo y nivel. No des diagnosticos medicos ni anadas avisos "
            "medicos: el sistema los anade.\n"
            "Nunca prescribas ejercicios, series, repeticiones, cargas, rutinas ni planes de "
            "entrenamiento, ni siquiera de ejemplo: las rutinas solo las genera el programador "
            "validado. Si el usuario quiere un plan, dile que lo pida escribiendo \"dame una "
            "rutina\".\n"
            "En 'texto' va la respuesta. 'contiene_ejercicios' es true si el texto recomienda o "
            "prescribe ejercicios concretos, series, repeticiones, cargas o una rutina; si no, "
            "false.\n"
            f"Perfil: {perfil.model_dump_json() if perfil else 'incompleto'}.\n"
            f"Lesiones activas: {', '.join(l.zona for l in lesiones) or 'ninguna'}.\n"
            f"Nunca recomiendes: {', '.join(sorted(prohibidos)) or 'nada en particular'}."
        )
        return [SystemMessage(content=sistema), *self._historial(estado),
                HumanMessage(content=estado["mensaje"])]

    async def _conversar(self, estado: EstadoCoach) -> str:
        lesiones = estado.get("lesiones") or []
        excluidos = estado.get("ejercicios_excluidos") or []
        try:
            prohibidos = self._prohibidos(lesiones, excluidos)
        except ZonaLesionDesconocida:
            return MSG_RESPUESTA_INSEGURA
        fijo = MSG_PIDE_RUTINA if estado.get("perfil") else MSG_PLAN_TRAS_PERFIL
        try:
            respuesta = await self._responder.ainvoke(self._prompt_conversar(estado, prohibidos))
        except LLMNoDisponible:
            raise  # caida del proveedor: la API responde 503 (no se entrega ningun texto)
        except Exception:
            # salida estructurada invalida u otro fallo: falla cerrado con el mensaje fijo
            logger.exception("Fallo la salida estructurada de la conversacion; mensaje fijo")
            return fijo
        if respuesta is None:
            return fijo
        texto = respuesta.texto
        # salvaguardas: el texto libre no puede recomendar ejercicios prohibidos ni entregar un
        # plan (solo programador -> seguridad entrega rutinas, spec 7). Dos redes independientes:
        # la marca del LLM y la expresion regular determinista; basta con una.
        if self._menciona(texto, prohibidos):
            return MSG_RESPUESTA_INSEGURA
        if respuesta.contiene_ejercicios or parece_prescripcion(texto):
            logger.warning("Texto libre de la sintesis con ejercicios o forma de plan: se sustituye")
            return fijo
        return texto
