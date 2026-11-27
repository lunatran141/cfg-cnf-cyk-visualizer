# T05 — Kiểm thử Parser CFG và Loại bỏ ε-production (`test_parser_epsilon.py`)

## 1. Thông tin task

| Thuộc tính | Nội dung |
|---|---|
| Mã task | T05 |
| Người thực hiện | Phạm Đăng Khôi — TV2 |
| Nhóm công việc | Kiểm thử (`Kiểm thử & đánh giá`) |
| Nhánh GitHub | `feature/T05-test-parser-epsilon` |
| Repository | `cfg-cnf-cyk-visualizer` |
| Mục báo cáo liên quan | **R19** (TV2 tổng hợp phần CFG/CNF cùng T15 của TV1) |
| Thời gian dự kiến | 27/11/2026 |
| Đầu ra | `tests/test_parser_epsilon.py`, bảng ma trận kiểm thử, báo cáo phân tích lỗi/hạn chế và file `.md` |

---

## 2. Mục tiêu và phạm vi

### 2.1. Mục tiêu

- Lập **ma trận kiểm thử đầy đủ** cho Parser CFG (T02/T03) và bước loại bỏ $\varepsilon$-production (T04) theo 3 nhóm bắt buộc của rubric: **Hợp lệ**, **Không hợp lệ** và **Biên**.
- Viết bộ unit test và integration test tự động bao phủ toàn bộ yêu cầu checklist T05:
  - $\varepsilon$ trực tiếp, $\varepsilon$ gián tiếp nhiều tầng, chuỗi biến nullable liên tiếp, chu trình biến.
  - Bảo toàn $S \to \varepsilon$ khi $\varepsilon \in L(G)$ và tạo ký hiệu bắt đầu mới `S0` (tự tăng `S1`, `S2`... khi trùng tên) khi $S \in \text{nullable}$ hoặc $S$ xuất hiện ở vế phải.
  - Terminal nhiều ký tự `id`/`num`, lỗi parser theo dòng/cột gốc, đủ 11 mã lỗi `ErrorCode`, luật trùng, dòng rỗng và ký hiệu lạ.
