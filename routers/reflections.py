from datetime import datetime
import html
import asyncio
import logging
import re
import psycopg2

DB_URL = "postgresql://postgres:rjKAEdhpAeVceQzFobzCKFRbWnJwYOem@thomas.proxy.rlwy.net:12836/railway"
CHANNEL_ID = -1002140833802

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
    "Кешке, ұйықтар алдында, біз күннің қорытындысын жасаймыз:\n\n"
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
    marker_start = re.search(
        r"Сегодня\s*\d+\s+[А-Яа-яЁёӘҒҚҢӨҰҮҺІәғқңөұүһі]+",
        text,
        flags=re.IGNORECASE,
    )
    if marker_start:
        cleaned = text[marker_start.end():]
    else:
        cleaned = text

    for stop in [
        "Рассказать:",
        "Поделиться:",
        "Aудио-ежедневник:",
        "Аудио-ежедневник:",
        "Тег audio",
        "Альтернативный вариант",
    ]:
        idx = cleaned.find(stop)
        if idx != -1:
            cleaned = cleaned[:idx]

    garbage_patterns = [
        r"WWW\.MOS-NACH\.RU",
        r"Группа\s*\"[^\"]*\"",
        r"г\.\s*Москва\.?",
        r"Поделиться:?",
        r"Рассказать:?",
        r"Twitter",
        r"Facebook",
        r"Vkontakte",
        r"Skype",
        r"WhatsApp",
        r"Telegram",
        r"EMail",
        r"\bMail\b",
        r"Тег\s*audio.*",
        r"Альтернативный вариант ежедневника\.?",
        r"Ежедневные Размышления на\s+\d+\s+\w+\.?",
        # Казахские сноски
        r"Анонимді Алкоголиктер,?\s*\d+[-–]бет",
        r"Alcoholics Anonymous,?\s*\d+[-–]бет",
        r"Анонимді Алкоголиктер",
        r"\d+[-–]бет",
    ]
    for pattern in garbage_patterns:
        cleaned = re.sub(pattern, " ", cleaned, flags=re.IGNORECASE)

    cleaned = re.sub(r"\s+", " ", cleaned).strip()

    title_match = re.search(
        r"([А-ЯЁӘҒҚҢӨҰҮҺІA-Z]"
        r"[А-ЯЁӘҒҚҢӨҰҮҺІA-Z\s\-–—,\.!?]{4,80}?)"
        r"(?=\s+[А-ЯЁӘҒҚҢӨҰҮҺІA-Z][а-яёәғқңөұүһіa-z])",
        cleaned,
    )
    reflection_title = None
    if title_match:
        candidate = title_match.group(1).strip(" .,-–—")
        words = [w for w in candidate.split() if len(w) >= 2]
        if 1 < len(words) <= 8:
            reflection_title = candidate
            cleaned = cleaned[title_match.end():].strip()

    sentences = re.split(
        r"(?<=[.!?])\s+(?=[А-ЯЁӘҒҚҢӨҰҮҺІA-Z«\"(])", cleaned
    )
    paragraphs = []
    current = []
    for s in sentences:
        s = s.strip()
        if not s:
            continue
        current.append(s)
        if len(current) >= 3:
            paragraphs.append(" ".join(current))
            current = []
    if current:
        paragraphs.append(" ".join(current))

    body = "\n\n".join(paragraphs)

    if reflection_title:
        body_final = (
            f"<b>{html.escape(reflection_title)}</b>\n\n{html.escape(body)}"
        )
    else:
        body_final = html.escape(body)

    if lang == "kk":
        months_kk = [
            "қаңтардың", "ақпанның", "наурыздың", "сәуірдің", "мамырдың",
            "маусымның", "шілденің", "тамыздың", "қыркүйектің", "қазанның",
            "қарашаның", "желтоқсанның",
        ]
        return (
            f"📖 <b>АА Күнделікті ой-толғаулары</b>\n\n"
            f"📋 <b>{today.day} {months_kk[today.month - 1]}</b>\n\n"
            f"{body_final}"
        )
    else:
        months_ru = [
            "января", "февраля", "марта", "апреля", "мая", "июня",
            "июля", "августа", "сентября", "октября", "ноября", "декабря",
        ]
        return (
            f"📖 <b>Ежедневные размышления АА</b>\n\n"
            f"📋 <b>{today.day} {months_ru[today.month - 1]}</b>\n\n"
            f"{body_final}"
        )
    

async def send_daily_reflection_to_channel(
    bot, lang="ru", target_chat_id=CHANNEL_ID
):
    today = datetime.now()
    months_map_kk = {
        1: "Январь", 2: "Февраль", 3: "Март", 4: "Апрель",
        5: "Май", 6: "Июнь", 7: "Июль", 8: "Август",
        9: "Сентябрь", 10: "Октябрь", 11: "Ноябрь", 12: "Декабрь",
    }
    current_month_name = months_map_kk.get(today.month, "Январь")

    try:
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()

        if lang == "kk":
            cur.execute(
                "SELECT title, text FROM reflections "
                "WHERE month = %s ORDER BY id LIMIT 1 OFFSET %s",
                (current_month_name, today.day - 1),
            )
            row = cur.fetchone()
        else:
            cur.execute(
                "SELECT title, text FROM reflections_archive "
                "WHERE month = %s AND day = %s LIMIT 1",
                (today.month, today.day),
            )
            row = cur.fetchone()

        cur.close()
        conn.close()

        if row:
            title, content = row
            if lang == "kk" and title:
                combined = f"{title}\n\n{content}"
            else:
                combined = content
            formatted_text = format_reflection_text(
                combined, today, lang=lang
            )
            await bot.send_message(
                target_chat_id, formatted_text, parse_mode="HTML"
            )
        else:
            logging.warning(
                f"Размышление на языке '{lang}' на сегодня "
                f"(месяц: {current_month_name}, день: {today.day}) не найдено."
            )
    except Exception as e:
        logging.error(f"Ошибка получения размышлений из БД: {e}")


async def send_morning_prayer_to_channel(
    bot, lang="ru", target_chat_id=CHANNEL_ID
):
    try:
        text = (
            MORNING_PRAYER_TEXT_KK if lang == "kk" else MORNING_PRAYER_TEXT_RU
        )
        await bot.send_message(target_chat_id, text, parse_mode="HTML")
    except Exception as e:
        logging.error(f"Ошибка отправки утренней молитвы: {e}")


async def send_evening_prayer_to_channel(
    bot, lang="ru", target_chat_id=CHANNEL_ID
):
    try:
        text = (
            EVENING_PRAYER_TEXT_KK if lang == "kk" else EVENING_PRAYER_TEXT_RU
        )
        await bot.send_message(target_chat_id, text, parse_mode="HTML")
    except Exception as e:
        logging.error(f"Ошибка отправки вечерней молитвы: {e}")