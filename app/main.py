"""Основной модуль FastAPI-приложения: роуты, статика, запуск фоновых задач."""

import time
import asyncio
from pathlib import Path
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.routes.pages import router as pages_router
from app.routes.ws import router as ws_router
from app.services.timer import start_timer_task
from app.services.donationalerts import donation_manager
from app.core.db import init_db, load_runtime_state
from app.core.state import state

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
    """Инициализация при старте: подготовка БД, восстановление таймера и автозапуск донатов."""
    init_db()

    st = load_runtime_state()
    if st:
        rem = int(st.get("remaining_seconds", "60"))
        is_running = st.get("is_running", "0") == "1"
        fraction = float(st.get("fraction_carry", "0.0"))
        last_upd = int(st.get("last_update_at", "0"))

        if is_running and last_upd:
            diff = int(time.time()) - last_upd
            rem = max(rem - diff, 0)

        state.remaining_seconds = rem
        state.is_running = is_running and rem > 0
        state.fraction_carry = fraction

    start_timer_task()

    # Автозапуск donation listener, если всё есть
    if state.oauth_client_id and state.oauth_client_secret and state.oauth_access_token:
        state.donation_task = asyncio.create_task(donation_manager())
