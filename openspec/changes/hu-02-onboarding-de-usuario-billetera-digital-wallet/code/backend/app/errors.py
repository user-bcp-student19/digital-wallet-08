from typing import Any, Dict, List, Optional

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException


class ApiError(Exception):
    def __init__(
        self,
        status_code: int,
        code: str,
        message: str,
        *,
        details: Optional[List[Dict[str, str]]] = None,
        suggestions: Optional[List[str]] = None,
        retry_after_seconds: Optional[int] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> None:
        super().__init__(code)
        self.status_code = status_code
        self.code = code
        self.message = message
        self.details = details
        self.suggestions = suggestions
        self.retry_after_seconds = retry_after_seconds
        self.headers = dict(headers or {})


def _body(exc: ApiError) -> Dict[str, Any]:
    body: Dict[str, Any] = {"code": exc.code, "message": exc.message}
    if exc.details is not None:
        body["details"] = exc.details
    if exc.suggestions is not None:
        body["suggestions"] = exc.suggestions
    if exc.retry_after_seconds is not None:
        body["retry_after_seconds"] = exc.retry_after_seconds
    return body


async def api_error_handler(request: Request, exc: ApiError) -> JSONResponse:
    headers = dict(exc.headers)
    if exc.retry_after_seconds is not None:
        headers["Retry-After"] = str(exc.retry_after_seconds)
    return JSONResponse(status_code=exc.status_code, content=_body(exc), headers=headers or None)


_RULES = {
    "string_too_long": "max_length",
    "string_too_short": "min_length",
    "string_pattern_mismatch": "pattern",
    "missing": "required",
}


async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """422 sin eco de los valores recibidos (nunca se usa `input`)."""
    details = []
    for err in exc.errors():
        loc = [str(p) for p in err.get("loc", ()) if p not in ("body", "query", "path")]
        details.append(
            {
                "field": ".".join(loc) or "body",
                "rule": _RULES.get(err.get("type", ""), err.get("type", "invalid")),
            }
        )
    body = {"code": "VALIDATION_ERROR", "message": "Datos de entrada inválidos", "details": details}
    return JSONResponse(status_code=422, content=body)


_HTTP_CODES = {
    401: "UNAUTHORIZED",
    403: "FORBIDDEN",
    404: "NOT_FOUND",
    405: "METHOD_NOT_ALLOWED",
}


async def http_error_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    code = _HTTP_CODES.get(exc.status_code, "HTTP_ERROR")
    message = exc.detail if isinstance(exc.detail, str) else "Error"
    return JSONResponse(
        status_code=exc.status_code,
        content={"code": code, "message": message},
        headers=getattr(exc, "headers", None),
    )
