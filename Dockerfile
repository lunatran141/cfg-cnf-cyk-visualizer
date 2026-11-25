# Sử dụng Python 3.11 bản gọn nhẹ.
FROM python:3.11-slim

# Không tạo file .pyc và hiển thị log ngay lập tức.
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=5000

# Thư mục làm việc bên trong container.
WORKDIR /app

# Tạo người dùng riêng để không chạy ứng dụng bằng root.
RUN groupadd --system appgroup \
    && useradd --system --gid appgroup appuser

# Cài đặt dependencies trước để tận dụng Docker layer cache.
COPY requirements.txt .

RUN python -m pip install \
    --no-cache-dir \
    --disable-pip-version-check \
    -r requirements.txt

# Sao chép mã nguồn vào container.
COPY . .

# Chuyển quyền sở hữu cho người dùng ứng dụng.
RUN chown -R appuser:appgroup /app

USER appuser

# Khai báo cổng Flask sử dụng.
EXPOSE 5000

# Kiểm tra trạng thái hoạt động của ứng dụng.
HEALTHCHECK \
    --interval=30s \
    --timeout=5s \
    --start-period=10s \
    --retries=3 \
    CMD python -c \
    "import urllib.request; urllib.request.urlopen('http://127.0.0.1:5000/health')" \
    || exit 1

# Khởi chạy Flask skeleton.
CMD ["python", "run.py"]