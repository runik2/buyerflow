# BuyerFlow

BuyerFlow — MVP Telegram-бота и веб-админ-панели для байер-сервисов. Клиент отправляет ссылку, выбирает валюту и параметры товара, получает предварительный расчёт и создаёт заявку владельцу сервиса.

## Возможности

- FastAPI + SQLAlchemy 2 async + SQLite в local-режиме.
- JWT-админ, Argon2-библиотека для паролей, CORS allowlist и аудит.
- Валюты USD/EUR/GBP/CNY/TRY и добавление других; ручной курс или базовый курс с наценкой.
- Каталог магазинов с demo/seed-данными, тарифы доставки, заявка с фиксированным использованным курсом.
- Предварительный калькулятор, неизвестный вес приводит к сообщению «расчёт доставки уточняется».
- Mock- и TelegramNotificationService; Telegram-токен берётся только из `.env`.
- React + TypeScript + Vite адаптивная тёмная панель: Login, обзор заявок, экспорт CSV.

## Быстрый запуск

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
uvicorn app.main:app --reload
```

Админ по умолчанию: `admin` / `change-me`; пароль обязательно поменяйте в `.env`. API: http://localhost:8000/docs.

```powershell
cd frontend
npm install
npm run dev
```

## API

Реализованы auth, currencies, stores, shipping-rates, calculator/quote, orders, recalculate, notify, export.csv и health endpoints из задания. Swagger автоматически доступен на `/docs`. Для админских маршрутов передаётся Bearer JWT.

## Настройка

Создайте валюты и тарифы через Swagger или админский API. Для фиксированной доставки задайте `fixed_price` и `price_per_kg=0`; для веса — `fixed_price + weight * price_per_kg`. Seed-магазины добавляются только при первом запуске пустой local-базы и помечены описанием `demo/seed data`.

## Telegram

Укажите `TELEGRAM_BOT_TOKEN` и `TELEGRAM_ADMIN_CHAT_ID` в `.env`. Без токена приложение работает локально с безопасным no-op поведением. Реальные сообщения проверяются только при наличии валидного токена и chat id; секрет не возвращается API и не логируется.

## Безопасность

HTTP(S)-ссылки проверяются, localhost/loopback/private/link-local/reserved адреса блокируются; поля ограничены по длине, цена должна быть положительной, количество — от 1. CSV экспортирует только табличные данные и выдаёт UTF-8 BOM для Excel.

## Проверки и ограничения

Проверены локально: health, login, базовый расчёт USD с наценкой 20%, URL/цена/количество validation и отсутствие Telegram токена в ответе API. Полный набор интеграционных сценариев требует расширения тестовых фикстур.

Не проверены в этом окружении: живой Telegram Bot API без токена, Docker/PostgreSQL/Redis, production reverse proxy и frontend browser E2E. Реальные платежи не подключены. Автоматическое чтение цены с сайтов не выполняется без отдельного согласия и юридической проверки. Калькулятор предварительный, окончательную сумму подтверждает владелец.

## Roadmap

Полный Telegram conversation handler, полноценные CRUD-экраны админки, клиенты/настройки/журнал в UI, Alembic-миграции вместо create_all, realtime-курс валют и интеграция платежей.

