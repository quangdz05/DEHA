# BÁO CÁO PHÂN TÍCH CHỨC NĂNG HỆ THỐNG & ĐỀ XUẤT CẢI TIẾN
*Dựa trên cấu trúc Cơ sở dữ liệu Gym Booking đã được nâng cấp*

Tài liệu này phân tích chi tiết các chức năng phần mềm cần được xây dựng tương ứng với cấu trúc dữ liệu hiện tại, đồng thời đề xuất những cải tiến về mặt nghiệp vụ nhằm tối ưu hóa trải nghiệm người dùng và hiệu quả quản lý vận hành phòng gym.

---

## 1. Bản đồ chức năng hệ thống (System Functional Map)

Dựa trên cấu trúc cơ sở dữ liệu đã nâng cấp, hệ thống cần được chia thành 7 phân hệ chức năng cốt lõi sau:

### Phân hệ 1: Quản lý Tài khoản & Hồ sơ cá nhân (Auth & User Profile)
* **Đăng ký / Đăng nhập phân quyền**:
  - Đăng ký tài khoản cho Học viên (Member) và Huấn luyện viên (Trainer).
  - Tự động phân vai trò người dùng (Admin, Trainer, Member) thông qua thực thể `Profile` và hệ thống Django Auth.
* **Cập nhật Hồ sơ cá nhân**:
  - Cho phép học viên cập nhật thông tin liên hệ, ảnh đại diện, đặc biệt là **Thông tin liên hệ khẩn cấp** (`emergency_contact_name`, `emergency_contact_phone`) để xử lý các sự cố y tế trong phòng tập.
* **Hồ sơ chỉ số sức khỏe & Mục tiêu tập luyện**:
  - Học viên tự khai báo bệnh lý nền, chấn thương (`health_notes`) và mục tiêu thể hình (`fitness_goals`).
  - Cho phép huấn luyện viên truy cập xem các chỉ số này của học viên đăng ký lớp mình dạy để hướng dẫn an toàn, tránh chấn thương.

### Phân hệ 2: Quản lý Huấn luyện viên & Danh mục lớp/phòng (Trainer & Gym Catalog)
* **Trang thông tin Huấn luyện viên**:
  - Hiển thị danh sách huấn luyện viên kèm tiểu sử (`bio`), số năm kinh nghiệm, hình ảnh và **chứng chỉ bằng cấp chuyên môn** (`certifications`) để học viên dễ dàng chọn lựa.
* **Quản lý danh mục lớp học (GymClass)**:
  - Thiết lập thông tin các lớp học (Zumba, Yoga, Kickboxing...), bao gồm mức độ khó (`difficulty_level`), thời lượng chuẩn (`duration_minutes`), mô tả và huấn luyện viên mặc định.
* **Quản lý phòng tập (Room)**:
  - Khai báo vị trí phòng, sức chứa tối đa (`capacity`) và **trang thiết bị/tiện ích đi kèm** (`amenities`, ví dụ: hệ thống âm thanh, thảm tập, xe đạp quay...).

### Phân hệ 3: Lập lịch học chi tiết (Class Scheduling)
* **Xếp lịch học (ClassSchedule)**:
  - Lập lịch lớp học cụ thể theo khung giờ (`start_time`, `end_time`).
  - Chỉ định phòng tập (`room`) và **Huấn luyện viên phụ trách cụ thể** (`trainer`) cho ca học đó (hỗ trợ phân công dạy thế linh hoạt mà không ảnh hưởng tới huấn luyện viên mặc định của lớp học).
* **Kiểm tra xung đột lịch biểu (Conflict Detection)**:
  - Hệ thống tự động ngăn chặn việc xếp lịch trùng giờ cho cùng một phòng tập hoặc cùng một huấn luyện viên.

