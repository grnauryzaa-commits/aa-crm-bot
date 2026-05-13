import asyncio

from aiogram import Bot, Dispatcher

from config import TOKEN
from database import init_db

# routers
from start import router as start_router
from sponsors import router as sponsors_router
from steps import router as steps_router
from traditions import router as traditions_router
from help import router as help_router
from form import router as form_router
from admin import router as admin_router


# =====================================================
# BOT
# =====================================================

bot = Bot(token=TOKEN)

dp = Dispatcher()


# =====================================================
# ROUTERS
# =====================================================

dp.include_router(start_router)

# sponsors раньше form
dp.include_router(sponsors_router)

dp.include_router(steps_router)
dp.include_router(traditions_router)
dp.include_router(help_router)

# form почти в конце
dp.include_router(form_router)

dp.include_router(admin_router)


# =====================================================
# START BOT
# =====================================================

async def main():

    print("🚀 BOT STARTING...")

    init_db()

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())