from aiogram import Router, F, types
from datetime import datetime
import aiohttp
from bs4 import BeautifulSoup
import logging

router = Router()

@router.message(F.text == "📘 Ежедневные размышления")
async def show_reflections(message: types.Message):
    waiting_message = await message.answer("🔄 Загружаю сегодняшнее размышление...")

    now = datetime.now()
    day = now.strftime("%d")
    month = now.strftime("%m")
    
    url = f"https://aarussia.ru/daily-reflections/?date={day}-{month}"

    # Маскируемся под обычный компьютерный браузер Chrome
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'ru-RU,ru;q=0.8,en-US;q=0.5,en;q=0.3'
    }

    try:
        # Делаем асинхронный запрос через aiohttp
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get(url, timeout=10) as response:
                if response.status != 200:
                    raise Exception(f"Сайт вернул статус код: {response.status}")
                
                html = await response.text()

        soup = BeautifulSoup(html, 'html.parser')
        
        # Находим основной контейнер с текстом
        reflection_block = soup.find('div', class_='daily-reflection')
        
        if reflection_block:
            date_title = reflection_block.find('h2').get_text(strip=True) if reflection_block.find('h2') else f"{day}.{month}"
            heading = reflection_block.find('h3').get_text(strip=True) if reflection_block.find('h3') else ""
            
            paragraphs = [p.get_text(strip=True) for p in reflection_block.find_all('p') if p.get_text(strip=True)]
            
            if len(paragraphs) >= 2:
                quote = paragraphs[0]
                source = paragraphs[1]
                main_text = "\n\n".join(paragraphs[2:])
            else:
                quote = ""
                source = ""
                main_text = "\n\n".join(paragraphs)

            text = (
                f"📅 **{date_title}**\n\n"
                f"☀️ **{heading.upper()}**\n\n"
                f"«{quote}»\n"
                f"_* {source}_\n\n"
                f"{main_text}"
            )
        else:
            text = (
                f"📘 **Ежедневные размышления**\n\n"
                f"Не удалось вытащить текст из структуры сайта, но его можно прочесть по ссылке:\n"
                f"🔗 [Читать на aarussia.ru]({url})"
            )

        await waiting_message.delete()
        await message.answer(text, parse_mode="Markdown", disable_web_page_preview=True)

    except Exception as e:
        logging.error(f"Ошибка парсинга размышлений: {e}")
        await waiting_message.delete()
        await message.answer(
            f"⚠️ Не удалось загрузить текст прямо сюда из-за защиты сайта.\n"
            f"Пожалуйста, прочти его по прямой ссылке:\n\n🔗 [Ежедневное размышление на сегодня]({url})",
            parse_mode="Markdown"
        )