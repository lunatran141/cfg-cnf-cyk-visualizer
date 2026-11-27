# T03 - Chuẩn hóa Parser và Diagnostics CFG

## 1. Thông tin nhiệm vụ

| Thuộc tính | Nội dung |
|---|---|
| Mã task | T03 |
| Thành viên | Tuấn - TV5 |
| Nhóm công việc | Thuật toán/Parser |
| Dự án | CFG-CNF-CYK Visualizer |
| Ngày bắt đầu | 25/11/2026 |
| Deadline | 25/11/2026 |
| Nhánh phát triển | feature/T03-parser-errors |
| Task tiền nhiệm | T02 - Parser CFG và Tokenizer |
| Đầu ra | Parser normalization, diagnostics, unit test và tài liệu Markdown |

## 2. Mục tiêu

T03 nâng cấp Parser CFG đã xây dựng trong T02 nhằm chuẩn hóa văn bản đầu vào, phát hiện lỗi có hệ thống và cung cấp thông báo lỗi rõ ràng cho người sử dụng.

Các mục tiêu chính:

- Chuẩn hóa khoảng trắng và ký hiệu tương đương.
- Hỗ trợ các ký hiệu Unicode được quy định.
- Giữ nguyên quy ước tên biến và terminal của T02.
- Phát hiện và phân loại lỗi văn phạm.
- Cung cấp mã lỗi thống nhất.
- Xác định chính xác dòng và cột lỗi trong văn bản gốc.
- Cung cấp thông điệp và gợi ý sửa lỗi.
- Hỗ trợ chuyển đổi kết quả sang JSON.
- Đảm bảo tương thích với các chức năng T01 và T02.

## 3. Phạm vi và yêu cầu nhiệm vụ

| STT | Yêu cầu | Kết quả thực hiện |
|---|---|---|
| 1 | Chuẩn hóa khoảng trắng, mũi tên, dấu phân cách và quy ước tên biến/terminal | Hoàn thành |
| 2 | Phân loại lỗi cú pháp, ký hiệu chưa khai báo và production rỗng | Hoàn thành |
| 3 | Trả về dòng, mã lỗi, thông điệp và gợi ý sửa | Hoàn thành |
| 4 | Kiểm thử định dạng tương đương, Unicode, lỗi liên tiếp và input rất ngắn | Hoàn thành |
| 5 | Bàn giao normalization, diagnostics, test và file Markdown | Hoàn thành phần local |

T03 không thực hiện các thuật toán chuyển đổi CNF hoặc phân tích CYK.

## 4. Cơ sở lý thuyết

### 4.1. Văn phạm phi ngữ cảnh

Văn phạm phi ngữ cảnh CFG được biểu diễn bởi bộ bốn thành phần:

G = (V, Σ, P, S)

Trong đó:

- V: tập ký hiệu biến.
- Σ: tập ký hiệu kết thúc.
- P: tập luật sinh.
- S: ký hiệu bắt đầu.

Mỗi luật sinh CFG có dạng:

A → α

Trong đó A là một biến và α là chuỗi gồm các biến, terminal hoặc epsilon.

### 4.2. Chuẩn hóa đầu vào

Normalization là quá trình đưa những cách biểu diễn tương đương của văn bản về một định dạng thống nhất trước khi phân tích cú pháp.

Ví dụ:

~~~text
  S   →   A B ｜ id
  A   →   a
  B   →   ε
~~~

Sau khi chuẩn hóa:

~~~text
S -> A B | id
A -> a
B -> ε
~~~

Quá trình này không chuyển đổi CFG sang CNF và không làm thay đổi các luật sinh hợp lệ.

### 4.3. Diagnostics

Diagnostics là cơ chế thu thập, phân loại và trình bày thông tin lỗi trong quá trình phân tích văn phạm.

Một lỗi cần cung cấp:

- Vị trí dòng.
- Vị trí cột.
- Mã lỗi.
- Nội dung liên quan.
- Thông điệp mô tả.
- Gợi ý khắc phục.

Diagnostics giúp người dùng xác định nguyên nhân lỗi và chỉnh sửa văn phạm trước khi tiếp tục các thuật toán xử lý CFG.

## 5. Kiến trúc chương trình

### 5.1. Luồng xử lý

