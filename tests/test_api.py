from fastapi.testclient import TestClient

from src.app import app

client = TestClient(app)


def test_api_root_home_page() -> None:
    response = client.get("/")
    assert response.status_code == 200
    assert "URL Shortener Service" in response.text


def test_api_shorten_url_success() -> None:
    payload = {"url": "https://fastapi.tiangolo.com"}
    response = client.post("/shorten", json=payload)

    assert response.status_code == 201
    data = response.json()
    assert "short_code" in data
    assert data["target_url"] == "https://fastapi.tiangolo.com/"


def test_api_shorten_url_rejects_insecure_http() -> None:
    payload = {"url": "http://insecure-site.com"}
    response = client.post("/shorten", json=payload)

    assert response.status_code == 422


def test_api_redirect_success() -> None:
    create_resp = client.post("/shorten", json={"url": "https://docs.pydantic.dev"})
    code = create_resp.json()["short_code"]

    redirect_resp = client.get(f"/{code}", follow_redirects=False)
    assert redirect_resp.status_code == 307
    assert redirect_resp.headers["location"] == "https://docs.pydantic.dev/"


def test_api_redirect_not_found() -> None:
    response = client.get("/definitelymissingcode123", follow_redirects=False)
    assert response.status_code == 404
    assert response.json() == {"detail": "Short code not found"}