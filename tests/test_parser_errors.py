"""Kiểm thử normalization, diagnostics và parser T03."""

import json

import pytest

from app.services.normalizer import (
    normalize_line,
    normalize_lines,
    normalize_grammar,
)
from app.services.diagnostics import (
    ErrorCode,
    ParseError,
    Diagnostics,
)
from app.services.parser import parseGrammar


class TestNormalizer:
    """Kiểm thử chuẩn hóa văn phạm CFG."""

    def test_ascii_arrow(self):
        assert normalize_grammar("S -> a") == "S -> a"

    def test_unicode_arrow(self):
        assert normalize_grammar("S → a") == "S -> a"

    def test_ascii_pipe(self):
        assert normalize_grammar("S -> a | b") == "S -> a | b"

    def test_unicode_pipe(self):
        assert normalize_grammar("S → a ｜ b") == "S -> a | b"

    def test_leading_spaces(self):
        assert normalize_grammar("   S -> a") == "S -> a"

    def test_trailing_spaces(self):
        assert normalize_grammar("S -> a   ") == "S -> a"

    def test_multiple_spaces(self):
        assert normalize_grammar("S   ->   A B") == "S -> A B"

    def test_tabs(self):
        assert normalize_grammar("\tS\t->\ta\t") == "S -> a"

    def test_unicode_spaces(self):
        assert normalize_grammar("S\u00a0→\u00a0a") == "S -> a"

    def test_variable_names(self):
        assert normalize_grammar("S0 → A1B'") == "S0 -> A1B'"

    def test_terminal_names(self):
        assert normalize_grammar("S → id ｜ num") == "S -> id | num"

    def test_epsilon(self):
        assert normalize_grammar("S → ε") == "S -> ε"

    def test_empty_input(self):
        assert normalize_grammar("") == ""

    def test_whitespace_only(self):
        assert normalize_grammar("   \t  ") == ""

    def test_single_character(self):
        assert normalize_grammar("S") == "S"

    def test_empty_lines(self):
        text = "S → a\n\nA → b"
        assert normalize_grammar(text) == "S -> a\n\nA -> b"

    def test_invalid_symbol_preserved(self):
        assert normalize_grammar("S → a@b") == "S -> a@b"

    def test_idempotence(self):
        text = "  S  →  a ｜ ε "
        normalized = normalize_grammar(text)
        assert normalize_grammar(normalized) == normalized

    def test_column_mapping(self):
        line = normalize_line("S → a@")

        assert line.original == "S → a@"
        assert line.text == "S -> a@"
        assert line.column_map == (1, 2, 3, 3, 4, 5, 6)
        assert line.original_column(7) == 6

    def test_line_numbers(self):
        lines = normalize_lines("S → a\n\nA → b")

        assert len(lines) == 3
        assert [line.line for line in lines] == [1, 2, 3]
        assert lines[1].text == ""


