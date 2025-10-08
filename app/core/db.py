import os, sqlite3, time
from typing import Optional
from app.core.config import cfg
from app.core.state import state

DB_PATH = os.getenv("APP_DB_PATH", "app_data.db")

def _conn():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def init_db():
    conn = _conn()
    try:
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        """)
        conn.commit()

        # defaults
        if get_setting("rub_to_sec") is None:
            set_setting("rub_to_sec", str(cfg.default_rub_to_sec))
        if get_setting("timer_color") is None:
            set_setting("timer_color", "black")

        # mirror to state
        rub = get_setting("rub_to_sec")
        if rub is not None:
            state.rub_to_sec = float(rub)

        color = get_setting("timer_color")
        if color in ("black", "white"):
            state.timer_text_color = color

        at = get_setting("access_token")
        if at:
            state.oauth_access_token = at
    finally:
        conn.close()

def get_setting(key: str) -> Optional[str]:
    conn = _conn()
    try:
        cur = conn.cursor()
        cur.execute("SELECT value FROM settings WHERE key = ?", (key,))
        row = cur.fetchone()
        return row[0] if row else None
    finally:
        conn.close()

def set_setting(key: str, value: str) -> None:
    conn = _conn()
    try:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO settings(key, value) VALUES(?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            (key, value),
        )
        conn.commit()
    finally:
        conn.close()

# tokens helpers (как были)
def save_tokens(access_token: str, refresh_token: Optional[str], expires_in: Optional[int]):
    set_setting("access_token", access_token or "")
    if refresh_token is not None:
        set_setting("refresh_token", refresh_token or "")
    if expires_in is not None:
        expires_at = int(time.time()) + int(expires_in) - 30
        set_setting("token_expires_at", str(expires_at))

def load_tokens():
    return {
        "access_token": get_setting("access_token"),
        "refresh_token": get_setting("refresh_token"),
        "token_expires_at": int(get_setting("token_expires_at") or "0"),
    }