- Kiểm chứng luồng tích hợp đầu–cuối `parseGrammar → removeEpsilon` (tương đương định dạng nhập, round-trip serialize quay lại parser, bất biến đầu vào, tính xác định và bảo toàn ngôn ngữ $L(G') = L(G)$).
- Đảm bảo **toàn bộ bộ test dự án chạy được bằng một lệnh duy nhất** (`python -m pytest -v`).
- Ghi nhận rõ `Expected / Actual / Pass-Fail` và **phân tích sâu các lỗi tiềm ẩn, hành vi biên và hạn chế hiện tại** để phục vụ đánh giá và bảo vệ.

### 2.2. Phạm vi

- **Trong phạm vi T05:** Thiết kế ma trận kiểm thử, cài đặt file `tests/test_parser_epsilon.py`, chạy kiểm thử hồi quy toàn dự án và lập báo cáo phân tích lỗi/hạn chế.
- **Ngoài phạm vi T05:** Không chỉnh sửa mã nguồn sản phẩm trong `app/` (các module T02/T03/T04 trên `develop` giữ nguyên ổn định); các bước loại unit (T06), loại useless (T07), thay terminal/binarization (T08) và tích hợp test CNF toàn pipeline (T15) sẽ được kết hợp khi tổng hợp mục báo cáo **R19**.

---

## 3. Phương pháp kiểm thử và Cách xác định kết quả đúng (*Test Oracle*)

Để không chỉ đếm số test pass mà chứng minh được *vì sao kết quả đúng*, T05 áp dụng 4 nguyên tắc xác định kết quả mong đợi (*Test Oracle*):

1. **Đối chiếu trực tiếp đặc tả & Định lý lý thuyết:**
   - Parser: đối chiếu quy ước token trong `app/services/tokenizer.py` (`VARIABLE: [A-Z][0-9]*'*`, `TERMINAL: id|num|[a-z0-9]`, `ARROW`, `PIPE`, `EPSILON`), quy ước chuẩn hóa `normalizer.py` và 11 mã lỗi `ErrorCode` trong `diagnostics.py`.
   - `removeEpsilon`: đối chiếu Định lý 5.3 [1], [2], [3] (tập biến nullable, tổ hợp $2^k - 1$, điều kiện tạo `S0` và bảo toàn $\varepsilon$).
2. **Kiểm chứng hậu điều kiện bất biến (*Postcondition Invariants*):** Hàm `_assert_epsilon_invariants` kiểm tra tự động sau mỗi ca test `removeEpsilon`:
   - Không tồn tại luật $A \to \varepsilon$ cho bất kỳ $A \neq S_{\text{new}}$ nào.
   - Nếu tồn tại $S_{\text{new}} \to \varepsilon$ thì bắt buộc $S_{\text{old}} \in \text{nullable}$, `log.preserves_epsilon == True`, và $S_{\text{new}}$ **không xuất hiện** ở vế phải của bất kỳ luật nào.
3. **Đối chứng bảo toàn ngôn ngữ tự động bằng BFS:** Hàm `_derive_bounded_language` dùng tìm kiếm theo chiều rộng (BFS) theo dẫn xuất trái nhất để sinh tập mọi chuỗi terminal độ dài $\le 4$ (kể cả `()` cho $\varepsilon$ và các token `id`, `num`) từ cả CFG gốc $G$ lẫn CFG sau xử lý $G'$, khẳng định `orig_lang == new_lang`.
4. **Kiểm chứng khép kín (*Round-trip*), bất biến & tính xác định:**
   - Serialize `result.grammar` về lại văn bản CFG rồi gọi `parseGrammar` để chứng minh đầu ra của T04 tương thích 100% với cú pháp của T02/T03.
   - Chụp `copy.deepcopy(grammar)` trước/sau để chứng minh không có *mutation*.
   - Chạy lặp 5 lần để khẳng định đầu ra JSON hoàn toàn xác định (*deterministic*).

---

## 4. Ma trận kiểm thử chi tiết (Expected / Actual / Pass–Fail)

Toàn bộ ma trận gồm **46 hạng mục Test Case (`TC-PV01..10`, `TC-PI01..15`, `TC-RE01..13`, `TC-IN01..08`)**, khi triển khai với `@pytest.mark.parametrize` tạo thành **80 ca kiểm thử tự động** trong `tests/test_parser_epsilon.py`.

### 4.1. Nhóm A — Parser CFG: Hợp lệ & Biên hợp lệ (`TestParserValidMatrix` — 10 test)

| Mã TC | Phân loại | Kịch bản & Input tóm tắt | Kết quả mong đợi (Expected) | Kết quả thực tế (Actual) | Trạng thái |
|---|---|---|---|---|---|
| `TC-PV01` | Hợp lệ / Biên | Nhiều dòng cùng biến + luật trùng: `S -> id \| id`, `S -> num \| ε`, `S -> id \| ε` | `success=True`, gộp còn 3 luật duy nhất `{("id",), ("num",), ()}` | Đúng 3 luật, không trùng lặp | **PASS** |
| `TC-PV02` | Hợp lệ | Terminal `id`/`num` xen biến: `S -> A id B num`, `A -> id`, `B -> num` | `terminals={"id", "num"}`, RHS `("A", "id", "B", "num")` | Khớp hoàn toàn | **PASS** |
| `TC-PV03` | Biên | Tách tham lam `S -> idnum \| mid \| AidB` vs cách `S -> i d \| n u m` | Tham lam tách `("id","num")`, `("m","id")`, `("A","id","B")`; có cách tách từng ký tự đơn | Khớp hoàn toàn (ghi nhận hạn chế ở Mục 6) | **PASS** |
| `TC-PV04` | Hợp lệ | Terminal chữ số `0`, `1` và biến phức hợp `S0`, `A1'`, `B2''` | `variables={"S0","A1'","B2''"}`, `terminals={"0","1"}`, `start="S0"` | Khớp hoàn toàn | **PASS** |
| `TC-PV05` | Biên | Dòng rỗng xen kẽ và xuống dòng LF (`\n`), CRLF (`\r\n`), CR (`\r`) | Cả 3 kiểu cho `Grammar.to_dict()` y hệt nhau | Trùng khớp 100% | **PASS** |
| `TC-PV06` | Hợp lệ | Chuẩn hóa `→`, `｜`, `\t`, NBSP (`\u00a0`) so với ASCII chuẩn | `to_dict()` bằng nhau giữa bản Unicode và bản ASCII | Trùng khớp 100% | **PASS** |
| `TC-PV07` | Biên | Có dòng rỗng đầu file: `\n   \nE -> id\nS -> num` | `start_symbol` mặc định là biến vế trái hợp lệ đầu tiên `"E"` | `start_symbol == "E"` | **PASS** |
| `TC-PV08` | Biên | Truyền `start_symbol="  A  "` có khoảng trắng bao quanh | Tự `.strip()`, `success=True`, `start_symbol == "A"` | `start_symbol == "A"` | **PASS** |
| `TC-PV09` | Hợp lệ | Tham chiếu tiến & đệ quy tương hỗ `S -> B`, `B -> A`, `A -> S \| id` | Không báo lỗi biến chưa khai báo, `production_count() == 4` | `success=True`, 4 luật | **PASS** |
| `TC-PV10` | Biên | Biên quy ước regex biến: `S -> A'1`, `A' -> id` | Tách thành biến `A'` + terminal `1` (`("A'", "1")`) | Khớp hoàn toàn (ghi nhận ở Mục 6) | **PASS** |

### 4.2. Nhóm B — Parser CFG: Không hợp lệ & Lỗi theo dòng (`TestParserInvalidMatrix` — 42 test)

| Mã TC | Phân loại | Kịch bản & Input tóm tắt | Kết quả mong đợi (Expected) | Kết quả thực tế (Actual) | Trạng thái |
|---|---|---|---|---|---|
| `TC-PI01` | Không hợp lệ / Biên | Input rỗng / chỉ khoảng trắng (`""`, `"   "`, `"\t\r\n"`, `"\n\n"`) | `success=False`, `grammar=None`, `EMPTY_INPUT` ở dòng 1 | 4/4 biến thể đúng | **PASS** |
| `TC-PI02` | Không hợp lệ / Biên | Input sai kiểu (`None`, `123`, `["S -> a"]`, `{"S": "a"}`) | `INVALID_INPUT_TYPE`, không crash | 4/4 biến thể đúng | **PASS** |
| `TC-PI03` | Không hợp lệ | Thiếu mũi tên dòng 2: `S -> a\nA b` | `MISSING_ARROW`, `line=2`, `content="A b"` | Đúng dòng 2 và mã lỗi | **PASS** |
| `TC-PI04` | Không hợp lệ / Biên | Thừa mũi tên có Unicode & space: `"  S  →  A  →  a"` | `MULTIPLE_ARROWS`, `line=1`, `column=12` (cột gốc) | Đúng cột gốc `12` | **PASS** |
| `TC-PI05` | Không hợp lệ | 5 dạng vế trái sai (`a -> b`, `id -> a`, `AB -> a`, `-> a`, `ε -> a`) | `INVALID_LHS` cho cả 5 trường hợp | 5/5 biến thể đúng | **PASS** |
| `TC-PI06` | Không hợp lệ | Vế phải rỗng (`S ->`, `S →   `) | `EMPTY_RHS` | 2/2 biến thể đúng | **PASS** |
| `TC-PI07` | Không hợp lệ / Biên | Production rỗng (`\| a`, `a \|`, `a \|\| b`, `a ｜ ｜ b`, `\| a \|`) | `EMPTY_PRODUCTION` (riêng `\| a \|` trả đủ 2 lỗi) | 5/5 biến thể đúng | **PASS** |
| `TC-PI08` | Không hợp lệ | `ε` không đứng riêng (`aε`, `εa`, `A ε B`, `ε ε`) | `INVALID_EPSILON` cho cả 4 trường hợp | 4/4 biến thể đúng | **PASS** |
| `TC-PI09` | Không hợp lệ / Biên | Ký hiệu lạ & toán tử chưa hỗ trợ (`@`, `#`, `$`, `+`, `*`, `(`, `λ`) | `INVALID_SYMBOL`, kèm thông điệp chứa ký hiệu và gợi ý sửa | 7/7 biến thể đúng | **PASS** |
| `TC-PI10` | Không hợp lệ | Biến chưa khai báo lặp nhiều chỗ (`S -> B B\nA -> B`) | 3 lỗi `UNDEFINED_VARIABLE` tại `(1,6)`, `(1,8)`, `(2,6)` | Khớp chính xác 3 tọa độ | **PASS** |
| `TC-PI11` | Biên (lỗi dây chuyền) | Dòng khai báo hỏng cú pháp: `S -> A\nA -> @` | Ghi nhận 2 lỗi: `(1, UNDEFINED_VARIABLE)` và `(2, INVALID_SYMBOL)` | Khớp thực tế (phân tích ở Mục 6) | **PASS** |
| `TC-PI12` | Không hợp lệ / Biên | `start_symbol` sai (`"X"`, `""`, `"   "`, `123`) | `INVALID_START_SYMBOL`, không crash | 4/4 biến thể đúng | **PASS** |
| `TC-PI13` | Không hợp lệ | 5 lỗi khác loại trên nhiều dòng xen dòng rỗng | Giữ đúng số dòng gốc `1, 3, 5, 6, 8` và sắp tăng dần | Khớp hoàn toàn | **PASS** |
| `TC-PI14` | Biên | Ánh xạ cột gốc sau chuẩn hóa `"   S   →  id  ｜  @"` | `INVALID_SYMBOL` tại cột `19` (vị trí `@` trên chuỗi gốc) | `column == 19` | **PASS** |
| `TC-PI15` | Không hợp lệ | Phủ đủ cả 11 giá trị `ErrorCode` & kiểm tra JSON serialization | Kích hoạt đủ `11/11` `ErrorCode`, `json.dumps` hợp lệ | 11/11 mã lỗi PASS | **PASS** |

### 4.3. Nhóm C — `removeEpsilon`: Ma trận trực tiếp / gián tiếp / biên (`TestRemoveEpsilonMatrix` — 13 test)

| Mã TC | Phân loại | Kịch bản & Input tóm tắt | Kết quả mong đợi (Expected) | Kết quả thực tế (Actual) | Trạng thái |
|---|---|---|---|---|---|
| `TC-RE01` | Hợp lệ | `ε` trực tiếp ở biến thường: `S -> id A`, `A -> num \| ε` | `nullable={A}`, không tạo `S0`, `S -> id A \| id`, `A -> num` | Khớp hoàn toàn | **PASS** |
| `TC-RE02` | Hợp lệ | `ε` gián tiếp 4 tầng: `S->A->B->C->D->a\|ε` | `iterations=[["D"],["C"],["B"],["A"],["S"]]`, tạo `S0 -> S \| ε` | Hội tụ đúng 5 lượt | **PASS** |
| `TC-RE03` | Biên (mũ $2^k$) | 4 biến nullable liên tiếp `S -> A B C D` | `S` có đúng $2^4 - 1 = 15$ luật không trùng, `S0 -> S \| ε`, log không trùng | Đúng 15 luật, 0 trùng | **PASS** |
| `TC-RE04` | Biên (lọc trùng) | Cùng biến nullable lặp `S -> A A A A`, `A -> id \| ε` | `S` gộp còn đúng 4 luật (`AAAA`, `AAA`, `AA`, `A`) | Đúng 4 luật | **PASS** |
| `TC-RE05` | Biên (chu trình) | Chu trình 3 biến có `ε`: `A->B->C->A\|ε`, `S->A id` | Dừng sau 3 lượt `[["C"],["B"],["A"]]`, `S -> A id \| id` | Dừng đúng, khớp kết quả | **PASS** |
| `TC-RE06` | Biên (chu trình) | Chu trình 3 biến không có `ε`: `A->B->C->A`, `S->A\|id` | Dừng ngay lượt 1, `nullable=∅`, văn phạm giữ nguyên | Không lặp vô hạn | **PASS** |
| `TC-RE07` | Hợp lệ | Bảo toàn `S -> ε` khi `S` không ở RHS (`S -> AB`, `A->id\|ε`, `B->num\|ε`) | Tạo `S0 -> S \| ε`, `preserves_epsilon=True` | Khớp hoàn toàn | **PASS** |
| `TC-RE08` | Hợp lệ / Biên | Bảo toàn `S -> ε` khi `S` có ở RHS (`S -> a S b \| ε`) | Tạo `S0 -> S \| ε`, `S -> aSb \| ab`, `S0` không ở RHS | Khớp hoàn toàn | **PASS** |
| `TC-RE09` | Biên | `S` ở RHS nhưng `S ∉ nullable` (`S -> id S \| num`) | Tạo `S0 -> S`, **không** giữ `S0 -> ε`, `preserves_epsilon=False` | Khớp hoàn toàn | **PASS** |
| `TC-RE10` | Biên (trùng tên) | Grammar đã có sẵn cả `S0` và `S1`: `S -> S0 S1 \| ε` | Sinh tên mới `S2`, không ghi đè `S0`, `S1` | `start_symbol == "S2"` | **PASS** |
| `TC-RE11` | Biên | Văn phạm chỉ sinh chuỗi rỗng `S -> ε` | Tạo `S0 -> S \| ε`, ghi cảnh báo biến `S` hết luật sinh | Có warning cho `S` | **PASS** |
| `TC-RE12` | Biên | Văn phạm rỗng `Grammar()` | Không crash, trả bản sao mới, có warning, `0 → 0` luật | Khớp hoàn toàn | **PASS** |
| `TC-RE13` | Hợp lệ | Văn phạm sạch không `ε`, `S` không ở RHS (`S->AB`, `A->id`, `B->num`) | Không tạo `S0`, `added_rules=[]`, `removed_rules=[]` | Không thay đổi thừa | **PASS** |

### 4.4. Nhóm D — Tích hợp đầu–cuối `parseGrammar → removeEpsilon` (`TestParserEpsilonIntegrationMatrix` — 15 test)

| Mã TC | Phân loại | Kịch bản & Input tóm tắt | Kết quả mong đợi (Expected) | Kết quả thực tế (Actual) | Trạng thái |
|---|---|---|---|---|---|
| `TC-IN01` | Tích hợp | ASCII chuẩn vs Unicode (`→`, `｜`, `\u00a0`, CRLF, dòng rỗng, luật trùng) qua toàn luồng | Output JSON `removeEpsilon(...).to_dict()` trùng khớp 100% | Khớp tuyệt đối | **PASS** |
| `TC-IN02` | Tích hợp | Terminal `id`/`num` đi qua `parseGrammar → removeEpsilon` (`E -> T A`, `T -> id\|num`, `A -> id T A\|ε`) | Token `id`/`num` giữ nguyên nguyên khối trong mọi biến thể | Khớp hoàn toàn | **PASS** |
| `TC-IN03` | Tích hợp / Biên | **Round-trip:** serialize output `removeEpsilon` (4 grammar gồm `S0`, `S2`, `id`, `num`, `ε`) rồi gọi lại `parseGrammar` | Parse thành công cả 4/4 và `to_dict()` giống hệt bản gốc | 4/4 ca PASS | **PASS** |
| `TC-IN04` | Tích hợp | **Bảo toàn ngôn ngữ:** BFS sinh chuỗi độ dài $\le 4$ trước & sau `removeEpsilon` trên 5 grammar (có `id`/`num`/`ε`) | `orig_lang == new_lang` trên cả 5/5 văn phạm | 5/5 ca PASS | **PASS** |
| `TC-IN05` | Tích hợp / Biên | **Bất biến đầu vào:** snapshot `deepcopy` trước/sau khi gọi `addFreshStart` và `removeEpsilon` | `Grammar` sau `parseGrammar` không bị mutate bất kỳ thuộc tính nào | Không mutation | **PASS** |
| `TC-IN06` | Tích hợp / Biên | **Determinism:** chạy lặp 5 lần `parseGrammar → removeEpsilon` | Cả 5 kết quả `to_dict()` bằng nhau tuyệt đối | 5/5 giống hệt | **PASS** |
| `TC-IN07` | Không hợp lệ | Truyền `parse_result.grammar` (`None`) từ input lỗi vào `removeEpsilon` | Ném `TypeError` rõ ràng, không xử lý dữ liệu lỗi | Raise `TypeError` | **PASS** |
| `TC-IN08` | Biên (hợp đồng T06) | Grammar có sẵn `S -> A` và sinh thêm self-loop `A -> A` | Không log thừa `S -> A` trong `added_rules`; giữ `A -> A` cho T06 | Khớp hợp đồng T06 | **PASS** |

---

## 5. Cách chạy kiểm thử bằng một lệnh & Kết quả thực tế

### 5.1. Môi trường thực thi

- Hệ điều hành: Windows
- Python local: `3.13.7` (trong môi trường ảo `.venv`, cú pháp tương thích hoàn toàn Python `3.11` trên GitHub Actions CI)
- Pytest: `9.2.0`

### 5.2. Lệnh chạy kiểm thử

Chạy toàn bộ bộ test dự án bằng **một lệnh duy nhất**:

```powershell
python -m pytest -v
```

*(Hoặc khi dùng môi trường ảo `.venv` trên Windows: `.venv\Scripts\python.exe -m pytest -v`; chạy riêng T05: `.venv\Scripts\python.exe -m pytest tests/test_parser_epsilon.py -v`.)*

### 5.3. Bảng tổng hợp kết quả thực tế

| File kiểm thử | Task | Số test | PASS | FAIL | Thời gian |
|---|---|---:|---:|---:|---:|
| `tests/test_app.py` | T01 (TV1) | 4 | 4 | 0 | — |
| `tests/test_parser.py` | T02 (TV5) | 46 | 46 | 0 | — |
| `tests/test_parser_errors.py` | T03 (TV5) | 60 | 60 | 0 | — |
| `tests/test_remove_epsilon.py` | T04 (TV2) | 52 | 52 | 0 | — |
| **`tests/test_parser_epsilon.py`** | **T05 (TV2)** | **80** | **80** | **0** | **0.35s** |
| **Tổng toàn dự án (`python -m pytest -v`)** | **T01–T05** | **242** | **242** | **0** | **0.40s** |

Chi tiết phân bổ trong riêng `tests/test_parser_epsilon.py` (**80/80 PASS**):
- `TestParserValidMatrix`: **10 passed**
- `TestParserInvalidMatrix`: **42 passed**
- `TestRemoveEpsilonMatrix`: **13 passed**
- `TestParserEpsilonIntegrationMatrix`: **15 passed**

---

## 6. Phân tích lỗi phát hiện, hành vi biên và hạn chế hiện tại

Quá trình kiểm thử chéo Parser (T02/T03) và `removeEpsilon` (T04) ghi nhận **1 lỗi tự viết test đã sửa ngay** và **6 hạn chế/hành vi biên quan trọng** của hệ thống hiện tại:

### 6.1. Lỗi phát hiện và xử lý trong quá trình viết test T05
- Ở lần chạy đầu tiên, `test_pv03_multichar_terminals_adjacent_greedy_and_spaced` thất bại (`1 failed, 79 passed`) do chuỗi mẫu `"S -> idnum | mid | AidB"` dùng hai biến `A`, `B` nhưng chưa khai báo luật sinh cho `A`, `B`, khiến `parseGrammar` báo chính xác `UNDEFINED_VARIABLE`. Sau khi bổ sung `A -> a` và `B -> b`, cả **80/80 test T05** và **242/242 test toàn dự án** đều PASS.

### 6.2. Phân tích 6 hạn chế & hành vi biên của hệ thống hiện tại

| STT | Module | Hạn chế / Hành vi phát hiện | Minh chứng TC | Tác động & hướng xử lý |
|---|---|---|---|---|
| 1 | `tokenizer.py` | **Tách tham lam `id`/`num` không theo ranh giới từ:** regex `id\|num\|[a-z0-9]` tách `mid` thành `("m", "id")` thay vì `("m", "i", "d")`. | `TC-PV03` | Người dùng muốn nhập hai terminal đơn `i`, `d` kề nhau bắt buộc phải cách bằng khoảng trắng (`i d`). Cần ghi rõ trong hướng dẫn cú pháp ở UI (T10). |
| 2 | `tokenizer.py` | **Chưa hỗ trợ ký hiệu toán tử (`+`, `*`, `(`, `)`) và ký hiệu `λ`:** Các ký hiệu thường gặp trong giáo trình bị báo `INVALID_SYMBOL`, còn chữ `"epsilon"` bị tách thành 7 ký tự thường. | `TC-PI09` | Chưa nhập trực tiếp được văn phạm biểu thức số học kinh điển `E -> E + T \| T`, `F -> (E) \| id`. Hướng cải tiến: mở rộng tập terminal hoặc hỗ trợ chuẩn hóa `λ → ε` khi nhóm thống nhất. |
| 3 | `tokenizer.py` | **Thứ tự số và dấu nháy trong tên biến:** Regex `[A-Z][0-9]*'*` nhận `A1'` là 1 biến nhưng tách `A'1` thành biến `A'` + terminal `1`. | `TC-PV10` | Cần quy ước thống nhất trong tài liệu và form nhập (chỉ số số đặt trước dấu nháy, vd `S0`, `A1'`). |
| 4 | `parser.py` | **Lỗi thứ cấp `UNDEFINED_VARIABLE` khi dòng khai báo hỏng cú pháp:** Với `S -> A\nA -> @`, vì dòng 2 lỗi nên `A` không được đăng ký vào `declared_variables`, kéo theo báo thêm `UNDEFINED_VARIABLE` cho `A` ở dòng 1. | `TC-PI11` | Không làm crash chương trình và có gợi ý sửa, nhưng người dùng có thể thấy 2 lỗi cho 1 nguyên nhân gốc. Có thể cải thiện sau bằng cách đăng ký trước LHS hợp lệ của các dòng lỗi vế phải. |
| 5 | `remove_epsilon.py` | **Tăng trưởng mũ $O(2^k)$ số luật sinh:** Với 4 biến nullable liên tiếp (`S -> A B C D`), số luật tăng từ 1 lên 15 ($2^4 - 1$). | `TC-RE03` | Bản chất lý thuyết của loại $\varepsilon$-production; với grammar lớn nhiều biến nullable có thể gây chậm ở thực nghiệm (T23). |
| 6 | `remove_epsilon.py` | **Chưa dọn biến hết luật sinh và unit self-loop trong cùng bước:** `S -> ε` để lại `S` rỗng luật sinh (có warning); `A -> SA` tạo self-loop `A -> A`. | `TC-RE11`, `TC-IN08` | Đúng theo ranh giới thiết kế pipeline; bắt buộc phải chạy nối tiếp `removeUnit` (T06) và `removeUseless` (T07) trước khi đưa vào `validateCNF` (T09) và CYK. |

---

## 7. Liên kết chuẩn bị cho mục báo cáo R19 và Test Runner tổng (T22)

- **Với mục báo cáo R19 (*Thiết kế bộ test CFG/CNF*, TV2 tổng hợp từ T05 + T15):**
  - T05 đã chốt xong nửa đầu của R19 gồm: ma trận test hợp lệ/sai cú pháp cho Parser, terminal nhiều ký tự `id`/`num`, `ε` trực tiếp/gián tiếp, bảo toàn `S → ε`, tạo `S0` khi `S` sinh `ε` hoặc ở vế phải, round-trip và bảo toàn ngôn ngữ.
  - Khi TV1 hoàn thành **T15** (`test_cnf` bao phủ `removeUnit`, `removeUseless`, thay terminal, binarization, `validateCNF` và *idempotence* toàn pipeline), TV2 sẽ ghép trực tiếp vào bảng tổng hợp của R19.
- **Với T22 (*Test runner tổng* của TV5):** File `tests/test_parser_epsilon.py` hoàn toàn độc lập, không phụ thuộc trạng thái ngoài, đặt theo chuẩn `test_*.py` của Pytest nên tự động được gom khi chạy `python -m pytest -v`.

---

## 8. Nội dung chuẩn bị bảo vệ cá nhân (TV2)

1. Cách phân nhóm ma trận kiểm thử **Hợp lệ / Không hợp lệ / Biên** và lý do mỗi nhóm đều cần thiết (đáp ứng tiêu chí Kiểm thử & đánh giá 10%).
2. Cách xác định kết quả đúng (*Test Oracle*) mà không phụ thuộc cảm tính: đối chiếu Định lý 5.3, kiểm tra 2 hậu điều kiện bất biến (`_assert_epsilon_invariants`), kiểm chứng bảo toàn ngôn ngữ bằng BFS (`_derive_bounded_language`) và kiểm chứng *round-trip* qua `parseGrammar`.
3. Giải thích cụ thể các edge case tiêu biểu đã test: tách tham lam `id`/`num` vs `i d`, lỗi thứ cấp `UNDEFINED_VARIABLE` khi dòng khai báo hỏng, tránh trùng tên `S0`/`S1` thành `S2`, tạo `S0 -> S` không giữ `ε` khi `S` ở RHS nhưng không nullable, và chuỗi 4 biến nullable sinh $2^4 - 1 = 15$ luật.
4. Giải thích cách chạy toàn bộ 242 test dự án bằng một lệnh `python -m pytest -v` và cách chứng minh không gây regression cho T01–T04.

---

## 9. Minh chứng cần bổ sung

- [ ] Ảnh chụp terminal chạy `.venv\Scripts\python.exe -m pytest tests/test_parser_epsilon.py -v` (**80 passed**).
- [ ] Ảnh chụp terminal chạy `.venv\Scripts\python.exe -m pytest -v` toàn dự án (**242 passed**).
- [ ] Link Pull Request nhánh `feature/T05-test-parser-epsilon` vào `develop`.
- [ ] Ảnh xác nhận 2 job GitHub Actions (`CI / test` và `CI / docker-build`) xanh sau khi đẩy PR.

---

## 10. Tài liệu tham khảo

1. Sipser, M. (2012). *Introduction to the Theory of Computation* (3rd ed.). Cengage Learning. (Chương 2: Context-Free Languages — Chomsky Normal Form).
2. Hopcroft, J. E., Motwani, R., & Ullman, J. D. (2006). *Introduction to Automata Theory, Languages, and Computation* (3rd ed.). Pearson Education. (Chương 7: Properties of Context-Free Languages).
3. Giáo trình & Slide học phần *Ngôn ngữ hình thức* — Chương *Văn phạm phi ngữ cảnh* (`Chuong4_FCG.pdf`, `van-pham-phi-ngu-canh.pdf`, tài liệu lưu hành nội bộ môn học).
4. Pytest Development Team (2025). *Pytest Documentation (v9.2)*. Truy cập tại https://docs.pytest.org/ (ngày truy cập: 26/11/2026).
5. Tài liệu đóng góp nội bộ của nhóm: `docs/contributions/TV5/T02-cfg-parser.md`, `docs/contributions/TV5/T03-parser-errors.md`, `docs/contributions/TV2/T04-remove-epsilon.md`.

---

## 11. Khai báo sử dụng AI

- **Công cụ sử dụng:** Trợ lý AI hỗ trợ rà soát biên mã nguồn `tokenizer.py`, `normalizer.py`, `parser.py`, `remove_epsilon.py`, đề xuất ma trận kiểm thử, viết các ca test tham số hóa (`@pytest.mark.parametrize`) và biên tập tài liệu Markdown.
- **Phần tự kiểm chứng:** Toàn bộ 80 test T05 và 242 test toàn dự án đã được chạy thực tế bằng Pytest trên máy cục bộ (0 failed), đối chiếu từng kết quả `Expected / Actual` với mã nguồn và lý thuyết môn học; thành viên TV2 nắm vững logic từng ca test và chịu trách nhiệm giải thích khi bảo vệ.