class TestDiagnostics:
    """Kiểm thử cấu trúc và quản lý lỗi."""

    @staticmethod
    def create_diagnostics() -> Diagnostics:
        """Tạo diagnostics phục vụ kiểm thử."""
        diagnostics = Diagnostics()

        diagnostics.add(
            code=ErrorCode.INVALID_SYMBOL,
            line=1,
            column=7,
            content="S -> a@b",
            message="Invalid symbol",
            suggestion="Remove invalid symbol",
        )

        return diagnostics

    def test_error_code_count(self):
        assert len(ErrorCode) == 11

    def test_error_code_value(self):
        assert ErrorCode.INVALID_SYMBOL.value == "INVALID_SYMBOL"

    def test_empty_diagnostics(self):
        diagnostics = Diagnostics()

        assert diagnostics.errors == []
        assert diagnostics.has_errors is False
        assert diagnostics.count() == 0

    def test_add_error(self):
        diagnostics = self.create_diagnostics()

        assert diagnostics.count() == 1
        assert diagnostics.has_errors is True

    def test_error_fields(self):
        error = self.create_diagnostics().errors[0]

        assert error.line == 1
        assert error.column == 7
        assert error.content == "S -> a@b"
        assert error.code == ErrorCode.INVALID_SYMBOL
        assert error.message == "Invalid symbol"
        assert error.suggestion == "Remove invalid symbol"

    def test_error_to_dict(self):
        error = self.create_diagnostics().errors[0]

        assert error.to_dict() == {
            "line": 1,
            "column": 7,
            "code": "INVALID_SYMBOL",
            "content": "S -> a@b",
            "message": "Invalid symbol",
            "suggestion": "Remove invalid symbol",
        }

    def test_json_serialization(self):
        diagnostics = self.create_diagnostics()
        data = diagnostics.to_dict()

        assert json.loads(json.dumps(data)) == data

    def test_sort_by_line(self):
        diagnostics = Diagnostics()

        for line in [3, 1, 2]:
            diagnostics.add(
                ErrorCode.MISSING_ARROW,
                line,
                1,
                "S a",
                "Missing arrow",
                "Add arrow",
            )

        assert [
            error.line for error in diagnostics.errors
        ] == [1, 2, 3]

    def test_sort_by_column(self):
        diagnostics = Diagnostics()

        for column in [7, 3, 5]:
            diagnostics.add(
                ErrorCode.INVALID_SYMBOL,
                1,
                column,
                "Invalid input",
                "Invalid symbol",
                "Remove symbol",
            )

        assert [
            error.column for error in diagnostics.errors
        ] == [3, 5, 7]

    def test_error_list_independence(self):
        diagnostics = self.create_diagnostics()

        errors = diagnostics.errors
        errors.clear()

        assert diagnostics.count() == 1

    def test_clear_diagnostics(self):
        diagnostics = self.create_diagnostics()
        diagnostics.clear()

        assert diagnostics.errors == []
        assert diagnostics.has_errors is False
        assert diagnostics.count() == 0

    def test_parse_error_instance(self):
        error = self.create_diagnostics().errors[0]

        assert isinstance(error, ParseError)


