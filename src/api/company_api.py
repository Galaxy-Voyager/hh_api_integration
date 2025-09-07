import requests
from typing import List, Dict, Any
import time
from dataclasses import dataclass
import os


@dataclass
class Company:
    """Модель компании"""
    hh_id: int
    name: str
    url: str
    description: str
    vacancies_url: str


class HHCompanyAPI:
    """Класс для работы с API компаний HeadHunter"""

    def __init__(self):
        self.base_url = "https://api.hh.ru"
        self.headers = {"User-Agent": "HH-Company-API/1.0"}
        self.companies = self._get_predefined_companies()

    def _get_predefined_companies(self) -> List[Dict[str, Any]]:
        """Список предопределенных компаний для сбора данных"""
        return [
            {"id": 1740, "name": "Яндекс"},  # Яндекс
            {"id": 1122462, "name": "Сбер"},  # Сбер
            {"id": 15478, "name": "VK"},  # VK
            {"id": 2180, "name": "Ozon"},  # Ozon
            {"id": 2748, "name": "Ростелеком"},  # Ростелеком
            {"id": 3529, "name": "Тинькофф"},  # Тинькофф
            {"id": 4181, "name": "Билайн"},  # Билайн
            {"id": 907345, "name": "Альфа-Банк"},  # Альфа-Банк
            {"id": 4934, "name": "МТС"},  # МТС
            {"id": 1057, "name": "Kaspersky"},  # Kaspersky
            {"id": 1373, "name": "Лаборатория Касперского"},  # Лаборатория Касперского
            {"id": 87021, "name": "Wildberries"},  # Wildberries
            {"id": 157944, "name": "2GIS"},  # 2GIS
            {"id": 6093775, "name": "Yandex Praktikum"},  # Яндекс Практикум
            {"id": 2324020, "name": "Skyeng"}  # Skyeng
        ]

    def get_company_info(self, company_id: int) -> Dict[str, Any]:
        """Получение информации о компании по ID"""
        try:
            url = f"{self.base_url}/employers/{company_id}"
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()

            data = response.json()
            return {
                "id": data.get("id"),
                "name": data.get("name"),
                "alternate_url": data.get("alternate_url"),
                "description": self._clean_html(data.get("description", "")),
                "vacancies_url": data.get("vacancies_url")
            }

        except requests.RequestException as e:
            print(f"Ошибка при получении данных компании {company_id}: {e}")
            return {}
        except Exception as e:
            print(f"Неожиданная ошибка для компании {company_id}: {e}")
            return {}

    def get_company_vacancies(self, company_id: int, per_page: int = 100) -> List[Dict[str, Any]]:
        """Получение вакансий компании"""
        vacancies = []
        page = 0

        try:
            while True:
                url = f"{self.base_url}/vacancies"
                params = {
                    "employer_id": company_id,
                    "per_page": per_page,
                    "page": page,
                    "only_with_salary": True  # Только вакансии с зарплатой
                }

                response = requests.get(url, headers=self.headers, params=params)
                response.raise_for_status()

                data = response.json()
                vacancies.extend(data.get("items", []))

                # Проверяем есть ли следующая страница
                pages = data.get("pages", 0)
                if page >= pages - 1 or page >= 4:  # Ограничиваем 5 страницами
                    break

                page += 1
                time.sleep(0.1)  # Задержка чтобы не превысить лимиты API

        except requests.RequestException as e:
            print(f"Ошибка при получении вакансий компании {company_id}: {e}")
        except Exception as e:
            print(f"Неожиданная ошибка при получении вакансий: {e}")

        return vacancies

    def get_all_companies_data(self) -> List[Dict[str, Any]]:
        """Получение данных всех компаний"""
        companies_data = []

        for company in self.companies:
            print(f"Получение данных компании: {company['name']}...")

            company_info = self.get_company_info(company["id"])
            if company_info:
                vacancies = self.get_company_vacancies(company["id"])
                company_info["vacancies"] = vacancies
                companies_data.append(company_info)

                print(f"✅ {company['name']}: {len(vacancies)} вакансий")
            else:
                print(f"❌ Не удалось получить данные для {company['name']}")

            time.sleep(0.5)  # Задержка между запросами

        return companies_data

    def _clean_html(self, text: str) -> str:
        """Очистка HTML тегов из текста"""
        import re
        if not text:
            return ""
        clean = re.compile('<.*?>')
        return re.sub(clean, '', text)

    def get_companies_with_vacancies(self, min_vacancies: int = 5) -> List[Dict[str, Any]]:
        """Получение компаний с минимальным количеством вакансий"""
        all_data = self.get_all_companies_data()
        return [company for company in all_data if len(company.get("vacancies", [])) >= min_vacancies]


# Утилитарная функция для использования в основном коде
def fetch_companies_data() -> List[Dict[str, Any]]:
    """Получение данных компаний с вакансиями"""
    api = HHCompanyAPI()
    return api.get_companies_with_vacancies(min_vacancies=3)
