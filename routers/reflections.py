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
    
    filtered = []
    for line in lines:
        if any(f in line for f in forbidden):
            continue
        if f"{today.day}" in line and "июня" in line.lower() and len(line) < 20:
            continue
        filtered.append(line)
    
    body = "\n\n".join(filtered)
    
    months = ["января", "февраля", "марта", "апреля", "мая", "июня", 
              "июля", "августа", "сентября", "октября", "ноября", "декабря"]
    
    return (
        f"📖 <b>Ежедневные размышления АА</b>\n\n"
        f"📋 <b>{today.day} {months[today.month - 1]}</b>\n\n"
        f"{html.escape(body)}"
    )

async def send_daily_reflection_to_channel(bot: Bot):
    today = datetime.now()
    try:
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()
        cur.execute("SELECT text FROM reflections_archive WHERE day = %s AND month = %s", 
                    (today.day, today.month))
        row = cur.fetchone()
        cur.close()
        conn.close()

        if row:
            text_content = format_reflection_text(row[0], today)
            await bot.send_message(CHANNEL_ID, text_content, parse_mode="HTML")
        else:
            logging.error("Размышление на сегодня не найдено в базе.")
    except Exception as e:
        logging.error(f"Ошибка рассылки: {e}")

async def send_morning_prayer_to_channel(bot: Bot):
    text = (
        "🌾 <b>Действия 11 шага по БК АА</b>\n"
        "<i>Утренняя Часть</i>\n\n"
        "<i>Одиннадцатый шаг предлагает молитву и углублённое размышление (медитацию). Она помогает при усердии и соответствующем отношении к ней. Мы можем предложить кое-что ценное и определённое.</i>\n\n"
        "1. <b>Молитва</b> в самом начале дня :\n"
        "<i>«Боже, направь мои помыслы в верное русло, убереги меня от жалости к себе, бесчестных поступков, корыстолюбия».</i>\n\n"
        "2. Утром, надо <b>подумать о предстоящем дне.</b>\n"
        "Рассмотрим наши планы.\n"
        "(Чтобы что-то рассмотреть, возможно это стоит написать.)\n\n"
        "3. Размышляя о предстоящем дне... Если есть неуверенность или не способен решить, какие действия предпринять, -  <b>молитва:</b>\n"
        "<i>«Боже, дай мне вдохновение, интуитивные мысли или решения».</i>\n\n"
        "4. <b>Погружаемся в медитацию.</b>\n"
        "(Тихое время, углублённое размышление.)\n"
        "Мы успокаиваемся и не нервничаем. Мы ни с кем и ни с чем не боремся.\n"
        "<b>Заканчиваем период углублённого размышления молитвой</b> :\n"
        "<i>«Боже, открой (покажи), каким должен быть мой следующий шаг, и дай мне всё, что необходимо для решения моих проблем. Освободи меня от своеволия».</i>\n\n"
        "5. В течение дня, <b>если появляются сомнения или волнения</b> по какому-то поводу, нужно сделать паузу и попросить Бога:\n"
        " <i>«Боже, укажи правильную мысль или действие».</i>\n\n"
        "6. <b>Мы постоянно напоминаем себе</b>, что мы больше не мним себя центром вселенной, смиренно повторяя каждый день:\n"
        " <i>«Да исполнится воля Твоя, а не моя».</i>\n"
        "Аминь 📖🙏"
    )
    try:
        await bot.send_message(CHANNEL_ID, text, parse_mode="HTML")
    except Exception as e:
        logging.error(f"Ошибка при отправке утренней молитвы: {e}")

@router.message(F.text == "📖 Ежедневные размышления")
async def show_reflections(message: types.Message):
    today = datetime.now()
    try:
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()
        cur.execute("SELECT text FROM reflections_archive WHERE day = %s AND month = %s", 
                    (today.day, today.month))
        row = cur.fetchone()
        cur.close()
        conn.close()

        if row:
            text = format_reflection_text(row[0], today)
            await message.answer(text, parse_mode="HTML")
        else:
            await message.answer("⚠️ Размышление на сегодня не найдено.")
    except Exception as e:
        logging.error(f"Ошибка вывода: {e}")
        await message.answer("❌ Ошибка при получении размышления.")

@router.message(F.text == "/test_send")
async def test_send(message: types.Message, bot: Bot):
    await message.answer("Попытка запуска тестовой рассылки размышлений...")
    try:
        await send_daily_reflection_to_channel(bot)
        await message.answer("Рассылка размышлений успешно выполнена!")
    except Exception as e:
        await message.answer(f"Ошибка: {str(e)}")
        logging.error(f"Тест рассылки упал: {e}")

@router.message(F.text == "/test_prayer")
async def test_prayer(message: types.Message, bot: Bot):
    await message.answer("Попытка запуска тестовой утренней молитвы...")
    try:
        await send_morning_prayer_to_channel(bot)
        await message.answer("Утренняя молитва успешно отправлена в канал!")
    except Exception as e:
        await message.answer(f"Ошибка: {str(e)}")
        logging.error(f"Тест молитвы упал: {e}")