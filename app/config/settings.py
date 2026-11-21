"""Configuración central: modelos, rutas y parámetros en YAML."""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

import yaml

APP_DIR = Path(__file__).resolve().parent.parent
PROMPTS_DIR = APP_DIR / "prompts"
CONFIG_DIR = APP_DIR / "config"

# Modelo principal de los agentes y modelo ligero para los buscadores.
MODEL = os.getenv("PINAPEDIA_MODEL", "gemini-3.5-flash-lite")
MODEL_LITE = os.getenv("PINAPEDIA_MODEL_LITE", MODEL)


def load_prompt(name: str) -> str:
    """Lee app/prompts/<name>.md.

    Ojo: ADK interpreta {llaves} en las instrucciones como variables de estado,
    así que los prompts no deben llevar llaves literales.
    """
    return (PROMPTS_DIR / f"{name}.md").read_text(encoding="utf-8")


@lru_cache(maxsize=None)
def load_yaml(name: str) -> dict:
    """Lee app/config/<name>.yaml (cacheado: se lee una vez por proceso)."""
    return yaml.safe_load((CONFIG_DIR / f"{name}.yaml").read_text(encoding="utf-8"))