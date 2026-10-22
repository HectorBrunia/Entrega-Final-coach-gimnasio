from pydantic import BaseModel

from app.domain.modelos import Ejercicio, Rutina


class EntradaVolumen(BaseModel):
    rutina: Rutina
    catalogo: dict[str, Ejercicio]


class SalidaVolumen(BaseModel):
    series_por_musculo: dict[str, int]
