import psycopg2
import logging
import asyncio
from config import DATABASE_URL as DB_URL

# Настройка логирования
logging.basicConfig(level=logging.INFO)

async def init_db():
    logging.info("🚀 Запуск принудительного обновления структуры базы данных (добавление пола)...")
    try:
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()
        
        # 1. СОЗДАНИЕ ТАБЛИЦЫ SPONSORS И ПРОВЕРКА КОЛОНОК
        cur.execute("""
            CREATE TABLE IF NOT EXISTS sponsors (
                user_id BIGINT UNIQUE PRIMARY KEY,
                name VARCHAR(100),
                gender VARCHAR(10),
                age INT,
                sobriety VARCHAR(100),
                city VARCHAR(100),
                username VARCHAR(100),
                phone VARCHAR(100),
                program_info TEXT
            );
        """)
        
        # 2. ГАРАНТИРУЕМ ПРАВИЛЬНУЮ СТРУКТУРУ ТАБЛИЦЫ ЧЕРНОВИКОВ
        try:
            cur.execute("SELECT user_id FROM sponsor_drafts LIMIT 1;")
        except Exception:
            conn.rollback()
            logging.warning("⚠️ Таблица sponsor_drafts повреждена или не содержит user_id. Пересоздаем...")
            cur.execute("DROP TABLE IF EXISTS sponsor_drafts;")
            
        cur.execute("""
            CREATE TABLE IF NOT EXISTS sponsor_drafts (
                user_id BIGINT PRIMARY KEY,
                name VARCHAR(100),
                gender VARCHAR(10),
                age INT,
                sobriety VARCHAR(100),
                city VARCHAR(100),
                username VARCHAR(100),
                phone VARCHAR(100),
                program_info TEXT
            );
        """)

        # ПРИНУДИТЕЛЬНО ДОБАВЛЯЕМ КОЛОНКИ, ЕСЛИ ИХ НЕТ (ДЛЯ БЕЗОПАСНОГО ОБНОВЛЕНИЯ)
        cur.execute("ALTER TABLE sponsors ADD COLUMN IF NOT EXISTS gender VARCHAR(10);")
        cur.execute("ALTER TABLE sponsor_drafts ADD COLUMN IF NOT EXISTS gender VARCHAR(10);")
        cur.execute("ALTER TABLE sponsors ADD COLUMN IF NOT EXISTS program_info TEXT;")
        cur.execute("ALTER TABLE sponsor_drafts ADD COLUMN IF NOT EXISTS program_info TEXT;")
        
        # 3. СОЗДАНИЕ ТАБЛИЦЫ ДЛЯ ЕЖЕДНЕВНЫХ РАЗМЫШЛЕНИЙ
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
        logging.info("🎉 СТРУКТУРА БАЗЫ ДАННЫХ ИСПРАВЛЕНА И ГОТОВА К РАБОТЕ!")
        
    except Exception as e:
        logging.error(f"❌ Критическая ошибка инициализации БД: {e}")
        raise e


# =====================================================================
# ФУНКЦИИ ВЗАИМОДЕЙСТВИЯ С БАЗОЙ ДАННЫХ
# =====================================================================

def _get_sponsor_sync(user_id):
    try:
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()
        cur