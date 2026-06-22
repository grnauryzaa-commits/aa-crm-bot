import asyncio
import logging
from aiogram import Bot, Dispatcher
from config import TOKEN
from database import init_db

# Импортируем роутеры из папки routers
from routers.start import router as start_router
from routers.menu import router as menu_router
from routers.form import router as form_router
from routers.sponsors import router as sponsors_router
from routers.admin import router as admin_router
from routers.help import router as help_router
from routers.schedules import router as schedules_router

# Настройка логирования
logging.basicConfig(level=logging.INFO)

async def main():
    # Инициализируем базу данных при старте
    await init_db()
    
    bot = Bot(token=TOKEN)
    dp = Dispatcher()

    # Регистрируем все роутеры в диспетчере
    dp.include_routers(
        start_router,
        menu_router,
        form_router,
        sponsors_router,
        admin_router,
        help_router,
        schedules_router
    )

    logging.info("Бот успешно запущен и готов к работе!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())