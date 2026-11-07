FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .

# Обновляем pip и ставим зависимости без кэша
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "bot.py"]