"""
Standardised API response helpers.
"""

from typing import Any, Optional
from fastapi.responses import JSONResponse


def success(data: Any, status_code: int = 200) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={"ok": True, "data": data},
    )


def error(message: str, status_code: int = 400, detail: Optional[Any] = None) -> JSONResponse:
    body: dict = {"ok": False, "message": message}
    if detail is not None:
        body["detail"] = detail
    return JSONResponse(status_code=status_code, content=body)
