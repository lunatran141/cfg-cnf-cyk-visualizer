"""Kiểm thử đơn vị cho tìm biến nullable và loại bỏ ε-production (T04)."""

from collections import deque
import copy

import pytest

from app.algorithms.cnf import (
    EpsilonStepLog,
    RemoveEpsilonResult,
    RuleChange,
    addFreshStart,
    find_nullable_variables,
    generate_fresh_start_symbol,
    removeEpsilon,
)
from app.models.grammar import EPSILON, Grammar
from app.services.parser import parseGrammar
from app.services.tokenizer import tokenize_line


def _parse_valid(text: str, start_symbol: str | None = None) -> Grammar:
    """Phân tích nhanh một văn phạm hợp lệ để phục vụ kiểm thử."""
    result = parseGrammar(text, start_symbol=start_symbol)
    assert result.success and result.grammar is not None, result.errors
    return result.grammar


def _derive_terminal_strings(
    grammar: Grammar,
    max_len: int = 5,
    max_steps: int = 12,
    max_states: int = 4000,
) -> set[tuple[str, ...]]:
    """Sinh các chuỗi terminal độ dài <= max_len bằng BFS dẫn xuất trái nhất.

    Chỉ dùng trong kiểm thử để đối chiếu bảo toàn ngôn ngữ trên grammar nhỏ.
    """
    start_form: tuple[str, ...] = (grammar.start_symbol,)
    queue: deque[tuple[tuple[str, ...], int]] = deque([(start_form, 0)])
    visited: set[tuple[str, ...]] = {start_form}
    terminal_strings: set[tuple[str, ...]] = set()

    while queue and len(visited) < max_states:
        sentential, steps = queue.popleft()

        # Tìm biến trái nhất.
        first_var_index = next(
            (
                idx
                for idx, sym in enumerate(sentential)
                if sym in grammar.variables
            ),
            None,
        )

        if first_var_index is None:
            if len(sentential) <= max_len:
                terminal_strings.add(sentential)
            continue

        if steps >= max_steps:
            continue

        var = sentential[first_var_index]
        for rhs in grammar.get_productions(var):
            next_form = (
                sentential[:first_var_index]
                + rhs
                + sentential[first_var_index + 1:]
            )
            # Cắt nhánh nếu số terminal đã vượt quá max_len.
            terminal_count = sum(
                1 for sym in next_form if sym in grammar.terminals
            )
            if terminal_count > max_len or len(next_form) > max_len + 4:
                continue

            if next_form not in visited:
                visited.add(next_form)
                queue.append((next_form, steps + 1))

    return terminal_strings


def _assert_epsilon_postconditions(
    original: Grammar,
    result: RemoveEpsilonResult,
) -> None:
    """Kiểm tra các bất biến bắt buộc sau khi chạy removeEpsilon."""
    new_grammar = result.grammar
    new_start = new_grammar.start_symbol

    # Không tồn tại luật A -> ε cho bất kỳ biến A != new_start nào.
    for lhs, rules in new_grammar.productions.items():
        if lhs != new_start:
            assert EPSILON not in rules, (
                f"Còn sót luật sinh ε ở biến không phải start: {lhs} -> ε"
            )

    # Nếu giữ new_start -> ε thì ngôn ngữ phải chứa ε và new_start không ở RHS.
    if EPSILON in new_grammar.get_productions(new_start):
        assert original.start_symbol in result.nullable_variables
        assert result.log.preserves_epsilon is True
        for rules in new_grammar.productions.values():
            for rhs in rules:
                assert new_start not in rhs


# Nhóm 1: Tìm tập biến nullable bằng lặp điểm cố định
def test_find_nullable_direct() -> None:
    """Tìm biến nullable trực tiếp từ luật A -> ε."""
    grammar = _parse_valid("S -> aA\nA -> b | ε")

    nullable, iterations = find_nullable_variables(grammar)

    assert nullable == {"A"}
    assert iterations == [["A"]]


