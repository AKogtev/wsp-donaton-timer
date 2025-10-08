"""WebSocket-маршруты: обновление таймера, настроек и управление приложением."""

import asyncio
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.core.state import state, broadcast_control, broadcast_timer_cfg
from app.core.db import set_setting, get_setting
from app.services.timer import format_time
from app.services.donationalerts import donation_manager

router = APIRouter()


@router.websocket("/ws")
async def timer_ws(websocket: WebSocket):
    """Соединение для страницы с таймером: рассылает оставшееся время."""
    await websocket.accept()
    state.timer_clients.append(websocket)

    # Отправить стартовое значение при подключении
    await websocket.send_text(format_time(state.remaining_seconds))

    try:
        while True:
            await websocket.receive_text()  # сообщения от клиента не используем
    except WebSocketDisconnect:
        if websocket in state.timer_clients:
            state.timer_clients.remove(websocket)


@router.websocket("/timer_cfg")
async def timer_cfg_ws(websocket: WebSocket):
    """Соединение для страницы настроек таймера: рассылает текущий цвет текста."""
    await websocket.accept()
    state.timer_cfg_clients.append(websocket)

    # Отправить цвет при подключении
    await websocket.send_text(state.timer_text_color)

    try:
        while True:
            await websocket.receive_text()  # клиент ничего не присылает
    except WebSocketDisconnect:
        if websocket in state.timer_cfg_clients:
            state.timer_cfg_clients.remove(websocket)


@router.websocket("/control")
async def control_ws(websocket: WebSocket):
    """Соединение панели управления: принимает команды для управления таймером и токенами."""
    await websocket.accept()
    state.control_clients.append(websocket)
    await websocket.send_text("Connected to control panel")

    try:
        while True:
            cmd = await websocket.receive_text()

            if cmd.startswith("set "):
                # Установить новое значение таймера
                try:
                    h, m, s = cmd[4:].split(":")
                    state.timer_total_seconds = int(h) * 3600 + int(m) * 60 + int(s)
                    state.remaining_seconds = state.timer_total_seconds
                    await websocket.send_text(
                        f"Установлено время: {format_time(state.remaining_seconds)}"
                    )
                    from app.core.state import broadcast_timer

                    await broadcast_timer(format_time(state.remaining_seconds))
                except Exception:
                    await websocket.send_text("Ошибка формата (нужно HH:MM:SS)")

            elif cmd == "start":
                state.is_running = True
                await websocket.send_text("Таймер запущен")

            elif cmd == "stop":
                state.is_running = False
                await websocket.send_text("Таймер остановлен")

            elif cmd == "reset":
                state.remaining_seconds = state.timer_total_seconds
                from app.core.state import broadcast_timer

                await broadcast_timer(format_time(state.remaining_seconds))
                await websocket.send_text("Таймер сброшен")

            elif cmd.startswith("token "):
                # Установка access_token вручную и запуск donation listener
                maybe = cmd[6:].strip()
                if maybe:
                    set_setting("access_token", maybe)
                    state.oauth_access_token = maybe

                if not (
                    state.oauth_client_id
                    and state.oauth_client_secret
                    and (get_setting("access_token") or state.oauth_access_token)
                ):
                    await websocket.send_text(
                        "Не заданы client_id/secret или пустой Access Token"
                    )
                    continue

                if state.donation_task:
                    state.donation_task.cancel()
                    await websocket.send_text("Перезапуск DA-листенера...")

                state.donation_task = asyncio.create_task(donation_manager())
                await websocket.send_text(
                    "Access Token сохранён, пробуем подключиться к DonationAlerts..."
                )

            elif cmd.startswith("coef "):
                # Изменить коэффициент рубль → секунды
                try:
                    val = float(cmd[5:].strip().replace(",", "."))
                    if val < 0:
                        await websocket.send_text(
                            "Ошибка: коэффициент не может быть отрицательным"
                        )
                    else:
                        state.rub_to_sec = val
                        set_setting("rub_to_sec", str(val))
                        await websocket.send_text(
                            f"Соотношение изменено: 1₽ = {val:g} секунд"
                        )
                except Exception:
                    await websocket.send_text("Ошибка: укажи число, например 4.5")

            elif cmd.startswith("color "):
                # Изменить цвет текста таймера
                col = cmd[6:].strip().lower()
                if col not in ("black", "white"):
                    await websocket.send_text(
                        "Ошибка: допустимы только 'black' или 'white'"
                    )
                else:
                    state.timer_text_color = col
                    set_setting("timer_color", col)
                    await broadcast_timer_cfg(col)
                    await websocket.send_text(f"Цвет таймера установлен: {col}")

            else:
                await websocket.send_text(f"Неизвестная команда: {cmd}")

    except WebSocketDisconnect:
        if websocket in state.control_clients:
            state.control_clients.remove(websocket)
            