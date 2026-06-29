# 🔍 Phân Tích Lỗi Logic — Gym Booking System

> **Thực hiện bởi:** Software Engineer Review  
> **Ngày:** 2026-06-29  
> **Phạm vi:** Backend Django (Clean Architecture) + Frontend HTML/JS

---

## Tổng Quan Kiến Trúc

Dự án theo mô hình **Clean Architecture**:
- `domain/` — Constants, Entities, Exceptions
- `application/` — Use Cases, Services, Validators, Interfaces
- `infrastructure/` — Models, Repositories
- `presentation/` — Views (API), Serializers

---

## 🐛 DANH SÁCH LỖI LOGIC ĐÃ PHÁT HIỆN

---

### BUG #1 — `BookingRepository`: Các hàm stub trả về giá trị rỗng [SEVERITY: CRITICAL]

**File:** [`booking_repository.py`](file:///d:/DEHA/DEHA/gym_booking_backend/infrastructure/repositories/booking_repository.py)

**Mô tả:**  
Các phương thức sau bị **stub hoàn toàn** — không có logic thực, luôn trả về `None` hoặc `False`:

```python
def get_booking_by_id(self, booking_id):
    return None  # ← LUÔN LUÔN None!

def get_next_waitlisted_booking(self, schedule_id, select_for_update=False):
    return None  # ← Không bao giờ lấy được waitlist

def get_user_bookings(self, user):
    return TrainerBooking.objects.none()  # ← Luôn trả về queryset rỗng

def has_duplicate_booking(self, user, schedule):
    return False  # ← Không bao giờ phát hiện duplicate

def has_overlapping_booking(self, user, schedule):
    return False  # ← Không bao giờ phát hiện overlap

def create_booking(self, user, schedule, booking_code, note="", status=None):
    return None  # ← Không tạo được booking class!

def has_completed_booking_for_trainer(self, user, trainer_id):
    return False  # ← Review trainer luôn bị chặn

def has_completed_booking_for_class(self, user, gym_class_id):
    return False  # ← Review class luôn bị chặn

def count_user_bookings_in_week(self, user, start_dt, end_dt):
    class_count = 0  # ← Không đếm class bookings, chỉ tính trainer bookings
    ...
```

**Hậu quả:**
- `create_booking` → Luôn trả về `None`, response API bị lỗi 500 hoặc dữ liệu rỗng
- `cancel_booking` → Waitlist promotion hoàn toàn bị bỏ qua
- `validate_user_not_duplicate_booking` & `validate_user_not_overlap_booking` → Không hoạt động, user có thể book trùng
- `has_completed_booking_for_trainer` → `create_review` luôn trả về lỗi "You can only review a trainer if you have completed a class" — review không bao giờ tạo được!
- `count_user_bookings_in_week` → Weekly booking limit chỉ tính TrainerBooking, không tính ClassBooking

**Fix:**  
Implement đầy đủ tất cả các phương thức stub với query thực tế:
```python
def get_booking_by_id(self, booking_id):
    from gym_booking_backend.infrastructure.models import Booking
    return Booking.objects.filter(id=booking_id).first()

def has_duplicate_booking(self, user, schedule):
    from gym_booking_backend.infrastructure.models import Booking
    return Booking.objects.filter(
        user=user, schedule=schedule,
        status__in=[BookingStatus.PENDING, BookingStatus.CONFIRMED, BookingStatus.WAITLIST]
    ).exists()
# ... v.v.
```

---

### BUG #2 — Model `MembershipPackage` tham chiếu `allowed_categories` không tồn tại [SEVERITY: CRITICAL]

**File:** [`booking_validator.py`](file:///d:/DEHA/DEHA/gym_booking_backend/application/validators/booking_validator.py) (line 100)  
**File:** [`models.py`](file:///d:/DEHA/DEHA/gym_booking_backend/infrastructure/models.py) — `MembershipPackage` (line 213-227)

**Mô tả:**
```python
# booking_validator.py line 100
if package.allowed_categories.exists():  # ← AttributeError!
```

Model `MembershipPackage` **không có field `allowed_categories`** nào trong định nghĩa. Field này chưa được thêm vào model nhưng đã được gọi trong validator.

```python
# MembershipPackage model — không có allowed_categories!
class MembershipPackage(SoftDeleteModel):
    name = models.CharField(...)
    price = models.DecimalField(...)
    duration_days = models.PositiveIntegerField()
    max_bookings_per_week = ...
    is_freezable = ...
    max_freeze_days = ...
    status = ...
    # THIẾU: allowed_categories = models.ManyToManyField(...)
```

Đồng thời trong `serializers.py` (line 199) cũng có:
```python
fields = (..., "allowed_categories", ...)  # ← Field không tồn tại trong model!
```

**Hậu quả:** `AttributeError` khi bất kỳ user nào cố đặt lịch class → toàn bộ tính năng booking class bị sập.

**Fix:** Thêm field `allowed_categories` vào `MembershipPackage`:
```python
allowed_categories = models.ManyToManyField(
    'ClassCategory', blank=True, related_name='allowed_packages'
)
```

---

### BUG #3 — `views.py`: `BookingSerializer` chưa được import [SEVERITY: HIGH]

**File:** [`views.py`](file:///d:/DEHA/DEHA/gym_booking_backend/presentation/views.py) (line 600)

```python
class TrainerBookingAttendanceAPIView(BaseAPIView):
    ...
    return self.handle_result(Result.success_result(booking), BookingSerializer)  
    # ← BookingSerializer không được import!
```

`BookingSerializer` không xuất hiện trong danh sách import ở đầu file và không tồn tại trong `serializers.py`. 

**Hậu quả:** `NameError: name 'BookingSerializer' is not defined` → API attendance bị crash.

**Fix:**  
Tạo `BookingSerializer` trong `serializers.py` và import vào `views.py`.

---

### BUG #4 — `payment_service.confirm_payment`: Reset membership dates mỗi lần confirm [SEVERITY: HIGH]

**File:** [`payment_service.py`](file:///d:/DEHA/DEHA/gym_booking_backend/application/services/payment_service.py) (lines 70-76)

```python
if payment.membership:
    membership = payment.membership
    membership.status = MembershipStatus.ACTIVE
    membership.start_date = timezone.localdate()       # ← Luôn reset về hôm nay!
    membership.end_date = membership.start_date + timedelta(days=membership.package.duration_days)
    membership.save(...)
```

**Vấn đề:** Nếu admin confirm payment cho một membership đã active (ví dụ confirm lại sau khi hệ thống lỗi), `start_date` sẽ bị reset về ngày hôm nay, không phải ngày user đăng ký ban đầu.

**Fix:** Chỉ set `start_date` khi membership đang ở trạng thái `PENDING`:
```python
if payment.membership and payment.membership.status == MembershipStatus.PENDING:
    membership = payment.membership
    membership.status = MembershipStatus.ACTIVE
    if not membership.start_date:  # Chỉ set nếu chưa có
        membership.start_date = timezone.localdate()
    membership.end_date = membership.start_date + timedelta(...)
    membership.save(...)
```

---

### BUG #5 — `booking_service.cancel_booking`: Waitlist promotion thiếu `updated_at` [SEVERITY: MEDIUM]

**File:** [`booking_service.py`](file:///d:/DEHA/DEHA/gym_booking_backend/application/services/booking_service.py) (lines 97-99)

```python
if next_waitlist:
    next_waitlist.status = BookingStatus.PENDING
    next_waitlist.save(update_fields=["status"])  # ← Thiếu "updated_at"!
```

**Vấn đề:** `TimestampedModel` có `updated_at = auto_now=True` nhưng khi dùng `update_fields`, Django không tự động cập nhật `updated_at`. Trường này sẽ không được update.

**Fix:**
```python
next_waitlist.save(update_fields=["status", "updated_at"])
```

---

### BUG #6 — `pt_booking_service.complete_pt_booking`: Race condition với `remaining_sessions` [SEVERITY: MEDIUM]

**File:** [`pt_booking_service.py`](file:///d:/DEHA/DEHA/gym_booking_backend/application/services/pt_booking_service.py) (lines 308-313)

```python
user_package.used_sessions += 1
if user_package.remaining_sessions == 0:   # ← Dùng property (tính toán sau khi +=)
    user_package.status = UserPTPackageStatus.COMPLETED
user_package.save(update_fields=["used_sessions", "status"])
```

`remaining_sessions` là `@property = max(total - used, 0)`. Sau khi `used_sessions += 1`, `remaining_sessions` được tính **trên object trong memory** — đây là đúng, nhưng nguy hiểm nếu có concurrent requests. Nếu 2 request confirm cùng 1 lúc, cả 2 đọc `used_sessions = N`, cả 2 tăng lên `N+1`, kết quả chỉ tăng 1 thay vì 2.

**Fix:** Dùng `F()` expression để tăng atomic:
```python
from django.db.models import F
user_package.used_sessions = F('used_sessions') + 1
user_package.save(update_fields=["used_sessions"])
user_package.refresh_from_db()  # Lấy giá trị thực tế
if user_package.remaining_sessions == 0:
    user_package.status = UserPTPackageStatus.COMPLETED
    user_package.save(update_fields=["status"])
```

---

### BUG #7 — `membership_service.freeze_membership`: Không kiểm tra freeze overlap [SEVERITY: MEDIUM]

**File:** [`membership_service.py`](file:///d:/DEHA/DEHA/gym_booking_backend/application/services/membership_service.py) (lines 118-130)

```python
existing_freeze_days = sum(f.duration_days for f in membership.freezes.all())
if existing_freeze_days + duration_days > package.max_freeze_days:
    return Result.failure_result(...)
```

Chỉ kiểm tra **tổng số ngày freeze**, nhưng **không kiểm tra xem có 2 freeze trùng ngày nhau không**.  
User có thể tạo 2 freeze records với cùng khoảng ngày (ví dụ 01/07-15/07 và 05/07-20/07). Hệ thống sẽ extend end_date của membership gấp đôi mà không báo lỗi.

**Fix:** Thêm kiểm tra overlap giữa các freeze:
```python
overlapping = membership.freezes.filter(
    start_date__lt=end_date, end_date__gt=start_date
).exists()
if overlapping:
    return Result.failure_result("Khoảng freeze này trùng với freeze đã tạo.", status_code=400)
```

---

### BUG #8 — `review_service.create_review`: `has_completed_booking_for_trainer` luôn `False` → Review bị chặn vĩnh viễn [SEVERITY: HIGH]

**File:** [`booking_repository.py`](file:///d:/DEHA/DEHA/gym_booking_backend/infrastructure/repositories/booking_repository.py) (line 91-95)

```python
def has_completed_booking_for_trainer(self, user, trainer_id):
    return False  # ← Stub!

def has_completed_booking_for_class(self, user, gym_class_id):
    return False  # ← Stub!
```

Liên quan đến BUG #1. Người dùng **không bao giờ** có thể tạo review cho trainer hoặc class vì hàm kiểm tra luôn trả về `False`.

**Fix:**
```python
def has_completed_booking_for_trainer(self, user, trainer_id):
    return TrainerBooking.objects.filter(
        user=user, trainer_id=trainer_id, status=BookingStatus.COMPLETED
    ).exists() or PTBooking.objects.filter(
        user=user, trainer_id=trainer_id, status=PTBookingStatus.COMPLETED
    ).exists()
```

---

### BUG #9 — `AdminPackageDetailAPIView.delete`: Hard delete thay vì Soft delete [SEVERITY: MEDIUM]

**File:** [`views.py`](file:///d:/DEHA/DEHA/gym_booking_backend/presentation/views.py) (line 830)

```python
package.delete()  # ← Hard delete! Mất dữ liệu lịch sử
```

`MembershipPackage` kế thừa `SoftDeleteModel` với phương thức `soft_delete()`. Nhưng admin API đang dùng `.delete()` thông thường → **xóa vĩnh viễn** khỏi DB và phá vỡ các `UserMembership` liên kết (dù có `on_delete=PROTECT`, nếu không có membership nào thì xóa được và mất data history).

**Fix:**
```python
package.soft_delete()  # Dùng soft delete
return self.handle_result(Result.success_result({"message": "Package đã bị vô hiệu hóa."}))
```

Tương tự với `AdminTrainerDetailAPIView.delete` (line 897): cũng nên dùng `trainer.soft_delete()`.

---

### BUG #10 — `AdminCreateUserAPIView`: Tạo trainer không nhất quán với `register_user` [SEVERITY: MEDIUM]

**File:** [`views.py`](file:///d:/DEHA/DEHA/gym_booking_backend/presentation/views.py) (lines 705-744)

Code này gọi `register_user.execute(role="trainer")` → `auth_service.register_user()` → tạo `Trainer` record với `name` và `email` cơ bản. Sau đó lại có đoạn code tạo thêm `Trainer.objects.get_or_create(...)` với thêm `specialty`, `session_price`.

Kết quả: `auth_service.register_user` tạo Trainer record với thông tin cơ bản, sau đó `get_or_create` sẽ **không update** vì Trainer đã tồn tại rồi (điều kiện `get_or_create` trả về `created=False`). **Các field `specialty`, `session_price`, `experience_years` sẽ không được lưu**.

**Fix:**
```python
trainer, created = Trainer.objects.get_or_create(user=user, ...)
if not created:
    # Update các field còn thiếu
    trainer.specialty = specialty
    trainer.session_price = session_price
    trainer.save()
```

---

### BUG #11 — `booking_service.create_booking`: Waitlist bỏ qua validation membership [SEVERITY: MEDIUM]

**File:** [`booking_service.py`](file:///d:/DEHA/DEHA/gym_booking_backend/application/services/booking_service.py) (lines 49-58)

```python
is_full = schedule.current_participants >= schedule.max_participants

if is_full:
    booking = Booking.objects.create(..., status=BookingStatus.WAITLIST)
    return Result.success_result(booking, "Added to waitlist", status_code=201)
```

Khi schedule đầy, hệ thống **vẫn bypass tất cả validation** (membership, weekly limit, v.v.) và trực tiếp tạo `Booking.objects.create()` thay vì qua `booking_repository.create_booking()`. 

Nhưng thực ra, tất cả validations đã được gọi **trước** đoạn này (lines 41-47) nên validation là đúng. Vấn đề là: **không dùng repository** mà gọi trực tiếp `Booking.objects.create()` — vi phạm kiến trúc sạch (Clean Architecture).

**Fix:** Gọi qua repository:
```python
booking = booking_repository.create_booking(
    user, schedule, _generate_booking_code(), note, status=BookingStatus.WAITLIST
)
```

---

### BUG #12 — `_add_months` trong booking_service: Tính ngày sai cho tháng ngắn [SEVERITY: LOW]

**File:** [`booking_service.py`](file:///d:/DEHA/DEHA/gym_booking_backend/application/services/booking_service.py) (lines 19-23)

```python
def _add_months(start_date, months):
    year = start_date.year + (start_date.month - 1 + months) // 12
    month = (start_date.month - 1 + months) % 12 + 1
    day = min(start_date.day, 28)  # ← Hard-code ngày 28!
    return start_date.replace(year=year, month=month, day=day)
```

Luôn truncate day về 28, nghĩa là nếu user đặt từ ngày 30/01, end_date sẽ là ngày 28/03 thay vì 30/03 (hoặc 28/02 nếu 1 tháng).

**Fix:**
```python
import calendar
def _add_months(start_date, months):
    month = start_date.month - 1 + months
    year = start_date.year + month // 12
    month = month % 12 + 1
    day = min(start_date.day, calendar.monthrange(year, month)[1])
    return start_date.replace(year=year, month=month, day=day)
```

---

### BUG #13 — `MembershipPackage`: Hard delete xóa soft-deleted packages [SEVERITY: MEDIUM]

**File:** [`models.py`](file:///d:/DEHA/DEHA/gym_booking_backend/infrastructure/models.py) (line 213)

`MembershipPackage` dùng `SoftDeleteModel` nhưng `SoftDeleteManager` (default manager) filter `is_deleted=False`. Khi admin query `MembershipPackage.objects.filter(name=name)` để kiểm tra duplicate (view line 776), nó **không thể tìm thấy** package đã bị soft-delete với cùng tên, dẫn đến tạo trùng tên nhưng với `is_deleted=True`.

Về lý thuyết, `unique=True` sẽ chặn điều này ở DB level, nhưng nếu soft-deleted record có `unique` constraint thì DB sẽ raise `IntegrityError` khi cố tạo mới cùng tên.

**Fix:** Dùng `all_objects` manager khi check duplicate:
```python
if MembershipPackage.all_objects.filter(name=name).exists():
    return Result.failure_result(f"Gói tập '{name}' đã tồn tại.", ...)
```

---

### BUG #14 — `InvoiceItem.unique_invoice_item_per_object`: Constraint chặn re-invoice [SEVERITY: MEDIUM]

**File:** [`models.py`](file:///d:/DEHA/DEHA/gym_booking_backend/infrastructure/models.py) (lines 304-310)

```python
constraints = [
    models.UniqueConstraint(
        fields=["content_type", "object_id"],
        condition=models.Q(object_id__isnull=False),
        name="unique_invoice_item_per_object",
    ),
]
```

Constraint này ngăn tạo 2 `InvoiceItem` cho cùng 1 object (ví dụ 1 membership). Tuy nhiên `InvoiceItem` dùng `object_id` (raw int), **không có** `content_type` khi tạo qua `invoice_repository.create_invoice_item()`:

```python
def create_invoice_item(self, invoice, item_type, object_id, amount):
    return InvoiceItem.objects.create(
        invoice=invoice,
        item_type=item_type,
        object_id=object_id,  # ← content_type KHÔNG được set!
        amount=amount,
    )
```

`content_type` là nullable nhưng khi `object_id` không null và `content_type` null → constraint `unique_invoice_item_per_object` chỉ apply khi `object_id IS NOT NULL`, nhưng không phân biệt được membership vs trainer_booking nếu chúng có cùng `id` (ví dụ membership.id=1 và trainer_booking.id=1 sẽ conflict).

**Fix:** Luôn set `content_type` khi tạo `InvoiceItem`:
```python
from django.contrib.contenttypes.models import ContentType
from gym_booking_backend.infrastructure.models import UserMembership, TrainerBooking

def create_invoice_item(self, invoice, item_type, object_id, amount, model_class=None):
    content_type = ContentType.objects.get_for_model(model_class) if model_class else None
    return InvoiceItem.objects.create(
        invoice=invoice,
        item_type=item_type,
        content_type=content_type,
        object_id=object_id,
        amount=amount,
    )
```

---

## 📊 TỔNG KẾT

| # | Bug | Severity | File | Impact |
|---|-----|----------|------|--------|
| 1 | Stub methods trong BookingRepository | 🔴 CRITICAL | `booking_repository.py` | Toàn bộ class booking bị vô hiệu hóa |
| 2 | `allowed_categories` không tồn tại trong model | 🔴 CRITICAL | `models.py` + `booking_validator.py` | AttributeError khi đặt lịch class |
| 3 | `BookingSerializer` không được import | 🟠 HIGH | `views.py` | NameError ở Attendance API |
| 4 | Reset membership dates mỗi lần confirm | 🟠 HIGH | `payment_service.py` | Membership dates bị overwrite sai |
| 8 | Review bị chặn vĩnh viễn do stub | 🟠 HIGH | `booking_repository.py` | Không tạo được review nào |
| 10 | Tạo trainer không nhất quán | 🟡 MEDIUM | `views.py` | Specialty, session_price không lưu |
| 5 | Waitlist missing `updated_at` | 🟡 MEDIUM | `booking_service.py` | Timestamp sai |
| 6 | Race condition `used_sessions` | 🟡 MEDIUM | `pt_booking_service.py` | Session count sai khi concurrent |
| 7 | Freeze overlap không được kiểm tra | 🟡 MEDIUM | `membership_service.py` | User có thể freeze trùng ngày |
| 9 | Hard delete thay vì Soft delete | 🟡 MEDIUM | `views.py` | Mất data lịch sử |
| 11 | Waitlist bypass repository pattern | 🟡 MEDIUM | `booking_service.py` | Vi phạm Clean Architecture |
| 13 | Soft-deleted package name conflict | 🟡 MEDIUM | `views.py` | IntegrityError khi tạo cùng tên |
| 14 | InvoiceItem missing content_type | 🟡 MEDIUM | `invoice_repository.py` | Constraint conflict giữa các object type |
| 12 | `_add_months` hard-code day=28 | 🟢 LOW | `booking_service.py` | End date sai ≤2 ngày |

---

## 🗺️ ROADMAP SỬA LỖI (Theo Độ Ưu Tiên)

### Phase 1 — Critical Fixes (Sửa ngay)
1. **[BUG#1 + BUG#8]** Implement đầy đủ tất cả stub methods trong `DjangoBookingRepository`
2. **[BUG#2]** Thêm field `allowed_categories` vào `MembershipPackage` model + tạo migration
3. **[BUG#3]** Tạo `BookingSerializer` và import đúng chỗ trong `views.py`

### Phase 2 — High Fixes
4. **[BUG#4]** Fix payment confirmation không reset membership dates sai
5. **[BUG#10]** Fix AdminCreateUser — đảm bảo update trainer fields đầy đủ

### Phase 3 — Medium Fixes
6. **[BUG#6]** Dùng `F()` expression cho `used_sessions` để atomic update
7. **[BUG#7]** Thêm kiểm tra freeze overlap trong `freeze_membership`
8. **[BUG#9]** Chuyển sang `soft_delete()` trong admin delete APIs
9. **[BUG#11]** Refactor waitlist booking qua repository
10. **[BUG#13]** Dùng `all_objects` manager khi check duplicate package name
11. **[BUG#14]** Luôn set `content_type` khi tạo `InvoiceItem`
12. **[BUG#5]** Thêm `updated_at` vào waitlist save

### Phase 4 — Low Fixes
13. **[BUG#12]** Fix `_add_months` dùng `calendar.monthrange`

---

## 📝 GHI CHÚ QUAN TRỌNG

> [!WARNING]
> **BUG #1 là bug quan trọng nhất.** Toàn bộ luồng đặt lịch class gym (`ClassSchedule`/`Booking`) bị vô hiệu hóa hoàn toàn. Hệ thống chỉ hoạt động với `TrainerBooking` và `PTBooking`. Cần implement ngay trước khi chạy production.

> [!IMPORTANT]
> **BUG #2** sẽ gây `AttributeError` crash ngay khi user đặt lịch class nếu đã có data `ClassSchedule`. Cần tạo migration cho field `allowed_categories`.

> [!NOTE]
> Nhiều bugs (BUG #1, #8) bắt nguồn từ cùng 1 file — `booking_repository.py` được thiết kế như skeleton nhưng chưa được implement đầy đủ. Đây là "technical debt" lớn nhất của dự án hiện tại.
