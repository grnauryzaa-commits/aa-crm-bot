import psycopg2
import os

# Скрипт сам подхватит настройки, если запустить через 'railway run'
DB_URL = os.getenv("DATABASE_URL")

def check_db():
    try:
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()
        print("Подключение успешно!")
        
        cur.execute("SELECT day, month, title, text FROM reflections_archive WHERE day = 29 AND month = 6")
        row = cur.fetchone()
        
        if row:
            day, month, title, text = row
            print(f"\n--- ДАННЫЕ ЗА {day}.{month} ---")
            print(f"ЗАГОЛОВОК: {title}")
            print(f"\nСЫРОЙ ТЕКСТ:\n{text}")
            
            parts = text.split('***')
            print(f"\nРАЗБИВКА (найдено частей: {len(parts)}):")
            for i, part in enumerate(parts):
                print(f"\n--- ЧАСТЬ {i} ---\n{part}")
        else:
            print("Запись за 29 июня не найдена.")
            
        cur.close()
        conn.close()
    except Exception as e:
        print(f"ОШИБКА: {e}")

if __name__ == "__main__":
    check_db()