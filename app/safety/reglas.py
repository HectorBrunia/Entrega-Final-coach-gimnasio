"""Contraindicaciones deterministas por zona de lesion (spec 7).

Cada zona tiene una `ReglaZona` que bloquea por atributos del catalogo real (free-exercise-db):
musculos primarios o secundarios, patrones en el id o el nombre, e ids concretos.
Criterio conservador: ante la duda, bloquear. Estas reglas las revisa el usuario
(ver docs/revision/bloqueos-por-zona.md, generado con scripts/generar_revision_bloqueos.py).
"""

import re
from dataclasses import dataclass, field

from pydantic import BaseModel

from app.domain.modelos import Ejercicio, Lesion


@dataclass(frozen=True)
class ReglaZona:
    musculos: frozenset[str] = field(default_factory=frozenset)
    patrones_nombre: tuple[str, ...] = ()
    ids_extra: frozenset[str] = field(default_factory=frozenset)


# Los patrones se comparan sin mayusculas y sin separadores (ver `_compactar`), como subcadena
# del id o del nombre: "upright row" bloquea "Upright_Row", "Upright-Row" y "Cable Upright Rows".

_HOMBRO = ReglaZona(
    musculos=frozenset({
        "shoulders",         # deltoides: la articulacion lesionada trabaja directamente
        "chest",             # pectoral: mueve el hombro (aduccion horizontal, rotacion interna)
        "lats",              # dorsal: mueve el hombro desde flexion completa (jalones, dominadas)
        "traps",             # trapecio: carga la cintura escapular (encogimientos, remos altos)
        "middle back",       # romboides/escapula: remos y retracciones con el hombro cargado
    }),
    patrones_nombre=(
        "overhead",          # carga por encima de la cabeza: compresion subacromial
        "military",          # press militar: empuje vertical con barra
        "shoulder press",    # press de hombro en cualquier variante
        "push press",        # press con impulso por encima de la cabeza
        "arnold",            # press Arnold: rotacion interna con carga vertical
        "upright row",       # remo al menton: rotacion interna con abduccion (pinzamiento)
        "behind the neck",   # tras nuca: rotacion externa extrema bajo carga
        "behind neck",       # variante de nombre del tras nuca
        "behind the head",   # extensiones tras la cabeza: flexion completa de hombro cargada
        "behind the back",   # agarre por detras: extension de hombro forzada
        "dip",               # fondos: extension de hombro extrema con todo el peso corporal
        "handstand",         # apoyo invertido: hombro soporta todo el peso
        "snatch",            # arrancada: recepcion por encima de la cabeza
        "jerk",              # envion: recepcion por encima de la cabeza
        "clean",             # cargada: recepcion en rack con impacto en hombro y muneca
        "thruster",          # sentadilla + press por encima de la cabeza
        "squat",             # sentadillas: barra en la espalda o en rack fuerza la rotacion externa
        "good morning",      # buenos dias: barra en la espalda (rotacion externa forzada)
        "barbell lunge",     # zancada con barra en la espalda
        "barbell walking lunge",  # zancada caminando con barra en la espalda
        "barbell step",      # subida al cajon con barra en la espalda
        "barbell side",      # side bend / side split con barra en la espalda
        "deadlift",          # peso muerto: traccion pesada sobre la articulacion colgando
        "rack pull",        # tiron desde soportes: traccion pesada sobre el hombro
        "farmer",            # paseo del granjero: traccion sostenida sobre el hombro
        "rickshaw",          # strongman: traccion pesada sobre el hombro
        "yoke",              # strongman: yugo sobre hombros y trapecios
        "pull up",           # dominadas: colgado con el hombro en flexion completa
        "pullup",            # variante de nombre sin separador
        "chin up",           # dominadas supinas: misma carga que pull up
        "chinup",            # variante de nombre sin separador
        "chins",             # variantes de dominadas (sternum chins, side to side chins)
        "grip chin",         # dominadas de agarre mixto ("chin" a secas casaria con "machine")
        "gorilla chin",      # dominada con crunch colgado
        "muscle up",         # transicion sobre la barra: alto riesgo de hombro
        "pulldown",          # jalon: traccion desde flexion completa del hombro
        "pullover",          # pullover: flexion de hombro cargada en rango extremo
        "hang",              # colgado de la barra (hanging, one handed hang) y cargadas colgantes
        "row",               # remos: traccion horizontal con el hombro cargado
        "raise",             # elevaciones (laterales, frontales, posteriores): palanca larga
        "bench press",       # press de banca: hombro anterior en rango extremo
        "floor press",       # press en suelo: empuje horizontal cargado
        "chest press",       # press de pecho en maquina o cable
        "push up",           # flexiones: carga de hombro con el peso corporal
        "pushup",            # variante de nombre sin separador
        "body up",           # body-up: apoyo en plancha con extension de codo
        "body tricep",       # press de triceps con peso corporal en apoyo
        "triceps extension",  # extensiones de triceps: la cabeza larga cruza el hombro
        "tricep extension",  # variante de nombre en singular
        "triceps press",     # press de triceps tumbado: flexion de hombro cargada
        "tricep press",      # variante de nombre en singular
        "skull",             # rompecraneos: hombro en flexion con carga
        "kickback",          # patada de triceps: extension de hombro sostenida
        "fly",               # aperturas: palanca larga sobre el hombro en abduccion horizontal
        "flye",              # variante de nombre de aperturas
        "crossover",         # cruces de cable: aduccion horizontal con palanca larga
        "iron cross",        # cruz de hierro: abduccion con palanca maxima
        "crucifix",          # sujecion con brazos extendidos (strongman)
        "rotation",          # rotaciones interna/externa: carga directa sobre el manguito
        "windmill",          # molino: carga sostenida por encima de la cabeza
        "get up",            # turkish get up: carga por encima de la cabeza en transicion
        "getup",             # variante de nombre sin separador
        "halo",              # halo con kettlebell: circunduccion cargada alrededor de la cabeza
        "throw",             # lanzamientos: aceleracion balistica del brazo
        "slam",              # balon al suelo: movimiento balistico por encima de la cabeza
        "swing",             # swing con kettlebell: hombro frena la carga balistica
        "pike",              # pike / apoyos invertidos parciales
        "plank",             # plancha: hombro estabiliza el peso corporal
        "crawl",             # gateos (bear crawl, spider crawl): apoyo sobre las manos
        "rope",              # cuerdas de batalla / trepa: carga repetitiva y balistica
        "log lift",          # strongman: tronco hasta por encima de la cabeza
        "atlas stone",       # strongman: carga de piedra con hombros en riesgo
        "renegade",          # remo renegado: apoyo en plancha sobre mancuernas
        "london bridge",     # colgado de cuerda: traccion con el hombro en flexion
        "sled",              # trineo: empuje/arrastre/remo con los brazos
        "jammer",            # landmine jammer: empuje explosivo con el brazo
        "landmine",          # landmine: press/rotacion con el brazo cargado
        "incline dumbbell curl",  # curl inclinado: hiperextension de hombro bajo carga
        "incline hammer",    # curl martillo inclinado: misma posicion de hiperextension
        "incline inner",     # curl inclinado de biceps interno: misma posicion
        "drag curl",         # curl arrastrado: extension de hombro con carga
        "high cable curl",   # curl alto en polea: hombro abducido a 90 grados
        "high pulley",       # curl o remo en polea alta: hombro elevado
        "against wall",      # estiramientos contra la pared con el brazo en rango extremo
        "triceps stretch",   # estiramiento de triceps: flexion completa del hombro
        "tricep side stretch",  # estiramiento lateral de triceps: flexion completa del hombro
        "biceps stretch",    # estiramiento de biceps: extension forzada del hombro
        "around the world",  # circunduccion de hombro con carga
        "circles",           # circulos de brazo/hombro: movilidad del hombro lesionado
        "chest push",        # empuje explosivo del pecho
        "chest pass",        # pase de balon: empuje balistico
        "medicine ball",     # balon medicinal: lanzamientos y recepciones con el brazo
        "neck press",        # press al cuello: abduccion horizontal extrema
        "svend",             # press Svend: hombros en flexion sostenida
        "power partials",    # parciales explosivos de elevaciones
        "rack delivery",     # recepcion de la barra en rack
        "inchworm",          # gusano: caminar sobre las manos con el peso corporal
        "wind sprint",       # wind sprints: abdominales colgado de la barra
        "judo flip",         # rotacion explosiva tirando de un cable con los brazos
        "chain handle",      # extension con cadenas: carga variable sobre el hombro
    ),
)

