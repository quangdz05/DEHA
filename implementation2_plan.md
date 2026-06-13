# Chức năng đặt PT theo tháng với lịch cố định tự động tạo booking

## Mô tả

Người dùng (hội viên) chọn một gói PT, chọn huấn luyện viên, ngày bắt đầu, các thứ trong tuần muốn tập và khung giờ cố định. Hệ thống tự động tạo tất cả các buổi tập (booking) trong khoảng thời gian của gói, sau khi kiểm tra đầy đủ ràng buộc lịch của PT.

**Ví dụ**: Mua gói PT Standard (12 buổi/30 ngày), chọn PT Nguyễn Văn A, tập Thứ 2/4/6, giờ 18:00-19:00, bắt đầu 01/06/2026 → Hệ thống tự động tạo 12 booking confirmed.

> [!IMPORTANT]
> Dự án đang sử dụng kiến trúc DDD (Domain → Application → Infrastructure → Presentation) với REST API + Frontend HTML/JS riêng biệt. Tất cả code mới sẽ tuân thủ kiến trúc này, **không dùng Django Template Engine hay Django Forms** mà tiếp tục dùng **DRF APIView + Frontend JavaScript** giống như toàn bộ hệ thống hiện tại.

## Open Questions

> [!IMPORTANT]
> **Model `Booking` hiện tại** trong dự án gắn liền với `ClassSchedule` (lịch lớp tập nhóm). Booking PT 1-1 đang dùng model `TrainerBooking` riêng. Vì vậy, tôi sẽ tạo model **`PTBooking`** riêng cho các buổi tập PT theo tháng, tách biệt khỏi `Booking` (lớp tập nhóm) và `TrainerBooking` (đặt lịch 1-1 lẻ). Điều này đảm bảo không phá vỡ logic đã có.

> [!WARNING]
> **Model `TrainerMonthlyBooking` hiện tại** chỉ lưu metadata (start_date, end_date, months, sessions_per_week) nhưng **không tạo các buổi tập cụ thể**. Model mới `UserPTPackage` + `PTBooking` sẽ thay thế vai trò này với lịch cố định chi tiết. Model `TrainerMonthlyBooking` cũ sẽ được giữ nguyên để không ảnh hưởng dữ liệu cũ.

## Proposed Changes

### 1. Domain Layer - Constants & Exceptions

#### [MODIFY] [constants.py](file:///d:/DEHA/DEHA/gym_booking_backend/domain/constants.py)
Thêm các constants mới:
- `PTPackageStatus`: `active`, `inactive`
- `UserPTPackageStatus`: `active`, `expired`, `completed`, `cancelled`
- `PTBookingStatus`: `pending`, `confirmed`, `completed`, `cancelled`
- `WeekdayChoices`: 0-6 (Monday-Sunday)

#### [MODIFY] [exceptions.py](file:///d:/DEHA/DEHA/gym_booking_backend/domain/exceptions.py)
Thêm `PTBookingException(GymException)` cho lỗi nghiệp vụ PT.

---

### 2. Infrastructure Layer - Models, Admin, Repository

#### [MODIFY] [models.py](file:///d:/DEHA/DEHA/gym_booking_backend/infrastructure/models.py)
Thêm 4 models mới:

**PTPackage** - Gói PT mẫu:
| Trường | Kiểu | Mô tả |
|--------|------|-------|
| name | CharField(100) | Tên gói (unique) |
| duration_days | PositiveIntegerField | Thời hạn (ngày) |
| total_sessions | PositiveIntegerField | Tổng số buổi |
| price | DecimalField | Giá gói |
| description | TextField | Mô tả |
| is_active | BooleanField | Đang hoạt động? |
| created_at, updated_at | auto | Timestamps |

**TrainerSchedule** - Lịch làm việc của PT:
| Trường | Kiểu | Mô tả |
|--------|------|-------|
| trainer | ForeignKey(Trainer) | PT |
| weekday | IntegerField(0-6) | Thứ trong tuần |
| start_time | TimeField | Giờ bắt đầu ca |
| end_time | TimeField | Giờ kết thúc ca |
| is_available | BooleanField | Còn nhận lịch? |
| Constraint | unique_together | (trainer, weekday, start_time) |

**UserPTPackage** - Gói PT đã đăng ký:
| Trường | Kiểu | Mô tả |
|--------|------|-------|
| user | ForeignKey(User) | Hội viên |
| trainer | ForeignKey(Trainer) | PT phụ trách |
| package | ForeignKey(PTPackage) | Gói PT mẫu |
| start_date | DateField | Ngày bắt đầu |
| end_date | DateField | Ngày hết hạn |
| total_sessions | PositiveIntegerField | Tổng buổi |
| used_sessions | PositiveIntegerField | Đã tập |
| remaining_sessions | PositiveIntegerField | Còn lại |
| status | CharField | active/expired/completed/cancelled |
| selected_weekdays | CharField | "0,2,4" (JSON string lưu các thứ đã chọn) |
| start_time | TimeField | Giờ bắt đầu cố định |
| end_time | TimeField | Giờ kết thúc cố định |
| created_at, updated_at | auto | Timestamps |

