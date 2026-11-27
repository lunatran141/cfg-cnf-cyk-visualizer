"""Quản lý thông tin lỗi khi phân tích văn phạm CFG."""

from dataclasses import dataclass
from enum import StrEnum


class ErrorCode(StrEnum):
    """Danh sách mã lỗi của parser CFG."""

    EMPTY_INPUT = "EMPTY_INPUT"
    INVALID_INPUT_TYPE = "INVALID_INPUT_TYPE"
    INVALID_SYMBOL = "INVALID_SYMBOL"
    MISSING_ARROW = "MISSING_ARROW"
    MULTIPLE_ARROWS = "MULTIPLE_ARROWS"
    INVALID_LHS = "INVALID_LHS"
    EMPTY_RHS = "EMPTY_RHS"
    EMPTY_PRODUCTION = "EMPTY_PRODUCTION"
    INVALID_EPSILON = "INVALID_EPSILON"
    UNDEFINED_VARIABLE = "UNDEFINED_VARIABLE"
    INVALID_START_SYMBOL = "INVALID_START_SYMBOL"


@dataclass(frozen=True)
class ParseError:
    """Lưu thông tin chi tiết của một lỗi văn phạm."""

    line: int
    column: int
    content: str
    message: str
    suggestion: str
    code: ErrorCode

    def to_dict(self) -> dict[str, int | str]:
        """Chuyển thông tin lỗi thành dữ liệu tương thích JSON."""
        return {
            "line": self.line,
            "column": self.column,
            "code": self.code.value,
            "content": self.content,
            "message": self.message,
            "suggestion": self.suggestion,
        }


class Diagnostics:
    """Thu thập và quản lý danh sách lỗi của parser."""

    def __init__(self) -> None:
        """Khởi tạo danh sách lỗi rỗng."""
        self._errors: list[ParseError] = []

    def add(
        self,
        code: ErrorCode,
        line: int,
        column: int,
        content: str,
        message: str,
        suggestion: str,
    ) -> None:
        """Thêm một lỗi vào danh sách diagnostics."""
        self._errors.append(
            ParseError(
                line=line,
                column=column,
                content=content,
                message=message,
                suggestion=suggestion,
                code=code,
            )
        )

    @property
    def errors(self) -> list[ParseError]:
        """Trả về danh sách lỗi theo thứ tự dòng và cột."""
        return sorted(
            self._errors,
            key=lambda error: (
                error.line,
                error.column,
            ),
        )

    @property
    def has_errors(self) -> bool:
        """Kiểm tra danh sách có chứa lỗi hay không."""
        return bool(self._errors)

    def count(self) -> int:
        """Đếm tổng số lỗi đã phát hiện."""
        return len(self._errors)

    def to_dict(self) -> list[dict[str, int | str]]:
        """Chuyển danh sách lỗi thành dữ liệu tương thích JSON."""
        return [
            error.to_dict()
            for error in self.errors
        ]

    def clear(self) -> None:
        """Xóa toàn bộ lỗi trong danh sách."""
        self._errors.clear()