_RODILLA = ReglaZona(
    musculos=frozenset({
        "quadriceps",        # cuadriceps: extiende la rodilla
        "hamstrings",        # isquios: flexionan la rodilla
        "calves",            # gemelos: cruzan la rodilla; elevaciones con la rodilla bloqueada
        "glutes",            # gluteos: casi siempre con la rodilla flexionada o en apoyo
        "adductors",         # aductores: maquina y desplazamientos laterales con palanca en la rodilla
        "abductors",         # abductores: maquina y bandas con palanca en la rodilla
    }),
    patrones_nombre=(
        "squat",             # sentadillas: flexion de rodilla cargada
        "lunge",             # zancadas: flexion de rodilla cargada y cizalla
        "jump",              # saltos: impacto en la recepcion
        "leg extension",     # extension de cuadriceps: cizalla en la rodilla
        "leg press",         # prensa: flexion de rodilla cargada
        "leg curl",          # curl femoral: flexion de rodilla cargada
        "step up",           # subidas al cajon: rodilla en carga unilateral
        "stepup",            # variante de nombre sin separador
        "pistol",            # sentadilla a una pierna: flexion profunda unilateral
        "split",             # sentadilla bulgara / split: rodilla en carga unilateral
        "hack",              # hack squat: flexion de rodilla cargada
        "sissy",             # sissy squat: cizalla extrema de rodilla
        "box",               # trabajo en cajon (saltos, subidas): impacto o carga
        "hops",              # saltitos: impacto repetido
        "bound",             # zancadas pliometricas: impacto unilateral
        "leap",              # saltos largos: impacto en la recepcion
        "hurdle",            # vallas: saltos con impacto
        "skip",              # skipping: impacto repetido
        "sprint",            # carrera rapida: alta carga articular
        "running",           # carrera: impacto repetido
        "jog",               # trote: impacto repetido
        "walk",              # caminatas con carga (yoke, monster walk, cinta)
        "carioca",           # desplazamiento lateral cruzado: torsion de rodilla
        "shuffle",           # desplazamientos laterales: cambios de direccion
        "skating",           # patinador: recepcion lateral sobre una pierna
        "cone",              # drills de conos: cambios de direccion
        "agility",           # agilidad: cambios de direccion bruscos
        "mountain climber",  # escaladores: flexion rapida de rodilla
        "burpee",            # burpees: sentadilla + salto
        "kneeling",          # de rodillas: apoyo directo sobre la rodilla
        "knee",              # cualquier ejercicio que menciona la rodilla
        "rollout",           # rueda abdominal: se hace de rodillas
        "ab roller",         # rueda abdominal: se hace de rodillas
        "fallout",           # fallout en suspension: variante de rueda, a menudo de rodillas
        "child's pose",      # postura del nino: flexion maxima de rodilla en apoyo
        "cat stretch",       # cuadrupedia: apoyo sobre las rodillas
        "all fours",         # cuadrupedia: apoyo sobre las rodillas
        "crawl",             # gateos: flexion y apoyo de rodilla
        "groiner",           # groiners: zancada dinamica profunda
        "stance",            # salidas desde posicion de tres apoyos: extension explosiva
        "wall sit",          # sentadilla isometrica en pared
        "clean",             # cargada: recepcion en sentadilla
        "snatch",            # arrancada: recepcion en sentadilla
        "jerk",              # envion: flexion y recepcion con impacto
        "thruster",          # sentadilla + press
        "deadlift",          # peso muerto: flexo-extension de rodilla cargada
        "sled",              # trineo: empuje con rodillas en carga
        "tire flip",         # volteo de neumatico: extension explosiva de rodilla
        "yoke",              # strongman: caminar con carga axial pesada
        "farmer",            # paseo del granjero: caminar con carga
        "stair",             # escaleras: flexion de rodilla repetida en carga
        "step mill",         # escalera mecanica: flexion de rodilla repetida
        "bicycl",            # bicicleta (bicycling): flexion repetida de rodilla
        "bike",              # bicicleta estatica: flexion repetida de rodilla
        "elliptical",        # eliptica: flexion repetida de rodilla
        "treadmill",         # cinta: impacto repetido
        "rowing",            # remo ergometro: flexion completa de rodilla
        "frog",              # postura de rana: rotacion y flexion de rodilla
        "rocket",            # saltos explosivos (rocket jump)
        "tuck",              # tuck jump / tucks: flexion maxima de rodilla
        "throw",             # lanzamientos con impulso de piernas (sentadilla + lanzamiento)
        "landmine",          # landmine 180 / jammer: pivote sobre los pies
        "wood chop",         # lenador: pivote del pie con rotacion
        "woodchop",          # variante de nombre sin separador
        "judo flip",         # rotacion explosiva pivotando sobre los pies
        "battling",          # cuerdas de batalla: semisentadilla sostenida
        "heavy bag",         # empuje del saco: impulso desde las piernas en zancada
        "chest push",        # empujes de balon desde rodillas o desde posicion de salida
        "quad",              # cualquier trabajo o estiramiento de cuadriceps
        "hamstring",         # cualquier trabajo o estiramiento de isquios
    ),
)

