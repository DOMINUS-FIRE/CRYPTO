FROM python:3.10-slim

WORKDIR /app

# Копируем зависимости
COPY requirements.txt .

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем код
COPY . .

# Создаем необходимые файлы если их нет
RUN touch subscribers.json
RUN if [ ! -f messages.json ]; then python -c "import json; json.dump({'messages': []}, open('messages.json', 'w'))" ; fi

# Запускаем бота
CMD ["python", "crypto_bot.py"]