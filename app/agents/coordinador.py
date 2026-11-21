"""Agente raíz: detecta la intención y transfiere al especialista adecuado."""

from google.adk.agents import Agent

from app.agents.agronomo import agronomo
from app.agents.mercado_clima import mercado_clima
from app.agents.planificador import planificador
from app.config.settings import MODEL, load_prompt

coordinador = Agent(
    name="coordinador",
    model=MODEL,
    description="Punto de entrada de PiñaPedia; enruta cada pregunta al especialista.",
    instruction=load_prompt("coordinador"),
    sub_agents=[agronomo, planificador, mercado_clima],
)