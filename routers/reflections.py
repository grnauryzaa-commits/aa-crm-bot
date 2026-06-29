import os
import psycopg2
from aiogram import Router, types
from aiogram.filters import Command
from datetime import datetime
import html

router = Router()
DB_URL = os.getenv("DATABASE_URL")

@router.message(lambda message: message.text == "📖 Ежедневные размышления")
@router.message(Command("daily"))
async def send_reflection(message: types.Message):
    if not DB_URL:
        return

    today = datetime.now()
    
    try:
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()
        cur.execute("SELECT title, text FROM reflections_archive WHERE day = %s AND month = %s", 
                    (today.day, today.month))
        row = cur.fetchone()
        cur.close()
        conn.close()

        if row:
            title, text = row
            # Разделяем на части (предполагаем, что разделитель ***)
            parts = text.split('***') 
            
            # Цитата и основной текст
            quote = parts[0].strip() if len(parts) > 0 else ""
            full_body = parts[1].strip() if len(parts) > 1 else ""

            # --- ФИЛЬТРЫ ОЧИСТКИ МУСОРА ---
            trash_filters = [
                "1990©", "Alcoholics Anonymous", "Анонимные Алкоголики", 
                "Группа", "Наша помощь", "Сайт информирует", 
                "Даже когда мы", "Место под", "всемирного содружества"
            ]
            
            clean_body_lines = []
            for line in full_body.split('\n'):
                line = line.strip()
                if not line: continue
                # Если строка содержит мусор, пропускаем её
                if any(filter_word in line for filter_word in trash_filters):
                    continue
                clean_body_lines.append(line)
            
            clean_body = "\n\n".join(clean_body_lines)
            # -------------------------------

            months = ["января", "февраля", "марта", "апреля", "мая", "июня", 
                      "июля", "августа", "сентября", "октября", "ноября", "декабря"]
            
            # Формируем красивое сообщение
            response = (
                f"📋 <b>{today.day} {months[today.month - 1]}</b>\n\n"
                f"<b>{title.upper()}</b>\n\n"
                f"{html.escape(quote)}\n\n"
                f"{html.escape(clean_body)}"
            )

            await message.answer(response, parse_mode="HTML")
        else:
            await message.answer("⚠️ Размышление на сегодня не найдено.")
            
    except Exception as e:
        print(f"Ошибка: {e}")