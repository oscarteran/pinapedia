"""Especialista en planeación: calendario de labores y costos (herramientas deterministas)."""

from google.adk.agents import Agent

from app.config.settings import MODEL, load_prompt
from app.tools.calendario import generar_calendario
from app.tools.costos import estimar_costos

planificador = Agent(
    name="planificador",
    model=MODEL,
    description=(
        "Planea el cultivo de piña: arma el calendario de labores a partir de la "
        "fecha de siembra y estima costos de establecimiento por hectárea."
    ),
    instruction=load_prompt("planificador"),
    tools=[generar_calendario, estimar_costos],
)