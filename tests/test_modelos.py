import pytest
from pydantic import ValidationError
from app.domain.modelos import Perfil, EntrenoRegistro, Nivel
from uuid import uuid4
from datetime import date

def test_perfil_rechaza_dias_fuera_de_rango():
    with pytest.raises(ValidationError):
        Perfil(usuario_id=uuid4(), objetivo="masa", dias_disponibles=8, equipo=[], nivel=Nivel.principiante)

def test_entreno_rechaza_rpe_fuera_de_rango():
    with pytest.raises(ValidationError):
        EntrenoRegistro(usuario_id=uuid4(), fecha=date(2026,10,1), ejercicio_id="press_banca",
                        series=3, repeticiones=8, peso_kg=20, rpe=11, notas=None)

def test_nivel_rechaza_valor_desconocido():
    with pytest.raises(ValidationError):
        Perfil(usuario_id=uuid4(), objetivo="masa", dias_disponibles=3, equipo=[], nivel="experto")
