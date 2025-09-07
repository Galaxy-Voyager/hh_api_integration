from src.api.company_api import HHCompanyAPI


def test_company_api():
    """Тестирование API компаний"""
    print("🧪 Тестирование HH Company API...")

    api = HHCompanyAPI()

    # Тестируем получение данных одной компании
    test_company_id = 1740  # Яндекс
    company_info = api.get_company_info(test_company_id)

    if company_info:
        print(f"✅ Данные компании получены: {company_info['name']}")
        print(f"   URL: {company_info['alternate_url']}")
        print(f"   Описание: {company_info['description'][:100]}...")
    else:
        print("❌ Не удалось получить данные компании")
        return

    # Тестируем получение вакансий
    vacancies = api.get_company_vacancies(test_company_id, per_page=5)
    print(f"✅ Получено вакансий: {len(vacancies)}")

    if vacancies:
        for i, vac in enumerate(vacancies[:3], 1):
            print(f"   {i}. {vac.get('name')} - {vac.get('salary', {}).get('from')} руб.")


if __name__ == "__main__":
    test_company_api()
