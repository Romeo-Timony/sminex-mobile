# Использование базового образа Python
FROM python:3.10-slim

# Установка системных зависимостей для тестирования APK (Java, ADB, Node.js)
RUN apt-get update && apt-get install -y --no-install-recommends \
    openjdk-17-jre-headless \
    android-tools-adb \
    curl \
    gnupg \
    wget \
    unzip \
    && rm -rf /var/lib/apt/lists/*

# Создание рабочей директории в контейнере
WORKDIR /app

# Копирование файла зависимостей
COPY requirements.txt .

# Установка Python-библиотек
RUN pip install --no-cache-dir -r requirements.txt

# Копирование исходного кода тестов
COPY . .

# Команда по умолчанию для запуска тестов
CMD ["pytest", "--alluredir=allure-results"]
