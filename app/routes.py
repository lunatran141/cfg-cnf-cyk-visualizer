"""Định nghĩa các HTTP route của ứng dụng."""

from flask import Blueprint, jsonify, render_template

# Blueprint giúp tách route khỏi phần khởi tạo ứng dụng.
main_bp = Blueprint("main", __name__)


@main_bp.get("/")
def index():
    """Hiển thị trang chính của ứng dụng."""

    return render_template(
        "index.html",
        app_name="CFG–CNF–CYK Visualizer",
    )


@main_bp.get("/health")
def health():
    """Trả về trạng thái hoạt động cho CI và Docker."""

    return jsonify(
        {
            "service": "cfg-cnf-cyk-visualizer",
            "status": "healthy",
        }
    )