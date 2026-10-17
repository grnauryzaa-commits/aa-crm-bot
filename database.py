import asyncio
import logging
import psycopg2
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup
from config import DATABASE_URL as DB_URL

logging.basicConfig(level=logging.INFO)

async def init_db():
  logging.info("🚀 Запуск инициализации структуры базы данных...")
  try:
    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()

    cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                telegram_id BIGINT PRIMARY KEY,
                language VARCHAR(10) DEFAULT 'ru'
            );
        """)
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
    cur.execute("ALTER TABLE sponsors ADD COLUMN IF NOT EXISTS gender VARCHAR(10);")
    cur.execute("ALTER TABLE sponsor_drafts ADD COLUMN IF NOT EXISTS gender VARCHAR(10);")
    cur.execute("ALTER TABLE sponsors ADD COLUMN IF NOT EXISTS program_info TEXT;")
    cur.execute("ALTER TABLE sponsor_drafts ADD COLUMN IF NOT EXISTS program_info TEXT;")
    cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS language VARCHAR(10) DEFAULT 'ru';")
    
    cur.execute("""
            CREATE TABLE IF NOT EXISTS reflections_archive (
                day INT, month INT, title VARCHAR(255), text TEXT, PRIMARY KEY (day, month)
            );
        """)
    cur.execute("""
            CREATE TABLE IF NOT EXISTS dialog_history (
                id SERIAL PRIMARY KEY, user_id BIGINT, role TEXT, content TEXT, timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
    conn.commit()
    cur.close()
    conn.close()
    logging.info("🎉 БАЗА ДАННЫХ УСПЕШНО ИНИЦИАЛИЗИРОВАНА!")
  except Exception as e:
    logging.error(f"❌ Ошибка инициализации БД: {e}")
    raise e

def _get_user_language_sync(user_id: int) -> str:
  try:
    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()
    cur.execute("SELECT language FROM users WHERE telegram_id = %s", (user_id,))
    row = cur.fetchone()
    cur.close(); conn.close()
    return row[0] if row and row[0] in ["ru", "kk"] else "ru"
  except Exception: return "ru"

async def get_user_language(user_id: int) -> str:
  return await asyncio.to_thread(_get_user_language_sync, user_id)

def _set_user_language_sync(user_id: int, lang: str):
  try:
    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()
    cur.execute("""
            INSERT INTO users (telegram_id, language) VALUES (%s, %s)
            ON CONFLICT (telegram_id) DO UPDATE SET language = EXCLUDED.language
        """, (user_id, lang))
    conn.commit(); cur.close(); conn.close()
  except Exception as e: logging.error(f"Ошибка сохранения языка: {e}")

async def set_user_language(user_id: int, lang: str):
  await asyncio.to_thread(_set_user_language_sync, user_id, lang)

def get_main_menu_keyboard(lang: str = "ru") -> ReplyKeyboardMarkup:
  if lang == "kk":
    keyboard = [[KeyboardButton(text="➕ Демеуші болу"), KeyboardButton(text="🤝 Демеушілер")],
                [KeyboardButton(text="🗓 Кесте"), KeyboardButton(text="📖 Күнделікті ой-толғаулар")],
                [KeyboardButton(text="? Көмек"), KeyboardButton(text="🌐 Тіл: Қазақша")]]
  else:
    keyboard = [[KeyboardButton(text="➕ Стать спонсором"), KeyboardButton(text="🤝 Спонсоры")],
                [KeyboardButton(text="🗓 Расписание"), KeyboardButton(text="📖 Ежедневные размышления")],
                [KeyboardButton(text="? Помощь"), KeyboardButton(text="🌐 Язык: Русский")]]
  return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

def _get_sponsor_sync(user_id):
  try:
    conn = psycopg2.connect(DB_URL); cur = conn.cursor()
    cur.execute("SELECT user_id FROM sponsors WHERE user_id = %s;", (user_id,))
    res = cur.fetchone(); cur.close(); conn.close()
    return res
  except Exception: return None

async def get_sponsor_by_tg_id(user_id):
  return await asyncio.to_thread(_get_sponsor_sync, user_id)

def _save_draft_sync(user_id, data):
  conn = psycopg2.connect(DB_URL); cur = conn.cursor()
  cur.execute("""
        INSERT INTO sponsor_drafts (user_id, name, gender, age, sobriety, city, program_info, username, phone)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (user_id) DO UPDATE SET
            name = EXCLUDED.name, gender = EXCLUDED.gender, age = EXCLUDED.age, 
            sobriety = EXCLUDED.sobriety, city = EXCLUDED.city, program_info = EXCLUDED.program_info,
            username = EXCLUDED.username, phone = EXCLUDED.phone;
    """, (user_id, data.get("name"), data.get("gender"), int(data.get("age", 0)),
          data.get("sobriety"), data.get("city"), data.get("program_info"), data.get("username"), data.get("phone")))
  conn.commit(); cur.close(); conn.close()

async def save_sponsor_draft(user_id, data):
  await asyncio.to_thread(_save_draft_sync, user_id, data)

def _add_message_sync(user_id: int, role: str, content: str):
  try:
    conn = psycopg2.connect(DB_URL); cur = conn.cursor()
    cur.execute("INSERT INTO dialog_history (user_id, role, content) VALUES (%s, %s, %s)", (user_id, role, content))
    conn.commit(); cur.close(); conn.close()
  except Exception as e: logging.error(f"Ошибка сохранения истории: {e}")

async def add_message_to_history(user_id: int, role: str, content: str):
  await asyncio.to_thread(_add_message_sync, user_id, role, content)

def _get_recent_history_sync(user_id: int, limit: int = 6) -> list:
  try:
    conn = psycopg2.connect(DB_URL); cur = conn.cursor()
    cur.execute("SELECT role, content FROM dialog_history WHERE user_id = %s ORDER BY id DESC LIMIT %s", (user_id, limit))
    rows = cur.fetchall(); cur.close(); conn.close()
    return [{"role": r, "content": c} for r, c in reversed(rows)]
  except Exception: return []

async def get_recent_history(user_id: int, limit: int = 6) -> list:
  return await asyncio.to_thread(_get_recent_history_sync, user_id, limit)

def _init_actions_table_sync():
    try:
        conn = psycopg2.connect(DB_URL); cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS user_actions (
                id SERIAL PRIMARY KEY, user_id BIGINT NOT NULL, action_type VARCHAR(50) NOT NULL, action_name VARCHAR(150) NOT NULL, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        conn.commit(); cur.close(); conn.close()
    except Exception as e: logging.error(f"Ошибка создания user_actions: {e}")

def _log_user_action_sync(user_id: int, action_type: str, action_name: str):
    try:
        conn = psycopg2.connect(DB_URL); cur = conn.cursor()
        cur.execute("INSERT INTO user_actions (user_id, action_type, action_name) VALUES (%s, %s, %s);", (user_id, action_type, action_name))
        conn.commit(); cur.close(); conn.close()
    except Exception as e: logging.error(f"Ошибка логирования действия: {e}")

async def log_user_action(user_id: int, action_type: str, action_name: str):
    await asyncio.to_thread(_log_user_action_sync, user_id, action_type, action_name)

def _get_report_data_sync() -> dict:
    result = {
        "total_users": 0, "active_week": 0, "total_actions": 0, "ai_week": 0, "top_actions": [],
        "total_sponsors": 0, "drafts_count": 0, "cities": [], "genders": [], "ages": [],
        "monthly_users": [], "action_types": [], "city_activity": [], "lang_ru": 0, "lang_kk": 0,
    }
    try:
        conn = psycopg2.connect(DB_URL); cur = conn.cursor()

        cur.execute("SELECT COUNT(*) FROM users;"); result["total_users"] = cur.fetchone()[0] or 0
        cur.execute("SELECT COUNT(*) FROM sponsors;"); result["total_sponsors"] = cur.fetchone()[0] or 0
        cur.execute("SELECT COUNT(*) FROM sponsor_drafts;"); result["drafts_count"] = cur.fetchone()[0] or 0
        
        cur.execute("SELECT language, COUNT(*) FROM users GROUP BY language;")
        langs = dict(cur.fetchall()); result["lang_ru"] = langs.get("ru", 0); result["lang_kk"] = langs.get("kk", 0)

        cur.execute("SELECT gender, COUNT(*) FROM sponsors WHERE gender IS NOT NULL AND gender != '' GROUP BY gender;"); result["genders"] = cur.fetchall()
        cur.execute("SELECT city, COUNT(*) FROM sponsors WHERE city IS NOT NULL AND city != '' GROUP BY city ORDER BY COUNT(*) DESC LIMIT 10;"); result["cities"] = cur.fetchall()
        
        # РОСТ ПО МЕСЯЦАМ (ПО ПЕРВОМУ СООБЩЕНИЮ - ТАК БЫЛО РАНЬШЕ)
        cur.execute("""
            WITH first_messages AS (SELECT user_id, MIN(timestamp) as first_seen FROM dialog_history GROUP BY user_id)
            SELECT TO_CHAR(first_seen, 'TMMonth YYYY') as month_name, TO_CHAR(first_seen, 'YYYY-MM') as month_num, COUNT(*) as cnt
            FROM first_messages GROUP BY month_name, month_num ORDER BY month_num DESC LIMIT 12;
        """)
        result["monthly_users"] = [(row[0], row[2]) for row in cur.fetchall()]

        cur.execute("""
            SELECT CASE WHEN age BETWEEN 18 AND 25 THEN '18-25' WHEN age BETWEEN 26 AND 35 THEN '26-35' WHEN age BETWEEN 36 AND 45 THEN '36-45' WHEN age BETWEEN 46 AND 55 THEN '46-55' WHEN age BETWEEN 56 AND 65 THEN '56-65' WHEN age > 65 THEN '65+' ELSE 'не указан' END AS age_group, COUNT(*)
            FROM sponsors WHERE age IS NOT NULL GROUP BY age_group ORDER BY COUNT(*) DESC;
        """)
        result["ages"] = cur.fetchall()

        cur.execute("SELECT COUNT(*) FROM user_actions;"); result["total_actions"] = cur.fetchone()[0] or 0
        cur.execute("SELECT COUNT(*) FROM user_actions WHERE action_type = 'ai_chat' AND created_at >= NOW() - INTERVAL '7 days';"); result["ai_week"] = cur.fetchone()[0] or 0
        cur.execute("SELECT COUNT(DISTINCT user_id) FROM user_actions WHERE created_at >= NOW() - INTERVAL '7 days';"); result["active_week"] = cur.fetchone()[0] or 0

        cur.execute("SELECT action_type, COUNT(*) as cnt FROM user_actions GROUP BY action_type ORDER BY cnt DESC;"); result["action_types"] = cur.fetchall()
        cur.execute("SELECT action_type, action_name, COUNT(*) as cnt FROM user_actions GROUP BY action_type, action_name ORDER BY cnt DESC LIMIT 15;"); result["top_actions"] = cur.fetchall()
        cur.execute("SELECT s.city, COUNT(ua.id) as cnt FROM user_actions ua JOIN sponsors s ON ua.user_id = s.user_id WHERE s.city IS NOT NULL AND s.city != '' GROUP BY s.city ORDER BY cnt DESC LIMIT 5;"); result["city_activity"] = cur.fetchall()

        cur.close(); conn.close()
    except Exception as e:
        logging.error(f"Ошибка сбора данных отчёта: {e}")
    return result

async def get_report_data() -> dict:
    return await asyncio.to_thread(_get_report_data_sync)