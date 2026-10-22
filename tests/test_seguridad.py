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


def test_zona_desconocida_no_bloquea_y_no_falla():
    res = filtrar_por_lesiones([_ej("press_militar")],
                               [Lesion(zona="hombro", severidad="grave", activa=True)])
    assert len(res.permitidos) == 1 and res.bloqueados == []


def test_dos_lesiones_reportan_cada_par():
    res = filtrar_por_lesiones([_ej("press_militar")],
                               [Lesion(zona="hombro_derecho", severidad="leve", activa=True),
                                Lesion(zona="hombro_izquierdo", severidad="leve", activa=True)])
    assert res.permitidos == []
    assert ("press_militar", "hombro_derecho") in res.bloqueados
    assert ("press_militar", "hombro_izquierdo") in res.bloqueados
