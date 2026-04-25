"""Authentication request and response schemas."""

from pydantic import BaseModel


class LoginRequest(BaseModel):
    """User login payload."""

    username: str
    password: str


class TokenResponse(BaseModel):
    """JWT token response schema."""

    access_token: str
    token_type: str = "bearer"
