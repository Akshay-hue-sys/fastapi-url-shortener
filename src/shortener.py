import secrets
import sqlite3
import string
from pathlib import Path

ALPHABET = string.ascii_letters + string.digits
DB_PATH = Path("urls.db")


def init_db(db_path: Path = DB_PATH) -> None:
    with sqlite3.connect(db_path) as conn:
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS urls (
                code TEXT PRIMARY KEY,
                target_url TEXT NOT NULL
            );
            """
        )


def generate_short_code(length: int = 6) -> str:
    return "".join(secrets.choice(ALPHABET) for _ in range(length))


def save_url(target_url: str, db_path: Path = DB_PATH) -> str:
    init_db(db_path)
    with sqlite3.connect(db_path) as conn:
        while True:
            code = generate_short_code()
            cursor = conn.execute("SELECT 1 FROM urls WHERE code = ?", (code,))
            if cursor.fetchone() is None:
                conn.execute(
                    "INSERT INTO urls (code, target_url) VALUES (?, ?)",
                    (code, target_url),
                )
                conn.commit()
                return code


def get_target_url(code: str, db_path: Path = DB_PATH) -> str | None:
    init_db(db_path)
    with sqlite3.connect(db_path) as conn:
        cursor = conn.execute("SELECT target_url FROM urls WHERE code = ?", (code,))
        row = cursor.fetchone()
        if row is not None:
            return str(row[0])
        return None