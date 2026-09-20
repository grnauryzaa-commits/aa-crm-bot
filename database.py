import psycopg2
import logging
import asyncio
from config import DATABASE_URL as DB_URL
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

logging.basicConfig(level=logging.INFO)

async def init_db():
    logging.info("🚀 Запуск инициализации структуры базы данных...")
    try:
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()
        
        # Таблица пользователей и языков
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id BIGINT PRIMARY KEY,
                language VARCHAR(10) DEFAULT 'ru'
            );
        """)

        # Таблица спонсоров
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
        
        # Таблица черновиков анкет спонсоров
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

        # Безопасное добавление колонок
        cur.execute("ALTER TABLE sponsors ADD COLUMN IF NOT EXISTS gender VARCHAR(10);")
        cur.execute("ALTER TABLE sponsor_drafts ADD COLUMN IF NOT EXISTS gender VARCHAR(10);")
        cur.execute("ALTER TABLE sponsors ADD COLUMN IF NOT EXISTS program_info TEXT;")
        cur.execute("ALTER TABLE sponsor_drafts ADD COLUMN IF NOT EXISTS program_info TEXT;")
        cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS language VARCHAR(10) DEFAULT 'ru';")
        
        # Таблица архива размышлений
        cur.execute("""
            CREATE TABLE IF NOT EXISTS reflections_archive (
                day INT,
                month INT,
                title VARCHAR(255),
                text TEXT,
                PRIMARY KEY (day, month)
            );
        """)

        # Таблица истории диалогов с ИИ
        cur.execute("""
            CREATE TABLE IF NOT EXISTS dialog_history (
                id SERIAL PRIMARY KEY,
                user_id BIGINT,
                role TEXT,
                content TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        conn.commit()
        cur.close()
        conn.close()
        logging.info("🎉 БАЗА ДАННЫХ УСПЕШНО ИНИЦИАЛИЗИРОВАНА!")
        
    except Exception as e:
        logging.error(f"❌ Ошибка инициализации БД: {e}")
        raise e

# Функции языка
def _get_user_language_sync(user_id: int) -> str:
    try:
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()
        cur.execute("SELECT language FROM users WHERE user_id = %s", (user_id,))
        row = cur.fetchone()
        cur.close()
        conn.close()
        return row[0] if row and row[0] in ['ru', 'kk'] else 'ru'
    except Exception as e:
        logging.error(f"Ошибка получения языка: {e}")
        return 'ru'

async def get_user_language(user_id: int) -> str:
    return await asyncio.to_thread(_get_user_language_sync, user_id)

def _set_user_language_sync(user_id: int, lang: str):
    try:
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO users (user_id, language) VALUES (%s, %s)
            ON CONFLICT (user_id) DO UPDATE SET language = EXCLUDED.language
        """, (user_id, lang))
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        logging.error(f"Ошибка сохранения языка: {e}")

async def set_user_language(user_id: int, lang: str):
    await asyncio.to_thread(_set_user_language_sync, user_id, lang)

# Генератор главного меню под конкретный язык (решает проблему сброса кнопок)
def get_main_menu_keyboard(lang: str = "ru") -> ReplyKeyboardMarkup:
    if lang == "kk":
        keyboard = [
            [KeyboardButton(text="➕ Демеуші болу"), KeyboardButton(text="🤝 Демеушілер")],
            [KeyboardButton(text="🗓 Кесте"), KeyboardButton(text="📖 Күнделікті ой-толғаулар")],
            [KeyboardButton(text="? Көмек"), KeyboardButton(text="🌐 Тіл: Қазақша")]
        ]
    else:
        keyboard = [
            [KeyboardButton(text="➕ Стать спонсором"), KeyboardButton(text="🤝 Спонсоры")],
            [KeyboardButton(text="🗓 Расписание"), KeyboardButton(text="📖 Ежедневные размышления")],
            [KeyboardButton(text="? Помощь"), KeyboardButton(text="🌐 Язык: Русский")]
        ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

# Остальные функции базы данных
def _get_sponsor_sync(user_id):
    try:
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()
        cur.execute("SELECT user_id FROM sponsors WHERE user_id = %s;", (user_id,))
        res = cur.fetchone()
        cur.close()
        conn.close()
        return res
    except Exception as e:
        return None

async def get_sponsor_by_tg_id(user_id):
    return await asyncio.to_thread(_get_sponsor_sync, user_id)

def _save_draft_sync(user_id, data):
    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO sponsor_drafts (user_id, name, gender, age, sobriety, city, program_info, username, phone)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (user_id) DO UPDATE SET
            name = EXCLUDED.name, gender = EXCLUDED.gender, age = EXCLUDED.age, 
            sobriety = EXCLUDED.sobriety, city = EXCLUDED.city, program_info = EXCLUDED.program_info,
            username = EXCLUDED.username, phone = EXCLUDED.phone;
    """, (user_id, data.get('name'), data.get('gender'), int(data.get('age', 0)),
          data.get('sobriety'), data.get('city'), data.get('program_info'),
          data.get('username'), data.get('phone')))
    conn.commit()
    cur.close()
    conn.close()

async def save_sponsor_draft(user_id, data):
    await asyncio.to_thread(_save_draft_sync, user_id, data)

def _add_message_sync(user_id: int, role: str, content: str):
    try:
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()
        cur.execute("INSERT INTO dialog_history (user_id, role, content) VALUES (%s, %s, %s)", (user_id, role, content))
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        logging.error(f"Ошибка сохранения истории: {e}")

async def add_message_to_history(user_id: int, role: str, content: str):
    await asyncio.to_thread(_add_message_sync, user_id, role, content)

def _get_recent_history_sync(user_id: int, limit: int = 6) -> list:
    try:
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()
        cur.execute("SELECT role, content FROM dialog_history WHERE user_id = %s ORDER BY id DESC LIMIT %s", (user_id, limit))
        rows = cur.fetchall()
        cur.close()
        conn.close()
        return [{"role": r, "content": c} for r, c in reversed(rows)]
    except Exception:
        return []

async def get_recent_history(user_id: int, limit: int = 6) -> list:
    return await asyncio.to_thread(_get_recent_history_sync, user_id, limit)