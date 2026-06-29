@router.message(lambda message: message.text == "📖 Ежедневные размышления")
@router.message(Command("daily"))
async def send_reflection(message: types.Message):
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
            parts = text.split('\n\n')
            
            # Цитата — первый блок, остальное — текст. Источник (parts[1]) пропускаем.
            quote = parts[0] if len(parts) > 0 else ""
            body = "\n\n".join(parts[2:]) if len(parts) > 2 else ""

            # Формируем сообщение
            # Используем месяц в текстовом виде (для красоты)
            months = [
                "января", "февраля", "марта", "апреля", "мая", "июня", 
                "июля", "августа", "сентября", "октября", "ноября", "декабря"
            ]
            date_str = f"{today.day} {months[today.month - 1]}"

            response = (
                f"📖 **Ежедневные размышления АА**\n\n"
                f"📋 **{date_str}**\n\n"
                f"**{title}**\n\n"
                f"**{quote}**\n\n"
                f"{body}"
            )
            
            await message.answer(response, parse_mode="Markdown")
        else:
            await message.answer("⚠️ Размышление на сегодня пока не найдено.")
            
    except Exception as e:
        await message.answer("❌ Произошла ошибка при доступе к базе данных.")