from aiogram import F, Router, types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from database import get_user_language
import requests
from bs4 import BeautifulSoup
import logging
import asyncio

router = Router()

TEXTS = {
    "ru": {
        "title": "📅 <b>Расписание собраний АА</b>\nВыберите город:",
        "help_text": "\n\nЕсли у вас есть вопросы, нужна поддержка — мы готовы помочь.\n📞 Горячая линия: +7 (707) 208-05-53",
        "back": "⬅️ Назад",
        "no_schedule": "Для этой группы пока нет расписания."
    },
    "kk": {
        "title": "📅 <b>АА жиналыстарының кестесі</b>\nҚаланы таңдаңыз:",
        "help_text": "\n\nЕгер сұрақтарыңыз болса, көмек керек болса — біз көмектесуге дайынбыз.\n📞 Жедел желі: +7 (707) 433-74-08",
        "back": "⬅️ Артқа",
        "no_schedule": "Бұл топ үшін әзірге кесте жоқ."
    }
}

CACHED_DATA = None

def fetch_schedule_sync():
    global CACHED_DATA
    if CACHED_DATA:
        return CACHED_DATA

    url = "https://aaorg.kz/sobraniya/"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    
    try:
        res = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(res.text, 'html.parser')
        
        # 1. Берем ВЕСЬ текст страницы, убираем пустые строки
        full_text = soup.get_text(separator='\n')
        lines = [line.strip() for line in full_text.split('\n') if line.strip()]
        
        data = {}
        current_city = None
        current_group_name = None
        current_group_info = []
        
        # 2. Идем по строкам и собираем данные
        for line in lines:
            lower_line = line.lower()
            
            # Пропускаем служебные слова, которые не являются ни городами, ни группами
            if any(w in lower_line for w in ["главная", "собрания", "жизнь в аа", "литература", "наши истории", "фонд обслуживания", "english", "где проходят", "выбери свою", "прокрутить вверх", "группы в", "группы"]):
                continue
                
            # 3. Определяем, является ли строка названием города
            # Город — это короткая строка (до 25 символов), которая не содержит признаков группы
            if len(line) < 25 and not any(w in lower_line for w in ["аа ", "аа«", "аа «", "группа", "адрес", "время", "контакт", "zoom", "пароль", "формат", "2gis", "телефон", "https://"]):
                # Сохраняем предыдущую группу, если она была
                if current_city and current_group_name:
                    data[current_city].append(f"• <b>{current_group_name}</b>\n" + "\n".join(current_group_info))
                    current_group_name = None
                    current_group_info = []
                
                # Проверяем, не является ли это мусором (например, "онлайн")
                if line not in ["Контакты", "Зенкова 13", "8 (707) 208-05-53", "Прокрутить вверх"]:
                    current_city = line
                    if current_city not in data:
                        data[current_city] = []
                continue

            # 4. Определяем, является ли строка названием группы
            if any(w in line for w in ["АА «", "АА \"", "Мужская группа", "Талгар", "каскелен", "АА  «", "АА гр."]):
                # Сохраняем предыдущую группу, если она была
                if current_city and current_group_name:
                    data[current_city].append(f"• <b>{current_group_name}</b>\n" + "\n".join(current_group_info))
                
                current_group_name = line
                current_group_info = []
                continue

            # 5. Собираем информацию для текущей группы
            if current_group_name:
                # Если строка содержит ключевые слова, форматируем её
                formatted_line = line.replace("Адрес:", "📍 Адрес:").replace("Время:", "⏰ Время:").replace("Контакты:", "📞 Контакты:").replace("Площадка Zoom:", "💻 Zoom:").replace("Пароль по номеру:", "🔑 Пароль:").replace("Чат в Whatsapp:", "💬 WhatsApp:").replace("Чат в Telegram:", "💬 Telegram:").replace("2Gis:", "📍 2GIS:")
                current_group_info.append(formatted_line)

        # Сохраняем последнюю группу
        if current_city and current_group_name:
            data[current_city].append(f"• <b>{current_group_name}</b>\n" + "\n".join(current_group_info))

        # Очищаем пустые города
        data = {k: v for k, v in data.items() if v}
        
        if not data:
            return {}
            
        CACHED_DATA = data
        return data
    except Exception as e:
        logging.error(f"Ошибка парсинга: {e}")
        return {}

def get_cities_kb(data, lang="ru"):
    kb = []
    row = []
    cities = sorted(data.keys())
    
    for city in cities:
        row.append(InlineKeyboardButton(text=city, callback_data=f"s_{city}"))
        if len(row) == 2:
            kb.append(row)
            row = []
    if row: kb.append(row)
    
    return InlineKeyboardMarkup(inline_keyboard=kb)

@router.message(F.chat.type == "private", F.text.in_({"📅 Расписание", "📅 Кесте"}))
async def show_schedule_menu(message: types.Message):
    lang = await get_user_language(message.from_user.id)
    if not lang: lang = "ru"
    
    # Парсим в фоне
    data = await asyncio.to_thread(fetch_schedule_sync)
    
    if not data:
        await message.answer("Сайт с расписанием временно недоступен. Попробуйте позже.")
        return
        
    await message.answer(
        TEXTS[lang]["title"],
        reply_markup=get_cities_kb(data, lang),
        parse_mode="HTML",
    )

@router.callback_query(F.data.startswith("s_"))
async def callback_schedule(callback: types.CallbackQuery):
    data_str = callback.data
    lang = await get_user_language(callback.from_user.id)
    if not lang: lang = "ru"
    t = TEXTS[lang]

    if data_str == "s_back":
        if CACHED_DATA:
            await callback.message.edit_text(t["title"], reply_markup=get_cities_kb(CACHED_DATA, lang), parse_mode="HTML")
        else:
            await callback.answer("Нажмите «Расписание» заново.", show_alert=True)
        await callback.answer()
        return

    elif data_str.startswith("s_"):
        city_name = data_str.replace("s_", "")
        groups = CACHED_DATA.get(city_name) if CACHED_DATA else None
        
        if not groups:
            await callback.answer(t["no_schedule"], show_alert=True)
            return
            
        text = f"🏙 <b>{city_name}</b>\n\n" + "\n\n".join(groups) + t["help_text"]
        
        # Если Алматы выдает очень много текста, бьем на части
        if len(text) > 4000:
            chunks = [text[i:i+4000] for i in range(0, len(text), 4000)]
            
            for chunk in chunks:
                await callback.bot.send_message(callback.from_user.id, chunk, parse_mode="HTML")
            
            kb = [[InlineKeyboardButton(text=t["back"], callback_data="s_back")]]
            await callback.bot.send_message(callback.from_user.id, "Выберите действие:", reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))
            
        else:
            kb = [[InlineKeyboardButton(text=t["back"], callback_data="s_back")]]
            await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=kb), parse_mode="HTML")

    await callback.answer()