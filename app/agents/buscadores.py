"""Agentes de búsqueda web.

google_search es una herramienta integrada de Gemini: se aísla en su propio agente
y los especialistas la usan envuelta en AgentTool.
"""

from google.adk.agents import Agent
from google.adk.tools import google_search

from app.config.settings import MODEL_LITE, load_prompt

buscador_web = Agent(
    name="buscador_web",
    model=MODEL_LITE,
    description=(
        "Busca en la web información técnica sobre producción de piña cuando "
        "las guías técnicas internas no alcanzan. Devuelve hallazgos con fuentes."
    ),
    instruction=load_prompt("buscador_web"),
    tools=[google_search],
)

buscador_precios = Agent(
    name="buscador_precios",
    model=MODEL_LITE,
    description=(
        "Busca precios recientes de la piña en centrales de abasto y mercados de México, "
        "siempre con fuente y fecha."
    ),
    instruction=load_prompt("buscador_precios"),
    tools=[google_search],
)