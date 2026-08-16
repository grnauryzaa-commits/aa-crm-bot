import asyncio
import logging
from aiogram import Bot, Dispatcher
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

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

async def safe_send_reflection(bot):
    try:
        await send_daily_reflection_to_channel(bot)
    except Exception as e:
        logging.error(f"❌ Ошибка в рассылке ежедневных размышлений: {e}")

async def safe_send_morning(bot):
    try:
        await send_morning_prayer_to_channel(bot)
    except Exception as e:
        logging.error(f"❌ Ошибка в рассылке утреннего 11 шага: {e}")

async def safe_send_evening(bot):
    try:
        await send_evening_prayer_to_channel(bot)
    except Exception as e:
        logging.error(f"❌ Ошибка в рассылке вечернего 11 шага: {e}")

async def main():
    bot = Bot(token=TOKEN)
    dp = Dispatcher()
    dp.include_routers(start_router, menu_router, form_router, sponsors_router, admin_router, help_router, schedules_router, reflections_router)

    job_defaults = {
        'max_instances': 3
    }
    
    # Планировщик в зоне Алматы
    scheduler = AsyncIOScheduler(timezone="Asia/Almaty", job_defaults=job_defaults)
    
    # 06:00 по Алматы - Ежедневные размышления
    scheduler.add_job(safe_send_reflection, CronTrigger(hour=6, minute=0), args=[bot])
    # 06:30 по Алматы - Утренний 11 шаг
    scheduler.add_job(safe_send_morning, CronTrigger(hour=6, minute=30), args=[bot])
    # 01:00 ночи по Алматы - Вечерний 11 шаг (Временная проверка)
    scheduler.add_job(safe_send_evening, CronTrigger(hour=1, minute=0), args=[bot])
    
    scheduler.start()
    logging.info("Планировщик запущен в таймзоне Asia/Almaty (Вечерний 11 шаг временно на 01:00).")

    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())