### Phân hệ 4: Đặt chỗ & Quản lý lớp học (Class Booking & Roster)
* **Đặt chỗ lớp học (Booking)**:
  - Học viên đăng ký tham gia buổi học và nhận mã đặt chỗ duy nhất (`booking_code`).
  - Kiểm tra điều kiện đặt chỗ: gói tập còn hạn, gói tập có quyền học lớp này không, kiểm tra giới hạn đặt lịch hàng tuần.
* **Hàng đợi chờ (Waitlist)**:
  - Khi lớp học đạt giới hạn người tham gia tối đa (`max_participants`), cho phép học viên đăng ký vào **danh sách chờ (Waitlist)**.
* **Hủy lịch & Tự động đôn hàng đợi**:
  - Cho phép học viên hủy đặt chỗ, cập nhật lý do hủy (`cancellation_reason`).
  - Khi có học viên hủy lịch, hệ thống tự động trừ `current_participants` và tự động chuyển học viên đứng đầu danh sách chờ (Waitlist) lên trạng thái đặt lịch chính thức (Confirmed).
* **Điểm danh & Phân loại ca học (Roster Management)**:
  - Huấn luyện viên điểm danh học viên tại lớp, cập nhật trạng thái đặt chỗ thành `COMPLETED` (đã tham gia) hoặc `NO_SHOW` (đăng ký nhưng không đến tập).

### Phân hệ 5: Quản lý Gói tập & Đóng băng gói (Membership & Freeze)
* **Mua gói tập (UserMembership)**:
  - Học viên lựa chọn mua các gói tập phù hợp với nhu cầu sử dụng.
* **Phân quyền gói tập theo danh mục lớp**:
  - Kiểm tra điều kiện truy cập: Chỉ cho phép đặt chỗ đối với các lớp học nằm trong danh mục được cho phép (`allowed_categories`) của gói tập.
* **Tạm ngừng gói tập (Freeze Membership)**:
  - Học viên gửi yêu cầu tạm dừng gói tập vì lý do cá nhân (ốm đau, đi công tác).
  - Hệ thống ghi nhận lịch sử đóng băng (`MembershipFreeze`), trừ số ngày đóng băng khả dụng (`max_freeze_days`) của gói và tự động **kéo dài ngày hết hạn của gói tập** (`end_date`) tương ứng sau khi gói được kích hoạt lại.

### Phân hệ 6: Hóa đơn & Thanh toán trực tuyến (Billing & Payment)
* **Tự động xuất hóa đơn (Invoice)**:
  - Khi học viên mua gói tập hoặc phát sinh chi phí, hệ thống sinh hóa đơn (`Invoice`) kèm các mục chi tiết (`InvoiceItem`). Thiết kế này cho phép thanh toán nhiều loại dịch vụ (gói tập, vé lẻ theo buổi, nước uống, PT cá nhân).
* **Thanh toán trực tuyến (Payment Integration)**:
  - Hỗ trợ thanh toán qua VNPay, MoMo, chuyển khoản hoặc tiền mặt.
  - Lưu trữ mã giao dịch cổng thanh toán (`transaction_code`) và **toàn bộ phản hồi thô** (`payment_gateway_response`) để phục vụ đối soát tự động khi xảy ra lỗi thanh toán.

### Phân hệ 7: Đánh giá & Phản hồi (Reviews & Feedback)
* **Đánh giá dịch vụ (Review)**:
  - Cho phép học viên đánh giá huấn luyện viên hoặc lớp học theo thang điểm 1-5 sao (`RatingChoices`).
* **Đánh giá xác thực (Verified Reviews)**:
  - Chỉ cho phép gửi đánh giá nếu học viên đó thực sự đã đặt lịch và tham gia hoàn thành ca học (`Booking.status = COMPLETED`). Tránh tuyệt đối spam review khống.

---

## 2. Các điểm cần cải thiện & Đề xuất tối ưu nghiệp vụ (Business Improvements)

Để nâng tầm hệ thống từ quản lý cơ bản lên một nền tảng vận hành phòng gym chuyên nghiệp chuẩn quốc tế, chúng tôi đề xuất các cải tiến nghiệp vụ sau:

