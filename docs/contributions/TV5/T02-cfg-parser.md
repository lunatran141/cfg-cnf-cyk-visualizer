# T02 - Parser CFG và Tokenizer

## 1. Thông tin task

| Thuộc tính | Nội dung |
|---|---|
| Mã task | T02 |
| Người thực hiện | Tuấn - TV5 |
| Nhóm công việc | Thuật toán cốt lõi |
| Hàm chính | parseGrammar |
| Nhánh GitHub | feature/T02-cfg-parser |
| Repository | cfg-cnf-cyk-visualizer |
| Nội dung báo cáo | R02, R04 |

## 2. Mục tiêu

- Xây dựng mô hình dữ liệu văn phạm phi ngữ cảnh.
- Phân tách văn bản CFG thành các token.
- Nhận diện biến, terminal, epsilon, mũi tên và dấu phân cách.
- Hỗ trợ terminal nhiều ký tự như id và num.
- Phân tích văn bản thành đối tượng Grammar.
- Kiểm tra tính hợp lệ của cú pháp và ký hiệu bắt đầu.
- Trả về thông tin lỗi có vị trí và gợi ý sửa.
- Cung cấp dữ liệu đầu vào cho các module CNF và CYK.
- Kiểm thử tự động bằng Pytest.

## 3. Cơ sở lý thuyết - R02

### 3.1. Định nghĩa CFG

Văn phạm phi ngữ cảnh (Context-Free Grammar) được định nghĩa:

G = (V, Σ, P, S)

Trong đó:

- V: tập hữu hạn các biến (non-terminal).
- Σ: tập hữu hạn các ký hiệu kết thúc (terminal).
- P: tập các luật sinh (production).
- S: ký hiệu bắt đầu, thuộc V.
- V và Σ không giao nhau.

Mỗi luật sinh có dạng:

A → α

Trong đó A thuộc V và α là một chuỗi hữu hạn các ký hiệu thuộc V hoặc Σ, có thể là chuỗi rỗng ε.

### 3.2. Ví dụ văn phạm

```text
S -> AB | id
A -> a
B -> num | ε
```

Các thành phần:

- V = {S, A, B}
- Σ = {a, id, num}
- S = S
- P gồm 5 luật sinh:

```text
S → AB
S → id
A → a
B → num
B → ε
```

### 3.3. Quy ước nhập văn phạm

| Thành phần | Quy ước | Ví dụ |
|---|---|---|
| Biến | Chữ cái in hoa, có thể kèm số và dấu nháy | S, A1, B' |
| Terminal | Chữ thường hoặc chữ số | a, b, 0, 1 |
| Terminal nhiều ký tự | Ưu tiên nhận diện id và num | id, num |
| Mũi tên | ASCII hoặc Unicode | ->, → |
| Phân cách | Dấu gạch đứng | \| |
| Epsilon | Ký hiệu chuỗi rỗng | ε |
| Khoảng trắng | Bỏ qua khoảng trắng và tab giữa token | A B |

Mỗi dòng chứa một biến vế trái và một hoặc nhiều lựa chọn ở vế phải.

Epsilon phải đứng riêng trong một lựa chọn luật sinh.

## 4. Mô hình dữ liệu Grammar

Mô hình Grammar được cài đặt bằng dataclass trong Python.

| Thuộc tính | Kiểu dữ liệu | Ý nghĩa |
|---|---|---|
| variables | set[str] | Tập biến |
| terminals | set[str] | Tập terminal |
| productions | dict[str, set[tuple[str, ...]]] | Tập luật sinh |
| start_symbol | str | Ký hiệu bắt đầu |

Production được lưu bằng tuple để giữ đúng thứ tự ký hiệu.

Các luật sinh được lưu trong set để tránh trùng lặp.

Epsilon được biểu diễn bằng tuple rỗng:

```python
EPSILON = ()
```

Ví dụ:

```python
productions = {
    "S": {("A", "B"), ("id",)},
    "A": {("a",)},
    "B": {("num",), ()}
}
```

### 4.1. Các phương thức

| Phương thức | Chức năng |
|---|---|
| add_production | Thêm luật sinh |
| get_productions | Lấy các luật sinh của một biến |
| production_count | Đếm tổng số luật sinh |
| copy | Tạo bản sao độc lập |
| to_dict | Chuyển Grammar thành dữ liệu tương thích JSON |

Phương thức copy hỗ trợ các thuật toán chuyển đổi CFG sang CNF mà không làm thay đổi văn phạm ban đầu.

