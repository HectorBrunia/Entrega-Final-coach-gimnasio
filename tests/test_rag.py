import threading

import pytest

from app.domain.modelos import Nivel
from app.rag.ingesta import Documento, ingerir
from app.rag.recuperador import FiltrosBusqueda, buscar

SIN_FILTROS = FiltrosBusqueda(equipo=None, nivel=None, musculo=None)


async def test_filtro_por_equipo_excluye_otros_equipos(coleccion_prueba, settings_rag):
    res = await buscar("empuje de pecho", FiltrosBusqueda(equipo="cuerpo", nivel=None, musculo=None),
                       k=5, settings=settings_rag, **coleccion_prueba)
    assert res and all(d.metadatos["equipo"] == "cuerpo" for d in res)


async def test_filtro_por_nivel_y_musculo(coleccion_prueba, settings_rag):
    res = await buscar("ejercicio", FiltrosBusqueda(equipo=None, nivel=Nivel.intermedio, musculo="quadriceps"),
                       k=5, settings=settings_rag, **coleccion_prueba)
    assert [d.id for d in res] == ["Barbell_Squat"]


async def test_ingerir_es_idempotente(cliente_qdrant, settings_rag, denso_falso, coleccion_prueba):
    doc = Documento(id="x1", texto="uno", fuente="f", metadatos={"equipo": "cuerpo"})
    await ingerir([doc], settings_rag, **coleccion_prueba)
    await ingerir([doc], settings_rag, **coleccion_prueba)
    n = await cliente_qdrant.count(settings_rag.qdrant_collection)
    assert n.count == 4  # 3 del catalogo + x1, sin duplicar


async def test_embeddings_densos_fuera_del_event_loop(coleccion_prueba, settings_rag, denso_falso):
    denso_falso.hilos.clear()
    await buscar("sentadilla", SIN_FILTROS, k=3, settings=settings_rag, **coleccion_prueba)
    assert denso_falso.hilos and all(h != threading.get_ident() for h in denso_falso.hilos)


async def test_busqueda_hibrida_recupera_coincidencia_solo_lexica(cliente_qdrant, settings_rag):
    """El denso da vector casi ortogonal al documento; solo el disperso lo encuentra."""
    from tests.conftest import DisperoFalso

    class DensoPlano:
        def codificar(self, textos):
            # documento objetivo lejos de la consulta; el resto cerca
            return [[0.0, 1.0] if "zancada" in t else [1.0, 0.0] for t in textos]

        def codificar_consulta(self, textos):
            return [[1.0, 0.0] for _ in textos]

    inj = dict(cliente=cliente_qdrant, denso=DensoPlano(), disperso=DisperoFalso())
    docs = [Documento(id=f"d{i}", texto=f"relleno {i}", fuente="f", metadatos={"equipo": "cuerpo"}) for i in range(5)]
    docs.append(Documento(id="obj", texto="zancada", fuente="f", metadatos={"equipo": "cuerpo"}))
    await ingerir(docs, settings_rag, **inj)
    res = await buscar("zancada", SIN_FILTROS, k=2, settings=settings_rag, **inj)
    assert "obj" in [d.id for d in res]