### 2.1. Động cơ tự động xếp lịch lặp lại (Recurring Schedule Engine)
* **Vấn đề**: Hiện tại cấu trúc dữ liệu lưu lịch học (`ClassSchedule`) là các ca học độc lập. Admin phải tạo thủ công từng buổi học rất tốn thời gian.
* **Giải pháp**: Xây dựng tính năng "Xếp lịch định kỳ". Cho phép cấu hình quy tắc lặp lại (ví dụ: Lớp Yoga Basics, diễn ra vào 08:00 sáng Thứ Hai và Thứ Sáu hàng tuần, lặp lại liên tục trong 3 tháng). Hệ thống sẽ tự động chạy tiến trình ngầm (cron job) để sinh ra toàn bộ các bản ghi `ClassSchedule` tương ứng trong tương lai.

### 2.2. Chính sách phạt khi hủy lịch muộn (Late Cancellation Policy)
* **Vấn đề**: Nhiều học viên đặt lịch giữ chỗ nhưng hủy sát giờ học hoặc không đến tập (`NO_SHOW`), gây lãng phí tài nguyên phòng tập và tước đi cơ hội của người khác trong danh sách chờ.
* **Giải pháp**: 
  - Quy định khung thời gian hủy lịch an toàn (ví dụ: tối thiểu trước giờ học 2 tiếng).
  - Nếu học viên hủy muộn (Late Cancel) hoặc tự ý nghỉ (`NO_SHOW`) quá 3 lần trong tháng, hệ thống sẽ tự động tạm khóa quyền đặt lịch trực tuyến trong vòng 7 ngày tiếp theo, hoặc trừ trực tiếp số buổi tập khả dụng trong gói thành viên.

### 2.3. Tích hợp Thông báo và Nhắc lịch thời gian thực (Real-time Notification Integration)
* **Vấn đề**: Học viên dễ quên lịch học, hoặc học viên trong hàng đợi chờ không biết mình vừa được đôn lên danh sách chính thức khi có người hủy lịch.
* **Giải pháp**: 
  - Tích hợp cổng gửi tin nhắn (Email/SMS/Push Notification/Zalo ZNS).
  - Tự động gửi nhắc lịch tập trước giờ học 1 tiếng cho cả học viên và huấn luyện viên.
  - Tự động gửi thông báo chúc mừng kèm mã QR check-in khi học viên được chuyển từ Waitlist sang Confirmed.

### 2.4. Bảng điều khiển phân tích số liệu (Analytics Dashboard)
* **Vấn đề**: Quản lý phòng gym cần số liệu trực quan để tối ưu hóa nguồn lực phòng tập và doanh thu.
* **Giải pháp**: Xây dựng phân hệ báo cáo cho quản trị viên bao gồm:
  - **Tỷ lệ lấp đầy lớp (Occupancy Rate)**: Thống kê số lượng người tham gia thực tế so với sức chứa của phòng tập để xác định khung giờ vàng hoặc lớp học kém hiệu quả.
  - **Báo cáo doanh thu & Dòng tiền**: Phân tích doanh thu từ các hóa đơn theo tháng, thống kê tỷ lệ chọn các phương thức thanh toán (VNPay, MoMo, chuyển khoản).
  - **Đánh giá Huấn luyện viên**: Tổng hợp điểm đánh giá trung bình và số lượng học viên tham gia học của từng huấn luyện viên để làm cơ sở tính lương thưởng/KPI.

### 2.5. Hệ thống mã giảm giá & Chiến dịch Marketing (Coupon & Campaign Engine)
* **Vấn đề**: Chưa có cơ chế khuyến mãi kích cầu mua gói tập.
* **Giải pháp**: Thiết kế thêm bảng `Coupon` (Mã giảm giá) liên kết với thực thể `Invoice`. Cho phép Admin tạo các mã giảm giá theo tỷ lệ phần trăm (ví dụ: giảm 10% gói VIP cho ngày lễ) hoặc giảm số tiền cố định để thu hút khách hàng mới đăng ký.
