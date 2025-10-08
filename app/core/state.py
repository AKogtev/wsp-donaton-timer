import asyncio
from typing import Optional
from app.core.config import cfg

class AppState:
    # Timer
    timer_total_seconds: int = 60
    remaining_seconds: int = 60
    is_running: bool = False

    # WS clients
    timer_clients: list = []       # /ws (время)
    control_clients: list = []     # /control (панель)
    timer_cfg_clients: list = []   # /timer_cfg (настройки таймера: цвет и т.п.)

    # OAuth / DA (runtime)
    oauth_client_id: Optional[str] = cfg.da_client_id or None
    oauth_client_secret: Optional[str] = cfg.da_client_secret or None
    oauth_redirect_uri: str = cfg.oauth_redirect_uri
    oauth_access_token: Optional[str] = None  # mirrored for UI

    # Settings
    rub_to_sec: float = float(cfg.default_rub_to_sec)
    fraction_carry: float = 0.0 
    timer_text_color: str = "black"  # new: "black" | "white"

    donation_task: Optional[asyncio.Task] = None
    lock = asyncio.Lock()

state = AppState()

async def broadcast_timer(msg: str):
    dead = []
    for ws in state.timer_clients:
        try:
            await ws.send_text(msg)
        except Exception:
            dead.append(ws)
    for ws in dead:
        state.timer_clients.remove(ws)

async def broadcast_control(msg: str):
    dead = []
    for ws in state.control_clients:
        try:
            await ws.send_text(msg)
        except Exception:
            dead.append(ws)
    for ws in dead:
        state.control_clients.remove(ws)

async def broadcast_timer_cfg(msg: str):
    dead = []
    for ws in state.timer_cfg_clients:
        try:
            await ws.send_text(msg)  # шлём просто "black" или "white"
        except Exception:
            dead.append(ws)
    for ws in dead:
        state.timer_cfg_clients.remove(ws)
