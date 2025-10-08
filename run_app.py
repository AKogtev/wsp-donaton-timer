# run_app.py
import os, sys, asyncio

# Windows: стабильный event loop
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

# >>> КЛЮЧ: импортируем FastAPI-приложение ЯВНО <<<
from app.main import app as fastapi_app

def main():
    import uvicorn
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(
        fastapi_app,                 # <-- передаём объект, а не строку "app.main:app"
        host="0.0.0.0",
        port=port,
        log_level="info",
        reload=False,
    )

if __name__ == "__main__":
    main()
