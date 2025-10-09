"""Маршруты FastAPI для HTML-страниц и OAuth-авторизации DonationAlerts."""

import secrets
from urllib.parse import urlencode, quote_plus
from pathlib import Path

from fastapi import APIRouter, Request, Form
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from app.core.state import state
from app.core.db import get_setting, save_tokens

router = APIRouter()

# Директория с Jinja2-шаблонами
TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


@router.get("/")
async def index(request: Request):
    """Главная страница (таймер)."""
    return templates.TemplateResponse("index.html", {"request": request})


@router.get("/config")
async def config_page(request: Request):
    """Страница настроек таймера и токенов."""
    token = get_setting("access_token") or ""
    state.oauth_access_token = token

    rub = get_setting("rub_to_sec")
    if rub is not None:
        try:
            state.rub_to_sec = float(rub)
        except ValueError:
            state.rub_to_sec = 10.0

    return templates.TemplateResponse(
        "config.html",
        {"request": request, "token": token, "coef": state.rub_to_sec},
    )


@router.get("/auth")
async def auth_page(request: Request):
    """Страница ввода client_id/secret и старта OAuth-авторизации."""
    return templates.TemplateResponse(
        "auth.html", {"request": request, "redirect_uri": state.oauth_redirect_uri}
    )


@router.post("/start_auth")
async def start_auth(
    request: Request, client_id: str = Form(...), client_secret: str = Form(...)
):
    """Формирует URL авторизации и перенаправляет пользователя в DonationAlerts."""
    state.oauth_client_id = client_id
    state.oauth_client_secret = client_secret

    oauth_state = secrets.token_urlsafe(16)
    params = {
        "client_id": state.oauth_client_id,
        "redirect_uri": state.oauth_redirect_uri,
        "response_type": "code",
        "scope": "oauth-user-show oauth-donation-subscribe",
        "state": oauth_state,
    }
    auth_url = "https://www.donationalerts.com/oauth/authorize?" + urlencode(
        params, quote_via=quote_plus
    )
    return RedirectResponse(url=auth_url)


@router.get("/callback")
async def callback(code: str):
    """Обработчик редиректа от DonationAlerts: получает и сохраняет токены."""
    import httpx

    token_url = "https://www.donationalerts.com/oauth/token"
    data = {
        "client_id": state.oauth_client_id,
        "client_secret": state.oauth_client_secret,
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": state.oauth_redirect_uri,
    }

    async with httpx.AsyncClient() as client:
        r = await client.post(token_url, data=data)
        if r.status_code == 200:
            js = r.json()
            access_token = js.get("access_token")
            refresh_token = js.get("refresh_token")
            expires_in = js.get("expires_in", 3600)
            save_tokens(access_token, refresh_token, expires_in)
            state.oauth_access_token = access_token

    return RedirectResponse(url="/config")