def test_find_nullable_indirect_chain() -> None:
    """Tìm biến nullable gián tiếp qua nhiều vòng lặp điểm cố định."""
    grammar = _parse_valid(
        "S -> AB\n"
        "A -> C\n"
        "C -> ε\n"
        "B -> DD\n"
        "D -> ε"
    )

    nullable, iterations = find_nullable_variables(grammar)

    assert nullable == {"S", "A", "B", "C", "D"}
    assert iterations == [["C", "D"], ["A", "B"], ["S"]]


def test_find_nullable_cycle_with_epsilon() -> None:
    """Đảm bảo lặp điểm cố định dừng đúng khi có chu trình chứa ε."""
    grammar = _parse_valid(
        "S -> A\n"
        "A -> B\n"
        "B -> A | ε"
    )

    nullable, iterations = find_nullable_variables(grammar)

    assert nullable == {"S", "A", "B"}
    assert iterations == [["B"], ["A"], ["S"]]


def test_find_nullable_cycle_without_epsilon() -> None:
    """Đảm bảo dừng đúng và trả tập rỗng khi có chu trình không sinh ε."""
    grammar = _parse_valid(
        "S -> A | a\n"
        "A -> B\n"
        "B -> A"
    )

    nullable, iterations = find_nullable_variables(grammar)

    assert nullable == set()
    assert iterations == []


def test_find_nullable_no_epsilon() -> None:
    """Văn phạm không có ε cho tập nullable rỗng."""
    grammar = _parse_valid(
        "S -> AB\n"
        "A -> a\n"
        "B -> b"
    )

    nullable, iterations = find_nullable_variables(grammar)

    assert nullable == set()
    assert iterations == []


def test_find_nullable_terminal_blocks_nullability() -> None:
    """Biến có terminal trong mọi vế phải không thể là nullable."""
    grammar = _parse_valid(
        "S -> aA | Bb\n"
        "A -> ε\n"
        "B -> ε"
    )

    nullable, _ = find_nullable_variables(grammar)

    assert nullable == {"A", "B"}
    assert "S" not in nullable


@pytest.mark.parametrize("bad_input", [None, "S -> a", 123, {}])
def test_find_nullable_invalid_type(bad_input: object) -> None:
    """Báo lỗi TypeError khi đầu vào không phải Grammar."""
    with pytest.raises(TypeError):
        find_nullable_variables(bad_input)  # type: ignore[arg-type]


# Nhóm 2: Sinh tên ký hiệu bắt đầu mới và addFreshStart
def test_generate_fresh_start_default() -> None:
    """Ưu tiên sinh S0 nếu chưa tồn tại."""
    assert generate_fresh_start_symbol({"S", "A", "a"}) == "S0"


def test_generate_fresh_start_avoids_collision() -> None:
    """Tăng chỉ số S0, S1, S2... khi tên dự kiến đã tồn tại."""
    candidate = generate_fresh_start_symbol({"S", "S0", "S1", "a"})

    assert candidate == "S2"
    tokens = tokenize_line(f"{candidate} -> S")
    assert tokens[0].type == "VARIABLE"
    assert tokens[0].value == "S2"


def test_add_fresh_start_when_start_nullable() -> None:
    """Tạo S0 mới khi S sinh được ε mà không sửa Grammar gốc."""
    grammar = _parse_valid("S -> a | ε")
    snapshot = copy.deepcopy(grammar)

    updated, created, reason = addFreshStart(grammar)

    assert created is True
    assert reason is not None
    assert updated.start_symbol == "S0"
    assert ("S",) in updated.get_productions("S0")
    assert grammar.to_dict() == snapshot.to_dict()


def test_add_fresh_start_when_start_on_rhs() -> None:
    """Tạo S0 mới khi S xuất hiện ở vế phải dù không sinh ε."""
    grammar = _parse_valid("S -> aS | a")

    updated, created, reason = addFreshStart(grammar)

    assert created is True
    assert reason is not None and "vế phải" in reason
    assert updated.start_symbol == "S0"
    assert ("S",) in updated.get_productions("S0")


