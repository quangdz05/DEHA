# HỆ THỐNG QUẢN LÝ ĐẶT LỊCH PHÒNG TẬP - GYM BOOKING SYSTEM

Chào mừng bạn đến với **Gym Booking System**, giải pháp công nghệ toàn diện phục vụ quản trị phòng tập, đăng ký thẻ thành viên, xếp lịch lớp học, đăng ký PT 1-1 và chăm sóc khách hàng tự động với trợ lý AI Chatbot. Hệ thống được thiết kế theo mô hình tách biệt rõ ràng giữa Backend (API) và Frontend (Single/Multi-page Application) cùng hệ thống bảo mật cao cấp (JWT, 2FA, Rate Limiting).

---

## 🗺️ Bản đồ Chức năng Hệ thống (Functional Map)

Hệ thống được chia thành 7 phân hệ cốt lõi với sự phân quyền chặt chẽ giữa 3 đối tượng người dùng: **Hội viên (Member)**, **Huấn luyện viên (Trainer)**, và **Quản trị viên (Admin)**.

### 1. Quản lý Tài khoản & Bảo mật (Auth & Security)
- **Đăng ký/Đăng nhập phân quyền**: Tự động phân vai trò dựa vào thực thể `Profile` kết hợp Django Auth.
- **Xác thực 2 lớp (2FA - TOTP)**: Bảo vệ tài khoản thông qua mã OTP 6 số từ các ứng dụng như Google Authenticator / Microsoft Authenticator (quét mã QR động).
- **Khôi phục mật khẩu**: Gửi email chứa liên kết đặt lại mật khẩu sử dụng mã hóa token bảo mật cao.
- **Phòng chống Brute-Force**: Giới hạn tần suất đăng nhập (Rate Limiting) tối đa 5 lần/phút.

### 2. Quản lý Hồ sơ Hội viên (Member Profiles)
- **Thông tin sức khỏe**: Hội viên tự khai báo bệnh lý nền, chấn thương (`health_notes`) và mục tiêu thể hình (`fitness_goals`).
- **An toàn tập luyện**: Huấn luyện viên có thể xem thông tin sức khỏe và thông tin liên hệ khẩn cấp (`emergency_contact`) của học viên trong lớp để phòng ngừa rủi ro chấn thương.

### 3. Tra cứu & Đăng ký Lớp học (Gym Catalog & Class Booking)
- **Danh mục trực quan**: Tra cứu danh sách lớp học (mức độ khó, thời lượng, tiện ích phòng tập) và danh sách HLV (kinh nghiệm, chứng chỉ).
- **Hàng đợi chờ (Waitlist)**: Tự động xếp học viên vào danh sách chờ khi lớp học đạt sức chứa tối đa (`max_participants`).
- **Tự động đôn hàng chờ**: Khi có học viên hủy lịch tập (yêu cầu nhập `cancellation_reason`), hệ thống tự động đẩy học viên đứng đầu danh sách chờ vào danh sách chính thức (`Confirmed`).
- **Điểm danh (Attendance)**: HLV điểm danh học viên tại lớp, đánh dấu trạng thái tham gia thực tế (`COMPLETED` hoặc `NO_SHOW`).

### 4. Đặt lịch Huấn luyện viên cá nhân 1-1 (PT Monthly Booking)
- **Xếp lịch tự động**: Hội viên lựa chọn gói tập PT, huấn luyện viên và các ngày muốn tập trong tuần (ví dụ: Thứ 2, Thứ 4, Thứ 6).
- **Kiểm tra xung đột (Overlap Detection)**: Hệ thống tự động kiểm tra lịch trống của HLV để sinh ra chuỗi các buổi tập 1-1 khớp hoàn toàn, ngăn ngừa việc trùng lịch.
- **Quản lý buổi tập**: Hệ thống tự động trừ số buổi tập khả dụng khi buổi tập hoàn thành.

### 5. Quản lý Gói tập & Đóng băng thẻ (Membership & Freeze)
- **Mua gói thành viên**: Đăng ký các gói tập theo ngày/tháng/năm.
- **Ràng buộc danh mục**: Kiểm tra điều kiện mua gói: chỉ cho phép đặt các lớp học thuộc danh mục được cấu hình trong gói tập.
- **Tạm dừng thẻ tập (Freeze)**: Cho phép học viên gửi yêu cầu đóng băng thẻ tập trong một thời gian, hệ thống phê duyệt sẽ tự động cộng thêm số ngày tương ứng vào ngày hết hạn (`end_date`).

