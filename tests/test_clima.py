"""Prueba pronostico_clima sin red: se simulan las respuestas de Open-Meteo."""

import httpx

from app.tools import clima


class _Resp:
    def __init__(self, data):
        self._data = data

    def raise_for_status(self):
        pass

    def json(self):
        return self._data


GEO = {
    "results": [
        {"name": "Loma Bonita", "admin1": "Oaxaca", "latitude": 18.1, "longitude": -95.88},
    ]
}
FORECAST = {
    "daily": {
        "time": ["2026-11-21", "2026-11-22"],
        "precipitation_sum": [0.0, 12.5],
        "precipitation_probability_max": [10, 80],
        "temperature_2m_max": [30.1, 27.4],
        "temperature_2m_min": [20.3, 21.0],
        "wind_speed_10m_max": [12.0, 25.5],
    }
}


def test_pronostico_ok(monkeypatch):
    def fake_get(url, params=None, timeout=None):
        return _Resp(GEO if url == clima.GEOCODING_URL else FORECAST)

    monkeypatch.setattr(clima.httpx, "get", fake_get)
    r = clima.pronostico_clima("Loma Bonita, Oaxaca")
    assert r["status"] == "ok"
    assert r["ubicacion"] == "Loma Bonita, Oaxaca"
    assert r["dias"][1]["lluvia_mm"] == 12.5


def test_localidad_no_encontrada(monkeypatch):
    monkeypatch.setattr(clima.httpx, "get", lambda *a, **k: _Resp({"results": []}))
    assert clima.pronostico_clima("Lugar Inexistente")["status"] == "error"


def test_servicio_caido(monkeypatch):
    def boom(*a, **k):
        raise httpx.ConnectError("sin red")

    monkeypatch.setattr(clima.httpx, "get", boom)
    assert clima.pronostico_clima("Loma Bonita")["status"] == "error"