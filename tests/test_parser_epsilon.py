"""Bộ kiểm thử ma trận và tích hợp cho Parser CFG (T02/T03) và removeEpsilon (T04) — Task T05."""

from collections import deque
import copy
import json

import pytest

from app.algorithms.cnf import (
    RemoveEpsilonResult,
    addFreshStart,
    removeEpsilon,
)
from app.models.grammar import EPSILON, Grammar
from app.services.diagnostics import ErrorCode
from app.services.parser import parseGrammar


def _parse_valid(text: str, start_symbol: str | None = None) -> Grammar:
    """Phân tích một văn phạm hợp lệ và khẳng định thành công."""
    result = parseGrammar(text, start_symbol=start_symbol)
    assert result.success is True, result.errors
    assert result.grammar is not None
    assert result.errors == []
    return result.grammar


def _serialize_grammar(grammar: Grammar) -> str:
    """Chuyển Grammar thành văn bản CFG chuẩn để kiểm chứng round-trip."""
    lines: list[str] = []
    ordered_lhs = sorted(
        grammar.productions.keys(),
        key=lambda var: (0 if var == grammar.start_symbol else 1, var),
    )

    for lhs in ordered_lhs:
        rules = sorted(grammar.productions[lhs])
        formatted_alternatives = [
            "ε" if rhs == EPSILON else " ".join(rhs)
            for rhs in rules
        ]
        lines.append(f"{lhs} -> {' | '.join(formatted_alternatives)}")

    return "\n".join(lines)


def _derive_bounded_language(
    grammar: Grammar,
    max_len: int = 4,
    max_steps: int = 11,
    max_states: int = 5000,
) -> set[tuple[str, ...]]:
    """Sinh tập chuỗi terminal độ dài <= max_len bằng BFS dẫn xuất trái nhất."""
    start_form: tuple[str, ...] = (grammar.start_symbol,)
    queue: deque[tuple[tuple[str, ...], int]] = deque([(start_form, 0)])
    visited: set[tuple[str, ...]] = {start_form}
    language: set[tuple[str, ...]] = set()

    while queue and len(visited) < max_states:
        sentential, steps = queue.popleft()

        first_var_index = next(
            (
                index
                for index, symbol in enumerate(sentential)
                if symbol in grammar.variables
            ),
            None,
        )

        if first_var_index is None:
            if len(sentential) <= max_len:
                language.add(sentential)
            continue

        if steps >= max_steps:
            continue

        variable = sentential[first_var_index]
        for rhs in grammar.get_productions(variable):
            next_form = (
                sentential[:first_var_index]
                + rhs
                + sentential[first_var_index + 1:]
            )
            terminal_count = sum(
                1 for sym in next_form if sym in grammar.terminals
            )
            if terminal_count > max_len or len(next_form) > max_len + 4:
                continue

            if next_form not in visited:
                visited.add(next_form)
                queue.append((next_form, steps + 1))

    return language


def _assert_epsilon_invariants(
    original: Grammar,
    result: RemoveEpsilonResult,
) -> None:
    """Kiểm tra bất biến hậu điều kiện sau khi loại bỏ ε-production."""
    new_grammar = result.grammar
    new_start = new_grammar.start_symbol

    for lhs, rules in new_grammar.productions.items():
        if lhs != new_start:
            assert EPSILON not in rules, (
                f"Phát hiện luật ε không hợp lệ ở biến {lhs}."
            )

    has_start_epsilon = EPSILON in new_grammar.get_productions(new_start)
    if has_start_epsilon:
        assert original.start_symbol in result.nullable_variables
        assert result.log.preserves_epsilon is True
        for rules in new_grammar.productions.values():
            for rhs in rules:
                assert new_start not in rhs
    else:
        assert result.log.preserves_epsilon is False


# ============================================================================
# NHÓM A: MA TRẬN PARSER HỢP LỆ & BIÊN HỢP LỆ (TC-PV01 .. TC-PV10)
# ============================================================================