### 6. Hóa đơn & Thanh toán (Billing & Payment Gateway)
- **Hóa đơn chi tiết (`Invoice` / `InvoiceItem`)**: Tự động sinh hóa đơn khi phát sinh giao dịch mua gói hoặc dịch vụ.
- **Thanh toán trực tuyến**: Tích hợp thanh toán giả lập qua các cổng MoMo, VNPay, chuyển khoản ngân hàng, lưu vết chi tiết phản hồi thô (`payment_gateway_response`) để phục vụ đối soát.

### 7. Trợ lý ảo AI Chatbot
- **Hỗ trợ thời gian thực**: Trợ lý AI tích hợp trực tiếp giúp hội viên tra cứu lịch tập, kiểm tra thông tin gói thành viên và hỗ trợ đặt lịch nhanh chóng qua ngôn ngữ tự nhiên.

---

## 💻 Công nghệ Sử dụng (Tech Stack)

### Frontend (Giao diện Người dùng)
- **Cấu trúc & Logic**: HTML5, Vanilla JavaScript.
- **Phong cách Thiết kế**: CSS3 thuần với thiết kế giao diện Glassmorphism hiện đại, sử dụng bảng màu HSL mượt mà, chuyển động micro-animations sinh động, responsive hoàn toàn trên các thiết bị.
- **Thư viện Hỗ trợ**: Bootstrap 5.3.3, Google Fonts (Inter, Outfit), Bootstrap Icons.
- **Cơ chế Xác thực**:
  - Access Token (hạn ngắn): Lưu trong bộ nhớ tạm (JS Memory / State) của ứng dụng để tránh tấn công XSS.
  - Refresh Token (hạn dài): Lưu trong HttpOnly Cookie với cờ `SameSite=Strict` và giới hạn đường dẫn truy cập `/api/auth/refresh/` giúp loại bỏ hoàn toàn lỗ hổng CSRF.
  - Cơ chế tự động làm mới access token (Interceptor) khi nhận mã phản hồi HTTP 401.

### Backend (Hệ thống API)
- **Framework**: Django 6.0 & Django REST Framework (DRF).
- **Thư viện Xác thực & OTP**: `djangorestframework-simplejwt` (JWT Tokens) và `pyotp` (TOTP 2FA).
- **Hệ quản trị Cơ sở dữ liệu**: SQLite (trong môi trường phát triển).
- **Công cụ kiểm thử**: Django Test Framework (APITestCase) giúp tự động hóa kiểm thử tất cả các luồng nghiệp vụ.

---

## 📁 Cấu trúc Thư mục Dự án (Directory Structure)

```text
DEHA/
│
├── gym_booking_frontend/          # Mã nguồn giao diện (Frontend)
│   ├── assets/
│   │   ├── css/
│   │   │   └── app.css            # Hệ thống CSS Design System & Layout
│   │   └── js/
│   │       ├── api.js             # Core API Fetch & Interceptor tự động refresh token
│   │       ├── app.js             # Logic ứng dụng: Booking, Reviews, 2FA, Ngôn ngữ
│   │       ├── admin.js           # Logic Dashboard Admin
│   │       └── trainer.js         # Logic Dashboard Huấn luyện viên
│   │
│   ├── index.html                 # Trang chủ giới thiệu
│   ├── login.html                 # Trang đăng nhập hỗ trợ 2FA
│   ├── register.html              # Trang đăng ký thành viên
│   ├── classes.html               # Danh mục lớp tập
│   ├── trainers.html              # Danh sách huấn luyện viên
│   ├── schedules.html             # Lịch học và đặt chỗ
│   ├── my-bookings.html           # Lịch tập cá nhân, đánh giá & cài đặt 2FA
│   ├── forgot-password.html       # Giao diện yêu cầu khôi phục mật khẩu
│   ├── reset-password.html        # Giao diện đặt lại mật khẩu mới
│   ├── admin-dashboard.html       # Bảng điều khiển quản trị viên
│   └── trainer-dashboard.html     # Bảng điều khiển huấn luyện viên
│
└── gym_booking_backend/           # Mã nguồn máy chủ API (Backend)
    ├── config/                    # Cấu hình dự án Django (settings.py, urls.py)
    │
    ├── domain/                    # Tầng nghiệp vụ cốt lõi (Business Domain)
    │   ├── constants.py           # Định nghĩa các Trạng thái & Quyền hạn người dùng
    │   └── exceptions.py          # Lớp ngoại lệ nghiệp vụ tùy chỉnh
    │
    ├── application/               # Tầng dịch vụ ứng dụng (Use Cases)
    │   └── services/              # Xử lý logic nghiệp vụ Booking, PT Scheduling...
    │
    ├── infrastructure/            # Tầng hạ tầng & Cơ sở dữ liệu
    │   ├── models.py              # Định nghĩa các thực thể (Profile, Booking, PTBooking...)
    │   └── migrations/            # Lịch sử thay đổi cấu trúc dữ liệu
    │
    ├── presentation/              # Tầng giao tiếp (API Views & Routes)
    │   ├── views.py               # Các API View cơ bản (Profile, Class, Invoice...)
    │   ├── jwt_views.py           # API Login, Refresh, Logout bằng JWT
    │   ├── two_factor_views.py    # API đăng ký, xác minh, bật/tắt 2FA
    │   ├── password_reset_views.py# API gửi link & đổi mật khẩu
    │   └── chatbot.py             # API tích hợp Trợ lý AI Chatbot
    │
    ├── tests.py                   # Bộ unit test tự động (19 test cases)
    └── manage.py                  # Công cụ quản trị Django
```

