# Используем официальный образ Python
FROM python:3.11-slim

# Устанавливаем зависимости системы
RUN apt-get update && apt-get install -y build-essential && rm -rf /var/lib/apt/lists/*

# Копируем файлы проекта
WORKDIR /app
COPY . /app

# Устанавливаем Python-зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Открываем порт (Railway сам подставит $PORT)
EXPOSE 5050

# Команда запуска
CMD ["gunicorn", "petri_dish.run:app", "--worker-class", "eventlet", "-w", "1", "--bind", "0.0.0.0:5050"]
