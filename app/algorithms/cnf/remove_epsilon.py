"""Thuật toán tìm biến nullable và loại bỏ luật sinh ε (T04)."""

from dataclasses import dataclass, field

from app.models.grammar import EPSILON, Grammar, Production


def _format_rhs(rhs: Production) -> str:
    """Định dạng vế phải của luật sinh thành chuỗi dễ đọc."""
    if rhs == EPSILON:
        return "ε"
    return " ".join(rhs)


@dataclass(frozen=True)
class RuleChange:
    """Ghi nhận một thay đổi luật sinh trong bước chuyển đổi."""

    action: str
    lhs: str
    rhs: Production
    reason: str

    def to_dict(self) -> dict[str, object]:
        """Chuyển thông tin thay đổi luật thành dữ liệu JSON."""
        return {
            "action": self.action,
            "lhs": self.lhs,
            "rhs": list(self.rhs),
            "rule": f"{self.lhs} -> {_format_rhs(self.rhs)}",
            "reason": self.reason,
        }


@dataclass
class EpsilonStepLog:
    """Log chi tiết của bước tìm nullable và loại bỏ ε-production."""

    step: str = "remove_epsilon"
    nullable_variables: list[str] = field(default_factory=list)
    nullable_iterations: list[list[str]] = field(default_factory=list)
    fresh_start_created: bool = False
    old_start_symbol: str = "S"
    new_start_symbol: str = "S"
    fresh_start_reason: str | None = None
    preserves_epsilon: bool = False
    rule_count_before: int = 0
    rule_count_after: int = 0
    added_rules: list[RuleChange] = field(default_factory=list)
    removed_rules: list[RuleChange] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        """Chuyển log bước chuyển đổi thành dữ liệu JSON."""
        return {
            "step": self.step,
            "nullable_variables": list(self.nullable_variables),
            "nullable_iterations": [
                list(iteration)
                for iteration in self.nullable_iterations
            ],
            "fresh_start_created": self.fresh_start_created,
            "old_start_symbol": self.old_start_symbol,
            "new_start_symbol": self.new_start_symbol,
            "fresh_start_reason": self.fresh_start_reason,
            "preserves_epsilon": self.preserves_epsilon,
            "rule_count_before": self.rule_count_before,
            "rule_count_after": self.rule_count_after,
            "added_rules": [
                change.to_dict()
                for change in self.added_rules
            ],
            "removed_rules": [
                change.to_dict()
                for change in self.removed_rules
            ],
            "warnings": list(self.warnings),
        }


@dataclass
class RemoveEpsilonResult:
    """Kết quả của quá trình loại bỏ luật sinh ε."""

    grammar: Grammar
    nullable_variables: set[str] = field(default_factory=set)
    log: EpsilonStepLog = field(default_factory=EpsilonStepLog)

    def to_dict(self) -> dict[str, object]:
        """Chuyển kết quả loại bỏ ε thành dữ liệu tương thích JSON."""
        return {
            "grammar": self.grammar.to_dict(),
            "nullable_variables": sorted(self.nullable_variables),
            "log": self.log.to_dict(),
        }


def _validate_grammar_input(grammar: object) -> None:
    """Kiểm tra đầu vào có phải đối tượng Grammar hợp lệ không."""
    if not isinstance(grammar, Grammar):
        raise TypeError("Đầu vào phải là một đối tượng Grammar hợp lệ.")


def _start_appears_on_rhs(
    grammar: Grammar,
    start_symbol: str,
) -> bool:
    """Kiểm tra ký hiệu bắt đầu có xuất hiện ở vế phải luật sinh nào không."""
    return any(
        start_symbol in rhs
        for rules in grammar.productions.values()
        for rhs in rules
    )


def _build_fresh_start_reason(
    start_symbol: str,
    start_is_nullable: bool,
    start_on_rhs: bool,
    force: bool = False,
) -> str | None:
    """Tạo mô tả lý do cần sinh ký hiệu bắt đầu mới."""
    if start_is_nullable and start_on_rhs:
        return (
            f"Ký hiệu bắt đầu {start_symbol} vừa sinh được ε "
            f"vừa xuất hiện ở vế phải."
        )

    if start_is_nullable:
        return f"Ký hiệu bắt đầu {start_symbol} có thể sinh chuỗi rỗng ε."

    if start_on_rhs:
        return (
            f"Ký hiệu bắt đầu {start_symbol} xuất hiện ở vế phải "
            f"của luật sinh."
        )

    if force:
        return "Tạo ký hiệu bắt đầu mới theo yêu cầu tường minh."

    return None


def generate_fresh_start_symbol(
    existing_symbols: set[str],
    base: str = "S",
) -> str:
    """Sinh tên ký hiệu bắt đầu mới (S0, S1, ...) không trùng ký hiệu đã có.

    Tên sinh ra tuân theo quy ước biến [A-Z][0-9]*'* của tokenizer.
    """
    prefix = base if (base and len(base) == 1 and "A" <= base <= "Z") else "S"

    index = 0
    while True:
        candidate = f"{prefix}{index}"
        if candidate not in existing_symbols:
            return candidate
        index += 1


