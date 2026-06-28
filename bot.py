import asyncio
import logging
import sys
from aiogram import Bot, Dispatcher
from config import TOKEN
from database import init_db

# Импортируем все роутеры
from routers.start import router as start_router
from routers.menu import router as menu_router
from routers.form import router as form_router
from routers.sponsors import router as sponsors_router
from routers.sponsors_mod import router as sponsors_mod_router
from routers.reflections import router as reflections_router
# ДОБАВЛЯЕМ ЭТИ ДВЕ СТРОКИ:
from routers.help import router as help_router
from routers.schedules import router as schedules_router

async def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)]
    )
    
    await init_db()

    bot = Bot(token=TOKEN)
    dp = Dispatcher()
    
    # ДОБАВЛЯЕМ help_router и schedules_router В СПИСОК:
    dp.include_routers(
        start_router,
        menu_router,
        form_router,
        sponsors_router,
        sponsors_mod_router,
        reflections_router,
        help_router,
        schedules_router
    )
    
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Бот остановлен.")