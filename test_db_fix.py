#!/usr/bin/env python3
"""
Тест для проверки исправления проблем с БД
"""
import os
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from src.database.db_manager import DBConfig, DBManager, setup_database
from dotenv import load_dotenv

load_dotenv()


def test_db_creation():
    """Тестирование создания БД"""
    print("🧪 Тестирование создания БД...")

    config = DBConfig.from_env()
    db_manager = DBManager(config)

    try:
        # Пробуем создать БД
        db_manager.create_database()
        print("✅ База данных создана успешно")

        # Пробуем создать таблицы
        db_manager.create_tables()
        print("✅ Таблицы созданы успешно")

        # Проверяем подключение
        with db_manager.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT version();")
                version = cursor.fetchone()
                print(f"✅ Подключение к PostgreSQL: {version[0]}")

                # Проверяем существование таблиц
                cursor.execute("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public'
                """)
                tables = cursor.fetchall()
                print(f"✅ Таблицы в базе: {[t[0] for t in tables]}")

        return True

    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    test_db_creation()
