# T01 Kiến trúc, GitHub, Flask Skeleton và Docker

## 1. Thông tin task

| Thuộc tính | Nội dung |
|---|---|
| Mã task | T01 |
| Nhánh GitHub | `feature/T01-kien-truc-skeleton-docker` |
| Người thực hiện | TV1 |
| Repository | `cfg-cnf-cyk-visualizer` |
| Nhóm công việc | Kiến trúc, GitHub, Flask skeleton và Docker |
| Đầu ra | Cấu trúc repository, module contract, khung ứng dụng, Docker image chạy cổng 5000 và CI |

---

## 2. Mục tiêu

T01 xây dựng nền móng kỹ thuật để các thành viên phát triển những task tiếp theo trên cùng một kiến trúc và quy trình thống nhất.

Các mục tiêu chính:

- Khởi tạo repository GitHub và cấu trúc nhánh.
- Tách mã nguồn theo module để giảm xung đột khi làm việc nhóm.
- Dựng Flask application skeleton.
- Tạo giao diện HTML, CSS và JavaScript cơ bản.
- Cung cấp endpoint kiểm tra trạng thái ứng dụng.
- Viết bộ test đầu tiên bằng Pytest.
- Đóng gói ứng dụng bằng Docker.
- Tạo GitHub Actions CI để tự động chạy test và build Docker.
- Thiết lập quy ước commit, Pull Request và tài liệu đóng góp.

T01 không cài đặt parser CFG, chuyển đổi CNF hoặc thuật toán CYK. Các chức năng đó được phát triển ở những task chuyên biệt sau.

---

## 3. Phạm vi thực hiện

### 3.1. Trong phạm vi

- Repository và Git workflow.
- Flask application factory.
- Blueprint và các route nền tảng.
- Endpoint `/` và `/health`.
- HTML/CSS/JavaScript skeleton.
- Pytest cho ứng dụng Flask.
- `Dockerfile` và `.dockerignore`.
- Workflow `.github/workflows/ci.yml`.
- README và tài liệu T01.

### 3.2. Ngoài phạm vi

- Phân tích cú pháp CFG.
- Chuyển đổi CFG sang CNF.
- Cài đặt thuật toán CYK.
- Dựng parse tree thật.
- Hoàn thiện giao diện sản phẩm cuối.
- Đánh giá hiệu năng thuật toán.

---

## 4. Công nghệ sử dụng

| Thành phần | Công nghệ |
|---|---|
| Ngôn ngữ | Python 3.11.9 |
| Web framework | Flask |
| Giao diện | HTML, CSS, JavaScript |
| Kiểm thử | Pytest 9.2.0 |
| Đóng gói | Docker 29.0.1 |
| CI | GitHub Actions |
| Quản lý mã nguồn | Git và GitHub |
| Tài liệu | Markdown |

Phiên bản thư viện Python cụ thể được lưu trong `requirements.txt`.

---

## 5. Kiến trúc tổng thể

Ứng dụng sử dụng kiến trúc module, trong đó giao diện, route, thuật toán, model, service và kiểm thử được tách riêng.

```text
Người dùng
    |
    v
HTML / CSS / JavaScript
    |
    v
Flask Routes / API
    |
    v
Services
    |
    +--> Parser CFG
    +--> Chuyển CFG sang CNF
    +--> CNF Validator
    +--> Thuật toán CYK
    +--> Trace và Parse Tree
```

Trong T01, các module thuật toán mới được tạo vị trí trong kiến trúc, chưa chứa cài đặt thuật toán thật.

---

## 6. Cấu trúc repository

```text
cfg-cnf-cyk-visualizer/
├── .github/
│   └── workflows/
│       └── ci.yml
├── app/
│   ├── algorithms/
│   │   ├── cnf/
│   │   │   └── __init__.py
│   │   ├── cyk/
│   │   │   └── __init__.py
│   │   └── __init__.py
│   ├── models/
│   │   └── __init__.py
│   ├── services/
│   │   └── __init__.py
│   ├── static/
│   │   ├── css/
│   │   │   └── style.css
│   │   └── js/
│   │       └── app.js
│   ├── templates/
│   │   └── index.html
│   ├── __init__.py
│   └── routes.py
├── docs/
│   ├── contributions/
│   │   └── TV1/
│   │       └── T01-kien-truc-skeleton-docker.md
│   └── diagrams/
├── tests/
│   ├── __init__.py
│   └── test_app.py
├── .dockerignore
├── .env.example
├── .gitignore
├── Dockerfile
├── README.md
├── requirements.txt
└── run.py
```

