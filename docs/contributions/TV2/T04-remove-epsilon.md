# T04 — Tìm biến Nullable và Loại bỏ luật sinh ε (`removeEpsilon`)

## 1. Thông tin task

| Thuộc tính | Nội dung |
|---|---|
| Mã task | T04 |
| Người thực hiện | Phạm Đăng Khôi — TV2 |
| Nhóm công việc | Thuật toán cốt lõi (`CFG → CNF`) |
| Hàm chính | `removeEpsilon`, `find_nullable_variables`, `addFreshStart` |
| Nhánh GitHub | `feature/T04-remove-epsilon` |
| Repository | `cfg-cnf-cyk-visualizer` |
| Mục báo cáo liên quan | R05 (chính), đóng góp R10 |
| Thời gian dự kiến | 25/11/2026 – 26/11/2026 |

---

## 2. Mục tiêu và phạm vi

### 2.1. Mục tiêu

- Tự cài đặt thuật toán tìm tập biến có thể triệt tiêu (**nullable variables**) bằng lặp điểm cố định (*fixed-point iteration*) đến khi tập không đổi.
- Tự cài đặt thuật toán thêm ký hiệu bắt đầu mới (`addFreshStart`) và loại bỏ toàn bộ $\varepsilon$-production (`removeEpsilon`) nhưng bảo toàn chính xác ngôn ngữ $L(G)$, kể cả trường hợp $\varepsilon \in L(G)$.
- Thiết kế cấu trúc log chi tiết (`RemoveEpsilonResult`, `EpsilonStepLog`, `RuleChange`) hỗ trợ trực quan hóa từng bước trên giao diện và chuẩn bị cho module diagnostics ở **T12**.
- Đảm bảo tính **bất biến đầu vào** (*immutability* — không sửa trực tiếp đối tượng `Grammar` gốc) và tính **xác định** (*determinism*).
- Kiểm thử tự động đầy đủ bằng Pytest cho các trường hợp chuẩn, trường hợp phức tạp và trường hợp biên.

### 2.2. Phạm vi

- **Trong phạm vi T04:** Tìm tập biến nullable, tạo ký hiệu bắt đầu mới `S0` không trùng tên khi cần, sinh mọi biến thể luật sinh hợp lệ khi loại bỏ biến nullable, loại bỏ luật trùng, xóa mọi luật sinh $\varepsilon$ không thuộc ngoại lệ `S0 -> ε`, ghi log và cảnh báo.
- **Ngoài phạm vi T04:**
  - Loại bỏ luật sinh đơn vị (*unit productions*, bao gồm self-loop $A \to A$ có thể phát sinh sau khi bỏ nullable) — do TV3 thực hiện ở **T06**.
  - Loại bỏ ký hiệu vô ích (*non-generating* và *unreachable*, kể cả các biến không còn luật sinh sau khi bỏ $\varepsilon$) — do TV5 thực hiện ở **T07**.
  - Thay terminal trong luật dài và binarization — do TV3 thực hiện ở **T08**.
  - Kiểm chứng CNF tổng thể — do TV2 thực hiện ở **T09**.

---

## 3. Cơ sở lý thuyết (R05)

### 3.1. Luật sinh ε và biến Nullable

Cho văn phạm phi ngữ cảnh (CFG) $G = (V, \Sigma, P, S)$ [1], [2]:

- Một **luật sinh $\varepsilon$** ($\varepsilon$-production) là luật sinh có dạng:

$$A \to \varepsilon \quad (A \in V)$$

- Một biến $A \in V$ được gọi là **biến có thể triệt tiêu** (*nullable variable*) nếu tồn tại dẫn xuất không bước hoặc nhiều bước từ $A$ sang chuỗi rỗng:

$$A \Rightarrow_G^* \varepsilon$$

Tập các biến nullable $N \subseteq V$ được đặc trưng đệ quy bởi hai quy tắc [1], [3]:
1. **Cơ sở:** Nếu $A \to \varepsilon \in P$ thì $A \in N$.
2. **Quy nạp:** Nếu $B \to C_1 C_2 \dots C_k \in P$ với mọi $C_i \in N$ ($1 \le i \le k$) thì $B \in N$.

