import sqlite3
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, HTTPException, status
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from projects.url_shortener.src.schemas import ShortenRequest, ShortenResponse
from projects.url_shortener.src.shortener import (
    DB_PATH,
    get_target_url,
    init_db,
    save_url,
)

STATIC_DIR = Path(__file__).resolve().parent.parent / "static"


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="QuickLink URL Shortener",
    description="FastAPI URL shortener with analytics and static dashboard",
    version="1.0.0",
    lifespan=lifespan,
)


@app.post("/urls", response_model=ShortenResponse, status_code=status.HTTP_201_CREATED)
async def shorten_url(payload: ShortenRequest) -> ShortenResponse:
    target = str(payload.url)
    code = save_url(target_url=target)
    return ShortenResponse(short_code=code, target_url=target)


@app.get("/urls")
async def list_urls() -> list[dict]:
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT short_code, target_url, clicks FROM urls ORDER BY id DESC"
        ).fetchall()
        return [dict(r) for r in rows]


@app.get("/r/{short_code}")
async def redirect_short_code(short_code: str):
    target = get_target_url(code=short_code)
    if target is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Short code '{short_code}' not found.",
        )
    return RedirectResponse(
        url=target,
        status_code=status.HTTP_307_TEMPORARY_REDIRECT,
    )


app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")