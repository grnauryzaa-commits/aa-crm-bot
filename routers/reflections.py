@router.message(F.text == "📖 Ежедневные размышления")
async def show_reflections(message: types.Message):
    # Берем текущие дату и месяц
    now = datetime.now()
    
    try:
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()
        
        # Запрос без лишних усложнений
        cur.execute(
            "SELECT title, text FROM reflections_archive WHERE day = %s AND month = %s", 
            (now.day, now.month)
        )
        row = cur.fetchone()
        
        # Если пусто, берем хотя бы последнюю запись из базы для проверки
        if not row:
            cur.execute("SELECT title, text FROM reflections_archive ORDER BY month DESC, day DESC LIMIT 1")
            row = cur.fetchone()
            await message.answer("⚠️ На сегодня размышлений не найдено, но вот последнее, что есть в базе:")
            
        cur.close()
        conn.close()
        
        if row:
            await message.answer(f"📖 **{row[0]}**\n\n{row[1]}")
        else:
            await message.answer("База данных пуста. Запустите скрипт заполнения снова.")
            
    except Exception as e:
        await message.answer(f"Ошибка БД: {e}")