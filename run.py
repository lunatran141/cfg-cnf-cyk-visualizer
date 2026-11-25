"""Điểm khởi chạy ứng dụng Flask trong môi trường phát triển."""

import os

from app import create_app

# Tạo ứng dụng thông qua application factory.
app = create_app()


if __name__ == "__main__":
    # Đọc cổng từ biến môi trường, mặc định là 5000.
    port = int(os.getenv("PORT", "5000"))

    app.run(
        # Cho phép truy cập ứng dụng từ bên ngoài Docker container.
        host="0.0.0.0",
        port=port,
        # Chỉ bật debug khi FLASK_DEBUG=1.
        debug=os.getenv("FLASK_DEBUG", "0") == "1",
    )