def test_add_fresh_start_not_needed() -> None:
    """Không tạo S0 khi S không sinh ε và không xuất hiện ở vế phải."""
    grammar = _parse_valid("S -> AB\nA -> a\nB -> b")

    updated, created, reason = addFreshStart(grammar)

    assert created is False
    assert reason is None
    assert updated.start_symbol == "S"
    assert updated.to_dict() == grammar.to_dict()


def test_add_fresh_start_empty_grammar() -> None:
    """Grammar rỗng không tự sinh S0 trừ khi force=True."""
    grammar = Grammar()

    updated, created, reason = addFreshStart(grammar)
    assert created is False
    assert reason is None
    assert updated.start_symbol == "S"

    forced, created_forced, reason_forced = addFreshStart(grammar, force=True)
    assert created_forced is True
    assert reason_forced is not None
    assert forced.start_symbol == "S0"


@pytest.mark.parametrize("bad_input", [None, "S -> a"])
def test_add_fresh_start_invalid_type(bad_input: object) -> None:
    """addFreshStart báo lỗi TypeError khi đầu vào không phải Grammar."""
    with pytest.raises(TypeError):
        addFreshStart(bad_input)  # type: ignore[arg-type]


# Nhóm 3: Loại bỏ ε-production và sinh tổ hợp luật sinh
def test_remove_epsilon_textbook_example_5_10() -> None:
    """Kiểm chứng theo Thí dụ 5.10 trong giáo trình (van-pham-phi-ngu-canh.pdf)."""
    grammar = _parse_valid(
        "S -> AB\n"
        "A -> aA | ε\n"
        "B -> bB | ε"
    )

    result = removeEpsilon(grammar)

    assert result.nullable_variables == {"A", "B", "S"}
    assert result.grammar.start_symbol == "S0"
    assert result.grammar.productions == {
        "S0": {("S",), EPSILON},
        "S": {("A", "B"), ("A",), ("B",)},
        "A": {("a", "A"), ("a",)},
        "B": {("b", "B"), ("b",)},
    }
    assert result.log.fresh_start_created is True
    assert result.log.preserves_epsilon is True
    _assert_epsilon_postconditions(grammar, result)


def test_remove_epsilon_slide_example_page_19() -> None:
    """Kiểm chứng ví dụ giản lược trong slide Chuong4_FCG.pdf trang 19."""
    grammar = _parse_valid(
        "S -> aA | BD\n"
        "A -> b | ε\n"
        "B -> C | d\n"
        "C -> A\n"
        "D -> e\n"
        "E -> f"
    )

    result = removeEpsilon(grammar)

    assert result.nullable_variables == {"A", "B", "C"}
    assert result.log.nullable_iterations == [["A"], ["C"], ["B"]]
    assert result.grammar.start_symbol == "S"
    assert result.log.fresh_start_created is False
    assert result.log.preserves_epsilon is False
    assert result.grammar.productions == {
        "S": {("a", "A"), ("a",), ("B", "D"), ("D",)},
        "A": {("b",)},
        "B": {("C",), ("d",)},
        "C": {("A",)},
        "D": {("e",)},
        "E": {("f",)},
    }
    _assert_epsilon_postconditions(grammar, result)


def test_remove_epsilon_multiple_consecutive_nullables_deduplication() -> None:
    """Nhiều biến nullable liên tiếp không sinh luật trùng lặp."""
    grammar = _parse_valid(
        "S -> AAA\n"
        "A -> a | ε"
    )

    result = removeEpsilon(grammar)

    assert result.nullable_variables == {"A", "S"}
    assert result.grammar.start_symbol == "S0"
    assert result.grammar.productions["S"] == {
        ("A", "A", "A"),
        ("A", "A"),
        ("A",),
    }
    assert result.grammar.productions["S0"] == {("S",), EPSILON}
    assert result.grammar.productions["A"] == {("a",)}

    # Đảm bảo không ghi log added_rules trùng cho S -> AA hay S -> A.
    added_pairs = [(c.lhs, c.rhs) for c in result.log.added_rules]
    assert len(added_pairs) == len(set(added_pairs))
    _assert_epsilon_postconditions(grammar, result)


