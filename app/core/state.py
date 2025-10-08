"""Глобальное состояние приложения и утилиты широковещательной отправки по WebSocket."""

import asyncio
from typing import Optional

from app.core.config import cfg


class AppState:
    """Хранилище текущего состояния приложения (простая модель без потоковой безопасности)."""

    # Параметры таймера
    timer_total_seconds: int = 60
    remaining_seconds: int = 60
    is_running: bool = False

    # Подключённые WebSocket-клиенты
    timer_clients: list = []        # клиенты страницы таймера (/ws)
    control_clients: list = []      # клиенты панели управления (/control)
    timer_cfg_clients: list = []    # клиенты, слушающие изменения настроек таймера (/timer_cfg)

    # OAuth (текущие значения доступны для UI)
    oauth_client_id: Optional[str] = cfg.da_client_id or None
    oauth_client_secret: Optional[str] = cfg.da_client_secret or None
    oauth_redirect_uri: str = cfg.oauth_redirect_uri
    oauth_access_token: Optional[str] = None

    # Настройки таймера (из БД / по умолчанию)
    rub_to_sec: float = float(cfg.default_rub_to_sec)
    fraction_carry: float = 0.0
    timer_text_color: str = "black"  # "black" | "white"

    # Фоновые задачи и синхронизация
    donation_task: Optional[asyncio.Task] = None
    lock = asyncio.Lock()


# Единый экземпляр состояния
state = AppState()


async def broadcast_timer(msg: str) -> None:
    """Отправить сообщение всем подписчикам таймера; удалить оборванные соединения."""
    dead = []
    for ws in state.timer_clients:
        try:
            await ws.send_text(msg)
        except Exception:
            dead.append(ws)
    for ws in dead:
        state.timer_clients.remove(ws)


async def broadcast_control(msg: str) -> None:
    """Отправить сообщение всем клиентам панели управления; удалить оборванные соединения."""
    dead = []
    for ws in state.control_clients:
        try:
            await ws.send_text(msg)
        except Exception:
            dead.append(ws)
    for ws in dead:
        state.control_clients.remove(ws)


async def broadcast_timer_cfg(msg: str) -> None:
    """Отправить сообщение всем подписчикам настроек таймера; удалить оборванные соединения."""
    dead = []
    for ws in state.timer_cfg_clients:
        try:
            await ws.send_text(msg)
        except Exception:
            dead.append(ws)
    for ws in dead:
        state.timer_cfg_clients.remove(ws)
