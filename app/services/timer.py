"""Логика таймера: форматирование времени и фоновый цикл уменьшения секунд."""

import asyncio
import time
from datetime import timedelta

from app.core.state import state, broadcast_timer
from app.core.db import save_runtime_state


def format_time(sec: int) -> str:
    """Форматировать количество секунд в строку HH:MM:SS."""
    td = str(timedelta(seconds=sec))
    h, m, s = td.split(":")
    return f"{int(h):02}:{int(m):02}:{int(s):02}"


async def timer_loop():
    """Фоновый цикл: каждую секунду уменьшает оставшееся время и сохраняет состояние."""
    while True:
        await asyncio.sleep(1)

        if state.is_running and state.remaining_seconds > 0:
            state.remaining_seconds -= 1
            await broadcast_timer(format_time(state.remaining_seconds))

        # сохраняем каждые 5 секунд
        if int(time.time()) % 5 == 0:
            save_runtime_state(state.remaining_seconds, state.is_running, state.fraction_carry)

        if state.remaining_seconds == 0 and state.is_running:
            state.is_running = False
            save_runtime_state(state.remaining_seconds, state.is_running, state.fraction_carry)


def start_timer_task():
    """Запустить фоновую задачу таймера (одну на всё приложение)."""
    asyncio.create_task(timer_loop())
