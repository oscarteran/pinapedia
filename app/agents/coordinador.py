"""Agente raíz: detecta la intención y transfiere al especialista adecuado."""

from google.adk.agents import Agent

from app.agents.agronomo import agronomo
from app.config.settings import MODEL, load_prompt

coordinador = Agent(
    name="coordinador",
    model=MODEL,
    description="Punto de entrada de PiñaPedia; enruta cada pregunta al especialista.",
    instruction=load_prompt("coordinador"),
    # El sábado se suman planificador y mercado_clima.
    sub_agents=[agronomo],
)