FROM python:3.11-slim

RUN apt-get update && apt-get install -y build-essential && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY . /app

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8000

CMD exec gunicorn bacteria_simulation.run:app --worker-class eventlet -w 1 --bind 0.0.0.0:$PORT
