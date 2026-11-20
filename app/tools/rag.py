"""Herramienta de recuperación sobre las guías técnicas de piña (Firestore kNN)."""

from __future__ import annotations

import os
from functools import lru_cache

from google import genai
from google.cloud import firestore
from google.cloud.firestore_v1.base_vector_query import DistanceMeasure
from google.cloud.firestore_v1.vector import Vector
from google.genai import types

COLLECTION = "chunks"
EMBED_MODEL = "gemini-embedding-001"
DIM = 768
# Distancia coseno: 0 = idéntico, 2 = opuesto. Ajusta tras ver resultados reales.
MAX_DISTANCE = float(os.getenv("RAG_MAX_DISTANCE", "0.45"))
MIN_FRAGMENTOS = 2


@lru_cache(maxsize=1)
def _clients() -> tuple[genai.Client, firestore.Client]:
    project = os.environ["GOOGLE_CLOUD_PROJECT"]
    location = os.getenv("EMBED_LOCATION", "us-central1")
    return (
        genai.Client(vertexai=True, project=project, location=location),
        firestore.Client(project=project),
    )


def buscar_conocimiento(pregunta: str, k: int = 5) -> dict:
    """Busca en las guías técnicas de producción de piña los fragmentos más relevantes.

    Úsala antes que cualquier otra fuente para preguntas agronómicas: variedades,
    densidad de siembra, fertilización, inducción floral, plagas, enfermedades y cosecha.

    Args:
        pregunta: La pregunta del usuario, en español o inglés.
        k: Número máximo de fragmentos a devolver (1 a 8).

    Returns:
        Un diccionario con:
        - fragmentos: lista de {texto, titulo, pagina, url, distancia}.
        - suficiente: False si hay menos de 2 fragmentos relevantes; en ese caso
          conviene complementar con búsqueda web.
    """
    genai_client, db = _clients()
    k = max(1, min(k, 8))

    emb = genai_client.models.embed_content(
        model=EMBED_MODEL,
        contents=pregunta,
        config=types.EmbedContentConfig(
            task_type="RETRIEVAL_QUERY",
            output_dimensionality=DIM,
        ),
    ).embeddings[0].values

    query = db.collection(COLLECTION).find_nearest(
        vector_field="embedding",
        query_vector=Vector(emb),
        distance_measure=DistanceMeasure.COSINE,
        limit=k,
        distance_result_field="distancia",
    )

    fragmentos = []
    for doc in query.get():
        d = doc.to_dict()
        if d["distancia"] > MAX_DISTANCE:
            continue
        fragmentos.append(
            {
                "texto": d["texto"],
                "titulo": d["titulo"],
                "pagina": d["pagina"],
                "url": d.get("url", ""),
                "distancia": round(d["distancia"], 3),
            }
        )

    return {"fragmentos": fragmentos, "suficiente": len(fragmentos) >= MIN_FRAGMENTOS}
