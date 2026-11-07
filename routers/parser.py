import requests
from bs4 import BeautifulSoup
import psycopg2
import logging
from config import DATABASE_URL

logging.basicConfig(level=logging.INFO)

# Задаем порядок городов для красоты в меню
CITY_ORDER = {
    "Алматы": 1, "Астана": 2, "Актау": 3, "Актобе": 4, "Атырау": 5,
    "Караганда": 6, "Кокшетау": 7, "Конаев": 8, "Костанай": 9,
    "Павлодар": 10, "Петропавловск": 11, "Рудный": 12, "Семей": 13,
    "Талдыкорган": 14, "Усть-Каменогорск": 15, "Кызылорда": 16,
    "Шымкент": 17, "Экибастуз": 18, "Жетысай": 19
}

def update_schedule_from_site():
    url = "https://aaorg.kz/sobraniya/"
    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        current_city = "Неизвестно"
        groups_data = []

        # Ищем заголовки и текст под ними
        for element in soup.find_all(['h2', 'h3', 'p']):
            text = element.text.strip()
            if not text: continue
            
            if element.name == 'h2':
                current_city = text
            elif element.name == 'h3':
                # Название группы (например, АА «Виктория»)
                group_name = text
                # Ищем следующий параграф с адресом и временем
                next_p = element.find_next('p')
                address, time_info, contacts = "", "", ""
                if next_p:
                    p_text = next_p.text.strip()
                    if "Адрес:" in p_text:
                        address = p_text.split("Адрес:")[1].split("Время:")[0].strip()
                    if "Время:" in p_text:
                        time_info = p_text.split("Время:")[1].split("Контакты:")[0].strip()
                    if "Контакты:" in p_text:
                        contacts = p_text.split("Контакты:")[1].strip()
                
                sort_order = CITY_ORDER.get(current_city, 99)
                groups_data.append((current_city, group_name, address, time_info, contacts, sort_order))

        if not groups_data:
            logging.warning("Парсер не нашел данные на сайте.")
            return

        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        cur.execute("TRUNCATE TABLE aa_schedule RESTART IDENTITY;")
        
        for group in groups_data:
            cur.execute(
                "INSERT INTO aa_schedule (city, group_name, address, time_info, contacts, sort_order) VALUES (%s, %s, %s, %s, %s, %s)",
                group
            )
        
        conn.commit()
        cur.close()
        conn.close()
        logging.info(f"Успешно обновлено {len(groups_data)} групп.")
        
    except Exception as e:
        logging.error(f"Ошибка парсинга: {e}")

if __name__ == "__main__":
    update_schedule_from_site()