class TestParserValidMatrix:
    """Kiểm thử các trường hợp hợp lệ và biên hợp lệ của Parser CFG."""

    def test_pv01_valid_multiline_same_lhs_and_duplicates(self) -> None:
        """TC-PV01: Gộp nhiều dòng cùng biến và loại bỏ luật trùng lặp."""
        grammar = _parse_valid(
            "S -> id | id\n"
            "S -> num | ε\n"
            "S -> id | ε"
        )

        assert grammar.variables == {"S"}
        assert grammar.terminals == {"id", "num"}
        assert grammar.production_count() == 3
        assert grammar.productions["S"] == {("id",), ("num",), EPSILON}

    def test_pv02_multichar_terminals_id_and_num_with_spaces(self) -> None:
        """TC-PV02: Terminal nhiều ký tự id/num xen kẽ biến và khoảng trắng."""
        grammar = _parse_valid(
            "S -> A id B num\n"
            "A -> id\n"
            "B -> num"
        )

        assert grammar.terminals == {"id", "num"}
        assert grammar.productions["S"] == {("A", "id", "B", "num")}

    def test_pv03_multichar_terminals_adjacent_greedy_and_spaced(self) -> None:
        """TC-PV03: Kiểm chứng tách tham lam id/num vs tách rời bằng khoảng trắng."""
        greedy = _parse_valid("S -> idnum | mid | AidB\nA -> a\nB -> b")
        spaced = _parse_valid("S -> i d | n u m")

        assert greedy.productions["S"] == {
            ("id", "num"),
            ("m", "id"),
            ("A", "id", "B"),
        }
        assert spaced.terminals == {"i", "d", "n", "u", "m"}
        assert spaced.productions["S"] == {("i", "d"), ("n", "u", "m")}

    def test_pv04_digit_terminals_and_complex_variables(self) -> None:
        """TC-PV04: Terminal chữ số 0/1 cùng biến chứa số và dấu nháy."""
        grammar = _parse_valid(
            "S0 -> 0 S0 1 | A1'\n"
            "A1' -> B2'' | ε\n"
            "B2'' -> 0 | 1"
        )

        assert grammar.variables == {"S0", "A1'", "B2''"}
        assert grammar.terminals == {"0", "1"}
        assert grammar.start_symbol == "S0"
        assert grammar.productions["S0"] == {("0", "S0", "1"), ("A1'",)}

    def test_pv05_blank_lines_and_line_endings(self) -> None:
        """TC-PV05: Dòng rỗng xen kẽ và các kiểu xuống dòng LF/CRLF/CR tương đương."""
        lf = _parse_valid("\n\nS -> AB\n\nA -> id\n\nB -> num\n\n")
        crlf = _parse_valid("\r\nS -> AB\r\n\r\nA -> id\r\nB -> num\r\n")
        cr = _parse_valid("\rS -> AB\r\rA -> id\rB -> num\r")

        assert lf.to_dict() == crlf.to_dict() == cr.to_dict()

    def test_pv06_unicode_and_whitespace_normalization(self) -> None:
        """TC-PV06: Chuẩn hóa mũi tên Unicode, dấu ｜, tab và khoảng trắng NBSP."""
        ascii_g = _parse_valid("S -> A B | id | ε\nA -> num\nB -> a")
        unicode_g = _parse_valid(
            "\t S \u00a0→\u00a0 A   B ｜ id ｜ ε \n"
            "  A → num\t\n"
            "B → a  "
        )

        assert ascii_g.to_dict() == unicode_g.to_dict()

    def test_pv07_default_start_symbol_first_lhs(self) -> None:
        """TC-PV07: Start symbol mặc định là biến vế trái đầu tiên dù có dòng trống."""
        grammar = _parse_valid("\n   \nE -> id\nS -> num")

        assert grammar.start_symbol == "E"

    def test_pv08_custom_start_symbol_with_spaces(self) -> None:
        """TC-PV08: Start symbol truyền tay có khoảng trắng thừa được strip hợp lệ."""
        grammar = _parse_valid("S -> A\nA -> id", start_symbol="  A  ")

        assert grammar.start_symbol == "A"

    def test_pv09_forward_and_mutual_references(self) -> None:
        """TC-PV09: Tham chiếu tiến và đệ quy tương hỗ giữa nhiều biến."""
        grammar = _parse_valid(
            "S -> B\n"
            "B -> A\n"
            "A -> S | id"
        )

        assert grammar.variables == {"S", "A", "B"}
        assert grammar.production_count() == 4

    def test_pv10_variable_prime_then_digit_boundary(self) -> None:
        """TC-PV10: Biên regex biến — A'1 tách thành biến A' và terminal 1."""
        grammar = _parse_valid("S -> A'1\nA' -> id")

        assert grammar.variables == {"S", "A'"}
        assert grammar.terminals == {"1", "id"}
        assert grammar.productions["S"] == {("A'", "1")}


