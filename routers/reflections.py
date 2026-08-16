import psycopg2
from aiogram import Router, F, types, Bot
from datetime import datetime
import html
import logging

router = Router()

DB_URL = "postgresql://postgres:rjKAEdhpAeVceQzFobzCKFRbWnJwYOem@thomas.proxy.rlwy.net:12836/railway"
CHANNEL_ID = -1002140833802

# Тексты молитв 11 шага (используются и для рассылки, и для кнопок в меню)
MORNING_PRAYER_TEXT = (
    "🌾 <b>Действия 11 шага по БК АА</b>\n"
    "<i>Утренняя Часть</i>\n\n"
    "1. <b>Молитва</b> в самом начале дня :\n"
    "<i>«Боже, направь мои помыслы в верное русло, убереги меня от жалости к себе, бесчестных поступков, корыстолюбия».</i>\n\n"
    "2. Утром, надо <b>подумать о предстоящем дне.</b>\n\n"
    "3. Размышляя о предстоящем дне... Если есть неуверенность, - <b>молитва:</b>\n"
    "<i>«Боже, дай мне вдохновение, интуитивные мысли или решения».</i>\n\n"
    "4. <b>Погружаемся в медитацию.</b>\n"
    "<i>«Боже, открой, каким должен быть мой следующий шаг, и дай мне всё, что необходимо для решения моих проблем. Освободи меня от своеволия».</i>\n\n"
    "5. В течение дня, <b>если появляются сомнения</b>:\n"
    " <i>«Боже, укажи правильную мысль или действие».</i>\n\n"
    "6. <b>Да исполнится воля Твоя, а не моя.</b>\n"
    "Аминь 📖🙏"
)

EVENING_PRAYER_TEXT = (
    "🌙 <b>Действия 11 шага по БК АА</b>\n"
    "<i>Вечерняя Часть (Подведение итогов)</i>\n\n"
    "Вечером, перед сном, мы подводим итоги дня:\n\n"
    "1. Был ли я сегодня эгоистичен? Нечестен? Озлоблен? Испытывал ли страх?\n"
    "2. Должен ли я перед кем-то извиниться?\n"
    "3. Был ли я добр и внимателен к окружающим?\n"
    "4. Что я мог бы сделать лучше?\n"
    "5. Думал ли я о том, чем могу быть полезен другим?\n\n"
    "<i>Затем мы прощаем всех, а свои ошибки вручаем Высшей Силе, прося о прощении и избавлении.</i>\n\n"
    "🙏 <b>Спокойной ночи!</b>"
)

def format_reflection_text(text, today):
    lines = [l.strip() for l in text.split('\n') if l.strip()]
    forbidden = [
        "WWW.MOS-NACH.RU", "Анонимные Алкоголики.", "Группа", "Поделиться:", 
        "Рассказать:", "Twitter", "Facebook", "Vkontakte", "WhatsApp", 
        "Telegram", "EMail", "Тег audio", "Aудио-ежедневник", 
        "Skype", "Mail", "Альтернативный вариант",
        "Ежедневные Размышления на", "Сегодня"
    ]
    filtered = [line for line in lines if not any(f in line for f in forbidden)]
    if len(filtered) > 0 and f"{today.day}" in filtered[0] and "июня" in filtered[0].lower() and len(filtered[0]) < 20:
        filtered.pop(0)
    
    body = "\n\n".join(filtered)
    months = ["января", "февраля", "марта", "апреля", "мая", "июня", 
              "июля", "августа", "сентября", "октября", "ноября", "декабря"]
    return f"📖 <b>Ежедневные размышления АА</b>\n\n📋 <b>{today.day} {months[today.month - 1]}</b>\n\n{html.escape(body)}"

async def send_daily_reflection_to_channel(bot: Bot):
    today = datetime.now()
    try:
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()
        cur.execute("SELECT text FROM reflections_archive WHERE day = %s AND month = %s", (today.day, today.month))
        row = cur.fetchone()
        cur.close()
        conn.close()
        if row:
            await bot.send_message(CHANNEL_ID, format_reflection_text(row[0], today), parse_mode="HTML")
    except Exception as e:
        logging.error(f"Ошибка рассылки размышлений: {e}")

async def send_morning_prayer_to_channel(bot: Bot):
    try:
        await bot.send_message(CHANNEL_ID, MORNING_PRAYER_TEXT, parse_mode="HTML")
    except Exception as e:
        logging.error(f"Ошибка отправки молитвы: {e}")

async def send_evening_prayer_to_channel(bot: Bot):
    try:
        await bot.send_message(CHANNEL_ID, EVENING_PRAYER_TEXT, parse_mode="HTML")
    except Exception as e:
        logging.error(f"Ошибка отправки вечерней молитвы: {e}")

@router.message(F.text == "/test_send")
async def test_send(message: types.Message, bot: Bot):
    await send_daily_reflection_to_channel(bot)
    await message.answer("Ежедневные размышления отправлены.")

@router.message(F.text == "/test_prayer")
async def test_prayer(message: types.Message, bot: Bot):
    await send_morning_prayer_to_channel(bot)
    await message.answer("Утренняя молитва 11 шага отправлена.")

@router.message(F.text == "/test_evening")
async def test_evening(message: types.Message, bot: Bot):
    await send_evening_prayer_to_channel(bot)
    await message.answer("Вечерняя молитва 11 шага отправлена.")