~~~mermaid
flowchart TD
    A[CFG Input] --> B[Normalizer]
    B --> C[Tokenizer]
    C --> D[Parser CFG]
    D --> E{Co loi?}
    E -->|Khong| F[Grammar Model]
    E -->|Co| G[Diagnostics]
    F --> H[ParseResult]
    G --> H
    H --> I[JSON-compatible data]
~~~

### 5.2. Các module

| Module | Trách nhiệm |
|---|---|
| grammar.py | Lưu trữ mô hình Grammar |
| tokenizer.py | Phân tách các token |
| normalizer.py | Chuẩn hóa đầu vào và ánh xạ vị trí |
| diagnostics.py | Quản lý mã lỗi và thông tin lỗi |
| parser.py | Điều phối quá trình phân tích CFG |
| test_parser_errors.py | Kiểm thử chức năng T03 |

Grammar Model và Tokenizer được kế thừa từ T02.

## 6. Xây dựng Normalizer

### 6.1. Quy tắc chuẩn hóa

| Thành phần | Đầu vào | Kết quả |
|---|---|---|
| Mũi tên Unicode | → | -> |
| Mũi tên ASCII | -> | -> |
| Dấu phân cách Unicode | ｜ | Dấu pipe ASCII |
| Khoảng trắng liên tiếp | Nhiều dấu cách | Một dấu cách |
| Tab | Ký tự tab | Dấu cách |
| Khoảng trắng Unicode | NBSP | Dấu cách |
| Khoảng trắng đầu/cuối dòng | Có | Loại bỏ |
| Dòng rỗng | Có | Giữ vị trí dòng |
| Tên biến | A1, S0, B' | Giữ nguyên |
| Terminal | a, id, num | Giữ nguyên |
| Epsilon | ε | Giữ nguyên |
| Ký hiệu không hợp lệ | @, #, $ | Giữ lại để báo lỗi |

Normalizer không tự động chuyển đổi chữ hoa thành chữ thường hoặc ngược lại.

Điều này đảm bảo không làm thay đổi ý nghĩa của biến và terminal.

### 6.2. Cấu trúc NormalizedLine

| Thuộc tính | Kiểu dữ liệu | Ý nghĩa |
|---|---|---|
| original | str | Nội dung dòng gốc |
| text | str | Nội dung dòng chuẩn hóa |
| line | int | Số dòng |
| column_map | tuple[int, ...] | Ánh xạ vị trí cột |

NormalizedLine sử dụng dataclass với frozen=True nhằm hạn chế thay đổi dữ liệu sau khi khởi tạo.

### 6.3. Các hàm chính

| Hàm | Chức năng |
|---|---|
| normalize_line() | Chuẩn hóa một dòng |
| normalize_lines() | Chuẩn hóa nhiều dòng |
| normalize_grammar() | Trả về toàn bộ văn bản chuẩn hóa |
| original_column() | Khôi phục vị trí cột trong văn bản gốc |

### 6.4. Thuật toán chuẩn hóa

~~~text
Input: Một dòng văn phạm
Output: NormalizedLine

1. Khởi tạo danh sách ký tự kết quả.
2. Khởi tạo danh sách ánh xạ vị trí cột.
3. Duyệt từng ký tự trong dòng gốc.
4. Nếu là khoảng trắng:
   - Loại bỏ khoảng trắng đầu dòng.
   - Gộp khoảng trắng liên tiếp.
5. Nếu là ký hiệu tương đương:
   - Thay thế bằng ký hiệu chuẩn.
6. Nếu là ký hiệu khác:
   - Giữ nguyên ký hiệu.
7. Lưu vị trí gốc tương ứng với mỗi ký tự đầu ra.
8. Loại bỏ khoảng trắng cuối dòng.
9. Trả về NormalizedLine.
~~~

### 6.5. Ánh xạ vị trí cột

Ví dụ đầu vào:

~~~text
S → a@
~~~

Văn bản chuẩn hóa:

~~~text
S -> a@
~~~

Bảng ánh xạ:

| Cột chuẩn hóa | Ký tự | Cột gốc |
|---:|---|---:|
| 1 | S | 1 |
| 2 | Space | 2 |
| 3 | - | 3 |
| 4 | > | 3 |
| 5 | Space | 4 |
| 6 | a | 5 |
| 7 | @ | 6 |

column_map:

~~~python
(1, 2, 3, 3, 4, 5, 6)
~~~

Ký hiệu @ được phát hiện tại cột 7 trong văn bản chuẩn hóa nhưng nằm tại cột 6 trong văn bản gốc.

Hàm original_column(7) trả về 6.

