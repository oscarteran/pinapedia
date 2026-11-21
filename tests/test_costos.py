import pytest

from app.config.settings import load_yaml
from app.tools.costos import estimar_costos


def test_costos_escalan_con_hectareas():
    una = estimar_costos(1)
    tres = estimar_costos(3)
    assert una["status"] == tres["status"] == "ok"
    assert tres["total"] == pytest.approx(una["total"] * 3)
    assert tres["costo_por_hectarea"] == pytest.approx(una["costo_por_hectarea"])


def test_densidad_default_y_personalizada():
    default = load_yaml("costos")["densidad_default_plantas_ha"]
    assert estimar_costos(1)["densidad_plantas_ha"] == default
    alta = estimar_costos(1, densidad_plantas_ha=default + 10000)
    assert alta["total"] > estimar_costos(1)["total"]


def test_total_es_suma_del_desglose():
    r = estimar_costos(2.5)
    assert r["total"] == pytest.approx(sum(d["monto"] for d in r["desglose"]))


@pytest.mark.parametrize("ha", [0, -1, 5000])
def test_hectareas_invalidas(ha):
    assert estimar_costos(ha)["status"] == "error"