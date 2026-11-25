<div align="center">

# CFG–CNF–CYK Visualizer

### Ứng dụng web chuyển đổi CFG sang CNF và trực quan hóa từng bước thuật toán CYK

[![Python](https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-Web%20Framework-000000?logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?logo=docker&logoColor=white)](https://www.docker.com/)
[![CI](https://github.com/lunatran141/cfg-cnf-cyk-visualizer/actions/workflows/ci.yml/badge.svg)](https://github.com/lunatran141/cfg-cnf-cyk-visualizer/actions/workflows/ci.yml)

</div>

---

## 1. Giới thiệu

**CFG–CNF–CYK Visualizer** là ứng dụng web hỗ trợ nhập văn phạm phi ngữ cảnh, chuyển đổi CFG sang dạng chuẩn Chomsky và kiểm tra một chuỗi có thuộc ngôn ngữ của văn phạm hay không bằng thuật toán CYK.

Ứng dụng không chỉ trả về kết quả **Accepted** hoặc **Rejected** mà còn trực quan hóa:

- Các bước chuyển đổi CFG sang CNF.
- Bảng quy hoạch động của thuật toán CYK.
- Quá trình điền từng ô trong bảng.
- Luật sinh và điểm chia được sử dụng.
- Cây phân tích cú pháp được dựng từ backpointer.
- Nguyên nhân chuỗi được chấp nhận hoặc từ chối.

Dự án được thực hiện trong học phần **Ngôn ngữ hình thức và Automata**.

---

## 2. Mục tiêu

- Vận dụng kiến thức về văn phạm phi ngữ cảnh CFG.
- Cài đặt quy trình chuyển đổi CFG sang CNF.
- Tự cài đặt thuật toán CYK bằng Python.
- Phân tích độ phức tạp thời gian và bộ nhớ.
- Trực quan hóa thuật toán bằng giao diện web.
- Kiểm thử các trường hợp hợp lệ, không hợp lệ và trường hợp biên.
- Tổ chức mã nguồn theo module để các thành viên phát triển song song.
- Đóng gói ứng dụng bằng Docker.

---

## 3. Đầu vào và đầu ra

### Đầu vào

- Văn phạm phi ngữ cảnh CFG.
- Ký hiệu bắt đầu.
- Tập production.
- Chuỗi cần kiểm tra.

Ví dụ văn phạm:

```text
S -> AB | BC
A -> BA | a
B -> CC | b
C -> AB | a
```

Chuỗi cần kiểm tra:

```text
baaba
```

### Đầu ra

- Văn phạm đã được phân tích.
- Danh sách lỗi cú pháp theo từng dòng.
- Văn phạm sau từng bước chuyển đổi.
- Văn phạm cuối cùng ở dạng CNF.
- Bảng CYK và trace của từng ô.
- Kết quả Accepted hoặc Rejected.
- Cây phân tích cú pháp nếu chuỗi được chấp nhận.
- Thống kê thời gian chạy và số lượng production.

---

## 4. Chức năng chính

### 4.1. Nhập và phân tích CFG

- Nhập văn phạm trực tiếp trên giao diện.
- Hỗ trợ nhiều production trên một dòng.
- Nhận diện biến, terminal và ký hiệu `ε`.
- Chuẩn hóa khoảng trắng và ký hiệu mũi tên.
- Hiển thị lỗi kèm số dòng và gợi ý sửa.

### 4.2. Chuyển CFG sang CNF

1. Phân tích và chuẩn hóa CFG.
2. Xác định nullable variables.
3. Loại `ε-production`.
4. Loại unit production bằng unit-closure.
5. Loại non-generating symbols.
6. Loại unreachable symbols.
7. Thay terminal trong production dài.
8. Binarize production dài hơn hai ký hiệu.
9. Kiểm tra kết quả bằng CNF validator.

### 4.3. Thuật toán CYK

- Khởi tạo bảng quy hoạch động.
- Điền hàng cơ sở từ terminal.
- Duyệt theo `length`, `start` và `split`.
- Tra cứu production bằng chỉ mục luật CNF.
- Kiểm tra ký hiệu bắt đầu tại ô cuối.
- Lưu trace và backpointer để giải thích kết quả.

### 4.4. Trực quan hóa

- Hiển thị bảng CYK dạng tam giác.
- Chạy từng bước bằng Next, Previous và Reset.
- Tô màu ô đang xử lý và hai ô nguồn.
- Hiển thị production và điểm chia.
- Dựng parse tree.
- Giải thích Accepted hoặc Rejected.

### 4.5. Kiểm thử và đánh giá

- Unit test cho parser CFG.
- Unit test cho từng bước chuyển CFG sang CNF.
- Unit test cho CNF validator và thuật toán CYK.
- Test chuỗi Accepted, Rejected và các trường hợp biên.
- Test tích hợp toàn bộ luồng xử lý.
- Đo thời gian chạy với nhiều kích thước đầu vào.

---

## 5. Luồng xử lý

```text
Nhập CFG và chuỗi
        |
        v
Parser và Tokenizer
        |
        v
Kiểm tra lỗi CFG
        |
        v
Chuyển CFG sang CNF
        |
        v
CNF Validator
        |
        v
Thuật toán CYK
        |
        v
Bảng CYK + Trace + Backpointer
        |
        v
Accepted/Rejected + Parse Tree
```

---

## 6. Kiến trúc module

| Module | Trách nhiệm |
|---|---|
| `parser` | Đọc và kiểm tra cú pháp CFG |
| `grammar` | Lưu cấu trúc dữ liệu văn phạm |
| `cnf` | Chuyển CFG sang CNF |
| `validator` | Kiểm tra văn phạm có đúng CNF |
| `cyk` | Cài đặt thuật toán CYK |
| `trace` | Lưu các bước thực hiện thuật toán |
| `parse_tree` | Dựng cây phân tích cú pháp |
| `routes` | Kết nối giao diện với backend Flask |
| `templates` | Chứa giao diện HTML |
| `static` | Chứa CSS và JavaScript |
| `tests` | Chứa các bộ kiểm thử |

---

## 7. Cấu trúc thư mục dự kiến

```text
cfg-cnf-cyk-visualizer/
├── .github/
│   └── workflows/
│       └── ci.yml
├── app/
│   ├── algorithms/
│   │   ├── cnf/
│   │   └── cyk/
│   ├── models/
│   ├── services/
│   ├── static/
│   │   ├── css/
│   │   └── js/
│   ├── templates/
│   ├── __init__.py
│   └── routes.py
├── docs/
│   ├── contributions/
│   └── diagrams/
├── tests/
├── .dockerignore
├── .env.example
├── .gitignore
├── Dockerfile
├── requirements.txt
├── run.py
└── README.md
```

---

## 8. Công nghệ sử dụng

| Thành phần | Công nghệ |
|---|---|
| Backend và thuật toán | Python 3.11, Flask |
| Giao diện | HTML, CSS, JavaScript |
| Kiểm thử | Pytest |
| Đóng gói | Docker |
| CI | GitHub Actions |
| Quản lý mã nguồn | Git và GitHub |
| Tài liệu | Markdown |

---

## 9. Cài đặt trên máy cá nhân

Clone repository:

```bash
git clone https://github.com/lunatran141/cfg-cnf-cyk-visualizer.git
cd cfg-cnf-cyk-visualizer
```

Tạo và kích hoạt môi trường ảo trên Windows:

```powershell
python -m venv .venv
.venv\Scripts\activate
```

Cài đặt thư viện:

```powershell
python -m pip install -r requirements.txt
```

Chạy ứng dụng:

```powershell
python run.py
```

Truy cập:

```text
http://localhost:5000
```

> Các lệnh chạy ứng dụng sẽ hoạt động sau khi skeleton Flask của T01 được hoàn thành.

---

## 10. Chạy bằng Docker

Build image:

```bash
docker build -t cfg-cnf-cyk-visualizer .
```

Chạy container:

```bash
docker run --rm -p 5000:5000 cfg-cnf-cyk-visualizer
```

---

## 11. Kiểm thử và CI

Chạy toàn bộ test:

```powershell
pytest -v
```

GitHub Actions sẽ tự động kiểm tra khi:

- Push lên nhánh `feature/*`.
- Tạo Pull Request vào `develop`.
- Tạo Pull Request vào `main`.

Pull Request chỉ được merge khi các CI checks thành công.

---

## 12. Quy trình Git

- `main`: phiên bản ổn định.
- `develop`: nhánh tích hợp.
- `feature/Txx-*`: nhánh thực hiện từng task.

```text
feature/Txx-* → Pull Request → develop → Pull Request → main
```

Ví dụ nhánh T01:

```text
feature/T01-kien-truc-skeleton-docker
```

Quy ước commit:

| Tiền tố | Ý nghĩa |
|---|---|
| `feat` | Thêm chức năng mới |
| `fix` | Sửa lỗi |
| `test` | Thêm hoặc sửa kiểm thử |
| `docs` | Cập nhật tài liệu |
| `refactor` | Tái cấu trúc code |
| `chore` | Cấu hình hoặc công việc hỗ trợ |

---

## 13. Quy tắc Pull Request

Mỗi Pull Request cần:

- Liên kết với mã task tương ứng.
- Mô tả nội dung đã thực hiện.
- Liệt kê file chính đã thay đổi.
- Có hướng dẫn kiểm thử.
- Đính kèm ảnh hoặc log minh chứng nếu cần.
- Vượt qua toàn bộ CI checks.
- Có ít nhất một thành viên review.
- Không còn conversation chưa được giải quyết.

Không push trực tiếp vào `main` hoặc `develop`.

---

## 14. Tài liệu đóng góp

Mỗi thành viên tạo file mô tả tại:

```text
docs/contributions/TVx/
```

Ví dụ T01:

```text
docs/contributions/TV1/T01-kien-truc-skeleton-docker.md
```

File mô tả cần có:

- Mục tiêu của task.
- Input và output.
- Thiết kế hoặc thuật toán.
- Nội dung đã cài đặt.
- File code liên quan.
- Cách chạy và kiểm thử.
- Trường hợp biên.
- Kết quả đạt được.
- Lỗi và hạn chế.
- Hình ảnh hoặc log minh chứng.
- Nội dung chuẩn bị cho phần bảo vệ.

---

## 15. Độ phức tạp dự kiến

Với chuỗi đầu vào có độ dài `n`, thuật toán CYK có:

- Độ phức tạp thời gian cơ bản: `O(n³ × |P|)`.
- Độ phức tạp bộ nhớ: `O(n²)` ô bảng.

Dự án sẽ sử dụng chỉ mục production để giảm chi phí tra cứu luật trong quá trình điền bảng.

---

## 16. Trạng thái dự án

- [x] Khởi tạo repository.
- [x] Thiết lập `main` và `develop`.
- [x] Tạo nhánh T01.
- [ ] Hoàn thiện kiến trúc thư mục.
- [ ] Dựng Flask skeleton.
- [ ] Thiết lập Docker.
- [ ] Thiết lập GitHub Actions CI.
- [ ] Cài đặt parser CFG.
- [ ] Cài đặt chuyển đổi CFG sang CNF.
- [ ] Cài đặt thuật toán CYK.
- [ ] Trực quan hóa bảng CYK.
- [ ] Dựng parse tree.
- [ ] Hoàn thiện kiểm thử và báo cáo.

---

## 17. Trách nhiệm thành viên

Mỗi thành viên chịu trách nhiệm:

1. Cài đặt phần code được giao.
2. Viết kiểm thử cho phần đã cài đặt.
3. Cập nhật file Markdown tương ứng.
4. Tạo Pull Request vào `develop`.
5. Giải thích được code và lý thuyết liên quan khi bảo vệ.

---

## 18. Giới hạn dự kiến

- Chưa hỗ trợ mọi biến thể cú pháp CFG.
- Có thể chỉ hiển thị một parse tree đối với grammar mơ hồ.
- Chưa tối ưu cho chuỗi và grammar có kích thước rất lớn.
- Hiệu năng phụ thuộc số lượng production sau khi chuyển đổi CNF.

Các giới hạn sẽ được cập nhật sau giai đoạn kiểm thử và thực nghiệm.

---

## 19. Khai báo sử dụng AI

Nhóm có thể sử dụng công cụ AI để hỗ trợ:

- Gợi ý cấu trúc dự án.
- Giải thích thuật toán.
- Gợi ý kiểm thử.
- Kiểm tra lỗi và cải thiện cách trình bày.

Mọi nội dung và mã nguồn có AI hỗ trợ đều phải được thành viên kiểm tra, chạy thử và giải thích được khi bảo vệ.

---

<div align="center">

**CFG–CNF–CYK Visualizer — Formal Languages and Automata Project**

</div>