Phương thức to_dict sắp xếp các thành phần trước khi trả về, giúp kết quả biểu diễn nhất quán.

## 5. Thiết kế Tokenizer - R04

### 5.1. Đầu vào

Văn bản CFG do người dùng nhập.

### 5.2. Đầu ra

Danh sách Token.

Mỗi Token gồm:

- type: loại token.
- value: giá trị token.
- line: số dòng.
- column: vị trí cột.

Số dòng và số cột bắt đầu từ 1.

### 5.3. Các loại token

- VARIABLE: biến.
- TERMINAL: ký hiệu kết thúc.
- ARROW: mũi tên.
- PIPE: dấu phân cách.
- EPSILON: chuỗi rỗng.
- INVALID: ký hiệu không hợp lệ.

Khoảng trắng và tab được bỏ qua.

### 5.4. Thuật toán

1. Tách văn bản thành từng dòng.
2. Sử dụng biểu thức chính quy để nhận diện ký hiệu.
3. Ưu tiên nhận diện id và num trước terminal đơn.
4. Bỏ qua khoảng trắng.
5. Tạo Token kèm số dòng và cột.
6. Ghi nhận ký hiệu không hợp lệ bằng token INVALID.
7. Trả về danh sách token.

### 5.5. Ví dụ

Đầu vào:

```text
S -> AB | id | num | ε
```

Kết quả:

| Loại | Giá trị |
|---|---|
| VARIABLE | S |
| ARROW | -> |
| VARIABLE | A |
| VARIABLE | B |
| PIPE | \| |
| TERMINAL | id |
| PIPE | \| |
| TERMINAL | num |
| PIPE | \| |
| EPSILON | ε |

## 6. Thiết kế Parser CFG - R04

### 6.1. Hàm chính

```python
parseGrammar(text, start_symbol=None)
```

Tham số:

- text: văn bản CFG.
- start_symbol: ký hiệu bắt đầu tùy chọn.

Nếu không chỉ định start_symbol, parser chọn biến vế trái đầu tiên của văn phạm hợp lệ.

### 6.2. Kết quả trả về

ParseResult gồm:

- grammar: Grammar hợp lệ hoặc None.
- errors: danh sách lỗi.
- success: trạng thái phân tích.

### 6.3. Luồng xử lý

```text
Văn bản CFG
    |
    v
Tokenizer
    |
    v
Kiểm tra ký hiệu và cú pháp
    |
    v
Phân tích các production
    |
    v
Kiểm tra biến chưa khai báo
    |
    v
Kiểm tra ký hiệu bắt đầu
    |
    v
Grammar hoặc danh sách lỗi
```

### 6.4. Các bước thuật toán

1. Kiểm tra dữ liệu đầu vào rỗng hoặc sai kiểu.
2. Duyệt từng dòng văn phạm.
3. Bỏ qua dòng rỗng.
4. Phân tách token.
5. Kiểm tra ký hiệu không hợp lệ.
6. Kiểm tra số lượng mũi tên.
7. Kiểm tra vế trái là một biến hợp lệ.
8. Kiểm tra vế phải không rỗng.
9. Tách các production theo dấu phân cách.
10. Kiểm tra epsilon đứng riêng.
11. Xây dựng tập biến, terminal và production.
12. Kiểm tra biến chưa khai báo sau khi đọc toàn bộ văn phạm.
13. Kiểm tra ký hiệu bắt đầu nếu chưa có lỗi trước đó.
14. Trả về Grammar hoặc danh sách lỗi.

Việc kiểm tra biến sau khi đọc toàn bộ văn phạm cho phép xử lý các biến được tham chiếu trước khi khai báo.

## 7. Xử lý lỗi

Mỗi ParseError gồm:

| Thuộc tính | Ý nghĩa |
|---|---|
| line | Số dòng |
| column | Vị trí cột |
| content | Nội dung gây lỗi |
| message | Thông báo lỗi |
| suggestion | Gợi ý sửa |

Các trường hợp lỗi được xử lý:

- Văn phạm rỗng hoặc sai kiểu dữ liệu.
- Thiếu hoặc thừa mũi tên.
- Vế trái không hợp lệ.
- Vế phải rỗng.
- Production rỗng giữa các dấu phân cách.
- Ký hiệu không hợp lệ.
- Epsilon không đứng riêng.
- Biến chưa được khai báo.
- Ký hiệu bắt đầu không hợp lệ.