_LUMBAR = ReglaZona(
    musculos=frozenset({
        "lower back",        # erectores lumbares: la zona lesionada trabaja directamente
        "abdominals",        # abdominales: flexion/rotacion de tronco y antiextension lumbar
        "hamstrings",        # isquios: bisagra de cadera y tiran de la pelvis
        "glutes",            # gluteos: extension de cadera con la lumbar estabilizando
    }),
    patrones_nombre=(
        "deadlift",          # peso muerto: flexion lumbar bajo carga
        "good morning",      # buenos dias: flexion de cadera con carga sobre la columna
        "hyperextension",    # hiperextensiones: extension lumbar cargada
        "back extension",    # extension de espalda: extension lumbar cargada
        "bent over",         # remo inclinado: lumbar sostiene el torso en flexion
        "clean",             # cargada: extension explosiva con columna cargada
        "snatch",            # arrancada: extension explosiva con columna cargada
        "jerk",              # envion: carga axial explosiva
        "squat",             # sentadilla: carga axial sobre la columna
        "lunge",             # zancada con carga: carga axial
        "thruster",          # sentadilla + press: carga axial
        "leg press",         # prensa: retroversion pelvica y flexion lumbar al fondo
        "romanian",          # peso muerto rumano
        "stiff leg",         # peso muerto piernas rigidas
        "pull through",      # tiron entre las piernas: bisagra de cadera
        "rack pull",         # tiron desde soportes: carga lumbar
        "high pull",         # tiron alto: extension explosiva desde bisagra
        "swing",             # swing con kettlebell: bisagra balistica
        "pass between",      # pase de kettlebell entre las piernas: bisagra
        "figure 8",          # ocho con kettlebell: bisagra con rotacion
        "superman",          # superman: hiperextension lumbar
        "locust",            # langosta (yoga): hiperextension lumbar
        "row",               # remos: ante la duda, la mayoria cargan la lumbar
        "shrug",             # encogimientos pesados: carga axial
        "overhead",          # carga por encima de la cabeza: compresion axial
        "military",          # press militar de pie: carga axial
        "push press",        # press con impulso: carga axial explosiva
        "handstand",         # apoyo invertido: carga axial con riesgo de hiperextension
        "standing",          # de pie con carga: la lumbar estabiliza (press, curls, elevaciones)
        "powerlifting",      # press de banca con arco lumbar marcado
        "sit up",            # abdominales completos: flexion lumbar repetida
        "situp",             # variante de nombre sin separador
        "crunch",            # crunch: flexion lumbar repetida
        "v up",              # v-up: flexion lumbar balistica
        "jackknife",         # navaja: flexion lumbar balistica
        "leg raise",         # elevaciones de piernas: psoas tira de la lumbar
        "rollout",           # rueda abdominal: hiperextension lumbar
        "ab roller",         # rueda abdominal: hiperextension lumbar
        "fallout",           # fallout en suspension: antiextension extrema
        "twist",             # giros (russian twist): rotacion lumbar cargada
        "rotation",          # rotaciones de tronco cargadas
        "wood chop",         # lenador: rotacion cargada
        "woodchop",          # variante de nombre sin separador
        "windmill",          # molino: flexion lateral cargada
        "side bend",         # flexion lateral cargada
        "landmine",          # landmine: rotacion de tronco cargada
        "muscle up",         # muscle up con kipping: balanceo y extension lumbar brusca
        "kipping",           # kipping: hiperextension balistica
        "rope",              # trepa de cuerda / cuerdas de batalla / comba: impacto y traccion
        "atlas stone",       # strongman: flexion lumbar con carga
        "stone",             # cualquier levantamiento de piedra
        "log lift",          # strongman: carga desde el suelo
        "tire flip",         # volteo de neumatico: flexion lumbar cargada
        "yoke",              # strongman: carga axial pesada
        "farmer",            # paseo del granjero: carga axial
        "rickshaw",          # strongman: tiron desde el suelo
        "keg",               # strongman: levantamiento de barril desde el suelo
        "sandbag",           # saco: carga desde el suelo
        "sled",              # trineo: la lumbar estabiliza el empuje/arrastre
        "drag",              # arrastres con carga: la lumbar estabiliza
        "car driver",        # strongman: car drivers con carga y rotacion
        "throw",             # lanzamientos: rotacion/extension balistica
        "slam",              # balon al suelo: flexion lumbar balistica
        "chest push",        # empuje explosivo desde posicion de salida
        "stance",            # salidas desde posicion de tres apoyos: extension explosiva
        "heavy bag",         # empuje del saco: extension explosiva de tronco
        "rack delivery",     # recepcion de la barra con impacto axial
        "bridge",            # puentes: extension lumbar
        "hip thrust",        # empuje de cadera: extension lumbar cargada
        "pullover",          # pullover: arqueo lumbar
        "hanging",           # colgado: traccion y balanceo lumbar
        "jump",              # saltos: impacto axial en la recepcion
        "hops",              # saltitos: impacto axial repetido
        "bound",             # zancadas pliometricas: impacto axial
        "leap",              # saltos largos: impacto axial
        "skip",              # skipping: impacto repetido
        "sprint",            # carrera rapida: impacto y extension lumbar
        "running",           # carrera: impacto repetido
        "jog",               # trote: impacto repetido
        "skating",           # patinador: impacto lateral
        "mountain climber",  # escaladores: antiextension dinamica
        "burpee",            # burpees: flexion y extension rapidas
        "box",               # cajon: saltos y subidas con impacto
        "step up",           # subidas al cajon con carga axial
        "stepup",            # variante de nombre sin separador
        "bicycl",            # bicicleta: flexion lumbar sostenida
        "bike",              # bicicleta estatica / air bike: flexion lumbar sostenida
        "shoulder press",    # press de hombro: carga axial (de pie o sentado sin respaldo)
        "kettlebell",        # kettlebell: casi siempre parte de una cargada desde el suelo (bisagra)
        "seesaw",            # press alterno tipo balancin: de pie, con carga axial asimetrica
        "see saw",           # variante de nombre con separador (See-Saw Press)
        "para press",        # para press: cargada previa y press por encima de la cabeza
        "arnold",            # press Arnold: press por encima de la cabeza con carga axial
        "bradford",          # press Bradford/Rocky: barra recogida del suelo y por encima de la cabeza
        "cuban press",       # press cubano: termina con las mancuernas por encima de la cabeza
        "seated dumbbell press",  # press de hombro sentado: misma carga axial que shoulder press
        "dumbbell one arm triceps extension",  # extension de triceps por encima de la cabeza
        "seated triceps press",  # extension de triceps sentado por encima de la cabeza
        "anti gravity",      # anti-gravity press: la barra se recoge del suelo antes de presionar
        "jammer",            # landmine jammer: extension explosiva de todo el cuerpo
        "medicine ball",     # balon medicinal: lanzamientos con impulso de tronco
        "power partials",    # parciales explosivos de pie
        "calf raise",        # elevaciones de talones con carga axial (barra, smith)
        "donkey",            # donkey calf raise: carga apoyada sobre la zona lumbar
        "monster walk",      # paseo con banda en semisentadilla: lumbar en isometria
        "groiner",           # groiners: flexion de tronco dinamica
        "bench press",       # press de banca: arco lumbar e impulso de piernas
        "board press",       # variante de powerlifting con arco lumbar
        "pin press",         # variante de powerlifting con arco lumbar
        "push up",           # flexiones: plancha dinamica, riesgo de hundir la lumbar
        "pushup",            # variante de nombre sin separador
        "plyo",              # pliometria: impacto y extension lumbar brusca
        "drop push",         # flexiones con caida: impacto
        "hip flexor",        # estiramientos de flexor de cadera: hiperextension lumbar
        "iron crosses",      # estiramiento con rotacion lumbar
        "lying crossover",   # estiramiento con rotacion lumbar
        "looking at ceiling",  # estiramiento con hiperextension lumbar
        "back",              # cualquier ejercicio que menciona la espalda
    ),
)

