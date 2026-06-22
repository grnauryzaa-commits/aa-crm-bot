import os
import psycopg2
from psycopg2.extras import DictCursor

# Получаем строку подключения из переменных окружения Railway
DATABASE_URL = os.getenv("DATABASE_URL")

def get_connection():
    # Создаем подключение к PostgreSQL
    return psycopg2.connect(DATABASE_URL, sslmode="require")

def init_db():
    conn = get_connection()
    cur = conn.cursor()

    # В PostgreSQL синтаксис немного отличается (SERIAL вместо AUTOINCREMENT)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS sponsors (
        id SERIAL PRIMARY KEY,
        name TEXT,
        age TEXT,
        identity TEXT,
        sobriety TEXT,
        city TEXT,
        formats TEXT,
        telegram TEXT,
        phone TEXT,
        about TEXT
    );
    """)
    conn.commit()
    cur.close()
    conn.close()


def add_sponsor(data):
    conn = get_connection()
    cur = conn.cursor()

    # В PostgreSQL плейсхолдеры — %s вместо ?
    cur.execute("""
    INSERT INTO sponsors
    (name, age, identity, sobriety, city, formats, telegram, phone, about)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, data)

    conn.commit()
    cur.close()
    conn.close()


def get_all():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT id, name, city, sobriety FROM sponsors;")
    data = cur.fetchall()

    cur.close()
    conn.close()
    return data


def get_sponsor_by_id(sponsor_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT id, name, age, identity, sobriety, city, formats, telegram, phone, about FROM sponsors WHERE id=%s;", (sponsor_id,))
    data = cur.fetchone()

    cur.close()
    conn.close()
    return data