class TestParserT03:
    """Kiểm thử parser sau khi tích hợp T03."""

    @staticmethod
    def assert_error(
        text: str | None,
        code: ErrorCode,
        start_symbol: str | None = None,
    ) -> ParseError:
        """Kiểm tra kết quả lỗi và trả về lỗi đầu tiên."""
        result = parseGrammar(text, start_symbol)

        assert result.success is False
        assert result.grammar is None
        assert result.errors
        assert result.errors[0].code == code

        return result.errors[0]

    def test_equivalent_formats(self):
        first = parseGrammar(
            "S -> AB | id\nA -> a\nB -> ε"
        )
        second = parseGrammar(
            "  S  →  A B ｜ id\n A → a\n B → ε "
        )

        assert first.success
        assert second.success
        assert first.grammar.to_dict() == second.grammar.to_dict()

    def test_unicode_arrow(self):
        assert parseGrammar("S → a").success

    def test_unicode_pipe(self):
        assert parseGrammar("S → a ｜ b").success

    def test_unicode_whitespace(self):
        assert parseGrammar("S\u00a0→\u00a0a").success

    def test_empty_input(self):
        self.assert_error("", ErrorCode.EMPTY_INPUT)

    def test_whitespace_only(self):
        self.assert_error("   \t\n", ErrorCode.EMPTY_INPUT)

    def test_invalid_input_type(self):
        self.assert_error(None, ErrorCode.INVALID_INPUT_TYPE)

    def test_invalid_symbol(self):
        self.assert_error("S -> a@b", ErrorCode.INVALID_SYMBOL)

    def test_missing_arrow(self):
        self.assert_error("S a", ErrorCode.MISSING_ARROW)

    def test_multiple_arrows(self):
        error = self.assert_error(
            "S -> A → a",
            ErrorCode.MULTIPLE_ARROWS,
        )

        assert error.column == 8

    def test_invalid_lhs(self):
        self.assert_error("a → b", ErrorCode.INVALID_LHS)

    def test_empty_rhs(self):
        self.assert_error("S → ", ErrorCode.EMPTY_RHS)

    def test_empty_production_middle(self):
        error = self.assert_error(
            "S → a ｜ ｜ b",
            ErrorCode.EMPTY_PRODUCTION,
        )

        assert error.column == 9

    def test_empty_production_first(self):
        self.assert_error("S → | a", ErrorCode.EMPTY_PRODUCTION)

    def test_empty_production_last(self):
        self.assert_error("S → a |", ErrorCode.EMPTY_PRODUCTION)

    def test_invalid_epsilon(self):
        self.assert_error("S → aε", ErrorCode.INVALID_EPSILON)

    def test_undefined_variable(self):
        error = self.assert_error(
            "  S → AB\nA → a",
            ErrorCode.UNDEFINED_VARIABLE,
        )

        assert error.line == 1
        assert error.column == 8

    def test_invalid_start_symbol(self):
        self.assert_error(
            "S → a",
            ErrorCode.INVALID_START_SYMBOL,
            start_symbol="X",
        )

    def test_original_column(self):
        error = self.assert_error(
            "  S  →  a@b",
            ErrorCode.INVALID_SYMBOL,
        )

        assert error.line == 1
        assert error.column == 10

    def test_original_content(self):
        text = "  S  →  a@b"
        error = self.assert_error(text, ErrorCode.INVALID_SYMBOL)

        assert error.content == text

    def test_blank_line_position(self):
        error = self.assert_error(
            "S → a\n\nA → @",
            ErrorCode.INVALID_SYMBOL,
        )

        assert error.line == 3
        assert error.column == 5

    def test_multiple_invalid_symbols(self):
        result = parseGrammar("S → a@#")

        assert not result.success
        assert len(result.errors) == 2
        assert all(
            error.code == ErrorCode.INVALID_SYMBOL
            for error in result.errors
        )
        assert [
            error.column for error in result.errors
        ] == [6, 7]

    def test_multiple_error_lines(self):
        result = parseGrammar(
            "S → @\n"
            "A b\n"
            "B →\n"
            "a → b\n"
            "C → a || b"
        )

        expected = [
            (1, ErrorCode.INVALID_SYMBOL),
            (2, ErrorCode.MISSING_ARROW),
            (3, ErrorCode.EMPTY_RHS),
            (4, ErrorCode.INVALID_LHS),
            (5, ErrorCode.EMPTY_PRODUCTION),
        ]

        assert not result.success
        assert [
            (error.line, error.code)
            for error in result.errors
        ] == expected

    def test_very_short_inputs(self):
        cases = {
            "S": ErrorCode.MISSING_ARROW,
            "ε": ErrorCode.MISSING_ARROW,
            "|": ErrorCode.MISSING_ARROW,
            "→": ErrorCode.INVALID_LHS,
            "@": ErrorCode.INVALID_SYMBOL,
        }

        for text, code in cases.items():
            self.assert_error(text, code)

    def test_valid_json(self):
        result = parseGrammar("S → id ｜ ε")

        expected = {
            "success": True,
            "grammar": {
                "variables": ["S"],
                "terminals": ["id"],
                "productions": {
                    "S": [[], ["id"]],
                },
                "start_symbol": "S",
            },
            "errors": [],
        }

        assert json.loads(json.dumps(result.to_dict())) == expected

    def test_invalid_json(self):
        text = "S → a@b"
        result = parseGrammar(text)
        data = json.loads(json.dumps(result.to_dict()))

        assert data["success"] is False
        assert data["grammar"] is None
        assert len(data["errors"]) == 1

        error = data["errors"][0]

        assert set(error) == {
            "line",
            "column",
            "code",
            "content",
            "message",
            "suggestion",
        }
        assert error["code"] == "INVALID_SYMBOL"
        assert error["line"] == 1
        assert error["column"] == 6
        assert error["content"] == text
        assert error["message"]
        assert error["suggestion"]

    def test_line_endings(self):
        first = parseGrammar("S -> A\nA -> a")
        second = parseGrammar("S -> A\r\nA -> a")
        third = parseGrammar("S -> A\rA -> a")

        assert first.success
        assert second.success
        assert third.success
        assert first.to_dict() == second.to_dict() == third.to_dict()

    def test_no_cascading_start_error(self):
        result = parseGrammar("S → a@b")

        assert not result.success
        assert len(result.errors) == 1
        assert result.errors[0].code == ErrorCode.INVALID_SYMBOL
