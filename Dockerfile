FROM python:3.11-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Сначала копируем только requirements.txt (для кэширования слоев)
COPY requirements.txt .

# Устанавливаем зависимости. Флаг --no-cache-dir экономит память.
RUN pip install --no-cache-dir -r requirements.txt

# Копируем весь остальной код
COPY . .

# Запускаем бота
CMD ["python", "bot.py"]