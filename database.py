import sqlite3


def init_db():
    conn = sqlite3.connect("sponsors.db")
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS sponsors (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        age TEXT,
        identity TEXT,
        sobriety TEXT,
        city TEXT,
        formats TEXT,
        telegram TEXT UNIQUE,
        phone TEXT,
        about TEXT
    )
    """)

    conn.commit()
    conn.close()


def add_sponsor(data):
    conn = sqlite3.connect("sponsors.db")
    cur = conn.cursor()

    cur.execute("""
    INSERT OR IGNORE INTO sponsors VALUES (NULL,?,?,?,?,?,?,?,?,?)
    """, data)

    conn.commit()
    conn.close()


def get_all():
    conn = sqlite3.connect("sponsors.db")
    cur = conn.cursor()

    cur.execute("SELECT * FROM sponsors")
    data = cur.fetchall()

    conn.close()
    return data

def get_sponsor_by_id(sponsor_id):

    conn = sqlite3.connect("database.db")
    cur = conn.cursor()

    cur.execute(
        "SELECT * FROM sponsors WHERE id=?",
        (sponsor_id,)
    )

    sponsor = cur.fetchone()

    conn.close()

    return sponsor