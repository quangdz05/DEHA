# BÁO CÁO PHÂN TÍCH & ĐÁNH GIÁ LOGIC HỆ THỐNG GYM BOOKING

Báo cáo này tập trung đánh giá sâu về **logic nghiệp vụ (business logic)**, **ràng buộc dữ liệu (validation constraints)**, **vấn đề đồng thời (concurrency)** và các **lỗ hổng tiềm ẩn** trong hệ thống Gym Booking hiện tại.

---

## 1. ⚠️ CÁC VẤN ĐỀ LOGIC NGHIỆP VỤ & LỖ HỔNG (CRITICAL LOGIC BUGS)

### Vấn đề 1: Trùng Lịch Huấn Luyện Viên (Trainer Schedule Overlap)
* **Mô tả**: Khi người dùng đặt lịch lớp tập nhóm (`ClassSchedule`), hệ thống gọi hàm check trùng lịch của trainer: `schedule_repository.has_trainer_conflict(...)`. Tuy nhiên, HLV hiện tại tham gia vào 3 loại lịch trình:
  1. Lịch dạy lớp nhóm (`ClassSchedule`).
  2. Đặt lịch cá nhân 1-1 lẻ (`TrainerBooking`).
  3. Lịch tập PT cố định theo tháng (`PTBooking`).
* **Hậu quả**: Hàm `has_trainer_conflict` hiện tại **chỉ** truy vấn chéo với bảng `ClassSchedule` khác mà bỏ qua kiểm tra chéo với `TrainerBooking` và `PTBooking`. HLV có thể bị trùng lịch dạy lớp nhóm và dạy PT 1-1 cùng một giờ.
* **Hướng khắc phục**: Refactor lại repository check trùng lịch để quét qua cả 3 bảng:
  ```python
  def has_trainer_conflict(trainer, start_time, end_time, exclude_schedule_id=None):
      # 1. Check ClassSchedule
      # 2. Check TrainerBooking (status in PENDING, CONFIRMED)
      # 3. Check PTBooking (status in CONFIRMED)
  ```

---

### Vấn đề 2: Lỗi Đồng Thời (Race Condition) Khi Hủy Lịch & Đẩy Hàng Đợi (Waitlist Promotion)
* **Mô tả**: Trong hàm `cancel_booking` (`booking_service.py`), khi một hội viên hủy lịch, hệ thống sẽ tự động tìm kiếm người đầu tiên trong danh sách chờ (`WAITLIST`) để đẩy lên trạng thái `PENDING`:
  ```python
  next_waitlist = Booking.objects.filter(
      schedule=schedule,
      status=BookingStatus.WAITLIST
  ).order_by("created_at", "id").first()
  ```
  Mặc dù toàn bộ hàm được bọc trong `@transaction.atomic`, nhưng truy vấn lấy `next_waitlist` **không sử dụng** cơ chế khóa bản ghi (`select_for_update()`).
* **Hậu quả**: Nếu có 2 hội viên cùng hủy lịch của lớp đó tại cùng một thời điểm (concurrency cao), cả 2 luồng xử lý có thể cùng đọc ra một bản ghi `next_waitlist` duy nhất và cùng chuyển nó lên `PENDING`, dẫn đến việc số lượng người tham gia thực tế desync hoặc mất suất của người xếp hàng chờ tiếp theo.
* **Hướng khắc phục**: Áp dụng cơ chế khóa pessimistic lock cho bản ghi waitlist được chọn:
  ```python
  next_waitlist = Booking.objects.select_for_update().filter(
      schedule=schedule,
      status=BookingStatus.WAITLIST
  ).order_by("created_at", "id").first()
  ```

---

### Vấn đề 3: Logic Tính Giới Hạn Đặt Lịch Theo Tuần Bị Lệch Múi Giờ (Timezone Boundary Desync)
* **Mô tả**: Trong `booking_validator.py` (`validate_weekly_booking_limit`), đầu tuần và cuối tuần được tính bằng:
  ```python
  week_start = base_date - timedelta(days=base_date.weekday())
  week_end = week_start + timedelta(days=6)
  ```
  `base_date` được lấy bằng `timezone.localdate()`. Tuy nhiên, cơ sở dữ liệu lưu các trường `start_time` dưới dạng UTC datetime.
* **Hậu quả**: Nếu hệ thống chạy ở múi giờ Việt Nam (UTC+7), một lượt đặt lịch vào sáng Thứ Hai (ví dụ 05:00 sáng Thứ Hai giờ Việt Nam) thực tế sẽ lưu trong DB là 22:00 Chủ Nhật giờ UTC. Khi thực hiện câu lệnh SQL đếm số lượng đặt lịch trong tuần từ ngày `week_start` (Thứ Hai) đến `week_end` (Chủ Nhật), bản ghi này sẽ bị tính lệch sang tuần trước, làm sai lệch logic giới hạn số buổi tập tối đa của gói hội viên.
* **Hướng khắc phục**: Chuẩn hóa ngày giờ về timezone UTC hoặc múi giờ local được cấu hình cụ thể (`settings.TIME_ZONE`) trước khi so sánh ngày ở mức Database.

---

