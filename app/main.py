"""Основной модуль FastAPI-приложения: роуты, статика, запуск фоновых задач."""

from pathlib import Path
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.routes.pages import router as pages_router
from app.routes.ws import router as ws_router
from app.services.timer import start_timer_task
from app.core.db import init_db

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"

app = FastAPI()

# Подключение статики
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Роуты
app.include_router(pages_router)
app.include_router(ws_router)


@app.get("/health")
async def health():
    """Простой healthcheck для проверки состояния сервера."""
    return {"status": "ok"}


@app.on_event("startup")
async def _startup():
    """Инициализация при старте: подготовка БД и запуск фонового таймера."""
    init_db()
    start_timer_task()
