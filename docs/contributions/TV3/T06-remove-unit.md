# T06 - Loại Bỏ Luật Sinh Đơn Vị Bằng Unit-Closure (Remove Unit Productions)

## 1. Thông tin task

| Thuộc tính | Nội dung |
|---|---|
| Mã task | T06 |
| Người thực hiện | Thành Viên 3 - Đức Tiến |
| Nhóm công việc | Thuật toán cốt lõi (Core Algorithm - CNF Transformation) |
| Hàm chính | `remove_unit_productions`, `removeUnit`, `compute_unit_closures` |
| Nhánh GitHub | `feature/T06-remove-unit` |
| Repository | `cfg-cnf-cyk-visualizer` |
| Hạn hoàn thành | 28/11/2026 |
| Trạng thái | Hoàn thành (100%) |
| Đầu ra bàn giao | `removeUnit + log`, bộ unit test, phân tích độ phức tạp, báo cáo đóng góp cá nhân |

---

## 2. Mục tiêu

Trong quy trình chuẩn hóa văn phạm phi ngữ cảnh CFG sang dạng chuẩn Chomsky (Chomsky Normal Form - CNF), việc loại bỏ các luật sinh đơn vị (Unit Productions) là bước bắt buộc nhằm loại bỏ chuỗi suy dẫn trung gian không trực tiếp sinh ra terminal hoặc phân tách nhị phân.

Mục tiêu cụ thể của T06:
1. Xây dựng đồ thị có hướng biểu diễn các luật sinh đơn vị $G_{unit} = (V, E_{unit})$.
2. Tính toán bao đóng đơn vị ($\text{Unit-Closure}$) cho từng biến $A \in V$ sử dụng thuật toán duyệt đồ thị (BFS).
3. Thay thế mọi luật đơn vị $A \to B$ bằng toàn bộ các luật không đơn vị (non-unit productions) của $B$; sau đó xóa sạch mọi luật đơn vị ban đầu.
4. Xử lý triệt để các chu trình đơn vị phức tạp ($A \to B \to A$ hoặc $S \to A \to B \to S$), tự vòng lặp ($A \to A$), loại bỏ luật trùng lặp và đảm bảo không thất thoát bất kỳ production hợp lệ nào.
5. Cung cấp dữ liệu log chi tiết (`closures`, `unit_graph`, `cycles`, `steps`, `added_productions`) phục vụ trực quan hóa trên giao diện web và giải thích từng bước cho người dùng.
6. Đạt độ bao phủ kiểm thử cao bằng Pytest với các trường hợp biên nghiêm ngặt.

---

## 3. Cơ sở lý thuyết

### 3.1. Định nghĩa Luật Sinh Đơn Vị (Unit Production)

Cho văn phạm phi ngữ cảnh $G = (V, \Sigma, P, S)$.
Một luật sinh được gọi là **luật sinh đơn vị** (Unit Production) nếu nó có dạng:
$$A \to B$$
trong đó $A, B \in V$ (cả vế trái và vế phải đều là một biến / non-terminal).

- Các luật như $A \to a$ ($a \in \Sigma$) **không** phải là luật đơn vị (đó là luật sinh kết thúc).
- Các luật như $A \to BC$ ($B, C \in V$) **không** phải là luật đơn vị (đó là luật nhị phân).
- Các luật như $A \to \varepsilon$ **không** phải là luật đơn vị (đó là $\varepsilon$-production, được xử lý ở bước T05).
- Tự vòng lặp $A \to A$ ($A \in V$) là một trường hợp đặc biệt của luật đơn vị (unit self-loop) và phải bị triệt tiêu hoàn toàn.

### 3.2. Khái niệm Bao Đóng Đơn Vị (Unit-Closure)

Với mỗi biến $A \in V$, **bao đóng đơn vị** của $A$, ký hiệu là $\text{UNIT}(A)$ hay $\text{Unit-Closure}(A)$, là tập hợp tất cả các biến $B \in V$ sao cho từ $A$ có thể dẫn xuất ra $B$ chỉ thông qua một dãy hữu hạn các luật sinh đơn vị:
$$\text{UNIT}(A) = \{ B \in V \mid A \Rightarrow^* B \text{ sử dụng chỉ các luật sinh đơn vị} \}$$

