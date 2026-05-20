FROM python:3.12

WORKDIR /app

# Копируем и устанавливаем зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade -r requirements.txt

# Копируем главный скрипт и остальные модули
COPY . .

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
  CMD curl -f http://localhost:8034/health || exit 1

# Запускаем uvicorn, указывая main:app (main.py в корне)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8034", "--log-level", "debug"]