def test_remove_epsilon_mixed_terminals_and_nullables() -> None:
    """Sinh đủ 2^k biến thể khi vế phải trộn terminal và biến nullable."""
    grammar = _parse_valid(
        "S -> aAbBc\n"
        "A -> x | ε\n"
        "B -> y | ε"
    )

    result = removeEpsilon(grammar)

    assert result.nullable_variables == {"A", "B"}
    assert result.grammar.start_symbol == "S"
    assert result.grammar.productions["S"] == {
        ("a", "A", "b", "B", "c"),
        ("a", "A", "b", "c"),
        ("a", "b", "B", "c"),
        ("a", "b", "c"),
    }
    _assert_epsilon_postconditions(grammar, result)


def test_remove_epsilon_indirect_multi_level() -> None:
    """Nullable gián tiếp nhiều tầng tạo đầy đủ tổ hợp hợp lệ."""
    grammar = _parse_valid(
        "S -> AB\n"
        "A -> C\n"
        "C -> a | ε\n"
        "B -> DE\n"
        "D -> b | ε\n"
        "E -> c | ε"
    )

    result = removeEpsilon(grammar)

    assert result.nullable_variables == {"S", "A", "B", "C", "D", "E"}
    assert result.grammar.start_symbol == "S0"
    assert result.grammar.productions["B"] == {("D", "E"), ("D",), ("E",)}
    assert result.grammar.productions["S"] == {("A", "B"), ("A",), ("B",)}
    assert result.grammar.productions["S0"] == {("S",), EPSILON}
    _assert_epsilon_postconditions(grammar, result)


def test_remove_epsilon_cycle_with_epsilon() -> None:
    """Xử lý chu trình biến có ε mà không lặp vô hạn."""
    grammar = _parse_valid(
        "S -> Ab\n"
        "A -> B\n"
        "B -> A | a | ε"
    )

    result = removeEpsilon(grammar)

    assert result.nullable_variables == {"A", "B"}
    assert result.grammar.start_symbol == "S"
    assert result.grammar.productions == {
        "S": {("A", "b"), ("b",)},
        "A": {("B",)},
        "B": {("A",), ("a",)},
    }
    _assert_epsilon_postconditions(grammar, result)


def test_remove_epsilon_cycle_without_epsilon() -> None:
    """Xử lý chu trình biến không có ε."""
    grammar = _parse_valid(
        "S -> A | a\n"
        "A -> B\n"
        "B -> A"
    )

    result = removeEpsilon(grammar)

    assert result.nullable_variables == set()
    assert result.grammar.start_symbol == "S"
    assert result.grammar.productions == grammar.productions
    assert result.log.added_rules == []
    assert result.log.removed_rules == []


# Nhóm 4: Ký hiệu bắt đầu mới S0 và bảo toàn ε
def test_remove_epsilon_start_nullable_and_on_rhs() -> None:
    """S vừa sinh ε vừa xuất hiện ở vế phải -> tạo S0 và giữ S0 -> ε."""
    grammar = _parse_valid("S -> aSb | ε")

    result = removeEpsilon(grammar)

    assert result.nullable_variables == {"S"}
    assert result.grammar.start_symbol == "S0"
    assert result.grammar.productions == {
        "S0": {("S",), EPSILON},
        "S": {("a", "S", "b"), ("a", "b")},
    }
    assert result.log.fresh_start_created is True
    assert result.log.preserves_epsilon is True
    assert "vừa sinh được ε vừa xuất hiện ở vế phải" in (
        result.log.fresh_start_reason or ""
    )
    _assert_epsilon_postconditions(grammar, result)


