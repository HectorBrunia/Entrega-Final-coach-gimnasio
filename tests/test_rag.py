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


async def test_coleccion_usa_modificador_idf_en_vector_disperso(cliente_qdrant, settings_rag, coleccion_prueba):
    from qdrant_client.models import Modifier

    info = await cliente_qdrant.get_collection(settings_rag.qdrant_collection)
    assert info.config.params.sparse_vectors["disperso"].modifier == Modifier.IDF


def test_codificador_disperso_recibe_modelo_e_idioma_de_settings(settings_rag, monkeypatch):
    from app.rag import codificadores

    recibidos = []

    class BM25Falso:
        def __init__(self, modelo, idioma):
            recibidos.append((modelo, idioma))

    monkeypatch.setattr(codificadores, "DispersoBM25", BM25Falso)
    monkeypatch.setattr(codificadores, "_disperso_por_defecto", {})
    codificadores.disperso_desde_settings(settings_rag.model_copy(update={"bm25_idioma": "portuguese"}))
    codificadores.disperso_desde_settings(settings_rag)
    codificadores.disperso_desde_settings(settings_rag.model_copy(update={"bm25_modelo": "otro/bm25"}))
    codificadores.disperso_desde_settings(settings_rag)  # cacheado por (modelo, idioma)
    assert recibidos == [("Qdrant/bm25", "portuguese"), ("Qdrant/bm25", "spanish"),
                         ("otro/bm25", "spanish")]


def test_bm25_de_produccion_usa_el_modelo_de_settings(monkeypatch):
    import sys
    import types

    from app.rag.codificadores import DispersoBM25

    cargados = []

    class SparseFalso:
        def __init__(self, nombre, language):
            cargados.append((nombre, language))

    monkeypatch.setitem(sys.modules, "fastembed", types.SimpleNamespace(SparseTextEmbedding=SparseFalso))
    DispersoBM25("mi-org/bm25", "spanish")._cargar()
    assert cargados == [("mi-org/bm25", "spanish")]


async def test_coleccion_existente_sin_idf_lanza_incompatible(cliente_qdrant, settings_rag):
    from qdrant_client.models import Distance, SparseVectorParams, VectorParams

    from app.rag.ingesta import ColeccionIncompatible, asegurar_coleccion

    nombre = settings_rag.qdrant_collection
    await cliente_qdrant.create_collection(
        nombre,
        vectors_config={"denso": VectorParams(size=16, distance=Distance.COSINE)},
        sparse_vectors_config={"disperso": SparseVectorParams()},
    )
    with pytest.raises(ColeccionIncompatible, match=nombre):
        await asegurar_coleccion(cliente_qdrant, nombre, 16)


async def test_coleccion_existente_compatible_no_se_recrea(cliente_qdrant, settings_rag, coleccion_prueba):
    from app.rag.ingesta import asegurar_coleccion

    antes = await cliente_qdrant.count(settings_rag.qdrant_collection)
    await asegurar_coleccion(cliente_qdrant, settings_rag.qdrant_collection, 16)
    despues = await cliente_qdrant.count(settings_rag.qdrant_collection)
    assert antes.count == despues.count == 3  # los datos siguen ahi


async def test_coleccion_existente_con_dimension_distinta_lanza_incompatible(cliente_qdrant, settings_rag, coleccion_prueba):
    from app.rag.ingesta import ColeccionIncompatible, asegurar_coleccion

    with pytest.raises(ColeccionIncompatible):
        await asegurar_coleccion(cliente_qdrant, settings_rag.qdrant_collection, 32)


async def test_filtros_no_excluyen_documentos_sin_ese_metadato(cliente_qdrant, settings_rag, coleccion_prueba):
    """Las guias no tienen nivel/equipo/musculo: un filtro solo restringe a los ejercicios."""
    from app.rag.ingesta import documentos_desde_guia

    guia = documentos_desde_guia("progresion", "# Guia\n\n## Por nivel\nIntermedio: rutina dividida.\n")
    await ingerir(guia, settings_rag, **coleccion_prueba)
    res = await buscar("rutina dividida intermedio",
                       FiltrosBusqueda(equipo="barbell", nivel=Nivel.principiante, musculo=None),
                       k=10, settings=settings_rag, **coleccion_prueba)
    ids = [d.id for d in res]
    assert "progresion#por-nivel" in ids
    catalogo = [d for d in res if d.fuente == "catalogo"]
    assert all(d.metadatos["nivel"] == "principiante" and d.metadatos["equipo"] == "barbell" for d in catalogo)


def test_documentos_desde_guia_trocea_por_seccion_y_omite_fuentes():
    from app.rag.ingesta import documentos_desde_guia

    md = ("# Guía: técnica\n\n> aviso\n\n## Principios generales\n- a\n- b\n\n"
          "## Patrones frecuentes\n- c\n\n## Fuentes\n- ACSM\n")
    docs = documentos_desde_guia("tecnica_basica", md)
    assert [d.id for d in docs] == ["tecnica_basica#principios-generales", "tecnica_basica#patrones-frecuentes"]
    assert all(d.fuente == "guia:tecnica_basica" and d.metadatos == {} for d in docs)
    assert docs[0].texto.startswith("Guía: técnica. Principios generales.")
    assert "ACSM" not in " ".join(d.texto for d in docs)


def test_documentos_desde_guias_reales_tienen_ids_unicos():
    from pathlib import Path

    from app.rag.ingesta import documentos_desde_guias

    docs = documentos_desde_guias(Path(__file__).resolve().parent.parent / "data" / "guias")
    ids = [d.id for d in docs]
    assert len(ids) == len(set(ids)) and len(ids) >= 3
    assert {"progresion#por-nivel", "consideraciones_por_zona_lesion#hombro"} <= set(ids)