Nhờ đó, parser không báo sai vị trí lỗi khi ký hiệu Unicode được thay thế bằng nhiều ký tự ASCII.

### 6.6. Tính nhất quán

Normalizer được kiểm thử tính idempotence:

N(N(x)) = N(x)

Chuẩn hóa lại văn bản đã chuẩn hóa không làm thay đổi kết quả trong các trường hợp được kiểm thử.

## 7. Xây dựng Diagnostics

### 7.1. ErrorCode

ErrorCode sử dụng StrEnum của Python 3.11 để quản lý các mã lỗi.

| STT | Mã lỗi | Ý nghĩa | Hướng khắc phục |
|---:|---|---|---|
| 1 | EMPTY_INPUT | Văn phạm rỗng | Nhập ít nhất một luật sinh |
| 2 | INVALID_INPUT_TYPE | Sai kiểu đầu vào | Sử dụng dữ liệu dạng chuỗi |
| 3 | INVALID_SYMBOL | Ký hiệu không hợp lệ | Xóa hoặc thay thế ký hiệu |
| 4 | MISSING_ARROW | Thiếu mũi tên | Bổ sung mũi tên |
| 5 | MULTIPLE_ARROWS | Nhiều mũi tên | Giữ một mũi tên mỗi dòng |
| 6 | INVALID_LHS | Vế trái không hợp lệ | Sử dụng một biến hợp lệ |
| 7 | EMPTY_RHS | Vế phải rỗng | Bổ sung luật sinh hoặc epsilon |
| 8 | EMPTY_PRODUCTION | Production rỗng | Bổ sung production hoặc xóa dấu phân cách thừa |
| 9 | INVALID_EPSILON | Epsilon sử dụng sai | Đặt epsilon riêng trong một production |
| 10 | UNDEFINED_VARIABLE | Biến chưa khai báo | Bổ sung luật sinh cho biến |
| 11 | INVALID_START_SYMBOL | Ký hiệu bắt đầu không hợp lệ | Chọn biến đã khai báo |

### 7.2. Cấu trúc ParseError

| Thuộc tính | Kiểu dữ liệu | Ý nghĩa |
|---|---|---|
| line | int | Dòng xảy ra lỗi |
| column | int | Cột xảy ra lỗi |
| code | ErrorCode | Mã định danh lỗi |
| content | str | Nội dung văn bản liên quan |
| message | str | Thông báo lỗi |
| suggestion | str | Gợi ý sửa lỗi |

ParseError hỗ trợ phương thức to_dict() để chuyển dữ liệu sang dạng tương thích JSON.

### 7.3. Class Diagnostics

| Phương thức | Chức năng |
|---|---|
| add() | Thêm lỗi mới |
| errors | Trả về danh sách lỗi đã sắp xếp |
| has_errors | Kiểm tra có lỗi hay không |
| count() | Đếm tổng số lỗi |
| to_dict() | Chuyển danh sách lỗi thành dictionary |
| clear() | Xóa toàn bộ lỗi |

Danh sách lỗi được sắp xếp theo thứ tự dòng và cột tăng dần.

Danh sách trả về từ thuộc tính errors là danh sách mới, giúp tránh việc chỉnh sửa trực tiếp danh sách nội bộ.

### 7.4. Ví dụ dữ liệu lỗi

Input:

~~~text
S → a@b
~~~

Kết quả lỗi:

~~~json
{
    "line": 1,
    "column": 6,
    "code": "INVALID_SYMBOL",
    "content": "S → a@b",
    "message": "Ký hiệu không hợp lệ: @",
    "suggestion": "Xóa hoặc thay thế ký hiệu không hợp lệ."
}
~~~

## 8. Nâng cấp Parser CFG

### 8.1. Giao diện hàm

~~~python
parseGrammar(
    text: str,
    start_symbol: str | None = None,
) -> ParseResult
~~~

Tên hàm parseGrammar được giữ nguyên từ T02.

### 8.2. ParseResult

| Thuộc tính | Ý nghĩa |
|---|---|
| grammar | Grammar hợp lệ hoặc None |
| errors | Danh sách ParseError |
| success | Trạng thái phân tích |
| to_dict() | Chuyển kết quả sang dữ liệu tương thích JSON |

Nếu văn phạm không hợp lệ, parser không trả về Grammar chưa hoàn chỉnh.

### 8.3. Thuật toán tổng quát