def test_remove_epsilon_start_not_nullable_but_on_rhs() -> None:
    """S không sinh ε nhưng xuất hiện ở RHS -> tạo S0 nhưng KHÔNG giữ S0 -> ε."""
    grammar = _parse_valid("S -> aS | a")

    result = removeEpsilon(grammar)

    assert result.nullable_variables == set()
    assert result.grammar.start_symbol == "S0"
    assert result.grammar.productions == {
        "S0": {("S",)},
        "S": {("a", "S"), ("a",)},
    }
    assert result.log.fresh_start_created is True
    assert result.log.preserves_epsilon is False
    assert EPSILON not in result.grammar.get_productions("S0")
    _assert_epsilon_postconditions(grammar, result)


def test_remove_epsilon_only_epsilon_grammar() -> None:
    """Văn phạm chỉ sinh đúng chuỗi rỗng L(G) = {ε}."""
    grammar = _parse_valid("S -> ε")

    result = removeEpsilon(grammar)

    assert result.nullable_variables == {"S"}
    assert result.grammar.start_symbol == "S0"
    assert result.grammar.productions == {
        "S0": {("S",), EPSILON},
    }
    assert result.log.preserves_epsilon is True
    assert any("Biến S không còn luật sinh" in w for w in result.log.warnings)
    _assert_epsilon_postconditions(grammar, result)


def test_remove_epsilon_fresh_start_collision_with_existing_s0() -> None:
    """Khi biến S0 đã tồn tại trong văn phạm, phải chọn tên khác không trùng."""
    grammar = _parse_valid(
        "S -> S0 | ε\n"
        "S0 -> a"
    )

    result = removeEpsilon(grammar)

    assert result.grammar.start_symbol == "S1"
    assert "S0" in result.grammar.variables
    assert "S1" in result.grammar.variables
    assert result.grammar.productions["S1"] == {("S",), EPSILON}
    assert result.grammar.productions["S"] == {("S0",)}
    assert result.grammar.productions["S0"] == {("a",)}
    _assert_epsilon_postconditions(grammar, result)


def test_remove_epsilon_custom_start_symbol_nullable() -> None:
    """Hỗ trợ văn phạm có ký hiệu bắt đầu khác S."""
    grammar = _parse_valid(
        "E -> A | ε\n"
        "A -> id",
        start_symbol="E",
    )

    result = removeEpsilon(grammar)

    assert result.grammar.start_symbol == "S0"
    assert result.log.old_start_symbol == "E"
    assert result.log.new_start_symbol == "S0"
    assert result.grammar.productions["S0"] == {("E",), EPSILON}
    assert result.grammar.productions["E"] == {("A",)}
    _assert_epsilon_postconditions(grammar, result)


# Nhóm 5: Trường hợp biên, bất biến đầu vào, tính xác định & cấu trúc log
def test_remove_epsilon_empty_grammar() -> None:
    """Văn phạm rỗng không gây crash và trả cảnh báo rõ ràng."""
    grammar = Grammar()

    result = removeEpsilon(grammar)

    assert isinstance(result, RemoveEpsilonResult)
    assert result.grammar is not grammar
    assert result.grammar.production_count() == 0
    assert result.nullable_variables == set()
    assert result.log.rule_count_before == 0
    assert result.log.rule_count_after == 0
    assert result.log.fresh_start_created is False
    assert result.log.warnings


def test_remove_epsilon_no_epsilon_no_change() -> None:
    """Văn phạm không có ε và S không ở RHS được giữ nguyên."""
    grammar = _parse_valid("S -> AB\nA -> a\nB -> b")

    result = removeEpsilon(grammar)

    assert result.nullable_variables == set()
    assert result.grammar.to_dict() == grammar.to_dict()
    assert result.log.fresh_start_created is False
    assert result.log.added_rules == []
    assert result.log.removed_rules == []
    assert result.log.rule_count_before == 3
    assert result.log.rule_count_after == 3


def test_remove_epsilon_variable_becomes_empty_warns() -> None:
    """Biến chỉ có A -> ε sẽ sinh cảnh báo sau khi xóa luật ε."""
    grammar = _parse_valid("S -> aA\nA -> ε")

    result = removeEpsilon(grammar)

    assert result.grammar.productions == {
        "S": {("a", "A"), ("a",)},
    }
    assert "A" in result.grammar.variables
    assert "A" not in result.grammar.productions
    assert any("Biến A" in warning for warning in result.log.warnings)
    _assert_epsilon_postconditions(grammar, result)


