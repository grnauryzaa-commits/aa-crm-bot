import psycopg2

# Твоя рабочая строка подключения
DB_URL = "postgresql://postgres:rjKAEdhpAeVceQzFobzCKFRbWnJwYOem@postgres.railway.internal:5432/railway"

def fix_database():
    print("🚀 Подключаемся к PostgreSQL на Railway для исправления...")
    try:
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()
        
        # 1. Добавляем колонку program_info, если её не было
        print("⚡ Проверяем и добавляем колонку 'program_info'...")
        cur.execute("ALTER TABLE sponsors ADD COLUMN IF NOT EXISTS program_info TEXT;")
        cur.execute("ALTER TABLE sponsor_drafts ADD COLUMN IF NOT EXISTS program_info TEXT;")
        
        # 2. Создаем правильную таблицу для ежедневных размышлений (reflections_archive)
        print("⚡ Проверяем и создаем таблицу 'reflections_archive'...")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS reflections_archive (
                day INT,
                month INT,
                title VARCHAR(255),
                text TEXT,
                PRIMARY KEY (day, month)
            );
        """)
        
        conn.commit()
        cur.close()
        conn.close()
        print("🎉 УСПЕХ! Все исправления внесены в базу данных Railway!")
        
    except Exception as e:
        print(f"❌ Произошла ошибка при выполнении скрипта: {e}")

if __name__ == "__main__":
    fix_database()