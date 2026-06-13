# PHÂN RÃ CHỨC NĂNG HỆ THỐNG THEO VAI TRÒ & MÀN HÌNH
*Dự án Hệ thống Gym Booking*

Tài liệu này phân chia rõ ràng các nhóm chức năng tương ứng với 3 đối tượng người dùng chính trong hệ thống: **Học viên (Hội viên / Khách hàng)**, **Huấn luyện viên (HLV)**, và **Quản trị viên (Admin)**. Việc phân rã này giúp việc phát triển giao diện (UI/UX) và phân quyền kiểm soát truy cập (Access Control) trên Frontend diễn ra chuẩn xác.

---

## 1. Màn hình Học viên / Khách hàng (Member Portal)

Học viên là đối tượng sử dụng chính của hệ thống để tra cứu, đăng ký gói tập và đặt lịch học.

### 1.1. Tra cứu Danh mục & Lịch học
- **Xem thông tin Huấn luyện viên (`trainers.html`)**: Xem danh sách HLV, thông tin kinh nghiệm, chuyên môn và **chứng chỉ bằng cấp** (`certifications`).
- **Xem thông tin Lớp học (`classes.html`)**: Xem danh mục lớp học, mô tả, mức độ khó, thời lượng và **trang thiết bị trong phòng học** (`amenities`).
- **Tra cứu lịch tập (`schedules.html`)**: Lọc lịch học theo ngày hoặc theo HLV. Xem ca học cụ thể dạy bởi HLV nào, số slot còn trống.

### 1.2. Mua Gói tập & Quản lý Thẻ thành viên (`packages.html`)
- **Đăng ký gói tập**: Chọn mua gói tập (Standard, VIP...), tự động sinh **Hóa đơn chi tiết** (`Invoice` / `InvoiceItem`) hiển thị tổng tiền, chi tiết dịch vụ mua.
- **Thanh toán**: Tích hợp thanh toán qua VNPay, MoMo hoặc chuyển khoản ngân hàng.
- **Tạm dừng thẻ tập (Membership Freeze)**: Yêu cầu tạm dừng kích hoạt gói tập khi đi công tác/bị ốm, tự động gia hạn số ngày hết hạn tương ứng.

### 1.3. Quản lý Đặt lịch tập cá nhân (`my-bookings.html`)
- **Đặt chỗ ca học**: Đặt lịch tập (Confirmed nếu còn chỗ, tự động xếp vào **Hàng chờ Waitlist** nếu lớp đã đầy).
- **Xem lịch sử đặt chỗ**: Theo dõi danh sách các buổi tập đã đặt kèm trạng thái thực tế (Chờ xác nhận, Đã xác nhận, Danh sách chờ, Đã học xong, Vắng mặt, Đã hủy).
- **Hủy lịch tập**: Cho phép học viên hủy lịch trước giờ học, bắt buộc nhập **Lý do hủy lịch** (`cancellation_reason`).
- **Gửi đánh giá xác thực (Verified Review)**: Gửi phản hồi, chấm điểm sao (1-5 sao) cho HLV hoặc Lớp học sau khi buổi học kết thúc thành công (`status = COMPLETED`).

---

## 2. Màn hình Huấn luyện viên (Trainer Portal)

Huấn luyện viên sử dụng cổng thông tin này để theo dõi lịch giảng dạy được phân công và quản lý học viên trong lớp học của mình.

### 2.1. Quản lý Lịch giảng dạy cá nhân (`trainer-dashboard.html`)
- **Xem lịch dạy**: Hiển thị danh sách các ca học (`ClassSchedule`) được phân công đứng lớp (bao gồm ca dạy chính thức và các ca được phân công dạy thế).
- **Trạng thái lớp**: Theo dõi số lượng học viên đăng ký thực tế trên tổng số tối đa (`current_participants` / `max_participants`).

### 2.2. Điểm danh & Quản lý Học viên lớp học
- **Xem danh sách học viên (Roster)**: Xem danh sách học viên đã đặt lịch trong ca dạy của mình.
- **Xem Hồ sơ sức khỏe học viên**: Truy cập xem **Ghi chú bệnh lý/chấn thương** (`health_notes`) và **Mục tiêu thể hình** (`fitness_goals`) của từng học viên đăng ký trong lớp để điều chỉnh giáo án phù hợp.
- **Liên hệ khẩn cấp**: Xem số điện thoại và tên liên hệ khẩn cấp của học viên để xử lý khi có chấn thương/sự cố y tế xảy ra.
- **Điểm danh học viên**: Đánh dấu học viên đã tham gia học (`COMPLETED`) hoặc vắng mặt (`NO_SHOW`).

### 2.3. Theo dõi Đánh giá phản hồi
- Xem danh sách nhận xét, góp ý và chấm điểm số sao mà học viên gửi riêng cho mình để nâng cao chất lượng giảng dạy.

---

## 3. Màn hình Quản trị viên (Admin Portal)

Admin sử dụng bảng điều khiển này để quản lý toàn bộ hệ thống, kiểm soát dữ liệu thô, phê duyệt thanh toán và cấu hình lịch học.

### 3.1. Thiết lập Lịch học & Quản lý Phòng/Lớp
- **Tạo mới lớp học & phòng tập**: Quản lý danh mục lớp, khai báo phòng học mới kèm danh sách tiện ích phòng.
- **Thiết lập lịch tập (ClassSchedule)**: Tạo ca học chi tiết, phân bổ phòng tập, thời gian bắt đầu/kết thúc và HLV đứng lớp.
- **Ngăn trùng lịch tự động**: Hệ thống hiển thị cảnh báo chặn lưu khi xếp phòng tập hoặc HLV bị trùng lịch giờ dạy với ca học khác.

### 3.2. Quản lý Đặt chỗ & Phê duyệt (Booking & Operation Control)
- **Quản lý đặt chỗ toàn hệ thống**: Theo dõi danh sách đăng ký học của tất cả lớp. Cho phép Admin thay đổi trạng thái đặt chỗ thủ công khi cần.
- **Kiểm soát hàng chờ (Waitlist)**: Theo dõi danh sách học viên đang xếp hàng chờ của các lớp đã đầy.
- **Duyệt đóng băng thẻ tập**: Xem xét và phê duyệt các yêu cầu tạm dừng gói tập của hội viên.

### 3.3. Phê duyệt Giao dịch & Quản lý Hóa đơn (`admin-dashboard.html`)
- **Duyệt thanh toán gói tập**: Xem danh sách giao dịch nạp tiền mua gói thành viên (`Payment`).
- **Kích hoạt thẻ tập**: Admin phê duyệt giao dịch thành công -> Hóa đơn tương ứng chuyển sang trạng thái đã thanh toán (`InvoiceStatus.PAID`) và tự động kích hoạt gói tập (`UserMembership`) cho học viên.
- **Thống kê Báo cáo tài chính**: 
  - Thống kê doanh thu thực tế nhận được.
  - Theo dõi lượng hóa đơn đang chờ thanh toán/bị hủy.