~~~text
Input: Văn bản CFG và ký hiệu bắt đầu tùy chọn
Output: ParseResult

1. Khởi tạo Grammar và Diagnostics.
2. Kiểm tra kiểu dữ liệu đầu vào.
3. Kiểm tra văn phạm rỗng.
4. Chuẩn hóa ký tự xuống dòng.
5. Chuẩn hóa văn bản CFG.
6. Duyệt từng dòng:
   6.1. Bỏ qua dòng rỗng.
   6.2. Phân tách token.
   6.3. Kiểm tra ký hiệu không hợp lệ.
   6.4. Kiểm tra số lượng mũi tên.
   6.5. Kiểm tra vế trái.
   6.6. Kiểm tra vế phải.
   6.7. Tách các production.
   6.8. Kiểm tra production rỗng.
   6.9. Kiểm tra epsilon.
   6.10. Xây dựng Grammar.
7. Kiểm tra các biến tham chiếu chưa khai báo.
8. Xác định ký hiệu bắt đầu.
9. Nếu không có lỗi trước đó, kiểm tra ký hiệu bắt đầu.
10. Nếu có lỗi:
    - Sắp xếp diagnostics.
    - Trả về grammar=None và danh sách lỗi.
11. Nếu không có lỗi:
    - Trả về Grammar hợp lệ.
~~~

### 8.4. Xử lý nhiều lỗi

Parser tiếp tục xử lý các dòng tiếp theo sau khi phát hiện lỗi tại một dòng.

Ví dụ:

~~~text
S → @
A b
B →
a → b
C → a || b
~~~

Kết quả:

| Dòng | Mã lỗi |
|---:|---|
| 1 | INVALID_SYMBOL |
| 2 | MISSING_ARROW |
| 3 | EMPTY_RHS |
| 4 | INVALID_LHS |
| 5 | EMPTY_PRODUCTION |

Parser không dừng toàn bộ quá trình ngay khi phát hiện lỗi đầu tiên.

Một số lỗi cú pháp trên cùng một dòng được xử lý theo thứ tự ưu tiên, do đó không đảm bảo phát hiện mọi lỗi có thể có trên dòng đó.

### 8.5. Kiểm tra biến chưa khai báo

Ví dụ:

~~~text
S → AB
A → a
~~~

Biến B xuất hiện tại vế phải nhưng không có luật sinh khai báo tại vế trái.

Parser trả về mã lỗi UNDEFINED_VARIABLE.

Việc kiểm tra được thực hiện sau khi đọc toàn bộ văn phạm để hỗ trợ khai báo biến ở các dòng phía sau.

Đây là quy tắc kiểm tra đầu vào của dự án, không phải điều kiện bắt buộc của mọi định nghĩa CFG tổng quát.

### 8.6. Hạn chế lỗi dây chuyền

Ví dụ:

~~~text
S → a@b
~~~

Parser trả về INVALID_SYMBOL.

Việc kiểm tra ký hiệu bắt đầu được bỏ qua nếu đã có lỗi trước đó nhằm hạn chế thông báo INVALID_START_SYMBOL phát sinh do quá trình phân tích chưa hoàn chỉnh.

### 8.7. Hỗ trợ ký tự xuống dòng

Parser hỗ trợ:

- LF: hệ điều hành Linux.
- CRLF: hệ điều hành Windows.
- CR: một số định dạng văn bản cũ.

Các kiểu xuống dòng được chuẩn hóa trước khi phân tích.

## 9. Ví dụ kết quả phân tích

### 9.1. Văn phạm hợp lệ

Input:

~~~text
S → id ｜ ε
~~~

Output:

~~~json
{
    "success": true,
    "grammar": {
        "variables": ["S"],
        "terminals": ["id"],
        "productions": {
            "S": [
                [],
                ["id"]
            ]
        },
        "start_symbol": "S"
    },
    "errors": []
}
~~~

Epsilon được biểu diễn bằng tuple rỗng trong Grammar và danh sách rỗng trong JSON.

### 9.2. Văn phạm không hợp lệ

Input:

~~~text
S → a@b
~~~

Output:

~~~json
{
    "success": false,
    "grammar": null,
    "errors": [
        {
            "line": 1,
            "column": 6,
            "code": "INVALID_SYMBOL",
            "content": "S → a@b",
            "message": "Ký hiệu không hợp lệ: @",
            "suggestion": "Xóa hoặc thay thế ký hiệu không hợp lệ."
        }
    ]
}
~~~