# ============================================================================
# NHÓM B: MA TRẬN PARSER KHÔNG HỢP LỆ & BÁO LỖI THEO DÒNG (TC-PI01 .. TC-PI15)
# ============================================================================


class TestParserInvalidMatrix:
    """Kiểm thử các lỗi cú pháp, ánh xạ dòng/cột và biên lỗi của Parser CFG."""

    @pytest.mark.parametrize("text", ["", "   ", "\t\r\n", "\n\n"])
    def test_pi01_empty_and_whitespace_inputs(self, text: str) -> None:
        """TC-PI01: Đầu vào rỗng hoặc chỉ khoảng trắng trả EMPTY_INPUT."""
        result = parseGrammar(text)

        assert result.success is False
        assert result.grammar is None
        assert len(result.errors) == 1
        assert result.errors[0].code == ErrorCode.EMPTY_INPUT
        assert result.errors[0].line == 1

    @pytest.mark.parametrize("bad_input", [None, 123, ["S -> a"], {"S": "a"}])
    def test_pi02_invalid_input_types(self, bad_input: object) -> None:
        """TC-PI02: Đầu vào sai kiểu trả INVALID_INPUT_TYPE, không crash."""
        result = parseGrammar(bad_input)  # type: ignore[arg-type]

        assert result.success is False
        assert result.grammar is None
        assert result.errors[0].code == ErrorCode.INVALID_INPUT_TYPE

    def test_pi03_missing_arrow_and_line_number(self) -> None:
        """TC-PI03: Phát hiện thiếu mũi tên ở đúng dòng 2."""
        result = parseGrammar("S -> a\nA b")

        assert result.success is False
        assert result.grammar is None
        assert len(result.errors) == 1
        assert result.errors[0].code == ErrorCode.MISSING_ARROW
        assert result.errors[0].line == 2
        assert result.errors[0].content == "A b"

    def test_pi04_multiple_arrows_original_column(self) -> None:
        """TC-PI04: Phát hiện thừa mũi tên và ánh xạ đúng cột gốc sau chuẩn hóa."""
        text = "  S  →  A  →  a"
        result = parseGrammar(text)

        assert result.success is False
        assert len(result.errors) == 1
        assert result.errors[0].code == ErrorCode.MULTIPLE_ARROWS
        assert result.errors[0].line == 1
        assert result.errors[0].column == 12
        assert result.errors[0].content == text

    @pytest.mark.parametrize(
        "line",
        [
            "a -> b",
            "id -> a",
            "AB -> a",
            "-> a",
            "ε -> a",
        ],
    )
    def test_pi05_invalid_lhs_variants(self, line: str) -> None:
        """TC-PI05: Các dạng vế trái sai (terminal, id, 2 biến, rỗng, ε)."""
        result = parseGrammar(line)

        assert result.success is False
        assert result.errors[0].code == ErrorCode.INVALID_LHS
        assert result.errors[0].line == 1

    @pytest.mark.parametrize("line", ["S ->", "S →   "])
    def test_pi06_empty_rhs(self, line: str) -> None:
        """TC-PI06: Vế phải rỗng trả EMPTY_RHS."""
        result = parseGrammar(line)

        assert result.success is False
        assert result.errors[0].code == ErrorCode.EMPTY_RHS

    @pytest.mark.parametrize(
        "line,expected_count",
        [
            ("S -> | a", 1),
            ("S -> a |", 1),
            ("S -> a || b", 1),
            ("S → a ｜ ｜ b", 1),
            ("S -> | a |", 2),
        ],
    )
    def test_pi07_empty_production_variants(
        self,
        line: str,
        expected_count: int,
    ) -> None:
        """TC-PI07: Production rỗng ở đầu, giữa, cuối và nhiều dấu | thừa."""
        result = parseGrammar(line)

        assert result.success is False
        assert len(result.errors) == expected_count
        assert all(
            err.code == ErrorCode.EMPTY_PRODUCTION
            for err in result.errors
        )

    @pytest.mark.parametrize(
        "line",
        [
            "S -> aε",
            "S -> εa",
            "S -> A ε B\nA -> a\nB -> b",
            "S -> ε ε",
        ],
    )
    def test_pi08_invalid_epsilon_combinations(self, line: str) -> None:
        """TC-PI08: Epsilon không đứng riêng trả INVALID_EPSILON."""
        result = parseGrammar(line)

        assert result.success is False
        assert any(
            err.code == ErrorCode.INVALID_EPSILON
            for err in result.errors
        )

    @pytest.mark.parametrize(
        "line,bad_char",
        [
            ("S -> a@b", "@"),
            ("S -> id#num", "#"),
            ("S -> a$b", "$"),
            ("S -> a+b", "+"),
            ("S -> a*b", "*"),
            ("S -> (a)", "("),
            ("S -> λ", "λ"),
        ],
    )
    def test_pi09_invalid_symbols_and_unsupported_operators(
        self,
        line: str,
        bad_char: str,
    ) -> None:
        """TC-PI09: Ký hiệu lạ và toán tử chưa hỗ trợ trả INVALID_SYMBOL rõ ràng."""
        result = parseGrammar(line)

        assert result.success is False
        assert result.grammar is None
        assert result.errors[0].code == ErrorCode.INVALID_SYMBOL
        assert bad_char in result.errors[0].message
        assert result.errors[0].suggestion

    def test_pi10_undefined_variable_multiple_occurrences(self) -> None:
        """TC-PI10: Biến chưa khai báo xuất hiện nhiều lần được báo đủ vị trí."""
        result = parseGrammar("S -> B B\nA -> B")

        assert result.success is False
        assert len(result.errors) == 3
        assert all(
            err.code == ErrorCode.UNDEFINED_VARIABLE
            for err in result.errors
        )
        assert [(err.line, err.column) for err in result.errors] == [
            (1, 6),
            (1, 8),
            (2, 6),
        ]

    def test_pi11_secondary_undefined_variable_when_decl_line_broken(self) -> None:
        """TC-PI11: Ghi nhận lỗi thứ cấp UNDEFINED_VARIABLE khi dòng khai báo hỏng."""
        result = parseGrammar("S -> A\nA -> @")

        assert result.success is False
        assert [(err.line, err.code) for err in result.errors] == [
            (1, ErrorCode.UNDEFINED_VARIABLE),
            (2, ErrorCode.INVALID_SYMBOL),
        ]

    @pytest.mark.parametrize("bad_start", ["X", "", "   ", 123])
    def test_pi12_invalid_start_symbol_variants(
        self,
        bad_start: object,
    ) -> None:
        """TC-PI12: Start symbol không tồn tại, rỗng hoặc sai kiểu trả INVALID_START_SYMBOL."""
        result = parseGrammar(
            "S -> a",
            start_symbol=bad_start,  # type: ignore[arg-type]
        )

        assert result.success is False
        assert len(result.errors) == 1
        assert result.errors[0].code == ErrorCode.INVALID_START_SYMBOL

    def test_pi13_multiline_errors_with_blank_lines_sorted(self) -> None:
        """TC-PI13: Nhiều lỗi xen dòng rỗng giữ đúng số dòng gốc và sắp thứ tự."""
        text = (
            "S -> @\n"
            "\n"
            "A b\n"
            "\n"
            "B ->\n"
            "a -> b\n"
            "\n"
            "C -> a || b"
        )
        result = parseGrammar(text)

        assert result.success is False
        assert [(err.line, err.code) for err in result.errors] == [
            (1, ErrorCode.INVALID_SYMBOL),
            (3, ErrorCode.MISSING_ARROW),
            (5, ErrorCode.EMPTY_RHS),
            (6, ErrorCode.INVALID_LHS),
            (8, ErrorCode.EMPTY_PRODUCTION),
        ]

    def test_pi14_original_column_mapping_after_normalization(self) -> None:
        """TC-PI14: Khôi phục cột gốc chính xác khi có khoảng trắng, → và ｜."""
        text = "   S   →  id  ｜  @"
        result = parseGrammar(text)

        assert result.success is False
        assert len(result.errors) == 1
        assert result.errors[0].code == ErrorCode.INVALID_SYMBOL
        assert result.errors[0].line == 1
        assert result.errors[0].column == text.index("@") + 1

    def test_pi15_all_eleven_error_codes_covered(self) -> None:
        """TC-PI15: Xác nhận đủ cả 11 mã lỗi ErrorCode đều kích hoạt & xuất JSON được."""
        samples: list[tuple[object, str | None, ErrorCode]] = [
            ("", None, ErrorCode.EMPTY_INPUT),
            (None, None, ErrorCode.INVALID_INPUT_TYPE),
            ("S -> @", None, ErrorCode.INVALID_SYMBOL),
            ("S a", None, ErrorCode.MISSING_ARROW),
            ("S -> A -> a", None, ErrorCode.MULTIPLE_ARROWS),
            ("a -> b", None, ErrorCode.INVALID_LHS),
            ("S ->", None, ErrorCode.EMPTY_RHS),
            ("S -> a |", None, ErrorCode.EMPTY_PRODUCTION),
            ("S -> aε", None, ErrorCode.INVALID_EPSILON),
            ("S -> A", None, ErrorCode.UNDEFINED_VARIABLE),
            ("S -> a", "Z", ErrorCode.INVALID_START_SYMBOL),
        ]

        seen_codes: set[ErrorCode] = set()
        for raw_text, start, expected_code in samples:
            result = parseGrammar(
                raw_text,  # type: ignore[arg-type]
                start_symbol=start,
            )
            assert result.success is False
            assert result.errors[0].code == expected_code
            seen_codes.add(result.errors[0].code)

            # Kiểm tra xuất JSON không lỗi.
            payload = json.loads(json.dumps(result.to_dict()))
            assert payload["success"] is False
            assert payload["errors"][0]["code"] == expected_code.value

        assert seen_codes == set(ErrorCode)


