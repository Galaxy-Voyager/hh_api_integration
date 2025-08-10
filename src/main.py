from src.api.hh_api import HeadHunterAPI
from src.models.vacancy import Vacancy
from src.storage.json_saver import JSONSaver


def user_interaction():
    """Функция взаимодействия с пользователем через консоль"""
    print("Программа для поиска вакансий на HeadHunter")
    print("-------------------------------------------\n")

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
        print("\nРабота программы завершена")


if __name__ == "__main__":
    user_interaction()
