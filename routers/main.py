import asyncio
import logging
import sys
sys.path.append('.')

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
# Импортируем функции рассылки напрямую
from routers.reflections import (
    send_daily_reflection_to_channel, 
    send_morning_prayer_to_channel,
    send_evening_prayer_to_channel
)
from routers.ai_chat import router as ai_chat_router  # Отдельный роутер для ИИ

logging.basicConfig(level=logging.INFO)

async def main():
    bot = Bot(token=TOKEN)
    dp = Dispatcher()
    
    # Подключаем все рабочие роутеры
    # ВАЖНО: ai_chat_router (ИИ) стоит строго последним, чтобы не перехватывать кнопки!
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

    # Настраиваем планировщик для отправки контента в канал по расписанию
    scheduler = AsyncIOScheduler(timezone="Asia/Almaty")
    
    # 06:00 - Ежедневные размышления в канал
    scheduler.add_job(send_daily_reflection_to_channel, CronTrigger(hour=6, minute=0), args=[bot])
    # 06:30 - Утренний 11 шаг в канал
    scheduler.add_job(send_morning_prayer_to_channel, CronTrigger(hour=6, minute=30), args=[bot])
    # 23:00 - Вечерний 11 шаг в канал
    scheduler.add_job(send_evening_prayer_to_channel, CronTrigger(hour=23, minute=0), args=[bot])
    
    scheduler.start()
    logging.info("Планировщик запущен в таймзоне Asia/Almaty.")

    # Запуск бота
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())