### Ý nghĩa các thư mục chính

- `app/algorithms/cnf`: chứa các bước chuyển CFG sang CNF.
- `app/algorithms/cyk`: chứa thuật toán CYK và cấu trúc trace.
- `app/models`: chứa mô hình dữ liệu Grammar, Production và kết quả xử lý.
- `app/services`: điều phối parser, CNF, CYK và dữ liệu giao diện.
- `app/templates`: chứa template HTML.
- `app/static`: chứa CSS và JavaScript.
- `tests`: chứa các bộ kiểm thử tự động.
- `docs/contributions`: chứa tài liệu phần việc của từng thành viên.
- `.github/workflows`: chứa cấu hình GitHub Actions CI.

---

## 7. Module contract dự kiến

Để các thành viên có thể phát triển song song, các module cần trao đổi dữ liệu theo hợp đồng thống nhất.

### 7.1. Grammar

Mô hình Grammar dự kiến chứa:

- `variables`: tập biến.
- `terminals`: tập terminal.
- `productions`: tập production.
- `start_symbol`: ký hiệu bắt đầu.

### 7.2. Parser CFG

```text
Input:
    Văn bản CFG và ký hiệu bắt đầu

Output:
    Grammar hợp lệ hoặc danh sách lỗi theo dòng
```

### 7.3. Chuyển đổi CNF

```text
Input:
    Grammar hợp lệ

Output:
    Grammar ở dạng CNF và log từng bước chuyển đổi
```

### 7.4. Thuật toán CYK

```text
Input:
    Grammar CNF và chuỗi cần kiểm tra

Output:
    accepted, bảng CYK, trace và backpointer
```

### 7.5. Giao diện

Giao diện chỉ sử dụng dữ liệu trả về từ service; không cài thuật toán trực tiếp trong JavaScript.

---

## 8. Flask application skeleton

### 8.1. Application factory

Hàm `create_app()` trong `app/__init__.py` chịu trách nhiệm:

- Tạo Flask application.
- Nạp cấu hình mặc định.
- Cho phép test ghi đè cấu hình.
- Đăng ký Blueprint.

Application factory giúp mỗi test có thể tạo một ứng dụng độc lập và hỗ trợ mở rộng cấu hình theo môi trường.

### 8.2. Blueprint

`app/routes.py` định nghĩa `main_bp` để tách route khỏi phần khởi tạo ứng dụng.

Các endpoint của T01:

| Method | Endpoint | Chức năng |
|---|---|---|
| GET | `/` | Hiển thị giao diện chính |
| GET | `/health` | Trả về trạng thái cho CI và Docker |

Kết quả `/health`:

```json
{
  "service": "cfg-cnf-cyk-visualizer",
  "status": "healthy"
}
```

### 8.3. Giao diện skeleton

Giao diện hiện có:

- Form nhập CFG.
- Trường ký hiệu bắt đầu.
- Trường nhập chuỗi.
- Nút dùng dữ liệu ví dụ.
- Nút phân tích văn phạm.
- Khu vực hiển thị dữ liệu đầu vào.
- Trạng thái chờ dữ liệu.
- Responsive layout cơ bản.

Nút phân tích trong T01 mới minh họa luồng giao diện. Parser và CYK thật sẽ được tích hợp ở những task tiếp theo.

---

## 9. Quản lý cấu hình

File `.env.example` mô tả các biến môi trường:

```dotenv
PORT=5000
FLASK_DEBUG=0
```

- `PORT`: cổng ứng dụng, mặc định là 5000.
- `FLASK_DEBUG`: bật debug ở local khi bằng 1.

File `.env` thật bị loại khỏi Git bằng `.gitignore` để tránh đưa cấu hình riêng hoặc dữ liệu nhạy cảm lên repository.

---

## 10. Git workflow

Dự án sử dụng ba nhóm nhánh:

- `main`: phiên bản ổn định.
- `develop`: nhánh tích hợp.
- `feature/Txx-*`: nhánh thực hiện từng task.

Luồng làm việc:

```text
feature/Txx-* → Pull Request → develop → Pull Request → main
```

Nhánh của T01:

```text
feature/T01-kien-truc-skeleton-docker
```

### Quy ước commit

