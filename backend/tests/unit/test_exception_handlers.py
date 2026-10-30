import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from pydantic import BaseModel
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.exception.CustomException import (
    BadRequestException,
    BusinessRuleException,
    ConflictException,
    ForbiddenException,
    NotFoundException,
    UnauthorizedException,
)
from app.exception.ExceptionHandler import register_exception_handlers


def test_custom_exception_status_codes():
    assert NotFoundException().status_code == 404
    assert ForbiddenException().status_code == 403
    assert UnauthorizedException().status_code == 401
    assert ConflictException().status_code == 409
    assert BadRequestException().status_code == 400
    assert BusinessRuleException().status_code == 422


def test_custom_exception_payload():
    exc = NotFoundException("Item not found", data={"item_id": 123})
    assert exc.message == "Item not found"
    assert exc.data == {"item_id": 123}
    assert exc.status_code == 404


class SampleBody(BaseModel):
    name: str
    age: int


@pytest.fixture
def test_app() -> FastAPI:
    app = FastAPI()
    register_exception_handlers(app)

    @app.get("/test/not-found")
    async def route_not_found():
        raise NotFoundException("Target resource not found")

    @app.get("/test/bad-request")
    async def route_bad_request():
        raise BadRequestException("Invalid request format")

    @app.get("/test/starlette-http")
    async def route_starlette():
        raise StarletteHTTPException(status_code=403, detail="Starlette access denied")

    @app.get("/test/unhandled")
    async def route_unhandled():
        raise RuntimeError("Unexpected boom!")

    @app.post("/test/validation")
    async def route_validation(_body: SampleBody):
        return {"status": "ok"}

    return app


@pytest.mark.asyncio
async def test_handler_not_found_exception(test_app: FastAPI):
    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/test/not-found")
        assert response.status_code == 404
        data = response.json()
        assert data["success"] is False
        assert data["message"] == "Target resource not found"
        assert data["data"] is None


@pytest.mark.asyncio
async def test_handler_bad_request_exception(test_app: FastAPI):
    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/test/bad-request")
        assert response.status_code == 400
        data = response.json()
        assert data["success"] is False
        assert data["message"] == "Invalid request format"


@pytest.mark.asyncio
async def test_handler_starlette_exception(test_app: FastAPI):
    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/test/starlette-http")
        assert response.status_code == 403
        data = response.json()
        assert data["success"] is False
        assert data["message"] == "Starlette access denied"


@pytest.mark.asyncio
async def test_handler_validation_error(test_app: FastAPI):
    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/test/validation", json={"name": 123, "age": "not-an-int"})
        assert response.status_code == 422
        data = response.json()
        assert data["success"] is False
        assert "Input validation failed" in data["message"]
        assert "errors" in data["data"]
        assert len(data["data"]["errors"]) > 0


@pytest.mark.asyncio
async def test_handler_unhandled_exception(test_app: FastAPI):
    transport = ASGITransport(app=test_app, raise_app_exceptions=False)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/test/unhandled")
        assert response.status_code == 500
        data = response.json()
        assert data["success"] is False
        assert "internal server error" in data["message"].lower()
        assert data["data"] is None
