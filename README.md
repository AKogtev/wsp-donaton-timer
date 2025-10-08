## License
Source-available, non-commercial: **PolyForm Noncommercial 1.0.0**.  
See `LICENSE` for full text.  
For commercial use or exceptions, please contact <wsp@a.kogtev.ru>.

# Donatimer
Мини-приложение на **FastAPI**: веб-таймер обратного отсчёта (формат `HH:MM:SS`) с панелью управления, WebSocket-обновлениями и интеграцией **DonationAlerts** (OAuth + Centrifugo).  
Поддерживает: старт/стоп/сброс (с подтверждением), установку времени, настраиваемое соотношение «₽ → сек» (в т.ч. дробное, например `4.5`), выбор цвета текста таймера (чёрный/белый)
- `/` — чистый таймер (прозрачный фон, шрифт из UI).
    
- `/config` — панель управления (дарк-тема, логи).
    
- `/auth` — авторизация в DonationAlerts (ввод `client_id`/`client_secret`, копирование redirect URI).

## Структура проекта
```
donaton/
├─ app/
│  ├─ core/         # config/state/… (есть __init__.py)
│  ├─ routes/       # роуты страниц и сокетов (есть __init__.py)
│  ├─ services/     # таймер, DonationAlerts, менеджеры (есть __init__.py)
│  ├─ static/       # style.css, js/…
│  └─ templates/    # Jinja2 (base.html, config.html, auth.html, …)
├─ run_app.py       # Точка входа для dev/pyinstaller (см. ниже)
├─ requirements.txt # Зависимости которые устанавливаются при сборке
└─ .env             # (опционально) переменные окружения рядом с exe/репо
```

## Сборка проекта
Собираем в **один исполняемый файл** без установки пакетов в систему, я билдил на Винде с помощью cmd. Находясь в директории проекта выполняем команды:

Создаем виртуальную среду, чтобы не засорять систему разными пакетами:
 ```
py -m venv .venv
```

Устанавливаем pip
```
.\.venv\Scripts\python -m pip install --upgrade pip
```

Устанавливаем зависимости:
```
.\.venv\Scripts\pip install -r requirements.txt
```

Запускаем сборку .exe файла:
```
.\.venv\Scripts\pyinstaller --noconfirm --onefile --name Donatimer --paths . --hidden-import dotenv --add-data "app\templates;app\templates" --add-data "app\static;app\static" run_app.py
```

На выходе получаем готовый .exe файл в директории dist, то есть `dist\Donatimer.exe`

### Использование
После запуска вам в браузере будут доступны следующие страницы:
- **http://localhost:8000/** - только таймер на прозрачном фоне (текст белый/чёрный — управляется из панели)
- **http://localhost:8000/config** - Панель конфигурации таймера, тут можно выставить время, запустить, остановить, таймер. Настроить цвет таймера (Либо белый, либо черный). Посмотреть Логи действий, выставить коэффициент времени к сумме доната и так далее
- **http://localhost:8000/auth** - страница на который вы связываете свой аккаунт DonationAlerts и таймер

