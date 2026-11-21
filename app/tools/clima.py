"""Pronóstico del clima con Open-Meteo (gratis, sin API key)."""

from __future__ import annotations

import httpx

GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
TIMEOUT = 10.0


def pronostico_clima(lugar: str, pais: str = "MX") -> dict:
    """Obtiene el pronóstico del clima de los próximos 7 días para una localidad.

    Úsala cuando el usuario pregunte si va a llover, qué temperatura hará o si el
    clima es adecuado para fertilizar, aplicar agroquímicos o cosechar.

    Args:
        lugar: Nombre de la localidad, por ejemplo "Loma Bonita" o "Isla, Veracruz".
        pais: Código de país ISO de 2 letras. Por defecto "MX".

    Returns:
        Un diccionario con status "ok", la ubicación encontrada y una lista diaria con
        lluvia (mm), probabilidad de lluvia (%), temperaturas (°C) y viento máximo (km/h);
        o status "error" si no se encontró la localidad o falló el servicio.
    """
    nombre = lugar.split(",")[0].strip()
    if not nombre:
        return {"status": "error", "mensaje": "Indica el nombre de la localidad."}

    try:
        geo = httpx.get(
            GEOCODING_URL,
            params={"name": nombre, "count": 5, "language": "es", "countryCode": pais},
            timeout=TIMEOUT,
        )
        geo.raise_for_status()
        resultados = geo.json().get("results") or []
        if not resultados:
            return {"status": "error", "mensaje": f"No encontré la localidad '{lugar}'."}

        # Si el usuario dio estado ("Isla, Veracruz"), prioriza esa coincidencia.
        estado = lugar.split(",")[1].strip().lower() if "," in lugar else ""
        sitio = next(
            (r for r in resultados if estado and estado in (r.get("admin1") or "").lower()),
            resultados[0],
        )

        resp = httpx.get(
            FORECAST_URL,
            params={
                "latitude": sitio["latitude"],
                "longitude": sitio["longitude"],
                "daily": ",".join(
                    [
                        "precipitation_sum",
                        "precipitation_probability_max",
                        "temperature_2m_max",
                        "temperature_2m_min",
                        "wind_speed_10m_max",
                    ]
                ),
                "timezone": "auto",
                "forecast_days": 7,
            },
            timeout=TIMEOUT,
        )
        resp.raise_for_status()
        daily = resp.json()["daily"]
    except (httpx.HTTPError, KeyError, ValueError) as exc:
        return {"status": "error", "mensaje": f"El servicio de clima no respondió: {exc}"}

    dias = [
        {
            "fecha": daily["time"][i],
            "lluvia_mm": daily["precipitation_sum"][i],
            "prob_lluvia_pct": daily["precipitation_probability_max"][i],
            "temp_max_c": daily["temperature_2m_max"][i],
            "temp_min_c": daily["temperature_2m_min"][i],
            "viento_max_kmh": daily["wind_speed_10m_max"][i],
        }
        for i in range(len(daily["time"]))
    ]

    return {
        "status": "ok",
        "ubicacion": f"{sitio['name']}, {sitio.get('admin1', '')}".strip(", "),
        "dias": dias,
        "fuente": "Open-Meteo (open-meteo.com)",
    }