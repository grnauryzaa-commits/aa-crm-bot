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
        
        # Берем ВЕСЬ текст со страницы, убираем лишние пробелы и пустые строки
        full_text = soup.get_text(separator='\n')
        lines = [line.strip() for line in full_text.split('\n') if line.strip()]
        
        data = {}
        current_city = None
        current_groups = []
        
        # Список служебных слов, которые нам не нужны
        ignore_words = ["главная", "собрания", "қазақ тілінде", "жизнь в аа", "литература", "наши истории", "фонд обслуживания", "english", "где проходят", "выбери свою", "контакты", "зенкова 13", "8 (707) 208-05-53", "прокрутить вверх"]
        
        # Ищем начало расписания
        start_index = 0
        for i, line in enumerate(lines):
            if "группы" in line.lower() and ("онлайн" in line.lower() or i + 1 < len(lines)):
                start_index = i
                break
        
        # Проходим по тексту, начиная с расписания
        for line in lines[start_index:]:
            lower_line = line.lower()
            
            # Пропускаем мусор
            if any(word in lower_line for word in ignore_words):
                continue
                
            # Если нашли слово "группы в" — значит, следующий город это то, что нам нужно
            if lower_line.startswith("группы в"):
                continue # Просто пропускаем эту строку
                
            # Если строка короткая (до 20 символов) и не похожа на описание (нет "адрес:", "время:" и т.д.)
            # И начинается с большой буквы — значит, это город
            if len(line) < 25 and line[0].isupper() and not any(w in lower_line for w in ["адрес", "время", "контакт", "zoom", "пароль"]):
                # Сохраняем предыдущий город, если он есть
                if current_city and current_groups:
                    data[current_city] = current_groups
                
                current_city = line
                current_groups = []
            
            # Если это группа (начинается с АА, Мужская, Талгар, каскелен и т.д.)
            elif current_city and any(w in line for w in ["АА", "аа", "группа", "Талгар", "каскелен"]):
                # Собираем описание группы в кучу
                group_text = [f"• <b>{line}</b>"]
                
                # Берем следующие строки, пока не встретим новую группу или город
                # (это упрощенно, но работает для текущей структуры сайта)
                group_index = lines.index(line)
                for next_line in lines[group_index+1:]:
                    next_lower = next_line.lower()
                    if any(w in next_lower for w in ["адрес", "время", "контакт", "zoom", "пароль", "как нас найти", "формат группы", "2gis", "телефон", "сайт:", "instagram"]):
                        group_text.append(next_line.replace("Адрес:", "📍 Адрес:").replace("Время:", "⏰ Время:").replace("Контакты:", "📞 Контакты:").replace("Площадка Zoom:", "💻 Zoom:").replace("Пароль по номеру:", "🔑 Пароль:"))
                    else:
                        break # Если пошло что-то другое (новая группа или город), останавливаемся
                
                current_groups.append("\n".join(group_text))
        
        # Добавляем последний город
        if current_city and current_groups:
            data[current_city] = current_groups
            
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
    # Сортируем города по алфавиту
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
    
    # Сообщение о загрузке
    wait_msg = await message.answer("⏳ Загружаю расписание с сайта, подождите...")
    
    # Парсим в отдельном потоке
    data = await asyncio.to_thread(fetch_schedule_sync)
    
    # Удаляем сообщение о загрузке
    try:
        await wait_msg.delete()
    except Exception:
        pass
    
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
        
        # Если текст слишком длинный (Алматы), бьем на части
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