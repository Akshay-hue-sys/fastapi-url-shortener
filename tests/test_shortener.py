from pathlib import Path

import pytest
from pydantic import ValidationError

from src.schemas import ShortenRequest
from src.shortener import generate_short_code, get_target_url, save_url


def test_shorten_request_accepts_valid_https() -> None:
    req = ShortenRequest(url="https://docs.pydantic.dev")
    assert str(req.url) == "https://docs.pydantic.dev/"


def test_shorten_request_rejects_insecure_http() -> None:
    with pytest.raises(ValidationError):
        ShortenRequest(url="http://insecure-site.com")


def test_generate_short_code_length() -> None:
    code = generate_short_code(length=6)
    assert len(code) == 6
    assert code.isalnum()


def test_save_and_retrieve_url_sqlite(tmp_path: Path) -> None:
    test_db = tmp_path / "test_urls.db"
    target = "https://fastapi.tiangolo.com/"

    code = save_url(target, db_path=test_db)

    assert get_target_url(code, db_path=test_db) == target
    assert get_target_url("nonexistent_code", db_path=test_db) is None