| Tiền tố | Ý nghĩa |
|---|---|
| `feat` | Thêm chức năng |
| `fix` | Sửa lỗi |
| `test` | Thêm hoặc sửa test |
| `docs` | Cập nhật tài liệu |
| `refactor` | Tái cấu trúc code |
| `chore` | Cấu hình và công việc hỗ trợ |

### Quy tắc bảo vệ nhánh

`main` và `develop` được bảo vệ bằng GitHub Rulesets:

- Không push trực tiếp.
- Không force push.
- Không xóa nhánh.
- Phải tạo Pull Request.
- Cần ít nhất một approval.
- Phải giải quyết conversation.
- Phải vượt qua CI checks.

---

## 11. Kiểm thử

File `tests/test_app.py` có bốn test:

| Test | Mục đích |
|---|---|
| `test_create_app` | Kiểm tra application factory |
| `test_home_page_returns_success` | Kiểm tra trang chính trả về 200 |
| `test_health_endpoint_returns_success` | Kiểm tra dữ liệu health endpoint |
| `test_unknown_page_returns_not_found` | Kiểm tra đường dẫn sai trả về 404 |

Lệnh chạy:

```powershell
python -m pytest -v
```

Kết quả local:

```text
4 passed in 0.21s
```

### Các trường hợp biên đã kiểm tra

- Tạo ứng dụng với cấu hình test.
- Truy cập trang chính.
- Kiểm tra chính xác JSON của health endpoint.
- Truy cập đường dẫn không tồn tại.

---

## 12. Docker

### 12.1. Mục tiêu

Docker giúp các thành viên chạy ứng dụng trong môi trường thống nhất, không phụ thuộc vào Python đã cài trên máy.

### 12.2. Thiết kế Dockerfile

Dockerfile thực hiện:

1. Sử dụng image `python:3.11-slim`.
2. Thiết lập biến môi trường Python và cổng 5000.
3. Cài dependencies từ `requirements.txt`.
4. Sao chép mã nguồn.
5. Tạo người dùng không phải root.
6. Khai báo cổng 5000.
7. Kiểm tra `/health` bằng Docker Healthcheck.
8. Chạy ứng dụng bằng `python run.py`.

### 12.3. Build image

```powershell
docker build -t cfg-cnf-cyk-visualizer:latest .
```

Kết quả đã kiểm tra:

- Docker build thành công.
- Image ID tại thời điểm kiểm thử: `2264a35d19b2`.
- Content size hiển thị: khoảng 51.3 MB.

### 12.4. Chạy container

```powershell
docker run -d --rm \
  -p 5000:5000 \
  --name cfg-cnf-cyk-app \
  cfg-cnf-cyk-visualizer:latest
```

Kết quả:

- Container chạy cổng 5000.
- `/health` trả về HTTP 200.
- Docker Healthcheck chuyển sang `healthy`.

---

## 13. GitHub Actions CI

Workflow `.github/workflows/ci.yml` chạy khi:

- Push lên `main`.
- Push lên `develop`.
- Push lên nhánh `feature/**`.
- Tạo Pull Request vào `main` hoặc `develop`.

CI có hai job:

### `test`

- Checkout mã nguồn.
- Cài Python 3.11.
- Cache pip.
- Cài dependencies.
- Chạy Pytest.

### `docker-build`

- Checkout mã nguồn.
- Build Docker image.
- Không push image lên registry.

Hai required checks dùng trong Rulesets:

```text
CI / test
CI / docker-build
```

---

## 14. Cách chạy dự án

### 14.1. Chạy local

```powershell
python -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt
python run.py
```

Truy cập:

```text
http://127.0.0.1:5000
```

### 14.2. Chạy test

```powershell
python -m pytest -v
```

### 14.3. Chạy Docker

```powershell
docker build -t cfg-cnf-cyk-visualizer:latest .
docker run --rm -p 5000:5000 cfg-cnf-cyk-visualizer:latest
```

---

## 15. Kết quả đạt được

- Repository GitHub đã được khởi tạo.
- Đã thiết lập `main`, `develop` và nhánh feature của T01.
- README mô tả toàn diện dự án.
- Cấu trúc module đã sẵn sàng cho các task thuật toán.
- Flask application skeleton chạy local thành công.
- Giao diện skeleton nhận và hiển thị dữ liệu mẫu.
- Health endpoint trả về đúng trạng thái.
- Bốn test Flask đều pass.
- Docker image build thành công.
- Container chạy cổng 5000 và có trạng thái healthy.
- GitHub Actions tự động chạy test và build Docker.
- Rulesets có thể dùng các CI jobs làm required checks.