# ============================================================================
# NHÓM C: MA TRẬN REMOVE EPSILON (TC-RE01 .. TC-RE13)
# ============================================================================


class TestRemoveEpsilonMatrix:
    """Kiểm thử ma trận cho tìm nullable, tạo S0 và loại bỏ ε-production."""

    def test_re01_direct_epsilon_no_fresh_start(self) -> None:
        """TC-RE01: ε trực tiếp ở biến thường, S không nullable và không ở RHS."""
        grammar = _parse_valid("S -> id A\nA -> num | ε")
        result = removeEpsilon(grammar)

        assert result.nullable_variables == {"A"}
        assert result.grammar.start_symbol == "S"
        assert result.log.fresh_start_created is False
        assert result.grammar.productions == {
            "S": {("id", "A"), ("id",)},
            "A": {("num",)},
        }
        _assert_epsilon_invariants(grammar, result)

    def test_re02_indirect_epsilon_four_levels(self) -> None:
        """TC-RE02: Nullable gián tiếp 4 tầng hội tụ đúng từng vòng lặp."""
        grammar = _parse_valid(
            "S -> A\n"
            "A -> B\n"
            "B -> C\n"
            "C -> D\n"
            "D -> a | ε"
        )
        result = removeEpsilon(grammar)

        assert result.nullable_variables == {"D", "C", "B", "A", "S"}
        assert result.log.nullable_iterations == [
            ["D"],
            ["C"],
            ["B"],
            ["A"],
            ["S"],
        ]
        assert result.grammar.start_symbol == "S0"
        assert result.grammar.productions["S0"] == {("S",), EPSILON}
        _assert_epsilon_invariants(grammar, result)

    def test_re03_consecutive_four_nullables_exponential_and_no_duplicates(
        self,
    ) -> None:
        """TC-RE03: 4 biến nullable liên tiếp sinh đúng 2^4 - 1 = 15 biến thể cho S."""
        grammar = _parse_valid(
            "S -> A B C D\n"
            "A -> a | ε\n"
            "B -> b | ε\n"
            "C -> c | ε\n"
            "D -> d | ε"
        )
        result = removeEpsilon(grammar)

        assert result.nullable_variables == {"S", "A", "B", "C", "D"}
        assert len(result.grammar.productions["S"]) == 15
        assert result.grammar.productions["S0"] == {("S",), EPSILON}
        added_pairs = [(c.lhs, c.rhs) for c in result.log.added_rules]
        assert len(added_pairs) == len(set(added_pairs))
        _assert_epsilon_invariants(grammar, result)

    def test_re04_duplicate_nullable_same_var_deduplication(self) -> None:
        """TC-RE04: Chuỗi lặp cùng biến nullable S -> AAAA lọc trùng còn đúng 4 luật."""
        grammar = _parse_valid("S -> A A A A\nA -> id | ε")
        result = removeEpsilon(grammar)

        assert result.grammar.productions["S"] == {
            ("A", "A", "A", "A"),
            ("A", "A", "A"),
            ("A", "A"),
            ("A",),
        }
        assert result.grammar.productions["S0"] == {("S",), EPSILON}
        _assert_epsilon_invariants(grammar, result)

    def test_re05_cycle_three_vars_with_epsilon(self) -> None:
        """TC-RE05: Chu trình 3 biến có ε dừng đúng và sinh đủ biến thể."""
        grammar = _parse_valid(
            "S -> A id\n"
            "A -> B\n"
            "B -> C\n"
            "C -> A | ε"
        )
        result = removeEpsilon(grammar)

        assert result.nullable_variables == {"A", "B", "C"}
        assert result.log.nullable_iterations == [["C"], ["B"], ["A"]]
        assert result.grammar.start_symbol == "S"
        assert result.grammar.productions["S"] == {("A", "id"), ("id",)}
        _assert_epsilon_invariants(grammar, result)

    def test_re06_cycle_three_vars_without_epsilon(self) -> None:
        """TC-RE06: Chu trình 3 biến không có ε dừng ngay, văn phạm không đổi."""
        grammar = _parse_valid(
            "S -> A | id\n"
            "A -> B\n"
            "B -> C\n"
            "C -> A"
        )
        result = removeEpsilon(grammar)

        assert result.nullable_variables == set()
        assert result.grammar.to_dict() == grammar.to_dict()
        assert result.log.added_rules == []
        assert result.log.removed_rules == []

    def test_re07_preserve_s_epsilon_when_s_not_on_rhs(self) -> None:
        """TC-RE07: S sinh ε (không ở RHS) tạo S0 -> S | ε bảo toàn ε."""
        grammar = _parse_valid(
            "S -> A B\n"
            "A -> id | ε\n"
            "B -> num | ε"
        )
        result = removeEpsilon(grammar)

        assert result.grammar.start_symbol == "S0"
        assert result.log.preserves_epsilon is True
        assert result.grammar.productions["S0"] == {("S",), EPSILON}
        assert result.grammar.productions["S"] == {("A", "B"), ("A",), ("B",)}
        _assert_epsilon_invariants(grammar, result)

    def test_re08_preserve_s_epsilon_when_s_on_rhs(self) -> None:
        """TC-RE08: S vừa sinh ε vừa xuất hiện ở RHS -> S0 -> S | ε, S0 không ở RHS."""
        grammar = _parse_valid("S -> a S b | ε")
        result = removeEpsilon(grammar)

        assert result.grammar.start_symbol == "S0"
        assert result.grammar.productions == {
            "S0": {("S",), EPSILON},
            "S": {("a", "S", "b"), ("a", "b")},
        }
        _assert_epsilon_invariants(grammar, result)

    def test_re09_create_s0_without_epsilon_when_s_on_rhs_not_nullable(
        self,
    ) -> None:
        """TC-RE09: S ở RHS nhưng không sinh ε -> tạo S0 -> S, KHÔNG giữ S0 -> ε."""
        grammar = _parse_valid("S -> id S | num")
        result = removeEpsilon(grammar)

        assert result.nullable_variables == set()
        assert result.grammar.start_symbol == "S0"
        assert result.log.fresh_start_created is True
        assert result.log.preserves_epsilon is False
        assert result.grammar.productions == {
            "S0": {("S",)},
            "S": {("id", "S"), ("num",)},
        }
        _assert_epsilon_invariants(grammar, result)

    def test_re10_fresh_start_avoids_multi_collision_s0_s1(self) -> None:
        """TC-RE10: Grammar đã có sẵn S0 và S1 -> tự chọn S2 không trùng tên."""
        grammar = _parse_valid(
            "S -> S0 S1 | ε\n"
            "S0 -> id\n"
            "S1 -> num"
        )
        result = removeEpsilon(grammar)

        assert result.grammar.start_symbol == "S2"
        assert {"S", "S0", "S1", "S2"}.issubset(result.grammar.variables)
        assert result.grammar.productions["S2"] == {("S",), EPSILON}
        _assert_epsilon_invariants(grammar, result)

    def test_re11_only_epsilon_language_and_dead_variable_warning(self) -> None:
        """TC-RE11: Văn phạm chỉ sinh chuỗi rỗng L(G) = {ε} có cảnh báo cho S."""
        grammar = _parse_valid("S -> ε")
        result = removeEpsilon(grammar)

        assert result.grammar.start_symbol == "S0"
        assert result.grammar.productions == {"S0": {("S",), EPSILON}}
        assert any("Biến S" in w for w in result.log.warnings)
        _assert_epsilon_invariants(grammar, result)

    def test_re12_empty_grammar_edge_case(self) -> None:
        """TC-RE12: Văn phạm rỗng không crash và ghi cảnh báo."""
        grammar = Grammar()
        result = removeEpsilon(grammar)

        assert result.grammar is not grammar
        assert result.grammar.production_count() == 0
        assert result.log.rule_count_before == 0
        assert result.log.rule_count_after == 0
        assert result.log.warnings

    def test_re13_no_epsilon_no_rhs_start_unchanged(self) -> None:
        """TC-RE13: Văn phạm sạch không ε và S không ở RHS được giữ nguyên."""
        grammar = _parse_valid("S -> A B\nA -> id\nB -> num")
        result = removeEpsilon(grammar)

        assert result.grammar.to_dict() == grammar.to_dict()
        assert result.log.fresh_start_created is False
        assert result.log.added_rules == []
        assert result.log.removed_rules == []


