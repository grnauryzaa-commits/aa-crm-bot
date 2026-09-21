from datetime import datetime
import html
import asyncio
import logging
import psycopg2

DB_URL = "postgresql://postgres:rjKAEdhpAeVceQzFobzCKFRbWnJwYOem@thomas.proxy.rlwy.net:12836/railway"
CHANNEL_ID = -1002140833802

# Тексты молитв 11 шага (Русский язык)
MORNING_PRAYER_TEXT_RU = (
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

EVENING_PRAYER_TEXT_RU = (
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

# Тексты молитв 11 шага (Казахский язык)
MORNING_PRAYER_TEXT_KK = (
    "🌾 <b>АА ҚБ бойынша 11-ші қадам әрекеттері</b>\n"
    "<i>Таңғы бөлім</i>\n\n"
    "1. Күннің басындағы <b>дұға</b>:\n"
    "<i>«Құдайым, ойымды дұрыс арнаға бағытта, өзімді аяудан, арсыз әрекеттерден, дүниеқоңыздықтан сақта».</i>\n\n"
    "2. Таңертең <b>алдағы күн туралы ойлану керек.</b>\n\n"
    "3. Алдағы күн туралы ойлана отырып... Егер сенімсіздік болса, - <b>дұға:</b>\n"
    "<i>«Құдайым, маған шабыт, интуитивті ойлар немесе шешімдер бер».</i>\n\n"
    "4. <b>Медитацияға терең бойлаймыз.</b>\n"
    "<i>«Құдайым, келесі қадамым қандай болу керектігін ашып көрсет, және мәселелерімізді шешуге қажеттінің бәрін бер. Мені өз білімділігімнен азат ет».</i>\n\n"
    "5. Күн бойы, <b>күмәнданған жағдайда</b>:\n"
    " <i>«Құдайым, дұрыс ойды немесе әрекетті нұсқап көрсет».</i>\n\n"
    "6. <b>Менің емес, Өзіңнің еркің орындалсын.</b>\n"
    "Аумин 📖🙏"
)

EVENING_PRAYER_TEXT_KK = (
    "🌙 <b>АА ҚБ бойынша 11-ші қадам әрекеттері</b>\n"
    "<i>Кешкі бөлім (Қорытынды жасау)</i>\n\n"
    "Кшке, ұйықтар алдында, біз күннің қорытындысын жасаймыз:\n\n"
    "1. Мен бүгін эгоист болдым ба? Әділетсіз болдым ба? Ашуландым ба? Қорқынышты сездім бе?\n"
    "2. Біреуден кешірім сұрауым керек пе?\n"
    "3. Айналамдағыларға мейірімді әрі мұқият болдым ба?\n"
    "4. Мен нені жақсырақ жасай алар едім?\n"
    "5. Басқаларға қалай пайдалы бола алатыным туралы ойладым ба?\n\n"
    "<i>Содан кейін бәрін кешіреміз, ал өз қателіктерімізді Жоғары Күшке тапсырып, кешірім мен құтқаруды сұраймыз.</i>\n\n"
    "🙏 <b>Қайырлы түн!</b>"
)

MORNING_PRAYER_TEXT = MORNING_PRAYER_TEXT_RU
EVENING_PRAYER_TEXT = EVENING_PRAYER_TEXT_RU


def format_reflection_text(text, today, lang="ru"):
    lines = [l.strip() for l in text.split('\n') if l.strip()]
    forbidden = [
        "WWW.MOS-NACH.RU", "Анонимные Алкоголики.", "Группа", "Поделиться:", 
        "Рассказать:", "Twitter", "Facebook", "Vkontakte", "WhatsApp", 
        "Telegram", "EMail", "Тег audio", "Aудио-ежедневник", "Skype", "Mail", 
        "Альтернативный вариант", "Ежедневные Размышления на", "Сегодня"
    ]
    filtered = [line for line in lines if not any(f in line for f in forbidden)]
    if len(filtered) > 0 and f"{today.day}" in filtered[0] and len(filtered[0]) < 20:
        filtered.pop(0)
    
    body = "\n\n".join(filtered)
    
    if lang == "kk":
        months_kk = [
            "қаңтардың", "ақпанның", "наурыздың", "сәуірдің", "мамырдың", "маусымның", 
            "шілденің", "тамыздың", "қыркүйектің", "қазанның", "қарашаның", "желтоқсанның"
        ]
        return f"📖 <b>АА Күнделікті ой-толғаулары</b>\n\n📋 <b>{today.day} {months_kk[today.month - 1]}</b>\n\n{html.escape(body)}"
    else:
        months_ru = [
            "января", "февраля", "марта", "апреля", "мая", "июня", 
            "июля", "августа", "сентября", "октября", "ноября", "декабря"
        ]
        return f"📖 <b>Ежедневные размышления АА</b>\n\n📋 <b>{today.day} {months_ru[today.month - 1]}</b>\n\n{html.escape(body)}"


async def send_daily_reflection_to_channel(bot):
    """Отправка ежедневных размышлений: казахский из таблицы reflections, русский из reflections_archive"""
    today = datetime.now()
    
    months_map_kk = {
        1: "Январь", 2: "Февраль", 3: "Март", 4: "Апрель", 
        5: "Май", 6: "Июнь", 7: "Июль", 8: "Август", 
        9: "Сентябрь", 10: "Октябрь", 11: "Ноябрь", 12: "Декабрь"
    }
    current_month_name = months_map_kk.get(today.month, "Январь")

    try:
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()
        
        # 1. Получаем казахский вариант из таблицы reflections
        cur.execute("SELECT title, text FROM reflections WHERE month = %s LIMIT 1 OFFSET %s", 
                    (current_month_name, today.day - 1))
        row_kk = cur.fetchone()

        # 2. Получаем русский вариант из таблицы reflections_archive 
        # (если структура полей такая же: month, title, text)
        cur.execute("SELECT title, text FROM reflections_archive WHERE month = %s LIMIT 1 OFFSET %s", 
                    (current_month_name, today.day - 1))
        row_ru = cur.fetchone()
        
        cur.close()
        conn.close()
        
        # Отправляем казахский вариант
        if row_kk:
            title_kk, content_kk = row_kk
            full_text_kk = f"📌 <b>{title_kk}</b>\n\n{content_kk}"
            text_kk = format_reflection_text(full_text_kk, today, lang="kk")
            await bot.send_message(CHANNEL_ID, text_kk, parse_mode="HTML")
            await asyncio.sleep(1)
        else:
            logging.warning(f"Казахское размышление на сегодня (месяц: {current_month_name}, день: {today.day}) не найдено.")

        # Отправляем русский вариант
        if row_ru:
            title_ru, content_ru = row_ru
            full_text_ru = f"📌 <b>{title_ru}</b>\n\n{content_ru}"
            text_ru = format_reflection_text(full_text_ru, today, lang="ru")
            await bot.send_message(CHANNEL_ID, text_ru, parse_mode="HTML")
        else:
            logging.warning(f"Русское размышление на сегодня в reflections_archive не найдено.")
            
    except Exception as e:
        logging.error(f"Ошибка двуязычной рассылки размышлений из БД: {e}")


async def send_morning_prayer_to_channel(bot):
    """Отправка утренней молитвы 11 шага сразу на двух языках"""
    try:
        await bot.send_message(CHANNEL_ID, MORNING_PRAYER_TEXT_KK, parse_mode="HTML")
        await asyncio.sleep(1)
        await bot.send_message(CHANNEL_ID, MORNING_PRAYER_TEXT_RU, parse_mode="HTML")
    except Exception as e:
        logging.error(f"Ошибка отправки утренней молитвы: {e}")


async def send_evening_prayer_to_channel(bot):
    """Отправка вечерней молитвы 11 шага сразу на двух языках"""
    try:
        await bot.send_message(CHANNEL_ID, EVENING_PRAYER_TEXT_KK, parse_mode="HTML")
        await asyncio.sleep(1)
        await bot.send_message(CHANNEL_ID, EVENING_PRAYER_TEXT_RU, parse_mode="HTML")
    except Exception as e:
        logging.error(f"Ошибка отправки вечерней молитвы: {e}")