# FastAPI Persistent URL Shortener

A high-performance, secure URL shortener service built with **FastAPI**, **Pydantic v2**, and **SQLite (WAL mode)**. It features cryptographic token generation, automated testing via `pytest`, and local TLS termination using `mkcert`.

## Architecture Overview

```
                      +---------------------------------------+
                      |               Client                  |
                      |    (Browser / curl / Swagger UI)      |
                      +-------------------+-------------------+
                                          |
                                          | HTTPS / HTTP
                                          v
                      +---------------------------------------+
                      |         Uvicorn ASGI Server           |
                      |   (Optional TLS Termination via PEM)  |
                      +-------------------+-------------------+
                                          |
                                          v
                      +---------------------------------------+
                      |          FastAPI Routing              |
                      |   - GET  /         (HTML Home)        |
                      |   - POST /shorten  (Validate & Store) |
                      |   - GET  /{code}   (307 Redirect)     |
                      +---------+-------------------+---------+
                                |                   |
               Pydantic Schema  |                   | SQL Queries
                  Validation    v                   v
                     +--------------+       +---------------+
                     | ShortenModel |       | SQLite Engine |
                     | (HTTPS-only) |       |   (urls.db)   |
                     +--------------+       |  WAL Journal  |
                                            +---------------+
```

## Key Features

* **Pydantic v2 Schema Validation:** Restricts input to well-formed URLs and strictly enforces `https://` schemes at the API boundary to prevent insecure redirects.
* **Cryptographic Collision Resistance:** Generates 6-character Base62 tokens (`[a-zA-Z0-9]`) using Python's `secrets` module (C-level cryptographic pseudo-random number generator) rather than predictable pseudo-random engines.
* **Embedded ACID Persistence:** Persists data to disk using Python's standard-library `sqlite3` configured with **Write-Ahead Logging (`PRAGMA journal_mode=WAL;`)** for high-concurrency read throughput without database locks.
* **Decoupled Automated Testing:** 9 tests covering root endpoints, input sanitization, 422 rejections, 307 temporary redirects, and database queries using isolated temporary directories (`tmp_path`).
* **Local TLS / HTTPS Support:** Fully compatible with local zero-config Certificate Authorities (`mkcert`) for browser-trusted development over HTTPS.

## Directory Structure

Below is the complete local directory layout, including runtime state and cryptographic files. Files marked with `[git-ignored]` are kept strictly on your local disk and excluded from version control via `.gitignore`.

```
projects/url_shortener/
├── .gitignore                # Rules ignoring .pem, .db, and cache files
├── pyproject.toml            # Project dependencies and tool configurations
├── README.md                 # Project documentation
│
├── localhost+1.pem           # [git-ignored] Local public TLS certificate
├── localhost+1-key.pem       # [git-ignored] Local private decryption key
│
├── urls.db                   # [git-ignored] SQLite database file (B-tree storage)
├── urls.db-wal               # [git-ignored] SQLite Write-Ahead Log journal
├── urls.db-shm               # [git-ignored] SQLite shared-memory index file
│
├── src/
│   ├── __init__.py
│   ├── app.py                # FastAPI routes, lifecycle, and redirect handler
│   ├── schemas.py            # Pydantic v2 request & response validation schemas
│   └── shortener.py          # SQLite connection, WAL init, and Base62 token logic
│
└── tests/
    ├── __init__.py
    ├── test_api.py           # End-to-end API integration tests via TestClient
    └── test_shortener.py     # Unit tests using isolated temporary database fixtures
```

### Git-Ignored File Details

| File Pattern | Category | Purpose & Why It Is Ignored |
| :--- | :--- | :--- |
| `*.pem` | Cryptographic Secrets | Contains your local private key (`localhost+1-key.pem`) and certificate. Private keys must never be committed to source control. |
| `urls.db` | Runtime State | The binary SQLite relational database storing URL mappings. Committing it would pollute Git history and overwrite local test states. |
| `urls.db-wal` | Storage Engine Journal | SQLite Write-Ahead Log storing uncommitted transactions before checkpointing into `urls.db`. |
| `urls.db-shm` | Storage Engine Index | SQLite shared-memory index file used for coordinating concurrent readers in WAL mode. |

---

## Installation & Setup

### Prerequisites

* Python 3.12+ (managed with `uv`)
* macOS, Linux, or WSL
* Homebrew (optional, for local HTTPS via `mkcert`)

### 1. Install Dependencies

From the project root, synchronize dependencies using `uv`:

```bash
uv sync
```

Or install the required packages directly:

```bash
uv add fastapi "uvicorn[standard]" pydantic
uv add --dev pytest ruff httpx
```

---

## Running the Application

### Mode A: Standard Local Development (HTTP)

Run the server on your local loopback interface:

```bash
uv run uvicorn src.app:app --reload --port 8000
```

* **Home Page:** `http://127.0.0.1:8000/`
* **Interactive Swagger UI:** `http://127.0.0.1:8000/docs`

### Mode B: Secure Context Development (HTTPS via `mkcert`)

To run the application with a trusted browser padlock:

1. Install and initialize `mkcert`:
   ```bash
   brew install mkcert
   mkcert -install
   mkcert localhost 127.0.0.1
   ```
   *(This produces `localhost+1.pem` and `localhost+1-key.pem` in your working directory.)*

2. Launch Uvicorn with TLS termination enabled:
   ```bash
   uv run uvicorn src.app:app --reload --port 8000 --ssl-certfile localhost+1.pem --ssl-keyfile localhost+1-key.pem
   ```

* **Secure Swagger UI:** `https://localhost:8000/docs`

---

## API Reference

### 1. Shorten a URL

* **Endpoint:** `POST /shorten`
* **Headers:** `Content-Type: application/json`
* **Request Body:**
  ```json
  {
    "url": "https://fastapi.tiangolo.com"
  }
  ```
* **Success Response (`201 Created`):**
  ```json
  {
    "short_code": "07nhUS",
    "target_url": "https://fastapi.tiangolo.com/"
  }
  ```
* **Error Response (`422 Unprocessable Entity`):**
  Occurs if the URL is invalid or uses an unencrypted scheme (e.g., `http://`).

### 2. Follow Short URL

* **Endpoint:** `GET /{code}`
* **Behavior:** Returns an HTTP `307 Temporary Redirect` with the `Location` header set to the stored destination URL.
* **Error Response (`404 Not Found`):**
  ```json
  {
    "detail": "Short code not found"
  }
  ```

---

## Verification & Testing

Execute the automated test suite across unit and integration tests:

```bash
uv run pytest -v
```

Execute static analysis and lint checks:

```bash
uv run ruff check .
```

---

## Security Model

1. **Zero Secret Leakage:** Local private keys (`*.pem`) and SQLite database files (`*.db*`) are excluded by `.gitignore` to prevent credential exposure or state pollution in version control.
2. **SQL Injection Defense:** All queries against SQLite execute strictly via parameterized placeholders (`?`), completely avoiding raw f-string SQL assembly.
3. **Open Redirect Mitigation:** The schema validator strictly requires absolute HTTPS addresses, preventing scheme manipulation.