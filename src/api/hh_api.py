import os
from abc import ABC, abstractmethod
import requests


class JobAPI(ABC):
    """Абстрактный класс для работы с API вакансий"""

    @abstractmethod
    def connect(self):
        """Метод для подключения к API"""
        pass

    @abstractmethod
    def get_vacancies(self, keyword: str) -> list[dict]:
        """Метод для получения вакансий по ключевому слову"""
        pass


class HeadHunterAPI(JobAPI):
    """Класс для работы с API HeadHunter"""

    def __init__(self):
        self.__base_url = "https://api.hh.ru/vacancies"
        self.__headers = {"User-Agent": "HH-User-Agent"}
        self.__params = {"text": "", "page": 0, "per_page": 100}

    def connect(self) -> bool:
        """Реализация абстрактного метода подключения к API"""
        try:
            response = requests.get(self.__base_url, headers=self.__headers)
            return response.status_code == 200
        except requests.RequestException:
            return False

    def get_vacancies(self, keyword: str) -> list[dict]:
        """
        Получение вакансий по ключевому слову
        :param keyword: Ключевое слово для поиска
        :return: Список вакансий в формате JSON
        """
        if not self.connect():
            raise ConnectionError("Не удалось подключиться к API HeadHunter")

        self.__params["text"] = keyword
        self.__params["page"] = 0
        vacancies = []

        max_pages = 1 if os.getenv("TEST_ENV") else 20

        while self.__params.get("page") < max_pages:
            try:
                response = requests.get(
                    self.__base_url, headers=self.__headers, params=self.__params
                )
                response.raise_for_status()

                data = response.json()
                vacancies.extend(data.get("items", []))

                if data.get("pages", 0) <= self.__params["page"] + 1:
                    break

                self.__params["page"] += 1

            except requests.RequestException as e:
                print(f"Ошибка при запросе страницы {self.__params['page']}: {e}")
                break

        return vacancies
