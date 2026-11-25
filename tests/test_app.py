"""Kiểm thử cơ bản cho Flask application skeleton."""

import pytest
from flask import Flask
from flask.testing import FlaskClient

from app import create_app


@pytest.fixture()
def app() -> Flask:
    """Tạo ứng dụng dùng riêng cho quá trình kiểm thử."""

    application = create_app(
        {
            "TESTING": True,
            "SECRET_KEY": "test-secret-key",
        }
    )

    return application


@pytest.fixture()
def client(app: Flask) -> FlaskClient:
    """Tạo HTTP client mô phỏng yêu cầu từ trình duyệt."""

    return app.test_client()


def test_create_app(app: Flask) -> None:
    """Ứng dụng phải được tạo ở chế độ kiểm thử."""

    assert app.config["TESTING"] is True


def test_home_page_returns_success(client: FlaskClient) -> None:
    """Trang chính phải phản hồi thành công."""

    response = client.get("/")

    assert response.status_code == 200
    assert "CFG–CNF–CYK Visualizer".encode("utf-8") in response.data


def test_health_endpoint_returns_success(
    client: FlaskClient,
) -> None:
    """Health endpoint phải trả về trạng thái healthy."""

    response = client.get("/health")
    data = response.get_json()

    assert response.status_code == 200
    assert data == {
        "service": "cfg-cnf-cyk-visualizer",
        "status": "healthy",
    }


def test_unknown_page_returns_not_found(
    client: FlaskClient,
) -> None:
    """Đường dẫn không tồn tại phải trả về mã 404."""

    response = client.get("/not-found")

    assert response.status_code == 404