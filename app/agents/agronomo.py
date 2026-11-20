"""Especialista agronómico: responde con las guías técnicas (RAG) y la web como respaldo."""

from google.adk.agents import Agent
from google.adk.tools.agent_tool import AgentTool

from app.agents.buscadores import buscador_web
from app.config.settings import MODEL, load_prompt
from app.tools.rag import buscar_conocimiento

agronomo = Agent(
    name="agronomo",
    model=MODEL,
    description=(
        "Especialista en el cultivo de piña: variedades, siembra, densidad, "
        "fertilización, inducción floral, plagas, enfermedades y cosecha. "
        "Responde preguntas técnicas citando sus fuentes."
    ),
    instruction=load_prompt("agronomo"),
    tools=[buscar_conocimiento, AgentTool(agent=buscador_web)],
)