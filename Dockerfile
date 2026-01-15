# Используем версию, которая совпадает с requirements.txt
FROM mcr.microsoft.com/playwright/python:v1.49.1-jammy

WORKDIR /app

# Сначала копируем требования и ставим их
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем весь остальной код
COPY . .

# Команда запуска (ИЗМЕНЕНО: запускаем как модуль -m)
CMD ["python", "-m", "hh_automation.server"]
