# app/core/config.py
import os
from dataclasses import dataclass
from dotenv import load_dotenv

# Подхватываем переменные из .env (если есть)
load_dotenv()

@dataclass
class Config:
    # Эти поля можно оставить пустыми — через /auth мы всё равно получим токены.
    da_client_id: str = os.getenv("DA_CLIENT_ID", "").strip()
    da_client_secret: str = os.getenv("DA_CLIENT_SECRET", "").strip()

    # ДОЛЖЕН 1:1 совпадать с настройками в DonationAlerts
    oauth_redirect_uri: str = os.getenv("OAUTH_REDIRECT_URI", "http://localhost:8000/callback").strip()

    # Базовое соотношение 1₽ -> секунды (можно менять в /config)
    default_rub_to_sec: int = int(os.getenv("RUB_TO_SEC", "10"))

# Экземпляр конфигурации, который импортируется как `cfg`
cfg = Config()