@pytest.mark.parametrize("bad_input", [None, "S -> ε", 42, []])
def test_remove_epsilon_invalid_input_type(bad_input: object) -> None:
    """Báo TypeError nếu tham số không phải Grammar."""
    with pytest.raises(TypeError):
        removeEpsilon(bad_input)  # type: ignore[arg-type]


def test_remove_epsilon_input_immutability() -> None:
    """Đảm bảo removeEpsilon không mutate Grammar đầu vào."""
    grammar = _parse_valid(
        "S -> AB | aSb | ε\n"
        "A -> a | ε\n"
        "B -> b | ε"
    )
    snapshot = copy.deepcopy(grammar)
    snapshot_dict = grammar.to_dict()

    result = removeEpsilon(grammar)

    assert result.grammar is not grammar
    assert grammar.variables == snapshot.variables
    assert grammar.terminals == snapshot.terminals
    assert grammar.productions == snapshot.productions
    assert grammar.start_symbol == snapshot.start_symbol
    assert grammar.to_dict() == snapshot_dict


def test_remove_epsilon_deterministic() -> None:
    """Chạy lặp nhiều lần trên cùng đầu vào phải cho kết quả y hệt nhau."""
    grammar = _parse_valid(
        "S -> ABC\n"
        "A -> a | ε\n"
        "B -> b | ε\n"
        "C -> c | ε"
    )

    first = removeEpsilon(grammar)
    second = removeEpsilon(grammar)

    assert first.to_dict() == second.to_dict()


def test_remove_epsilon_log_structure_and_json_export() -> None:
    """Kiểm tra đầy đủ cấu trúc dữ liệu log và chuyển đổi sang JSON dict."""
    grammar = _parse_valid("S -> aA | ε\nA -> b | ε")

    result = removeEpsilon(grammar)
    payload = result.to_dict()

    assert isinstance(result.log, EpsilonStepLog)
    assert all(isinstance(c, RuleChange) for c in result.log.added_rules)
    assert all(isinstance(c, RuleChange) for c in result.log.removed_rules)

    assert set(payload.keys()) == {"grammar", "nullable_variables", "log"}
    assert payload["nullable_variables"] == ["A", "S"]

    log_dict = payload["log"]
    assert log_dict["step"] == "remove_epsilon"
    assert log_dict["fresh_start_created"] is True
    assert log_dict["old_start_symbol"] == "S"
    assert log_dict["new_start_symbol"] == "S0"
    assert log_dict["preserves_epsilon"] is True
    assert log_dict["rule_count_before"] == 4
    assert log_dict["rule_count_after"] == 5
    assert len(log_dict["removed_rules"]) == 2
    assert len(log_dict["added_rules"]) == 3


def test_remove_epsilon_with_multichar_terminals_and_unicode() -> None:
    """Tích hợp parseGrammar có mũi tên Unicode và terminal nhiều ký tự id/num."""
    grammar = _parse_valid(
        "S → A B\n"
        "A → id | ε\n"
        "B → num | ε"
    )

    result = removeEpsilon(grammar)

    assert result.grammar.terminals == {"id", "num"}
    assert result.grammar.start_symbol == "S0"
    assert result.grammar.productions == {
        "S0": {("S",), EPSILON},
        "S": {("A", "B"), ("A",), ("B",)},
        "A": {("id",)},
        "B": {("num",)},
    }
    _assert_epsilon_postconditions(grammar, result)

