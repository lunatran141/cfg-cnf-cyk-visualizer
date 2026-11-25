"""Kiểm thử Grammar, Tokenizer và Parser CFG cho T02."""

import pytest

from app.models.grammar import Grammar, EPSILON
from app.services.tokenizer import tokenize, tokenize_line
from app.services.parser import parseGrammar


# Kiểm thử Grammar Model.

def test_grammar_initialization() -> None:
    """Kiểm tra trạng thái khởi tạo của Grammar."""
    grammar = Grammar()

    assert grammar.variables == set()
    assert grammar.terminals == set()
    assert grammar.productions == {}
    assert grammar.start_symbol == "S"


def test_grammar_add_production() -> None:
    """Kiểm tra chức năng thêm luật sinh."""
    grammar = Grammar()
    grammar.add_production("S", ("A", "B"))

    assert "S" in grammar.variables
    assert grammar.productions["S"] == {("A", "B")}


def test_grammar_duplicate_production() -> None:
    """Đảm bảo không lưu luật sinh trùng lặp."""
    grammar = Grammar()

    grammar.add_production("S", ("a",))
    grammar.add_production("S", ("a",))

    assert grammar.production_count() == 1


def test_grammar_epsilon() -> None:
    """Kiểm tra cách biểu diễn epsilon."""
    grammar = Grammar()
    grammar.add_production("S", EPSILON)

    assert EPSILON == ()
    assert EPSILON in grammar.get_productions("S")


def test_grammar_production_count() -> None:
    """Kiểm tra tổng số luật sinh."""
    grammar = Grammar()

    grammar.add_production("S", ("A", "B"))
    grammar.add_production("S", ("a",))
    grammar.add_production("A", ("b",))

    assert grammar.production_count() == 3


def test_grammar_copy_no_mutation() -> None:
    """Đảm bảo bản sao không làm thay đổi Grammar gốc."""
    grammar = Grammar()

    grammar.add_production("S", ("a",))
    grammar.terminals.add("a")

    copied = grammar.copy()

    copied.add_production("S", ("b",))
    copied.terminals.add("b")
    copied.variables.add("A")

    assert grammar.production_count() == 1
    assert copied.production_count() == 2
    assert "b" not in grammar.terminals
    assert "A" not in grammar.variables


def test_grammar_to_dict() -> None:
    """Kiểm tra chuyển Grammar thành dictionary."""
    grammar = Grammar()

    grammar.add_production("S", ("id",))
    grammar.add_production("S", EPSILON)
    grammar.terminals.add("id")

    assert grammar.to_dict() == {
        "variables": ["S"],
        "terminals": ["id"],
        "productions": {
            "S": [[], ["id"]],
        },
        "start_symbol": "S",
    }


def test_grammar_get_productions() -> None:
    """Kiểm tra truy xuất luật sinh của một biến."""
    grammar = Grammar()
    grammar.add_production("S", ("a",))

    assert grammar.get_productions("S") == {("a",)}
    assert grammar.get_productions("X") == set()


# Kiểm thử Tokenizer.

def test_tokenizer_valid_grammar() -> None:
    """Kiểm tra phân tách token của grammar hợp lệ."""
    tokens = tokenize_line("S -> AB | a")

    assert [(t.type, t.value) for t in tokens] == [
        ("VARIABLE", "S"),
        ("ARROW", "->"),
        ("VARIABLE", "A"),
        ("VARIABLE", "B"),
        ("PIPE", "|"),
        ("TERMINAL", "a"),
    ]


def test_tokenizer_multichar_terminals() -> None:
    """Kiểm tra terminal nhiều ký tự."""
    tokens = tokenize_line("S -> id | num")

    terminals = [
        token.value
        for token in tokens
        if token.type == "TERMINAL"
    ]

    assert terminals == ["id", "num"]


def test_tokenizer_epsilon() -> None:
    """Kiểm tra nhận diện epsilon."""
    tokens = tokenize_line("S -> ε")

    assert tokens[-1].type == "EPSILON"
    assert tokens[-1].value == "ε"


def test_tokenizer_unicode_arrow() -> None:
    """Kiểm tra nhận diện mũi tên Unicode."""
    tokens = tokenize_line("S → AB")

    assert tokens[1].type == "ARROW"
    assert tokens[1].value == "→"


