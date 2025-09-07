#!/usr/bin/env python3
"""
Главный запускающий файл проекта HH API Integration
"""
import os
import sys

# Добавляем текущую директорию в путь для импортов
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# Теперь импортируем наши модули
from src.api.hh_api import HeadHunterAPI
from src.api.company_api import fetch_companies_data
from src.models.vacancy import Vacancy
from src.storage.json_saver import JSONSaver
from src.database.db_manager import DBManager, DBConfig, setup_database
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()


def setup_and_fill_database():
    """Настройка и заполнение базы данных"""
    print("🔄 Настройка базы данных...")

    # Настройка БД
    config = DBConfig.from_env()
    db_manager = DBManager(config)

    if not setup_database():
        print("❌ Ошибка настройки базы данных")
        return False

    # Получение данных компаний
    print("📡 Получение данных с HH API...")
    companies_data = fetch_companies_data()

    if not companies_data:
        print("❌ Не удалось получить данные компаний")
        return False

    print(f"✅ Получено данных о {len(companies_data)} компаниях")

    # Заполнение базы данных
    print("💾 Заполнение базы данных...")
    total_vacancies = 0

    for company_data in companies_data:
        try:
            # Добавляем компанию
            company_id = db_manager.insert_company(company_data)

            if company_id:
                # Добавляем вакансии компании
                vacancies_added = 0
                for vacancy in company_data.get("vacancies", []):
                    if db_manager.insert_vacancy(vacancy, company_id):
                        vacancies_added += 1

                total_vacancies += vacancies_added
                print(f"✅ {company_data['name']}: добавлено {vacancies_added} вакансий")
            else:
                print(f"⚠️  {company_data['name']}: компания уже существует")

        except Exception as e:
            print(f"❌ Ошибка при добавлении {company_data['name']}: {e}")

    print(f"🎉 База данных заполнена! Всего вакансий: {total_vacancies}")
    return True


def db_manager_interface():
    """Интерфейс для работы с менеджером базы данных"""
    config = DBConfig.from_env()
    db_manager = DBManager(config)

    while True:
        print("\n" + "=" * 50)
        print("📊 МЕНЕДЖЕР БАЗЫ ДАННЫХ HH VACANCIES")
        print("=" * 50)
        print("1. 📈 Компании и количество вакансий")
        print("2. 📋 Все вакансии")
        print("3. 💰 Средняя зарплата")
        print("4. 🚀 Вакансии с зарплатой выше средней")
        print("5. 🔍 Поиск вакансий по ключевому слову")
        print("6. 🏠 Вернуться в главное меню")
        print("0. 🚪 Выход")
        print("=" * 50)

        choice = input("Выберите опцию (0-6): ").strip()

        if choice == "1":
            show_companies_and_vacancies_count(db_manager)
        elif choice == "2":
            show_all_vacancies(db_manager)
        elif choice == "3":
            show_avg_salary(db_manager)
        elif choice == "4":
            show_vacancies_with_higher_salary(db_manager)
        elif choice == "5":
            search_vacancies_by_keyword(db_manager)
        elif choice == "6":
            break
        elif choice == "0":
            print("👋 До свидания!")
            exit()
        else:
            print("❌ Неверный выбор. Попробуйте снова.")


def show_companies_and_vacancies_count(db_manager: DBManager):
    """Показать компании и количество вакансий"""
    print("\n🏢 КОМПАНИИ И КОЛИЧЕСТВО ВАКАНСИЙ")
    print("-" * 40)

    data = db_manager.get_companies_and_vacancies_count()
    if not data:
        print("❌ Нет данных о компаниях")
        return

    for i, (company, count) in enumerate(data, 1):
        print(f"{i:2d}. {company:<25} | {count:3d} вакансий")


