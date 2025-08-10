from unittest.mock import MagicMock, patch

import pytest
import requests

from src.api.hh_api import HeadHunterAPI
from src.models.vacancy import Vacancy
from src.storage.json_saver import JSONSaver


@pytest.fixture
def sample_vacancy():
    return Vacancy("Python Dev", "http://example.com", 100000, "Description")


@pytest.fixture
def json_saver(tmp_path):
    test_file = tmp_path / "test_vacancies.json"
    return JSONSaver(test_file)


def test_vacancy_creation(sample_vacancy):
    assert sample_vacancy.title == "Python Dev"
    assert sample_vacancy.salary == 100000


def test_vacancy_comparison():
    v1 = Vacancy("A", "http://a.com", 100000, "Desc")
    v2 = Vacancy("B", "http://b.com", 150000, "Desc")
    assert v1 < v2
    assert v2 > v1


def test_vacancy_without_salary():
    v = Vacancy("Intern", "http://example.com", None, "No salary")
    assert v.salary is None


def test_json_saver_add_vacancy(json_saver, sample_vacancy):
    json_saver.add_vacancy(sample_vacancy)
    vacancies = json_saver.get_vacancies({})
    assert len(vacancies) == 1
    assert vacancies[0].title == "Python Dev"


def test_json_saver_delete_vacancy(json_saver, sample_vacancy):
    json_saver.add_vacancy(sample_vacancy)
    json_saver.delete_vacancy(sample_vacancy)
    vacancies = json_saver.get_vacancies({})
    assert len(vacancies) == 0


def test_hh_api_get_vacancies():
    with patch("requests.get") as mock_get:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "items": [
                {
                    "name": "Python Dev",
                    "alternate_url": "http://example.com",
                    "salary": {"from": 100000},
                    "snippet": {"requirement": "Exp"},
                }
            ],
            "pages": 1,
            "per_page": 1,
        }
        mock_get.return_value = mock_response

        hh_api = HeadHunterAPI()
        hh_api._HeadHunterAPI__params["per_page"] = 1
        hh_api._HeadHunterAPI__params["page"] = 0

        result = hh_api.get_vacancies("Python")
        assert len(result) == 1
        assert result[0]["name"] == "Python Dev"


def test_hh_api_connection_error():
    with patch("requests.get") as mock_get:
        mock_get.return_value.status_code = 500

        hh_api = HeadHunterAPI()
        with pytest.raises(ConnectionError):
            hh_api.get_vacancies("Python")


def test_hh_api_request_exception():
    with patch("requests.get") as mock_get:
        mock_get.side_effect = requests.RequestException("Connection error")
        hh_api = HeadHunterAPI()
        with pytest.raises(ConnectionError):
            hh_api.get_vacancies("Python")


def test_vacancy_str_representation():
    v = Vacancy("Dev", "http://test.com", 100000, "Test")
    assert "Dev" in str(v)
    assert "100000" in str(v)


def test_vacancy_no_salary_comparison():
    v1 = Vacancy("A", "http://a.com", None, "Desc")
    v2 = Vacancy("B", "http://b.com", 50000, "Desc")
    assert v1 < v2


def test_json_saver_invalid_file(tmp_path):
    invalid_file = tmp_path / "invalid.json"
    invalid_file.write_text("{invalid json}")
    saver = JSONSaver(invalid_file)
    assert saver.get_vacancies({}) == []


def test_hh_api_empty_response():
    with patch("requests.get") as mock_get:
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {"items": []}
        hh_api = HeadHunterAPI()
        assert len(hh_api.get_vacancies("Python")) == 0


def test_hh_api_pagination():
    with patch("requests.get") as mock_get:
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.side_effect = [
            {"items": [{"name": "Page1"}], "pages": 2},
            {"items": [{"name": "Page2"}], "pages": 2},
        ]
        hh_api = HeadHunterAPI()
        hh_api._HeadHunterAPI__params["per_page"] = 1
        assert len(hh_api.get_vacancies("Python")) == 2


def test_vacancy_equality():
    v1 = Vacancy("A", "http://a.com", 100000, "Desc")
    v2 = Vacancy("A", "http://a.com", 100000, "Desc")
    assert v1 == v2


def test_vacancy_validation():
    # Пустое название
    with pytest.raises(ValueError, match="Название вакансии обязательно"):
        Vacancy("", "http://test.com", 100000, "Desc")

    # Невалидный URL
    with pytest.raises(ValueError, match="URL должен быть валидной ссылкой"):
        Vacancy("Test", "invalid_url", 100000, "Desc")

    # Некорректная зарплата
    with pytest.raises(ValueError):
        Vacancy("Test", "http://test.com", "not_number", "Desc")


