import os

from fastapi.testclient import TestClient

os.environ["APP_ENV"] = "test"
os.environ["DATABASE_URL"] = "sqlite+pysqlite:///./test_pages.db"
os.environ["ADMIN_USERNAME"] = "admin"
os.environ["ADMIN_PASSWORD"] = "admin"

from app.main import app  # noqa: E402


def test_home_page_loads() -> None:
    with TestClient(app) as client:
        response = client.get("/")
    assert response.status_code == 200
    assert "Bill Transparency Tracker" in response.text


def test_about_page_loads() -> None:
    with TestClient(app) as client:
        response = client.get("/about")
    assert response.status_code == 200
    assert "Methodology" in response.text


def test_search_page_loads_without_query() -> None:
    with TestClient(app) as client:
        response = client.get("/search")
    assert response.status_code == 200
    assert "Search Bills" in response.text


def test_404_page() -> None:
    with TestClient(app) as client:
        response = client.get("/not-a-real-path")
    assert response.status_code == 404
    assert "404" in response.text
