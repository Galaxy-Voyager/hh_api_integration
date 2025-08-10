import json
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List

from ..models.vacancy import Vacancy


class Storage(ABC):
    """Абстрактный класс для работы с хранилищем вакансий"""

    @abstractmethod
    def add_vacancy(self, vacancy: Vacancy) -> None:
        """Добавление вакансии в хранилище"""
        pass

    @abstractmethod
    def get_vacancies(self, criteria: dict) -> List[Vacancy]:
        """Получение вакансий по критериям"""
        pass

    @abstractmethod
    def delete_vacancy(self, vacancy: Vacancy) -> None:
        """Удаление вакансии из хранилища"""
        pass


class JSONSaver(Storage):
    """Класс для сохранения вакансий в JSON-файл"""

    def __init__(self, file_name: str = "vacancies.json"):
        self.__file_path = Path("data") / file_name
        self.__file_path.parent.mkdir(exist_ok=True)

    def __read_file(self) -> List[dict]:
        """Приватный метод для чтения файла"""
        try:
            if not self.__file_path.exists():
                return []

            with open(self.__file_path, "r", encoding="utf-8") as file:
                content = file.read()
                if not content.strip():
                    return []
                return json.loads(content)
        except (json.JSONDecodeError, IOError) as e:
            print(f"Ошибка чтения файла: {e}")
            return []

    def __write_file(self, data: List[dict]) -> None:
        """Приватный метод для записи в файл"""
        try:
            with open(self.__file_path, "w", encoding="utf-8") as file:
                json.dump(data, file, ensure_ascii=False, indent=2)
        except (IOError, PermissionError) as e:
            print(f"Ошибка записи в файл: {e}")
            raise

    def add_vacancy(self, vacancy: Vacancy) -> None:
        """Добавление вакансии в JSON-файл"""
        try:
            vacancies = self.__read_file()
            if not isinstance(vacancies, list):
                vacancies = []

            # Проверка на дубликаты
            if not any(
                isinstance(v, dict) and v.get("url") == vacancy.url for v in vacancies
            ):
                vacancies.append(
                    {
                        "title": vacancy.title,
                        "url": vacancy.url,
                        "salary": vacancy.salary,
                        "description": vacancy.description,
                    }
                )
                self.__write_file(vacancies)
        except Exception as e:
            print(f"Ошибка при добавлении вакансии: {e}")
            raise

    def get_vacancies(self, criteria: dict) -> List[Vacancy]:
        """Получение вакансий по критериям"""
        vacancies = self.__read_file()
        result = []

        for vacancy_data in vacancies:
            if not isinstance(vacancy_data, dict):
                continue

            try:
                match = True
                salary = vacancy_data.get("salary")

                # Фильтр по описанию
                if "description" in criteria and criteria["description"]:
                    description = str(vacancy_data.get("description", "")).lower()
                    search_words = str(criteria["description"]).lower().split()
                    if search_words and not all(
                        word in description for word in search_words
                    ):
                        match = False

                # Фильтр по зарплате
                if match and "salary" in criteria:
                    if salary is None:
                        match = False
                    else:
                        salary_min = criteria["salary"]["min"]
                        salary_max = criteria["salary"]["max"]
                        if not (salary_min <= salary <= salary_max):
                            match = False

                if match:
                    result.append(
                        Vacancy(
                            title=str(vacancy_data.get("title", "")),
                            url=str(vacancy_data.get("url", "")),
                            salary=salary,
                            description=str(vacancy_data.get("description", "")),
                        )
                    )

            except Exception as e:
                print(f"Ошибка обработки вакансии: {e}")
                continue

        return result

    def delete_vacancy(self, vacancy: Vacancy) -> None:
        """Удаление вакансии из JSON-файла"""
        vacancies = self.__read_file()
        vacancies = [v for v in vacancies if v["url"] != vacancy.url]
        self.__write_file(vacancies)
