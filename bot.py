import asyncio
import logging
import datetime
from aiogram import Bot, Dispatcher
from config import TOKEN
from database import init_db

# Импортируем роутеры
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

# НАДЕЖНЫЙ ФОНОВЫЙ ПЛАНИРОВЩИК БЕЗ ВНЕШНИХ БИБЛИОТЕК
async def daily_scheduler(bot: Bot):
    logging.info("Фоновый планировщик утренней рассылки успешно запущен!")
    while True:
        # Получаем текущее время сервера (с учетом переменной TZ=Asia/Almaty в Railway)
        now = datetime.datetime.now()
        
        # Условие: если сейчас ровно 07 часов и 00 минут
        if now.hour == 7 and now.minute == 0:
            logging.info("Наступило 07:00 утра. Запускаю утреннюю рассылку размышлений...")
            try:
                await send_daily_reflection_to_channel(bot)
            except Exception as e:
                logging.error(f"Ошибка при автоматической отправке рассылки: {e}")
            
            # Спим 65 секунд, чтобы внутри этой же минуты рассылка не сработала повторно
            await asyncio.sleep(65)
        
        # Проверяем время каждые 30 секунд
        await asyncio.sleep(30)

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

    # КРИТИЧЕСКИ ВАЖНО: Запускаем наш таймер как фоновую задачу asyncio
    asyncio.create_task(daily_scheduler(bot))
    logging.info("Таймер рассылки Наурыз инициализирован на 07:00.")

    logging.info("Бот успешно запущен и готов к работе!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())