## 10. Phân tích độ phức tạp

Quy ước:

- n: tổng số ký tự đầu vào.
- t: tổng số token.
- r: tổng số lần tham chiếu biến.
- e: tổng số lỗi.

### 10.1. Normalizer

Mỗi ký tự được duyệt một lần.

- Thời gian: O(n).
- Bộ nhớ bổ sung: O(n).

Bộ nhớ bổ sung dùng để lưu văn bản chuẩn hóa và ánh xạ vị trí cột.

### 10.2. Parser

Parser duyệt các token, xây dựng luật sinh và kiểm tra biến tham chiếu.

Với giả định thao tác tra cứu set và dictionary có độ phức tạp trung bình O(1):

- Phân tích token: O(t).
- Kiểm tra biến tham chiếu: O(r).
- Bộ nhớ lưu Grammar và tham chiếu: O(t).

### 10.3. Diagnostics

- Thêm lỗi: O(1) trung bình.
- Sắp xếp một lần danh sách lỗi: O(e log e).
- Bộ nhớ lưu lỗi: O(e), tính theo số bản ghi.

### 10.4. Tổng hợp

Độ phức tạp thời gian ước tính:

O(n + t + r + e log e)

Độ phức tạp bộ nhớ bổ sung:

O(n + t + e)

Các biểu thức trên sử dụng mô hình chi phí thông thường, chưa tính chi tiết chi phí sao chép chuỗi, hash chuỗi, sắp xếp các tập trong Grammar.to_dict() và kích thước JSON đầu ra.

Đây là phân tích lý thuyết, không phải kết quả benchmark thực nghiệm.

## 11. Kiểm thử

### 11.1. Môi trường

| Thành phần | Thông tin |
|---|---|
| Hệ điều hành local | Windows |
| Python | 3.11.9 |
| IDE | Visual Studio Code |
| Terminal | PowerShell |
| Môi trường ảo | .venv |
| Framework kiểm thử | Pytest |

### 11.2. Kiểm thử Normalizer

| Mã test | Nội dung | Kết quả |
|---|---|---|
| NM01 | Mũi tên ASCII | PASS |
| NM02 | Mũi tên Unicode | PASS |
| NM03 | Pipe ASCII | PASS |
| NM04 | Pipe Unicode | PASS |
| NM05 | Khoảng trắng đầu dòng | PASS |
| NM06 | Khoảng trắng cuối dòng | PASS |
| NM07 | Khoảng trắng liên tiếp | PASS |
| NM08 | Tab | PASS |
| NM09 | Khoảng trắng Unicode | PASS |
| NM10 | Tên biến | PASS |
| NM11 | Tên terminal | PASS |
| NM12 | Epsilon | PASS |
| NM13 | Input rỗng | PASS |
| NM14 | Input chỉ chứa khoảng trắng | PASS |
| NM15 | Input một ký tự | PASS |
| NM16 | Dòng rỗng | PASS |
| NM17 | Giữ ký hiệu không hợp lệ | PASS |
| NM18 | Idempotence | PASS |
| NM19 | Ánh xạ vị trí cột | PASS |
| NM20 | Số dòng | PASS |

Tổng cộng: 20 test.

### 11.3. Kiểm thử Diagnostics

| Mã test | Nội dung | Kết quả |
|---|---|---|
| DG01 | Số lượng mã lỗi | PASS |
| DG02 | Giá trị mã lỗi | PASS |
| DG03 | Diagnostics rỗng | PASS |
| DG04 | Thêm lỗi | PASS |
| DG05 | Các thuộc tính lỗi | PASS |
| DG06 | Chuyển lỗi thành dictionary | PASS |
| DG07 | JSON serialization | PASS |
| DG08 | Sắp xếp theo dòng | PASS |
| DG09 | Sắp xếp theo cột | PASS |
| DG10 | Tính độc lập của danh sách lỗi | PASS |
| DG11 | Xóa diagnostics | PASS |
| DG12 | Kiểu dữ liệu ParseError | PASS |

Tổng cộng: 12 test.

### 11.4. Kiểm thử Parser T03

