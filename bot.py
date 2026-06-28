import asyncio
import logging
from aiogram import Bot, Dispatcher
from config import TOKEN
from database import init_db

# Импортируем все роутеры
from routers.start import router as start_router
from routers.menu import router as menu_router
from routers.form import router as form_router
from routers.sponsors import router as sponsors_router
from routers.sponsors_mod import router as sponsors_mod_router  # 🟢 Импортировали модерацию
from routers.reflections import router as reflections_router

async def main():
    logging.basicConfig(level=logging.INFO)
    
    # Запуск и проверка структуры таблиц в базе данных
    await init_db()
    
    bot = Bot(token=TOKEN)
    dp = Dispatcher()
    
    # Регистрируем все роутеры в диспетчере
    dp.include_routers(
        start_router,
        menu_router,
        form_router,
        sponsors_router,
        sponsors_mod_router,  # 🟢 Подключили модерацию к боту
        reflections_router
    )
    
    print("🚀 Бот группы «Наурыз» запущен и слушает команды...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())