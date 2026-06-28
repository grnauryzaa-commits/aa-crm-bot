import os

# Берем токен и ссылку на БД из переменных окружения
TOKEN = os.getenv("TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")

if not TOKEN:
    raise ValueError("ОШИБКА: Переменная окружения 'TOKEN' не найдена!")
if not DATABASE_URL:
    raise ValueError("ОШИБКА: Переменная окружения 'DATABASE_URL' не найдена!")

# Список ID администраторов
ADMINS = [7374545230]