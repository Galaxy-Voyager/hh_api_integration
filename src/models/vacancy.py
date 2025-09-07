from dataclasses import dataclass
from typing import Optional


@dataclass
class Vacancy:
    """Класс для представления вакансии"""

    __slots__ = ("title", "url", "salary", "description")

    title: str  # Название вакансии
    url: str  # Ссылка на вакансию
    salary: Optional[int]  # Зарплата (может быть None)
    description: str  # Описание вакансии

    def __post_init__(self):
        """Валидация данных при создании вакансии"""
        if not isinstance(self.title, str) or not self.title.strip():
            raise ValueError("Название вакансии обязательно")
        if not isinstance(self.url, str) or not self.url.startswith("http"):
            raise ValueError("URL должен быть валидной ссылкой")
        self.__validate_salary()

    def __validate_salary(self):
        if self.salary is not None:
            if not isinstance(self.salary, (int, float)):
                raise ValueError("Зарплата должна быть числом")
            if self.salary < 0:
                raise ValueError("Зарплата не может быть отрицательной")

    def __validate_url(self):
        """Проверка корректности URL"""
        if not isinstance(self.url, str) or not self.url.startswith(
            ("http://", "https://")
        ):
            raise ValueError("URL должен начинаться с http:// или https://")

    def __lt__(self, other) -> bool:
        """Сравнение вакансий по зарплате (меньше)"""
        if self.salary is None:
            return True
        if other.salary is None:
            return False
        return self.salary < other.salary

    def __gt__(self, other) -> bool:
        """Сравнение вакансий по зарплате (больше)"""
        if self.salary is None:
            return False
        if other.salary is None:
            return True
        return self.salary > other.salary

    @classmethod
    def cast_to_object_list(cls, vacancies: list[dict]) -> list["Vacancy"]:
        """
        Преобразование списка словарей в список объектов Vacancy
        :param vacancies: Список вакансий в формате JSON
        :return: Список объектов Vacancy
        """
        result = []
        for vacancy in vacancies:
            salary = cls.__parse_salary(vacancy.get("salary"))
            result.append(
                cls(
                    title=vacancy.get("name", ""),
                    url=vacancy.get("alternate_url", ""),
                    salary=salary,
                    description=cls.clean_html(
                        vacancy.get("snippet", {}).get("requirement", "")
                    ),
                )
            )
        return result

    @staticmethod
    def __parse_salary(salary_data: Optional[dict]) -> Optional[int]:
        """Приватный метод для парсинга зарплаты из API"""
        if not salary_data:
            return None

        salary_from = salary_data.get("from")
        salary_to = salary_data.get("to")

        if salary_from and salary_to:
            return (salary_from + salary_to) // 2
        return salary_from or salary_to

    @staticmethod
    def clean_html(raw_html: str) -> str:
        """Удаление HTML-тегов из описания"""
        if not raw_html:
            return ""
        import re

        clean_text = re.sub(r"<[^>]+>", "", raw_html)
        return clean_text.strip()
