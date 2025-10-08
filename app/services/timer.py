"""Логика таймера: форматирование времени и фоновый цикл уменьшения секунд."""

import asyncio
from datetime import timedelta

from app.core.state import state, broadcast_timer


def format_time(sec: int) -> str:
    """Форматировать количество секунд в строку HH:MM:SS."""
    td = str(timedelta(seconds=sec))
    h, m, s = td.split(":")
    return f"{int(h):02}:{int(m):02}:{int(s):02}"


async def timer_loop():
    """Фоновый цикл: каждую секунду уменьшает оставшееся время и рассылает обновление."""
    while True:
        await asyncio.sleep(1)
        if state.is_running and state.remaining_seconds > 0:
            state.remaining_seconds -= 1
            await broadcast_timer(format_time(state.remaining_seconds))
        if state.remaining_seconds == 0:
            state.is_running = False


def start_timer_task():
    """Запустить фоновую задачу таймера (одну на всё приложение)."""
    asyncio.create_task(timer_loop())
