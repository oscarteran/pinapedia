"""Middleware de protección para la demo pública.

1. Lista blanca de rutas: ADK expone muchos endpoints de desarrollo (evals, deploy,
   artefactos, sesiones de otros usuarios). En producción solo se permiten los que
   usa el chat; el resto responde 404.
2. Límite de uso por IP y tope global diario sobre /run_sse (la ruta que gasta tokens).
3. Validación del cuerpo: app correcta y mensaje de longitud acotada.

Es un middleware ASGI puro para poder leer el cuerpo y "re-enviarlo" a ADK.
Funciona en memoria porque Cloud Run corre con max-instances=1.
"""

from __future__ import annotations

import json
import os
import re
import time
from collections import defaultdict, deque

APP_NAME = "app"

DEV_MODE = os.getenv("GUARD_DISABLED", "false").lower() == "true"
MAX_CHARS = int(os.getenv("MAX_MESSAGE_CHARS", "1000"))
MAX_BODY_BYTES = 16_000
PER_IP_HOUR = int(os.getenv("RATE_PER_IP_HOUR", "10"))
PER_IP_DAY = int(os.getenv("RATE_PER_IP_DAY", "30"))
GLOBAL_DAY = int(os.getenv("RATE_GLOBAL_DAY", "300"))

ALLOWED = [
    ("GET", re.compile(r"^/$")),
    ("GET", re.compile(r"^/static/[\w./-]+$")),
    ("GET", re.compile(r"^/health$")),
    ("POST", re.compile(rf"^/apps/{APP_NAME}/users/[\w-]{{8,64}}/sessions$")),
    ("POST", re.compile(r"^/run_sse$")),
]

HOUR, DAY = 3600, 86400


class RateLimiter:
    """Ventanas deslizantes en memoria: por IP (hora y día) y global (día)."""

    def __init__(self, per_hour: int, per_day: int, global_day: int, clock=time.time):
        self.per_hour, self.per_day, self.global_day = per_hour, per_day, global_day
        self.clock = clock
        self.by_ip: dict[str, deque[float]] = defaultdict(deque)
        self.all: deque[float] = deque()

    @staticmethod
    def _trim(q: deque[float], now: float, window: int) -> None:
        while q and q[0] <= now - window:
            q.popleft()

    def hit(self, ip: str) -> tuple[bool, str]:
        now = self.clock()
        q = self.by_ip[ip]
        self._trim(q, now, DAY)
        self._trim(self.all, now, DAY)

        if len(self.all) >= self.global_day:
            return False, "La demo alcanzó su límite diario. Intenta mañana."
        if len(q) >= self.per_day:
            return False, "Alcanzaste el límite diario de preguntas."
        if sum(1 for t in q if t > now - HOUR) >= self.per_hour:
            return False, "Alcanzaste el límite de preguntas por hora."

        q.append(now)
        self.all.append(now)
        return True, ""


def is_allowed(method: str, path: str) -> bool:
    return any(method == m and rx.match(path) for m, rx in ALLOWED)


def client_ip(scope) -> str:
    for name, value in scope.get("headers", []):
        if name == b"x-forwarded-for":
            return value.decode().split(",")[0].strip()
    client = scope.get("client")
    return client[0] if client else "desconocida"


def message_text(data: dict) -> str:
    msg = data.get("new_message") or data.get("newMessage") or {}
    return "".join(p.get("text", "") for p in msg.get("parts", []) if isinstance(p, dict))


async def _send_json(send, status: int, payload: dict) -> None:
    body = json.dumps(payload, ensure_ascii=False).encode()
    await send(
        {
            "type": "http.response.start",
            "status": status,
            "headers": [(b"content-type", b"application/json; charset=utf-8")],
        }
    )
    await send({"type": "http.response.body", "body": body})


class GuardMiddleware:
    def __init__(self, app, limiter: RateLimiter | None = None):
        self.app = app
        self.limiter = limiter or RateLimiter(PER_IP_HOUR, PER_IP_DAY, GLOBAL_DAY)

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http" or DEV_MODE:
            return await self.app(scope, receive, send)

        method, path = scope["method"], scope["path"]
        if not is_allowed(method, path):
            return await _send_json(send, 404, {"detail": "Not Found"})

        if path != "/run_sse":
            return await self.app(scope, receive, send)

        ok, reason = self.limiter.hit(client_ip(scope))
        if not ok:
            return await _send_json(send, 429, {"detail": reason})

        body, more = b"", True
        while more:
            msg = await receive()
            body += msg.get("body", b"")
            more = msg.get("more_body", False)
            if len(body) > MAX_BODY_BYTES:
                return await _send_json(send, 413, {"detail": "Solicitud demasiado grande."})

        try:
            data = json.loads(body or b"{}")
        except ValueError:
            return await _send_json(send, 400, {"detail": "JSON inválido."})

        if (data.get("app_name") or data.get("appName")) != APP_NAME:
            return await _send_json(send, 404, {"detail": "Not Found"})
        text = message_text(data)
        if not text.strip():
            return await _send_json(send, 400, {"detail": "El mensaje está vacío."})
        if len(text) > MAX_CHARS:
            return await _send_json(
                send, 413, {"detail": f"El mensaje supera {MAX_CHARS} caracteres."}
            )

        sent = False

        async def replay():
            nonlocal sent
            if not sent:
                sent = True
                return {"type": "http.request", "body": body, "more_body": False}
            return await receive()

        return await self.app(scope, replay, send)