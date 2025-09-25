# Minimalist Gemini Telegram Bot (private-only)

## Запуск
1) Заполните `.env` с ключами `TELEGRAM_BOT_TOKEN` и `GEMINI_API_KEY`.
2) (опционально) `GEMINI_MODEL`, `MAX_OUTPUT_TOKENS`, `ENABLE_STREAMING` и др. в `.env`.
3) Запуск: `python -m app.main`

## Политика
- Бот **исключительно** для личных чатов. При добавлении в группу/канал — автоматически покидает чат.
- Минималистичный UI: одно прогресс-сообщение + безопасное разбиение длинных ответов.
- История хранится структурно (role/parts), используется в контексте запросов.
- Поддержка стриминга при наличии у SDK, с graceful fallback.
