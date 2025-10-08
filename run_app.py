"""Точка входа для запуска FastAPI-приложения через uvicorn."""

import os
import sys
import asyncio

# На Windows задаём стабильный event loop
if sys.platform.startswith("win"):
    try:
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    except Exception:
        pass

# SSL для httpx внутри exe
try:
    import certifi

    os.environ.setdefault("SSL_CERT_FILE", certifi.where())
except Exception:
    pass

from app.main import app as fastapi_app


def main():
    """Запустить uvicorn-сервер с приложением FastAPI."""
    import uvicorn

    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(
        fastapi_app,
        host="0.0.0.0",
        port=port,
        log_level="info",
        reload=False,
    )


if __name__ == "__main__":
    main()
