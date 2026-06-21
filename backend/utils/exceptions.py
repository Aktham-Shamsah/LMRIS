from fastapi import FastAPI, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pymongo.errors import DuplicateKeyError


def register_exception_handlers(app: FastAPI) -> None:
    """Every error response uses the same shape FastAPI uses by default for
    HTTPException: {"detail": ...}. Without these handlers, RequestValidationError,
    DuplicateKeyError, and uncaught exceptions would each produce a differently
    shaped body, which is confusing for API clients to parse consistently."""

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(request: Request, exc: RequestValidationError):
        # exc.errors() can embed the raw exception instance in ctx["error"] for
        # validators that raise ValueError (e.g. custom field_validators) -
        # jsonable_encoder sanitizes that before it hits json.dumps.
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={"detail": jsonable_encoder(exc.errors())},
        )

    @app.exception_handler(DuplicateKeyError)
    async def duplicate_key_handler(request: Request, exc: DuplicateKeyError):
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={"detail": "Duplicate key error."},
        )

    @app.exception_handler(Exception)
    async def generic_handler(request: Request, exc: Exception):
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": str(exc)},
        )
