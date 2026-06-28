import asyncio
from aiogram import Bot, Dispatcher
from config import TOKEN
from database import init_db
from routers import start, menu, form, reflections, help, schedules, sponsors

async def main():
    await init_db()
    bot = Bot(token=TOKEN)
    dp = Dispatcher()
    
    # Твои старые роутеры в списке
    dp.include_routers(
        start.router, menu.router, form.router, 
        reflections.router, help.router, schedules.router, sponsors.router
    )
    
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())