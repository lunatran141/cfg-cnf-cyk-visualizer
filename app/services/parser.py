"""Phân tích và chuẩn hóa văn phạm phi ngữ cảnh CFG."""

from dataclasses import dataclass, field

from app.models.grammar import Grammar, EPSILON
from app.services.tokenizer import Token, tokenize_line
from app.services.normalizer import (
    NormalizedLine,
    normalize_lines,
)
from app.services.diagnostics import (
    ErrorCode,
    ParseError,
    Diagnostics,
)


@dataclass
class ParseResult:
    """Kết quả phân tích CFG."""

    grammar: Grammar | None = None
    errors: list[ParseError] = field(default_factory=list)

    @property
    def success(self) -> bool:
        """Kiểm tra parser có thành công không."""
        return self.grammar is not None and not self.errors

    def to_dict(self) -> dict:
        """Chuyển kết quả phân tích thành dữ liệu JSON."""
        return {
            "success": self.success,
            "grammar": (
                self.grammar.to_dict()
                if self.grammar is not None
                else None
            ),
            "errors": [
                error.to_dict()
                for error in self.errors
            ],
        }


def parseGrammar(
    text: str,
    start_symbol: str | None = None,
) -> ParseResult:
    """Chuẩn hóa và phân tích CFG thành Grammar hoặc diagnostics."""

    grammar = Grammar()
    diagnostics = Diagnostics()

    # Lưu các biến đã khai báo ở vế trái.
    declared_variables: set[str] = set()

    # Lưu biến tham chiếu và thông tin dòng gốc.
    references: list[tuple[Token, NormalizedLine]] = []

    first_variable: str | None = None

    def add_error(
        code: ErrorCode,
        line: NormalizedLine,
        column: int,
        message: str,
        suggestion: str,
    ) -> None:
        """Ghi nhận lỗi theo vị trí văn bản gốc."""
        diagnostics.add(
            code=code,
            line=line.line,
            column=line.original_column(column),
            content=line.original,
            message=message,
            suggestion=suggestion,
        )

    # Kiểm tra kiểu dữ liệu đầu vào.
    if not isinstance(text, str):
        diagnostics.add(
            code=ErrorCode.INVALID_INPUT_TYPE,
            line=1,
            column=1,
            content="",
            message="Văn phạm rỗng hoặc không hợp lệ.",
            suggestion="Nhập văn phạm dưới dạng văn bản.",
        )

        return ParseResult(errors=diagnostics.errors)

    # Kiểm tra văn phạm rỗng.
    if not text.strip():
        diagnostics.add(
            code=ErrorCode.EMPTY_INPUT,
            line=1,
            column=1,
            content=text,
            message="Văn phạm rỗng hoặc không hợp lệ.",
            suggestion="Nhập ít nhất một luật sinh, ví dụ S -> a.",
        )

        return ParseResult(errors=diagnostics.errors)

    # Chuẩn hóa xuống dòng, hỗ trợ CRLF, CR và LF.
    normalized_text = text.replace("\r\n", "\n")
    normalized_text = normalized_text.replace("\r", "\n")

    # Chuẩn hóa văn bản trước khi phân tích.
    lines = normalize_lines(normalized_text)

    for line in lines:

        # Bỏ qua dòng rỗng nhưng giữ nguyên số dòng.
        if not line.text:
            continue

        tokens = tokenize_line(
            line.text,
            line.line,
        )

        # Kiểm tra các ký hiệu không hợp lệ.
        invalid_tokens = [
            token for token in tokens
            if token.type == "INVALID"
        ]

        if invalid_tokens:
            for token in invalid_tokens:
                add_error(
                    ErrorCode.INVALID_SYMBOL,
                    line,
                    token.column,
                    f"Ký hiệu không hợp lệ: {token.value}",
                    "Xóa hoặc thay thế ký hiệu không hợp lệ.",
                )

            continue

        # Xác định vị trí mũi tên.
        arrows = [
            index
            for index, token in enumerate(tokens)
            if token.type == "ARROW"
        ]

        if not arrows:
            add_error(
                ErrorCode.MISSING_ARROW,
                line,
                1,
                "Mỗi dòng phải có đúng một mũi tên.",
                "Sử dụng dạng S -> a | b.",
            )
            continue

        if len(arrows) > 1:
            add_error(
                ErrorCode.MULTIPLE_ARROWS,
                line,
                tokens[arrows[1]].column,
                "Mỗi dòng phải có đúng một mũi tên.",
                "Chỉ sử dụng một mũi tên trên mỗi dòng.",
            )
            continue

        arrow_index = arrows[0]

        lhs_tokens = tokens[:arrow_index]
        rhs_tokens = tokens[arrow_index + 1:]

        # Vế trái phải chứa đúng một biến.
        if (
            len(lhs_tokens) != 1
            or lhs_tokens[0].type != "VARIABLE"
        ):
            add_error(
                ErrorCode.INVALID_LHS,
                line,
                tokens[0].column,
                "Vế trái phải là một biến hợp lệ.",
                "Sử dụng biến như S, A, B hoặc A1.",
            )
            continue

        lhs = lhs_tokens[0].value

        # Kiểm tra vế phải rỗng.
        if not rhs_tokens:
            add_error(
                ErrorCode.EMPTY_RHS,
                line,
                tokens[arrow_index].column,
                "Vế phải của luật sinh bị rỗng.",
                "Sử dụng ε nếu muốn biểu diễn chuỗi rỗng.",
            )
            continue

        # Tách các lựa chọn luật sinh.
        alternatives: list[list[Token]] = [[]]
        separators: list[Token] = []

        for token in rhs_tokens:
            if token.type == "PIPE":
                alternatives.append([])
                separators.append(token)
            else:
                alternatives[-1].append(token)

        # Kiểm tra vị trí các production rỗng.
        empty_indices = [
            index
            for index, alternative in enumerate(alternatives)
            if not alternative
        ]

        if empty_indices:
            for index in empty_indices:
                separator_index = min(
                    index,
                    len(separators) - 1,
                )

                add_error(
                    ErrorCode.EMPTY_PRODUCTION,
                    line,
                    separators[separator_index].column,
                    "Có production rỗng giữa các dấu phân cách.",
                    "Bổ sung luật sinh hoặc xóa dấu | thừa.",
                )

            continue

        # Đăng ký biến vế trái.
        declared_variables.add(lhs)
        grammar.variables.add(lhs)

        if first_variable is None:
            first_variable = lhs

        # Phân tích từng luật sinh.
        for alternative in alternatives:

            epsilon_tokens = [
                token
                for token in alternative
                if token.type == "EPSILON"
            ]

            if epsilon_tokens:
                if len(alternative) == 1:
                    grammar.add_production(lhs, EPSILON)
                else:
                    add_error(
                        ErrorCode.INVALID_EPSILON,
                        line,
                        epsilon_tokens[0].column,
                        "Epsilon phải đứng riêng trong một luật sinh.",
                        "Sử dụng dạng A -> a | ε.",
                    )

                continue

            production = tuple(
                token.value
                for token in alternative
            )

            for token in alternative:
                if token.type == "TERMINAL":
                    grammar.terminals.add(token.value)

                elif token.type == "VARIABLE":
                    grammar.variables.add(token.value)
                    references.append((token, line))

            grammar.add_production(lhs, production)

    # Kiểm tra biến chưa khai báo sau khi đọc toàn bộ CFG.
    for token, line in references:
        if token.value not in declared_variables:
            add_error(
                ErrorCode.UNDEFINED_VARIABLE,
                line,
                token.column,
                f"Biến {token.value} chưa được khai báo.",
                f"Bổ sung luật sinh cho biến {token.value}.",
            )

    # Xác định ký hiệu bắt đầu.
    if start_symbol is None:
        grammar.start_symbol = first_variable or "S"

    elif isinstance(start_symbol, str):
        grammar.start_symbol = start_symbol.strip()

    else:
        grammar.start_symbol = ""

    # Tránh lỗi dây chuyền khi văn phạm đã có lỗi.
    if (
        not diagnostics.has_errors
        and grammar.start_symbol not in declared_variables
    ):
        diagnostics.add(
            code=ErrorCode.INVALID_START_SYMBOL,
            line=1,
            column=1,
            content=grammar.start_symbol,
            message=(
                "Ký hiệu bắt đầu không hợp lệ "
                "hoặc chưa được khai báo."
            ),
            suggestion="Chọn một biến đã xuất hiện ở vế trái.",
        )

    # Không trả về Grammar chưa hợp lệ.
    if diagnostics.has_errors:
        return ParseResult(
            errors=diagnostics.errors,
        )

    return ParseResult(grammar=grammar)
