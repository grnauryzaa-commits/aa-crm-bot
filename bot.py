import asyncio
import logging
from aiogram import Bot, Dispatcher
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from pytz import utc

from config import TOKEN
from database import init_db
from routers import start, menu, form, reflections, help, schedules, sponsors
from routers.reflections import send_daily_reflection_to_channel

# Настройка логирования
logging.basicConfig(level=logging.INFO)

async def scheduled_reflections_job(bot):
    """
    Задача для планировщика: 
    1. Отправляет размышление на казахском языке (из таблицы reflections)
    2. Делает паузу в 2 секунды
    3. Отправляет размышление на русском языке (из таблицы reflections_archive)
    """
    logging.info("Запуск плановой отправки ежедневных размышлений...")
    
    # Отправка на казахском (lang="kk")
    await send_daily_reflection_to_channel(bot, lang="kk")
    await asyncio.sleep(2)
    
    # Отправка на русском (lang="ru")
    await send_daily_reflection_to_channel(bot, lang="ru")
    
    logging.info("Плановая отправка размышлений завершена.")

async def main():
    # 1. Инициализация локальной/удаленной базы данных
    await init_db()
    
    # 2. Инициализация бота и диспетчера
    bot = Bot(token=TOKEN)
    dp = Dispatcher()
    
    # 3. Подключение всех роутеров
    dp.include_routers(
        start.router, 
        menu.router, 
        form.router, 
        reflections.router, 
        help.router, 
        schedules.router, 
        sponsors.router
    )
    
    # 4. Настройка планировщика задач (07:00 по времени Алматы = 01:00 UTC)
    scheduler = AsyncIOScheduler(timezone=utc)
    scheduler.add_job(
        scheduled_reflections_job,  
        trigger='cron', 
        hour=1, 
        minute=0, 
        args=[bot]
    )
    scheduler.start()
    logging.info("Планировщик рассылки успешно запущен (01:00 UTC / 07:00 Алматы).")

    # 5. Запуск бота
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Бот остановлен пользователем.")