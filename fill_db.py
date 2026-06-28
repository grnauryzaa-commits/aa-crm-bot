import asyncio
import psycopg2
import aiohttp
from bs4 import BeautifulSoup

# ====================================================================
# 🟢 ВАША РЕАЛЬНАЯ ССЫЛКА ПОДКЛЮЧЕНА И АКТИВНА
# ====================================================================
DB_URL = "postgresql://postgres:rjKAEdhpAeVceQzFobzCKFRbWnJwYOem@postgres.railway.internal:5432/railway"

async def main():
    archive_url = "https://mos-nach.ru/thinks/"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
    }

    print("🚀 Подключаемся к главной странице архива размышлений...")
    
    async with aiohttp.ClientSession(headers=headers) as session:
        try:
            async with session.get(archive_url, timeout=15) as response:
                if response.status != 200:
                    print(f"❌ Не удалось открыть архив. Статус сайта: {response.status}")
                    return
                html = await response.text()
        except Exception as e:
            print(f"❌ Критическая ошибка при связи с сайтом: {e}")
            return

        soup = BeautifulSoup(html, 'html.parser')
        
        # Ищем все ссылки на конкретные дни размышлений
        links = []
        for a in soup.find_all('a', href=True):
            href = a['href']
            if "/thinks/" in href and href != "https://mos-nach.ru/thinks/" and href != "/thinks/":
                # ИСПРАВЛЕНИЕ: если ссылка относительная (начинается с /), добавляем домен сайта
                if href.startswith("/"):
                    full_url = f"https://mos-nach.ru{href}"
                else:
                    full_url = href
                    
                if full_url not in links:
                    links.append(full_url)

        if not links:
            print("⚠️ Не удалось автоматически собрать ссылки с архива. Пробуем запасной метод...")
            await fallback_generation(session)
            return

        print(f"🔎 Найдено {len(links)} страниц в архиве. Начинаем скачивание...")

        for url in links:
            # Извлекаем месяц и день из ссылки
            clean_url = url.rstrip('/')
            parts = clean_url.split('/')
            date_part = parts[-1] # Получим "06-26"
            
            try:
                month, day = map(int, date_part.split('-'))
            except:
                continue # Если ссылка не содержит дату в формате 00-00, пропускаем
                
            await parse_and_save_day(session, url, day, month)
            await asyncio.sleep(0.4) # Безопасная пауза

    print("\n🎉 Процесс завершен!")

async def parse_and_save_day(session, url, day, month):
    try:
        async with session.get(url, timeout=15) as response:
            if response.status != 200:
                print(f"❌ Ссылка недоступна ({response.status}) для даты: {day:02d}.{month:02d} | URL: {url}")
                return
            html = await response.text()
            
        soup = BeautifulSoup(html, 'html.parser')
        title_el = soup.find('h1', class_='entry-title') or soup.find('h1') or soup.find('h2')
        title_text = title_el.get_text(strip=True) if title_el else f"{day:02d}.{month:02d}"
        
        content_block = soup.find(id='content') or soup.find('article') or soup.find('main')
        paragraphs = [p.get_text(strip=True) for p in content_block.find_all('p')] if content_block else []
        
        clean_paragraphs = []
        for p in paragraphs:
            stop_words = ["место под альтернативный", "издание было подготовлено", "анонимные алкоголики ©", "архив размышлений", "предыдущее", "следующее"]
            if any(word in p.lower() for word in stop_words):
                break
            clean_paragraphs.append(p)
            
        if len(clean_paragraphs) >= 2:
            if title_text.lower() in clean_paragraphs[0].lower() or len(clean_paragraphs[0]) < 12:
                clean_paragraphs = clean_paragraphs[1:]
                
        full_text = "\n\n".join(clean_paragraphs)
        
        if not full_text.strip():
            return

        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO reflections_archive (day, month, title, text)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (day, month) DO UPDATE SET title = EXCLUDED.title, text = EXCLUDED.text;
        """, (day, month, title_text, full_text))
        conn.commit()
        cur.close()
        conn.close()
        print(f"✅ Сохранено: {day:02d}.{month:02d} — {title_text}")
        
    except Exception as e:
        print(f"⚠️ Ошибка на дате {day:02d}.{month:02d}: {e}")

async def fallback_generation(session):
    MONTHS_DAYS = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    for month_idx, max_days in enumerate(MONTHS_DAYS):
        month = month_idx + 1
        for day in range(1, max_days + 1):
            url = f"https://mos-nach.ru/thinks/{str(month).zfill(2)}-{str(day).zfill(2)}/"
            await parse_and_save_day(session, url, day, month)
            await asyncio.sleep(0.5)

if __name__ == "__main__":
    asyncio.run(main())