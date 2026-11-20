"""Configuración central: modelos y rutas, leída de variables de entorno."""

from __future__ import annotations

import os
from pathlib import Path

APP_DIR = Path(__file__).resolve().parent.parent
PROMPTS_DIR = APP_DIR / "prompts"

# Modelo principal de los agentes y modelo ligero para los buscadores.
MODEL = os.getenv("PINAPEDIA_MODEL", "gemini-3.5-flash-lite")
MODEL_LITE = os.getenv("PINAPEDIA_MODEL_LITE", MODEL)


def load_prompt(name: str) -> str:
    """Lee app/prompts/<name>.md.

    Ojo: ADK interpreta {llaves} en las instrucciones como variables de estado,
    así que los prompts no deben llevar llaves literales.
    """
    return (PROMPTS_DIR / f"{name}.md").read_text(encoding="utf-8")