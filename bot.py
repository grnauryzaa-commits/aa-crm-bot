import asyncio
import logging
from aiogram import Bot, Dispatcher
from config import TOKEN
from database import init_db

# Импорт планировщика задач
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from pytz import timezone

# Импортируем роутеры и функцию рассылки
from routers.start import router as start_router
from routers.menu import router as menu_router
from routers.form import router as form_router
from routers.sponsors import router as sponsors_router
from routers.admin import router as admin_router
from routers.help import router as help_router
from routers.schedules import router as schedules_router
from routers.reflections import router as reflections_router
from routers.reflections import send_daily_reflection_to_channel  # Импортируем функцию рассылки

logging.basicConfig(level=logging.INFO)

async def main():
    await init_db()
    
    bot = Bot(token=TOKEN)
    dp = Dispatcher()

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

    # НАСТРОЙКА АВТОРАССЫЛКИ В КАНАЛ
    scheduler = AsyncIOScheduler(timezone=timezone("Asia/Almaty"))
    
    # Настраиваем триггер: каждый день (trigger='cron') в 07 часов 00 минут
    scheduler.add_job(
        send_daily_reflection_to_channel, 
        trigger='cron', 
        hour=7, 
        minute=0, 
        args=[bot]
    )
    
    # Стартуем планировщик
    scheduler.start()
    logging.info("Планировщик рассылки запущен (время: Алматы, 07:00).")

    logging.info("Бот успешно запущен и готов к работе!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())