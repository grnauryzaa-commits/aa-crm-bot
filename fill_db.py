import asyncio
import aiohttp
import psycopg2
from bs4 import BeautifulSoup

# Твой адрес базы
DB_URL = "postgresql://postgres:rjKAEdhpAeVceQzFobzCKFRbWnJwYOem@thomas.proxy.rlwy.net:12836/railway"

async def fill():
    print("🧹 Начинаю запись базы (исправленный парсер)...")
    try:
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()
        cur.execute("DELETE FROM reflections_archive;")
        conn.commit()
    except Exception as e:
        print(f"❌ Ошибка БД: {e}")
        return
    
    async with aiohttp.ClientSession(headers={'User-Agent': 'Mozilla/5.0'}) as session:
        for month in range(1, 13):
            days = 31 if month in [1, 3, 5, 7, 8, 10, 12] else 30
            if month == 2: days = 28
            
            for day in range(1, days + 1):
                url = f"https://mos-nach.ru/thinks/daily_{str(day).zfill(2)}-{str(month).zfill(2)}.html"
                try:
                    async with session.get(url, timeout=10) as resp:
                        if resp.status != 200: continue
                        html_content = await resp.text()
                    
                    soup = BeautifulSoup(html_content, 'html.parser')
                    
                    # Ищем блок wrapper
                    wrapper = soup.find('div', id='wrapper')
                    if not wrapper: continue
                    
                    # Получаем текст из wrapper
                    full_text = wrapper.get_text(separator='\n').strip()
                    
                    # Отрезаем мусорный подвал
                    if "...Место под" in full_text:
                        full_text = full_text.split("...Место под")[0].strip()
                    
                    lines = [line.strip() for line in full_text.split('\n') if line.strip()]
                    
                    # Фильтр: пропускаем лишние строки (меню и навигацию)
                    # Обычно размышление начинается с заголовка, который идет после заголовка сайта
                    # Найдем индекс, где начинается реальный текст (пропуская навигацию)
                    start_idx = 0
                    for i, line in enumerate(lines):
                        if len(line) > 5 and "июня" not in line.lower() and "июля" not in line.lower():
                            start_idx = i
                            break
                    
                    if len(lines) < start_idx + 2: continue

                    title = lines[start_idx]
                    body = "\n".join(lines[start_idx+1:])
                    
                    cur.execute("""
                        INSERT INTO reflections_archive (day, month, title, text) 
                        VALUES (%s, %s, %s, %s)
                    """, (day, month, title, body))
                    conn.commit()
                    print(f"✅ Записано: {day:02d}.{month:02d} | {title[:20]}...")
                    
                except Exception as e:
                    print(f"❌ Ошибка {day:02d}.{month:02d}: {e}")
                    conn.rollback()
    
    cur.close()
    conn.close()
    print("🎉 Готово! База заполнена.")

if __name__ == "__main__":
    asyncio.run(fill())