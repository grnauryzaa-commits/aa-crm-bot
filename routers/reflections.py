import psycopg2
from aiogram import Router, F, types, Bot
from datetime import datetime
import html
import logging

router = Router()

DB_URL = "postgresql://postgres:rjKAEdhpAeVceQzFobzCKFRbWnJwYOem@thomas.proxy.rlwy.net:12836/railway"
CHANNEL_ID = -1002140833802

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
    text = (
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
    try:
        await bot.send_message(CHANNEL_ID, text, parse_mode="HTML")
    except Exception as e:
        logging.error(f"Ошибка отправки молитвы: {e}")

@router.message(F.text == "/test_prayer")
async def test_prayer(message: types.Message, bot: Bot):
    await send_morning_prayer_to_channel(bot)
    await message.answer("Молитва 11 шага отправлена в канал.")