"""Prueba rápida de recuperación.

Uso: uv run --env-file app/.env python -m scripts.probar_rag
"""

from app.tools.rag import buscar_conocimiento

PREGUNTAS = [
    "¿Cuándo se hace la inducción floral en piña MD2?",
    #"¿Qué densidad de siembra se recomienda por hectárea?",
    #"How do I control mealybugs in pineapple?",
]

for p in PREGUNTAS:
    r = buscar_conocimiento(p)
    print(f"\n=== {p}  (suficiente={r['suficiente']})")
    for f in r["fragmentos"]:
        print(f"  [{f['distancia']}] {f['titulo']} p.{f['pagina']}: {f['texto'][:120]}...")