#!/bin/bash
set -e

echo "Ожидание старта базы данных..."
sleep 5

echo "Инициализация базы данных..."
python init_db.py

echo "Запуск user_service..."
uvicorn main:app --host 0.0.0.0 --port 8000
