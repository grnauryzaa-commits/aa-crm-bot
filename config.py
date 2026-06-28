import os

# Берем токен и ссылку на БД из переменных окружения Railway
TOKEN = os.getenv("TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")

if not TOKEN:
    raise ValueError("ОШИБКА: Переменная окружения 'TOKEN' не найдена!")
if not DATABASE_URL:
    raise ValueError("ОШИБКА: Переменная окружения 'DATABASE_URL' не найдена!")

# Список ID администраторов, которые будут проверять анкеты спонсоров
# 🟢 Твой ID успешно добавлен первым в список. Через запятую можно добавлять других админов
ADMINS = [7374545230]