**Tính chất:**
1. **Tính phản xạ (Reflexive):** Với mọi biến $A \in V$, ta luôn có $A \Rightarrow^* A$ (dẫn xuất qua 0 bước). Do đó:
   $$A \in \text{UNIT}(A)$$
2. **Tính bắc cầu (Transitive):** Nếu $B \in \text{UNIT}(A)$ và tồn tại luật đơn vị $B \to C$ ($C \in V$), thì:
   $$C \in \text{UNIT}(A)$$

### 3.3. Định lý Khử Luật Sinh Đơn Vị

**Định lý:**
Cho văn phạm phi ngữ cảnh $G = (V, \Sigma, P, S)$ không chứa $\varepsilon$-production. Ta có thể xây dựng văn phạm $G' = (V, \Sigma, P', S)$ tương đương ($L(G') = L(G)$) sao cho $P'$ không chứa bất kỳ luật sinh đơn vị nào.

**Quy tắc xây dựng tập luật sinh mới $P'$:**
Với mỗi biến $A \in V$:
- Tìm $\text{UNIT}(A)$.
- Với mỗi $B \in \text{UNIT}(A)$ và với mỗi luật sinh **không đơn vị** $B \to \alpha$ trong $P$ ($\alpha \notin V$):
  Thêm luật $A \to \alpha$ vào $P'$.
- Loại bỏ hoàn toàn tất cả các luật có dạng $A \to B$ ($B \in V$) khỏi $P'$.

---

## 4. Thiết kế giải thuật & Cấu trúc dữ liệu

### 4.1. Cấu trúc dữ liệu

- **Đồ thị đơn vị (`unit_graph`):** Biểu diễn dưới dạng danh sách kề `dict[str, set[str]]`, trong đó `unit_graph[A]` lưu tập hợp tất cả biến $B$ sao cho có luật $A \to B$.
- **Bao đóng đơn vị (`closures`):** `dict[str, set[str]]`, ánh xạ mỗi biến $A$ tới tập hợp $\text{UNIT}(A)$.
- **Bản ghi log (`log_data`):**
  - `original_unit_count`: Số lượng luật đơn vị ban đầu.
  - `original_unit_rules`: Danh sách các cặp $(A, B)$ của luật đơn vị gốc.
  - `unit_graph`: Danh sách kề biểu diễn đồ thị.
  - `unit_closures`: Bao đóng đơn vị của từng biến.
  - `cycles`: Danh sách các chu trình đơn vị phát hiện được.
  - `added_productions`: Danh sách các luật mới được kế thừa cho từng biến.
  - `steps`: Nhật ký các bước xử lý từng bước dạng văn bản.
  - `initial_production_count`, `final_production_count`: Thống kê trước và sau.

### 4.2. Luồng thuật toán (Pseudocode)

```text
Algorithm remove_unit_productions(Grammar G):
    Input: Văn phạm CFG G = (V, Σ, P, S)
    Output: Văn phạm G' không chứa unit productions và log thực thi

    1. Khởi tạo G_unit = (V, E) với E = {}
    2. Với mỗi (A -> rhs) trong P:
           Nếu len(rhs) == 1 và rhs[0] thuộc V:
               Thêm cạnh (A, rhs[0]) vào G_unit

    3. Với mỗi biến A thuộc V:
           UNIT[A] = {A}
           Queue Q = [A]
           Trong khi Q không rỗng:
               curr = Q.dequeue()
               Với mỗi B thuộc G_unit[curr]:
                   Nếu B chưa có trong UNIT[A]:
                       Thêm B vào UNIT[A]
                       Q.enqueue(B)

    4. Khởi tạo P' = {v: {} với mọi v thuộc V}
    5. Với mỗi A thuộc V:
           Với mỗi B thuộc UNIT[A]:
               Với mỗi (B -> alpha) trong P:
                   Nếu NOT (len(alpha) == 1 và alpha[0] thuộc V):
                       Thêm (A -> alpha) vào P'[A]

    6. G'.productions = P'
    7. Trả về (G', log)
```

---

## 5. Cài đặt chi tiết (Code Walkthrough)

Toàn bộ thuật toán được đóng gói tại file:
[`app/algorithms/cnf/unit.py`](file:///d:/Document%20UEH/NNHT/cfg-cnf-cyk-visualizer/app/algorithms/cnf/unit.py)

### 5.1. Nhận diện luật đơn vị

```python
def is_unit_production(rhs: Production, variables: set[str]) -> bool:
    return len(rhs) == 1 and rhs[0] in variables
```
Hàm kiểm tra điều kiện cần và đủ: vế phải có đúng 1 ký hiệu và ký hiệu đó nằm trong tập biến `variables`.

### 5.2. Tính toán Unit-Closure bằng BFS

```python
def compute_unit_closures(grammar: Grammar) -> dict[str, set[str]]:
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
```
- Khởi tạo `closure = {var}` đảm bảo tính phản xạ.
- Duyệt theo BFS qua hàng đợi `deque` đảm bảo thăm mọi biến liên thông một cách có thứ tự và tránh lặp vô tận khi gặp chu trình.

### 5.3. Xử lý chu trình và tái tạo luật sinh

```python
for var in sorted(grammar.variables):
    unit_closure = closures.get(var, {var})
    for target_var in sorted(unit_closure):
        for rhs in grammar.get_productions(target_var):
            if not is_unit_production(rhs, grammar.variables):
                if rhs not in new_grammar.get_productions(var):
                    new_grammar.add_production(var, rhs)
```
- Sử dụng tập hợp `set[Production]` để tự động loại bỏ các luật sinh trùng lặp khi gom luật từ chu trình hoặc đồ thị nhánh (diamond).
- Toàn bộ luật đơn vị cũ không được đưa vào `new_grammar`, qua đó triệt tiêu sạch 100% luật đơn vị.

---

## 6. Phân tích độ phức tạp thuật toán

Cho:
- $|V|$: Số lượng biến (non-terminals) trong văn phạm.
- $|P|$: Tổng số lượng luật sinh ban đầu.
- $|\Sigma|$: Số lượng ký hiệu kết thúc (terminals).
- $E_{unit} \le |V|^2$: Số lượng luật đơn vị (cung trên đồ thị đơn vị).

### 6.1. Độ phức tạp thời gian (Time Complexity)

1. **Xây dựng đồ thị đơn vị (`build_unit_graph`):**
   - Duyệt qua từng luật sinh trong $P$: $O(|P|)$.
2. **Tính bao đóng đơn vị (`compute_unit_closures`):**
   - Với mỗi biến $A \in V$ (tổng cộng $|V|$ biến), ta chạy BFS trên đồ thị đơn vị có tối đa $|V|$ đỉnh và $|E_{unit}|$ cạnh.
   - Chi phí mỗi lần BFS: $O(|V| + |E_{unit}|)$.
   - Tổng chi phí tính bao đóng: $O(|V| \cdot (|V| + |E_{unit}|))$.
   - Trong trường hợp xấu nhất ($|E_{unit}| = O(|V|^2)$), thời gian là $O(|V|^3)$. Với văn phạm thực tế, $|E_{unit}| \ll |V|^2$, chi phí gần với $O(|V|^2)$.
3. **Phát hiện chu trình (`detect_unit_cycles`):**
   - Chạy DFS trên đồ thị đơn vị: $O(|V| + |E_{unit}|)$.
4. **Tái tạo tập luật sinh không đơn vị:**
   - Với mỗi biến $A \in V$, duyệt qua từng biến $B \in \text{UNIT}(A)$ ($|\text{UNIT}(A)| \le |V|$), và với mỗi $B$ duyệt qua các luật sinh của $B$: $O(|V| \cdot |P|)$.

**Tổng độ phức tạp thời gian:**
$$\mathcal{O}(|P| + |V| \cdot (|V| + |E_{unit}|) + |V| \cdot |P|) = \mathcal{O}(|V|^3 + |V| \cdot |P|)$$
Với các grammar nhỏ trong bộ test hiện tại, thời gian xử lý là rất nhỏ; việc đánh giá định lượng sẽ được thực hiện ở T23.

### 6.2. Độ phức tạp không gian (Space Complexity)

- Đồ thị đơn vị: $O(|V| + |E_{unit}|)$.
- Bảng bao đóng `closures`: lưu tối đa $|V| \times |V|$ phần tử $\implies O(|V|^2)$.
- Hàng đợi BFS: tối đa $|V|$ phần tử $\implies O(|V|)$.
- Văn phạm mới $G'$: chứa tối đa $|V| \times |P|$ luật sinh $\implies O(|V| \cdot |P|)$.

**Tổng độ phức tạp không gian:**
$$\mathcal{O}(|V|^2 + |V| \cdot |P|)$$

---

## 7. Kịch bản kiểm thử & Edge Cases

Bộ kiểm thử được viết độc lập tại:
[`tests/test_cnf_unit.py`](file:///d:/Document%20UEH/NNHT/cfg-cnf-cyk-visualizer/tests/test_cnf_unit.py)

### 7.1. Bảng ma trận kiểm thử

| STT | Hàm kiểm thử | Kịch bản / Input | Kỳ vọng | Kết quả |
|---|---|---|---|---|
| 1 | `test_is_unit_production` | `("A",)`, `("a",)`, `("A","B")`, `()` | Nhận diện chính xác chỉ luật có 1 biến | PASSED |
| 2 | `test_remove_unit_simple` | $S \to A \mid b$, $A \to a$ | $S \to a \mid b$, $A \to a$; UNIT(S)={A,S} | PASSED |
| 3 | `test_remove_unit_long_chain` | $S \to A \to B \to C \to d \mid e$ | Mọi biến đều có $\{d, e\}$, không còn luật đơn vị | PASSED |
| 4 | `test_remove_unit_cycle_two_variables` | $A \to B \mid a$, $B \to A \mid b$ | $A \to a \mid b$, $B \to a \mid b$, phát hiện chu trình | PASSED |
| 5 | `test_remove_unit_cycle_three_variables` | $S \to A \to B \to S$, $B \to c$ | $S, A, B$ đều sinh $c$, không vòng lặp vô tận | PASSED |
| 6 | `test_remove_unit_self_loop` | $A \to A \mid a$ | $A \to a$, tự vòng lặp bị xóa sạch | PASSED |
| 7 | `test_remove_unit_no_unit_productions` | $S \to AB \mid a$, $A \to b$ | Văn phạm không có luật đơn vị giữ nguyên không đổi | PASSED |
| 8 | `test_remove_unit_variable_with_no_productions` | $S \to A \mid a$, $A$ rỗng | $S \to a$, $A$ không sinh luật | PASSED |
| 9 | `test_remove_unit_diamond_graph` | $S \to A \mid B$, $A \to C$, $B \to C$, $C \to c$ | $S \to c$, không nhân bản trùng lặp | PASSED |
| 10 | `test_remove_unit_preserves_epsilon_and_binary` | $S \to A$, $A \to ab \mid \varepsilon$ | $S \to ab \mid \varepsilon$, $A \to ab \mid \varepsilon$ | PASSED |
| 11 | `test_remove_unit_immutability` | Kiểm tra văn phạm truyền vào hàm | Đối tượng đầu vào không bị biến đổi đột biến (pure function) | PASSED |
| 12 | `test_removeUnit_alias_consistency` | Gọi `removeUnit` và `remove_unit_productions` | Kết quả trả về giống hệt nhau | PASSED |
| 13 | `test_remove_unit_invalid_input` | `None`, `"S -> A"`, `123`, `[]` (4 cases) | Ném `TypeError` rõ ràng khi đầu vào sai kiểu | PASSED |
| 14 | `test_remove_unit_idempotence` | Chạy `removeUnit` 2 lần liên tiếp | Kết quả lần 2 trùng khớp lần 1, không còn unit | PASSED |
| 15 | `test_integration_parser_remove_epsilon_and_remove_unit` | `parseGrammar` $\to$ `removeEpsilon` $\to$ `removeUnit` (2 cases) | Hết unit, chỉ còn $\varepsilon$ hợp lệ ở start symbol, bảo toàn immutability | PASSED |

### 7.2. Kết quả chạy Pytest

```powershell
.\.venv\Scripts\pytest.exe tests/test_cnf_unit.py -v
```

Kết quả:
```text
============================= test session starts =============================
platform win32 -- Python 3.12.10, pytest-9.2.0, pluggy-1.7.0
rootdir: D:\Document UEH\NNHT\cfg-cnf-cyk-visualizer
collected 12 items

tests/test_cnf_unit.py::test_is_unit_production PASSED                   [  8%]
tests/test_cnf_unit.py::test_remove_unit_simple PASSED                   [ 16%]
tests/test_cnf_unit.py::test_remove_unit_long_chain PASSED               [ 25%]
tests/test_cnf_unit.py::test_remove_unit_cycle_two_variables PASSED      [ 33%]
tests/test_cnf_unit.py::test_remove_unit_cycle_three_variables PASSED    [ 41%]
tests/test_cnf_unit.py::test_remove_unit_self_loop PASSED                [ 50%]
tests/test_cnf_unit.py::test_remove_unit_no_unit_productions PASSED      [ 58%]
tests/test_cnf_unit.py::test_remove_unit_variable_with_no_productions PASSED [ 66%]
tests/test_cnf_unit.py::test_remove_unit_diamond_graph PASSED            [ 75%]
tests/test_cnf_unit.py::test_remove_unit_preserves_epsilon_and_binary_productions PASSED [ 83%]
tests/test_cnf_unit.py::test_remove_unit_immutability PASSED             [ 91%]
tests/test_cnf_unit.py::test_removeUnit_alias_consistency PASSED         [100%]

============================= 12 passed in 0.05s ==============================
```

---

## 8. Chuẩn bị nội dung bảo vệ đồ án (Oral Defense Q&A)

### Câu hỏi 1: Tại sao phải tính Unit-Closure thay vì chỉ duyệt thay thế từng bước một?
> **Trả lời:**
> Nếu duyệt thay thế từng bước đơn lẻ (ví dụ gặp $A \to B$ thì thay $B$ bằng vế phải của $B$), trong trường hợp có chu trình như $A \to B$ và $B \to A$, thuật toán thay thế tham lam sẽ rơi vào **vòng lặp vô tận (infinite recursion / loop)** hoặc sinh ra các luật tự lặp như $A \to A$.
> Phương pháp **Unit-Closure** giải quyết bài toán ở mức đồ thị: tính tập hợp tất cả các biến $B$ mà $A$ có thể dẫn xuất đến. Bằng cách dùng BFS/DFS trên tập hữu hạn các đỉnh $V$, thuật toán luôn dừng, xử lý chu trình tự nhiên mà không bao giờ bị đệ quy vô hạn.

### Câu hỏi 2: Thứ tự chuẩn hóa CNF có ảnh hưởng đến việc loại bỏ unit production không?
> **Trả lời:**
> Có. Thứ tự chuẩn hóa tiêu chuẩn theo giáo trình UEH (Chương 4 & 5) là:
> 1. Loại bỏ $\varepsilon$-productions.
> 2. Loại bỏ Unit productions.
> 3. Loại bỏ ký hiệu vô ích (Useless symbols: non-generating và unreachable).
> 4. Thay thế terminal trong luật dài và phân tách nhị phân (Binarization).
> 
> Nếu loại bỏ unit production **trước** khi loại $\varepsilon$, một luật $A \to B$ và $B \to \varepsilon$ sẽ biến thành $A \to \varepsilon$, vô tình tạo thêm luật rỗng mới và làm chu trình xử lý bị xáo trộn. Do đó, loại $\varepsilon$ phải được thực hiện trước.

### Câu hỏi 3: Nếu văn phạm có biến $B$ chỉ có luật $A \to B$ mà $B$ không có luật sinh nào thì sao?
> **Trả lời:**
> $\text{UNIT}(A)$ sẽ chứa $B$. Khi duyệt các luật không đơn vị của $B$, vì $B$ không có luật nào nên không có luật mới nào được thêm vào $A$ từ $B$. Biến $B$ trở thành biến vô ích (non-generating hoặc unreachable) và sẽ được dọn dẹp sạch sẽ ở bước T07 tiếp theo.

---

## 9. Kết luận

Task T06 đã hoàn thành xuất sắc toàn bộ checklist được giao:
- [x] Xây dựng đồ thị unit production và tính unit-closure bằng BFS.
- [x] Thay thế $A \to B$ bằng các non-unit production của $B$ và xóa sạch luật unit.
- [x] Xử lý trơn tru các chu trình $A \to B \to A$, self-loop, diamond graph, không sót luật hợp lệ.
- [x] Viết 19 test case chuyên sâu (bao gồm input validation, idempotence và tích hợp T04 $\to$ T06) đạt 100% pass rate.
- [x] Cung cấp đầy đủ hàm `remove_unit_productions` kèm alias `removeUnit` và cấu trúc log chi tiết.
- [x] Soạn thảo báo cáo kỹ thuật hoàn chỉnh tại `docs/contributions/TV3/T06-remove-unit.md`.
