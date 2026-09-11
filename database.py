import psycopg2
import logging
import asyncio
import aiosqlite # Убедись, что aiosqlite установлен в requirements.txt
from config import DATABASE_URL as DB_URL

# Настройка логирования
logging.basicConfig(level=logging.INFO)

async def init_db():
    logging.info("🚀 Запуск принудительного обновления структуры базы данных (добавление пола и истории диалогов)...")
    try:
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()
        
        # 1. СОЗДАНИЕ ТАБЛИЦЫ SPONSORS
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
        
        # 2. СОЗДАНИЕ ТАБЛИЦЫ ЧЕРНОВИКОВ (БЕЗОПАСНОЕ)
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

        # 4. СОЗДАНИЕ ТАБЛИЦЫ ДЛЯ ИСТОРИИ ДИАЛОГОВ (ЧЕРЕЗ aiosqlite или async psycopg2)
        # Так как проект использует async/await, инициализируем табличку диалогов через aiosqlite (или локальный файл БД истории)
        await init_history_db()

        logging.info("🎉 СТРУКТУРА БАЗЫ ДАННЫХ ИСПРАВЛЕНА И ГОТОВА К РАБОТЕ!")
        
    except Exception as e:
        logging.error(f"❌ Критическая ошибка инициализации БД: {e}")
        raise e


# =====================================================================
# ФУНКЦИИ ВЗАИМОДЕЙСТВИЯ С БАЗОЙ ДАННЫХ (СПОНСОРЫ И ЧЕРНОВИКИ)
# =====================================================================

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
        logging.error(f"Ошибка выполнения _get_sponsor_sync: {e}")
        return None

async def get_sponsor_by_tg_id(user_id):
    """Проверяет, есть ли пользователь в базе активных спонсоров"""
    return await asyncio.to_thread(_get_sponsor_sync, user_id)


def _save_draft_sync(user_id, data):
    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO sponsor_drafts (user_id, name, gender, age, sobriety, city, program_info, username, phone)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (user_id) DO UPDATE SET
            name = EXCLUDED.name, 
            gender = EXCLUDED.gender,
            age = EXCLUDED.age, 
            sobriety = EXCLUDED.sobriety,
            city = EXCLUDED.city, 
            program_info = EXCLUDED.program_info,
            username = EXCLUDED.username, 
            phone = EXCLUDED.phone;
    """, (
        user_id, 
        data.get('name'), 
        data.get('gender'),
        int(data.get('age', 0)),
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


# =====================================================================
# ФУНКЦИИ ИСТОРИИ ДИАЛОГОВ (ДЛЯ КОНТЕКСТА ИИ)
# =====================================================================

async def init_history_db():
    """Создает локальную таблицу истории чата для сохранения контекста беседы с ИИ"""
    async with aiosqlite.connect("sponsors.db") as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS dialog_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id BIGINT,
                role TEXT,
                content TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.commit()

async def add_message_to_history(user_id: int, role: str, content: str):
    """Записывает реплику пользователя или бота в историю диалога"""
    async with aiosqlite.connect("sponsors.db") as db:
        await db.execute(
            "INSERT INTO dialog_history (user_id, role, content) VALUES (?, ?, ?)",
            (user_id, role, content)
        )
        await db.commit()

async def get_recent_history(user_id: int, limit: int = 6) -> list:
    """Достает последние сообщения пользователя для сохранения логической цепочки"""
    async with aiosqlite.connect("sponsors.db") as db:
        async with db.execute(
            "SELECT role, content FROM dialog_history WHERE user_id = ? ORDER BY id DESC LIMIT ?",
            (user_id, limit)
        ) as cursor:
            rows = await cursor.fetchall()
            # Возвращаем в хронологическом порядке (от старых к новым)
            return [{"role": row[0], "content": row[1]} for row in reversed(rows)]