"""Checkpointer del grafo: el estado leido tiene los mismos tipos que el escrito.

El `AsyncRedisSaver` guarda el estado como JSON con `JsonPlusRedisSerializer`. Sin
configurar, ese serializador pierde dos tipos del `EstadoCoach`:

- Modelos Pydantic (`Perfil`, `Lesion`, `Rutina` y sus anidados): se escriben como sobres
  `{"lc": 2, "type": "constructor", ...}`, pero al leer solo se reconstruyen las clases del
  allowlist `allowed_json_modules` (vacio por defecto), asi que vuelven como ese sobre.
- `UUID`: orjson lo escribe como texto sin marca de tipo y vuelve como `str`.

Ademas, el serializador base escribe un modelo Pydantic con su `__dict__` crudo, sin
normalizar los valores anidados. Los modelos leidos de Postgres llevan en `usuario_id` un
`asyncpg.pgproto.pgproto.UUID` (subclase de `uuid.UUID` que Pydantic conserva): orjson no lo
serializa de forma nativa, cae al manejador por defecto y se escribe como un sobre
`asyncpg...UUID` sin el valor (no tiene `__dict__`). Al leer, ese sobre no se revive y el
modelo no valida: el serializador base lo registraba y devolvia `None` en silencio.

`SerializadorEstado` allowlista exactamente los modelos del esquema del estado (derivados
de `EstadoCoach`, no una lista a mano), escribe los modelos campo a campo normalizando cada
valor (los `UUID`, de cualquier subclase, como sobre de `uuid.UUID` con su texto) y, si un
modelo del allowlist no se puede reconstruir, lanza `ModeloNoReconstruible` en vez de `None`.
"""

from collections.abc import AsyncIterator, Callable
from contextlib import asynccontextmanager
from typing import Any, get_args, get_type_hints
from uuid import UUID

from langgraph.checkpoint.redis.jsonplus_redis import JsonPlusRedisSerializer
from pydantic import BaseModel, ValidationError

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


class ModeloNoReconstruible(ValueError):
    """Un modelo del estado guardado en el checkpoint no se puede reconstruir."""


class SerializadorEstado(JsonPlusRedisSerializer):
    """`JsonPlusRedisSerializer` que conserva los tipos del `EstadoCoach`."""

    def __init__(self) -> None:
        modelos = modelos_del_estado()
        super().__init__(allowed_json_modules=[_simbolo(m) for m in modelos])
        self._modelos = {_simbolo(m): m for m in modelos}

    def _preprocess_redis_json(
        self, obj: Any, *, encode_bytes: Callable[[bytes], Any] | None = None
    ) -> Any:
        if isinstance(obj, UUID):
            # uuid.UUID esta entre los tipos seguros de LangGraph: se revive sin allowlist.
            # Cualquier subclase (p. ej. el UUID de asyncpg) se escribe como uuid.UUID.
            return self._encode_constructor_envelope(UUID, args=[str(obj)])
        if type(obj) in self._modelos.values():
            # campo a campo y recursivo: los valores anidados se normalizan igual que el resto
            # del estado (el serializador base escribiria el __dict__ sin normalizar)
            kwargs = {
                nombre: self._preprocess_redis_json(getattr(obj, nombre), encode_bytes=encode_bytes)
                for nombre in type(obj).model_fields
            }
            return self._encode_constructor_envelope(type(obj), kwargs=kwargs)
        return super()._preprocess_redis_json(obj, encode_bytes=encode_bytes)

    def _revive_lc2(self, value: dict[str, Any]) -> Any:
        modelo = self._modelos.get(tuple(value["id"]))
        if modelo is None:
            return super()._revive_lc2(value)
        # Modelo propio del estado: el base devolveria None ante un error de validacion y el
        # estado perderia el dato sin avisar. Aqui el fallo es visible.
        try:
            return modelo(*(value.get("args") or ()), **(value.get("kwargs") or {}))
        except (ValidationError, TypeError) as exc:
            raise ModeloNoReconstruible(
                f"No se pudo reconstruir {modelo.__name__} desde el checkpoint: {exc}"
            ) from exc


def serializador_estado() -> SerializadorEstado:
    return SerializadorEstado()


def _es_sobre(obj: Any) -> bool:
    return isinstance(obj, dict) and obj.get("lc") in (1, 2) and obj.get("type") == "constructor"


def _clase_saver() -> type:
    from langgraph.checkpoint.redis.aio import AsyncRedisSaver

    class AsyncRedisSaverEstado(AsyncRedisSaver):
        """`AsyncRedisSaver` que no se traga el fallo al reconstruir un modelo del estado.

        Al leer los canales, el saver captura cualquier excepcion del serializador, la registra
        y devuelve el sobre crudo: el estado tendria un dict donde se espera p. ej. `Rutina`.
        `ModeloNoReconstruible` se propaga; el resto de sobres siguen la ruta del saver.
        """

        def _recursive_deserialize(self, obj: Any) -> Any:
            if _es_sobre(obj) and hasattr(self.serde, "_revive_if_needed"):
                try:
                    return self.serde._revive_if_needed(obj)
                except ModeloNoReconstruible:
                    raise
                except Exception:
                    pass  # la ruta del saver lo reintenta y registra el error
            return super()._recursive_deserialize(obj)

    return AsyncRedisSaverEstado


@asynccontextmanager
async def abrir_checkpointer_redis(redis_url: str) -> AsyncIterator[Any]:
    """`AsyncRedisSaver` de produccion, con el serializador del estado."""
    async with _clase_saver().from_conn_string(redis_url) as saver:
        # AsyncRedisSaver no acepta `serde` en su constructor: se sustituye antes de usarlo
        saver.serde = serializador_estado()
        await saver.asetup()
        yield saver