# Zona exacta (normalizada) -> regla. Zona activa sin regla: falla cerrado (ZonaLesionDesconocida);
# el llamador escala a revision humana.
REGLAS_LESION: dict[str, ReglaZona] = {
    "hombro_derecho": _HOMBRO,
    "hombro_izquierdo": _HOMBRO,
    "rodilla_derecha": _RODILLA,
    "rodilla_izquierda": _RODILLA,
    "zona_lumbar": _LUMBAR,
}


class ZonaLesionDesconocida(Exception):
    """Lesion activa cuya zona no tiene regla: el filtro falla cerrado."""


class ReglasInvalidas(Exception):
    """Las reglas no encajan con el catalogo cargado: la app no debe arrancar."""


def _normalizar(zona: str) -> str:
    return zona.strip().lower()


def _compactar(texto: str) -> str:
    """Minusculas sin separadores: 'Upright-Row', 'upright_row' y 'Upright Row' -> 'uprightrow'."""
    return re.sub(r"[^a-z0-9]+", "", texto.lower())


def motivos_bloqueo(ejercicio: Ejercicio, regla: ReglaZona) -> list[str]:
    """Motivos por los que la regla bloquea el ejercicio (vacio si no lo bloquea)."""
    motivos: list[str] = []
    if ejercicio.id in regla.ids_extra:
        motivos.append("id extra")
    musculos_regla = {_normalizar(m) for m in regla.musculos}
    musculos_ej = [ejercicio.musculo_primario, *ejercicio.musculos_secundarios]
    for m in dict.fromkeys(_normalizar(m) for m in musculos_ej):
        if m in musculos_regla:
            motivos.append(f"músculo: {m}")
    textos = (_compactar(ejercicio.id), _compactar(ejercicio.nombre))
    for patron in regla.patrones_nombre:
        p = _compactar(patron)
        if any(p in t for t in textos):
            motivos.append(f"patrón: {patron}")
    return motivos


