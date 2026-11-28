"""Bộ kiểm thử đơn vị cho thuật toán loại bỏ Unit Productions (T06)."""

import pytest
from app.algorithms.cnf import removeEpsilon, removeUnit
from app.algorithms.cnf.unit import (
    build_unit_graph,
    compute_unit_closures,
    detect_unit_cycles,
    is_unit_production,
    remove_unit_productions,
)
from app.models.grammar import Grammar, EPSILON
from app.services.parser import parseGrammar


def test_is_unit_production():
    """Kiểm tra nhận diện luật sinh đơn vị."""
    variables = {"S", "A", "B"}
    assert is_unit_production(("A",), variables) is True
    assert is_unit_production(("B",), variables) is True
    assert is_unit_production(("a",), variables) is False
    assert is_unit_production(("id",), variables) is False
    assert is_unit_production(EPSILON, variables) is False
    assert is_unit_production(("A", "B"), variables) is False
    assert is_unit_production(("A", "a"), variables) is False


def test_remove_unit_simple():
    """Kiểm tra loại bỏ luật đơn vị cơ bản: S -> A, A -> a."""
    g = Grammar(variables={"S", "A"}, terminals={"a", "b"}, start_symbol="S")
    g.add_production("S", ("A",))
    g.add_production("S", ("b",))
    g.add_production("A", ("a",))

    new_g, log = remove_unit_productions(g)

    assert ("A",) not in new_g.get_productions("S")
    assert ("a",) in new_g.get_productions("S")
    assert ("b",) in new_g.get_productions("S")
    assert ("a",) in new_g.get_productions("A")
    assert log["original_unit_count"] == 1
    assert log["unit_closures"]["S"] == ["A", "S"]
    assert log["unit_closures"]["A"] == ["A"]


def test_remove_unit_long_chain():
    """Kiểm tra chuỗi đơn vị dài: S -> A -> B -> C -> d | e."""
    g = Grammar(variables={"S", "A", "B", "C"}, terminals={"d", "e"}, start_symbol="S")
    g.add_production("S", ("A",))
    g.add_production("A", ("B",))
    g.add_production("B", ("C",))
    g.add_production("C", ("d",))
    g.add_production("C", ("e",))

    new_g, log = remove_unit_productions(g)

    for var in ["S", "A", "B", "C"]:
        prods = new_g.get_productions(var)
        assert prods == {("d",), ("e",)}, f"Biến {var} chưa nhận đủ luật sinh kế thừa"
        # Không được chứa bất kỳ luật đơn vị nào
        for rhs in prods:
            assert not is_unit_production(rhs, new_g.variables)

    assert log["original_unit_count"] == 3
    assert log["unit_closures"]["S"] == ["A", "B", "C", "S"]


def test_remove_unit_cycle_two_variables():
    """Kiểm tra xử lý chu trình A -> B -> A."""
    g = Grammar(variables={"A", "B"}, terminals={"a", "b"}, start_symbol="A")
    g.add_production("A", ("B",))
    g.add_production("A", ("a",))
    g.add_production("B", ("A",))
    g.add_production("B", ("b",))

    new_g, log = remove_unit_productions(g)

    assert new_g.get_productions("A") == {("a",), ("b",)}
    assert new_g.get_productions("B") == {("a",), ("b",)}
    assert len(log["cycles"]) >= 1


def test_remove_unit_cycle_three_variables():
    """Kiểm tra chu trình 3 biến: S -> A -> B -> S với luật kết thúc c."""
    g = Grammar(variables={"S", "A", "B"}, terminals={"c"}, start_symbol="S")
    g.add_production("S", ("A",))
    g.add_production("A", ("B",))
    g.add_production("B", ("S",))
    g.add_production("B", ("c",))

    new_g, log = remove_unit_productions(g)

    assert new_g.get_productions("S") == {("c",)}
    assert new_g.get_productions("A") == {("c",)}
    assert new_g.get_productions("B") == {("c",)}
    assert log["unit_closures"]["S"] == ["A", "B", "S"]


def test_remove_unit_self_loop():
    """Kiểm tra vòng lặp đơn vị tại chính nó: A -> A."""
    g = Grammar(variables={"A"}, terminals={"a"}, start_symbol="A")
    g.add_production("A", ("A",))
    g.add_production("A", ("a",))

    new_g, log = remove_unit_productions(g)

    assert new_g.get_productions("A") == {("a",)}
    assert log["original_unit_count"] == 1


def test_remove_unit_no_unit_productions():
    """Kiểm tra văn phạm không có luật đơn vị thì giữ nguyên không đổi."""
    g = Grammar(variables={"S", "A"}, terminals={"a", "b"}, start_symbol="S")
    g.add_production("S", ("A", "b"))
    g.add_production("S", ("a",))
    g.add_production("A", ("b",))

    new_g, log = remove_unit_productions(g)

    assert new_g.get_productions("S") == g.get_productions("S")
    assert new_g.get_productions("A") == g.get_productions("A")
    assert log["original_unit_count"] == 0
    assert log["added_productions"] == {}


