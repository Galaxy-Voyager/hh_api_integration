import os
import psycopg2
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()


def test_postgres_connection():
    """Простой тест подключения к PostgreSQL"""
    try:
        # Пробуем подключиться к основной базе postgres
        conn = psycopg2.connect(
            dbname="postgres",
            user=os.getenv("DB_USER", "postgres"),
            password=os.getenv("DB_PASSWORD", "password"),
            host=os.getenv("DB_HOST", "localhost"),
            port=os.getenv("DB_PORT", "5432"),
            client_encoding='UTF-8'
        )

        with conn.cursor() as cursor:
            cursor.execute("SELECT version();")
            version = cursor.fetchone()
            print(f"✅ PostgreSQL version: {version[0]}")

            # Проверяем существование базы
            cursor.execute("SELECT 1 FROM pg_database WHERE datname = 'hh_vacancies'")
            exists = cursor.fetchone()
            if exists:
                print("✅ База hh_vacancies уже существует")
            else:
                print("ℹ️ База hh_vacancies не существует")

        conn.close()
        return True

    except Exception as e:
        print(f"❌ Ошибка подключения: {e}")
        return False


def test_db_creation():
    """Тест создания базы данных"""
    try:
        # Сначала подключаемся к postgres
        conn = psycopg2.connect(
            dbname="postgres",
            user=os.getenv("DB_USER", "postgres"),
            password=os.getenv("DB_PASSWORD", "password"),
            host=os.getenv("DB_HOST", "localhost"),
            port=os.getenv("DB_PORT", "5432")
        )
        conn.autocommit = True

        with conn.cursor() as cursor:
            # Создаем базу если не существует
            cursor.execute("SELECT 1 FROM pg_database WHERE datname = 'hh_vacancies'")
            if not cursor.fetchone():
                cursor.execute("CREATE DATABASE hh_vacancies")
                print("✅ База hh_vacancies создана")
            else:
                print("✅ База hh_vacancies уже существует")

        conn.close()
        return True

    except Exception as e:
        print(f"❌ Ошибка создания БД: {e}")
        return False


if __name__ == "__main__":
    print("🧪 Тестирование подключения к PostgreSQL...")

    if test_postgres_connection():
        print("\n🧪 Тестирование создания базы данных...")
        test_db_creation()
    else:
        print("\n❌ Не удалось подключиться к PostgreSQL")
        print("Проверьте:")
        print("1. Запущен ли PostgreSQL (Get-Service -Name postgresql*)")
        print("2. Правильный ли пароль в файле .env")
        print("3. Доступен ли localhost:5432")
