import asyncio
import aiohttp
import psycopg2
from bs4 import BeautifulSoup

# Адрес базы данных
DB_URL = "postgresql://postgres:rjKAEdhpAeVceQzFobzCKFRbWnJwYOem@thomas.proxy.rlwy.net:12836/railway"

async def fill():
    print("🧹 Начинаю очистку и обновление базы...")
    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()
    cur.execute("DELETE FROM reflections_archive;")
    conn.commit()

    async with aiohttp.ClientSession(headers={'User-Agent': 'Mozilla/5.0'}) as session:
        for month in range(1, 13):
            days = 31 if month in [1, 3, 5, 7, 8, 10, 12] else 30
            if month == 2: days = 28
            
            for day in range(1, days + 1):
                url = f"https://mos-nach.ru/thinks/daily_{str(day).zfill(2)}-{str(month).zfill(2)}.html"
                
                try:
                    async with session.get(url, timeout=10) as resp:
                        if resp.status != 200: continue
                        html = await resp.text()
                    
                    soup = BeautifulSoup(html, 'html.parser')
                    content_div = soup.find(id='content') or soup
                    paragraphs = content_div.find_all('p')
                    
                    final_text = []
                    for p in paragraphs:
                        text = p.text.strip()
                        
                        # Стоп-слова: как только скрипт встречает одно из них, 
                        # сбор текста прекращается.
                        if any(phrase in text for phrase in [
                            "Место под альтернативный", 
                            "Это издание было подготовлено", 
                            "1990©", 
                            "Alcoholics Anonymous ©",
                            "Московские Начинающие",
                            "Наша помощь бесплатна",
                            "Сайт информирует"
                        ]):
                            break
                        
                        if text:
                            final_text.append(text)
                    
                    # Собираем всё, что успели накопить до стоп-слов
                    clean_content = "\n\n".join(final_text)
                    title = soup.find('h1').text.strip() if soup.find('h1') else f"{day:02d}.{month:02d}"

                    cur.execute("""
                        INSERT INTO reflections_archive (day, month, title, text) 
                        VALUES (%s, %s, %s, %s)
                    """, (day, month, title, clean_content))
                    
                    print(f"✅ Добавлено: {day:02d}.{month:02d}")
                    
                except Exception as e:
                    print(f"Ошибка на {day}.{month}: {e}")

    conn.commit()
    cur.close()
    conn.close()
    print("🎉 База полностью обновлена!")

if __name__ == "__main__":
    asyncio.run(fill())