| Mã test | Nội dung | Kết quả |
|---|---|---|
| PS01 | Các định dạng tương đương | PASS |
| PS02 | Mũi tên Unicode | PASS |
| PS03 | Pipe Unicode | PASS |
| PS04 | Khoảng trắng Unicode | PASS |
| PS05 | Input rỗng | PASS |
| PS06 | Input chỉ chứa khoảng trắng | PASS |
| PS07 | Input sai kiểu | PASS |
| PS08 | Ký hiệu không hợp lệ | PASS |
| PS09 | Thiếu mũi tên | PASS |
| PS10 | Nhiều mũi tên | PASS |
| PS11 | Vế trái không hợp lệ | PASS |
| PS12 | Vế phải rỗng | PASS |
| PS13 | Production rỗng ở giữa | PASS |
| PS14 | Production rỗng ở đầu | PASS |
| PS15 | Production rỗng ở cuối | PASS |
| PS16 | Epsilon không hợp lệ | PASS |
| PS17 | Biến chưa khai báo | PASS |
| PS18 | Ký hiệu bắt đầu không hợp lệ | PASS |
| PS19 | Vị trí cột gốc | PASS |
| PS20 | Nội dung dòng gốc | PASS |
| PS21 | Vị trí sau dòng rỗng | PASS |
| PS22 | Nhiều ký hiệu không hợp lệ | PASS |
| PS23 | Lỗi liên tiếp trên nhiều dòng | PASS |
| PS24 | Input rất ngắn | PASS |
| PS25 | JSON kết quả hợp lệ | PASS |
| PS26 | JSON kết quả lỗi | PASS |
| PS27 | Các kiểu xuống dòng | PASS |
| PS28 | Hạn chế lỗi dây chuyền start symbol | PASS |

Tổng cộng: 28 test.

### 11.5. Tổng hợp kết quả

| Bộ kiểm thử | Tổng số test | PASS | FAIL |
|---|---:|---:|---:|
| Normalizer | 20 | 20 | 0 |
| Diagnostics | 12 | 12 | 0 |
| Parser T03 | 28 | 28 | 0 |
| Tổng T03 | 60 | 60 | 0 |
| Hồi quy T02 | 46 | 46 | 0 |
| Hồi quy T01 | 4 | 4 | 0 |
| Toàn dự án | 110 | 110 | 0 |

Kết quả PASS được ghi nhận theo xác nhận kiểm thử local của thành viên thực hiện.

### 11.6. Lệnh kiểm thử

Kiểm tra cú pháp:

~~~powershell
python -m py_compile app/services/normalizer.py app/services/diagnostics.py app/services/parser.py tests/test_parser_errors.py
~~~

Kiểm thử riêng T03:

~~~powershell
python -m pytest tests/test_parser_errors.py -v
~~~

Kiểm thử toàn dự án:

~~~powershell
python -m pytest -v
~~~

## 12. Các file đóng góp

| File | Loại thay đổi | Nội dung |
|---|---|---|
| app/services/normalizer.py | Tạo mới | Chuẩn hóa văn phạm |
| app/services/diagnostics.py | Tạo mới | Quản lý mã lỗi và diagnostics |
| app/services/parser.py | Cập nhật | Tích hợp normalization và diagnostics |
| tests/test_parser_errors.py | Tạo mới | 60 unit test T03 |
| docs/contributions/TV5/T03-parser-errors.md | Tạo mới | Tài liệu bàn giao T03 |

Không chủ động thay đổi Grammar Model, Tokenizer hoặc bộ test T01 và T02.

## 13. So sánh trước và sau T03

| Chức năng | T02 | T03 |
|---|---|---|
| Grammar Model | Có | Tái sử dụng |
| Tokenizer | Có | Tái sử dụng |
| Parser CFG | Có | Nâng cấp |
| Chuẩn hóa riêng biệt | Chưa có | Có |
| Mũi tên Unicode | Có | Có chuẩn hóa |
| Pipe Unicode | Chưa hỗ trợ | Có |
| Khoảng trắng Unicode | Hạn chế | Có chuẩn hóa |
| Mã lỗi | Chưa có | 11 mã lỗi |
| Dòng và cột lỗi | Có | Ánh xạ về văn bản gốc |
| Gợi ý sửa lỗi | Có | Tiếp tục hỗ trợ |
| ParseResult.to_dict() | Chưa có | Có |
| Quản lý danh sách lỗi | Cơ bản | Diagnostics |
| Unit test bổ sung | 46 | 60 |

## 14. Các vấn đề gặp phải

### 14.1. Sai lệch vị trí cột

Nguyên nhân:

Ký hiệu mũi tên Unicode có một ký tự, trong khi mũi tên ASCII có hai ký tự.

Giải pháp:

