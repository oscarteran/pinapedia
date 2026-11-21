"""Estimación de costos: función determinista a partir de config/costos.yaml."""

from __future__ import annotations

from app.config.settings import load_yaml


def estimar_costos(hectareas: float, densidad_plantas_ha: int | None = None) -> dict:
    """Estima el costo de establecer y llevar a cosecha un cultivo de piña.

    Usa esta herramienta siempre que el usuario pregunte cuánto cuesta sembrar,
    cuánto necesita invertir o el costo por hectárea. No calcules costos por tu cuenta.

    Args:
        hectareas: Superficie a sembrar, en hectáreas (mayor que 0).
        densidad_plantas_ha: Plantas por hectárea. Si no se indica, usa la densidad estándar.

    Returns:
        Un diccionario con status "ok", el desglose por concepto, el total y el
        costo por hectárea en MXN; o status "error" si algún dato es inválido.
    """
    cfg = load_yaml("costos")

    if hectareas is None or hectareas <= 0:
        return {"status": "error", "mensaje": "Las hectáreas deben ser mayores que 0."}
    if hectareas > 1000:
        return {"status": "error", "mensaje": "Para más de 1,000 ha consulta a un asesor."}

    densidad = densidad_plantas_ha or cfg["densidad_default_plantas_ha"]
    if densidad <= 0:
        return {"status": "error", "mensaje": "La densidad debe ser mayor que 0."}

    desglose = []
    for item in cfg["por_planta"]:
        monto = item["precio_unitario"] * densidad * hectareas
        desglose.append({"concepto": item["concepto"], "monto": round(monto, 2)})
    for item in cfg["por_hectarea"]:
        desglose.append({"concepto": item["concepto"], "monto": round(item["monto"] * hectareas, 2)})

    total = round(sum(d["monto"] for d in desglose), 2)

    return {
        "status": "ok",
        "moneda": cfg["moneda"],
        "hectareas": hectareas,
        "densidad_plantas_ha": densidad,
        "desglose": desglose,
        "total": total,
        "costo_por_hectarea": round(total / hectareas, 2),
        "vigencia": cfg.get("vigencia", ""),
        "nota": "Estimación ilustrativa; los costos reales varían por región y temporada.",
    }