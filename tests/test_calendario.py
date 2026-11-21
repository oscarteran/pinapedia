from app.tools.calendario import generar_calendario


def test_calendario_md2_ok():
    r = generar_calendario("2026-03-15", "MD2")
    assert r["status"] == "ok"
    assert r["labores"][0]["labor"] == "Siembra"
    assert r["labores"][0]["fecha_estimada"] == "2026-03-15"
    # Las fechas van en orden.
    fechas = [lab["fecha_estimada"] for lab in r["labores"]]
    assert fechas == sorted(fechas)


def test_variedad_sin_importar_mayusculas():
    r = generar_calendario("2026-03-15", "cayena lisa")
    assert r["status"] == "ok"
    assert r["variedad"] == "Cayena Lisa"


def test_fecha_invalida():
    r = generar_calendario("15/03/2026")
    assert r["status"] == "error"


def test_variedad_desconocida():
    r = generar_calendario("2026-03-15", "Perolera")
    assert r["status"] == "error"
    assert "MD2" in r["variedades_disponibles"]