def show_all_vacancies(db_manager: DBManager):
    """Показать все вакансии"""
    print("\n📋 ВСЕ ВАКАНСИИ")
    print("-" * 80)

    data = db_manager.get_all_vacancies()
    if not data:
        print("❌ Нет вакансий в базе данных")
        return

    for i, (company, title, salary, currency, url) in enumerate(data[:20], 1):
        salary_str = f"{salary:,.0f} {currency}" if salary and currency else "не указана"
        print(f"{i:2d}. {company}")
        print(f"   💼 {title}")
        print(f"   💰 {salary_str}")
        print(f"   🔗 {url}")
        print("-" * 80)

    if len(data) > 20:
        print(f"... и еще {len(data) - 20} вакансий")


def show_avg_salary(db_manager: DBManager):
    """Показать среднюю зарплату"""
    print("\n💰 СРЕДНЯЯ ЗАРПЛАТА ПО ВАКАНСИЯМ")
    print("-" * 30)

    avg_salary = db_manager.get_avg_salary()
    if avg_salary:
        print(f"Средняя зарплата: {avg_salary:,.0f} руб.")
    else:
        print("❌ Не удалось рассчитать среднюю зарплату")


def show_vacancies_with_higher_salary(db_manager: DBManager):
    """Показать вакансии с зарплатой выше средней"""
    print("\n🚀 ВАКАНСИИ С ЗАРПЛАТОЙ ВЫШЕ СРЕДНЕЙ")
    print("-" * 60)

    data = db_manager.get_vacancies_with_higher_salary()
    if not data:
        print("❌ Нет вакансий с зарплатой выше средней")
        return

    for i, (company, title, salary, currency, url) in enumerate(data[:15], 1):
        salary_str = f"{salary:,.0f} {currency}" if salary and currency else "не указана"
        print(f"{i:2d}. {company}")
        print(f"   💼 {title}")
        print(f"   💰 {salary_str}")
        print(f"   🔗 {url}")
        print("-" * 60)

    if len(data) > 15:
        print(f"... и еще {len(data) - 15} вакансий")


def search_vacancies_by_keyword(db_manager: DBManager):
    """Поиск вакансий по ключевому слову"""
    print("\n🔍 ПОИСК ВАКАНСИЙ ПО КЛЮЧЕВОМУ СЛОВУ")
    print("-" * 40)

    keyword = input("Введите ключевое слово для поиска: ").strip()
    if not keyword:
        print("❌ Необходимо ввести ключевое слово")
        return

    data = db_manager.get_vacancies_with_keyword(keyword)
    if not data:
        print(f"❌ Вакансии с ключевым словом '{keyword}' не найдены")
        return

    print(f"\n📊 Найдено вакансий: {len(data)}")
    print("-" * 60)

    for i, (company, title, salary, currency, url) in enumerate(data[:10], 1):
        salary_str = f"{salary:,.0f} {currency}" if salary and currency else "не указана"
        print(f"{i:2d}. {company}")
        print(f"   💼 {title}")
        print(f"   💰 {salary_str}")
        print(f"   🔗 {url}")
        print("-" * 60)

    if len(data) > 10:
        print(f"... и еще {len(data) - 10} вакансий")