---

## 16. Lỗi gặp phải và cách xử lý

### Docker Engine chưa chạy

**Hiện tượng:** Docker CLI có phiên bản nhưng không kết nối được `dockerDesktopLinuxEngine`.

**Cách xử lý:** Mở Docker Desktop, chờ Engine running rồi kiểm tra bằng `docker info`.

### Chạy container trước khi build image

**Hiện tượng:** Docker không tìm thấy `cfg-cnf-cyk-visualizer:latest`.

**Cách xử lý:** Chạy `docker build` trước, kiểm tra bằng `docker image ls`, sau đó mới `docker run`.

### Thư mục `.venv` xuất hiện trong Git

**Hiện tượng:** VS Code hiển thị hơn một nghìn file untracked.

**Cách xử lý:** Tạo `.gitignore` và thêm `.venv/` trước khi stage.

### Cài Flask bị hủy

**Hiện tượng:** `Operation cancelled by user` và `ModuleNotFoundError`.

**Cách xử lý:** Kích hoạt lại `.venv`, cài Flask và Pytest riêng, sau đó kiểm tra import.

---

## 17. Hạn chế hiện tại

- Giao diện mới là skeleton, chưa sử dụng dữ liệu thuật toán thật.
- Parser CFG chưa được cài đặt.
- Chuyển đổi CNF và CYK chưa được cài đặt.
- Docker hiện chạy Flask development server, phù hợp demo đồ án nhưng chưa phải cấu hình production.
- Test mới kiểm tra phần khung Flask, chưa kiểm thử thuật toán.
- Chưa triển khai ứng dụng lên máy chủ công khai.

---

## 18. Hướng phát triển

- Tích hợp parser CFG và diagnostics.
- Xây dựng mô hình dữ liệu Grammar.
- Cài đặt từng bước chuyển CFG sang CNF.
- Tích hợp CNF validator.
- Cài đặt và trực quan hóa CYK.
- Lưu backpointer và dựng parse tree.
- Bổ sung test thuật toán, test tích hợp và đo hiệu năng.
- Hoàn thiện giao diện dựa trên dữ liệu thật.
- Cân nhắc dùng production WSGI server khi triển khai.

---

## 19. Nội dung cần nắm khi bảo vệ

TV1 cần giải thích được:

1. Vì sao sử dụng application factory và Blueprint.
2. Vai trò của từng thư mục trong kiến trúc.
3. Hợp đồng input/output giữa parser, CNF, CYK và UI.
4. Sự khác nhau giữa `main`, `develop` và `feature`.
5. Quy trình Pull Request và Rulesets.
6. Cách `.gitignore` và `.dockerignore` hoạt động.
7. Các layer chính của Dockerfile.
8. Lý do không chạy container bằng root.
9. Cách Docker Healthcheck kiểm tra ứng dụng.
10. Cách GitHub Actions chạy Pytest và build Docker.
11. Ý nghĩa của từng test Flask.
12. Giới hạn của skeleton so với sản phẩm hoàn chỉnh.

---

## 20. Minh chứng cần bổ sung

Trước khi tổng hợp báo cáo, bổ sung ảnh hoặc liên kết:

- [ ] Cây thư mục dự án trong VS Code.
- [ ] Kết quả `4 passed` của Pytest.
- [ ] Giao diện skeleton trên trình duyệt.
- [ ] JSON trả về từ `/health`.
- [ ] Docker image build thành công.
- [ ] Container có trạng thái `healthy`.
- [ ] GitHub Actions có hai job màu xanh.
- [ ] Rulesets có hai required status checks.
- [ ] Link Pull Request T01 vào `develop`.

---

## 21. Kết luận

T01 đã tạo nền móng kỹ thuật cho toàn bộ dự án. Repository có cấu trúc rõ ràng, ứng dụng Flask chạy được ở local và Docker, test tự động hoạt động, CI kiểm tra code trên GitHub và quy trình nhánh hỗ trợ năm thành viên phát triển song song. Các task tiếp theo có thể tập trung vào parser, CNF, CYK và giao diện mà không cần thiết lập lại môi trường hoặc kiến trúc dự án.
