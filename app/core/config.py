"""Конфигурация приложения: считывание настроек из переменных окружения и .env."""

import os
from dataclasses import dataclass
from dotenv import load_dotenv

# Загрузить переменные из .env, если файл присутствует
load_dotenv()


@dataclass
class Config:
    """Контейнер конфигурации приложения."""

    # Идентификаторы OAuth для DonationAlerts (могут быть пустыми — токены можно получить через /auth)
    da_client_id: str = os.getenv("DA_CLIENT_ID", "").strip()
    da_client_secret: str = os.getenv("DA_CLIENT_SECRET", "").strip()

    # URL возврата после OAuth (должен совпадать с настройками в DonationAlerts)
    oauth_redirect_uri: str = os.getenv("OAUTH_REDIRECT_URI", "http://localhost:8000/callback").strip()

    # Базовый коэффициент конвертации: 1₽ -> секунды (значение по умолчанию можно менять в /config)
    default_rub_to_sec: float = float(os.getenv("RUB_TO_SEC", "10"))


# Глобальный экземпляр конфигурации
cfg = Config()
