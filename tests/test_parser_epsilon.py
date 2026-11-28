"""Kiểm thử Parser CFG và removeEpsilon cho T05."""

from collections import deque
import copy
import json

import pytest

from app.algorithms.cnf import addFreshStart, removeEpsilon
from app.models.grammar import EPSILON, Grammar
from app.services.diagnostics import ErrorCode
from app.services.parser import parseGrammar


def _parse_valid(text, start_symbol=None):
    result = parseGrammar(text, start_symbol=start_symbol)
    assert result.success, result.errors
    assert result.grammar is not None
    assert result.errors == []
    return result.grammar


def _serialize_grammar(grammar):
    lines = []
    # Đưa ký hiệu bắt đầu lên dòng đầu để parser giữ đúng start_symbol mặc định.
    ordered_lhs = sorted(
        grammar.productions.keys(),
        key=lambda var: (0 if var == grammar.start_symbol else 1, var),
    )

    for lhs in ordered_lhs:
        rules = sorted(grammar.productions[lhs])
        parts = ["ε" if rhs == EPSILON else " ".join(rhs) for rhs in rules]
        lines.append(f"{lhs} -> {' | '.join(parts)}")

    return "\n".join(lines)


def _derive_bounded_language(grammar, max_len=4, max_steps=11, max_states=5000):
    """Sinh các chuỗi terminal độ dài <= max_len bằng BFS dẫn xuất trái nhất."""
    start = (grammar.start_symbol,)
    queue = deque([(start, 0)])
    visited = {start}
    language = set()

    while queue and len(visited) < max_states:
        sentential, steps = queue.popleft()

        var_idx = None
        for idx, sym in enumerate(sentential):
            if sym in grammar.variables:
                var_idx = idx
                break

        if var_idx is None:
            if len(sentential) <= max_len:
                language.add(sentential)
            continue

        if steps >= max_steps:
            continue

        var = sentential[var_idx]
        for rhs in grammar.get_productions(var):
            next_form = sentential[:var_idx] + rhs + sentential[var_idx + 1:]
            num_terminals = sum(1 for s in next_form if s in grammar.terminals)
            if num_terminals > max_len or len(next_form) > max_len + 4:
                continue

            if next_form not in visited:
                visited.add(next_form)
                queue.append((next_form, steps + 1))

    return language


def _assert_epsilon_invariants(original, result):
    new_grammar = result.grammar
    new_start = new_grammar.start_symbol

    for lhs, rules in new_grammar.productions.items():
        if lhs != new_start:
            assert EPSILON not in rules, f"Còn luật ε ở biến {lhs}"

    has_start_eps = EPSILON in new_grammar.get_productions(new_start)
    if has_start_eps:
        assert original.start_symbol in result.nullable_variables
        assert result.log.preserves_epsilon
        for rules in new_grammar.productions.values():
            for rhs in rules:
                assert new_start not in rhs
    else:
        assert not result.log.preserves_epsilon


