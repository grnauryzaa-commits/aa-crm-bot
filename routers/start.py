import logging
import psycopg2
from aiogram import Router, types
from aiogram.filters import Command
from routers.menu import get_main_menu_keyboard

router = Router()

DB_URL = "postgresql://postgres:rjKAEdhpAeVceQzFobzCKFRbWnJwYOem@thomas.proxy.rlwy.net:12836/railway"
ADMIN_ID = 8149962536  # Твой ID для уведомлений

@router.message(Command("start"))
async def cmd_start(message: types.Message):
    user = message.from_user
    telegram_id = user.id
    username = f"@{user.username}" if user.username else "нет username"
    full_name = user.full_name or "Без имени"

    logging.info(f"Пользователь {telegram_id} ({full_name}) нажал /start")

    # Сохраняем или обновляем пользователя в базе данных
    try:
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO users (telegram_id, username, full_name) 
            VALUES (%s, %s, %s)
            ON CONFLICT (telegram_id) 
            DO UPDATE SET username = EXCLUDED.username, full_name = EXCLUDED.full_name;
            """,
            (telegram_id, username, full_name)
        )
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        logging.error(f"Ошибка сохранения пользователя в БД: {e}")

    # Отправляем тебе уведомление о новом запуске
    try:
        await message.bot.send_message(
            ADMIN_ID,
            f"👤 <b>Новый запуск бота!</b>\n\n"
            f"Имя: {full_name}\n"
            f"Username: {username}\n"
            f"ID: <code>{telegram_id}</code>",
            parse_mode="HTML"
        )
    except Exception as e:
        logging.error(f"Не удалось отправить уведомление админу: {e}")
    
    welcome_text = (
        "🕊 **Добро пожаловать в телеграм-бот группы АА «Наурыз»!**\n\n"
        "Этот бот создан для поддержки участников нашего Содружества.\n"
        "Здесь ты можешь узнать актуальное расписание живых встреч, найти спонсора "
        "или предложить свою помощь в качестве наставника.\n\n"
        "Пожалуйста, выбери интересующий раздел в меню ниже 👇"
    )
    
    # Вызываем функцию меню
    kb = get_main_menu_keyboard()
    
    # Отправляем сообщение с текстом и кнопками
    await message.answer(welcome_text, parse_mode="Markdown", reply_markup=kb)