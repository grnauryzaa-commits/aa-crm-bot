import logging
import psycopg2
from psycopg2.extras import DictCursor
from config import DATABASE_URL

async def init_db():
    """Создает таблицу спонсоров, если её ещё нет в PostgreSQL"""
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
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
        conn.commit()
        cursor.close()
        conn.close()
        logging.info("База данных PostgreSQL успешно проверена/инициализирована.")
    except Exception as e:
        logging.error(f"Ошибка при инициализации базы данных: {e}")

def get_db_connection():
    """Возвращает готовое подключение к PostgreSQL с DictCursor"""
    return psycopg2.connect(DATABASE_URL, cursor_factory=DictCursor)