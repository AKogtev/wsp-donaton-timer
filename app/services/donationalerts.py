# app/services/donationalerts.py
"""
Подключение к DonationAlerts через Centrifugo:
 - авто-обновление access_token (через refresh_token);
 - подключение к WS, подписка на канал донатов;
 - парсинг суммы и прибавка к таймеру с учётом ДРОБНОГО коэффициента (₽→сек);
 - graceful переподключение с экспоненциальной задержкой при обрывах.
"""

import json
import time
import math
import asyncio
import websockets
import httpx

from ..core.state import state, broadcast_control, broadcast_timer
from ..core.db import load_tokens, save_tokens
from .timer import format_time


def extract_amount_anywhere(obj):
    """Пытаемся вытащить сумму доната из произвольной структуры публикации Centrifugo."""
    if isinstance(obj, dict):
        # самые типовые ключи
        for key in ("amount", "amount_main"):
            if key in obj:
                return obj[key]
        # иначе рекурсивно
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
    """
    Возвращает валидный access_token.
    Если истёк — рефрешит через refresh_token и сохраняет новые значения в БД.
    """
    tokens = load_tokens()
    access = tokens.get("access_token")
    refresh = tokens.get("refresh_token")
    exp = int(tokens.get("token_expires_at") or 0)
    now = int(time.time())

    # Ещё валиден?
    if access and now < exp - 10:
        return access

    # Нечем рефрешить — просим авторизоваться
    if not refresh:
        raise RuntimeError("Нет refresh_token — авторизуйтесь заново через /auth.")

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
    """
    GET /api/v1/user/oauth → { data: { id, socket_connection_token, ... } }
    """
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
    """
    POST /api/v1/centrifuge/subscribe
      body: { channels: ["$alerts:donation_<user_id>"], client: "<client_id>" }
      resp: { channels: [{channel, token}] }
    """
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
    """
    Главный менеджер подключения к DonationAlerts (через Centrifugo):
      • авто-refresh access_token при необходимости;
      • подключение к WS, подписка на канал донатов;
      • парсинг сумм и увеличение таймера с учётом дробного коэффициента;
      • graceful переподключение (экспоненциальный backoff) при обрыве.
    Останавливается при фатальных ошибках авторизации/АПИ.
    """
    attempt = 0
    backoff = 2

    # Защитимся, если поле ещё не добавили в state
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
                # 1) CONNECT — получаем client UUID
                await ws.send(json.dumps({"params": {"token": socket_token}, "id": 1}))

                client_id = None
                while True:
                    raw = await ws.recv()
                    msg = json.loads(raw)
                    # CONNECT ack приходит с result.client
                    if msg.get("id") == 1 and "result" in msg and "client" in msg["result"]:
                        client_id = msg["result"]["client"]
                        await broadcast_control(f"DA: client={client_id}")
                        break

                # 2) SUBSCRIBE — токен на канал донатов
                channel, sub_token = await get_channel_sub_token(access_token, user_id, client_id)
                await ws.send(json.dumps({"params": {"channel": channel, "token": sub_token}, "method": 1, "id": 2}))
                await broadcast_control(f"DA: подписались на {channel}. Ждём донаты...")

                # успешное соединение — сбрасываем счётчик
                attempt = 0
                backoff = 2

                # 3) Слушаем публикации
                async for message in ws:
                    data = json.loads(message)
                    payload = data.get("result") or {}

                    amount = extract_amount_anywhere(payload)
                    if amount is None:
                        continue

                    try:
                        amount = float(amount)

                        # дробный коэффициент: 1₽ = state.rub_to_sec секунд (float)
                        coef = float(getattr(state, "rub_to_sec", 10.0))
                        add_seconds_float = amount * coef

                        # Разделяем на целое + дробь, дроби накапливаем
                        add_int = math.floor(add_seconds_float)
                        state.fraction_carry += (add_seconds_float - add_int)

                        if state.fraction_carry >= 1.0:
                            extra = math.floor(state.fraction_carry)
                            add_int += extra
                            state.fraction_carry -= extra

                        # Прибавляем секунды к таймеру
                        state.remaining_seconds += int(add_int)

                        await broadcast_timer(format_time(state.remaining_seconds))
                        await broadcast_control(
                            f"Донат {amount:g} → +{add_seconds_float:.2f} сек "
                            f"(добавлено сейчас {int(add_int)} сек), "
                            f"всего {format_time(state.remaining_seconds)}"
                        )
                    except Exception as e:
                        await broadcast_control(f"Ошибка парсинга суммы: {e}")

        except RuntimeError as e:
            # фатальная ошибка — не пытаемся переподключаться
            await broadcast_control(f"DA: фатальная ошибка: {e}. Останов.")
            return
        except Exception as e:
            await broadcast_control(f"DA: обрыв соединения: {e}. Переподключение через {backoff}s...")
            await asyncio.sleep(backoff)
            backoff = min(backoff * 2, 60)
            continue
