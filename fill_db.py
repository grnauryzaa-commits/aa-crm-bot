import asyncio
import psycopg2
import aiohttp
from bs4 import BeautifulSoup

# Твоя ссылка для БД
DB_URL = "postgresql://postgres:rjKAEdhpAeVceQzFobzCKFRbWnJwYOem@thomas.proxy.rlwy.net:12836/railway"

async def main():
    print("🚀 Начинаю загрузку и очистку архива...")
    async with aiohttp.ClientSession(headers={'User-Agent': 'Mozilla/5.0'}) as session:
        for month in range(1, 13):
            days_in_month = 31 if month in [1, 3, 5, 7, 8, 10, 12] else 30
            if month == 2: days_in_month = 28
            
            for day in range(1, days_in_month + 1):
                url = f"https://mos-nach.ru/thinks/daily_{str(day).zfill(2)}-{str(month).zfill(2)}.html"
                await parse_and_save(session, url, day, month)
                await asyncio.sleep(0.2) 

    print("\n🎉 Готово! Все данные очищены и обновлены.")

async def parse_and_save(session, day, month, url):
    global DB_URL
    try:
        async with session.get(url, timeout=10) as response:
            if response.status != 200: return
            html = await response.text()
            
        # СОЗДАЕМ SOUP ВНУТРИ ФУНКЦИИ
        soup = BeautifulSoup(html, 'html.parser')
        
        # Заголовок
        title = soup.find('h1').text.strip() if soup.find('h1') else f"Размышление {day:02d}.{month:02d}"
        
        # Поиск текста и обрезка мусора
        content_div = soup.find(id='content') or soup.find('article') or soup
        paragraphs = content_div.find_all('p')
        
        final_text = []
        for p in paragraphs:
            text = p.text.strip()
            # Условие остановки
            if any(phrase in text for phrase in ["Место под альтернативный", "Это издание было подготовлено", "1990©", "Alcoholics Anonymous ©"]):
                break
            if len(text) > 10:
                final_text.append(text)
        
        content = "\n\n".join(final_text)
        if not content: return

        # Запись в БД
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO reflections_archive (day, month, title, text)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (day, month) DO UPDATE SET title = EXCLUDED.title, text = EXCLUDED.text;
        """, (day, month, title, content))
        conn.commit()
        cur.close()
        conn.close()
        print(f"✅ Обработано: {day:02d}.{month:02d}")
        
    except Exception as e:
        pass

if __name__ == "__main__":
    asyncio.run(main())