Parser trả về danh sách lỗi thay vì trả về Grammar chưa hợp lệ.

## 8. Ví dụ Input và Output

### 8.1. Văn phạm hợp lệ

Input:

```text
S -> AB | id
A -> a
B -> num | ε
```

Output khi gọi Grammar.to_dict():

```json
{
  "variables": ["A", "B", "S"],
  "terminals": ["a", "id", "num"],
  "productions": {
    "A": [["a"]],
    "B": [[], ["num"]],
    "S": [["A", "B"], ["id"]]
  },
  "start_symbol": "S"
}
```

Kết quả:

- success: True.
- errors: [].
- Tổng production: 5.

### 8.2. Văn phạm không hợp lệ

Input:

```text
S -> a@b
```

Output:

```text
success: False
grammar: None
line: 1
column: 7
content: S -> a@b
message: Ký hiệu không hợp lệ: @
suggestion: Xóa hoặc thay thế ký hiệu không hợp lệ.
```

## 9. Phân tích độ phức tạp

Gọi:

- n là tổng số ký tự đầu vào.
- t là tổng số token.
- e là số lỗi phát hiện.

Tokenizer có độ phức tạp thời gian O(n).

Parser duyệt các token để kiểm tra cú pháp và xây dựng Grammar.

Các thao tác tra cứu và thêm phần tử vào set hoặc dict có chi phí trung bình O(1), nếu coi chi phí xử lý mỗi ký hiệu là hằng số.

Chi phí sắp xếp danh sách lỗi là O(e log e).

Do đó:

- Thời gian phân tích: O(n + t + e log e).
- Bộ nhớ: O(n + t + e).

Phương thức to_dict có thêm chi phí sắp xếp biến, terminal và production. Chi phí này không thuộc quá trình parseGrammar chính.

## 10. Cấu trúc mã nguồn

| File | Chức năng |
|---|---|
| app/models/grammar.py | Mô hình dữ liệu Grammar |
| app/services/tokenizer.py | Phân tách token |
| app/services/parser.py | Phân tích cú pháp CFG |
| tests/test_parser.py | Unit test T02 |
| docs/contributions/TV5/T02-cfg-parser.md | Tài liệu đóng góp |

T02 không thay đổi Flask skeleton hoặc các module thuật toán khác.

## 11. Kiểm thử

### 11.1. Môi trường

- Hệ điều hành: Windows.
- Python: 3.11.9.
- Pytest: 9.2.0.
- IDE: Visual Studio Code.
- Môi trường ảo: .venv.

### 11.2. Chạy riêng test T02

```powershell
python -m pytest tests/test_parser.py -v
```

Kết quả thực tế:

```text
46 passed in 0.21s
```

### 11.3. Chạy toàn bộ test dự án

```powershell
python -m pytest -v
```

Kết quả thực tế:

```text
50 passed in 0.25s
```

### 11.4. Tổng hợp kết quả

| Nhóm kiểm thử | Tổng | PASS | FAIL |
|---|---:|---:|---:|
| Grammar Model | 8 | 8 | 0 |
| Tokenizer | 12 | 12 | 0 |
| Parser CFG | 26 | 26 | 0 |
| Tổng T02 | 46 | 46 | 0 |
| Flask skeleton T01 | 4 | 4 | 0 |
| Tổng toàn dự án | 50 | 50 | 0 |

### 11.5. Các trường hợp kiểm thử chính

| Trường hợp | Kết quả |
|---|---|
| Grammar hợp lệ | PASS |
| Thiếu mũi tên | PASS |
| Thừa mũi tên | PASS |
| Vế trái không hợp lệ | PASS |
| Dòng rỗng | PASS |
| Epsilon | PASS |
| Epsilon sử dụng sai | PASS |
| Ký hiệu không hợp lệ | PASS |
| Terminal id và num | PASS |
| Ký hiệu bắt đầu không hợp lệ | PASS |
| Biến chưa khai báo | PASS |
| Production trùng lặp | PASS |
| Production rỗng | PASS |
| Mũi tên Unicode | PASS |
| Nhiều lỗi trên nhiều dòng | PASS |
| Grammar copy không mutation | PASS |
| Kết quả biểu diễn nhất quán | PASS |
| Đầu vào sai kiểu | PASS |

### 11.6. Docker và CI

- Docker local: chưa kiểm thử.
- GitHub Actions CI: chưa xác nhận.
- Pull Request: chưa tạo.