**PTBooking** - Từng buổi tập cụ thể:
| Trường | Kiểu | Mô tả |
|--------|------|-------|
| user | ForeignKey(User) | Hội viên |
| trainer | ForeignKey(Trainer) | PT |
| user_pt_package | ForeignKey(UserPTPackage) | Gói PT đã mua |
| booking_code | CharField(30, unique) | Mã booking |
| booking_date | DateField | Ngày tập |
| start_time | TimeField | Giờ bắt đầu |
| end_time | TimeField | Giờ kết thúc |
| status | CharField | pending/confirmed/completed/cancelled |
| note | TextField | Ghi chú |
| created_at, updated_at | auto | Timestamps |

#### [MODIFY] [admin.py](file:///d:/DEHA/DEHA/gym_booking_backend/infrastructure/admin.py)
Đăng ký 4 models mới với `list_display`, `search_fields`, `list_filter` phù hợp.

#### [NEW] pt_repository.py
File: `infrastructure/repositories/pt_repository.py`
- `get_active_pt_packages()` - Lấy danh sách gói PT active
- `get_pt_package_by_id(id)` - Lấy gói PT theo ID
- `get_user_pt_packages(user)` - Lấy danh sách gói PT của user
- `get_user_pt_package_by_id(user, id)` - Lấy chi tiết gói PT của user
- `get_trainer_schedules(trainer)` - Lấy lịch làm việc của PT
- `has_pt_booking_conflict(trainer, date, start_time, end_time)` - Kiểm tra trùng lịch PT
- `create_user_pt_package(...)` - Tạo UserPTPackage
- `create_pt_booking(...)` - Tạo PTBooking
- `get_pt_bookings_by_package(user_pt_package)` - Lấy danh sách booking của gói

---

### 3. Application Layer - Service & Validator

#### [NEW] pt_booking_service.py
File: `application/services/pt_booking_service.py`

Hàm chính: `create_monthly_pt_bookings(user, package_id, trainer_id, start_date, selected_weekdays, start_time, end_time, note)`

Thuật toán:
```
1. Validate input cơ bản (ngày, giờ, weekdays)
2. Lấy PTPackage, kiểm tra is_active
3. Lấy Trainer, kiểm tra status active
4. Tính end_date = start_date + package.duration_days
5. Duyệt từ start_date → end_date:
   - Nếu weekday của ngày thuộc selected_weekdays → thêm vào candidate_dates
   - Dừng khi đủ package.total_sessions
6. Kiểm tra từng ngày trong candidate_dates:
   - PT có TrainerSchedule vào weekday đó không?
   - Khung giờ có nằm trong ca làm việc không?
   - Có trùng PTBooking/TrainerBooking/ClassSchedule không?
7. Thu thập tất cả lỗi, nếu có → raise với danh sách chi tiết
8. Nếu OK → transaction.atomic():
   - Tạo UserPTPackage (status=active)
   - Tạo N PTBooking (status=confirmed)
9. Return UserPTPackage + danh sách bookings
```

Các hàm phụ:
- `complete_pt_booking(booking_id)` - Đánh dấu buổi hoàn thành → `used_sessions++`, `remaining_sessions--`, nếu `remaining_sessions == 0` → `UserPTPackage.status = completed`
- `cancel_pt_booking(user, booking_id)` - Hủy 1 buổi cụ thể
- `cancel_user_pt_package(user, package_id)` - Hủy toàn bộ gói
- `expire_old_pt_packages()` - Command/cron: kiểm tra & đánh dấu expired
- `get_trainer_schedule_for_weekday(trainer, weekday)` - Lấy lịch PT cho 1 ngày cụ thể

---

### 4. Presentation Layer - API Endpoints, Serializers, URLs

#### [MODIFY] [serializers.py](file:///d:/DEHA/DEHA/gym_booking_backend/presentation/serializers.py)
Thêm:
- `PTPackageSerializer` - Serialize gói PT
- `TrainerScheduleSerializer` - Serialize lịch làm việc PT
- `UserPTPackageSerializer` - Serialize gói PT đã mua (kèm bookings nested)
- `PTBookingSerializer` - Serialize từng buổi tập

#### [MODIFY] [views.py](file:///d:/DEHA/DEHA/gym_booking_backend/presentation/views.py)
Thêm các APIView:

