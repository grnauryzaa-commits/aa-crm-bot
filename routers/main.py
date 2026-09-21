import asyncio
import logging
import sys
sys.path.append('.')

from aiogram import Bot, Dispatcher
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from config import TOKEN 
from database import init_db

from routers.start import router as start_router
from routers.menu import router as menu_router
from routers.form import router as form_router
from routers.sponsors import router as sponsors_router
from routers.admin import router as admin_router
from routers.help import router as help_router
from routers.schedules import router as schedules_router
from routers.reflections import (
    send_daily_reflection_to_channel, 
    send_morning_prayer_to_channel,
    send_evening_prayer_to_channel
)
from routers.ai_chat import router as ai_chat_router

logging.basicConfig(level=logging.INFO)

# Функция для отправки контента сразу на двух языках с паузой в 1 секунду
async def send_bilingual_reflection(bot):
    await send_daily_reflection_to_channel(bot, lang="ru")
    await asyncio.sleep(1)
    await send_daily_reflection_to_channel(bot, lang="kk")

async def send_bilingual_morning_prayer(bot):
    await send_morning_prayer_to_channel(bot, lang="ru")
    await asyncio.sleep(1)
    await send_morning_prayer_to_channel(bot, lang="kk")

async def send_bilingual_evening_prayer(bot):
    await send_evening_prayer_to_channel(bot, lang="ru")
    await asyncio.sleep(1)
    await send_evening_prayer_to_channel(bot, lang="kk")

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
        ai_chat_router
    )

    scheduler = AsyncIOScheduler(timezone="Asia/Almaty")
    
    # 06:00 - Ежедневные размышления (Русский + Казахский)
    scheduler.add_job(send_bilingual_reflection, CronTrigger(hour=6, minute=0), args=[bot])
    
    # 06:30 - Утренний 11 шаг (Русский + Казахский)
    scheduler.add_job(send_bilingual_morning_prayer, CronTrigger(hour=6, minute=30), args=[bot])
    
    # 23:00 - Вечерний 11 шаг (Русский + Казахский)
    scheduler.add_job(send_bilingual_evening_prayer, CronTrigger(hour=23, minute=0), args=[bot])
    
    scheduler.start()
    logging.info("Планировщик двухъязычной рассылки запущен в таймзоне Asia/Almaty.")

    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())