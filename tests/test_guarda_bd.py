from tests.guarda_bd import resolver_url_pruebas


def test_sin_variable_se_omite():
    url, motivo = resolver_url_pruebas({})
    assert url is None and "TEST_DATABASE_URL" in motivo


def test_nombre_sin_sufijo_test_se_omite():
    url, motivo = resolver_url_pruebas(
        {"TEST_DATABASE_URL": "postgresql+asyncpg://u:secreto@localhost:5432/coach"}
    )
    assert url is None and "_test" in motivo and "secreto" not in motivo


def test_nombre_con_sufijo_test_se_acepta():
    u = "postgresql+asyncpg://u:p@localhost:5432/coach_test"
    assert resolver_url_pruebas({"TEST_DATABASE_URL": u}) == (u, None)
