"""Глобальное состояние приложения и утилиты широковещательной отправки по WebSocket."""

import asyncio
import time
from pathlib import Path

from app.core.config import cfg

# Папка логов
LOG_DIR = Path("wsp-timer-data") / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / "wsp-timer.log"


class AppState:
    """Хранилище текущего состояния приложения (простая модель без потоковой безопасности)."""

    timer_total_seconds: int = 60
    remaining_seconds: int = 60
    is_running: bool = False

    timer_clients: list = []
    control_clients: list = []
    timer_cfg_clients: list = []

    oauth_client_id: str | None = cfg.da_client_id or None
    oauth_client_secret: str | None = cfg.da_client_secret or None
    oauth_redirect_uri: str = cfg.oauth_redirect_uri
    oauth_access_token: str | None = None

    rub_to_sec: float = float(cfg.default_rub_to_sec)
    fraction_carry: float = 0.0
    timer_text_color: str = "black"

    donation_task: asyncio.Task | None = None
    lock = asyncio.Lock()


# Единый экземпляр
state = AppState()


def _write_log(message: str) -> None:
    """Записать строку в лог-файл с таймстампом."""
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{ts}] {message}\n")


async def broadcast_timer(msg: str) -> None:
    dead = []
    for ws in state.timer_clients:
        try:
            await ws.send_text(msg)
        except Exception:
            dead.append(ws)
    for ws in dead:
        state.timer_clients.remove(ws)


async def broadcast_control(msg: str) -> None:
    """Отправить сообщение всем клиентам панели управления и записать его в лог."""
    _write_log(msg)
    dead = []
    for ws in state.control_clients:
        try:
            await ws.send_text(msg)
        except Exception:
            dead.append(ws)
    for ws in dead:
        state.control_clients.remove(ws)


async def broadcast_timer_cfg(msg: str) -> None:
    dead = []
    for ws in state.timer_cfg_clients:
        try:
            await ws.send_text(msg)
        except Exception:
            dead.append(ws)
    for ws in dead:
        state.timer_cfg_clients.remove(ws)