### 3.2. Vai trò trong pipeline chuyển CFG → CNF (liên kết R10)

Theo Định nghĩa dạng chuẩn Chomsky (CNF) [1], [2], mọi luật sinh chỉ được phép có dạng $A \to BC$ ($B, C \in V$) hoặc $A \to a$ ($a \in \Sigma$). Ngoại lệ duy nhất cho phép là $S_0 \to \varepsilon$ khi và chỉ khi:

1. Chuỗi rỗng thuộc ngôn ngữ của văn phạm ($\varepsilon \in L(G)$), và
2. Ký hiệu bắt đầu $S_0$ **không xuất hiện ở vế phải** của bất kỳ luật sinh nào trong $P$.

Trong pipeline chuẩn hóa `CFG → CNF` của dự án, thứ tự thực hiện là:

```text
CFG gốc
  → Bước 1: Thêm ký hiệu bắt đầu mới S0 (khi cần) & Loại bỏ ε-production (T04)
  → Bước 2: Loại bỏ luật sinh đơn vị — unit-closure (T06)
  → Bước 3: Loại bỏ ký hiệu vô ích — generating trước, reachable sau (T07)
  → Bước 4: Thay terminal trong vế phải dài & Binarization (T08)
  → Bước 5: Kiểm chứng dạng chuẩn Chomsky — validateCNF (T09)
```

Loại $\varepsilon$-production **phải đứng trước** bước loại unit production (T06) vì khi bỏ biến nullable trong luật dạng $A \to BC$ (với $C \in N$), ta có thể sinh thêm luật đơn vị mới $A \to B$. Nếu chạy T06 trước T04 thì các luật đơn vị mới này sẽ bị sót lại.

### 3.3. Định lý bảo toàn ngôn ngữ

Theo Định lý 5.3 [2], [3]: với mọi CFG $G = (V, \Sigma, P, S)$, xây dựng $P'$ bằng cách lấy mọi luật $A \to X_1 X_2 \dots X_m \in P$ ($m \ge 1$), sinh mọi luật $A \to \alpha_1 \alpha_2 \dots \alpha_m$ sao cho:
- $\alpha_i = X_i$ nếu $X_i \notin N$,
- $\alpha_i \in \{X_i, \varepsilon\}$ nếu $X_i \in N$,
- Không phải tất cả $\alpha_i$ đều bằng $\varepsilon$ (tức $\alpha_1 \dots \alpha_m \neq \varepsilon$),

