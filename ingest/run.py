"""Ingesta de PDFs a Firestore con embeddings de Vertex AI.

Idempotente: cada fragmento usa como ID un hash de (doc_id, página, texto),
así que correrlo dos veces no duplica ni vuelve a pagar embeddings.

Uso (desde la raíz del repo):
    uv run --env-file app/.env python -m ingest.run
"""

from __future__ import annotations

import hashlib
import os
from pathlib import Path

import fitz  # PyMuPDF
import yaml
from google import genai
from google.cloud import firestore
from google.cloud.firestore_v1.vector import Vector
from google.genai import types

ROOT = Path(__file__).resolve().parent.parent
SOURCES = ROOT / "data" / "sources.yaml"

COLLECTION = "chunks"
EMBED_MODEL = "gemini-embedding-001"
DIM = 768
CHUNK_CHARS = 3000  # ~800 tokens en español
OVERLAP = 400  # ~100 tokens
MIN_CHARS = 200  # descarta páginas casi vacías (portadas, índices)


def chunk_text(text: str) -> list[str]:
    """Normaliza espacios y corta en ventanas con traslape."""
    text = " ".join(text.split())
    if not text:
        return []
    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = min(start + CHUNK_CHARS, len(text))
        chunks.append(text[start:end])
        if end == len(text):
            break
        start = end - OVERLAP
    return chunks


def embed(client: genai.Client, text: str) -> list[float]:
    resp = client.models.embed_content(
        model=EMBED_MODEL,
        contents=text,
        config=types.EmbedContentConfig(
            task_type="RETRIEVAL_DOCUMENT",
            output_dimensionality=DIM,
        ),
    )
    return resp.embeddings[0].values


def main() -> None:
    project = os.environ["GOOGLE_CLOUD_PROJECT"]
    location = os.getenv("EMBED_LOCATION", "us-central1")

    client = genai.Client(vertexai=True, project=project, location=location)
    db = firestore.Client(project=project)
    col = db.collection(COLLECTION)

    sources = yaml.safe_load(SOURCES.read_text(encoding="utf-8"))
    nuevos = existentes = 0

    for src in sources:
        pdf_path = ROOT / src["archivo"]
        pdf = fitz.open(pdf_path)
        doc_nuevos = 0

        for page_num, page in enumerate(pdf, start=1):
            for chunk in chunk_text(page.get_text()):
                if len(chunk) < MIN_CHARS:
                    continue

                key = f"{src['doc_id']}|{page_num}|{chunk}"
                chunk_id = hashlib.sha256(key.encode("utf-8")).hexdigest()[:32]
                ref = col.document(chunk_id)

                if ref.get().exists:
                    existentes += 1
                    continue

                ref.set(
                    {
                        "texto": chunk,
                        "embedding": Vector(embed(client, chunk)),
                        "doc_id": src["doc_id"],
                        "titulo": src["titulo"],
                        "pagina": page_num,
                        "url": src.get("url", ""),
                        "idioma": src.get("idioma", "es"),
                    }
                )
                nuevos += 1
                doc_nuevos += 1

        print(f"{src['doc_id']}: {len(pdf)} páginas, {doc_nuevos} fragmentos nuevos")

    print(f"Listo: {nuevos} nuevos, {existentes} ya existían.")


if __name__ == "__main__":
    main()