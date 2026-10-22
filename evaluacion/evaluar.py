"""Evaluacion del coach contra el golden set (spec sec. 10).

Uso: python evaluacion/evaluar.py [--golden RUTA] [--salida RUTA] [--sin-grafo]

Partes:
1. Recuperacion: `buscar` contra Qdrant (requiere la ingesta: scripts/ingerir.py). Mide
   hit rate@k (algun documento esperado en el top-k) y MRR@k. No usa el LLM.
2. Seguridad determinista: el filtro `filtrar_por_lesiones` sobre el catalogo real. Ningun
   ejercicio prohibido puede pasar y los permitidos no deben bloquearse. No usa el LLM.
3. Seguridad del grafo (solo si GOOGLE_API_KEY y TEST_DATABASE_URL estan configuradas):
   por cada caso crea un usuario con la lesion en la base de pruebas, pide la rutina al grafo
   real (Gemini) y comprueba que la rutina final guardada no contiene ejercicios bloqueados.

Todo se lee de Settings (entorno o .env). Escribe evaluacion/resultados.json. Devuelve 1 si
hay alguna violacion de seguridad.
"""

import argparse
import asyncio
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from app.catalogo.cargador import cargar_catalogo  # noqa: E402
from app.domain.modelos import Ejercicio, Lesion, Nivel, Perfil  # noqa: E402
from app.rag.recuperador import FiltrosBusqueda, buscar  # noqa: E402
from app.safety.reglas import filtrar_por_lesiones  # noqa: E402
from app.settings import Settings, SettingsSinLLM  # noqa: E402

AVISO_MEDICO = "Esto no es un diagnóstico médico."
GOLDEN = Path(__file__).resolve().parent / "golden_set.json"
SALIDA = Path(__file__).resolve().parent / "resultados.json"
EQUIPO_GRAFO = ["barbell", "dumbbell", "cable", "machine", "cuerpo"]


def _lesion(zona: str) -> Lesion:
    return Lesion(zona=zona, severidad="moderada", activa=True)


# --- 1. Recuperacion ------------------------------------------------------------------

async def evaluar_recuperacion(casos: list[dict], k: int, settings: Settings) -> dict[str, Any]:
    from app.rag.codificadores import cliente_desde_settings

    cliente = cliente_desde_settings(settings)
    try:
        try:
            existe = await cliente.collection_exists(settings.qdrant_collection)
        except Exception as exc:
            return {"estado": "omitida", "motivo": f"Qdrant no disponible ({type(exc).__name__})"}
        if not existe:
            return {"estado": "omitida",
                    "motivo": f"la coleccion '{settings.qdrant_collection}' no existe: ejecuta scripts/ingerir.py"}
        resultados = []
        for caso in casos:
            filtros = FiltrosBusqueda(**caso.get("filtros", {}))
            docs = await buscar(caso["consulta"], filtros, k, settings, cliente=cliente)
            esperados = set(caso["esperados"])
            rango = next(
                (i for i, d in enumerate(docs, 1) if d.id in esperados or d.fuente in esperados), None
            )
            resultados.append({
                "id": caso["id"],
                "consulta": caso["consulta"],
                "esperados": caso["esperados"],
                "recuperados": [d.id for d in docs],
                "acierto": rango is not None,
                "rango": rango,
            })
    finally:
        await cliente.close()
    n = len(resultados)
    aciertos = sum(r["acierto"] for r in resultados)
    mrr = sum(1 / r["rango"] for r in resultados if r["rango"]) / n if n else 0.0
    return {
        "estado": "ejecutada",
        "casos": resultados,
        "resumen": {"casos": n, "aciertos": aciertos,
                    f"hit_rate@{k}": round(aciertos / n, 3) if n else 0.0,
                    f"mrr@{k}": round(mrr, 3)},
    }


# --- 2. Seguridad determinista ---------------------------------------------------------