thì văn phạm $G'' = (V, \Sigma, P', S)$ không chứa luật sinh $\varepsilon$ và thỏa mãn:

$$L(G'') = L(G) \setminus \{\varepsilon\}$$

Để bảo toàn trọn vẹn $L(G)$ kể cả khi $\varepsilon \in L(G)$ và đồng thời đảm bảo điều kiện CNF (ký hiệu bắt đầu không xuất hiện ở vế phải), ta kiểm tra: nếu $S \in N$ hoặc $S$ xuất hiện ở vế phải của bất kỳ luật sinh nào trong $P$, ta tạo biến bắt đầu mới $S_0 \notin V \cup \Sigma$, thêm $S_0 \to S$, và chỉ thêm $S_0 \to \varepsilon$ khi $S \in N$. Khi đó $L(G') = L(G)$ trong mọi trường hợp [1], [2].

---

## 4. Mô hình dữ liệu và Input/Output

### 4.1. Input và Output

- **Input:** `grammar: Grammar` định nghĩa tại `app/models/grammar.py` với 4 thành phần `variables: set[str]`, `terminals: set[str]`, `productions: dict[str, set[tuple[str, ...]]]`, `start_symbol: str` và hằng số `EPSILON = ()`.
- **Output:** Đối tượng `RemoveEpsilonResult`:

| Thành phần | Kiểu dữ liệu | Ý nghĩa |
|---|---|---|
| `grammar` | `Grammar` | Văn phạm mới sau khi loại bỏ $\varepsilon$-production (độc lập với input) |
| `nullable_variables` | `set[str]` | Tập tất cả biến $A$ thỏa $A \Rightarrow^* \varepsilon$ |
| `log` | `EpsilonStepLog` | Nhật ký chi tiết phục vụ hiển thị, chẩn đoán (T12) và kiểm thử |

### 4.2. Cấu trúc log (`EpsilonStepLog` và `RuleChange`)

| Trường của `EpsilonStepLog` | Kiểu dữ liệu | Mô tả |
|---|---|---|
| `step` | `str` | Định danh bước (`"remove_epsilon"`) |
| `nullable_variables` | `list[str]` | Danh sách biến nullable đã sắp xếp |
| `nullable_iterations` | `list[list[str]]` | Biến nullable mới phát hiện ở từng vòng lặp điểm cố định |
| `fresh_start_created` | `bool` | Có tạo ký hiệu bắt đầu mới hay không |
| `old_start_symbol` | `str` | Ký hiệu bắt đầu trước chuyển đổi |
| `new_start_symbol` | `str` | Ký hiệu bắt đầu sau chuyển đổi (`S0`, `S1`, ... hoặc giữ nguyên) |
| `fresh_start_reason` | `str \| None` | Lý do tạo ký hiệu bắt đầu mới |
| `preserves_epsilon` | `bool` | `True` khi giữ `S0 -> ε` vì $\varepsilon \in L(G)$ |
| `rule_count_before` / `rule_count_after` | `int` | Tổng số luật sinh trước và sau bước chuyển đổi |
| `added_rules` / `removed_rules` | `list[RuleChange]` | Danh sách luật thêm/xóa kèm lý do chi tiết |
| `warnings` | `list[str]` | Cảnh báo biên (grammar rỗng, biến hết luật sinh sau khi bỏ $\varepsilon$, ...) |

Cả `RemoveEpsilonResult`, `EpsilonStepLog` và `RuleChange` đều có phương thức `to_dict()` trả về dữ liệu tương thích JSON và được sắp xếp nhất quán (*deterministic*).

---

## 5. Thiết kế thuật toán và Pseudocode

### 5.1. Thuật toán 1 — Tìm tập biến Nullable (`find_nullable_variables`)

```text
ALGORITHM FindNullableVariables(G = (V, Σ, P, S)):
    nullable ← ∅
    iterations ← []

    LOOP:
        newly_nullable ← ∅
        FOR each A ∈ sorted(keys(P)):
            IF A ∈ nullable:
                CONTINUE
            FOR each rhs ∈ P[A]:
                // Với rhs = () (tức ε), điều kiện ∀ X ∈ rhs đúng tầm thường
                IF ∀ X ∈ rhs: X ∈ nullable:
                    newly_nullable ← newly_nullable ∪ {A}
                    BREAK

        IF newly_nullable = ∅:
            BREAK

        nullable ← nullable ∪ newly_nullable
        APPEND sorted(newly_nullable) TO iterations

    RETURN (nullable, iterations)
```

> **Ghi chú cài đặt:** Việc gom `newly_nullable` theo từng lượt đồng bộ (cập nhật `nullable` sau khi duyệt hết toàn bộ biến trong lượt) đảm bảo `nullable_iterations` luôn xác định (*deterministic*), không phụ thuộc thứ tự hash của `dict`/`set` trong Python.

### 5.2. Thuật toán 2 — Sinh ký hiệu bắt đầu mới (`generate_fresh_start_symbol` / `addFreshStart`)

```text
ALGORITHM GenerateFreshStartSymbol(existing_symbols, base = "S"):
    index ← 0
    WHILE TRUE:
        candidate ← base + str(index)      // S0, S1, S2, ...
        IF candidate ∉ existing_symbols:
            RETURN candidate
        index ← index + 1
```

Tên sinh ra (`S0`, `S1`, `S2`, ...) luôn khớp tuyệt đối với quy ước biểu thức chính quy biến `[A-Z][0-9]*'*` trong `app/services/tokenizer.py`.

### 5.3. Thuật toán 3 — Loại bỏ luật sinh ε (`removeEpsilon`)

```text
ALGORITHM RemoveEpsilon(G = (V, Σ, P, S)):
    IF |P| = 0:
        RETURN (copy(G), ∅, log_with_warning("Văn phạm rỗng"))

    (nullable, iterations) ← FindNullableVariables(G)

    start_is_nullable ← (S ∈ nullable)
    start_on_rhs ← (∃ (A → α) ∈ P sao cho S ∈ α)
    need_fresh_start ← start_is_nullable OR start_on_rhs

    IF need_fresh_start:
        S_new ← GenerateFreshStartSymbol(V ∪ Σ)
    ELSE:
        S_new ← S

    G' ← Grammar(V' = copy(V), Σ' = copy(Σ), P' = ∅, start = S_new)
    IF need_fresh_start:
        V' ← V' ∪ {S_new}

    FOR each A ∈ sorted(keys(P)):
        FOR each rhs ∈ sorted(P[A]):
            IF rhs = ε:
                LOG removed (A → ε)
                CONTINUE

            ADD (A → rhs) TO P'
            nullable_positions ← [i | 0 ≤ i < |rhs| và rhs[i] ∈ nullable]
            k ← |nullable_positions|

            FOR mask FROM 1 TO (2^k - 1):
                omitted ← { nullable_positions[b] | bit b của mask = 1 }
                variant ← (rhs[i] | 0 ≤ i < |rhs| và i ∉ omitted)
                IF variant = ε:
                    CONTINUE
                ADD (A → variant) TO P'        // set tự động loại luật trùng
                IF variant ∉ P[A] và (A, variant) chưa log:
                    LOG added (A → variant) kèm tên biến đã bỏ

    IF need_fresh_start:
        ADD (S_new → S) TO P'
        LOG added (S_new → S)
        IF start_is_nullable:
            ADD (S_new → ε) TO P'
            LOG added (S_new → ε)

    RETURN RemoveEpsilonResult(G', nullable, log)
```

---

## 6. Chứng minh điều kiện dừng và tính đúng đắn

### 6.1. Điều kiện dừng

1. **Vòng lặp `FindNullableVariables`:**
   - Gọi $N_t$ là tập `nullable` sau lần lặp thứ $t$ ($N_0 = \emptyset$).
   - Nếu vòng lặp chưa dừng ở lần $t + 1$ thì `newly_nullable` $\neq \emptyset$ và `newly_nullable` $\cap N_t = \emptyset$, do đó:
     $$|N_{t+1}| \ge |N_t| + 1$$
   - Vì $N_t \subseteq V$ và tập biến $V$ hữu hạn ($|V| < \infty$), số lần lặp bị chặn trên chặt bởi $|V| + 1$.
   - Ngay cả khi văn phạm chứa chu trình biến (ví dụ $A \to B, B \to A$ hoặc $A \to B, B \to A \mid \varepsilon$), thuật toán vẫn dừng chắc chắn vì mỗi biến chỉ được thêm vào `nullable` tối đa 1 lần.
2. **Vòng lặp `GenerateFreshStartSymbol`:** Tập `existing_symbols` $= V \cup \Sigma$ hữu hạn, nên sau tối đa $|V| + |\Sigma| + 1$ lần thử chỉ số `index`, chắc chắn tìm được ứng viên `S{index}` chưa tồn tại.
3. **Vòng lặp sinh tổ hợp `mask`:** Mỗi luật $A \to \alpha$ có độ dài hữu hạn $|\alpha|$, số vị trí nullable $k \le |\alpha|$ hữu hạn, nên duyệt `mask` từ $1$ đến $2^k - 1$ luôn kết thúc sau hữu hạn bước.

### 6.2. Tính đúng đắn và bảo toàn ngôn ngữ

- **Không còn $\varepsilon$-production sai quy tắc:** Mọi luật $A \to \varepsilon$ gốc đều bị bỏ qua và mọi biến thể `variant == EPSILON` đều bị lọc bỏ. Ngoại lệ duy nhất có thể được thêm vào là $S_{\text{new}} \to \varepsilon$ khi $S \in N$; khi đó $S_{\text{new}}$ là biến mới nên không bao giờ xuất hiện ở vế phải bất kỳ luật nào.
- **Bảo toàn mọi chuỗi khác rỗng ($w \in L(G) \setminus \{\varepsilon\} \iff w \in L(G') \setminus \{\varepsilon\}$):** Theo Định lý 5.3 [2], [3], mọi dẫn xuất trong $G$ có sử dụng các biến nullable triệt tiêu thành $\varepsilon$ đều tương ứng trực tiếp với một dẫn xuất trong $G'$ dùng luật biến thể đã bỏ các vị trí nullable đó, và ngược lại.
- **Bảo toàn chuỗi rỗng ($\varepsilon \in L(G) \iff \varepsilon \in L(G')$):** $\varepsilon \in L(G) \iff S \Rightarrow_G^* \varepsilon \iff S \in N \iff (S_{\text{new}} \to \varepsilon) \in P' \iff \varepsilon \in L(G')$.

---

## 7. Phân tích độ phức tạp

Gọi $|V|$ là số biến, $|P|$ là tổng số luật sinh, $L = \sum_{(A \to \alpha) \in P} |\alpha|$ là tổng độ dài vế phải của văn phạm, và $k = \max_{(A \to \alpha) \in P} |\{i \mid \alpha_i \in N\}|$ là số lần xuất hiện biến nullable tối đa trên một vế phải.

| Thành phần | Độ phức tạp thời gian | Độ phức tạp bộ nhớ | Giải thích |
|---|---|---|---|
| `find_nullable_variables` | $O(|V| \cdot (|P| + L))$ | $O(|V|)$ | Tối đa $|V| + 1$ vòng lặp, mỗi vòng duyệt qua các luật sinh và kiểm tra ký hiệu vế phải |
| Kiểm tra `S` ở RHS & `generate_fresh_start_symbol` | $O(L + |V| + |\Sigma|)$ | $O(|V| + |\Sigma|)$ | Quét một lượt các vế phải và tìm chỉ số trống |
| Sinh biến thể tổ hợp & loại trùng | $O\left(\sum_{p \in P} |\alpha_p| \cdot 2^{k_p}\right) = O(|P| \cdot m \cdot 2^k)$ | $O(|P| \cdot 2^k)$ | Với mỗi luật có $k_p$ biến nullable ở vế phải, sinh tối đa $2^{k_p} - 1$ biến thể (với $m = \max |\alpha_p|$) |
| Sắp xếp log (deterministic) | $O(|P'| \log |P'|)$ | $O(|P'|)$ | Với $|P'|$ là số luật sau chuyển đổi |
| **Tổng cộng** | **$O(|V| \cdot L + |P| \cdot m \cdot 2^k)$** | **$O(|V| + |\Sigma| + |P| \cdot 2^k)$** | **Trường hợp xấu nhất phụ thuộc lũy thừa $2^k$ theo số biến nullable trên cùng một vế phải** |

> **Nhận xét về giới hạn lý thuyết:** Khi một luật sinh có rất nhiều biến nullable đứng cùng vế phải (ví dụ $S \to A_1 A_2 \dots A_k$ với $k$ lớn), số luật sinh mới có thể tăng theo hàm mũ $2^k - 1$. Trong thực tế với các văn phạm chuẩn và bài toán dạy học, $k$ thường nhỏ ($k \le 5$), nhưng đây là bản chất toán học của bước loại bỏ $\varepsilon$-production cần lưu ý khi phân tích hiệu năng (T23).

---

## 8. Ví dụ Input và Output thực tế

Xét **Thí dụ 5.10** trong tài liệu môn học [3]:

### Input

```text
S -> AB
A -> aA | ε
B -> bB | ε
```

### Quá trình thực hiện

1. **Tìm tập `nullable`:**
   - Vòng 1: `A -> ε`, `B -> ε` $\implies$ `newly_nullable = ["A", "B"]`.
   - Vòng 2: `S -> AB` (cả `A`, `B` đều nullable) $\implies$ `newly_nullable = ["S"]`.
   - Vòng 3: Không thêm biến mới $\implies$ dừng. Kết quả `nullable = {"A", "B", "S"}`.
2. **Tạo ký hiệu bắt đầu mới:** Vì `S ∈ nullable`, sinh `S0` mới, thêm `S0 -> S` và giữ `S0 -> ε`.
3. **Sinh biến thể và loại luật $\varepsilon$:**
   - `S -> AB` $\implies$ `S -> AB | A | B`.
   - `A -> aA | ε` $\implies$ `A -> aA | a` (xóa `A -> ε`).
   - `B -> bB | ε` $\implies$ `B -> bB | b` (xóa `B -> ε`).

### Output JSON thực tế từ `removeEpsilon(grammar).to_dict()`

```json
{
  "grammar": {
    "variables": ["A", "B", "S", "S0"],
    "terminals": ["a", "b"],
    "productions": {
      "A": [["a"], ["a", "A"]],
      "B": [["b"], ["b", "B"]],
      "S": [["A"], ["A", "B"], ["B"]],
      "S0": [[], ["S"]]
    },
    "start_symbol": "S0"
  },
  "nullable_variables": ["A", "B", "S"],
  "log": {
    "step": "remove_epsilon",
    "nullable_variables": ["A", "B", "S"],
    "nullable_iterations": [["A", "B"], ["S"]],
    "fresh_start_created": true,
    "old_start_symbol": "S",
    "new_start_symbol": "S0",
    "fresh_start_reason": "Ký hiệu bắt đầu S có thể sinh chuỗi rỗng ε.",
    "preserves_epsilon": true,
    "rule_count_before": 5,
    "rule_count_after": 9,
    "added_rules": [
      { "action": "added", "lhs": "A", "rhs": ["a"], "rule": "A -> a", "reason": "Sinh từ A -> a A khi loại bỏ biến nullable (A)." },
      { "action": "added", "lhs": "B", "rhs": ["b"], "rule": "B -> b", "reason": "Sinh từ B -> b B khi loại bỏ biến nullable (B)." },
      { "action": "added", "lhs": "S", "rhs": ["A"], "rule": "S -> A", "reason": "Sinh từ S -> A B khi loại bỏ biến nullable (B)." },
      { "action": "added", "lhs": "S", "rhs": ["B"], "rule": "S -> B", "reason": "Sinh từ S -> A B khi loại bỏ biến nullable (A)." },
      { "action": "added", "lhs": "S0", "rhs": [], "rule": "S0 -> ε", "reason": "Giữ lại S0 -> ε để bảo toàn chuỗi rỗng ε ∈ L(G)." },
      { "action": "added", "lhs": "S0", "rhs": ["S"], "rule": "S0 -> S", "reason": "Thêm luật cho ký hiệu bắt đầu mới: Ký hiệu bắt đầu S có thể sinh chuỗi rỗng ε." }
    ],
    "removed_rules": [
      { "action": "removed", "lhs": "A", "rhs": [], "rule": "A -> ε", "reason": "Loại bỏ luật sinh ε: A -> ε" },
      { "action": "removed", "lhs": "B", "rhs": [], "rule": "B -> ε", "reason": "Loại bỏ luật sinh ε: B -> ε" }
    ],
    "warnings": []
  }
}
```

---

## 9. Cấu trúc mã nguồn liên quan

| File | Trạng thái | Chức năng |
|---|---|---|
| `app/algorithms/cnf/remove_epsilon.py` | Tạo mới | Cài đặt `find_nullable_variables`, `generate_fresh_start_symbol`, `addFreshStart`, `removeEpsilon` và các dataclass log |
| `app/algorithms/cnf/__init__.py` | Cập nhật | Re-export API công khai của module loại bỏ $\varepsilon$ |
| `tests/test_remove_epsilon.py` | Tạo mới | Bộ 52 unit test tự động cho T04 |
| `docs/contributions/TV2/T04-remove-epsilon.md` | Tạo mới | Tài liệu đóng góp kỹ thuật phục vụ R05, R10 và bảo vệ |

---

## 10. Kiểm thử và kết quả thực tế

### 10.1. Môi trường kiểm thử

- Hệ điều hành: Windows
- Python local: `3.13.7` (cú pháp tương thích hoàn toàn Python `3.11` của GitHub Actions CI)
- Pytest: `9.2.0`
- Môi trường ảo: `.venv` cài theo `requirements.txt`

### 10.2. Lệnh chạy kiểm thử

```powershell
# Chạy riêng bộ test T04
.venv\Scripts\python -m pytest tests/test_remove_epsilon.py -v

# Chạy toàn bộ bộ test dự án
.venv\Scripts\python -m pytest -v
```

### 10.3. Bảng tổng hợp kết quả

| Nhóm kiểm thử | Số test | PASS | FAIL |
|---|---:|---:|---:|
| Tìm tập biến nullable (`find_nullable_variables`) | 10 | 10 | 0 |
| Sinh tên & `addFreshStart` | 8 | 8 | 0 |
| Loại $\varepsilon$-production & tổ hợp (`removeEpsilon`) | 9 | 9 | 0 |
| Tạo `S0` mới & bảo toàn chuỗi rỗng | 5 | 5 | 0 |
| Trường hợp biên, bất biến, determinism & log | 12 | 12 | 0 |
| Đối chiếu bảo toàn ngôn ngữ $L(G') = L(G)$ (BFS) & lặp lần 2 | 8 | 8 | 0 |
| **Tổng riêng T04 (`tests/test_remove_epsilon.py`)** | **52** | **52** | **0** |
| T01 Flask skeleton (`tests/test_app.py`) | 4 | 4 | 0 |
| T02 Parser CFG (`tests/test_parser.py`) | 46 | 46 | 0 |
| **Tổng toàn dự án** | **102** | **102** | **0** |

### 10.4. Các trường hợp biên đã kiểm chứng

| Trường hợp biên | Hành vi mong đợi & kết quả thực tế |
|---|---|
| Nhiều biến nullable liên tiếp (`S -> AAA`, `A -> a \| ε`) | Sinh đủ `AAA`, `AA`, `A`, không trùng luật và không trùng log `added_rules` (PASS) |
| Nullable gián tiếp nhiều tầng (`S -> AB`, `A -> C`, `C -> ε`, ...) | Lặp điểm cố định hội tụ đúng từng tầng `nullable_iterations` (PASS) |
| Chu trình có $\varepsilon$ (`A -> B`, `B -> A \| ε`) & không có $\varepsilon$ (`A -> B`, `B -> A`) | Dừng sau hữu hạn vòng lặp, không lặp vô hạn (PASS) |
| `S` sinh $\varepsilon$ và xuất hiện ở vế phải (`S -> aSb \| ε`) | Tạo `S0 -> S \| ε`, `S -> aSb \| ab`, `S0` không ở vế phải (PASS) |
| `S` không sinh $\varepsilon$ nhưng xuất hiện ở vế phải (`S -> aS \| a`) | Tạo `S0 -> S`, **không** thêm `S0 -> ε` (PASS) |
| Tên `S0` đã tồn tại trong `V` (`S -> S0 \| ε`, `S0 -> a`) | Tự động sinh `S1` không trùng tên và khớp regex biến tokenizer (PASS) |
| Văn phạm chỉ sinh chuỗi rỗng (`S -> ε`) | Tạo `S0 -> S \| ε`, ghi cảnh báo biến `S` không còn luật sinh (PASS) |
| Văn phạm rỗng (`Grammar()`) | Không crash, trả bản sao mới kèm cảnh báo rõ ràng (PASS) |
| Văn phạm không có $\varepsilon$ và `S` không ở vế phải | Giữ nguyên tập luật, không sinh `S0` thừa (PASS) |
| Đầu vào sai kiểu (`None`, `str`, `int`, `list`) | Ném `TypeError` rõ ràng (PASS) |
| Bất biến đầu vào (*Immutability*) | Snapshot `deepcopy` của `Grammar` trước/sau không đổi 100% (PASS) |
| Tính xác định (*Determinism*) | Chạy nhiều lần trả về cùng JSON `to_dict()` (PASS) |

---

## 11. Hạn chế hiện tại và hướng phát triển

### 11.1. Hạn chế

- **Bùng nổ tổ hợp luật sinh $O(2^k)$:** Nếu một vế phải chứa quá nhiều biến nullable đồng thời, số biến thể sinh ra tăng theo hàm mũ.
- **Chưa loại unit production và ký hiệu vô ích trong cùng bước:** Một số luật đơn vị (kể cả self-loop như $A \to A$ từ $A \to SA$ trong Bài tập 5.10) hoặc biến không còn luật sinh (như `A` trong `A -> ε`) vẫn tồn tại sau T04 và cần **T06 (`removeUnit`)** và **T07 (`removeUseless`)** dọn sạch ở các bước tiếp theo.
- **Chưa tích hợp vào endpoint Flask:** Endpoint `/api/normalize` và pipeline hợp nhất sẽ được nối ở các task sau (T12, T21A).

### 11.2. Hướng phát triển

- Mở rộng ma trận kiểm thử tích hợp Parser + `removeEpsilon` trong **T05**.
- Xây dựng bộ kiểm chứng dạng chuẩn `validateCNF` ở **T09**.
- Chuẩn hóa lớp trace/diagnostics chung cho toàn bộ pipeline `CFG → CNF` và bộ test bất biến input tổng quát ở **T12**.

---

## 12. Nội dung cần nắm khi bảo vệ cá nhân (TV2)

1. Định nghĩa biến **nullable** ($A \Rightarrow^* \varepsilon$) và phân biệt với luật sinh $\varepsilon$ trực tiếp ($A \to \varepsilon$).
2. Cách hoạt động của **lặp điểm cố định** và chứng minh điều kiện dừng sau tối đa $|V| + 1$ vòng lặp (đặc biệt khi văn phạm có chu trình $A \to B \to A$).
3. Cách dùng bitmask `1 .. (2^k - 1)` để sinh đủ mọi biến thể khi bỏ các tập con biến nullable và lý do bỏ tổ hợp rỗng `()`.
4. Vì sao cần tạo ký hiệu bắt đầu mới `S0` trong hai tình huống ($S \in \text{nullable}$ hoặc $S$ xuất hiện ở vế phải), và vì sao chỉ giữ $S_0 \to \varepsilon$ khi ngôn ngữ chứa $\varepsilon$.
5. Cách tránh trùng tên biến khi `S0` đã tồn tại và đảm bảo tương thích với quy ước tokenizer `[A-Z][0-9]*'*`.
6. Lý do thứ tự pipeline phải đặt `removeEpsilon` (T04) **trước** `removeUnit` (T06) và `removeUseless` (T07).
7. Độ phức tạp thời gian/bộ nhớ, đặc biệt trường hợp xấu nhất $O(|P| \cdot m \cdot 2^k)$.
8. Lý do cần bảo đảm tính bất biến đầu vào (*immutability*) và tính xác định (*determinism*) cho pipeline và test.

---

## 13. Minh chứng cần bổ sung trước khi tổng hợp báo cáo

- [ ] Ảnh chụp kết quả chạy `.venv\Scripts\python -m pytest tests/test_remove_epsilon.py -v` (52 passed).
- [ ] Ảnh chụp kết quả chạy `.venv\Scripts\python -m pytest -v` toàn dự án (102 passed).
- [ ] Link Pull Request nhánh `feature/T04-remove-epsilon` vào `develop`.
- [ ] Ảnh xác nhận 2 job GitHub Actions (`CI / test` và `CI / docker-build`) xanh sau khi đẩy PR.

---

## 14. Tài liệu tham khảo

1. Sipser, M. (2012). *Introduction to the Theory of Computation* (3rd ed.). Cengage Learning. (Chương 2: Context-Free Languages — Chomsky Normal Form).
2. Hopcroft, J. E., Motwani, R., & Ullman, J. D. (2006). *Introduction to Automata Theory, Languages, and Computation* (3rd ed.). Pearson Education. (Chương 7: Properties of Context-Free Languages — Simplification of CFGs).
3. Giáo trình & Slide học phần *Ngôn ngữ hình thức* — Chương *Văn phạm phi ngữ cảnh* (`Chuong4_FCG.pdf`, `van-pham-phi-ngu-canh.pdf`, tài liệu lưu hành nội bộ môn học).

---

## 15. Khai báo sử dụng AI

- **Công cụ sử dụng:** Trợ lý AI hỗ trợ lập trình trong quá trình thiết kế cấu trúc log, rà soát các trường hợp biên, gợi ý kịch bản unit test và hoàn thiện bố cục tài liệu Markdown.
- **Phần tự kiểm chứng:** Toàn bộ thuật toán `find_nullable_variables`, `addFreshStart`, `removeEpsilon` được đối chiếu trực tiếp với Định lý 5.3 trong giáo trình môn học, chạy kiểm thử tự động trên 52 unit test (102 test toàn dự án đều PASS), bao gồm đối chiếu bảo toàn ngôn ngữ trên các ví dụ giáo trình và slide bài giảng. Thành viên TV2 nắm rõ từng dòng mã và chịu trách nhiệm giải thích khi bảo vệ.