Sử dụng column_map để khôi phục vị trí gốc.

### 14.2. Khác biệt giữa các kiểu xuống dòng

Nguyên nhân:

Văn bản từ Windows và Linux có thể sử dụng ký tự xuống dòng khác nhau.

Giải pháp:

Chuẩn hóa CRLF và CR thành LF trước khi phân tích.

### 14.3. Lỗi chạy script kiểm thử

Nguyên nhân:

Script sử dụng PowerShell here-string được dán nhầm vào Python Shell.

Hậu quả:

Phát sinh SyntaxError, IndentationError và kết quả đếm 0 test.

Giải pháp:

Chạy script đúng môi trường PowerShell và bổ sung bộ unit test Pytest.

Không sử dụng kết quả 0 test làm bằng chứng kiểm thử thành công.

### 14.4. Tương thích với T02

Giải pháp:

- Giữ nguyên tên hàm parseGrammar().
- Giữ các thuộc tính kết quả chính.
- Tái sử dụng Grammar và Tokenizer.
- Chạy lại toàn bộ bộ test hồi quy.

## 15. Hạn chế

- Chỉ hỗ trợ quy ước tên biến và terminal của T02.
- Terminal nhiều ký tự vẫn giới hạn theo quy tắc Tokenizer hiện tại.
- Không hỗ trợ tất cả ký hiệu Unicode có thể tồn tại.
- Không tự động sửa lỗi cú pháp.
- Không đảm bảo phát hiện mọi lỗi trên cùng một dòng.
- Có thể phát sinh lỗi biến chưa khai báo nếu dòng khai báo biến chứa lỗi cú pháp.
- Vị trí cột tính theo ký tự trong chuỗi Python, không phải độ rộng hiển thị của tab hoặc ký tự Unicode.
- Lỗi start symbol sử dụng vị trí quy ước dòng 1, cột 1.
- Chưa tích hợp hiển thị diagnostics trên giao diện frontend.
- Chưa xác nhận khả năng tương thích với mọi thành phần tích hợp trong tương lai.
- Chưa kiểm thử Docker local.

## 16. Hướng phát triển

- Tích hợp diagnostics vào giao diện nhập CFG.
- Hiển thị vị trí lỗi trực tiếp trong trình nhập văn bản.
- Mở rộng quy ước terminal nếu nhóm thống nhất.
- Hỗ trợ cảnh báo bên cạnh lỗi.
- Bổ sung kiểm thử sinh dữ liệu và trường hợp biên.
- Kiểm thử tích hợp với pipeline chuyển đổi CNF và CYK.

## 17. Nội dung phục vụ bảo vệ đồ án

### Câu 1. Tại sao cần Normalizer?

Normalizer giúp các định dạng nhập tương đương được đưa về một cách biểu diễn thống nhất, giảm sự phụ thuộc vào cách người dùng nhập văn phạm.

### Câu 2. Tại sao cần column_map?

Vì quá trình chuẩn hóa có thể thay đổi số lượng ký tự. column_map giúp xác định đúng vị trí lỗi trong văn bản gốc.

### Câu 3. Tại sao cần mã lỗi?

Mã lỗi giúp phân loại lỗi thống nhất, hỗ trợ kiểm thử tự động và giúp frontend xử lý từng nhóm lỗi mà không phụ thuộc vào nội dung thông báo.

### Câu 4. Tại sao kiểm tra biến chưa khai báo sau khi đọc toàn bộ CFG?

Vì một biến có thể được sử dụng trước khi luật sinh của biến đó xuất hiện ở các dòng tiếp theo.

### Câu 5. Tại sao epsilon phải đứng riêng?

Epsilon đại diện cho chuỗi rỗng. Trong định dạng nhập của dự án, epsilon phải được biểu diễn thành một production riêng để tránh cách viết mơ hồ.

### Câu 6. Parser có dừng khi phát hiện lỗi đầu tiên không?

Không. Parser tiếp tục kiểm tra các dòng khác và tập hợp lỗi. Tuy nhiên, một số lỗi nghiêm trọng sẽ khiến parser bỏ qua những bước còn lại của dòng hiện tại.

### Câu 7. T03 có làm thay đổi thuật toán T02 không?

T03 bổ sung bước chuẩn hóa và nâng cấp cơ chế báo lỗi, đồng thời giữ lại mô hình Grammar, Tokenizer và chức năng phân tích chính của T02.