class TestParserValidMatrix:
    """Kiểm thử các trường hợp hợp lệ và biên của Parser CFG."""

    def test_pv01_valid_multiline_same_lhs_and_duplicates(self):
        grammar = _parse_valid(
            "S -> id | id\n"
            "S -> num | ε\n"
            "S -> id | ε"
        )

        assert grammar.variables == {"S"}
        assert grammar.terminals == {"id", "num"}
        assert grammar.production_count() == 3
        assert grammar.productions["S"] == {("id",), ("num",), EPSILON}

    def test_pv02_multichar_terminals_id_and_num_with_spaces(self):
        grammar = _parse_valid(
            "S -> A id B num\n"
            "A -> id\n"
            "B -> num"
        )

        assert grammar.terminals == {"id", "num"}
        assert grammar.productions["S"] == {("A", "id", "B", "num")}

    def test_pv03_multichar_terminals_adjacent_greedy_and_spaced(self):
        greedy = _parse_valid("S -> idnum | mid | AidB\nA -> a\nB -> b")
        spaced = _parse_valid("S -> i d | n u m")

        assert greedy.productions["S"] == {
            ("id", "num"),
            ("m", "id"),
            ("A", "id", "B"),
        }
        assert spaced.terminals == {"i", "d", "n", "u", "m"}
        assert spaced.productions["S"] == {("i", "d"), ("n", "u", "m")}

    def test_pv04_digit_terminals_and_complex_variables(self):
        grammar = _parse_valid(
            "S0 -> 0 S0 1 | A1'\n"
            "A1' -> B2'' | ε\n"
            "B2'' -> 0 | 1"
        )

        assert grammar.variables == {"S0", "A1'", "B2''"}
        assert grammar.terminals == {"0", "1"}
        assert grammar.start_symbol == "S0"
        assert grammar.productions["S0"] == {("0", "S0", "1"), ("A1'",)}

    def test_pv05_blank_lines_and_line_endings(self):
        lf = _parse_valid("\n\nS -> AB\n\nA -> id\n\nB -> num\n\n")
        crlf = _parse_valid("\r\nS -> AB\r\n\r\nA -> id\r\nB -> num\r\n")
        cr = _parse_valid("\rS -> AB\r\rA -> id\rB -> num\r")

        assert lf.to_dict() == crlf.to_dict() == cr.to_dict()

    def test_pv06_unicode_and_whitespace_normalization(self):
        ascii_g = _parse_valid("S -> A B | id | ε\nA -> num\nB -> a")
        unicode_g = _parse_valid(
            "\t S \u00a0→\u00a0 A   B ｜ id ｜ ε \n"
            "  A → num\t\n"
            "B → a  "
        )

        assert ascii_g.to_dict() == unicode_g.to_dict()

    def test_pv07_default_start_symbol_first_lhs(self):
        grammar = _parse_valid("\n   \nE -> id\nS -> num")
        assert grammar.start_symbol == "E"

    def test_pv08_custom_start_symbol_with_spaces(self):
        grammar = _parse_valid("S -> A\nA -> id", start_symbol="  A  ")
        assert grammar.start_symbol == "A"

    def test_pv09_forward_and_mutual_references(self):
        grammar = _parse_valid(
            "S -> B\n"
            "B -> A\n"
            "A -> S | id"
        )

        assert grammar.variables == {"S", "A", "B"}
        assert grammar.production_count() == 4

    def test_pv10_variable_prime_then_digit_boundary(self):
        # Regex biến là [A-Z][0-9]*'* nên A'1 tách thành biến A' và terminal 1.
        grammar = _parse_valid("S -> A'1\nA' -> id")

        assert grammar.variables == {"S", "A'"}
        assert grammar.terminals == {"1", "id"}
        assert grammar.productions["S"] == {("A'", "1")}


