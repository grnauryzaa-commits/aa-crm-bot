import json
import os
import psycopg2

DATABASE_URL = "postgresql://postgres:rjKAEdhpAeVceQzFobzCKFRbWnJwYOem@thomas.proxy.rlwy.net:12836/railway"
JSON_PATH = "reflections_parsed.json"

def upload_reflections_to_db():
    if not os.path.exists(JSON_PATH):
        print(f"Ошибка: Файл {JSON_PATH} не найден!")
        return

    with open(JSON_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    print(f"Загружено записей из JSON: {len(data)}")

    try:
        connection = psycopg2.connect(DATABASE_URL)
        cursor = connection.cursor()
        print("Успешное подключение к PostgreSQL на Railway!")

        insert_query = """
            INSERT INTO reflections (month, title, text) 
            VALUES (%s, %s, %s)
        """

        count = 0
        for item in data:
            cursor.execute(insert_query, (
                item.get("month"),
                item.get("title"),
                item.get("text")
            ))
            count += 1

        connection.commit()
        print(f"Успешно добавлено записей в базу данных: {count}")

    except Exception as error:
        print(f"Ошибка при работе с базой данных: {error}")
    
    finally:
        if 'cursor' in locals() and cursor:
            cursor.close()
        if 'connection' in locals() and connection:
            connection.close()
            print("Соединение с базой данных закрыто.")

if __name__ == "__main__":
    upload_reflections_to_db()