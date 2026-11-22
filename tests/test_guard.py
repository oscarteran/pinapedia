"""Pruebas del middleware de protección (sin llamar a Gemini)."""

import json

from fastapi import FastAPI
from fastapi.testclient import TestClient

from server.guard import GuardMiddleware, RateLimiter


def _app(limiter=None):
    inner = FastAPI()

    @inner.get("/health")
    def health():
        return {"status": "ok"}

    @inner.post("/run_sse")
    async def run_sse(body: dict):
        return {"echo": body["new_message"]["parts"][0]["text"]}

    @inner.get("/dev/apps/app/eval_sets")
    def dev():
        return {"secret": True}

    inner.add_middleware(GuardMiddleware, limiter=limiter or RateLimiter(100, 100, 100))
    return TestClient(inner)


def _payload(text="hola", app="app"):
    return {
        "app_name": app,
        "user_id": "u-12345678",
        "session_id": "s1",
        "new_message": {"role": "user", "parts": [{"text": text}]},
    }


def test_ruta_permitida():
    assert _app().get("/health").status_code == 200


def test_ruta_de_desarrollo_bloqueada():
    assert _app().get("/dev/apps/app/eval_sets").status_code == 404


def test_cuerpo_se_reenvia_intacto():
    r = _app().post(
        "/run_sse",
        content=json.dumps(_payload("¿cuándo cosecho?")),
        headers={"content-type": "application/json"},
    )
    assert r.status_code == 200
    assert r.json() == {"echo": "¿cuándo cosecho?"}


def test_mensaje_demasiado_largo():
    assert _app().post("/run_sse", json=_payload("x" * 1001)).status_code == 413


def test_mensaje_vacio_y_app_ajena():
    c = _app()
    assert c.post("/run_sse", json=_payload("   ")).status_code == 400
    assert c.post("/run_sse", json=_payload(app="otra")).status_code == 404


def test_limite_por_ip():
    c = _app(RateLimiter(per_hour=2, per_day=10, global_day=100))
    assert c.post("/run_sse", json=_payload()).status_code == 200
    assert c.post("/run_sse", json=_payload()).status_code == 200
    assert c.post("/run_sse", json=_payload()).status_code == 429


def test_ventana_deslizante_libera_cupo():
    now = [0.0]
    lim = RateLimiter(per_hour=1, per_day=10, global_day=100, clock=lambda: now[0])
    assert lim.hit("1.1.1.1")[0]
    assert not lim.hit("1.1.1.1")[0]
    now[0] = 3601
    assert lim.hit("1.1.1.1")[0]


def test_tope_global():
    lim = RateLimiter(per_hour=10, per_day=10, global_day=2)
    assert lim.hit("a")[0] and lim.hit("b")[0]
    assert not lim.hit("c")[0]