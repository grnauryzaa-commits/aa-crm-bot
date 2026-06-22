import logging
import psycopg2
from psycopg2.extras import DictCursor
from config import DATABASE_URL

async def init_db():
    """Создает таблицы спонсоров и размышлений, если их еще нет"""
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        
        # Таблица спонсоров
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sponsors (
                id SERIAL PRIMARY KEY,
                user_id BIGINT UNIQUE NOT NULL,
                username VARCHAR(255),
                name VARCHAR(255),
                age INT,
                sobriety VARCHAR(255),
                city VARCHAR(255),
                phone VARCHAR(255),
                status VARCHAR(50) DEFAULT 'pending'
            );
        """)
        
        # Новая таблица для Ежедневных размышлений
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS daily_reflections (
                id SERIAL PRIMARY KEY,
                day_month VARCHAR(10) UNIQUE NOT NULL, -- Формат: "22-06"
                date_title VARCHAR(50) NOT NULL,       -- Например: "22 июня"
                heading VARCHAR(255) NOT NULL,         -- Например: "СЕГОДНЯ Я СВОБОДЕН"
                quote TEXT NOT NULL,                   -- Цитата Билла
                source VARCHAR(100) NOT NULL,          -- Откуда цитата
                reflection TEXT NOT NULL               -- Основной текст размышления
            );
        """)
        
        conn.commit()
        cursor.close()
        conn.close()
        logging.info("База данных PostgreSQL успешно инициализирована (таблицы проверены).")
    except Exception as e:
        logging.error(f"Ошибка при инициализации базы данных: {e}")

def get_db_connection():
    """Возвращает готовое подключение к PostgreSQL с DictCursor"""
    return psycopg2.connect(DATABASE_URL, cursor_factory=DictCursor)