"""Mô hình dữ liệu văn phạm phi ngữ cảnh CFG."""

from dataclasses import dataclass, field


# Kiểu dữ liệu của vế phải production.
Production = tuple[str, ...]

# Tập luật sinh được nhóm theo biến vế trái.
Productions = dict[str, set[Production]]

# Epsilon được biểu diễn bằng tuple rỗng.
EPSILON: Production = ()


@dataclass
class Grammar:
    """Biểu diễn văn phạm phi ngữ cảnh G = (V, Σ, P, S)."""

    variables: set[str] = field(default_factory=set)
    terminals: set[str] = field(default_factory=set)
    productions: Productions = field(default_factory=dict)
    start_symbol: str = "S"

    def add_production(
        self,
        lhs: str,
        rhs: Production,
    ) -> None:
        """Thêm một luật sinh vào văn phạm."""
        self.variables.add(lhs)
        self.productions.setdefault(lhs, set()).add(rhs)

    def get_productions(self, lhs: str) -> set[Production]:
        """Lấy các luật sinh của một biến."""
        return set(self.productions.get(lhs, set()))

    def production_count(self) -> int:
        """Đếm tổng số luật sinh."""
        return sum(
            len(rules)
            for rules in self.productions.values()
        )

    def copy(self) -> "Grammar":
        """Tạo bản sao độc lập của văn phạm."""
        return Grammar(
            variables=set(self.variables),
            terminals=set(self.terminals),
            productions={
                lhs: set(rules)
                for lhs, rules in self.productions.items()
            },
            start_symbol=self.start_symbol,
        )

    def to_dict(self) -> dict:
        """Chuyển văn phạm thành dữ liệu tương thích JSON."""
        return {
            "variables": sorted(self.variables),
            "terminals": sorted(self.terminals),
            "productions": {
                lhs: [list(rhs) for rhs in sorted(rules)]
                for lhs, rules in sorted(self.productions.items())
            },
            "start_symbol": self.start_symbol,
        }