def test_tokenizer_whitespace() -> None:
    """Kiểm tra xử lý khoảng trắng."""
    tokens = tokenize_line("  S   ->   A B  ")

    assert [t.value for t in tokens] == [
        "S", "->", "A", "B"
    ]


@pytest.mark.parametrize("text", ["", "    ", "\t"])
def test_tokenizer_empty_line(text: str) -> None:
    """Kiểm tra dòng rỗng và dòng chỉ có khoảng trắng."""
    assert tokenize_line(text) == []


def test_tokenizer_invalid_symbol() -> None:
    """Kiểm tra nhận diện ký hiệu không hợp lệ."""
    tokens = tokenize_line("S -> a@b")

    invalid = [
        token for token in tokens
        if token.type == "INVALID"
    ]

    assert len(invalid) == 1
    assert invalid[0].value == "@"


def test_tokenizer_line_and_column() -> None:
    """Kiểm tra vị trí dòng và cột của token."""
    tokens = tokenize("S -> AB\nA -> a\nB -> @")

    invalid = [
        token for token in tokens
        if token.type == "INVALID"
    ]

    assert len(invalid) == 1
    assert invalid[0].line == 3
    assert invalid[0].column == 6


def test_tokenizer_variable_names() -> None:
    """Kiểm tra biến có chữ số và dấu nháy."""
    tokens = tokenize_line("S0 -> A1B' | a")

    assert [t.value for t in tokens] == [
        "S0", "->", "A1", "B'", "|", "a"
    ]


def test_tokenizer_multiple_lines() -> None:
    """Kiểm tra phân tách văn phạm nhiều dòng."""
    tokens = tokenize(
        "S -> AB | id\n"
        "A -> a\n"
        "B -> num | ε"
    )

    assert len(tokens) == 14
    assert tokens[0].line == 1
    assert tokens[-1].line == 3


# Kiểm thử Parser CFG.

def test_parser_valid_grammar() -> None:
    """Kiểm tra phân tích văn phạm hợp lệ."""
    result = parseGrammar(
        "S -> AB | id\n"
        "A -> a\n"
        "B -> num | ε"
    )

    assert result.success
    assert result.errors == []
    assert result.grammar is not None

    grammar = result.grammar

    assert grammar.variables == {"S", "A", "B"}
    assert grammar.terminals == {"a", "id", "num"}
    assert grammar.start_symbol == "S"
    assert grammar.production_count() == 5

    assert grammar.productions == {
        "S": {("A", "B"), ("id",)},
        "A": {("a",)},
        "B": {("num",), ()},
    }


def test_parser_missing_arrow() -> None:
    """Kiểm tra lỗi thiếu mũi tên."""
    result = parseGrammar("S a")

    assert not result.success
    assert result.grammar is None
    assert len(result.errors) == 1
    assert "mũi tên" in result.errors[0].message


def test_parser_invalid_lhs() -> None:
    """Kiểm tra vế trái không hợp lệ."""
    result = parseGrammar("a -> b")

    assert not result.success
    assert "Vế trái" in result.errors[0].message


def test_parser_ignore_blank_lines() -> None:
    """Kiểm tra parser bỏ qua dòng rỗng."""
    result = parseGrammar("\nS -> a\n\nA -> b\n")

    assert result.success
    assert result.grammar.production_count() == 2


def test_parser_epsilon() -> None:
    """Kiểm tra luật sinh chứa epsilon."""
    result = parseGrammar("S -> ε | a")

    assert result.success
    assert result.grammar.productions["S"] == {
        (), ("a",)
    }


def test_parser_invalid_symbol() -> None:
    """Kiểm tra thông báo lỗi ký hiệu không hợp lệ."""
    result = parseGrammar("S -> a@b")

    assert not result.success
    assert result.grammar is None
    assert len(result.errors) == 1

    error = result.errors[0]

    assert error.line == 1
    assert error.column == 7
    assert error.content == "S -> a@b"
    assert "Ký hiệu không hợp lệ" in error.message
    assert "@" in error.message
    assert error.suggestion


def test_parser_multichar_terminals() -> None:
    """Kiểm tra terminal id và num."""
    result = parseGrammar("S -> id | num")

    assert result.success
    assert result.grammar.terminals == {"id", "num"}
    assert result.grammar.productions["S"] == {
        ("id",), ("num",)
    }


