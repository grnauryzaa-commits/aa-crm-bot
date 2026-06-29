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
        await message.answer("Ошибка: база данных не подключена.")
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
            parts = text.split('***') 
            
            quote = parts[0].strip() if len(parts) > 0 else ""
            raw_body = parts[1].strip() if len(parts) > 1 else ""

            # --- ФИЛЬТР МУСОРА ---
            stop_phrases = [
                "Место под", "1990©", "Анонимные Алкоголики", "Группа", 
                "Наша помощь", "Сайт информирует", "Даже когда мы", 
                "Содружество АА", "Основное внимание", "За каждой цитатой",
                "И если хоть одному", "Содержание ее", "В предисловии"
            ]
            
            clean_lines = []
            for line in raw_body.split('\n'):
                line = line.strip()
                if not line: continue
                if any(phrase in line for phrase in stop_phrases):
                    break
                clean_lines.append(line)
            
            clean_body = "\n\n".join(clean_lines)

            months = ["января", "февраля", "марта", "апреля", "мая", "июня", 
                      "июля", "августа", "сентября", "октября", "ноября", "декабря"]
            
            # --- ФОРМИРОВАНИЕ ВЕРХА И ТЕЛА ---
            response = (
                f"📖 <b>Ежедневные размышления АА</b>\n\n"
                f"📋 <b>{today.day} {months[today.month - 1]}</b>\n\n"
                f"<b>{title.upper()}</b>\n\n"
                f"<i>«{html.escape(quote)}»</i>\n\n"
                f"{html.escape(clean_body)}"
            )

            await message.answer(response, parse_mode="HTML")
        else:
            await message.answer("⚠️ Размышление на сегодня не найдено.")
            
    except Exception as e:
        print(f"Ошибка: {e}")
        await message.answer("❌ Произошла ошибка при загрузке размышления.")