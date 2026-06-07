#!/bin/bash

echo "Развертывание Django-приложения security_channel"

echo "Установка зависимостей"
pip install django

echo "Применение миграций"
python manage.py migrate

echo "Остановка старых процессов"
killall python 2>/dev/null

echo "Запуск сервера"
python manage.py runserver 0.0.0.0:8000