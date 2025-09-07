import psycopg2
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import os
from contextlib import contextmanager


@dataclass
class DBConfig:
    """Конфигурация подключения к базе данных"""
    dbname: str = "hh_vacancies"
    user: str = "postgres"
    password: str = "password"  # Измените на ваш пароль!
    host: str = "localhost"
    port: str = "5432"

    @classmethod
    def from_env(cls):
        """Создание конфигурации из переменных окружения"""
        return cls(
            dbname=os.getenv("DB_NAME", "hh_vacancies"),
            user=os.getenv("DB_USER", "postgres"),
            password=os.getenv("DB_PASSWORD", "password"),
            host=os.getenv("DB_HOST", "localhost"),
            port=os.getenv("DB_PORT", "5432")
        )


class DBManager:
    """Класс для управления базой данных вакансий"""

    def __init__(self, config: DBConfig = None):
        self.config = config or DBConfig()
        self.connection = None

    @contextmanager
    def get_connection(self):
        """Контекстный менеджер для подключения к БД"""
        conn = None
        try:
            conn = psycopg2.connect(
                dbname=self.config.dbname,
                user=self.config.user,
                password=self.config.password,
                host=self.config.host,
                port=self.config.port,
                options="-c client_encoding=UTF8"  # Добавляем явное указание кодировки
            )
            # Устанавливаем кодировку явно
            with conn.cursor() as cursor:
                cursor.execute("SET client_encoding TO 'UTF8'")
            yield conn
        except Exception as e:
            print(f"❌ Ошибка подключения к БД: {e}")
            raise
        finally:
            if conn:
                conn.close()

    def create_database(self):
        """Создание базы данных если не существует"""
        try:
            # Подключаемся к дефолтной БД для создания новой
            conn = psycopg2.connect(
                dbname="postgres",
                user=self.config.user,
                password=self.config.password,
                host=self.config.host,
                port=self.config.port,
                options="-c client_encoding=UTF8"  # Добавляем явное указание кодировки
            )
            conn.autocommit = True
            cursor = conn.cursor()

            # Устанавливаем кодировку для соединения
            cursor.execute("SET client_encoding TO 'UTF8'")

            # Проверяем существование БД
            cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s", (self.config.dbname,))
            exists = cursor.fetchone()

            if not exists:
                # Создаем БД с явным указанием кодировки
                cursor.execute(f"CREATE DATABASE {self.config.dbname} WITH ENCODING 'UTF8' TEMPLATE template0")
                print(f"✅ База данных {self.config.dbname} создана с кодировкой UTF8")
            else:
                print(f"ℹ️ База данных {self.config.dbname} уже существует")

            cursor.close()
            conn.close()

        except Exception as e:
            print(f"❌ Ошибка при создании БД: {e}")
            raise

    def create_tables(self):
        """Создание таблиц в базе данных"""
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                # Таблица компаний
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS companies (
                        company_id SERIAL PRIMARY KEY,
                        name VARCHAR(255) NOT NULL UNIQUE,
                        url VARCHAR(500),
                        description TEXT,
                        hh_id INTEGER UNIQUE
                    )
                """)

                # Таблица вакансий
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS vacancies (
                        vacancy_id SERIAL PRIMARY KEY,
                        title VARCHAR(500) NOT NULL,
                        company_id INTEGER REFERENCES companies(company_id) ON DELETE CASCADE,
                        salary_from INTEGER,
                        salary_to INTEGER,
                        salary_avg INTEGER,
                        currency VARCHAR(10),
                        url VARCHAR(500) UNIQUE,
                        description TEXT,
                        experience VARCHAR(100),
                        employment_mode VARCHAR(100),
                        created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)

                # Индексы для улучшения производительности
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_vacancies_title ON vacancies(title)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_vacancies_salary_avg ON vacancies(salary_avg)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_vacancies_company ON vacancies(company_id)")

                conn.commit()
                print("Таблицы созданы успешно")

    def insert_company(self, company_data: Dict[str, Any]) -> Optional[int]:
        """Добавление компании в базу данных"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        INSERT INTO companies (name, url, description, hh_id)
                        VALUES (%s, %s, %s, %s)
                        ON CONFLICT (hh_id) DO NOTHING
                        RETURNING company_id
                    """, (
                        company_data.get('name'),
                        company_data.get('alternate_url'),
                        company_data.get('description'),
                        company_data.get('id')
                    ))

                    result = cursor.fetchone()
                    conn.commit()
                    return result[0] if result else None

        except Exception as e:
            print(f"Ошибка при добавлении компании: {e}")
            return None

    def insert_vacancy(self, vacancy_data: Dict[str, Any], company_id: int) -> bool:
        """Добавление вакансии в базу данных"""
        try:
            salary = vacancy_data.get('salary', {})
            salary_from = salary.get('from')
            salary_to = salary.get('to')
            salary_avg = self._calculate_avg_salary(salary_from, salary_to)

            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        INSERT INTO vacancies (
                            title, company_id, salary_from, salary_to, 
                            salary_avg, currency, url, description, 
                            experience, employment_mode
                        )
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (url) DO NOTHING
                    """, (
                        vacancy_data.get('name'),
                        company_id,
                        salary_from,
                        salary_to,
                        salary_avg,
                        salary.get('currency'),
                        vacancy_data.get('alternate_url'),
                        vacancy_data.get('description', ''),
                        vacancy_data.get('experience', {}).get('name'),
                        vacancy_data.get('employment', {}).get('name')
                    ))

                    conn.commit()
                    return True

        except Exception as e:
            print(f"Ошибка при добавлении вакансии: {e}")
            return False

    def _calculate_avg_salary(self, salary_from: Optional[int], salary_to: Optional[int]) -> Optional[int]:
        """Расчет средней зарплаты"""
        if salary_from and salary_to:
            return (salary_from + salary_to) // 2
        return salary_from or salary_to

    def get_companies_and_vacancies_count(self) -> List[tuple]:
        """Получает список всех компаний и количество вакансий у каждой компании"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        SELECT c.name, COUNT(v.vacancy_id) as vacancy_count
                        FROM companies c
                        LEFT JOIN vacancies v ON c.company_id = v.company_id
                        GROUP BY c.company_id, c.name
                        ORDER BY vacancy_count DESC
                    """)
                    return cursor.fetchall()
        except Exception as e:
            print(f"Ошибка при получении данных: {e}")
            return []

    def get_all_vacancies(self) -> List[tuple]:
        """Получает список всех вакансий с указанием названия компании, названия вакансии и зарплаты и ссылки на вакансию"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        SELECT c.name, v.title, 
                               COALESCE(v.salary_avg, v.salary_from, v.salary_to, 0) as salary,
                               v.currency, v.url
                        FROM vacancies v
                        JOIN companies c ON v.company_id = c.company_id
                        ORDER BY salary DESC NULLS LAST
                    """)
                    return cursor.fetchall()
        except Exception as e:
            print(f"Ошибка при получении вакансий: {e}")
            return []

    def get_avg_salary(self) -> float:
        """Получает среднюю зарплату по вакансиям"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        SELECT AVG(salary_avg) 
                        FROM vacancies 
                        WHERE salary_avg IS NOT NULL AND salary_avg > 0
                    """)
                    result = cursor.fetchone()
                    return round(result[0], 2) if result and result[0] else 0.0
        except Exception as e:
            print(f"Ошибка при расчете средней зарплаты: {e}")
            return 0.0

    def get_vacancies_with_higher_salary(self) -> List[tuple]:
        """Получает список всех вакансий, у которых зарплата выше средней по всем вакансиям"""
        try:
            avg_salary = self.get_avg_salary()
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        SELECT c.name, v.title, v.salary_avg, v.currency, v.url
                        FROM vacancies v
                        JOIN companies c ON v.company_id = c.company_id
                        WHERE v.salary_avg > %s
                        ORDER BY v.salary_avg DESC
                    """, (avg_salary,))
                    return cursor.fetchall()
        except Exception as e:
            print(f"Ошибка при получении вакансий: {e}")
            return []

    def get_vacancies_with_keyword(self, keyword: str) -> List[tuple]:
        """Получает список всех вакансий, в названии которых содержатся переданные слова"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        SELECT c.name, v.title, v.salary_avg, v.currency, v.url
                        FROM vacancies v
                        JOIN companies c ON v.company_id = c.company_id
                        WHERE LOWER(v.title) LIKE %s
                        ORDER BY v.salary_avg DESC NULLS LAST
                    """, (f'%{keyword.lower()}%',))
                    return cursor.fetchall()
        except Exception as e:
            print(f"Ошибка при поиске вакансий: {e}")
            return []


# Утилитарные функции
def setup_database():
    """Настройка базы данных"""
    print("🔄 Настройка базы данных...")

    # Настройка БД
    config = DBConfig.from_env()
    db_manager = DBManager(config)

    try:
        db_manager.create_database()
        db_manager.create_tables()
        print("✅ База данных настроена успешно")
        return True
    except Exception as e:
        print(f"❌ Ошибка при настройке БД: {e}")
        return False
