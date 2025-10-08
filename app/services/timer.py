import asyncio
from datetime import timedelta
from app.core.state import state, broadcast_timer

def format_time(sec: int) -> str:
    td = str(timedelta(seconds=sec))
    h, m, s = td.split(":")
    return f"{int(h):02}:{int(m):02}:{int(s):02}"

async def timer_loop():
    while True:
        await asyncio.sleep(1)
        if state.is_running and state.remaining_seconds > 0:
            state.remaining_seconds -= 1
            await broadcast_timer(format_time(state.remaining_seconds))
        if state.remaining_seconds == 0:
            state.is_running = False

def start_timer_task():
    # Стартуем 1 фоновую задачу
    asyncio.create_task(timer_loop())
