import os

# Пытаемся взять из Railway / системы, если нет — используем твои данные для локального теста
TOKEN = os.getenv("TOKEN") or os.getenv("BOT_TOKEN") or "8648635817:AAFBvlyhdjBO17i738EbIgkt3-Q4NCEAJXA"
BOT_TOKEN = TOKEN  

DATABASE_URL = os.getenv("DATABASE_URL") or "postgresql://postgres:rjKAEdhpAeVceQzFobzCKFRbWnJwYOem@thomas.proxy.rlwy.net:12836/railway"

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not TOKEN:
    raise ValueError("ОШИБКА: Переменная окружения 'TOKEN' или 'BOT_TOKEN' не найдена!")
if not DATABASE_URL:
    raise ValueError("ОШИБКА: Переменная окружения 'DATABASE_URL' не найдена!")

# Список ID администраторов
ADMINS = [7374545230, 697554935, 403343697]

# Список ID дежурных служащих
SERVANT_CHAT_IDS = [697554935, 403343697]