# Nhóm 6: Đối chiếu bảo toàn ngôn ngữ L(G') = L(G) trên các chuỗi hữu hạn
@pytest.mark.parametrize(
    "grammar_text",
    [
        "S -> aSb | ε",
        "S -> AB\nA -> aA | ε\nB -> bB | ε",
        "S -> aA | BD\nA -> b | ε\nB -> C | d\nC -> A\nD -> e\nE -> f",
        "S -> aS | b",
        "S -> ε",
        "S -> AAA\nA -> a | ε",
        "S -> aAbBc\nA -> x | ε\nB -> y | ε",
    ],
)
def test_remove_epsilon_preserves_language(grammar_text: str) -> None:
    """Tập chuỗi ngắn sinh bởi G và G' sau removeEpsilon phải trùng khớp hoàn toàn."""
    grammar = _parse_valid(grammar_text)
    result = removeEpsilon(grammar)

    _assert_epsilon_postconditions(grammar, result)

    original_lang = _derive_terminal_strings(grammar, max_len=4, max_steps=10)
    new_lang = _derive_terminal_strings(result.grammar, max_len=4, max_steps=11)

    assert new_lang == original_lang


def test_remove_epsilon_textbook_exercise_5_10() -> None:
    """Kiểm chứng Bài tập 5.10 giáo trình (nullable dây chuyền + S ở RHS + BB)."""
    grammar = _parse_valid(
        "S -> AB\n"
        "A -> SA | BB | bB\n"
        "B -> b | aA | ε"
    )

    result = removeEpsilon(grammar)

    assert result.nullable_variables == {"B", "A", "S"}
    assert result.log.nullable_iterations == [["B"], ["A"], ["S"]]
    assert result.grammar.start_symbol == "S0"
    assert result.grammar.productions == {
        "S0": {("S",), EPSILON},
        "S": {("A", "B"), ("A",), ("B",)},
        "A": {
            ("S", "A"),
            ("S",),
            ("A",),
            ("B", "B"),
            ("B",),
            ("b", "B"),
            ("b",),
        },
        "B": {("b",), ("a", "A"), ("a",)},
    }
    _assert_epsilon_postconditions(grammar, result)


def test_remove_epsilon_existing_variant_not_logged_as_added() -> None:
    """Biến thể sinh ra trùng luật đã có sẵn không bị ghi nhầm vào added_rules."""
    grammar = _parse_valid(
        "S -> AB | A\n"
        "A -> a\n"
        "B -> b | ε"
    )

    result = removeEpsilon(grammar)

    assert result.grammar.productions["S"] == {("A", "B"), ("A",)}
    assert result.log.added_rules == []
    assert len(result.log.removed_rules) == 1
    assert result.log.removed_rules[0].lhs == "B"
    assert result.log.removed_rules[0].rhs == EPSILON


def test_remove_epsilon_missing_start_variable_warns() -> None:
    """Grammar tạo thủ công thiếu start_symbol trong V sẽ phát sinh warning."""
    grammar = Grammar(start_symbol="S")
    grammar.add_production("A", ("a",))
    grammar.terminals.add("a")

    result = removeEpsilon(grammar)

    assert any("Ký hiệu bắt đầu S" in w for w in result.log.warnings)


def test_remove_epsilon_repeated_run_stability() -> None:
    """Chạy removeEpsilon lần hai vẫn giữ ngôn ngữ và thỏa hậu điều kiện."""
    # Trường hợp không sinh ε và S không ở RHS -> hoàn toàn bất biến (idempotent).
    g1 = _parse_valid("S -> aA\nA -> b | ε")
    r1 = removeEpsilon(g1)
    r2 = removeEpsilon(r1.grammar)
    assert r2.grammar.to_dict() == r1.grammar.to_dict()
    assert r2.log.added_rules == []
    assert r2.log.removed_rules == []

    # Trường hợp ngôn ngữ chứa ε -> lần 2 vẫn hợp lệ và bảo toàn ngôn ngữ.
    g2 = _parse_valid("S -> aSb | ε")
    s1 = removeEpsilon(g2)
    s2 = removeEpsilon(s1.grammar)
    _assert_epsilon_postconditions(s1.grammar, s2)
    assert _derive_terminal_strings(g2, max_len=4, max_steps=10) == (
        _derive_terminal_strings(s2.grammar, max_len=4, max_steps=12)
    )
