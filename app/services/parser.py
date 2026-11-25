"""Phân tích cú pháp văn phạm phi ngữ cảnh CFG."""

from dataclasses import dataclass, field

from app.models.grammar import Grammar, EPSILON
from app.services.tokenizer import Token, tokenize_line


@dataclass(frozen=True)
class ParseError:
    """Thông tin lỗi khi phân tích văn phạm."""

    line: int
    column: int
    content: str
    message: str
    suggestion: str


@dataclass
class ParseResult:
    """Kết quả phân tích CFG."""

    grammar: Grammar | None = None
    errors: list[ParseError] = field(default_factory=list)

    @property
    def success(self) -> bool:
        """Kiểm tra parser có thành công không."""
        return self.grammar is not None and not self.errors


def parseGrammar(
    text: str,
    start_symbol: str | None = None,
) -> ParseResult:
    """Chuyển văn bản CFG thành Grammar hoặc danh sách lỗi."""

    grammar = Grammar()
    errors: list[ParseError] = []

    # Lưu các biến đã khai báo ở vế trái.
    declared_variables: set[str] = set()

    # Lưu vị trí các biến xuất hiện ở vế phải.
    references: list[tuple[Token, str]] = []

    first_variable: str | None = None

    def add_error(
        line: int,
        column: int,
        content: str,
        message: str,
        suggestion: str,
    ) -> None:
        errors.append(
            ParseError(
                line=line,
                column=column,
                content=content,
                message=message,
                suggestion=suggestion,
            )
        )

    # Kiểm tra dữ liệu đầu vào rỗng.
    if not isinstance(text, str) or not text.strip():
        add_error(
            1,
            1,
            text if isinstance(text, str) else "",
            "Văn phạm rỗng hoặc không hợp lệ.",
            "Nhập ít nhất một luật sinh, ví dụ S -> a.",
        )
        return ParseResult(errors=errors)

    # Phân tích từng dòng văn phạm.
    for line_number, line in enumerate(
        text.splitlines(),
        start=1,
    ):
        if not line.strip():
            continue

        tokens = tokenize_line(line, line_number)

        # Kiểm tra ký hiệu không hợp lệ.
        invalid_tokens = [
            token for token in tokens
            if token.type == "INVALID"
        ]

        if invalid_tokens:
            for token in invalid_tokens:
                add_error(
                    token.line,
                    token.column,
                    line,
                    f"Ký hiệu không hợp lệ: {token.value}",
                    "Xóa hoặc thay thế ký hiệu không hợp lệ.",
                )
            continue

        # Xác định vị trí mũi tên.
        arrows = [
            index for index, token in enumerate(tokens)
            if token.type == "ARROW"
        ]

        if len(arrows) != 1:
            add_error(
                line_number,
                tokens[arrows[1]].column if len(arrows) > 1 else 1,
                line,
                "Mỗi dòng phải có đúng một mũi tên.",
                "Sử dụng dạng S -> a | b.",
            )
            continue

        arrow_index = arrows[0]

        lhs_tokens = tokens[:arrow_index]
        rhs_tokens = tokens[arrow_index + 1:]

        # Vế trái phải là đúng một biến.
        if (
            len(lhs_tokens) != 1
            or lhs_tokens[0].type != "VARIABLE"
        ):
            add_error(
                line_number,
                tokens[0].column,
                line,
                "Vế trái phải là một biến hợp lệ.",
                "Sử dụng biến như S, A, B hoặc A1.",
            )
            continue

        lhs = lhs_tokens[0].value

        # Kiểm tra vế phải rỗng.
        if not rhs_tokens:
            add_error(
                line_number,
                tokens[arrow_index].column,
                line,
                "Vế phải của luật sinh bị rỗng.",
                "Sử dụng ε nếu muốn biểu diễn chuỗi rỗng.",
            )
            continue

        # Tách các production theo dấu |.
        alternatives: list[list[Token]] = [[]]

        for token in rhs_tokens:
            if token.type == "PIPE":
                alternatives.append([])
            else:
                alternatives[-1].append(token)

        if any(not alternative for alternative in alternatives):
            add_error(
                line_number,
                tokens[arrow_index].column,
                line,
                "Có production rỗng giữa các dấu phân cách.",
                "Bổ sung luật sinh hoặc xóa dấu | thừa.",
            )
            continue

        # Đăng ký biến vế trái.
        declared_variables.add(lhs)
        grammar.variables.add(lhs)

        if first_variable is None:
            first_variable = lhs

        # Xử lý từng luật sinh.
        for alternative in alternatives:
            epsilon_tokens = [
                token for token in alternative
                if token.type == "EPSILON"
            ]

            if epsilon_tokens:
                if len(alternative) == 1:
                    grammar.add_production(lhs, EPSILON)
                else:
                    add_error(
                        line_number,
                        epsilon_tokens[0].column,
                        line,
                        "Epsilon phải đứng riêng trong một luật sinh.",
                        "Sử dụng dạng A -> a | ε.",
                    )
                continue

            production = tuple(
                token.value for token in alternative
            )

            for token in alternative:
                if token.type == "TERMINAL":
                    grammar.terminals.add(token.value)

                elif token.type == "VARIABLE":
                    grammar.variables.add(token.value)
                    references.append((token, line))

            grammar.add_production(lhs, production)

    # Kiểm tra biến chưa được khai báo.
    for token, line in references:
        if token.value not in declared_variables:
            add_error(
                token.line,
                token.column,
                line,
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

    # Chỉ kiểm tra start symbol khi không có lỗi trước đó.
    if not errors and grammar.start_symbol not in declared_variables:
        add_error(
            1,
            1,
            grammar.start_symbol,
            "Ký hiệu bắt đầu không hợp lệ hoặc chưa được khai báo.",
            "Chọn một biến đã xuất hiện ở vế trái.",
        )

    # Không trả về Grammar chưa hợp lệ.
    if errors:
        errors.sort(key=lambda error: (error.line, error.column))
        return ParseResult(errors=errors)

    return ParseResult(grammar=grammar)
