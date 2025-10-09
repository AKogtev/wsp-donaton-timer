"""Работа с SQLite: хранение настроек и состояния таймера + OAuth-токены."""

import os
import sys
import time
import sqlite3
from pathlib import Path
from typing import Optional

from app.core.config import cfg
from app.core.state import state

# Папка данных рядом с exe или исходниками
BASE_DIR = Path.cwd()
DATA_DIR = BASE_DIR / "wsp-timer-data"
DATA_DIR.mkdir(exist_ok=True)

DB_PATH = str(DATA_DIR / "app_data.db")


def _conn() -> sqlite3.Connection:
    """Создать подключение к SQLite с отключённой проверкой потока."""
    return sqlite3.connect(DB_PATH, check_same_thread=False)


def init_db() -> None:
    """Инициализировать БД и подтянуть настройки в состояние приложения."""
    conn = _conn()
    try:
        cur = conn.cursor()

        # Таблица настроек
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT
            )
            """
        )

        # Таблица состояния таймера
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS runtime_state (
                key TEXT PRIMARY KEY,
                value TEXT
            )
            """
        )
        conn.commit()

        # Значения по умолчанию
        if get_setting("rub_to_sec") is None:
            set_setting("rub_to_sec", str(cfg.default_rub_to_sec))
        if get_setting("timer_color") is None:
            set_setting("timer_color", "black")

        # Синхронизация конфигурации
        rub = get_setting("rub_to_sec")
        if rub is not None:
            state.rub_to_sec = float(rub)

        color = get_setting("timer_color")
        if color in ("black", "white"):
            state.timer_text_color = color

        # OAuth данные
        at = get_setting("access_token")
        if at:
            state.oauth_access_token = at
        rt = get_setting("refresh_token")
        if rt:
            # просто сохраняем, actual refresh делает donationalerts
            pass
        cid = get_setting("client_id")
        if cid:
            state.oauth_client_id = cid
        csec = get_setting("client_secret")
        if csec:
            state.oauth_client_secret = csec

    finally:
        conn.close()


def get_setting(key: str) -> Optional[str]:
    """Вернуть значение настройки по ключу, либо None если не найдено."""
    conn = _conn()
    try:
        cur = conn.cursor()
        cur.execute("SELECT value FROM settings WHERE key = ?", (key,))
        row = cur.fetchone()
        return row[0] if row else None
    finally:
        conn.close()


def set_setting(key: str, value: str) -> None:
    """Сохранить (вставить/обновить) настройку по ключу."""
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


def save_tokens(access_token: str, refresh_token: Optional[str], expires_in: Optional[int]) -> None:
    """Сохранить OAuth-токены и client_id/secret."""
    set_setting("access_token", access_token or "")
    if refresh_token is not None:
        set_setting("refresh_token", refresh_token or "")
    if state.oauth_client_id:
        set_setting("client_id", state.oauth_client_id)
    if state.oauth_client_secret:
        set_setting("client_secret", state.oauth_client_secret)
    if expires_in is not None:
        expires_at = int(time.time()) + int(expires_in) - 30
        set_setting("token_expires_at", str(expires_at))


def load_tokens() -> dict:
    """Загрузить сохранённые токены и время истечения."""
    return {
        "access_token": get_setting("access_token"),
        "refresh_token": get_setting("refresh_token"),
        "token_expires_at": int(get_setting("token_expires_at") or "0"),
    }


# ----------------- Runtime State -----------------

def save_runtime_state(remaining: int, is_running: bool, fraction: float) -> None:
    """Сохранить состояние таймера в БД."""
    conn = _conn()
    try:
        cur = conn.cursor()
        cur.execute("INSERT OR REPLACE INTO runtime_state(key, value) VALUES (?, ?)",
                    ("remaining_seconds", str(remaining)))
        cur.execute("INSERT OR REPLACE INTO runtime_state(key, value) VALUES (?, ?)",
                    ("is_running", "1" if is_running else "0"))
        cur.execute("INSERT OR REPLACE INTO runtime_state(key, value) VALUES (?, ?)",
                    ("fraction_carry", str(fraction)))
        cur.execute("INSERT OR REPLACE INTO runtime_state(key, value) VALUES (?, ?)",
                    ("last_update_at", str(int(time.time()))))
        conn.commit()
    finally:
        conn.close()


def load_runtime_state() -> dict:
    """Загрузить сохранённое состояние таймера."""
    conn = _conn()
    try:
        cur = conn.cursor()
        cur.execute("SELECT key, value FROM runtime_state")
        rows = cur.fetchall()
        return {k: v for k, v in rows}
    finally:
        conn.close()
