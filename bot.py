import asyncio
import logging
from aiogram import Bot, Dispatcher
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from pytz import utc

from config import TOKEN
from database import init_db
from routers import start, menu, form, reflections, help, schedules, sponsors
from routers.reflections import send_daily_reflection_to_channel

logging.basicConfig(level=logging.INFO)

async def main():
    # Инициализация базы данных
    await init_db()
    
    bot = Bot(token=TOKEN)
    dp = Dispatcher()
    
    # Подключение роутеров
    dp.include_routers(
        start.router, menu.router, form.router, 
        reflections.router, help.router, schedules.router, sponsors.router
    )
    
    # Настройка планировщика (07:00 Алматы = 01:00 UTC)
    scheduler = AsyncIOScheduler(timezone=utc)
    scheduler.add_job(
        send_daily_reflection_to_channel, 
        trigger='cron', 
        hour=1, 
        minute=0, 
        args=[bot]
    )
    scheduler.start()
    logging.info("Планировщик рассылки запущен (01:00 UTC).")

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())