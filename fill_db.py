import asyncio
import aiohttp
import psycopg2
from bs4 import BeautifulSoup

# Присваиваем адрес переменной, чтобы код работал
DB_URL = "postgresql://postgres:rjKAEdhpAeVceQzFobzCKFRbWnJwYOem@thomas.proxy.rlwy.net:12836/railway"

async def fill():
    print("🧹 Начинаю обновление базы...")
    try:
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()
        cur.execute("DELETE FROM reflections_archive;")
        conn.commit()
    except Exception as e:
        print(f"Ошибка подключения к базе: {e}")
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
                        html = await resp.text()
                    
                    soup = BeautifulSoup(html, 'html.parser')
                    content_div = soup.find(id='content') or soup
                    paragraphs = content_div.find_all('p')
                    
                    # Фильтруем только текстовые абзацы
                    data = [p.text.strip() for p in paragraphs if p.text.strip()]
                    
                    if not data: continue

                    # Логика:
                    # [0] - Заголовок
                    # [1] - Цитата
                    # [2] - Часто содержит источник (с. 123), его пропускаем
                    # [3:] - Основной текст
                    
                    title = data[0]
                    quote = data[1] if len(data) > 1 else ""
                    
                    # Если есть строка с "с." или "p." на 2-й позиции, считаем её источником и берем данные с 3-го индекса
                    if len(data) > 2 and ("с." in data[2].lower() or "p." in data[2].lower()):
                        body_lines = data[3:]
                    else:
                        body_lines = data[2:]
                    
                    body = "\n\n".join(body_lines)
                    
                    # Разделитель для бота
                    clean_content = f"{quote}***{body}"

                    cur.execute("""
                        INSERT INTO reflections_archive (day, month, title, text) 
                        VALUES (%s, %s, %s, %s)
                    """, (day, month, title[:250], clean_content))
                    
                    print(f"✅ Добавлено: {day:02d}.{month:02d}")
                    
                except Exception as e:
                    print(f"Ошибка {day}.{month}: {e}")
                    conn.rollback()

    conn.commit()
    cur.close()
    conn.close()
    print("🎉 База обновлена успешно!")

if __name__ == "__main__":
    asyncio.run(fill())