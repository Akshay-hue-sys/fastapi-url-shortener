from fastapi import FastAPI, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse

from src.schemas import ShortenRequest, ShortenResponse
from src.shortener import get_target_url, save_url

app = FastAPI(title="URL Shortener API")


@app.get("/", response_class=HTMLResponse)
async def home_page() -> str:
    return """
    <!DOCTYPE html>
    <html>
      <head>
        <title>URL Shortener</title>
        <style>
          body { font-family: sans-serif; max-width: 500px; margin: 50px auto; padding: 20px; }
          h2 { color: #333; }
          p { color: #666; }
        </style>
      </head>
      <body>
        <h2>URL Shortener Service</h2>
        <p>Status: Active and running on HTTPS.</p>
        <p>Use the API endpoint <code>POST /shorten</code> to create links.</p>
      </body>
    </html>
    """


@app.post("/shorten", response_model=ShortenResponse, status_code=status.HTTP_201_CREATED)
async def shorten_url_endpoint(payload: ShortenRequest) -> ShortenResponse:
    target = str(payload.url)
    code = save_url(target)
    return ShortenResponse(short_code=code, target_url=target)


@app.get("/{code}")
async def redirect_to_target(code: str) -> RedirectResponse:
    target = get_target_url(code)
    if target is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Short code not found",
        )
    return RedirectResponse(url=target, status_code=status.HTTP_307_TEMPORARY_REDIRECT)