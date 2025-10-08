"""Интеграция с DonationAlerts через Centrifugo.

Функции:
- обновление access_token по refresh_token;
- подключение к WebSocket и подписка на канал донатов;
- извлечение суммы из событий;
- добавление секунд к таймеру с учётом дробного коэффициента;
- переподключение при обрывах.
"""

import json
import time
import math
import asyncio
import websockets
import httpx

from app.core.state import state, broadcast_control, broadcast_timer
from app.core.db import load_tokens, save_tokens
from app.services.timer import format_time


def extract_amount_anywhere(obj):
    """Попробовать рекурсивно найти сумму доната в произвольном JSON-объекте."""
    if isinstance(obj, dict):
        for key in ("amount", "amount_main"):
            if key in obj:
                return obj[key]
        for v in obj.values():
            val = extract_amount_anywhere(v)
            if val is not None:
                return val
    elif isinstance(obj, list):
        for v in obj:
            val = extract_amount_anywhere(v)
            if val is not None:
                return val
    return None


async def ensure_access_token(client_id: str, client_secret: str) -> str:
    """Вернуть валидный access_token, при необходимости обновить его через refresh_token."""
    tokens = load_tokens()
    access = tokens.get("access_token")
    refresh = tokens.get("refresh_token")
    exp = int(tokens.get("token_expires_at") or 0)
    now = int(time.time())

    # Токен ещё не истёк
    if access and now < exp - 10:
        return access

    if not refresh:
        raise RuntimeError("Нет refresh_token — требуется повторная авторизация.")

    # Запрос на обновление токена
    data = {
        "client_id": client_id,
        "client_secret": client_secret,
        "grant_type": "refresh_token",
        "refresh_token": refresh,
    }
    async with httpx.AsyncClient() as client:
        r = await client.post("https://www.donationalerts.com/oauth/token", data=data)
        if r.status_code != 200:
            raise RuntimeError(f"Refresh failed: {r.status_code} {r.text}")

        js = r.json()
        access = js.get("access_token")
        refresh_new = js.get("refresh_token", refresh)
        expires_in = js.get("expires_in", 3600)

        save_tokens(access, refresh_new, expires_in)
        state.oauth_access_token = access
        await broadcast_control("Access token обновлён через refresh_token.")
        return access


async def get_user_and_socket_token(access_token: str):
    """Получить user_id и socket_connection_token через API /api/v1/user/oauth."""
    url = "https://www.donationalerts.com/api/v1/user/oauth"
    headers = {"Authorization": f"Bearer {access_token}"}
    async with httpx.AsyncClient() as client:
        r = await client.get(url, headers=headers)
        if r.status_code != 200:
            raise RuntimeError(f"Ошибка user/oauth: {r.status_code} {r.text}")
        js = r.json()
        data = js.get("data") or {}
        return data.get("id"), data.get("socket_connection_token")


async def get_channel_sub_token(access_token: str, user_id: int, client_id: str):
    """Получить токен подписки на канал донатов через /api/v1/centrifuge/subscribe."""
    url = "https://www.donationalerts.com/api/v1/centrifuge/subscribe"
    headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}
    channel = f"$alerts:donation_{user_id}"
    payload = {"channels": [channel], "client": client_id}

    async with httpx.AsyncClient() as client:
        r = await client.post(url, headers=headers, json=payload)
        if r.status_code != 200:
            raise RuntimeError(f"Ошибка subscribe: {r.status_code} {r.text}")
        js = r.json()
        arr = js.get("channels") or []
        if not arr:
            raise RuntimeError(f"subscribe: пустой ответ {js}")
        return arr[0].get("channel"), arr[0].get("token")


async def donation_manager(max_attempts: int = 10):
    """Менеджер подключения к DonationAlerts (WS).

    - автообновление токена;
    - подписка на канал донатов;
    - обработка сумм с дробным коэффициентом;
    - переподключение с экспоненциальным backoff.
    """
    attempt = 0
    backoff = 2

    # На всякий случай — гарантируем наличие fraction_carry
    if not hasattr(state, "fraction_carry"):
        state.fraction_carry = 0.0

    while True:
        attempt += 1
        if attempt > max_attempts:
            await broadcast_control("DA: достигнут лимит попыток переподключения. Остановлено.")
            return

        try:
            if not state.oauth_client_id or not state.oauth_client_secret:
                await broadcast_control("DA: client_id/secret не заданы. Останов.")
                return

            access_token = await ensure_access_token(state.oauth_client_id, state.oauth_client_secret)
            user_id, socket_token = await get_user_and_socket_token(access_token)
            if not user_id or not socket_token:
                await broadcast_control("DA: не удалось получить user_id или socket_token. Останов.")
                return

            ws_url = "wss://centrifugo.donationalerts.com/connection/websocket"
            await broadcast_control("DA: подключаемся к WebSocket...")

            async with websockets.connect(ws_url) as ws:
                # CONNECT: получаем client_id
                await ws.send(json.dumps({"params": {"token": socket_token}, "id": 1}))

                client_id = None
                while True:
                    raw = await ws.recv()
                    msg = json.loads(raw)
                    if msg.get("id") == 1 and "result" in msg and "client" in msg["result"]:
                        client_id = msg["result"]["client"]
                        await broadcast_control(f"DA: client={client_id}")
                        break

                # SUBSCRIBE: подписываемся на канал донатов
                channel, sub_token = await get_channel_sub_token(access_token, user_id, client_id)
                await ws.send(
                    json.dumps({"params": {"channel": channel, "token": sub_token}, "method": 1, "id": 2})
                )
                await broadcast_control(f"DA: подписались на {channel}. Ждём донаты...")

                attempt = 0
                backoff = 2

                # Слушаем публикации
                async for message in ws:
                    data = json.loads(message)
                    payload = data.get("result") or {}

                    amount = extract_amount_anywhere(payload)
                    if amount is None:
                        continue

                    try:
                        amount = float(amount)
                        coef = float(getattr(state, "rub_to_sec", 10.0))
                        add_seconds_float = amount * coef

                        add_int = math.floor(add_seconds_float)
                        state.fraction_carry += add_seconds_float - add_int

                        if state.fraction_carry >= 1.0:
                            extra = math.floor(state.fraction_carry)
                            add_int += extra
                            state.fraction_carry -= extra

                        state.remaining_seconds += int(add_int)

                        await broadcast_timer(format_time(state.remaining_seconds))
                        await broadcast_control(
                            f"Донат {amount:g} → +{add_seconds_float:.2f} сек "
                            f"(добавлено {int(add_int)} сек), "
                            f"итого {format_time(state.remaining_seconds)}"
                        )
                    except Exception as e:
                        await broadcast_control(f"Ошибка парсинга суммы: {e}")

        except RuntimeError as e:
            await broadcast_control(f"DA: фатальная ошибка: {e}. Останов.")
            return
        except Exception as e:
            await broadcast_control(f"DA: обрыв соединения: {e}. Переподключение через {backoff}s...")
            await asyncio.sleep(backoff)
            backoff = min(backoff * 2, 60)
            continue
