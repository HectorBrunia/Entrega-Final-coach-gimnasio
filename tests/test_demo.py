"""Modo demo (python scripts/demo.py): sin Docker, sin red y sin clave de Gemini."""

import subprocess
import sys

from app.demo.escenarios import LINEA_FINAL_OK, TITULO, ejecutar_demo
from tests.conftest import RAIZ


async def test_demo_completa_los_cinco_escenarios():
    lineas: list[str] = []
    r = await ejecutar_demo(lineas.append)
    fallos = [d for d, ok in r.comprobaciones if not ok]
    assert r.ok, fallos
    assert TITULO in lineas and lineas[-1] == LINEA_FINAL_OK
    # 1: rutina inicial con ids del catalogo
    assert "Tu rutina (versión 1)" in r.respuestas["rutina_inicial"]
    # 2: filtro determinista del hombro
    assert set(r.retirados_por_lesion) == {
        "Barbell_Squat", "Barbell_Bench_Press_-_Medium_Grip", "Bent_Over_Barbell_Row",
        "Standing_Military_Press"}
    assert r.rechazados_por_seguridad == ["Dumbbell_Shoulder_Press"]
    # 3: HITL reanudado
    assert "profesional" in r.respuestas["tras_revision"]
    # 4: urgencia toracica
    assert "112" in r.respuestas["pecho"]
    # 5: fuera de alcance sin plan
    assert "Tu rutina" not in r.respuestas["fuera_de_alcance"]


def test_script_de_demo_termina_con_codigo_0():
    r = subprocess.run([sys.executable, "scripts/demo.py"], cwd=RAIZ, capture_output=True,
                       timeout=300)
    salida = r.stdout.decode("utf-8")
    assert r.returncode == 0, salida + r.stderr.decode("utf-8", "replace")
    assert "MODO DEMO" in salida
    assert salida.strip().splitlines()[-1] == LINEA_FINAL_OK