### Vấn đề 4: Cơ Chế Tạo Lịch PT Theo Tháng Quá Cứng Nhắc (Rigid Generation Logic)
* **Mô tả**: Trong `pt_booking_service.py` (`preview_monthly_pt_bookings`), hệ thống sinh lịch dựa trên số ngày cố định của gói (`duration_days`). Nếu số ngày quá ngắn hoặc ngày bắt đầu rơi vào cuối tuần và người dùng chọn ít thứ trong tuần, số buổi tập tạo ra sẽ nhỏ hơn `total_sessions` của gói, hệ thống lập tức báo lỗi và dừng toàn bộ tiến trình đăng ký.
* **Hậu quả**: Gây trải nghiệm xấu cho khách hàng (UX blocker). Ví dụ khách mua gói 12 buổi hạn 30 ngày nhưng chỉ chọn tập Thứ Hai, nếu tháng đó có ít hơn 4 tuần hoặc có ngày lễ nghỉ, hệ thống sẽ từ chối đăng ký thay vì tự động đề xuất kéo dài thời hạn gói hoặc gợi ý thêm thứ tập khác.
* **Hướng khắc phục**:
  1. Cho phép tự động kéo dài ngày kết thúc (`end_date`) cho đến khi xếp đủ số buổi tập (`total_sessions`).
  2. Hiển thị cảnh báo trực quan khuyên người dùng chọn thêm thứ tập nếu số buổi sinh ra chưa đủ.

---

### Vấn đề 5: Thiếu Logic Xử Lý Thanh Toán Cho Gói PT Cá Nhân (Missing PT Payment Activation Flow)
* **Mô tả**: Trong `payment_service.py` (`confirm_payment`), hệ thống đã xử lý kích hoạt tự động cho thẻ hội viên (`membership`) và đặt lịch lẻ của HLV (`CLASS_FEE` item type). Tuy nhiên, khi một hóa đơn mua gói PT cá nhân theo tháng (`UserPTPackage`) được thanh toán thành công, hệ thống **chưa có** logic chuyển trạng thái của gói PT đó từ `pending` sang `active`.
* **Hậu quả**: Người dùng mua gói PT và thanh toán thành công nhưng gói tập trên hệ thống vẫn ở trạng thái chờ kích hoạt, lịch tập tự động tạo ra của gói không khớp với luồng xử lý doanh thu.
* **Hướng khắc phục**: Bổ sung kiểm tra loại InvoiceItem trong luồng xác nhận thanh toán:
  ```python
  # Kích hoạt gói PT cá nhân khi hóa đơn liên quan được xác nhận thanh toán
  pt_item = InvoiceItem.objects.filter(
      invoice=payment.invoice,
      item_type=InvoiceItemType.PT_PACKAGE # (Cần định nghĩa thêm)
  ).first()
  if pt_item and pt_item.object_id:
      user_pt_package = UserPTPackage.objects.filter(id=pt_item.object_id).first()
      if user_pt_package:
          user_pt_package.status = UserPTPackageStatus.ACTIVE
          user_pt_package.save(update_fields=["status", "updated_at"])
  ```

---

## 2. ⚡ ĐỀ XUẤT CẢI TIẾN KIẾN TRÚC & QUẢN TRỊ (ARCHITECTURAL RECOMMENDATIONS)

### 1. Đồng Bộ Hóa Cách Phân Quyền Giữa Backend & Frontend
* **Vấn đề**: Hiện tại, logic phân quyền hiển thị navbar đang bị chồng chéo:
  - Trên các trang HTML tĩnh (Frontend): Dùng thuộc tính `data-role` và xử lý qua Javascript (`api.js`).
  - Trên các trang Django Template (Backend): Dùng `request.user.profile.role` kiểm tra trực tiếp trong file `.html`.
* **Đề xuất**: Nên chuyển đổi hoàn toàn các trang PT (`/pt-packages/` và `/my-pt-packages/`) từ Django Template sang mô hình SPA/Static HTML + REST API giống như các trang khác (`classes.html`, `packages.html`). Điều này giúp mã nguồn đồng nhất, dễ bảo trì và dễ dàng đóng gói thành ứng dụng di động/PWA sau này.

### 2. Sử Dụng Hàng Đợi Sự Kiện (Event-Driven / Signals) Cho Thanh Toán & Đặt Lịch
* **Vấn đề**: Hàm `confirm_payment` đang phải import trực tiếp các model khác (`TrainerBooking`, `UserMembership`, `InvoiceItem`) tạo ra sự liên kết chặt cứng (tight coupling) giữa Service Thanh Toán và Service Đặt Lịch.
* **Đề xuất**: Sử dụng **Django Signals** hoặc cơ chế Event Dispatcher để phát đi sự kiện `payment_confirmed`. Các Service Đặt Lịch hoặc Hội Viên sẽ đăng ký lắng nghe sự kiện này để tự kích hoạt gói của mình, giúp phân tách các mô-đun rõ ràng hơn (Loose Coupling).

### 3. Tối Ưu Hóa Hiệu Năng Truy Vấn (Query Optimization)
* **Vấn đề**: Hàm `get_queryset` trong `UserPTPackageListView` sử dụng `select_related('trainer', 'package')`. Đây là điểm tốt, tuy nhiên trong màn hình chi tiết hoặc danh sách lịch tập nhóm vẫn còn tình trạng truy vấn lặp (N+1 query) khi lấy thông tin HLV hoặc Phòng học liên quan.
* **Đề xuất**: Luôn sử dụng `select_related` hoặc `prefetch_related` cho các trường khóa ngoại khi hiển thị danh sách để giảm thiểu tối đa số lượng kết nối tới SQLite/PostgreSQL.
