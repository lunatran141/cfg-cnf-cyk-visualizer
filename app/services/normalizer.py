"""Chuẩn hóa văn bản văn phạm phi ngữ cảnh CFG."""

from dataclasses import dataclass


# Các ký hiệu tương đương cần chuẩn hóa.
SYMBOL_MAP = {
    "→": "->",
    "｜": "|",
}


@dataclass(frozen=True)
class NormalizedLine:
    """Lưu nội dung chuẩn hóa và vị trí trong dòng gốc."""

    original: str
    text: str
    line: int
    column_map: tuple[int, ...]

    def original_column(self, column: int) -> int:
        """Chuyển vị trí cột chuẩn hóa về cột gốc."""
        if column < 1:
            return 1

        if column > len(self.column_map):
            return len(self.original) + 1

        return self.column_map[column - 1]


def normalize_line(
    text: str,
    line_number: int = 1,
) -> NormalizedLine:
    """Chuẩn hóa một dòng và giữ ánh xạ vị trí cột."""

    characters: list[str] = []
    column_map: list[int] = []

    for column, character in enumerate(text, start=1):

        # Chuẩn hóa khoảng trắng liên tiếp.
        if character.isspace():
            if characters and characters[-1] != " ":
                characters.append(" ")
                column_map.append(column)

            continue

        # Chuẩn hóa các ký hiệu tương đương.
        replacement = SYMBOL_MAP.get(
            character,
            character,
        )

        for normalized_character in replacement:
            characters.append(normalized_character)
            column_map.append(column)

    # Loại bỏ khoảng trắng cuối dòng.
    if characters and characters[-1] == " ":
        characters.pop()
        column_map.pop()

    return NormalizedLine(
        original=text,
        text="".join(characters),
        line=line_number,
        column_map=tuple(column_map),
    )


def normalize_lines(text: str) -> list[NormalizedLine]:
    """Chuẩn hóa từng dòng và giữ nguyên số dòng."""

    return [
        normalize_line(line, line_number)
        for line_number, line in enumerate(
            text.split("\n"),
            start=1,
        )
    ]


def normalize_grammar(text: str) -> str:
    """Trả về toàn bộ văn phạm sau khi chuẩn hóa."""

    return "\n".join(
        line.text
        for line in normalize_lines(text)
    )
