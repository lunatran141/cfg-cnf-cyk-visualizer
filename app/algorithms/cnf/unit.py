"""Thuật toán loại bỏ luật sinh đơn vị (Unit Productions) bằng Unit-Closure.

Trong văn phạm phi ngữ cảnh CFG, luật sinh đơn vị là luật có dạng A -> B,
trong đó A và B đều là các biến (non-terminals).
Thuật toán tính bao đóng đơn vị (unit-closure) cho từng biến và thay thế
luật đơn vị bằng các luật không đơn vị (non-unit productions).
"""

from collections import deque
from typing import Any

from app.models.grammar import Grammar, Production


def _validate_grammar_input(grammar: object) -> None:
    """Kiểm tra đầu vào có phải đối tượng Grammar hợp lệ không."""
    if not isinstance(grammar, Grammar):
        raise TypeError("Đầu vào phải là đối tượng Grammar.")


def is_unit_production(rhs: Production, variables: set[str]) -> bool:
    """Kiểm tra một vế phải có phải là luật sinh đơn vị hay không.
    
    Luật sinh đơn vị có dạng A -> B với B in V (độ dài vế phải bằng 1
    và ký hiệu duy nhất thuộc tập biến).
    """
    return len(rhs) == 1 and rhs[0] in variables


def build_unit_graph(grammar: Grammar) -> dict[str, set[str]]:
    """Xây dựng đồ thị có hướng của các luật sinh đơn vị.
    
    Mỗi đỉnh là một biến thuộc grammar.variables.
    Cung có hướng (A, B) tồn tại nếu tồn tại luật sinh A -> B với B in V.
    """
    _validate_grammar_input(grammar)
    graph: dict[str, set[str]] = {v: set() for v in grammar.variables}
    for lhs, rhs_set in grammar.productions.items():
        if lhs not in graph:
            graph[lhs] = set()
        for rhs in rhs_set:
            if is_unit_production(rhs, grammar.variables):
                graph[lhs].add(rhs[0])
    return graph


def compute_unit_closures(grammar: Grammar) -> dict[str, set[str]]:
    """Tính unit-closure (bao đóng đơn vị) cho mọi biến trong văn phạm.
    
    Unit-closure của biến A, ký hiệu UNIT(A), là tập tất cả các biến B sao cho
    A =>* B chỉ bằng cách áp dụng các luật sinh đơn vị.
    Bao đóng có tính phản xạ (A in UNIT(A)) và bắc cầu (A -> B và B in UNIT(C) => C in UNIT(A)).
    
    Sử dụng thuật toán tìm kiếm theo chiều rộng (BFS) từ từng đỉnh trên đồ thị luật đơn vị.
    """
    _validate_grammar_input(grammar)
    graph = build_unit_graph(grammar)
    closures: dict[str, set[str]] = {}

    for var in sorted(grammar.variables):
        closure: set[str] = {var}
        queue: deque[str] = deque([var])

        while queue:
            current = queue.popleft()
            for neighbor in graph.get(current, set()):
                if neighbor not in closure:
                    closure.add(neighbor)
                    queue.append(neighbor)

        closures[var] = closure

    return closures


def detect_unit_cycles(unit_graph: dict[str, set[str]]) -> list[list[str]]:
    """Phát hiện các chu trình luật đơn vị (ví dụ A -> B -> A).
    
    Trả về danh sách các chu trình đơn giản tìm thấy trong đồ thị.
    """
    cycles: list[list[str]] = []
    visited: set[str] = set()
    rec_stack: list[str] = []

    def dfs(node: str) -> None:
        rec_stack.append(node)
        for neighbor in sorted(unit_graph.get(node, set())):
            if neighbor in rec_stack:
                # Tìm thấy chu trình
                cycle_start_idx = rec_stack.index(neighbor)
                cycle = rec_stack[cycle_start_idx:] + [neighbor]
                # Chuẩn hóa để tránh trùng lặp chu trình đảo vòng
                min_node = min(cycle[:-1])
                min_idx = cycle.index(min_node)
                normalized = cycle[min_idx:-1] + cycle[:min_idx] + [min_node]
                if normalized not in cycles:
                    cycles.append(normalized)
            elif neighbor not in visited:
                dfs(neighbor)
        rec_stack.pop()
        visited.add(node)

    for node in sorted(unit_graph.keys()):
        if node not in visited:
            dfs(node)

    return cycles


