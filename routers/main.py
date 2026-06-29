import asyncio
import logging
from aiogram import Bot, Dispatcher
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from pytz import timezone

# Твой файл конфигурации
from config import TOKEN 

# Импорты роутеров
from routers.start import router as start_router
from routers.menu import router as menu_router
from routers.form import router as form_router
from routers.sponsors import router as sponsors_router
from routers.admin import router as admin_router
from routers.help import router as help_router
from routers.schedules import router as schedules_router
from routers.reflections import router as reflections_router

# Импорт функции рассылки
from routers.reflections import send_daily_reflection_to_channel

logging.basicConfig(level=logging.INFO)

async def main():
    # 1. Сначала создаем бота
    bot = Bot(token=TOKEN)
    dp = Dispatcher()

    # 2. Подключаем роутеры
    dp.include_routers(
        start_router,
        menu_router,
        form_router,
        sponsors_router,
        admin_router,
        help_router,
        schedules_router,
        reflections_router
    )

    # 3. Настраиваем планировщик (здесь 'bot' уже существует)
    scheduler = AsyncIOScheduler(timezone=timezone("Asia/Almaty"))
    
    scheduler.add_job(
        send_daily_reflection_to_channel, 
        trigger='cron', 
        hour=7, 
        minute=0, 
        args=[bot]  # Передаем созданный выше объект bot
    )
    
    scheduler.start()
    logging.info("Планировщик рассылки запущен (время: Алматы, 07:00).")

    # 4. Запускаем бота
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())