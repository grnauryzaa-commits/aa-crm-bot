import asyncio
import logging
from aiogram import Bot, Dispatcher
from config import TOKEN
from database import init_db

# Импортируем ВСЕ роутеры из папки routers
from routers.start import router as start_router
from routers.menu import router as menu_router
from routers.form import router as form_router
from routers.sponsors import router as sponsors_router
from routers.admin import router as admin_router
from routers.help import router as help_router
from routers.schedules import router as schedules_router
from routers.reflections import router as reflections_router  # Добавили размышления

# Настройка логирования
logging.basicConfig(level=logging.INFO)

async def main():
    # Инициализируем базу данных при старте сервера
    await init_db()
    
    # Создаем объекты бота и диспетчера
    bot = Bot(token=TOKEN)
    dp = Dispatcher()

    # Регистрируем абсолютно все роутеры в диспетчере
    dp.include_routers(
        start_router,
        menu_router,
        form_router,
        sponsors_router,
        admin_router,
        help_router,
        schedules_router,
        reflections_router  # Теперь диспетчер видит и этот роутер
    )

    logging.info("Бот успешно запущен и готов к работе!")
    
    # Запускаем бесконечный опрос сервера Telegram (Long Polling)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())