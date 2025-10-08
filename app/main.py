from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from .routes.pages import router as pages_router
from .routes.ws import router as ws_router
from .services.timer import start_timer_task
from .core.db import init_db

BASE_DIR = Path(__file__).resolve().parent        # .../app
STATIC_DIR = BASE_DIR / "static"                  # .../app/static

app = FastAPI()

# Статика монтируется по абсолютному пути — не зависит от CWD
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Роуты
app.include_router(pages_router)
app.include_router(ws_router)

# Быстрый healthcheck, чтобы проверить что сервер жив
@app.get("/health")
async def health():
    return {"status": "ok"}

@app.on_event("startup")
async def _startup():
    init_db()
    start_timer_task()
