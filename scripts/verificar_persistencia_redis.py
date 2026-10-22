"""Verifica que los checkpoints del grafo sobreviven a reinicios de Redis.

Usa el checkpointer de produccion (`abrir_checkpointer_redis`, con el serializador del
estado). Es un script en dos fases porque el reinicio del contenedor ocurre fuera de
Python (no es una prueba de pytest: reiniciar Docker desde la suite no es fiable ni
portable).

Uso (desde la raiz del repositorio, con REDIS_URL apuntando al Redis del compose):
    python scripts/verificar_persistencia_redis.py escribir        # imprime el thread_id
    docker compose restart redis                                   # o: down && up -d redis
    python scripts/verificar_persistencia_redis.py leer <thread_id>

`leer` termina con codigo 0 si el hilo existe y conserva sus tipos; 1 si no.
"""

import asyncio
import os
import sys
from pathlib import Path
from uuid import UUID, uuid4

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from langgraph.checkpoint.base import empty_checkpoint  # noqa: E402

from app.agentes.checkpointer import abrir_checkpointer_redis  # noqa: E402
from app.domain.modelos import (  # noqa: E402
    DiaRutina, EjercicioPlanificado, Lesion, Nivel, Perfil, Rutina,
)


def _url() -> str:
    url = os.environ.get("REDIS_URL")
    if not url:
        sys.exit("Falta REDIS_URL")
    return url


def _config(thread_id: str) -> dict:
    return {"configurable": {"thread_id": thread_id, "checkpoint_ns": ""}}


def _estado(uid: UUID) -> dict:
    return {
        "usuario_id": uid,
        "perfil": Perfil(usuario_id=uid, objetivo="fuerza", dias_disponibles=3,
                         equipo=["barra"], nivel=Nivel.principiante),
        "lesiones": [Lesion(zona="rodilla", severidad="leve", activa=True)],
        "rutina": Rutina(usuario_id=uid, version=1, dias=[DiaRutina(nombre="Dia A", ejercicios=[
            EjercicioPlanificado(ejercicio_id="sentadilla", series=3, repeticiones="8-10",
                                 descanso_seg=90, fuentes=["guia"])])]),
    }


async def escribir() -> None:
    uid = uuid4()
    ckpt = empty_checkpoint()
    ckpt["channel_values"] = _estado(uid)
    ckpt["channel_versions"] = {k: 1 for k in ckpt["channel_values"]}
    async with abrir_checkpointer_redis(_url()) as saver:
        await saver.aput(_config(str(uid)), ckpt, {}, ckpt["channel_versions"])
    print(str(uid))


async def leer(thread_id: str) -> int:
    async with abrir_checkpointer_redis(_url()) as saver:
        tupla = await saver.aget_tuple(_config(thread_id))
    if tupla is None:
        print(f"FALLO: el hilo {thread_id} no existe")
        return 1
    valores = tupla.checkpoint["channel_values"]
    tipos = {k: type(v).__name__ for k, v in valores.items()}
    print("tipos:", tipos)
    correcto = valores == _estado(UUID(thread_id)) and isinstance(valores["usuario_id"], UUID)
    print("OK: hilo intacto con sus tipos" if correcto else "FALLO: el estado cambio")
    return 0 if correcto else 1


def main() -> int:
    if len(sys.argv) >= 2 and sys.argv[1] == "escribir":
        asyncio.run(escribir())
        return 0
    if len(sys.argv) == 3 and sys.argv[1] == "leer":
        return asyncio.run(leer(sys.argv[2]))
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main())
