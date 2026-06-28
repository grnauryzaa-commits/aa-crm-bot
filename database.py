import psycopg2
import logging
from config import DATABASE_URL as DB_URL

# Настройка логирования, если она не задана в bot.py
logging.basicConfig(level=logging.INFO)

async def init_db():
    logging.info("🚀 Запуск инициализации и проверки структуры базы данных...")
    try:
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()
        
        # 1. СОЗДАНИЕ ТАБЛИЦ ДЛЯ СПОНСОРОВ (если их вообще не было)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS sponsors (
                id SERIAL PRIMARY KEY,
                user_id BIGINT UNIQUE,
                name VARCHAR(100),
                age INT,
                sobriety VARCHAR(100),
                city VARCHAR(100),
                username VARCHAR(100),
                phone VARCHAR(100)
            );
        """)
        
        cur.execute("""
            CREATE TABLE IF NOT EXISTS sponsor_drafts (
                user_id BIGINT PRIMARY KEY,
                name VARCHAR(100),
                age INT,
                sobriety VARCHAR(100),
                city VARCHAR(100),
                username VARCHAR(100),
                phone VARCHAR(100)
            );
        """)

        # 2. ИСПРАВЛЕНИЕ: Принудительно добавляем колонку program_info в обе таблицы
        logging.info("⚡ Проверка и добавление колонки 'program_info'...")
        cur.execute("ALTER TABLE sponsors ADD COLUMN IF NOT EXISTS program_info TEXT;")
        cur.execute("ALTER TABLE sponsor_drafts ADD COLUMN IF NOT EXISTS program_info TEXT;")
        
        # 3. СОЗДАНИЕ ПРАВИЛЬНОЙ ТАБЛИЦЫ ДЛЯ ЕЖЕДНЕВНЫХ РАЗМЫШЛЕНИЙ
        logging.info("⚡ Проверка и создание таблицы 'reflections_archive'...")
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
        logging.info("🎉 БАЗА ДАННЫХ УСПЕШНО ОБНОВЛЕНА И ГОТОВА К РАБОТЕ!")
        
    except Exception as e:
        logging.error(f"❌ Ошибка при инициализации БД внутри сервера: {e}")
        raise e