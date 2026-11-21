"""Calendario de labores: función determinista a partir de config/cultivo.yaml."""

from __future__ import annotations

from datetime import date, timedelta

from app.config.settings import load_yaml


def generar_calendario(fecha_siembra: str, variedad: str = "MD2") -> dict:
    """Genera el calendario de labores del cultivo de piña a partir de la fecha de siembra.

    Usa esta herramienta siempre que el usuario pregunte qué labores le tocan,
    cuándo fertilizar, cuándo inducir la floración o cuándo cosechará.

    Args:
        fecha_siembra: Fecha de siembra en formato AAAA-MM-DD (por ejemplo 2026-03-15).
        variedad: Variedad cultivada: "MD2" o "Cayena Lisa". Por defecto "MD2".

    Returns:
        Un diccionario con status "ok" y la lista de labores con su fecha estimada,
        o status "error" con un mensaje que explica qué dato falta o es inválido.
    """
    cfg = load_yaml("cultivo")
    variedades = cfg["variedades"]

    match = next((v for v in variedades if v.lower() == variedad.strip().lower()), None)
    if match is None:
        return {
            "status": "error",
            "mensaje": f"Variedad '{variedad}' no reconocida.",
            "variedades_disponibles": list(variedades),
        }

    try:
        inicio = date.fromisoformat(fecha_siembra.strip())
    except ValueError:
        return {
            "status": "error",
            "mensaje": "La fecha debe tener formato AAAA-MM-DD, por ejemplo 2026-03-15.",
        }

    hoy = date.today()
    labores = []
    for labor in variedades[match]["labores"]:
        fecha = inicio + timedelta(days=labor["dias"])
        labores.append(
            {
                "labor": labor["nombre"],
                "dias_despues_siembra": labor["dias"],
                "fecha_estimada": fecha.isoformat(),
                "estado": "pasada" if fecha < hoy else "próxima",
            }
        )

    return {
        "status": "ok",
        "variedad": match,
        "fecha_siembra": inicio.isoformat(),
        "labores": labores,
        "nota": "Fechas estimadas; dependen del clima, el tamaño de la planta y el manejo.",
        "fuente": cfg.get("fuente", ""),
    }