class TestParserInvalidMatrix:
    """Kiểm thử phát hiện lỗi cú pháp và vị trí dòng/cột của Parser CFG."""

    @pytest.mark.parametrize("text", ["", "   ", "\t\r\n", "\n\n"])
    def test_pi01_empty_and_whitespace_inputs(self, text):
        result = parseGrammar(text)

        assert not result.success
        assert result.grammar is None
        assert len(result.errors) == 1
        assert result.errors[0].code == ErrorCode.EMPTY_INPUT
        assert result.errors[0].line == 1

    @pytest.mark.parametrize("bad_input", [None, 123, ["S -> a"], {"S": "a"}])
    def test_pi02_invalid_input_types(self, bad_input):
        result = parseGrammar(bad_input)

        assert not result.success
        assert result.grammar is None
        assert result.errors[0].code == ErrorCode.INVALID_INPUT_TYPE

    def test_pi03_missing_arrow_and_line_number(self):
        result = parseGrammar("S -> a\nA b")

        assert not result.success
        assert result.grammar is None
        assert len(result.errors) == 1
        assert result.errors[0].code == ErrorCode.MISSING_ARROW
        assert result.errors[0].line == 2
        assert result.errors[0].content == "A b"

    def test_pi04_multiple_arrows_original_column(self):
        text = "  S  →  A  →  a"
        result = parseGrammar(text)

        assert not result.success
        assert len(result.errors) == 1
        assert result.errors[0].code == ErrorCode.MULTIPLE_ARROWS
        assert result.errors[0].line == 1
        assert result.errors[0].column == 12
        assert result.errors[0].content == text

    @pytest.mark.parametrize(
        "line",
        ["a -> b", "id -> a", "AB -> a", "-> a", "ε -> a"],
    )
    def test_pi05_invalid_lhs_variants(self, line):
        result = parseGrammar(line)

        assert not result.success
        assert result.errors[0].code == ErrorCode.INVALID_LHS
        assert result.errors[0].line == 1

    @pytest.mark.parametrize("line", ["S ->", "S →   "])
    def test_pi06_empty_rhs(self, line):
        result = parseGrammar(line)

        assert not result.success
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
    def test_pi07_empty_production_variants(self, line, expected_count):
        result = parseGrammar(line)

        assert not result.success
        assert len(result.errors) == expected_count
        assert all(err.code == ErrorCode.EMPTY_PRODUCTION for err in result.errors)

    @pytest.mark.parametrize(
        "line",
        [
            "S -> aε",
            "S -> εa",
            "S -> A ε B\nA -> a\nB -> b",
            "S -> ε ε",
        ],
    )
    def test_pi08_invalid_epsilon_combinations(self, line):
        result = parseGrammar(line)

        assert not result.success
        assert any(err.code == ErrorCode.INVALID_EPSILON for err in result.errors)

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
    def test_pi09_invalid_symbols_and_unsupported_operators(self, line, bad_char):
        result = parseGrammar(line)

        assert not result.success
        assert result.grammar is None
        assert result.errors[0].code == ErrorCode.INVALID_SYMBOL
        assert bad_char in result.errors[0].message
        assert result.errors[0].suggestion

    def test_pi10_undefined_variable_multiple_occurrences(self):
        result = parseGrammar("S -> B B\nA -> B")

        assert not result.success
        assert len(result.errors) == 3
        assert all(err.code == ErrorCode.UNDEFINED_VARIABLE for err in result.errors)
        assert [(err.line, err.column) for err in result.errors] == [
            (1, 6),
            (1, 8),
            (2, 6),
        ]

    def test_pi11_secondary_undefined_variable_when_decl_line_broken(self):
        result = parseGrammar("S -> A\nA -> @")

        assert not result.success
        assert [(err.line, err.code) for err in result.errors] == [
            (1, ErrorCode.UNDEFINED_VARIABLE),
            (2, ErrorCode.INVALID_SYMBOL),
        ]

    @pytest.mark.parametrize("bad_start", ["X", "", "   ", 123])
    def test_pi12_invalid_start_symbol_variants(self, bad_start):
        result = parseGrammar("S -> a", start_symbol=bad_start)

        assert not result.success
        assert len(result.errors) == 1
        assert result.errors[0].code == ErrorCode.INVALID_START_SYMBOL

    def test_pi13_multiline_errors_with_blank_lines_sorted(self):
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

        assert not result.success
        assert [(err.line, err.code) for err in result.errors] == [
            (1, ErrorCode.INVALID_SYMBOL),
            (3, ErrorCode.MISSING_ARROW),
            (5, ErrorCode.EMPTY_RHS),
            (6, ErrorCode.INVALID_LHS),
            (8, ErrorCode.EMPTY_PRODUCTION),
        ]

    def test_pi14_original_column_mapping_after_normalization(self):
        text = "   S   →  id  ｜  @"
        result = parseGrammar(text)

        assert not result.success
        assert len(result.errors) == 1
        assert result.errors[0].code == ErrorCode.INVALID_SYMBOL
        assert result.errors[0].line == 1
        assert result.errors[0].column == text.index("@") + 1

    def test_pi15_all_eleven_error_codes_covered(self):
        samples = [
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

        seen = set()
        for raw_text, start, expected_code in samples:
            result = parseGrammar(raw_text, start_symbol=start)
            assert not result.success
            assert result.errors[0].code == expected_code
            seen.add(result.errors[0].code)

            payload = json.loads(json.dumps(result.to_dict()))
            assert not payload["success"]
            assert payload["errors"][0]["code"] == expected_code.value

        assert seen == set(ErrorCode)


class TestRemoveEpsilonMatrix:
    """Kiểm thử loại bỏ ε-production và tạo biến bắt đầu mới."""

    def test_re01_direct_epsilon_no_fresh_start(self):
        grammar = _parse_valid("S -> id A\nA -> num | ε")
        result = removeEpsilon(grammar)

        assert result.nullable_variables == {"A"}
        assert result.grammar.start_symbol == "S"
        assert not result.log.fresh_start_created
        assert result.grammar.productions == {
            "S": {("id", "A"), ("id",)},
            "A": {("num",)},
        }
        _assert_epsilon_invariants(grammar, result)

    def test_re02_indirect_epsilon_four_levels(self):
        grammar = _parse_valid(
            "S -> A\n"
            "A -> B\n"
            "B -> C\n"
            "C -> D\n"
            "D -> a | ε"
        )
        result = removeEpsilon(grammar)

        assert result.nullable_variables == {"D", "C", "B", "A", "S"}
        assert result.log.nullable_iterations == [["D"], ["C"], ["B"], ["A"], ["S"]]
        assert result.grammar.start_symbol == "S0"
        assert result.grammar.productions["S0"] == {("S",), EPSILON}
        _assert_epsilon_invariants(grammar, result)

    def test_re03_consecutive_four_nullables_exponential_and_no_duplicates(self):
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

    def test_re04_duplicate_nullable_same_var_deduplication(self):
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

    def test_re05_cycle_three_vars_with_epsilon(self):
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

    def test_re06_cycle_three_vars_without_epsilon(self):
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

    def test_re07_preserve_s_epsilon_when_s_not_on_rhs(self):
        grammar = _parse_valid(
            "S -> A B\n"
            "A -> id | ε\n"
            "B -> num | ε"
        )
        result = removeEpsilon(grammar)

        assert result.grammar.start_symbol == "S0"
        assert result.log.preserves_epsilon
        assert result.grammar.productions["S0"] == {("S",), EPSILON}
        assert result.grammar.productions["S"] == {("A", "B"), ("A",), ("B",)}
        _assert_epsilon_invariants(grammar, result)

    def test_re08_preserve_s_epsilon_when_s_on_rhs(self):
        grammar = _parse_valid("S -> a S b | ε")
        result = removeEpsilon(grammar)

        assert result.grammar.start_symbol == "S0"
        assert result.grammar.productions == {
            "S0": {("S",), EPSILON},
            "S": {("a", "S", "b"), ("a", "b")},
        }
        _assert_epsilon_invariants(grammar, result)

    def test_re09_create_s0_without_epsilon_when_s_on_rhs_not_nullable(self):
        grammar = _parse_valid("S -> id S | num")
        result = removeEpsilon(grammar)

        assert result.nullable_variables == set()
        assert result.grammar.start_symbol == "S0"
        assert result.log.fresh_start_created
        assert not result.log.preserves_epsilon
        assert result.grammar.productions == {
            "S0": {("S",)},
            "S": {("id", "S"), ("num",)},
        }
        _assert_epsilon_invariants(grammar, result)

    def test_re10_fresh_start_avoids_multi_collision_s0_s1(self):
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

    def test_re11_only_epsilon_language_and_dead_variable_warning(self):
        grammar = _parse_valid("S -> ε")
        result = removeEpsilon(grammar)

        assert result.grammar.start_symbol == "S0"
        assert result.grammar.productions == {"S0": {("S",), EPSILON}}
        assert any("Biến S" in w for w in result.log.warnings)
        _assert_epsilon_invariants(grammar, result)

    def test_re12_empty_grammar_edge_case(self):
        grammar = Grammar()
        result = removeEpsilon(grammar)

        assert result.grammar is not grammar
        assert result.grammar.production_count() == 0
        assert result.log.rule_count_before == 0
        assert result.log.rule_count_after == 0
        assert result.log.warnings

    def test_re13_no_epsilon_no_rhs_start_unchanged(self):
        grammar = _parse_valid("S -> A B\nA -> id\nB -> num")
        result = removeEpsilon(grammar)

        assert result.grammar.to_dict() == grammar.to_dict()
        assert not result.log.fresh_start_created
        assert result.log.added_rules == []
        assert result.log.removed_rules == []


class TestParserEpsilonIntegrationMatrix:
    """Kiểm thử tích hợp luồng parseGrammar -> removeEpsilon."""

    def test_in01_equivalent_formatted_inputs_produce_identical_epsilon_output(self):
        text_ascii = (
            "S -> A B | id\n"
            "A -> a A | ε\n"
            "B -> num | ε"
        )
        text_unicode = (
            "\r\n  S \u00a0→\u00a0 A   B ｜ id ｜ id \r\n"
            "\r\n"
            "\tA → a A ｜ ε\r\n"
            "B → num\r\n"
            "B → ε\r\n"
        )

        r1 = removeEpsilon(_parse_valid(text_ascii))
        r2 = removeEpsilon(_parse_valid(text_unicode))

        assert r1.to_dict() == r2.to_dict()

    def test_in02_multichar_id_num_preserved_through_remove_epsilon(self):
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
    def test_in03_roundtrip_serialize_back_to_parser(self, text):
        original = _parse_valid(text)
        eps_result = removeEpsilon(original)

        serialized = _serialize_grammar(eps_result.grammar)
        reparsed = parseGrammar(
            serialized,
            start_symbol=eps_result.grammar.start_symbol,
        )

        assert reparsed.success, (serialized, reparsed.errors)
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
    def test_in04_language_preservation_with_multichar_and_epsilon(self, text):
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

    def test_in05_pipeline_input_immutability(self):
        parsed = _parse_valid(
            "S -> A B | id S | ε\n"
            "A -> id | ε\n"
            "B -> num | ε"
        )
        snapshot = copy.deepcopy(parsed)
        snapshot_dict = parsed.to_dict()

        addFreshStart(parsed)
        removeEpsilon(parsed)

        assert parsed.variables == snapshot.variables
        assert parsed.terminals == snapshot.terminals
        assert parsed.productions == snapshot.productions
        assert parsed.start_symbol == snapshot.start_symbol
        assert parsed.to_dict() == snapshot_dict

    def test_in06_pipeline_determinism_repeated_runs(self):
        text = (
            "S -> A B C\n"
            "A -> id | ε\n"
            "B -> num | ε\n"
            "C -> 0 | ε"
        )

        outputs = [removeEpsilon(_parse_valid(text)).to_dict() for _ in range(5)]
        assert all(item == outputs[0] for item in outputs[1:])

    def test_in07_failed_parse_blocks_remove_epsilon_safely(self):
        parse_result = parseGrammar("S -> a@b")

        assert not parse_result.success
        assert parse_result.grammar is None

        with pytest.raises(TypeError):
            removeEpsilon(parse_result.grammar)

    def test_in08_existing_variant_and_self_unit_contract_for_t06(self):
        grammar = _parse_valid(
            "S -> A B | A\n"
            "A -> S A | id | ε\n"
            "B -> num | ε"
        )
        result = removeEpsilon(grammar)

        # Luật S -> A có sẵn từ đầu nên không ghi vào added_rules.
        added_pairs = {(c.lhs, c.rhs) for c in result.log.added_rules}
        assert ("S", ("A",)) not in added_pairs

        # Giữ luật tự trỏ A -> A để bước removeUnit (T06) xử lý.
        assert ("A",) in result.grammar.productions["A"]
        _assert_epsilon_invariants(grammar, result)
