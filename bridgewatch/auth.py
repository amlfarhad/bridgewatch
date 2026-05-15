from __future__ import annotations

from fastapi import Header, HTTPException, status

from .config import get_settings


def require_operator(x_api_key: str | None = Header(default=None)) -> str:
    expected = get_settings().api_key
    if not x_api_key or x_api_key != expected:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Operator API key is required for this action.",
        )
    return "operator"

