import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import DataError, IntegrityError, OperationalError, SQLAlchemyError

logger = logging.getLogger(__name__)


def validation_message(error: dict) -> str:
    error_type = error.get("type", "")
    context = error.get("ctx") or {}
    message = error.get("msg", "Invalid value")

    if isinstance(message, str) and message.startswith("Value error, "):
        return message.removeprefix("Value error, ")
    if error_type == "json_invalid":
        return "Request body must be valid JSON"
    if error_type == "missing":
        return "This field is required"
    if error_type == "extra_forbidden":
        return "Unknown field"
    if error_type == "string_too_short" and context.get("min_length") == 1:
        return "Must not be empty"
    if error_type == "string_too_short":
        return f"Must be at least {context.get('min_length')} characters"
    if error_type == "string_too_long":
        return f"Must be at most {context.get('max_length')} characters"
    if error_type in {"int_parsing", "int_type"}:
        return "Must be an integer"
    if error_type == "string_type":
        return "Must be a string"
    if error_type == "greater_than":
        return f"Must be greater than {context.get('gt')}"
    if error_type == "less_than_equal":
        return f"Must be less than or equal to {context.get('le')}"
    return message


def validation_field(location: tuple) -> str:
    if not location:
        return "body"
    return ".".join(str(part) for part in location)


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        errors = [
            {
                "field": validation_field(tuple(error.get("loc", ()))),
                "message": validation_message(error),
            }
            for error in exc.errors()
        ]
        return JSONResponse(
            status_code=422,
            content={"detail": "Invalid request", "errors": errors},
        )

    @app.exception_handler(IntegrityError)
    async def integrity_error_handler(
        request: Request, exc: IntegrityError
    ) -> JSONResponse:
        logger.exception("Integrity error on %s %s", request.method, request.url.path)
        return JSONResponse(
            status_code=409,
            content={"detail": "This operation conflicts with existing data"},
        )

    @app.exception_handler(DataError)
    async def data_error_handler(request: Request, exc: DataError) -> JSONResponse:
        logger.exception("Invalid data on %s %s", request.method, request.url.path)
        return JSONResponse(status_code=422, content={"detail": "Invalid data"})

    @app.exception_handler(OperationalError)
    async def operational_error_handler(
        request: Request, exc: OperationalError
    ) -> JSONResponse:
        logger.exception(
            "Database unavailable on %s %s", request.method, request.url.path
        )
        return JSONResponse(
            status_code=503,
            content={"detail": "The database is unavailable. Try again later."},
        )

    @app.exception_handler(SQLAlchemyError)
    async def sqlalchemy_error_handler(
        request: Request, exc: SQLAlchemyError
    ) -> JSONResponse:
        logger.exception("Database error on %s %s", request.method, request.url.path)
        return JSONResponse(
            status_code=500, content={"detail": "A database error occurred"}
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        logger.exception("Unhandled error on %s %s", request.method, request.url.path)
        return JSONResponse(
            status_code=500, content={"detail": "An unexpected error occurred"}
        )