def evaluar_seguridad_determinista(casos: list[dict], catalogo: dict[str, Ejercicio]) -> dict[str, Any]:
    resultados = []
    for caso in casos:
        lesiones = [_lesion(caso["zona"])]
        ids = caso["prohibidos"] + caso.get("permitidos", [])
        desconocidos = [i for i in ids if i not in catalogo]
        conocidos = [catalogo[i] for i in ids if i in catalogo]
        bloqueados = {i for i, _ in filtrar_por_lesiones(conocidos, lesiones).bloqueados}
        # un prohibido ausente del catalogo invalida el caso: se cuenta como violacion
        violaciones = [i for i in caso["prohibidos"] if i not in bloqueados]
        sobrebloqueos = [i for i in caso.get("permitidos", []) if i in bloqueados]
        total_bloqueados = len(filtrar_por_lesiones(list(catalogo.values()), lesiones).bloqueados)
        resultados.append({
            "id": caso["id"],
            "zona": caso["zona"],
            "violaciones": violaciones,
            "sobrebloqueos": sobrebloqueos,
            "ids_fuera_del_catalogo": desconocidos,
            "bloqueados_en_catalogo": total_bloqueados,
            "ok": not violaciones and not sobrebloqueos and not desconocidos,
        })
    return {
        "estado": "ejecutada",
        "casos": resultados,
        "resumen": {
            "casos": len(resultados),
            "violaciones": sum(len(r["violaciones"]) for r in resultados),
            "sobrebloqueos": sum(len(r["sobrebloqueos"]) for r in resultados),
            "ids_fuera_del_catalogo": sum(len(r["ids_fuera_del_catalogo"]) for r in resultados),
        },
    }


# --- 3. Seguridad del grafo (LLM real) ---------------------------------------------------

def _motivo_omitir_grafo() -> tuple[Settings | None, str | None, str | None]:
    """(settings_completas, url_bd_pruebas, motivo_para_omitir)."""
    from pydantic import ValidationError

    from tests.guarda_bd import resolver_url_pruebas

    try:
        settings = Settings()
    except ValidationError as exc:
        faltan = sorted({str(e["loc"][0]) for e in exc.errors()})
        return None, None, f"configuracion incompleta para el grafo (faltan: {', '.join(faltan)})"
    if not settings.google_api_key.get_secret_value().strip():
        return None, None, "GOOGLE_API_KEY no configurada"
    url, motivo = resolver_url_pruebas(os.environ)
    if url is None:
        return None, None, motivo
    return settings, url, None


async def evaluar_seguridad_grafo(casos: list[dict], catalogo: dict[str, Ejercicio]) -> dict[str, Any]:
    settings, url_bd, motivo = _motivo_omitir_grafo()
    if motivo:
        return {"estado": "omitida", "motivo": motivo}

    from langgraph.checkpoint.redis.aio import AsyncRedisSaver
    from sqlalchemy.ext.asyncio import async_sessionmaker

    from app import observabilidad
    from app.agentes.grafo import config_hilo, construir_grafo
    from app.persistencia.repositorios import RepositorioDominio, crear_motor

    migracion = await asyncio.to_thread(
        subprocess.run, [sys.executable, "-m", "alembic", "upgrade", "head"],
        cwd=RAIZ, capture_output=True, text=True, env={**os.environ, "DATABASE_URL": url_bd},
    )
    if migracion.returncode != 0:
        return {"estado": "error", "motivo": "alembic upgrade head fallo en la base de pruebas"}

    cfg = settings.model_copy(update={"database_url": url_bd})
    observabilidad.configurar_trazas(cfg)
    motor = crear_motor(url_bd)
    repo = RepositorioDominio(async_sessionmaker(motor, expire_on_commit=False))
    resultados = []
    try:
        async with AsyncRedisSaver.from_conn_string(cfg.redis_url) as saver:
            await saver.asetup()
            grafo = await construir_grafo(cfg, repo, saver, catalogo=catalogo)
            for caso in casos:
                uid = await repo.crear_usuario()
                await repo.guardar_perfil(Perfil(
                    usuario_id=uid, objetivo="fuerza", dias_disponibles=3,
                    equipo=EQUIPO_GRAFO, nivel=Nivel.intermedio,
                ))
                lesiones = [_lesion(caso["zona"])]
                await repo.agregar_lesion(uid, lesiones[0])
                with observabilidad.contexto_traza(
                    f"evaluacion.{caso['id']}", thread_id=str(uid), usuario_id=str(uid)
                ):
                    salida = await grafo.ainvoke(
                        {"usuario_id": uid, "mensaje": caso["consulta"]}, config_hilo(uid)
                    )
                rutina = await repo.rutina_actual(uid)
                ids = sorted({p.ejercicio_id for d in rutina.dias for p in d.ejercicios}) if rutina else []
                conocidos = [catalogo[i] for i in ids if i in catalogo]
                bloqueados = {i for i, _ in filtrar_por_lesiones(conocidos, lesiones).bloqueados}
                violaciones = sorted(
                    {i for i in ids if i in bloqueados or i in caso["prohibidos"] or i not in catalogo}
                )
                respuesta = salida.get("respuesta") or ""
                resultados.append({
                    "id": caso["id"],
                    "zona": caso["zona"],
                    "rutina_generada": rutina is not None,
                    "ejercicios": ids,
                    "violaciones": violaciones,
                    "aviso_medico": AVISO_MEDICO in respuesta,
                    "requiere_humano": bool(salida.get("__interrupt__")),
                })
        from opentelemetry import trace

        proveedor = trace.get_tracer_provider()
        if hasattr(proveedor, "force_flush"):
            proveedor.force_flush()
    finally:
        await motor.dispose()
    return {
        "estado": "ejecutada",
        "casos": resultados,
        "resumen": {
            "casos": len(resultados),
            "rutinas_generadas": sum(r["rutina_generada"] for r in resultados),
            "violaciones": sum(len(r["violaciones"]) for r in resultados),
            "respuestas_sin_aviso": sum(not r["aviso_medico"] for r in resultados),
        },
    }


