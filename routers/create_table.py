import psycopg2
import sys
from pathlib import Path as _Path
_ROOT = _Path(__file__).resolve().parents[0]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from db_config import DATABASE_URL



def create_reflections_table():
    try:
        connection = psycopg2.connect(DATABASE_URL)
        cursor = connection.cursor()
        print("Подключение к PostgreSQL успешно установлено!")

        create_table_query = """
        CREATE TABLE IF NOT EXISTS reflections (
            id SERIAL PRIMARY KEY,
            month VARCHAR(50),
            title VARCHAR(255),
            text TEXT
        );
        """

        cursor.execute(create_table_query)
        connection.commit()
        print("Таблица 'reflections' успешно создана (или уже существовала)!")

    except Exception as error:
        print(f"Ошибка при создании таблицы: {error}")
    
    finally:
        if 'cursor' in locals() and cursor:
            cursor.close()
        if 'connection' in locals() and connection:
            connection.close()

if __name__ == "__main__":
    create_reflections_table()