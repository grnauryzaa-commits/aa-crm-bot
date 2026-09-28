import os
import logging

# Токен берём ТОЛЬКО из переменных окружения (Railway Variables)
TOKEN = os.getenv("TOKEN") or os.getenv("BOT_TOKEN")
if not TOKEN:
    raise ValueError(
        "ОШИБКА: Переменная окружения 'TOKEN' или 'BOT_TOKEN' не найдена!"
    )
BOT_TOKEN = TOKEN

# База данных — тоже из переменных окружения
DATABASE_URL = os.getenv("DATABASE_URL")

# DEBUG: временный лог, чтобы увидеть, что реально приходит из Railway
logging.error("DEBUG: DATABASE_URL = %r", DATABASE_URL)

if not DATABASE_URL:
    raise ValueError("ОШИБКА: Переменная окружения 'DATABASE_URL' не найдена!")

# Groq API (опционально)
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Список ID администраторов
ADMINS = [7374545230, 697554935, 403343697]

# Список ID дежурных служащих
SERVANT_CHAT_IDS = [7374545230, 403343697]