# --- principal ----------------------------------------------------------------------------

async def evaluar(golden: Path, salida: Path, *, con_grafo: bool = True) -> dict[str, Any]:
    datos = json.loads(golden.read_text(encoding="utf-8"))
    k = int(datos.get("k", 5))
    casos_rec = [c for c in datos["casos"] if c["tipo"] == "recuperacion"]
    casos_seg = [c for c in datos["casos"] if c["tipo"] == "seguridad"]
    settings = SettingsSinLLM()
    catalogo = {e.id: e for e in cargar_catalogo(settings.catalogo_path)}

    inicio = time.perf_counter()
    recuperacion = await evaluar_recuperacion(casos_rec, k, settings)
    determinista = evaluar_seguridad_determinista(casos_seg, catalogo)
    if con_grafo:
        grafo = await evaluar_seguridad_grafo(casos_seg, catalogo)
    else:
        grafo = {"estado": "omitida", "motivo": "--sin-grafo"}

    violaciones = determinista["resumen"]["violaciones"] + (
        grafo["resumen"]["violaciones"] if grafo["estado"] == "ejecutada" else 0
    )
    informe = {
        "fecha": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "golden_set": golden.name,
        "k": k,
        "coleccion": settings.qdrant_collection,
        "modelo_embeddings": settings.embedding_model,
        "segundos": round(time.perf_counter() - inicio, 1),
        "resumen": {
            "recuperacion": recuperacion.get("resumen", {"estado": recuperacion["estado"]}),
            "seguridad_determinista": determinista["resumen"],
            "seguridad_grafo": grafo.get("resumen", {"estado": grafo["estado"], "motivo": grafo.get("motivo")}),
            "violaciones_de_seguridad": violaciones,
        },
        "recuperacion": recuperacion,
        "seguridad_determinista": determinista,
        "seguridad_grafo": grafo,
    }
    salida.write_text(json.dumps(informe, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return informe


def main() -> int:
    parser = argparse.ArgumentParser(description="Evalua el coach contra el golden set")
    parser.add_argument("--golden", type=Path, default=GOLDEN)
    parser.add_argument("--salida", type=Path, default=SALIDA)
    parser.add_argument("--sin-grafo", action="store_true", help="omite la parte con el LLM")
    args = parser.parse_args()
    informe = asyncio.run(evaluar(args.golden, args.salida, con_grafo=not args.sin_grafo))
    print(json.dumps(informe["resumen"], ensure_ascii=False, indent=2))
    print(f"Resultados en {args.salida}")
    return 1 if informe["resumen"]["violaciones_de_seguridad"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
