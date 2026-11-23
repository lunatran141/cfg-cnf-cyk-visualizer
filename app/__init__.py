"""Khởi tạo ứng dụng CFG–CNF–CYK Visualizer."""

from flask import Flask


def create_app(test_config: dict | None = None) -> Flask:
    """Tạo và cấu hình ứng dụng Flask."""

    app = Flask(__name__)

    # Cấu hình mặc định dùng trong môi trường phát triển.
    app.config.from_mapping(
        SECRET_KEY="development-secret-key",
    )

    # Cho phép bộ kiểm thử ghi đè cấu hình mặc định.
    if test_config:
        app.config.update(test_config)

    # Đăng ký nhóm route chính của ứng dụng.
    from app.routes import main_bp

    app.register_blueprint(main_bp)

    return app