from aiogram import Router, F, types
import aiohttp
from bs4 import BeautifulSoup
import logging

router = Router()

@router.message(F.text == "📘 Ежедневные размышления")
async def show_reflections(message: types.Message):
    # Отправляем временный статус, чтобы пользователь видел, что бот работает
    waiting_message = await message.answer("🔄 Загружаю сегодняшнее размышление...")

    url = "https://mos-nach.ru/thinks/"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }

    try:
        # Делаем асинхронный запрос к новому сайту
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get(url, timeout=10) as response:
                if response.status != 200:
                    raise Exception(f"Сайт вернул статус код: {response.status}")
                html = await response.text()

        soup = BeautifulSoup(html, 'html.parser')
        
        # Находим главный блок, где лежит статья с размышлением
        article = soup.find('article')
        
        if article:
            # Находим заголовок (там обычно дата и название размышления)
            title_element = article.find('h1') or article.find('h2')
            title_text = title_element.get_text(strip=True) if title_element else "Ежедневное размышление"
            
            # Находим все абзацы текста внутри статьи
            paragraphs = [p.get_text(strip=True) for p in article.find_all('p') if p.get_text(strip=True)]
            
            # Очищаем текст от возможных технических строк сайта (например, ссылки на архив внизу)
            clean_paragraphs = []
            for p in paragraphs:
                if "Посмотреть размышления на другой день" in p or "Архив размышлений" in p:
                    continue
                clean_paragraphs.append(p)

            if len(clean_paragraphs) >= 2:
                quote = clean_paragraphs[0]        # Первый абзац — цитата
                source = clean_paragraphs[1]       # Второй — источник (книга)
                main_text = "\n\n".join(clean_paragraphs[2:]) # Всё остальное — размышление
            else:
                quote = ""
                source = ""
                main_text = "\n\n".join(clean_paragraphs)

            # Собираем красивое сообщение для отправки в Telegram
            text = (
                f"📘 **{title_text}**\n\n"
                f"«{quote}»\n"
                f"_* {source}_\n\n"
                f"{main_text}"
            )
        else:
            # Если структуру сайта не удалось прочитать, даем прямую ссылку
            text = (
                f"📘 **Ежедневные размышления**\n\n"
                f"Не удалось отобразить текст прямо в чате, но ты можешь прочесть его на сайте:\n"
                f"🔗 [Читать на mos-nach.ru]({url})"
            )

        # Удаляем плашку загрузки и отправляем готовое размышление
        await waiting_message.delete()
        await message.answer(text, parse_mode="Markdown", disable_web_page_preview=True)

    except Exception as e:
        logging.error(f"Ошибка парсинга с mos-nach.ru: {e}")
        await waiting_message.delete()
        # Если вдруг сайт ляжет, бот вежливо отправит ссылку
        await message.answer(
            f"⚠️ Прямо сейчас не удалось загрузить текст, "
            f"но ты можешь открыть его по прямой ссылке:\n\n🔗 [Ежедневное размышление]({url})",
            parse_mode="Markdown"
        )