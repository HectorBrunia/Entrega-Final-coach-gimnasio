import pytest

from app.safety.reglas import ZonaLesionDesconocida, filtrar_por_lesiones
from app.domain.modelos import Ejercicio, Lesion, Nivel


def _ej(id_, musculo="shoulders"):
    return Ejercicio(id=id_, nombre=id_, musculo_primario=musculo, musculos_secundarios=[],
                     equipo="mancuernas", nivel=Nivel.principiante, instrucciones=[])


def test_hombro_derecho_bloquea_press_militar():
    res = filtrar_por_lesiones([_ej("press_militar"), _ej("curl_biceps", "biceps")],
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


def test_zona_activa_desconocida_lanza():
    with pytest.raises(ZonaLesionDesconocida, match="hombro"):
        filtrar_por_lesiones([_ej("press_militar")],
                             [Lesion(zona="hombro", severidad="grave", activa=True)])


def test_zona_inactiva_desconocida_no_lanza():
    res = filtrar_por_lesiones([_ej("press_militar")],
                               [Lesion(zona="rodilla_x", severidad="leve", activa=False)])
    assert len(res.permitidos) == 1 and res.bloqueados == []


def test_zona_con_espacios_y_mayusculas_se_normaliza():
    res = filtrar_por_lesiones([_ej("press_militar")],
                               [Lesion(zona=" Hombro_Derecho ", severidad="leve", activa=True)])
    assert res.permitidos == []
    assert ("press_militar", "hombro_derecho") in res.bloqueados


def test_dos_lesiones_reportan_cada_par():
    res = filtrar_por_lesiones([_ej("press_militar")],
                               [Lesion(zona="hombro_derecho", severidad="leve", activa=True),
                                Lesion(zona="hombro_izquierdo", severidad="leve", activa=True)])
    assert res.permitidos == []
    assert ("press_militar", "hombro_derecho") in res.bloqueados
    assert ("press_militar", "hombro_izquierdo") in res.bloqueados
