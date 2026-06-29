import os
import psycopg2
from aiogram import Router, types
from aiogram.filters import Command
from datetime import datetime
import html # Добавляем для работы с текстом

router = Router()

DB_URL = os.getenv("DATABASE_URL")

# Функция для экранирования символов Markdown
def escape_markdown(text):
    # Экранируем символы, которые могут сломать Markdown: * _ ` [ ]
    chars = ['*', '_', '`', '[']
    for char in chars:
        text = text.replace(char, f"\\{char}")
    return text

@router.message(lambda message: message.text == "📖 Ежедневные размышления")
@router.message(Command("daily"))
async def send_reflection(message: types.Message):
    if not DB_URL:
        await message.answer("❌ Ошибка: переменная DATABASE_URL не найдена.")
        return

    today = datetime.now()
    
    try:
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()
        cur.execute("""
            SELECT title, text FROM reflections_archive 
            WHERE day = %s AND month = %s
        """, (today.day, today.month))
        
        row = cur.fetchone()
        cur.close()
        conn.close()

        if row:
            title, text = row
            # Разделяем по разделителю (убедись, что в fill_db такой же!)
            parts = text.split('***') # Используем *** как в твоем fill_db.py
            quote = parts[0].strip() if len(parts) > 0 else ""
            body = parts[1].strip() if len(parts) > 1 else ""

            months = [
                "января", "февраля", "марта", "апреля", "мая", "июня", 
                "июля", "августа", "сентября", "октября", "ноября", "декабря"
            ]
            
            # Экранируем переменные перед вставкой в Markdown
            response = (
                f"📖 *Ежедневные размышления АА*\n\n"
                f"📋 *{today.day} {months[today.month - 1]}*\n\n"
                f"*{escape_markdown(title)}*\n\n"
                f"« _{escape_markdown(quote)}_ »\n\n"
                f"{escape_markdown(body)}"
            )

            # Обрезаем текст, если он длиннее 4000 символов (лимит Telegram)
            if len(response) > 4000:
                response = response[:3997] + "..."

            await message.answer(response, parse_mode="MarkdownV2")
        else:
            await message.answer(f"⚠️ Размышление на {today.day} {months[today.month-1]} не найдено.")
            
    except Exception as e:
        await message.answer(f"❌ Ошибка: {str(e)[:100]}")