# ============================================================================
# NHÓM D: TÍCH HỢP ĐẦU–CUỐI PARSER -> REMOVE EPSILON (TC-IN01 .. TC-IN08)
# ============================================================================


class TestParserEpsilonIntegrationMatrix:
    """Kiểm thử luồng tích hợp parseGrammar -> removeEpsilon."""

    def test_in01_equivalent_formatted_inputs_produce_identical_epsilon_output(
        self,
    ) -> None:
        """TC-IN01: Các định dạng nhập tương đương cho cùng output removeEpsilon."""
        text_ascii = (
            "S -> A B | id\n"
            "A -> a A | ε\n"
            "B -> num | ε"
        )
        text_unicode_messy = (
            "\r\n  S \u00a0→\u00a0 A   B ｜ id ｜ id \r\n"
            "\r\n"
            "\tA → a A ｜ ε\r\n"
            "B → num\r\n"
            "B → ε\r\n"
        )

        r1 = removeEpsilon(_parse_valid(text_ascii))
        r2 = removeEpsilon(_parse_valid(text_unicode_messy))

        assert r1.to_dict() == r2.to_dict()

    def test_in02_multichar_id_num_preserved_through_remove_epsilon(
        self,
    ) -> None:
        """TC-IN02: Terminal nhiều ký tự id/num giữ nguyên nguyên khối sau removeEpsilon."""
        grammar = _parse_valid(
            "E -> T A\n"
            "T -> id | num\n"
            "A -> id T A | ε"
        )
        result = removeEpsilon(grammar)

        assert result.grammar.terminals == {"id", "num"}
        assert result.grammar.productions == {
            "E": {("T", "A"), ("T",)},
            "T": {("id",), ("num",)},
            "A": {("id", "T", "A"), ("id", "T")},
        }
        _assert_epsilon_invariants(grammar, result)

    @pytest.mark.parametrize(
        "text",
        [
            "S -> A B\nA -> id | ε\nB -> num | ε",
            "S -> a S b | ε",
            "S -> id S | num",
            "S -> S0 S1 | ε\nS0 -> id\nS1 -> num",
        ],
    )
    def test_in03_roundtrip_serialize_back_to_parser(self, text: str) -> None:
        """TC-IN03: Grammar sau removeEpsilon serialize lại phải parse được 100%."""
        original = _parse_valid(text)
        eps_result = removeEpsilon(original)

        serialized = _serialize_grammar(eps_result.grammar)
        reparsed = parseGrammar(
            serialized,
            start_symbol=eps_result.grammar.start_symbol,
        )

        assert reparsed.success is True, (serialized, reparsed.errors)
        assert reparsed.grammar is not None
        assert reparsed.grammar.to_dict() == eps_result.grammar.to_dict()

    @pytest.mark.parametrize(
        "text",
        [
            "S -> A B\nA -> id A | ε\nB -> num | ε",
            "S -> id S num | ε",
            "S -> id S | num",
            "S -> S0 S1 | ε\nS0 -> a | ε\nS1 -> b",
            "E -> T A\nT -> id | num\nA -> 0 T A | ε",
        ],
    )
    def test_in04_language_preservation_with_multichar_and_epsilon(
        self,
        text: str,
    ) -> None:
        """TC-IN04: Bảo toàn ngôn ngữ L(G') = L(G) với terminal nhiều ký tự và ε."""
        original = _parse_valid(text)
        result = removeEpsilon(original)

        _assert_epsilon_invariants(original, result)

        orig_lang = _derive_bounded_language(original, max_len=4, max_steps=10)
        new_lang = _derive_bounded_language(
            result.grammar,
            max_len=4,
            max_steps=11,
        )

        assert new_lang == orig_lang

    def test_in05_pipeline_input_immutability(self) -> None:
        """TC-IN05: Bất biến đối tượng Grammar xuyên suốt addFreshStart và removeEpsilon."""
        parsed = _parse_valid(
            "S -> A B | id S | ε\n"
            "A -> id | ε\n"
            "B -> num | ε"
        )
        snapshot = copy.deepcopy(parsed)
        snapshot_dict = parsed.to_dict()

        _ = addFreshStart(parsed)
        _ = removeEpsilon(parsed)

        assert parsed.variables == snapshot.variables
        assert parsed.terminals == snapshot.terminals
        assert parsed.productions == snapshot.productions
        assert parsed.start_symbol == snapshot.start_symbol
        assert parsed.to_dict() == snapshot_dict

    def test_in06_pipeline_determinism_repeated_runs(self) -> None:
        """TC-IN06: Chạy lặp 5 lần parseGrammar -> removeEpsilon luôn cho 1 JSON duy nhất."""
        text = (
            "S -> A B C\n"
            "A -> id | ε\n"
            "B -> num | ε\n"
            "C -> 0 | ε"
        )

        outputs = [
            removeEpsilon(_parse_valid(text)).to_dict()
            for _ in range(5)
        ]

        first = outputs[0]
        assert all(item == first for item in outputs[1:])

    def test_in07_failed_parse_blocks_remove_epsilon_safely(self) -> None:
        """TC-IN07: Khi parseGrammar lỗi (grammar=None), removeEpsilon từ chối bằng TypeError."""
        parse_result = parseGrammar("S -> a@b")

        assert parse_result.success is False
        assert parse_result.grammar is None

        with pytest.raises(TypeError):
            removeEpsilon(parse_result.grammar)  # type: ignore[arg-type]

    def test_in08_existing_variant_and_self_unit_contract_for_t06(self) -> None:
        """TC-IN08: Không log thừa luật có sẵn và giữ đúng unit rule cho T06."""
        grammar = _parse_valid(
            "S -> A B | A\n"
            "A -> S A | id | ε\n"
            "B -> num | ε"
        )
        result = removeEpsilon(grammar)

        # S -> A đã có sẵn nên không được báo là luật mới thêm.
        added_pairs = {(c.lhs, c.rhs) for c in result.log.added_rules}
        assert ("S", ("A",)) not in added_pairs

        # A -> A (self-loop unit) được giữ đúng theo Định lý 5.3 để T06 xử lý.
        assert ("A",) in result.grammar.productions["A"]
        _assert_epsilon_invariants(grammar, result)