def ejercicio_bloqueado(ejercicio: Ejercicio, regla: ReglaZona) -> bool:
    return bool(motivos_bloqueo(ejercicio, regla))


def _reglas_normalizadas() -> dict[str, ReglaZona]:
    return {_normalizar(k): v for k, v in REGLAS_LESION.items()}


def validar_reglas_contra_catalogo(catalogo: dict[str, Ejercicio]) -> None:
    """Lanza ReglasInvalidas si una regla nombra ids o musculos que no estan en el catalogo,
    tiene un patron vacio, o si una zona no bloquea ningun ejercicio (reglas desalineadas)."""
    vocabulario = {
        _normalizar(m)
        for e in catalogo.values()
        for m in (e.musculo_primario, *e.musculos_secundarios)
    }
    errores: list[str] = []
    for zona, regla in _reglas_normalizadas().items():
        if any(not _compactar(p) for p in regla.patrones_nombre):
            errores.append(f"zona {zona!r}: patrón vacío")
        ids_faltantes = sorted(regla.ids_extra - catalogo.keys())
        if ids_faltantes:
            errores.append(f"zona {zona!r}: ids_extra fuera del catálogo: {ids_faltantes}")
        musculos_faltantes = sorted(m for m in regla.musculos if _normalizar(m) not in vocabulario)
        if musculos_faltantes:
            errores.append(f"zona {zona!r}: músculos fuera del catálogo: {musculos_faltantes}")
        if not any(ejercicio_bloqueado(e, regla) for e in catalogo.values()):
            errores.append(f"zona {zona!r}: no bloquea ningún ejercicio del catálogo")
    if errores:
        raise ReglasInvalidas("Reglas de seguridad inválidas: " + "; ".join(errores))


class FiltroResultado(BaseModel):
    permitidos: list[Ejercicio]
    bloqueados: list[tuple[str, str]]  # (ejercicio_id, zona)


def filtrar_por_lesiones(ejercicios: list[Ejercicio], lesiones: list[Lesion]) -> FiltroResultado:
    reglas = _reglas_normalizadas()
    zonas = list(dict.fromkeys(_normalizar(les.zona) for les in lesiones if les.activa))
    for z in zonas:
        if z not in reglas:
            raise ZonaLesionDesconocida(f"Zona de lesion sin regla de seguridad: {z!r}")
    permitidos: list[Ejercicio] = []
    bloqueados: list[tuple[str, str]] = []
    for ej in ejercicios:
        zonas_bloqueantes = [z for z in zonas if ejercicio_bloqueado(ej, reglas[z])]
        if zonas_bloqueantes:
            bloqueados.extend((ej.id, z) for z in zonas_bloqueantes)
        else:
            permitidos.append(ej)
    return FiltroResultado(permitidos=permitidos, bloqueados=bloqueados)
