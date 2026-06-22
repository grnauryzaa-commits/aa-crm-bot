from aiogram import Router, F, types
from datetime import datetime
import urllib.request
from bs4 import BeautifulSoup
import logging

router = Router()

@router.message(F.text == "📘 Ежедневные размышления")
async def show_reflections(message: types.Message):
    # Отправляем временный статус, чтобы пользователь видел, что бот работает
    waiting_message = await message.answer("🔄 Загружаю сегодняшнее размышление...")

    # Получаем текущую дату сервера
    now = datetime.now()
    day = now.strftime("%d")
    month = now.strftime("%m")
    
    # URL страницы ежедневных размышлений АА России
    url = f"https://aarussia.ru/daily-reflections/?date={day}-{month}"

    try:
        # Делаем запрос к сайту с маскировкой под обычный браузер
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        html = urllib.request.urlopen(req).read()
        
        # Передаем код страницы парсеру
        soup = BeautifulSoup(html, 'html.parser')
        
        # Ищем блок с текстом размышления
        reflection_block = soup.find('div', class_='daily-reflection')
        
        if reflection_block:
            # Вытаскиваем заголовок даты (например, "22 июня")
            date_title = reflection_block.find('h2').get_text(strip=True) if reflection_block.find('h2') else f"{day}.{month}"
            
            # Вытаскиваем главный слоган дня
            heading = reflection_block.find('h3').get_text(strip=True) if reflection_block.find('h3') else ""
            
            # Собираем все абзацы текста очищая их от лишних пробелов
            paragraphs = [p.get_text(strip=True) for p in reflection_block.find_all('p') if p.get_text(strip=True)]
            
            if len(paragraphs) >= 2:
                quote = paragraphs[0]        # Первый абзац — цитата Билла
                source = paragraphs[1]       # Второй абзац — источник цитаты
                main_text = "\n\n".join(paragraphs[2:]) # Остальное — личные размышления
            else:
                quote = ""
                source = ""
                main_text = "\n\n".join(paragraphs)

            # Форматируем красивый текст сообщения для Telegram
            text = (
                f"📅 **{date_title}**\n\n"
                f"☀️ **{heading.upper()}**\n\n"
                f"«{quote}»\n"
                f"_* {source}_\n\n"
                f"{main_text}"
            )
        else:
            # Если вдруг структура сайта поменялась, бот выдаст прямую ссылку
            text = (
                f"📘 **Ежедневные размышления**\n\n"
                f"Не удалось отобразить текст прямо в чате, но ты можешь прочесть его на официальном сайте:\n"
                f"🔗 [Читать на aarussia.ru]({url})"
            )

        # Удаляем промежуточную плашку «Загружаю...» и выдаем готовое размышление
        await waiting_message.delete()
        await message.answer(text, parse_mode="Markdown", disable_web_page_preview=True)

    except Exception as e:
        logging.error(f"Ошибка парсинга размышлений: {e}")
        await waiting_message.delete()
        # В случае любой непредвиденной ошибки (например сайт лег) даем прямую ссылку
        await message.answer(
            f"⚠️ Прямо сейчас не удалось скопировать текст с сайта, "
            f"но ты можешь открыть его по прямой ссылке:\n\n🔗 [Ежедневное размышление на сегодня]({url})",
            parse_mode="Markdown"
        )