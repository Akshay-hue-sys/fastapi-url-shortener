"""Pydantic v2 schemas for URL shortening contracts."""

from pydantic import BaseModel, HttpUrl, field_validator


class ShortenRequest(BaseModel):
    """Payload sent by a user to create a short code."""

    url: HttpUrl

    @field_validator("url")
    @classmethod
    def enforce_https(cls, v: HttpUrl) -> HttpUrl:
        """Reject unencrypted http links; require https."""
        if v.scheme != "https":
            raise ValueError("Only secure HTTPS URLs are allowed")
        return v


class ShortenResponse(BaseModel):
    """Payload returned after generating the short code."""

    short_code: str
    target_url: str