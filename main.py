#!/usr/bin/env python3
"""
Главный запускающий файл проекта HH API Integration
"""
import os
import sys

# Добавляем текущую директорию в путь для импортов
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.main import user_interaction

if __name__ == "__main__":
    user_interaction()
