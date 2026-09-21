from docx import Document
import json
import os

def parse_reflections(file_path):
    if not os.path.exists(file_path):
        print(f"Ошибка: Файл {file_path} не найден!")
        return

    doc = Document(file_path)
    reflections_list = []
    current_month = "Белгісіз"
    current_title = "Без названия"
    current_text = []
    
    months_dict = {
        "қаңтар": "Январь", 
        "ақпан": "Февраль", 
        "наурыз": "Март",
        "сәуір": "Апрель", 
        "мамыр": "Май", 
        "маусым": "Июнь",
        "шілде": "Июль", 
        "тамыз": "Август", 
        "қыркүйек": "Сентябрь",
        "қазан": "Октябрь", 
        "қараша": "Ноябрь", 
        "желтоқсан": "Декабрь"
    }

    for paragraph in doc.paragraphs:
        text = paragraph.text.strip()
        if not text:
            continue
            
        text_lower = text.lower()
        
        # Проверяем, месяц ли это
        found_month = None
        for k, v in months_dict.items():
            if k in text_lower and len(text) < 30:
                found_month = v
                break
                
        if found_month:
            if current_text:
                reflections_list.append({
                    "month": current_month,
                    "title": current_title,
                    "text": "\n".join(current_text)
                })
                current_text = []
            current_month = found_month
            continue

        # Если строка короткая и написана капсом — считаем ее заголовком
        if text.isupper() and len(text.split()) < 6:
            if current_text:
                reflections_list.append({
                    "month": current_month,
                    "title": current_title,
                    "text": "\n".join(current_text)
                })
                current_text = []
            current_title = text
        else:
            current_text.append(text)
            
    # Сохраняем последний хвост
    if current_text:
        reflections_list.append({
            "month": current_month,
            "title": current_title,
            "text": "\n".join(current_text)
        })

    print(f"Успешно обработано записей: {len(reflections_list)}")
    
    # Сохраняем результат в JSON-файл в корне проекта
    output_json = "reflections_parsed.json"
    with open(output_json, "w", encoding="utf-8") as f:
        json.dump(reflections_list, f, ensure_ascii=False, indent=4)
    print(f"Готово! Файл сохранен как: {output_json}")

if __name__ == "__main__":
    # Указываем путь к файлу из расчета, что скрипт запускается из корня AA_BOT, 
    # а файл reflections_kz.docx лежит в папке routers (или наоборот, поменяйте при необходимости)
    file_name = "routers/reflections_kz.docx" 
    parse_reflections(file_name)