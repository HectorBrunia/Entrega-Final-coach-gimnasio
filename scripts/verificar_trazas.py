"""Verifica de extremo a extremo que las trazas llegan a Phoenix.

Requiere `docker compose up -d phoenix`. Uso: python scripts/verificar_trazas.py
Endpoint del colector: PHOENIX_COLLECTOR_ENDPOINT (por defecto el de docker-compose).
"""

import os
import sys
import time
from pathlib import Path
from urllib.parse import urlparse

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

ENDPOINT = os.environ.get("PHOENIX_COLLECTOR_ENDPOINT", "http://localhost:6006")
PROYECTO = "coach-gimnasio"


def main() -> int:
    from langchain_core.language_models.fake_chat_models import FakeListChatModel
    from opentelemetry import trace

    from app.observabilidad import configurar_trazas, contexto_traza

    class Cfg:  # basta el atributo que usa configurar_trazas (evita exigir todo el .env)
        phoenix_collector_endpoint = ENDPOINT

    configurar_trazas(Cfg())
    with contexto_traza("verificacion", thread_id="hilo-verif", usuario_id="usuario-verif"):
        FakeListChatModel(responses=["hola desde el modelo falso"]).invoke("di hola")
    trace.get_tracer_provider().force_flush()

    # Phoenix 6.0.0 no expone REST para listar spans: se consulta su API GraphQL.
    base = urlparse(ENDPOINT)
    url = f"{base.scheme}://{base.netloc}/graphql"
    consulta = (
        "{ projects { edges { node { name traceCount "
        "spans(first: 50) { edges { node { name spanKind } } } } } } }"
    )
    ultimo = ""
    for _ in range(15):
        r = httpx.post(url, json={"query": consulta}, timeout=5)
        ultimo = f"{r.status_code}: {r.text[:200]}"
        if r.status_code == 200:
            for p in r.json()["data"]["projects"]["edges"]:
                nodo = p["node"]
                if nodo["name"] == PROYECTO and nodo["traceCount"] >= 1:
                    spans = [e["node"] for e in nodo["spans"]["edges"]]
                    print(f"OK: {nodo['traceCount']} traza(s), {len(spans)} span(s) en '{PROYECTO}'")
                    for sp in spans:
                        print(" -", sp["name"], sp["spanKind"])
                    return 0
        time.sleep(1)
    print(f"FALLO: no llegaron trazas (ultima respuesta {ultimo})")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
