import os

# Бот автоматически берет токен из панели Railway
TOKEN = os.getenv("TOKEN")

# Бот будет брать список админов из Railway. 
# Если переменная ADMIN_IDS в Railway пустая, по умолчанию запишется ваш ID: 7374545230
ADMIN_IDS = [int(x.strip()) for x in os.getenv("ADMIN_IDS", "7374545230").split(",") if x.strip()]