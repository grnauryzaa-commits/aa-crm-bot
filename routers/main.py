import asyncio
import logging
from aiogram import Bot, Dispatcher
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from pytz import utc

from config import TOKEN 
from routers.start import router as start_router
from routers.menu import router as menu_router
from routers.form import router as form_router
from routers.sponsors import router as sponsors_router
from routers.admin import router as admin_router
from routers.help import router as help_router
from routers.schedules import router as schedules_router
from routers.reflections import (
    router as reflections_router, 
    send_daily_reflection_to_channel, 
    send_morning_prayer_to_channel,
    send_evening_prayer_to_channel
)

logging.basicConfig(level=logging.INFO)

async def main():
    bot = Bot(token=TOKEN)
    dp = Dispatcher()
    dp.include_routers(start_router, menu_router, form_router, sponsors_router, admin_router, help_router, schedules_router, reflections_router)

    scheduler = AsyncIOScheduler(timezone=utc)
    
    # 06:00 Алматы = 01:00 UTC
    scheduler.add_job(send_daily_reflection_to_channel, 'cron', hour=1, minute=0, args=[bot])
    # 06:30 Алматы = 01:30 UTC
    scheduler.add_job(send_morning_prayer_to_channel, 'cron', hour=1, minute=30, args=[bot])
    # 23:00 Алматы = 18:00 UTC
    scheduler.add_job(send_evening_prayer_to_channel, 'cron', hour=18, minute=0, args=[bot])
    
    scheduler.start()
    logging.info("Планировщик запущен: 06:00 (размышления), 06:30 (утр. молитва), 23:00 (веч. молитва) по Алматы.")

    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())