def find_nullable_variables(
    grammar: Grammar,
) -> tuple[set[str], list[list[str]]]:
    """Tìm tập biến nullable bằng lặp điểm cố định đến khi không đổi.

    Một biến A là nullable nếu A =>* ε.
    Trả về cặp (tập biến nullable, danh sách biến mới tìm được theo từng vòng).
    """
    _validate_grammar_input(grammar)

    nullable: set[str] = set()
    iterations: list[list[str]] = []

    while True:
        newly_nullable: set[str] = set()

        for lhs in sorted(grammar.productions.keys()):
            if lhs in nullable:
                continue

            for rhs in grammar.productions[lhs]:
                # Với rhs == () (EPSILON), all(...) trả về True ở vòng lặp đầu.
                if all(symbol in nullable for symbol in rhs):
                    newly_nullable.add(lhs)
                    break

        if not newly_nullable:
            break

        nullable.update(newly_nullable)
        iterations.append(sorted(newly_nullable))

    return nullable, iterations


def addFreshStart(
    grammar: Grammar,
    nullable: set[str] | None = None,
    force: bool = False,
) -> tuple[Grammar, bool, str | None]:
    """Tạo ký hiệu bắt đầu mới S0 không trùng tên khi cần mà không đổi L(G).

    Tạo start symbol mới nếu:
    - Ký hiệu bắt đầu S sinh được ε (S ∈ nullable), hoặc
    - Ký hiệu bắt đầu S xuất hiện ở vế phải của ít nhất một luật sinh, hoặc
    - Tham số force=True.

    Không làm thay đổi đối tượng Grammar đầu vào.
    """
    _validate_grammar_input(grammar)

    new_grammar = grammar.copy()

    if grammar.production_count() == 0 and not force:
        return new_grammar, False, None

    if nullable is None:
        nullable_set, _ = find_nullable_variables(grammar)
    else:
        nullable_set = set(nullable)

    old_start = grammar.start_symbol
    start_is_nullable = old_start in nullable_set
    start_on_rhs = _start_appears_on_rhs(grammar, old_start)

    reason = _build_fresh_start_reason(
        start_symbol=old_start,
        start_is_nullable=start_is_nullable,
        start_on_rhs=start_on_rhs,
        force=force,
    )

    if reason is None:
        return new_grammar, False, None

    existing_symbols = new_grammar.variables | new_grammar.terminals
    new_start = generate_fresh_start_symbol(existing_symbols)

    new_grammar.variables.add(new_start)
    new_grammar.add_production(new_start, (old_start,))
    new_grammar.start_symbol = new_start

    return new_grammar, True, reason


