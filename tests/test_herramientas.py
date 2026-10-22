from datetime import date
from uuid import uuid4

import pytest

from app.domain.modelos import (
    DiaRutina,
    Ejercicio,
    EjercicioPlanificado,
    EntrenoRegistro,
    Lesion,
    Nivel,
    Rutina,
)
from app.herramientas import funciones
from app.herramientas.esquemas import EntradaVolumen
from app.herramientas.funciones import (
    EjercicioDesconocido,
    buscar_conocimiento,
    consultar_historial,
    validar_plan,
    volumen_semanal,
)
from app.rag.ingesta import Documento
from app.rag.recuperador import FiltrosBusqueda
from app.safety.reglas import ZonaLesionDesconocida


def _ej(id_: str, musculo: str, nivel: Nivel = Nivel.principiante) -> Ejercicio:
    return Ejercicio(id=id_, nombre=id_, musculo_primario=musculo, musculos_secundarios=[],
                     equipo="mancuernas", nivel=nivel, instrucciones=[])


def _plan(*ids: str) -> Rutina:
    return Rutina(usuario_id=uuid4(), version=1, dias=[
        DiaRutina(nombre="A", ejercicios=[
            EjercicioPlanificado(ejercicio_id=i, series=3, repeticiones="8-10",
                                 descanso_seg=90, fuentes=["guia_tecnica"]) for i in ids])])


HOMBRO = [Lesion(zona="hombro_derecho", severidad="moderada", activa=True)]


def test_volumen_suma_series_por_musculo():
    rutina = _plan("press_banca", "aperturas")
    catalogo = {"press_banca": _ej("press_banca", "pecho"), "aperturas": _ej("aperturas", "pecho")}
    assert volumen_semanal(EntradaVolumen(rutina=rutina, catalogo=catalogo)).series_por_musculo == {"pecho": 6}


def test_volumen_id_desconocido_lanza():
    with pytest.raises(EjercicioDesconocido, match="fantasma"):
        volumen_semanal(EntradaVolumen(rutina=_plan("fantasma"), catalogo={}))


async def test_validar_plan_detecta_ejercicio_bloqueado():
    catalogo = {"press_militar": _ej("press_militar", "hombro", Nivel.intermedio)}
    assert await validar_plan(_plan("press_militar"), HOMBRO, catalogo=catalogo) == ["press_militar"]


async def test_validar_plan_id_fuera_de_catalogo_se_bloquea():
    catalogo = {"press_banca": _ej("press_banca", "pecho")}
    rutina = _plan("fantasma", "press_banca", "fantasma")
    assert await validar_plan(rutina, [], catalogo=catalogo) == ["fantasma"]


async def test_validar_plan_zona_desconocida_propaga():
    catalogo = {"press_banca": _ej("press_banca", "pecho")}
    with pytest.raises(ZonaLesionDesconocida):
        await validar_plan(_plan("press_banca"),
                           [Lesion(zona="rodilla_marciana", severidad="leve", activa=True)], catalogo=catalogo)


async def test_validar_plan_seguro_devuelve_vacio():
    catalogo = {"press_banca": _ej("press_banca", "pecho")}
    assert await validar_plan(_plan("press_banca"), HOMBRO, catalogo=catalogo) == []


async def test_consultar_historial_delega_en_repo():
    uid = uuid4()
    reg = EntrenoRegistro(usuario_id=uid, fecha=date(2026, 1, 1), ejercicio_id="x", series=3,
                          repeticiones=8, peso_kg=20, rpe=7)

    class RepoFalso:
        async def historial(self, usuario_id, limite):
            assert (usuario_id, limite) == (uid, 5)
            return [reg]

    assert await consultar_historial(RepoFalso(), uid, 5) == [reg]


async def test_buscar_conocimiento_delega_en_rag(monkeypatch):
    doc = Documento(id="d", texto="t", fuente="f", metadatos={})
    llamado = {}

    async def falso(consulta, filtros, k, settings, **kw):
        llamado.update(consulta=consulta, filtros=filtros, k=k, settings=settings)
        return [doc]

    monkeypatch.setattr(funciones, "buscar", falso)
    filtros = FiltrosBusqueda(musculo="pecho")
    sentinela = object()
    assert await buscar_conocimiento("press", filtros, k=3, settings=sentinela) == [doc]
    assert llamado == {"consulta": "press", "filtros": filtros, "k": 3, "settings": sentinela}