Các trạng thái sẽ được cập nhật sau khi có kết quả thực tế.

## 12. Lỗi gặp phải và cách xử lý

### 12.1. Lỗi dây chuyền khi kiểm tra start symbol

Trong quá trình kiểm thử ban đầu, hai trường hợp:

```text
S -> a@b
S -> a |
```

trả về lỗi ký hiệu bắt đầu trước lỗi cú pháp chính.

Nguyên nhân:

Parser bỏ qua dòng lỗi trước khi đăng ký biến vế trái. Sau đó, bước kiểm tra start symbol tạo thêm lỗi phụ.

Cách xử lý:

```python
if not errors and grammar.start_symbol not in declared_variables:
```

Parser chỉ kiểm tra start symbol khi chưa có lỗi trước đó.

Kết quả:

- Thông báo lỗi chính được trả về đúng.
- Hai trường hợp lỗi đã được đưa vào unit test hồi quy.
- Toàn bộ 46 unit test T02 đều PASS.

## 13. Hạn chế hiện tại

- Chưa hỗ trợ mọi biến thể cú pháp CFG.
- Terminal nhiều ký tự hiện ưu tiên id và num.
- Tên biến tuân theo quy ước của tokenizer.
- Một số ký hiệu đặc biệt chưa được hỗ trợ làm terminal.
- Parser chưa có hệ thống mã lỗi nâng cao.
- Khi văn phạm đã có lỗi, kiểm tra start symbol được hoãn đến lần phân tích tiếp theo.
- Chưa tích hợp parser vào giao diện Flask.
- Cấu trúc Grammar cần được thống nhất với các module CNF và CYK.
- Chưa kiểm chứng kết quả trong môi trường Docker và GitHub Actions.

## 14. Hướng phát triển

- Hoàn thiện normalization và diagnostics trong T03.
- Bổ sung mã lỗi và chuẩn hóa thông báo lỗi.
- Hoàn thiện khả năng xử lý các biến thể nhập liệu theo yêu cầu nhóm.
- Tái sử dụng Grammar Model cho T07.
- Tích hợp bộ test T02 vào test runner tổng T22.

## 15. Nội dung cần nắm khi bảo vệ

1. Định nghĩa CFG và bốn thành phần V, Σ, P, S.
2. Sự khác nhau giữa biến và terminal.
3. Vai trò của tokenizer và parser.
4. Cách nhận diện terminal nhiều ký tự.
5. Cách biểu diễn epsilon bằng tuple rỗng.
6. Lý do dùng set, dict và tuple.
7. Cách kiểm tra biến chưa khai báo.
8. Cách xác định ký hiệu bắt đầu.
9. Cách thu thập thông tin lỗi.
10. Cách ngăn production trùng lặp.
11. Cách sao chép Grammar không mutation.
12. Độ phức tạp của tokenizer và parser.
13. Ý nghĩa của bộ 46 unit test.

## 16. Minh chứng

- [ ] Ảnh cây thư mục mã nguồn T02.
- [ ] Ảnh kiểm thử Grammar Model.
- [ ] Ảnh kiểm thử Tokenizer.
- [ ] Ảnh kiểm thử Parser CFG.
- [ ] Ảnh kết quả 46 passed của T02.
- [ ] Ảnh kết quả 50 passed của toàn dự án.
- [ ] Ảnh kiểm thử Docker.
- [ ] Link Pull Request.
- [ ] Kết quả GitHub Actions CI.

## 17. Khai báo sử dụng AI

Sử dụng ChatGPT để hỗ trợ thiết kế cấu trúc dữ liệu, xây dựng thuật toán, đề xuất unit test, phân tích lỗi và soạn thảo tài liệu kỹ thuật.

Mã nguồn đã được kiểm thử local bởi thành viên thực hiện. Thành viên cần nắm được nguyên lý hoạt động và chịu trách nhiệm kiểm tra nội dung trước khi bàn giao.

## 18. Kết luận

T02 đã xây dựng Grammar Model, Tokenizer và Parser CFG, đáp ứng các trường hợp kiểm thử hiện tại.

Parser có khả năng chuyển văn bản CFG thành dữ liệu có cấu trúc, kiểm tra cú pháp và trả về thông tin lỗi.

Kết quả kiểm thử local đạt 46/46 test T02 và 50/50 test toàn dự án.

Các module đã tạo là nền tảng để tiếp tục T03, chuyển đổi CFG sang CNF và tích hợp thuật toán CYK.