def test_vacancy_from_dict():
    data = {
        "name": "Python Dev",
        "alternate_url": "http://test.com",
        "salary": {"from": 100000},
        "snippet": {"requirement": "Exp"},
    }
    vacancy = Vacancy.cast_to_object_list([data])[0]
    assert vacancy.title == "Python Dev"
    assert vacancy.salary == 100000


def test_json_saver_duplicates(json_saver, sample_vacancy):
    json_saver.add_vacancy(sample_vacancy)
    json_saver.add_vacancy(sample_vacancy)  # Дубликат
    assert len(json_saver.get_vacancies({})) == 1


def test_json_saver_complex_filter(json_saver):
    v1 = Vacancy("Python", "http://1.com", 100000, "Django Flask")
    v2 = Vacancy("Java", "http://2.com", 150000, "Spring")
    json_saver.add_vacancy(v1)
    json_saver.add_vacancy(v2)

    result = json_saver.get_vacancies(
        {"description": "django", "salary": {"min": 50000, "max": 120000}}
    )
    assert len(result) == 1
    assert result[0].title == "Python"


def test_integration_flow(tmp_path):
    # 1. Получаем вакансии
    hh_api = HeadHunterAPI()
    with patch.object(hh_api, "get_vacancies") as mock_get:
        mock_get.return_value = [
            {
                "name": "Python",
                "alternate_url": "http://test.com",
                "salary": {"from": 100000},
                "snippet": {"requirement": "Django"},
            }
        ]
        vacancies = hh_api.get_vacancies("Python")

    # 2. Сохраняем
    saver = JSONSaver(tmp_path / "test.json")
    for v in Vacancy.cast_to_object_list(vacancies):
        saver.add_vacancy(v)

    # 3. Проверяем
    assert len(saver.get_vacancies({"description": "django"})) == 1


def test_hh_api_invalid_response():
    with patch("requests.get") as mock_get:
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {
            "invalid": "data"
        }  # Нет ключа 'items'
        hh_api = HeadHunterAPI()
        assert len(hh_api.get_vacancies("Python")) == 0  # Должен вернуть пустой список


def test_vacancy_salary_parsing():
    # Тест парсинга зарплаты из API
    data = {
        "name": "Dev",
        "alternate_url": "http://test.com",
        "salary": {"from": None, "to": 200000},  # Только 'to'
        "snippet": {"requirement": ""},
    }
    vacancy = Vacancy.cast_to_object_list([data])[0]
    assert vacancy.salary == 200000


def test_json_saver_file_permissions(monkeypatch):
    # Мокаем все файловые операции
    def mock_open(*args, **kwargs):
        if "w" in args[1]:
            raise PermissionError("Permission denied")
        return MagicMock()

    monkeypatch.setattr("builtins.open", mock_open)
    monkeypatch.setattr("json.load", lambda *_: [])

    saver = JSONSaver("test.json")
    with pytest.raises(PermissionError):
        saver.add_vacancy(Vacancy("Test", "https://example.com", 100000, "Desc"))


def test_main_flow(monkeypatch, tmp_path):
    # Мокаем ввод
    inputs = ["Python", "5", "", "0", "200000"]
    monkeypatch.setattr("builtins.input", lambda _: inputs.pop(0))

    # Мокаем API
    with patch("src.api.hh_api.HeadHunterAPI.get_vacancies") as mock_get:
        mock_get.return_value = [
            {
                "name": "Python Dev",
                "alternate_url": "http://test.com",
                "salary": {"from": 100000},
                "snippet": {"requirement": "Django"},
            }
        ]

        # Мокаем JSONSaver
        with patch("src.storage.json_saver.JSONSaver") as mock_saver:
            mock_saver.return_value = MagicMock()

            # Запускаем main
            from src.main import user_interaction

            user_interaction()

            # Проверяем вызовы
            assert mock_saver.return_value.add_vacancy.called


def test_main_flow_empty_result(monkeypatch, capsys):
    inputs = ["Python", "5", "", "0", "200000"]
    monkeypatch.setattr("builtins.input", lambda _: inputs.pop(0))

    with patch("src.api.hh_api.HeadHunterAPI.get_vacancies", return_value=[]):
        from src.main import user_interaction

        user_interaction()

        captured = capsys.readouterr()
        assert "Нет вакансий" in captured.out


def test_json_saver_read_only_file(tmp_path):
    test_file = tmp_path / "read_only.json"
    test_file.write_text("[]")
    test_file.chmod(0o444)

    saver = JSONSaver(test_file)
    assert saver.get_vacancies({}) == []
