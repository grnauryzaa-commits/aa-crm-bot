import asyncio
from aiogram import Bot, Dispatcher

from config import TOKEN
from database import init_db

from routers.start import router as start_router
from routers.menu import router as menu_router
from routers.form import router as form_router
from routers.sponsors import router as sponsors_router
from routers.admin import router as admin_router
from routers.help import router as help_router
from routers.schedules import router as daily_router

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Регистрируем все роутеры
dp.include_router(start_router)
dp.include_router(form_router)
dp.include_router(sponsors_router)
dp.include_router(admin_router)
dp.include_router(help_router)
dp.include_router(daily_router)

async def main():
    print("🚀 BOT STARTING...")
    init_db()  # Инициализация БД
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())