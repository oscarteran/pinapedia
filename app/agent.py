import os
from google.adk.agents import Agent

root_agent = Agent(
    name        = "coordinador",
    model       = os.getenv("PINAPEDIA_MODEL", "gemini-3.5-flash-lite"),
    description = "Asistente experto en producción de piña.",
    instruction = (
        "Eres PiñaPedia, un asistente experto en el cultivo de piña. "
        "Responde siempre en el idioma en que te pregunten."
    ),
)