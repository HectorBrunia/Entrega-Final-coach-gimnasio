"""Checkpointer del grafo: el estado leido tiene los mismos tipos que el escrito.

El `AsyncRedisSaver` guarda el estado como JSON con `JsonPlusRedisSerializer`. Sin
configurar, ese serializador pierde dos tipos del `EstadoCoach`:

- Modelos Pydantic (`Perfil`, `Lesion`, `Rutina` y sus anidados): se escriben como sobres
  `{"lc": 2, "type": "constructor", ...}`, pero al leer solo se reconstruyen las clases del
  allowlist `allowed_json_modules` (vacio por defecto), asi que vuelven como ese sobre.
- `UUID`: orjson lo escribe como texto sin marca de tipo y vuelve como `str`.

`SerializadorEstado` allowlista exactamente los modelos del esquema del estado (derivados
de `EstadoCoach`, no una lista a mano) y escribe los `UUID` con su sobre de constructor.
"""

from collections.abc import AsyncIterator, Callable
from contextlib import asynccontextmanager
from typing import Any, get_args, get_type_hints
from uuid import UUID

from langgraph.checkpoint.redis.jsonplus_redis import JsonPlusRedisSerializer
from pydantic import BaseModel

from app.agentes.estado import EstadoCoach

_PAQUETE_PROPIO = "app"


def _recorrer(tipo: Any, vistos: list[type[BaseModel]]) -> None:
    if isinstance(tipo, type) and issubclass(tipo, BaseModel):
        # Solo modelos propios: los mensajes de LangChain tienen su propia serializacion.
        if tipo.__module__.split(".")[0] != _PAQUETE_PROPIO or tipo in vistos:
            return
        vistos.append(tipo)
        for campo in tipo.model_fields.values():
            _recorrer(campo.annotation, vistos)
        return
    for arg in get_args(tipo):  # list[...], X | None, Annotated[...], etc.
        _recorrer(arg, vistos)


def modelos_del_estado() -> list[type[BaseModel]]:
    """Modelos Pydantic propios que aparecen en `EstadoCoach`, incluidos los anidados."""
    vistos: list[type[BaseModel]] = []
    for tipo in get_type_hints(EstadoCoach, include_extras=True).values():
        _recorrer(tipo, vistos)
    return vistos


def _simbolo(cls: type) -> tuple[str, ...]:
    # mismo formato que el campo "id" del sobre lc:2: modulo partido por puntos + nombre
    return (*cls.__module__.split("."), cls.__name__)


class SerializadorEstado(JsonPlusRedisSerializer):
    """`JsonPlusRedisSerializer` que conserva los tipos del `EstadoCoach`."""

    def __init__(self) -> None:
        super().__init__(allowed_json_modules=[_simbolo(m) for m in modelos_del_estado()])

    def _preprocess_redis_json(
        self, obj: Any, *, encode_bytes: Callable[[bytes], Any] | None = None
    ) -> Any:
        if isinstance(obj, UUID):
            # uuid.UUID esta entre los tipos seguros de LangGraph: se revive sin allowlist
            return self._encode_constructor_envelope(UUID, args=[str(obj)])
        return super()._preprocess_redis_json(obj, encode_bytes=encode_bytes)


def serializador_estado() -> SerializadorEstado:
    return SerializadorEstado()


@asynccontextmanager
async def abrir_checkpointer_redis(redis_url: str) -> AsyncIterator[Any]:
    """`AsyncRedisSaver` de produccion, con el serializador del estado."""
    from langgraph.checkpoint.redis.aio import AsyncRedisSaver

    async with AsyncRedisSaver.from_conn_string(redis_url) as saver:
        # AsyncRedisSaver no acepta `serde` en su constructor: se sustituye antes de usarlo
        saver.serde = serializador_estado()
        await saver.asetup()
        yield saver
