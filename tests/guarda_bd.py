from collections.abc import Mapping

from sqlalchemy.engine import make_url


def url_sin_credenciales(url: str) -> str:
    u = make_url(url)
    return f"{u.drivername}://{u.host}:{u.port}/{u.database}"


def resolver_url_pruebas(env: Mapping[str, str]) -> tuple[str | None, str | None]:
    """Devuelve (url, None) si es segura, o (None, motivo_de_skip)."""
    url = env.get("TEST_DATABASE_URL")
    if not url:
        return None, "TEST_DATABASE_URL no configurada: no se ejecutan pruebas de integracion"
    try:
        nombre = make_url(url).database or ""
    except Exception:
        return None, "TEST_DATABASE_URL invalida"
    if not nombre.endswith("_test"):
        return None, "el nombre de la base de pruebas debe terminar en _test"
    return url, None
