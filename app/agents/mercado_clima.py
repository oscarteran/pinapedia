"""Especialista en clima y mercado: pronóstico (Open-Meteo) y precios (búsqueda web)."""

from google.adk.agents import Agent
from google.adk.tools.agent_tool import AgentTool

from app.agents.buscadores import buscador_precios
from app.config.settings import MODEL, load_prompt
from app.tools.clima import pronostico_clima

mercado_clima = Agent(
    name="mercado_clima",
    model=MODEL,
    description=(
        "Consulta el pronóstico del clima de una localidad y referencias de precios "
        "de mercado de la piña."
    ),
    instruction=load_prompt("mercado_clima"),
    tools=[pronostico_clima, AgentTool(agent=buscador_precios)],
)