| View | Method | Mô tả |
|------|--------|-------|
| `PTPackageListAPIView` | GET | Danh sách gói PT |
| `TrainerScheduleListAPIView` | GET | Lịch làm việc của 1 PT |
| `MonthlyPTBookingCreateAPIView` | POST | Tạo gói PT theo tháng (core) |
| `MonthlyPTBookingPreviewAPIView` | POST | Preview danh sách ngày trước khi đặt |
| `UserPTPackageListAPIView` | GET | Danh sách gói PT của tôi |
| `UserPTPackageDetailAPIView` | GET | Chi tiết 1 gói PT (kèm bookings) |
| `UserPTPackageCancelAPIView` | POST | Hủy gói PT |
| `PTBookingCompleteAPIView` | POST | Đánh dấu buổi hoàn thành (trainer) |
| `PTBookingCancelAPIView` | POST | Hủy 1 buổi tập |
| `AdminTrainerScheduleManageAPIView` | GET/POST | Admin quản lý lịch PT |
| `AdminPTPackageManageAPIView` | POST | Admin tạo gói PT |

#### [MODIFY] [urls.py](file:///d:/DEHA/DEHA/gym_booking_backend/presentation/urls.py)
Thêm routes:
```python
# Gói PT
path("pt-packages/", ...)

# Lịch làm việc PT
path("trainers/<int:trainer_id>/schedules/", ...)

# Đặt PT theo tháng
path("pt-booking/monthly/create/", ...)
path("pt-booking/monthly/preview/", ...)

# Gói PT của tôi
path("my-pt-packages/", ...)
path("my-pt-packages/<int:pk>/", ...)
path("my-pt-packages/<int:pk>/cancel/", ...)

# Quản lý buổi tập
path("pt-bookings/<int:booking_id>/complete/", ...)
path("pt-bookings/<int:booking_id>/cancel/", ...)

# Admin
path("admin/trainer-schedules/", ...)
path("admin/pt-packages/create/", ...)
```

---

### 5. Frontend

#### [NEW] pt-packages.html
File: `gym_booking_frontend/pt-packages.html`
Trang hiển thị danh sách gói PT + form đặt PT theo tháng:
- Card hiển thị từng gói PT (tên, giá, số buổi, thời hạn)
- Form đặt PT:
  - Dropdown chọn gói PT
  - Dropdown chọn PT (load từ API `/trainers/`)
  - Date picker chọn ngày bắt đầu
  - Checkbox 7 thứ trong tuần (hiển thị lịch làm việc PT bên cạnh)
  - Input giờ bắt đầu / kết thúc
  - Textarea ghi chú
  - Nút "Xem trước lịch" → gọi preview API → hiển thị bảng ngày sẽ tạo
  - Nút "Xác nhận đặt lịch" → gọi create API

#### [NEW] my-pt-packages.html
File: `gym_booking_frontend/my-pt-packages.html`
Trang hiển thị danh sách gói PT đã mua + chi tiết từng gói:
- Bảng tổng hợp: Gói, PT, Ngày BĐ, Ngày KT, Số buổi (dùng/còn), Trạng thái, Hành động
- Khi click vào gói → hiển thị bảng chi tiết các buổi tập (STT, Ngày, Giờ, PT, Trạng thái)

#### [MODIFY] [app.js](file:///d:/DEHA/DEHA/gym_booking_frontend/assets/js/app.js)
Thêm các hàm JavaScript cho 2 trang mới

#### [MODIFY] [index.html](file:///d:/DEHA/DEHA/gym_booking_frontend/index.html)
Thêm link "Gói PT" vào navbar

#### Cập nhật navbar trên tất cả các trang HTML
Thêm menu item "Gói PT" (cho member), "Gói PT của tôi" (cho member đã login)

---

## Verification Plan

### Automated Tests
```bash
# Chạy migration
python manage.py makemigrations
python manage.py migrate

# Chạy server
python manage.py runserver
```

### Manual Verification
1. **Admin**: Tạo gói PT mẫu (PT Basic 8 buổi, PT Standard 12 buổi) qua Django Admin
2. **Admin**: Tạo TrainerSchedule cho PT (ví dụ: Thứ 2/4/6, 6:00-21:00)
3. **Member**: Truy cập trang Gói PT, chọn gói, chọn PT, chọn ngày/giờ/thứ → Preview → Xác nhận
4. **Kiểm tra**: 12 booking được tạo với ngày chính xác
5. **Kiểm tra trùng lịch**: Tạo gói PT thứ 2 cùng PT cùng khung giờ → Phải báo lỗi ngày trùng
6. **Kiểm tra hết buổi**: Đánh dấu 12 buổi completed → UserPTPackage status = completed
7. **Kiểm tra expired**: Tạo gói có end_date trong quá khứ → Status = expired
