import os

# Берем токен и ссылку на БД из переменных окружения
TOKEN = os.getenv("TOKEN") or os.getenv("BOT_TOKEN")
BOT_TOKEN = TOKEN  # дублируем для совместимости со всеми файлами
DATABASE_URL = os.getenv("DATABASE_URL")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not TOKEN:
    raise ValueError("ОШИБКА: Переменная окружения 'TOKEN' или 'BOT_TOKEN' не найдена!")
if not DATABASE_URL:
    raise ValueError("ОШИБКА: Переменная окружения 'DATABASE_URL' не найдена!")

# Список ID администраторов
ADMINS = [7374545230, 697554935, 403343697]

# Список ID дежурных служащих
SERVANT_CHAT_IDS = [697554935, 403343697]