### Câu 8. Tại sao khi có lỗi lại trả về grammar=None?

Để tránh đưa một Grammar chưa hợp lệ vào những thuật toán phía sau như chuyển đổi CNF và CYK.

### Câu 9. Làm sao chứng minh T03 không phá vỡ T02?

Sử dụng bộ kiểm thử hồi quy gồm 46 test T02 và 4 test T01.

### Câu 10. Đóng góp chính của T03 là gì?

Chuẩn hóa đầu vào, giữ vị trí lỗi gốc, cung cấp 11 mã lỗi, hỗ trợ JSON và bổ sung 60 unit test.

## 18. Checklist bàn giao

- [x] Chuẩn hóa khoảng trắng.
- [x] Chuẩn hóa mũi tên.
- [x] Chuẩn hóa dấu phân cách.
- [x] Giữ quy ước tên biến và terminal.
- [x] Phân loại lỗi bằng ErrorCode.
- [x] Lưu dòng và cột lỗi.
- [x] Lưu nội dung lỗi gốc.
- [x] Cung cấp thông báo và gợi ý.
- [x] Hỗ trợ JSON serialization.
- [x] Kiểm thử Unicode.
- [x] Kiểm thử lỗi liên tiếp.
- [x] Kiểm thử input rất ngắn.
- [x] Viết 60 unit test T03.
- [x] Chạy kiểm thử hồi quy.
- [x] Soạn tài liệu Markdown.
- [ ] Rà soát Git và staging.
- [ ] Commit và push.
- [ ] GitHub Actions - test.
- [ ] GitHub Actions - docker-build.
- [ ] Pull Request vào develop.
- [ ] Review và merge.

## 19. Minh chứng kiểm thử

Các minh chứng cần bổ sung sau khi hoàn tất bàn giao:

| Minh chứng | Trạng thái |
|---|---|
| Terminal chạy riêng 60 test T03 | Cần lưu log hoặc ảnh |
| Terminal chạy toàn bộ 110 test | Cần lưu log hoặc ảnh |
| Git status và git diff | Chờ rà soát |
| Commit T03 | Chờ thực hiện |
| GitHub Actions - test | Chờ CI |
| GitHub Actions - docker-build | Chờ CI |
| Pull Request T03 | Chờ thực hiện |
| Review và merge | Chờ nhóm trưởng |

## 20. Tài liệu tham khảo

1. Python Software Foundation. Python 3.11 Documentation - dataclasses.
   https://docs.python.org/3.11/library/dataclasses.html

2. Python Software Foundation. Python 3.11 Documentation - enum.
   https://docs.python.org/3.11/library/enum.html

3. Python Software Foundation. Python 3.11 Documentation - json.
   https://docs.python.org/3.11/library/json.html

4. Pytest Documentation.
   https://docs.pytest.org/

5. Tài liệu đóng góp T02 của nhóm.
   docs/contributions/TV5/T02-cfg-parser.md

## 21. Sử dụng công cụ hỗ trợ AI

ChatGPT được sử dụng để hỗ trợ:

- Phân tích yêu cầu nhiệm vụ.
- Đề xuất thiết kế Normalizer và Diagnostics.
- Hỗ trợ xây dựng và giải thích mã nguồn.
- Đề xuất các trường hợp kiểm thử.
- Hỗ trợ xử lý lỗi khi chạy kiểm thử.
- Hỗ trợ soạn tài liệu Markdown.

Thành viên thực hiện chịu trách nhiệm kiểm tra mã nguồn, chạy kiểm thử, xác minh kết quả và thực hiện các thao tác Git.

## 22. Kết luận

T03 nâng cấp khả năng xử lý đầu vào và thông báo lỗi của Parser CFG.

Các chức năng chính đã được triển khai:

- Chuẩn hóa văn bản CFG.
- Ánh xạ vị trí ký tự về văn bản gốc.
- Quản lý 11 mã lỗi.
- Thu thập và sắp xếp diagnostics.
- Hỗ trợ dữ liệu tương thích JSON.
- Bổ sung 60 unit test.
- Duy trì bộ kiểm thử hồi quy T01 và T02.

T03 tạo nền tảng cho việc tích hợp parser với các thuật toán chuyển đổi văn phạm và giao diện người dùng.

Phần triển khai local và kiểm thử đã được xác nhận hoàn thành. Trạng thái bàn giao cuối cùng phụ thuộc vào kết quả GitHub Actions, review và merge vào develop.
