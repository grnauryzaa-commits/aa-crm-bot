from aiogram import Router, F, types
from datetime import datetime
import logging
from database import get_db_connection

router = Router()

@router.message(F.text == "📘 Ежедневные размышления")
async def show_reflections(message: types.Message):
    # Получаем текущую дату в формате "день-месяц" (например, "22-06")
    now = datetime.now()
    day_month_key = now.strftime("%d-%m")
    
    # Названия месяцев на русском для заголовка (на случай, если в БД пусто)
    months_ru = {
        1: "января", 2: "февраля", 3: "марта", 4: "апреля", 5: "мая", 6: "июня",
        7: "июля", 8: "августа", 9: "сентября", 10: "октября", 11: "ноября", 12: "декабря"
    }
    current_date_str = f"{now.day} {months_ru[now.month]}"

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        # Ищем размышление на сегодняшний день
        cursor.execute(
            "SELECT date_title, heading, quote, source, reflection FROM daily_reflections WHERE day_month = %s;", 
            (day_month_key,)
        )
        row = cursor.fetchone()
        cursor.close()
        conn.close()

        if row:
            # Если нашли в базе данных, выводим красиво оформленный текст
            text = (
                f"📅 **{row['date_title']}**\n\n"
                f"☀️ **{row['heading'].upper()}**\n\n"
                f"«{row['quote']}»\n"
                f"_* {row['source']}_\n\n"
                f"{row['reflection']}"
            )
        else:
            # Временный демонстрационный режим (Твой пример для 22 июня)
            # Если базы данных еще нет, бот покажет этот пример для наглядности
            text = (
                f"📅 **{current_date_str}**\n\n"
                f"☀️ **СЕГОДНЯ Я СВОБОДЕН**\n\n"
                "«Это привело меня к здравому осознанию того, что в мире еще много ситуаций, перед которыми лично я — бессилен. "
                "Если я с готовностью признал это в случае с алкоголем, то должен признать то же самое и в отношении многого другого. "
                "Мне надо успокоться и уяснить, что это Он — Бог, а вовсе не я.»\n"
                "_* Как это видит Билл (As Bill Sees It, p. 134)_\n\n"
                "Чтобы наслаждаться душевным покоем, я учусь принимать все как есть во всех ситуациях. Было время, когда жизнь была "
                "для меня постоянной битвой, — мне казалось, что каждый день я должен до полной победы сражаться с самим собой и с другими. "
                "В конце концов я проиграл это сражение. Всегда кончалось тем, что я напивался и оплакивал свое незавидное положение. "
                "Только позволив событиям идти своим чередом, а Богу — взять мою жизнь, я обрел душевный покой. Сегодня я свободен. "
                "Мне больше не надо ни с кем и ни с чем сражаться."
            )
            
        await message.answer(text, parse_mode="Markdown")
        
    except Exception as e:
        logging.error(f"Ошибка при загрузке размышления: {e}")
        await message.answer("⚠️ Не удалось загрузить размышление на сегодня. Попробуйте позже.")