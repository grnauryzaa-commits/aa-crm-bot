import asyncio
import logging
from aiogram import Bot, Dispatcher
from config import BOT_TOKEN
# Импортируем ВСЕ роутеры, включая новые
from routers import form, sponsors, sponsors_mod, help, schedules

async def main():
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()

    # Подключаем ВСЕ роутеры в диспетчер
    dp.include_router(form.router)
    dp.include_router(sponsors.router)
    dp.include_router(sponsors_mod.router)
    dp.include_router(help.router)      # Обязательно
    dp.include_router(schedules.router) # Обязательно

    logging.info("Бот успешно запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())