def search_vacancies_via_api():
    """Поиск вакансий через API (оригинальная функциональность)"""
    hh_api = HeadHunterAPI()
    json_saver = JSONSaver()

    try:
        # Ввод поискового запроса
        search_query = input("Введите поисковый запрос: ").strip()
        print("\nИдет поиск вакансий...")

        # Получение вакансий
        vacancies_json = hh_api.get_vacancies(search_query)
        vacancies = Vacancy.cast_to_object_list(vacancies_json)

        # Сохранение
        for vacancy in vacancies:
            json_saver.add_vacancy(vacancy)
        print(f"Найдено и сохранено {len(vacancies)} вакансий")

        # Фильтрация
        print("\nПараметры поиска:")
        filter_words = (
            input("Введите ключевые слова для фильтрации (через пробел): ")
            .strip()
            .split()
        )
        print(f"- Ключевые слова: {filter_words}")

        try:
            salary_min = int(input("Введите минимальную зарплату: ") or 0)
            salary_max = int(input("Введите максимальную зарплату: ") or 999999999)
        except ValueError:
            print(
                "Некорректный ввод зарплаты, будут использованы значения по умолчанию"
            )
            salary_min, salary_max = 0, 999999999

        print(f"- Диапазон зарплат: {salary_min}-{salary_max}\n")

        filtered_vacancies = json_saver.get_vacancies(
            {
                "description": " ".join(filter_words),
                "salary": {"min": salary_min, "max": salary_max},
            }
        )

        # Сортировка и вывод
        sorted_vacancies = sorted(filtered_vacancies, reverse=True)
        print(
            f"\nТоп {min(5, len(sorted_vacancies))} вакансий из {len(sorted_vacancies)} найденных:\n"
        )

        if not sorted_vacancies:
            print("Нет вакансий, соответствующих критериям")
        else:
            for i, vacancy in enumerate(sorted_vacancies[:5], 1):
                salary = f"{vacancy.salary} руб." if vacancy.salary else "не указана"
                print(f"{i}. {vacancy.title}")
                print(f"   Зарплата: {salary}")
                print(f"   Ссылка: {vacancy.url}")
                print(f"   Описание: {vacancy.description[:200]}...\n")

    except Exception as e:
        print(f"\nОшибка: {e}")
    finally:
        print("\nПоиск завершен")


def user_interaction():
    """Функция взаимодействия с пользователем через консоль"""
    print("Программа для поиска вакансий на HeadHunter")
    print("-------------------------------------------\n")

    # Настройка и заполнение БД (только при первом запуске)
    config = DBConfig.from_env()
    db_manager = DBManager(config)

    # Сначала проверяем существование таблиц
    try:
        with db_manager.get_connection() as conn:
            with conn.cursor() as cursor:
                # Проверяем существование таблицы vacancies
                cursor.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_schema = 'public' 
                        AND table_name = 'vacancies'
                    )
                """)
                vacancies_exists = cursor.fetchone()[0]

                if not vacancies_exists:
                    print("🔄 Таблицы не существуют, создаем базу данных...")
                    if not setup_database():
                        print("❌ Не удалось создать базу данных")
                        return

                    # Заполняем данными
                    print("📡 Заполняем базу данных данными...")
                    if not setup_and_fill_database():
                        print("❌ Не удалось заполнить базу данных")
                        return
                else:
                    # Проверяем есть ли данные
                    cursor.execute("SELECT COUNT(*) FROM vacancies")
                    vacancy_count = cursor.fetchone()[0]

                    if vacancy_count == 0:
                        print("🔄 База данных пустая, заполняем данными...")
                        if not setup_and_fill_database():
                            return
                    else:
                        print(f"✅ База данных уже содержит {vacancy_count} вакансий")

    except Exception as e:
        print(f"❌ Ошибка при проверке базы данных: {e}")
        print("🔄 Пытаемся создать базу данных заново...")
        if not setup_database() or not setup_and_fill_database():
            print("❌ Не удалось инициализировать базу данных")
            return

    while True:
        print("\n" + "=" * 50)
        print("🎯 ГЛАВНОЕ МЕНЮ")
        print("=" * 50)
        print("1. 🔍 Поиск вакансий через HH API")
        print("2. 📊 Управление базой данных")
        print("0. 🚪 Выход")
        print("=" * 50)

        choice = input("Выберите опцию (0-2): ").strip()

        if choice == "1":
            search_vacancies_via_api()
        elif choice == "2":
            db_manager_interface()
        elif choice == "0":
            print("👋 До свидания!")
            break
        else:
            print("❌ Неверный выбор. Попробуйте снова.")


if __name__ == "__main__":
    user_interaction()
