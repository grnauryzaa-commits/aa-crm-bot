import psycopg2
from psycopg2.extras import RealDictCursor
# Импортируем DATABASE_URL и переименовываем в DB_URL для удобства
from config import DATABASE_URL as DB_URL

async def init_db():
    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()
    
    # Таблица активных спонсоров (видят все пользователи)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS sponsors (
            tg_id BIGINT PRIMARY KEY,
            name VARCHAR(100),
            age VARCHAR(10),
            sobriety VARCHAR(100),
            city VARCHAR(100),
            program_info TEXT,
            username VARCHAR(100),
            phone VARCHAR(50)
        );
    """)
    
    # Таблица черновиков на проверку админу (модерация изменений)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS sponsor_drafts (
            tg_id BIGINT PRIMARY KEY,
            name VARCHAR(100),
            age VARCHAR(10),
            sobriety VARCHAR(100),
            city VARCHAR(100),
            program_info TEXT,
            username VARCHAR(100),
            phone VARCHAR(50)
        );
    """)
    conn.commit()
    cur.close()
    conn.close()

async def get_sponsor_by_tg_id(tg_id: int):
    conn = psycopg2.connect(DB_URL, cursor_factory=RealDictCursor)
    cur = conn.cursor()
    cur.execute("SELECT * FROM sponsors WHERE tg_id = %s", (tg_id,))
    res = cur.fetchone()
    cur.close()
    conn.close()
    return res

async def save_sponsor_draft(tg_id: int, data: dict):
    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO sponsor_drafts (tg_id, name, age, sobriety, city, program_info, username, phone)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (tg_id) DO UPDATE SET
            name = EXCLUDED.name, 
            age = EXCLUDED.age, 
            sobriety = EXCLUDED.sobriety,
            city = EXCLUDED.city, 
            program_info = EXCLUDED.program_info,
            username = EXCLUDED.username, 
            phone = EXCLUDED.phone;
    """, (tg_id, data['name'], data['age'], data['sobriety'], data['city'], data['program_info'], data['username'], data.get('phone', 'Не указан')))
    conn.commit()
    cur.close()
    conn.close()

async def approve_sponsor_draft(tg_id: int):
    conn = psycopg2.connect(DB_URL, cursor_factory=RealDictCursor)
    cur = conn.cursor()
    
    # Ищем черновик, который одобрил админ
    cur.execute("SELECT * FROM sponsor_drafts WHERE tg_id = %s", (tg_id,))
    draft = cur.fetchone()
    
    if draft:
        # Переносим/обновляем данные в основную таблицу активных спонсоров
        cur.execute("""
            INSERT INTO sponsors (tg_id, name, age, sobriety, city, program_info, username, phone)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (tg_id) DO UPDATE SET
                name = EXCLUDED.name, 
                age = EXCLUDED.age, 
                sobriety = EXCLUDED.sobriety,
                city = EXCLUDED.city, 
                program_info = EXCLUDED.program_info,
                username = EXCLUDED.username, 
                phone = EXCLUDED.phone;
        """, (draft['tg_id'], draft['name'], draft['age'], draft['sobriety'], draft['city'], draft['program_info'], draft['username'], draft['phone']))
        
        # Удаляем из таблицы черновиков, так как он уже одобрен
        cur.execute("DELETE FROM sponsor_drafts WHERE tg_id = %s", (tg_id,))
        conn.commit()
        res = True
    else:
        res = False
        
    cur.close()
    conn.close()
    return res

async def delete_sponsor_draft(tg_id: int):
    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()
    cur.execute("DELETE FROM sponsor_drafts WHERE tg_id = %s", (tg_id,))
    conn.commit()
    cur.close()
    conn.close()