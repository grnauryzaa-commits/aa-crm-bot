import asyncio

from aiogram import Bot, Dispatcher
from aiogram.filters import CommandStart
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Message

from config import TOKEN
from database import init_db
from menu import main_menu

# 📦 routers
from steps import router as steps_router
from traditions import router as traditions_router
from help import router as help_router
from sponsors import router as sponsors_router
from form import router as form_router
from admin import router as admin_router


# 🚀 BOT + FSM STORAGE (ВАЖНО)
import os

print("ENV TOKEN =", os.environ.get("TOKEN"))
bot = Bot(token=TOKEN)

dp = Dispatcher(storage=MemoryStorage())


# 🧱 INIT DB
init_db()


# 📦 ROUTERS (ПРАВИЛЬНЫЙ ПОРЯДОК)
dp.include_router(help_router)
dp.include_router(steps_router)
dp.include_router(traditions_router)
dp.include_router(sponsors_router)

# ⚙️ админка ДО формы (чтобы не блокировалась)
dp.include_router(admin_router)

# 📩 форма ВСЕГДА ПОСЛЕДНЯЯ
dp.include_router(form_router)


# 🚀 START
@dp.message(CommandStart())
async def start(message: Message):

    await message.answer(
        "🤝 <b>CRM PRO BOT</b>\n\nДобро пожаловать!",
        reply_markup=main_menu,
        parse_mode="HTML"
    )


# ▶️ RUN BOT
async def main():
    print("🚀 BOT STARTING...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())