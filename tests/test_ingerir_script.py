"""scripts/ingerir.py: corpus desde Settings e idempotencia (Qdrant en memoria, codificadores falsos)."""

from qdrant_client.models import PointStruct

from app.rag.codificadores import VECTOR_DENSO, VECTOR_DISPERSO
from app.rag.ingesta import punto_id
from scripts.ingerir import documentos_corpus, ingerir_corpus
from tests.conftest import RAIZ, DisperoFalso


def _settings(settings_rag):
    return settings_rag.model_copy(update={
        "catalogo_path": RAIZ / "tests/fixtures/catalogo_muestra.json",
        "guias_dir": RAIZ / "data/guias",
    })


def test_corpus_incluye_catalogo_y_guias(settings_rag):
    ejercicios, guias = documentos_corpus(_settings(settings_rag))
    assert len(ejercicios) == 3
    assert guias and all(g.fuente.startswith("guia:") for g in guias)


async def test_segunda_ingesta_sin_cambios_no_recodifica(cliente_qdrant, settings_rag, denso_falso):
    cfg = _settings(settings_rag)
    kw = dict(cliente=cliente_qdrant, denso=denso_falso, disperso=DisperoFalso())
    primera = await ingerir_corpus(cfg, **kw)
    n = (await cliente_qdrant.count(cfg.qdrant_collection)).count
    assert primera.reingestado and n == primera.ejercicios + primera.fragmentos_guias

    segunda = await ingerir_corpus(cfg, **kw)
    assert not segunda.reingestado
    assert (await cliente_qdrant.count(cfg.qdrant_collection)).count == n

    forzada = await ingerir_corpus(cfg, forzar=True, **kw)
    assert forzada.reingestado


async def test_elimina_puntos_que_ya_no_estan_en_el_corpus(cliente_qdrant, settings_rag, denso_falso):
    cfg = _settings(settings_rag)
    kw = dict(cliente=cliente_qdrant, denso=denso_falso, disperso=DisperoFalso())
    r = await ingerir_corpus(cfg, **kw)
    obsoleto = PointStruct(
        id=punto_id("obsoleto"),
        vector={VECTOR_DENSO: denso_falso.codificar(["x"])[0],
                VECTOR_DISPERSO: DisperoFalso().codificar(["x"])[0]},
        payload={"id": "obsoleto", "texto": "x", "fuente": "f", "metadatos": {}},
    )
    await cliente_qdrant.upsert(cfg.qdrant_collection, points=[obsoleto], wait=True)

    r2 = await ingerir_corpus(cfg, **kw)
    assert r2.eliminados == 1
    assert (await cliente_qdrant.count(cfg.qdrant_collection)).count == r.ejercicios + r.fragmentos_guias
