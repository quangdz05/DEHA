# Kế hoạch cải tiến thiết kế Cơ sở dữ liệu và sửa lỗi Concurrency (Race Condition)

Kế hoạch này nhằm thực hiện các sửa đổi nâng cấp cơ sở dữ liệu và logic nghiệp vụ dựa trên báo cáo phân tích [database_analysis_report.md](file:///d:/DEHA/ThemLichTap_GYM/database_analysis_report.md). Chúng ta sẽ tối ưu hóa cấu trúc database để đảm bảo tính linh hoạt, tính toàn vẹn và hiệu năng cho hệ thống Gym Booking, đồng thời giải quyết triệt để lỗi tranh chấp tài nguyên (race condition) khi đặt lịch lớp học.

## User Review Required

> [!IMPORTANT]
> **Các thay đổi tương thích ngược (Backward Compatibility):**
> 1. Để tránh phá vỡ các API hiện có và các đoạn kiểm thử (Tests), chúng ta sẽ giữ lại trường `trainer` trong `GymClass` làm "Huấn luyện viên mặc định". Đồng thời, thêm trường `trainer` vào `ClassSchedule`. Khi lưu `ClassSchedule`, nếu không truyền `trainer`, hệ thống sẽ tự động gán bằng `gym_class.trainer`.
> 2. Giữ trường `membership` (UserMembership) trong bảng `Payment` dưới dạng nullable, đồng thời thêm trường `invoice` để liên kết hóa đơn tổng. Việc này giúp các API thanh toán hiện tại không bị lỗi.

## Open Questions

Không có câu hỏi mở nào cần giải đáp khẩn cấp trước khi triển khai, do chúng tôi đã thiết kế giải pháp tương thích ngược hoàn hảo giúp bảo đảm các bộ test hiện tại chạy bình thường.

---

## Proposed Changes

Các thay đổi được chia theo các tầng tương ứng của dự án Django.

### 1. Tầng Domain (Constants & Exceptions)

#### [MODIFY] [constants.py](file:///d:/DEHA/ThemLichTap_GYM/gym_booking_backend/domain/constants.py)
- Thêm trạng thái `WAITLIST` vào `BookingStatus`.
- Thêm trạng thái `UNPAID`, `PAID`, `CANCELLED` cho `InvoiceStatus` (nếu cần thiết hoặc định nghĩa trực tiếp trong model/constants).

### 2. Tầng Infrastructure (Models & Migrations)

#### [MODIFY] [models.py](file:///d:/DEHA/ThemLichTap_GYM/gym_booking_backend/infrastructure/models.py)
- **`Profile`**: Thêm `emergency_contact_name`, `emergency_contact_phone`, `health_notes`, `fitness_goals`.
- **`Trainer`**: Thêm `certifications` (TextField).
- **`Room`**: Thêm `amenities` (TextField).
- **`Category`**: Đổi kế thừa từ `models.Model` sang `TimestampedModel`.
- **`ClassSchedule`**: 
  - Thêm `trainer` (ForeignKey đến `Trainer`, nullable, blank=True).
  - Override hàm `save()` để tự động điền `trainer` từ `gym_class.trainer` nếu không được cung cấp.
- **`Booking`**:
  - Thêm `updated_at` (DateTimeField, auto_now=True).
  - Thêm `cancellation_reason` (TextField, blank=True).
  - Cập nhật trạng thái `status` hỗ trợ `WAITLIST`.
  - Thêm ràng buộc UniqueConstraint trên cặp `(user, schedule)` với điều kiện chỉ áp dụng cho booking hoạt động (PENDING, CONFIRMED).
- **`MembershipPackage`**:
  - Thêm `is_freezable` (BooleanField, default=True).
  - Thêm `max_freeze_days` (PositiveIntegerField, default=30).
  - Thêm `allowed_categories` (ManyToManyField đến `Category`, blank=True).
- **`UserMembership`**:
  - Thêm `updated_at` (DateTimeField, auto_now=True).
- **[NEW] `MembershipFreeze`**: Thêm model mới để quản lý lịch sử tạm dừng gói tập.
- **[NEW] `Invoice` và `InvoiceItem`**: Thêm các model để quản lý hóa đơn, hỗ trợ tách rời Payment khỏi gói tập.
- **`Payment`**:
  - Thêm `invoice` (ForeignKey đến `Invoice`, null=True, blank=True).
  - Thêm `updated_at` (DateTimeField, auto_now=True).
  - Thêm `payment_gateway_response` (JSONField, null=True, blank=True).
  - Cho phép `membership` chuyển thành `null=True, blank=True`.
- **`Review`**:
  - Thêm `booking` (ForeignKey đến `Booking`, null=True, blank=True).
  - Thêm ràng buộc logic để đảm bảo ít nhất `trainer` hoặc `gym_class` được gán giá trị.

### 3. Tầng Infrastructure Repositories (Database Queries)

#### [MODIFY] [schedule_repository.py](file:///d:/DEHA/ThemLichTap_GYM/gym_booking_backend/infrastructure/repositories/schedule_repository.py)
- Cập nhật hàm `get_schedule_by_id`, `get_available_schedules` và các hàm query khác để `select_related('trainer')` thay vì đi qua `gym_class__trainer`.
- Cập nhật `get_schedules_by_trainer` để lọc trực tiếp trên trường `trainer_id` của `ClassSchedule`.

#### [MODIFY] [booking_repository.py](file:///d:/DEHA/ThemLichTap_GYM/gym_booking_backend/infrastructure/repositories/booking_repository.py)
- Cập nhật `get_booking_by_id` và các hàm query liên quan để tải các trường mới và tương thích với thay đổi cấu trúc lịch học.

### 4. Tầng Application (Services & Validators)

#### [MODIFY] [booking_service.py](file:///d:/DEHA/ThemLichTap_GYM/gym_booking_backend/application/services/booking_service.py)
- Sử dụng `.select_for_update()` khi truy vấn `ClassSchedule` trong transaction của `create_booking` để ngăn chặn hoàn toàn Race Condition.

#### [MODIFY] [booking_validator.py](file:///d:/DEHA/ThemLichTap_GYM/gym_booking_backend/application/validators/booking_validator.py)
- Kiểm tra tính tương thích của gói thành viên với lớp học đăng ký (nếu gói thành viên có cấu hình `allowed_categories`).

### 5. Tầng Presentation (REST API Serializers & Views)

#### [MODIFY] [serializers.py](file:///d:/DEHA/ThemLichTap_GYM/gym_booking_backend/presentation/serializers.py)
- Cập nhật `ClassScheduleSerializer` để lấy `trainer_name` từ `trainer.name` của Schedule thay vì `gym_class.trainer.name`.
- Thêm serializer cho các thực thể mới (`Invoice`, `InvoiceItem`, `MembershipFreeze`) để chuẩn bị cho API mở rộng.

#### [MODIFY] [views.py](file:///d:/DEHA/ThemLichTap_GYM/gym_booking_backend/presentation/views.py)
- Cập nhật các API truy vấn lịch của huấn luyện viên để lọc trực tiếp theo `ClassSchedule.trainer`.

---

## Verification Plan

### Automated Tests
Chúng ta sẽ chạy bộ test của Django để kiểm tra xem các sửa đổi có làm hỏng tính năng hiện tại không:
```bash
python manage.py test
```
Chúng ta cũng sẽ viết bổ sung các test cases sau trong `tests.py`:
1. Test đặt lịch đồng thời (Race Condition) bằng luồng giả lập hoặc kiểm tra hoạt động lock thông qua Unit Test.
2. Test tính năng tự động điền Trainer mặc định của lớp học vào Schedule khi tạo mới lịch tập.
3. Test ràng buộc duy nhất (UniqueConstraint) đối với các booking hoạt động.

### Manual Verification
- Sử dụng Django Admin dashboard tại `/admin` để tạo phòng tập, danh mục lớp học, lịch tập và kiểm tra giao diện nhập liệu của các trường mới.
