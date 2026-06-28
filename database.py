import psycopg2
import logging
import asyncio
from config import DATABASE_URL as DB_URL

# Настройка логирования
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

        # 2. ИСПРАВЛЕНИЕ СТРУКТУРЫ: Принудительно добавляем колонку program_info в обе таблицы
        logging.info("⚡ Проверка и добавление колонки 'program_info'...")
        cur.execute("ALTER TABLE sponsors ADD COLUMN IF NOT EXISTS program_info TEXT;")
        cur.execute("ALTER TABLE sponsor_drafts ADD COLUMN IF NOT EXISTS program_info TEXT;")
        
        # 3. СОЗДАНИЕ ТАБЛИЦЫ ДЛЯ ЕЖЕДНЕВНЫХ РАЗМЫШЛЕНИЙ
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

# =====================================================================
# АСИНХРОННЫЕ ФУНКЦИИ ДЛЯ ФОРМЫ РЕГИСТРАЦИИ (form.py)
# =====================================================================

def _get_sponsor_sync(user_id):
    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()
    cur.execute("SELECT user_id FROM sponsors WHERE user_id = %s;", (user_id,))
    res = cur.fetchone()
    cur.close()
    conn.close()
    return res

async def get_sponsor_by_tg_id(user_id):
    """Проверяет, есть ли пользователь уже в базе активных спонсоров"""
    return await asyncio.to_thread(_get_sponsor_sync, user_id)


def _save_draft_sync(user_id, data):
    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()
    # Записываем анкету в черновики (sponsor_drafts)
    cur.execute("""
        INSERT INTO sponsor_drafts (user_id, name, age, sobriety, city, program_info, username, phone)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (user_id) DO UPDATE SET
            name = EXCLUDED.name, 
            age = EXCLUDED.age, 
            sobriety = EXCLUDED.sobriety,
            city = EXCLUDED.city, 
            program_info = EXCLUDED.program_info,
            username = EXCLUDED.username, 
            phone = EXCLUDED.phone;
    """, (
        user_id, 
        data.get('name'), 
        int(data.get('age', 0)) if str(data.get('age')).isdigit() else 0,
        data.get('sobriety'), 
        data.get('city'), 
        data.get('program_info'),
        data.get('username'), 
        data.get('phone')
    ))
    conn.commit()
    cur.close()
    conn.close()

async def save_sponsor_draft(user_id, data):
    """Сохраняет заполненную анкету пользователя в таблицу черновиков"""
    await asyncio.to_thread(_save_draft_sync, user_id, data)