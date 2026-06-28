import asyncio
import logging
import sys
from aiogram import Bot, Dispatcher
from config import TOKEN
from database import init_db

# Импортируем все роутеры группы «Наурыз»
from routers.start import router as start_router
from routers.menu import router as menu_router
from routers.form import router as form_router
from routers.sponsors import router as sponsors_router
from routers.sponsors_mod import router as sponsors_mod_router
from routers.reflections import router as reflections_router

async def main():
    # Настраиваем подробный вывод логов в консоль Railway
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)]
    )
    
    logging.info("⏳ Попытка подключения и инициализации базы данных...")
    try:
        # Проверяем базу данных с таймаутом, чтобы бот не зависал вечно
        await asyncio.wait_for(init_db(), timeout=15.0)
        logging.info("✅ База данных успешно ответила.")
    except asyncio.TimeoutError:
        logging.error("❌ КРИТИЧЕСКАЯ ОШИБКА: База данных не ответила за 15 секунд! Проверь DATABASE_URL.")
    except Exception as e:
        logging.error(f"❌ КРИТИЧЕСКАЯ ОШИБКА при старте БД: {e}")

    # Создаем объекты бота и диспетчера
    bot = Bot(token=TOKEN)
    dp = Dispatcher()
    
    # Регистрируем все роутеры в строгом порядке
    dp.include_routers(
        start_router,
        menu_router,
        form_router,
        sponsors_router,
        sponsors_mod_router,
        reflections_router
    )
    
    logging.info("🧹 Очистка очереди зависших сообщений (drop_pending_updates)...")
    try:
        # Удаляем всё, что ты нажимал, пока бот висел, чтобы он не зациклился
        await bot.delete_webhook(drop_pending_updates=True)
    except Exception as e:
        logging.error(f"Не удалось очистить вебхук: {e}")

    logging.info("🚀 Бот группы «Наурыз» запущен и слушает команды...")
    try:
        await dp.start_polling(bot)
    except Exception as e:
        logging.error(f"❌ Бот упал во время полинга: {e}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Бот остановлен вручную.")