---

## 🛠️ Hướng dẫn Khởi chạy & Kiểm thử (Setup & Validation Guide)

### 1. Khởi chạy Backend (Django API)

1. Mở terminal tại thư mục dự án và di chuyển vào thư mục backend:
   ```bash
   cd gym_booking_backend
   ```

2. Kích hoạt môi trường ảo (Virtual Environment):
   ```bash
   # Trên Windows (PowerShell)
   venv\Scripts\Activate.ps1
   
   # Trên macOS/Linux
   source venv/bin/activate
   ```

3. Thực hiện cập nhật cấu trúc dữ liệu (Migrations) nếu cần:
   ```bash
   python manage.py migrate
   ```

4. Khởi chạy máy chủ API:
   ```bash
   python manage.py runserver 127.0.0.1:8000
   ```
   *Lưu ý: API sẽ chạy tại địa chỉ `http://127.0.0.1:8000/api/`*

### 2. Khởi chạy Frontend

Sử dụng bất kỳ máy chủ HTTP tĩnh nào để khởi chạy mã nguồn Frontend. Ví dụ:
- **Live Server (VS Code Extension)**: Click chuột phải vào `index.html` và chọn `Open with Live Server`. Theo cấu hình CORS mặc định, hãy chạy frontend trên cổng **`5500`** hoặc **`5501`** (ví dụ: `http://127.0.0.1:5500/`).

### 3. Chạy Unit Test kiểm thử hệ thống

Bộ unit test chứa **19 test cases** tự động kiểm tra toàn bộ luồng đăng ký thẻ thành viên, xếp lịch phòng tập trùng lặp, thanh toán hóa đơn, đặt lịch PT và các luồng bảo mật (JWT, Rate limiting, 2FA, Reset password).

Để thực hiện chạy test, chạy lệnh sau:
```bash
python manage.py test
```

Kết quả mong đợi:
```text
Creating test database for alias 'default'...
...................
----------------------------------------------------------------------
Ran 19 tests in 137.282s

OK
Destroying test database for alias 'default'...
Found 19 test(s).
System check identified no issues (0 silenced).
```

---

## 🛡️ Điểm nhấn Bảo mật của Hệ thống (Security Highlights)

1. **Chống tấn công CSRF (Cross-Site Request Forgery):**
   - Loại bỏ hoàn toàn cơ chế session cookie truyền thống.
   - Refresh Token được lưu trong `HttpOnly Cookie` với cờ `SameSite=Strict`, chặn mọi đoạn mã độc hại truy cập hoặc tự động gửi yêu cầu từ trang web thứ ba.

2. **Chống tấn công XSS (Cross-Site Scripting):**
   - Access Token được lưu trong bộ nhớ tạm (JS State) của trình duyệt. Không lưu ở `localStorage` hay `sessionStorage`, do đó các mã script độc hại (nếu lọt qua) cũng không thể đọc trộm được token này.

3. **Chống tấn công brute-force dò mật khẩu:**
   - Cấu hình rate limit thông qua `ScopedRateThrottle` của DRF cho đầu API đăng nhập: Giới hạn tối đa **5 yêu cầu mỗi phút**. Nếu vượt quá sẽ bị khóa tạm thời và trả về lỗi HTTP 429 Too Many Requests.