def test_parser_custom_start_symbol() -> None:
    """Kiểm tra ký hiệu bắt đầu do người dùng chỉ định."""
    result = parseGrammar(
        "S -> a\nA -> b",
        start_symbol="A",
    )

    assert result.success
    assert result.grammar.start_symbol == "A"


def test_parser_invalid_start_symbol() -> None:
    """Kiểm tra ký hiệu bắt đầu không hợp lệ."""
    result = parseGrammar("S -> a", "X")

    assert not result.success
    assert "Ký hiệu bắt đầu" in result.errors[0].message


def test_parser_default_start_symbol() -> None:
    """Kiểm tra ký hiệu bắt đầu mặc định."""
    result = parseGrammar("A -> a\nS -> b")

    assert result.success
    assert result.grammar.start_symbol == "A"


def test_parser_undefined_variable() -> None:
    """Kiểm tra biến chưa được khai báo."""
    result = parseGrammar("S -> AB\nA -> a")

    assert not result.success
    assert result.errors[0].line == 1
    assert "Biến B chưa được khai báo" in (
        result.errors[0].message
    )


@pytest.mark.parametrize(
    "text",
    [
        "S -> a |",
        "S -> | a",
        "S -> a || b",
    ],
)
def test_parser_empty_alternative(text: str) -> None:
    """Kiểm tra các luật sinh rỗng."""
    result = parseGrammar(text)

    assert not result.success
    assert len(result.errors) == 1
    assert "production rỗng" in result.errors[0].message


def test_parser_empty_rhs() -> None:
    """Kiểm tra vế phải bị rỗng."""
    result = parseGrammar("S ->")

    assert not result.success
    assert "Vế phải" in result.errors[0].message


def test_parser_invalid_epsilon() -> None:
    """Kiểm tra epsilon không đứng riêng."""
    result = parseGrammar("S -> aε")

    assert not result.success
    assert "Epsilon phải đứng riêng" in (
        result.errors[0].message
    )


@pytest.mark.parametrize("text", ["", "   ", "\n\n"])
def test_parser_empty_input(text: str) -> None:
    """Kiểm tra văn phạm đầu vào rỗng."""
    result = parseGrammar(text)

    assert not result.success
    assert result.grammar is None
    assert result.errors


def test_parser_duplicate_productions() -> None:
    """Kiểm tra loại bỏ luật sinh trùng lặp."""
    result = parseGrammar("S -> a | a\nS -> a")

    assert result.success
    assert result.grammar.production_count() == 1


def test_parser_unicode_arrow() -> None:
    """Kiểm tra văn phạm sử dụng mũi tên Unicode."""
    result = parseGrammar(
        "S → AB\n"
        "A → a\n"
        "B → b"
    )

    assert result.success
    assert result.grammar.productions["S"] == {
        ("A", "B")
    }


def test_parser_multiple_arrows() -> None:
    """Kiểm tra một dòng chứa nhiều mũi tên."""
    result = parseGrammar("S -> A -> a")

    assert not result.success
    assert "mũi tên" in result.errors[0].message


def test_parser_multiple_errors() -> None:
    """Kiểm tra thu thập nhiều lỗi trên các dòng."""
    result = parseGrammar(
        "S -> @\n"
        "A b\n"
        "a -> b"
    )

    assert not result.success
    assert result.grammar is None
    assert len(result.errors) == 3

    assert [error.line for error in result.errors] == [
        1, 2, 3
    ]

    assert all(
        error.suggestion
        for error in result.errors
    )


def test_parser_forward_reference() -> None:
    """Kiểm tra biến được khai báo ở các dòng phía sau."""
    result = parseGrammar(
        "S -> AB\n"
        "A -> a\n"
        "B -> b"
    )

    assert result.success
    assert result.grammar.variables == {"S", "A", "B"}


def test_parser_deterministic() -> None:
    """Đảm bảo cùng đầu vào cho cùng kết quả."""
    text = "S -> AB | id\nA -> a\nB -> num | ε"

    first = parseGrammar(text)
    second = parseGrammar(text)

    assert first.success
    assert second.success

    assert first.grammar.to_dict() == (
        second.grammar.to_dict()
    )


def test_parser_invalid_input_type() -> None:
    """Kiểm tra parser không crash khi đầu vào sai kiểu."""
    result = parseGrammar(None)

    assert not result.success
    assert result.grammar is None
    assert result.errors