def test_remove_unit_variable_with_no_productions():
    """Kiểm tra biến rỗng không có luật sinh: S -> A | a, A không có luật."""
    g = Grammar(variables={"S", "A"}, terminals={"a"}, start_symbol="S")
    g.add_production("S", ("A",))
    g.add_production("S", ("a",))

    new_g, log = remove_unit_productions(g)

    assert new_g.get_productions("S") == {("a",)}
    assert new_g.get_productions("A") == set()


def test_remove_unit_diamond_graph():
    """Kiểm tra cấu trúc kim cương (diamond) không bị trùng luật sinh:
    S -> A | B
    A -> C
    B -> C
    C -> c
    """
    g = Grammar(variables={"S", "A", "B", "C"}, terminals={"c"}, start_symbol="S")
    g.add_production("S", ("A",))
    g.add_production("S", ("B",))
    g.add_production("A", ("C",))
    g.add_production("B", ("C",))
    g.add_production("C", ("c",))

    new_g, log = remove_unit_productions(g)

    assert new_g.get_productions("S") == {("c",)}
    assert new_g.get_productions("A") == {("c",)}
    assert new_g.get_productions("B") == {("c",)}
    assert new_g.get_productions("C") == {("c",)}


def test_remove_unit_preserves_epsilon_and_binary_productions():
    """Kiểm tra bảo toàn các luật không đơn vị khác (nhị phân, chuỗi dài, epsilon)."""
    g = Grammar(variables={"S", "A"}, terminals={"a", "b"}, start_symbol="S")
    g.add_production("S", ("A",))
    g.add_production("A", ("a", "b"))
    g.add_production("A", EPSILON)

    new_g, log = remove_unit_productions(g)

    assert ("a", "b") in new_g.get_productions("S")
    assert EPSILON in new_g.get_productions("S")
    assert ("a", "b") in new_g.get_productions("A")
    assert EPSILON in new_g.get_productions("A")
    assert ("A",) not in new_g.get_productions("S")


def test_remove_unit_immutability():
    """Đảm bảo văn phạm đầu vào không bị thay đổi (immutability)."""
    g = Grammar(variables={"S", "A"}, terminals={"a"}, start_symbol="S")
    g.add_production("S", ("A",))
    g.add_production("A", ("a",))

    old_s_prods = set(g.get_productions("S"))
    new_g, _ = remove_unit_productions(g)

    assert g.get_productions("S") == old_s_prods
    assert ("A",) in g.get_productions("S")
    assert ("A",) not in new_g.get_productions("S")


def test_removeUnit_alias_consistency():
    """Kiểm tra alias removeUnit cho kết quả đồng nhất."""
    g = Grammar(variables={"S", "A"}, terminals={"a"}, start_symbol="S")
    g.add_production("S", ("A",))
    g.add_production("A", ("a",))

    res1_g, res1_log = remove_unit_productions(g)
    res2_g, res2_log = removeUnit(g)

    assert res1_g.productions == res2_g.productions
    assert res1_log == res2_log


@pytest.mark.parametrize("bad_input", [None, "S -> A", 123, []])
def test_remove_unit_invalid_input(bad_input):
    """Kiểm tra ném TypeError khi đầu vào không phải đối tượng Grammar."""
    with pytest.raises(TypeError):
        removeUnit(bad_input)


def test_remove_unit_idempotence():
    """Kiểm tra tính lũy đẳng (idempotence): chạy removeUnit 2 lần cho kết quả giống nhau."""
    g = Grammar(variables={"S", "A", "B"}, terminals={"a", "b"}, start_symbol="S")
    g.add_production("S", ("A",))
    g.add_production("A", ("B",))
    g.add_production("B", ("A",))
    g.add_production("A", ("a",))
    g.add_production("B", ("b",))

    first, _ = removeUnit(g)
    second, second_log = removeUnit(first)

    assert second.to_dict() == first.to_dict()
    assert second_log["original_unit_count"] == 0


@pytest.mark.parametrize(
    "grammar_text",
    [
        "S -> A | ε\nA -> B | a\nB -> b",
        "S -> a A | B\nA -> b | ε\nB -> C\nC -> c",
    ],
)
def test_integration_parser_remove_epsilon_and_remove_unit(grammar_text):
    """Kiểm thử tích hợp pipeline thật: parseGrammar -> removeEpsilon -> removeUnit."""
    parsed = parseGrammar(grammar_text)
    assert parsed.success and parsed.grammar is not None

    before_epsilon = parsed.grammar.to_dict()
    epsilon_result = removeEpsilon(parsed.grammar)
    before_unit = epsilon_result.grammar.to_dict()

    unit_grammar, unit_log = removeUnit(epsilon_result.grammar)

    # 1. Không còn bất kỳ unit production nào
    for lhs, prods in unit_grammar.productions.items():
        for rhs in prods:
            assert not is_unit_production(rhs, unit_grammar.variables), (
                f"Vẫn còn luật đơn vị {lhs} -> {rhs}"
            )

    # 2. Chỉ còn ε hợp lệ ở start symbol mới (nếu ngôn ngữ chứa ε)
    for lhs, prods in unit_grammar.productions.items():
        if EPSILON in prods:
            assert lhs == unit_grammar.start_symbol

    # 3. Grammar đầu vào của mỗi bước không bị sửa đổi (immutability)
    assert parsed.grammar.to_dict() == before_epsilon
    assert epsilon_result.grammar.to_dict() == before_unit
    assert isinstance(unit_log, dict)
