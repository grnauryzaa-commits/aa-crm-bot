import asyncio
from aiogram import Bot, Dispatcher
from config import TOKEN
from database import init_db

# Роутеры
from routers.start import router as start_router
from routers.menu import router as menu_router
from routers.form import router as form_router
from routers.help import router as help_router
from routers.schedules import router as schedules_router

async def main():
    await init_db()
    bot = Bot(token=TOKEN)
    dp = Dispatcher()
    
    # Регистрация
    dp.include_routers(start_router, menu_router, form_router, help_router, schedules_router)
    
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())