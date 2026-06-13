# DEHA - Gym Booking System

## 1. Giới thiệu dự án

**DEHA - Gym Booking System** là hệ thống quản lý và đặt lịch tập gym, hỗ trợ người dùng xem thông tin lớp học, huấn luyện viên, đặt lịch tập và quản lý lịch đã đăng ký. Dự án được xây dựng với mục tiêu mô phỏng một hệ thống đặt lịch phòng gym đơn giản, dễ sử dụng và phù hợp với nhu cầu học tập, thực hành phát triển web.

Hệ thống gồm hai phần chính:

* **Backend**: Xử lý nghiệp vụ, quản lý dữ liệu, xác thực người dùng và cung cấp API.
* **Frontend**: Hiển thị giao diện người dùng, danh sách lớp học, lịch tập, thông tin huấn luyện viên và các chức năng tương tác.

---

## 2. Công nghệ sử dụng

### Backend

* Python
* Django
* Django ORM
* Django Forms
* Class-based Views
* SQLite / Database tùy cấu hình

### Frontend

* HTML5
* CSS3
* JavaScript
* Bootstrap / CSS tùy chỉnh

### Công cụ hỗ trợ

* Git / GitHub
* Visual Studio Code
* Python Virtual Environment

---

## 3. Chức năng chính

### Người dùng

* Đăng ký tài khoản
* Đăng nhập / đăng xuất
* Xem danh sách lớp tập
* Xem thông tin huấn luyện viên
* Đặt lịch tập
* Xem lịch tập đã đăng ký
* Hủy hoặc quản lý lịch đặt

### Huấn luyện viên

* Xem lịch dạy
* Quản lý thông tin cá nhân
* Theo dõi lớp học được phân công

### Quản trị viên

* Quản lý người dùng
* Quản lý lớp học
* Quản lý huấn luyện viên
* Quản lý lịch tập
* Quản lý gói tập / membership
* Theo dõi dữ liệu hệ thống

---

## 4. Cấu trúc thư mục

```bash
DEHA/
│
├── gym_booking_backend/
│   ├── migrations/
│   ├── presentation/
│   ├── infrastructure/
│   ├── management/
│   ├── tests.py
│   └── ...
│
├── gym_booking_frontend/
│   ├── assets/
│   ├── index.html
│   ├── classes.html
│   ├── trainers.html
│   ├── schedule.html
│   ├── my-bookings.html
│   └── ...
│
├── database_analysis_report.md
├── frontend_improvement_guide.md
├── functional_requirements.md
├── implementation_plan.md
├── role_based_features.md
└── README.md
```

---

## 5. Cài đặt và chạy dự án

### Bước 1: Clone repository

```bash
git clone https://github.com/quangdz05/DEHA.git
cd DEHA
```

### Bước 2: Tạo môi trường ảo

```bash
python -m venv venv
```

### Bước 3: Kích hoạt môi trường ảo

Trên Windows:

```bash
venv\Scripts\activate
```

Trên macOS / Linux:

```bash
source venv/bin/activate
```

### Bước 4: Cài đặt thư viện

```bash
pip install -r requirements.txt
```

Nếu chưa có file `requirements.txt`, có thể cài Django thủ công:

```bash
pip install django pillow
```

### Bước 5: Chạy migration

```bash
python manage.py makemigrations
python manage.py migrate
```

### Bước 6: Tạo tài khoản admin

```bash
python manage.py createsuperuser
```

### Bước 7: Chạy server

```bash
python manage.py runserver
```

Sau đó mở trình duyệt tại:

```bash
http://127.0.0.1:8000/
```

---

## 6. Tài khoản và phân quyền

Hệ thống có thể chia người dùng thành nhiều vai trò khác nhau:

| Vai trò | Mô tả                   |
| ------- | ----------------------- |
| User    | Người dùng đặt lịch tập |
| Trainer | Huấn luyện viên         |
| Admin   | Quản trị viên hệ thống  |

Mỗi vai trò có quyền truy cập và chức năng riêng nhằm đảm bảo hệ thống hoạt động rõ ràng, an toàn và dễ quản lý.

---

## 7. Đóng góp cá nhân

| Thành viên      | Vai trò   | Đóng góp                                                                                  |
| --------------- | --------- | ----------------------------------------------------------------------------------------- |
| Dương Văn Quang | Developer | Phân tích yêu cầu, thiết kế chức năng, xây dựng backend, frontend và xử lý logic đặt lịch |
| Contributor     | Developer | Hỗ trợ phát triển chức năng, sửa lỗi và kiểm thử hệ thống                                 |

---

## 8. Hướng dẫn đóng góp

Nếu muốn đóng góp vào dự án, hãy thực hiện các bước sau:

1. Fork repository
2. Tạo branch mới

```bash
git checkout -b feature/ten-chuc-nang
```

3. Thực hiện chỉnh sửa
4. Commit thay đổi

```bash
git add .
git commit -m "Add new feature"
```

5. Push branch lên GitHub

```bash
git push origin feature/ten-chuc-nang
```

6. Tạo Pull Request để xem xét và merge vào repository chính

---

## 9. Ghi chú khi sử dụng Git

Không nên đưa các file cache hoặc file môi trường lên GitHub. Nên thêm các dòng sau vào file `.gitignore`:

```gitignore
__pycache__/
*.pyc
*.pyo
*.pyd
venv/
.env
.vscode/
db.sqlite3
```

Nếu muốn lưu database mẫu lên GitHub, hãy xóa dòng:

```gitignore
db.sqlite3
```

---

## 10. Định hướng phát triển

Trong tương lai, hệ thống có thể được mở rộng thêm các chức năng:

* Thanh toán gói tập online
* Gửi email xác nhận lịch đặt
* Thông báo lịch tập cho người dùng
* Dashboard thống kê doanh thu
* Quản lý ca làm việc của huấn luyện viên
* API cho ứng dụng mobile
* Cải thiện giao diện responsive trên nhiều thiết bị

---

## 11. Tác giả

**Dương Văn Quang**

GitHub: [quangdz05](https://github.com/quangdz05)

---

## 12. License

Dự án được xây dựng phục vụ mục đích học tập và thực hành phát triển phần mềm.

