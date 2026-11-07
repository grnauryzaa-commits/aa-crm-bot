FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Добавляем пути, чтобы Питон видел и корень, и папку routers
ENV PYTHONPATH=/app:/app/routers

CMD ["python", "bot.py"]