def removeEpsilon(grammar: Grammar) -> RemoveEpsilonResult:
    """Loại bỏ các luật sinh ε và bảo toàn ngôn ngữ L(G).

    Các bước chính:
    1. Tìm tập biến nullable bằng lặp điểm cố định.
    2. Nếu ký hiệu bắt đầu S sinh ε hoặc xuất hiện ở vế phải, sinh ký hiệu
       bắt đầu mới S0 không trùng tên.
    3. Với mỗi luật A -> X1...Xk (khác ε), sinh mọi tổ hợp hợp lệ khi bỏ
       các biến nullable ở vế phải, loại bỏ tổ hợp rỗng và luật trùng.
    4. Xóa toàn bộ luật sinh ε cũ; chỉ thêm S0 -> ε khi ngôn ngữ chứa ε.

    Hàm không làm thay đổi đối tượng Grammar đầu vào.
    """
    _validate_grammar_input(grammar)

    old_start = grammar.start_symbol
    rule_count_before = grammar.production_count()

    # Trường hợp biên: văn phạm rỗng (không có luật sinh nào).
    if rule_count_before == 0:
        copied = grammar.copy()
        log = EpsilonStepLog(
            nullable_variables=[],
            nullable_iterations=[],
            fresh_start_created=False,
            old_start_symbol=old_start,
            new_start_symbol=old_start,
            fresh_start_reason=None,
            preserves_epsilon=False,
            rule_count_before=0,
            rule_count_after=0,
            added_rules=[],
            removed_rules=[],
            warnings=["Văn phạm rỗng, không có luật sinh để xử lý."],
        )
        return RemoveEpsilonResult(
            grammar=copied,
            nullable_variables=set(),
            log=log,
        )

    # Bước 1: Tìm tập biến nullable bằng lặp điểm cố định.
    nullable, iterations = find_nullable_variables(grammar)

    # Bước 2: Xác định có cần tạo ký hiệu bắt đầu mới S0 hay không.
    start_is_nullable = old_start in nullable
    start_on_rhs = _start_appears_on_rhs(grammar, old_start)
    fresh_start_reason = _build_fresh_start_reason(
        start_symbol=old_start,
        start_is_nullable=start_is_nullable,
        start_on_rhs=start_on_rhs,
    )
    fresh_start_created = fresh_start_reason is not None

    if fresh_start_created:
        existing_symbols = grammar.variables | grammar.terminals
        new_start = generate_fresh_start_symbol(existing_symbols)
    else:
        new_start = old_start

    # Khởi tạo Grammar mới độc lập hoàn toàn với input.
    new_grammar = Grammar(
        variables=set(grammar.variables),
        terminals=set(grammar.terminals),
        productions={},
        start_symbol=new_start,
    )

    if fresh_start_created:
        new_grammar.variables.add(new_start)

    added_rules: list[RuleChange] = []
    removed_rules: list[RuleChange] = []
    warnings: list[str] = []
    seen_added: set[tuple[str, Production]] = set()

    if old_start not in grammar.variables:
        warnings.append(
            f"Ký hiệu bắt đầu {old_start} chưa xuất hiện trong tập biến V."
        )

    # Bước 3: Duyệt từng luật sinh, loại ε và sinh các biến thể hợp lệ.
    for lhs in sorted(grammar.productions.keys()):
        original_rules = grammar.productions[lhs]

        for rhs in sorted(original_rules):
            if rhs == EPSILON:
                removed_rules.append(
                    RuleChange(
                        action="removed",
                        lhs=lhs,
                        rhs=EPSILON,
                        reason=f"Loại bỏ luật sinh ε: {lhs} -> ε",
                    )
                )
                continue

            # Giữ lại luật gốc không phải ε.
            new_grammar.add_production(lhs, rhs)

            nullable_positions = [
                index
                for index, symbol in enumerate(rhs)
                if symbol in nullable
            ]

            if not nullable_positions:
                continue

            count = len(nullable_positions)
            # Duyệt mọi tổ hợp bỏ ít nhất 1 vị trí nullable (mask từ 1 đến 2^k - 1).
            for mask in range(1, 1 << count):
                omitted_indices = {
                    nullable_positions[bit]
                    for bit in range(count)
                    if (mask >> bit) & 1
                }

                variant = tuple(
                    symbol
                    for index, symbol in enumerate(rhs)
                    if index not in omitted_indices
                )

                # Không tạo lại luật sinh ε cho biến thông thường.
                if variant == EPSILON:
                    continue

                new_grammar.add_production(lhs, variant)

                key = (lhs, variant)
                if variant not in original_rules and key not in seen_added:
                    seen_added.add(key)
                    omitted_names = ", ".join(
                        rhs[index] for index in sorted(omitted_indices)
                    )
                    added_rules.append(
                        RuleChange(
                            action="added",
                            lhs=lhs,
                            rhs=variant,
                            reason=(
                                f"Sinh từ {lhs} -> {_format_rhs(rhs)} "
                                f"khi loại bỏ biến nullable ({omitted_names})."
                            ),
                        )
                    )

    # Bước 4: Bổ sung luật cho ký hiệu bắt đầu mới S0 (nếu đã tạo).
    preserves_epsilon = False
    if fresh_start_created:
        new_grammar.add_production(new_start, (old_start,))
        added_rules.append(
            RuleChange(
                action="added",
                lhs=new_start,
                rhs=(old_start,),
                reason=f"Thêm luật cho ký hiệu bắt đầu mới: {fresh_start_reason}",
            )
        )

        if start_is_nullable:
            new_grammar.add_production(new_start, EPSILON)
            preserves_epsilon = True
            added_rules.append(
                RuleChange(
                    action="added",
                    lhs=new_start,
                    rhs=EPSILON,
                    reason=(
                        f"Giữ lại {new_start} -> ε để bảo toàn "
                        f"chuỗi rỗng ε ∈ L(G)."
                    ),
                )
            )

    # Ghi cảnh báo các biến không còn luật sinh sau khi bỏ ε (để T07 xử lý).
    for variable in sorted(grammar.productions.keys()):
        if variable not in new_grammar.productions:
            warnings.append(
                f"Biến {variable} không còn luật sinh nào sau khi loại bỏ "
                f"ε-production (sẽ được xử lý ở bước loại ký hiệu vô ích)."
            )

    # Sắp xếp log để kết quả luôn xác định (deterministic).
    added_rules.sort(key=lambda item: (item.lhs, item.rhs, item.action))
    removed_rules.sort(key=lambda item: (item.lhs, item.rhs, item.action))

    log = EpsilonStepLog(
        nullable_variables=sorted(nullable),
        nullable_iterations=iterations,
        fresh_start_created=fresh_start_created,
        old_start_symbol=old_start,
        new_start_symbol=new_start,
        fresh_start_reason=fresh_start_reason,
        preserves_epsilon=preserves_epsilon,
        rule_count_before=rule_count_before,
        rule_count_after=new_grammar.production_count(),
        added_rules=added_rules,
        removed_rules=removed_rules,
        warnings=warnings,
    )

    return RemoveEpsilonResult(
        grammar=new_grammar,
        nullable_variables=nullable,
        log=log,
    )