def remove_unit_productions(grammar: Grammar) -> tuple[Grammar, dict[str, Any]]:
    """Loại bỏ toàn bộ luật sinh đơn vị khỏi văn phạm bằng phương pháp unit-closure.
    
    Quy trình:
    1. Xác định tập các luật sinh đơn vị ban đầu và xây đồ thị đơn vị.
    2. Phát hiện các chu trình và self-loop trên đồ thị đơn vị.
    3. Tính unit-closure UNIT(A) cho từng biến A.
    4. Với mỗi biến A, với mỗi B in UNIT(A), thêm mọi luật không đơn vị B -> alpha vào A.
    5. Xóa bỏ hoàn toàn các luật sinh đơn vị.
    
    Trả về:
        tuple[Grammar, dict[str, Any]]:
            - Văn phạm mới không còn luật đơn vị.
            - Bản ghi log chi tiết các bước thực hiện.
    """
    _validate_grammar_input(grammar)
    unit_graph = build_unit_graph(grammar)
    closures = compute_unit_closures(grammar)
    cycles = detect_unit_cycles(unit_graph)

    # Thu thập danh sách luật đơn vị ban đầu
    unit_rules: list[dict[str, str]] = []
    for lhs in sorted(grammar.productions.keys()):
        for rhs in sorted(grammar.get_productions(lhs)):
            if is_unit_production(rhs, grammar.variables):
                unit_rules.append({"lhs": lhs, "rhs": rhs[0]})

    # Tạo văn phạm mới
    new_grammar = Grammar(
        variables=set(grammar.variables),
        terminals=set(grammar.terminals),
        productions={v: set() for v in grammar.variables},
        start_symbol=grammar.start_symbol,
    )

    added_rules: dict[str, list[list[str]]] = {v: [] for v in grammar.variables}
    steps_log: list[str] = []

    steps_log.append(f"Bước 1: Phát hiện {len(unit_rules)} luật sinh đơn vị ban đầu.")
    for rule in unit_rules:
        steps_log.append(f"  - {rule['lhs']} -> {rule['rhs']}")

    if cycles:
        steps_log.append(f"Bước 2: Phát hiện {len(cycles)} chu trình đơn vị:")
        for c in cycles:
            steps_log.append(f"  - {' -> '.join(c)}")
    else:
        steps_log.append("Bước 2: Không có chu trình đơn vị phức tạp.")

    steps_log.append("Bước 3: Tính toán Unit-Closure cho từng biến:")
    for var in sorted(closures.keys()):
        closure_str = ", ".join(sorted(closures[var]))
        steps_log.append(f"  - UNIT({var}) = {{{closure_str}}}")

    steps_log.append("Bước 4: Thay thế các luật đơn vị bằng các luật không đơn vị:")
    for var in sorted(grammar.variables):
        unit_closure = closures.get(var, {var})
        for target_var in sorted(unit_closure):
            for rhs in grammar.get_productions(target_var):
                if not is_unit_production(rhs, grammar.variables):
                    # Nếu luật này chưa có ở biến var ban đầu và đến từ target_var != var
                    if rhs not in new_grammar.get_productions(var):
                        new_grammar.add_production(var, rhs)
                        if target_var != var:
                            added_rules[var].append(list(rhs))
                            rhs_repr = "".join(rhs) if rhs else "ε"
                            steps_log.append(
                                f"  - Thêm {var} -> {rhs_repr} (kế thừa từ {target_var} qua bao đóng)"
                            )

    steps_log.append("Bước 5: Xóa bỏ toàn bộ luật đơn vị cũ hoàn tất.")

    # Chuyển đổi closures và added_rules sang định dạng json-serializable
    serializable_closures = {
        v: sorted(closures[v]) for v in sorted(closures.keys())
    }
    serializable_graph = {
        v: sorted(unit_graph[v]) for v in sorted(unit_graph.keys())
    }

    log_data: dict[str, Any] = {
        "original_unit_count": len(unit_rules),
        "original_unit_rules": unit_rules,
        "unit_graph": serializable_graph,
        "unit_closures": serializable_closures,
        "cycles": cycles,
        "added_productions": {v: p for v, p in added_rules.items() if p},
        "steps": steps_log,
        "initial_production_count": grammar.production_count(),
        "final_production_count": new_grammar.production_count(),
    }

    return new_grammar, log_data


# Alias tương thích theo checklist và rubric của nhóm
removeUnit = remove_unit_productions
