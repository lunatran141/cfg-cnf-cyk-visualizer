"""Tokenizer cho văn phạm phi ngữ cảnh CFG."""

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class Token:
    """Lưu loại, giá trị và vị trí của token."""

    type: str
    value: str
    line: int
    column: int


# Quy tắc nhận diện token theo thứ tự ưu tiên.
TOKEN_PATTERN = re.compile(
    r"(?P<ARROW>->|→)"
    r"|(?P<PIPE>\|)"
    r"|(?P<EPSILON>ε)"
    r"|(?P<VARIABLE>[A-Z][0-9]*'*)"
    r"|(?P<TERMINAL>id|num|[a-z0-9])"
    r"|(?P<WHITESPACE>[ \t]+)"
    r"|(?P<INVALID>.)"
)


def tokenize_line(
    text: str,
    line_number: int = 1,
) -> list[Token]:
    """Phân tách token trên một dòng văn phạm."""

    tokens: list[Token] = []

    for match in TOKEN_PATTERN.finditer(text):
        token_type = match.lastgroup
        value = match.group()

        # Bỏ qua khoảng trắng.
        if token_type == "WHITESPACE":
            continue

        tokens.append(
            Token(
                type=token_type,
                value=value,
                line=line_number,
                column=match.start() + 1,
            )
        )

    return tokens


def tokenize(text: str) -> list[Token]:
    """Phân tách token của toàn bộ văn phạm."""

    tokens: list[Token] = []

    for line_number, line in enumerate(
        text.splitlines(),
        start=1,
    ):
        tokens.extend(
            tokenize_line(line, line_number)
        )

    return tokens
