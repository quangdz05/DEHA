const defaultClass = "assets/images/default-class.jpg";
const defaultAvatar = "assets/images/default-avatar.png";
const APP_LANG_KEY = "gym_lang";

const I18N_TEXT = {
  vi: {
    no_data: "Ch\u01b0a c\u00f3 d\u1eef li\u1ec7u.",
    edit: "S\u1eeda",
    delete: "X\u00f3a",
    close: "\u0110\u00f3ng",
    save_changes: "L\u01b0u thay \u0111\u1ed5i",
    edit_schedule: "S\u1eeda l\u1ecbch t\u1eadp",
    edit_trainer: "S\u1eeda hu\u1ea5n luy\u1ec7n vi\u00ean",
    no_schedule_data: "Ch\u01b0a c\u00f3 l\u1ecbch d\u1ea1y n\u00e0o.",
    no_trainer_data: "Ch\u01b0a c\u00f3 HLV n\u00e0o.",
    no_package_data: "Ch\u01b0a c\u00f3 g\u00f3i t\u1eadp n\u00e0o.",
    update_schedule_success: "C\u1eadp nh\u1eadt l\u1ecbch t\u1eadp th\u00e0nh c\u00f4ng.",
    update_trainer_success: "C\u1eadp nh\u1eadt HLV th\u00e0nh c\u00f4ng.",
    delete_schedule_confirm: "B\u1ea1n ch\u1eafc ch\u1eafn mu\u1ed1n x\u00f3a l\u1ecbch t\u1eadp n\u00e0y?",
    delete_trainer_confirm: "B\u1ea1n ch\u1eafc ch\u1eafn mu\u1ed1n x\u00f3a HLV n\u00e0y?",
    delete_package_confirm: "B\u1ea1n ch\u1eafc ch\u1eafn mu\u1ed1n x\u00f3a g\u00f3i t\u1eadp n\u00e0y?"
  },
  en: {
    no_data: "No data available.",
    edit: "Edit",
    delete: "Delete",
    close: "Close",
    save_changes: "Save changes",
    edit_schedule: "Edit Schedule",
    edit_trainer: "Edit Trainer",
    no_schedule_data: "No schedules found.",
    no_trainer_data: "No trainers found.",
    no_package_data: "No packages found.",
    update_schedule_success: "Schedule updated successfully.",
    update_trainer_success: "Trainer updated successfully.",
    delete_schedule_confirm: "Are you sure you want to delete this schedule?",
    delete_trainer_confirm: "Are you sure you want to delete this trainer?",
    delete_package_confirm: "Are you sure you want to delete this package?"
  }
};

function getAppLanguage() {
  const saved = localStorage.getItem(APP_LANG_KEY);
  if (saved === "vi" || saved === "en") return saved;
  const navLang = (navigator.language || "en").toLowerCase();
  return navLang.startsWith("vi") ? "vi" : "en";
}

function t(key) {
  const lang = getAppLanguage();
  const text = I18N_TEXT[lang] || I18N_TEXT.vi;
  return text[key] || I18N_TEXT.vi[key] || key;
}

function formatDateTime(value) {
  if (!value) return "-";
  return new Date(value).toLocaleString("vi-VN", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).replace(",", " -");
}

function statusText(status) {
  const labels = {
    open: "Còn chỗ",
    full: "Hết chỗ",
    cancelled: "Đã hủy",
    active: "Đang hoạt động",
    inactive: "Không hoạt động",
    pending: "Chờ xác nhận",
    confirmed: "Đã xác nhận",
    completed: "Hoàn thành",
    no_show: "Vắng mặt",
    waitlist: "Danh sách chờ",
    success: "Thành công",
    failed: "Thất bại",
    paid: "Đã thanh toán",
    expired: "Hết hạn",
    frozen: "Tạm dừng",
  };
  return labels[status] || status || "-";
}

function statusBadge(status) {
  return `<span class="status-badge status-${status}">${statusText(status)}</span>`;
}

function loadingRow(colspan, text = "Đang tải...") {
  return `<tr><td colspan="${colspan}" class="loading-state"><span class="spinner-border spinner-border-sm text-brand me-2"></span>${text}</td></tr>`;
}

function emptyRow(colspan, title, desc = "") {
  return `<tr><td colspan="${colspan}" class="empty-state"><strong>${title}</strong>${desc ? `<span>${desc}</span>` : ""}</td></tr>`;
}

function getInitials(name) {
  return String(name || "HLV")
    .trim()
    .split(/\s+/)
    .slice(-2)
    .map((part) => part.charAt(0).toUpperCase())
    .join("") || "HLV";
}

function getClassType(item) {
  const source = `${item.category_name || ""} ${item.name || ""}`.toLowerCase();
  if (source.includes("boxing")) return { key: "boxing", icon: "BX", label: "Boxing" };
  if (source.includes("cardio")) return { key: "cardio", icon: "CD", label: "Cardio" };
  if (source.includes("yoga")) return { key: "yoga", icon: "YG", label: "Yoga" };
  if (source.includes("weight") || source.includes("tạ") || source.includes("ta")) return { key: "weight", icon: "WT", label: "Weight Training" };
  if (source.includes("zumba")) return { key: "zumba", icon: "ZB", label: "Zumba" };
  return { key: "default", icon: "GY", label: item.category_name || "Gym Class" };
}

function classVisual(item) {
  if (item.image) {
    return `<img src="${imageUrl(item.image, defaultClass)}" alt="${item.name}">`;
  }
  const type = getClassType(item);
  return `<div class="class-visual ${type.key}"><span class="class-icon">${type.icon}</span><span class="class-label">${type.label}</span></div>`;
}

function fixVietnameseTextNodes(root = document.body) {
  if (!root) return;
  const replacements = [
    ["Lop tap", "Lớp tập"],
    ["Lich tap", "Lịch tập"],
    ["Goi tap", "Gói tập"],
    ["Quan ly he thong", "Quản lý hệ thống"],
    ["Quan ly Admin", "Quản lý Admin"],
    ["Chua phan cong", "Chưa phân công"],
    ["Con ch?", "Còn chỗ"],
    ["Xem h?c vien", "Xem học viên"],
    ["Dat lich 1-1", "Đặt lịch 1-1"],
    ["Ho tro tam dung", "Hỗ trợ tạm dừng"],
    ["Cho duyet thanh toan", "Chờ duyệt thanh toán"],
    ["Dang nhap", "Đăng nhập"],
    ["Dang xuat", "Đăng xuất"],
    ["Lich cua toi", "Lịch của tôi"],
    ["Lich day HLV", "Lịch dạy HLV"],
    ["Hoc vien", "Học viên"],
    ["Hanh dong", "Hành động"],
    ["Trang thai", "Trạng thái"],
    ["Thoi gian", "Thời gian"],
    ["Phong", "Phòng"],
    ["Gia", "Giá"],
    ["So ngay", "Số ngày"],
    ["Tam dung", "Tạm dừng"],
    ["Huy", "Hủy"],
    ["Dong", "Đóng"],
    ["Dang tai", "Đang tải"],
    ["Thanh toan", "Thanh toán"],
    ["Chua co", "Chưa có"],
    ["Khong kha dung", "Không khả dụng"],
    ["Lá»›p táº­p", "Lớp tập"],
    ["Lá»‹ch táº­p", "Lịch tập"],
    ["GÃ³i táº­p", "Gói tập"],
    ["Lá»‹ch cá»§a tÃ´i", "Lịch của tôi"],
    ["Lá»‹ch dáº¡y HLV", "Lịch dạy HLV"],
    ["Quáº£n lÃ½ Admin", "Quản lý Admin"],
    ["ÄÄƒng nháº­p", "Đăng nhập"],
    ["ÄÄƒng xuáº¥t", "Đăng xuất"],
    ["Huáº¥n luyá»‡n viÃªn", "Huấn luyện viên"],
    ["Khu vá»±c Huáº¥n luyá»‡n viÃªn", "Khu vực Huấn luyện viên"],
    ["PhÃ²ng Táº­p", "Phòng tập"],
    ["Thá»i Gian", "Thời gian"],
    ["Tráº¡ng ThÃ¡i", "Trạng thái"],
    ["Danh sÃ¡ch há»c viÃªn", "Danh sách học viên"],
    ["Há»c ViÃªn", "Học viên"],
    ["Sá»‘ Äiá»‡n Thoáº¡i", "Số điện thoại"],
    ["ÄÃ³ng", "Đóng"],
    ["Äang táº£i", "Đang tải"],
  ];

  const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT, {
    acceptNode(node) {
      const parent = node.parentElement;
      if (!parent || ["SCRIPT", "STYLE", "NOSCRIPT"].includes(parent.tagName)) {
        return NodeFilter.FILTER_REJECT;
      }
      return NodeFilter.FILTER_ACCEPT;
    },
  });
  const nodes = [];
  while (walker.nextNode()) nodes.push(walker.currentNode);
  nodes.forEach((node) => {
    let text = node.nodeValue;
    replacements.forEach(([from, to]) => {
      text = text.replaceAll(from, to);
    });
    node.nodeValue = text;
  });

  root.querySelectorAll("input[placeholder], textarea[placeholder], button[value]").forEach((el) => {
    ["placeholder", "value"].forEach((attr) => {
      if (!el.hasAttribute(attr)) return;
      let text = el.getAttribute(attr);
      replacements.forEach(([from, to]) => {
        text = text.replaceAll(from, to);
      });
      el.setAttribute(attr, text);
    });
  });
}

function applyAdminLanguageText() {
  const scheduleTitle = document.getElementById("editScheduleModalTitle");
  const trainerTitle = document.getElementById("editTrainerModalTitle");
  const scheduleClose = document.getElementById("editScheduleModalCloseBtn");
  const trainerClose = document.getElementById("editTrainerModalCloseBtn");
  const scheduleSave = document.getElementById("editScheduleModalSaveBtn");
  const trainerSave = document.getElementById("editTrainerModalSaveBtn");
  if (scheduleTitle) scheduleTitle.textContent = t("edit_schedule");
  if (trainerTitle) trainerTitle.textContent = t("edit_trainer");
  if (scheduleClose) scheduleClose.textContent = t("close");
  if (trainerClose) trainerClose.textContent = t("close");
  if (scheduleSave) scheduleSave.textContent = t("save_changes");
  if (trainerSave) trainerSave.textContent = t("save_changes");
}

function applyMyBookingsLanguageText() {
  const english = getAppLanguage() === "en";
  const heading = document.querySelector("main .container h1");
  if (heading && document.getElementById("bookingRows")) {
    heading.textContent = english ? "My Bookings" : "Lịch tập của tôi";
  }
  const tableHeaders = document.querySelectorAll(".my-bookings-table thead th");
  if (tableHeaders.length === 5) {
    const vi = ["Mã", "Lớp", "Thời gian", "Trạng thái", "Hành động"];
    const en = ["Code", "Class", "Time", "Status", "Action"];
    const values = english ? en : vi;
    values.forEach((value, index) => {
      tableHeaders[index].textContent = value;
    });
  }
}

async function refreshAdminLanguageData() {
  if (!document.getElementById("adminScheduleListRows")) return;
  applyAdminLanguageText();
  await Promise.allSettled([
    loadAdminScheduleList(),
    loadAdminTrainerList(),
    loadAdminPackageList(),
  ]);
}

function setAppLanguage(lang) {
  const next = lang === "en" ? "en" : "vi";
  localStorage.setItem(APP_LANG_KEY, next);
  if (document.getElementById("adminScheduleListRows")) {
    refreshAdminLanguageData();
    return;
  }
  if (document.getElementById("bookingRows")) {
    applyMyBookingsLanguageText();
    loadMyBookings();
    return;
  }
  location.reload();
}

function initLanguageSwitcher() {
  const selector = document.getElementById("appLangSelect");
  if (!selector) return;
  selector.value = getAppLanguage();
  selector.addEventListener("change", (event) => {
    setAppLanguage(event.target.value);
  });
  applyAdminLanguageText();
  applyMyBookingsLanguageText();
}

window.setAppLanguage = setAppLanguage;
window.applyScheduleFilters = applyScheduleFilters;
window.resetScheduleFilters = resetScheduleFilters;
document.addEventListener("DOMContentLoaded", initLanguageSwitcher);
document.addEventListener("DOMContentLoaded", () => fixVietnameseTextNodes());

function qs(name) {
  return new URLSearchParams(location.search).get(name);
}

function renderCards(target, items, render) {
  const el = document.querySelector(target);
  if (!el) return;
  el.innerHTML = items.length ? items.map(render).join("") : `<p class="text-muted">${t("no_data")}</p>`;
  fixVietnameseTextNodes(el);
}

async function loadHome() {
  if (localStorage.getItem("gymUser")) {
    try {
      window.userMemberships = await apiFetch("/memberships/my/");
    } catch (err) {
      console.error("Error fetching memberships on home load", err);
    }
  }
  const [classes, trainers, packages] = await Promise.all([
    apiFetch("/classes/"),
    apiFetch("/trainers/"),
    apiFetch("/membership-packages/"),
  ]);
  window.gymTrainerCache = trainers;
  renderCards("#featuredClasses", classes.slice(0, 6), classCard);
  renderCards("#featuredTrainers", trainers.slice(0, 3), trainerCard);
  renderCards("#packages", packages, packageCard);
}

async function loadClasses() {
  const classes = await apiFetch("/classes/");
  renderCards("#classList", classes, classCard);
}

async function loadTrainers() {
  const trainers = await apiFetch("/trainers/");
  window.gymTrainerCache = trainers;
  renderCards("#trainerList", trainers, trainerCard);
}

async function loadPackages() {
  const packages = await apiFetch("/membership-packages/");
  renderCards("#packageList", packages, packageCard);
}

async function loadSchedules() {
  const schedules = await apiFetch("/schedules/");
  window.gymSchedules = schedules;
  renderSchedules(schedules);
}

function applyScheduleFilters() {
  const schedules = window.gymSchedules || [];
  const keyword = (document.getElementById("scheduleSearch")?.value || "").trim().toLowerCase();
  const date = document.getElementById("scheduleDate")?.value || "";
  const room = (document.getElementById("scheduleRoom")?.value || "").trim().toLowerCase();
  const status = document.getElementById("scheduleStatus")?.value || "";

  const filtered = schedules.filter((s) => {
    const text = `${s.gym_class_name || ""} ${s.trainer_name || ""}`.toLowerCase();
    const scheduleDate = s.start_time ? new Date(s.start_time).toISOString().slice(0, 10) : "";
    const roomName = String(s.room_name || "").toLowerCase();
    return (!keyword || text.includes(keyword))
      && (!date || scheduleDate === date)
      && (!room || roomName.includes(room))
      && (!status || s.status === status);
  });

  renderSchedules(filtered);
}

function resetScheduleFilters() {
  ["scheduleSearch", "scheduleDate", "scheduleRoom", "scheduleStatus"].forEach((id) => {
    const el = document.getElementById(id);
    if (el) el.value = "";
  });
  renderSchedules(window.gymSchedules || []);
}

function renderSchedules(schedules) {
  const body = document.querySelector("#scheduleRows");
  if (!body) return;
  const currentUser = JSON.parse(localStorage.getItem("gymUser") || "null");
  const canViewStudents = currentUser && (currentUser.role === "trainer" || currentUser.role === "admin");

  if (!schedules.length) {
    body.innerHTML = emptyRow(7, "Không có lịch phù hợp", "Hãy thử đổi bộ lọc hoặc quay lại sau.");
    return;
  }

  body.innerHTML = schedules.map((s) => {
    const amenitiesInfo = s.room_amenities ? `<br><small class="text-muted"><i class="bi bi-info-circle me-1"></i>Tiện ích: ${s.room_amenities}</small>` : "";

    let actionBtn = "";
    if (canViewStudents) {
      const className = (s.gym_class_name || "").replace(/\\/g, "\\\\").replace(/'/g, "\\'");
      const startLabel = formatDateTime(s.start_time).replace(/\\/g, "\\\\").replace(/'/g, "\\'");
      actionBtn = `<button class="btn btn-sm btn-outline-brand" onclick="openScheduleStudentsModal(${s.id}, '${className}', '${startLabel}')">Xem học viên</button>`;
    } else if (s.status === "open" && s.available_slots > 0) {
      actionBtn = `<button class="btn btn-sm btn-brand" onclick="bookSchedule(${s.id})">Đặt lịch</button>`;
    } else if (s.status === "full" || (s.status === "open" && s.available_slots <= 0)) {
      actionBtn = `<button class="btn btn-sm btn-warning text-dark fw-bold" onclick="bookSchedule(${s.id})">Vào hàng chờ</button>`;
    } else {
      actionBtn = `<button class="btn btn-sm btn-secondary" disabled>Không khả dụng</button>`;
    }

    return `
      <tr>
        <td><strong>${s.gym_class_name}</strong></td>
        <td>${s.trainer_name || '<span class="text-muted">Chưa phân công</span>'}</td>
        <td>
          <strong>${s.room_name}</strong>
          ${amenitiesInfo}
        </td>
        <td>${formatDateTime(s.start_time)}</td>
        <td>${s.available_slots}/${s.max_participants}</td>
        <td>${statusBadge(s.available_slots <= 0 && s.status === "open" ? "full" : s.status)}</td>
        <td>${actionBtn}</td>
      </tr>
    `;
  }).join("");
  fixVietnameseTextNodes(body);
}

async function openScheduleStudentsModal(scheduleId, className, dateTimeLabel) {
  const currentUser = JSON.parse(localStorage.getItem("gymUser") || "null");
  if (!currentUser || (currentUser.role !== "trainer" && currentUser.role !== "admin")) {
    showAlert("Bạn không có quyền xem danh sách học viên.", "warning");
    return;
  }

  const titleEl = document.getElementById("scheduleStudentsLabel");
  const rowsEl = document.getElementById("scheduleStudentsRows");
  const modalEl = document.getElementById("scheduleStudentsModal");
  if (!titleEl || !rowsEl || !modalEl) return;

  titleEl.textContent = `Danh sách học viên - ${className} (${dateTimeLabel})`;
  rowsEl.innerHTML = loadingRow(5);

  const modal = new bootstrap.Modal(modalEl);
  modal.show();

  const endpoint = currentUser.role === "admin"
    ? `/admin/schedules/${scheduleId}/bookings/`
    : `/trainer/schedules/${scheduleId}/bookings/`;

  try {
    const students = await apiFetch(endpoint);
    rowsEl.innerHTML = students.length ? students.map((p, index) => `
      <tr>
        <td>${index + 1}</td>
        <td>
          <strong>${p.full_name}</strong> <span class="text-muted">(@${p.username})</span>
        </td>
        <td>${p.phone || '<i class="text-muted">Chưa cập nhật</i>'}</td>
        <td><span class="status-badge status-${p.status}">${getStatusLabel(p.status)}</span></td>
        <td>
          ${p.health_notes ? `<div><span class="badge bg-danger">Sức khỏe: ${p.health_notes}</span></div>` : ""}
          ${p.fitness_goals ? `<div class="mt-1"><span class="badge bg-primary">Mục tiêu: ${p.fitness_goals}</span></div>` : ""}
        </td>
      </tr>
    `).join("") : emptyRow(5, "Chưa có học viên đăng ký");
  } catch (error) {
    rowsEl.innerHTML = `<tr><td colspan="5" class="text-center text-danger">${error.message}</td></tr>`;
  }
}
async function bookSchedule(scheduleId) {
  if (!localStorage.getItem("gymUser")) {
    location.href = "login.html";
    return;
  }
  try {
    const booking = await apiFetch("/bookings/", {
      method: "POST",
      body: JSON.stringify({ schedule: scheduleId, note: "Dat tu frontend rieng" }),
    });
    if (booking && booking.status === "waitlist") {
      showAlert("Lop hoc a ay. Ban a uoc them vao danh sach cho thanh cong!", "warning");
    } else {
      showAlert("at lich thanh cong.");
    }
  } catch (error) {
    showAlert(error.message, "danger");
  }
}

function getStatusLabel(status) {
  const english = getAppLanguage() === "en";
  const labels = english
    ? {
      pending: "Pending",
      confirmed: "Confirmed",
      cancelled: "Cancelled",
      completed: "Completed",
      no_show: "No Show",
      waitlist: "Waitlist",
    }
    : {
      pending: "Cho xac nhan",
      confirmed: "Da xac nhan",
      cancelled: "Da huy",
      completed: "Hoan thanh",
      no_show: "Vang mat",
      waitlist: "Danh sach cho",
    };
  return labels[status] || status;
}

function setupStarRating() {
  document.querySelectorAll(".star-btn").forEach(btn => {
    btn.onclick = function () {
      const val = parseInt(btn.getAttribute("data-value"));
      document.getElementById("reviewRating").value = val;

      document.querySelectorAll(".star-btn").forEach(s => {
        const sVal = parseInt(s.getAttribute("data-value"));
        if (sVal <= val) {
          s.classList.remove("bi-star");
          s.classList.add("bi-star-fill");
        } else {
          s.classList.remove("bi-star-fill");
          s.classList.add("bi-star");
        }
      });
    };
  });
}

function showReviewModal(gymClassId, trainerId, targetName) {
  const modalEl = document.getElementById("reviewModal");
  if (!modalEl) return;

  document.getElementById("reviewGymClassId").value = gymClassId || "";
  document.getElementById("reviewTrainerId").value = trainerId || "";
  document.getElementById("reviewTargetLabel").textContent = targetName;
  document.getElementById("reviewRating").value = "5";
  document.getElementById("reviewComment").value = "";

  document.querySelectorAll(".star-btn").forEach(s => {
    s.classList.remove("bi-star");
    s.classList.add("bi-star-fill");
  });

  setupStarRating();

  let modal = bootstrap.Modal.getInstance(modalEl);
  if (modal) {
    modal.dispose();
  }
  modal = new bootstrap.Modal(modalEl, {
    backdrop: 'static',
    keyboard: false
  });
  modal.show();
}

async function submitReview(event) {
  event.preventDefault();
  const form = event.target;
  const gym_class = form.gym_class_id.value ? parseInt(form.gym_class_id.value) : null;
  const trainer = form.trainer_id.value ? parseInt(form.trainer_id.value) : null;
  const rating = parseInt(form.rating.value);
  const comment = form.comment.value;

  try {
    await apiFetch("/reviews/", {
      method: "POST",
      body: JSON.stringify({ gym_class, trainer, rating, comment })
    });

    const modalEl = document.getElementById("reviewModal");
    const modal = bootstrap.Modal.getInstance(modalEl);
    if (modal) {
      modal.hide();
    }
    form.reset();

    showAlert("Da gui danh gia thanh cong. Cam on y kien cua ban!");
  } catch (err) {
    showAlert("Loi gui danh gia: " + err.message, "danger");
  }
}


async function cancelBooking(id) {
  const reason = prompt("Vui long nhap ly do huy lich tap:");
  if (reason === null) return; // User clicked Cancel in the prompt dialog
  try {
    await apiFetch(`/bookings/${id}/cancel/`, {
      method: "POST",
      body: JSON.stringify({ cancellation_reason: reason }),
    });
    showAlert("Da huy lich.");
    loadMyBookings();
  } catch (error) {
    showAlert(error.message, "danger");
  }
}

async function cancelTrainerBooking(id) {
  const reason = prompt("Vui long nhap ly do huy lich 1-1:");
  if (reason === null) return;
  try {
    await apiFetch(`/trainer-bookings/${id}/cancel/`, {
      method: "POST",
      body: JSON.stringify({ cancellation_reason: reason }),
    });
    showAlert("Da huy lich 1-1.");
    loadMyBookings();
  } catch (error) {
    showAlert(error.message, "danger");
  }
}

async function cancelTrainerMonthlyBooking(id) {
  const reason = prompt("Vui long nhap ly do huy dang ky HLV theo thang:");
  if (reason === null) return;
  try {
    await apiFetch(`/trainer-monthly-bookings/${id}/cancel/`, {
      method: "POST",
      body: JSON.stringify({ cancellation_reason: reason }),
    });
    showAlert("Da huy dang ky HLV theo thang.");
    loadMyBookings();
  } catch (error) {
    showAlert(error.message, "danger");
  }
}

async function loadMyBookings() {
  const body = document.querySelector("#bookingRows");
  if (!body) return;
  const english = getAppLanguage() === "en";
  try {
    const [classBookings, trainerBookings, monthlyBookings] = await Promise.all([
      apiFetch("/bookings/my/"),
      apiFetch("/trainer-bookings/my/"),
      apiFetch("/trainer-monthly-bookings/my/"),
    ]);
    const bookings = [
      ...classBookings.map((item) => ({ ...item, booking_type: "class" })),
      ...trainerBookings.map((item) => ({ ...item, booking_type: "trainer" })),
      ...monthlyBookings.map((item) => ({ ...item, booking_type: "trainer_monthly", start_time: item.start_date })),
    ].sort((a, b) => new Date(a.start_time) - new Date(b.start_time));

    body.innerHTML = bookings.length ? bookings.map((b) => {
      let actionHtml = "";
      if (["pending", "confirmed", "waitlist"].includes(b.status)) {
        actionHtml = b.booking_type === "trainer_monthly"
          ? `<button class="btn btn-sm btn-action-delete" onclick="cancelTrainerMonthlyBooking(${b.id})">${english ? "Cancel" : "Huy"}</button>`
          : b.booking_type === "trainer"
            ? `<button class="btn btn-sm btn-action-delete" onclick="cancelTrainerBooking(${b.id})">${english ? "Cancel" : "Huy"}</button>`
            : `<button class="btn btn-sm btn-action-delete" onclick="cancelBooking(${b.id})">${english ? "Cancel" : "Huy"}</button>`;
      } else if (b.status === "completed") {
        actionHtml = b.booking_type === "trainer"
          ? `<button class="btn btn-sm btn-action-edit py-0 px-2 small" onclick="showReviewModal(null, ${b.trainer}, 'HLV: ${b.trainer_name || "Huan luyen vien"}')">${english ? "Rate Trainer" : "Danh gia HLV"}</button>`
          : `
            <div class="d-flex gap-1">
              <button class="btn btn-sm btn-brand py-0 px-2 small" onclick="showReviewModal(${b.gym_class_id}, null, 'Lop hoc: ${b.schedule_name}')">${english ? "Rate Class" : "Danh gia Lop"}</button>
              <button class="btn btn-sm btn-action-edit py-0 px-2 small" onclick="showReviewModal(null, ${b.trainer_id}, 'HLV: ${b.trainer_name || "Huan luyen vien"}')">${english ? "Rate Trainer" : "Danh gia HLV"}</button>
            </div>
          `;
      }
      const bookingName = b.booking_type === "trainer_monthly"
        ? `<span class="badge bg-success me-1">${english ? "Monthly" : "Thang"}</span> HLV: ${b.trainer_name || ""}<br><small>${b.sessions_per_week} ${english ? "sessions/week" : "buoi/tuan"}, ${b.months} ${english ? "month(s)" : "thang"}</small>`
        : b.booking_type === "trainer"
          ? `<span class="badge bg-dark me-1">1-1</span> HLV: ${b.trainer_name || ""}`
          : `<span class="badge bg-brand me-1">${english ? "Class" : "Lop"}</span> ${b.schedule_name}`;
      const timeText = b.booking_type === "trainer_monthly"
        ? `${new Date(b.start_date).toLocaleDateString("vi-VN")} - ${new Date(b.end_date).toLocaleDateString("vi-VN")}`
        : new Date(b.start_time).toLocaleString("vi-VN");
      return `
        <tr>
          <td><strong class="text-brand">${b.booking_code}</strong></td>
          <td>${bookingName}</td>
          <td>${timeText}</td>
          <td><span class="status-badge status-${b.status}">${getStatusLabel(b.status)}</span></td>
          <td>${actionHtml}</td>
        </tr>
      `;
    }).join("") : `<tr><td colspan="5" class="text-center text-muted">${english ? "No bookings found." : "Chua co lich tap nao."}</td></tr>`;
  } catch (error) {
    showAlert(english ? "Please log in to view your bookings." : "Ban can dang nhap de xem lich.", "warning");
  }
}

async function handleLogin(event) {
  event.preventDefault();
  const form = event.currentTarget;
  try {
    const user = await apiFetch("/auth/login/", {
      method: "POST",
      body: JSON.stringify({
        username: form.username.value,
        password: form.password.value,
      }),
    });
    localStorage.setItem("gymUser", JSON.stringify(user));
    if (typeof markUserActivity === "function") {
      markUserActivity(true);
    }

    const next = new URLSearchParams(location.search).get("next");
    if (next) {
      location.href = next;
    } else if (user.role === "admin") {
      location.href = "admin-dashboard.html";
    } else if (user.role === "trainer") {
      location.href = "trainer-dashboard.html";
    } else {
      location.href = "index.html";
    }
  } catch (error) {
    showAlert(error.message, "danger");
  }
}

async function handleRegister(event) {
  event.preventDefault();
  const form = event.currentTarget;
  if (form.password.value !== form.password_confirm.value) {
    showAlert("Mat khau nhap lai khong khop.", "danger");
    return;
  }
  try {
    await apiFetch("/auth/register/", {
      method: "POST",
      body: JSON.stringify({
        username: form.username.value,
        email: form.email.value,
        password: form.password.value,
        first_name: form.full_name.value,
        role: form.role.value,
      }),
    });
    showAlert("ang ky thanh cong. Ban co the ang nhap.", "success");
    setTimeout(() => location.href = "login.html", 900);
  } catch (error) {
    showAlert(error.message, "danger");
  }
}

// =========================================================================
// ADMIN DASHBOARD LOGIC
// =========================================================================

async function loadAdminBookings() {
  const container = document.querySelector("#adminBookingRows");
  if (!container) return;
  try {
    const bookings = await apiFetch("/admin/bookings/");
    container.innerHTML = bookings.length ? bookings.map((b) => {
      const dateStr = new Date(b.start_time).toLocaleString("vi-VN");
      return `
        <tr>
          <td><strong class="text-brand">${b.booking_code}</strong></td>
          <td>${b.user_username}</td>
          <td>
            <strong>${b.schedule_name}</strong><br>
            <small class="text-muted">${dateStr}</small>
          </td>
          <td><span class="status-badge status-${b.status}">${b.status}</span></td>
          <td>${b.note || "-"}</td>
          <td>
            <div class="btn-group gap-1">
              ${b.status === "pending" ? `<button class="btn btn-sm btn-success" onclick="changeBookingStatus(${b.id}, 'confirmed')">Xac nhan</button>` : ""}
              ${["pending", "confirmed"].includes(b.status) ? `<button class="btn btn-sm btn-outline-danger" onclick="changeBookingStatus(${b.id}, 'cancelled')">Hay</button>` : ""}
              ${b.status === "confirmed" ? `<button class="btn btn-sm btn-primary" onclick="changeBookingStatus(${b.id}, 'completed')">Hoan thanh</button>` : ""}
              ${b.status === "confirmed" ? `<button class="btn btn-sm btn-warning text-dark" onclick="changeBookingStatus(${b.id}, 'no_show')">Vang mat</button>` : ""}
            </div>
          </td>
        </tr>
      `;
    }).join("") : `<tr><td colspan="6" class="text-center text-muted">Khong co du lieu at lich.</td></tr>`;
  } catch (err) {
    showAlert("Khong the tai danh sach at lich: " + err.message, "danger");
  }
}

async function changeBookingStatus(bookingId, status) {
  if (!confirm(`Ban muon oi trang thai at lich nay thanh "${status}"?`)) return;
  try {
    await apiFetch(`/admin/bookings/${bookingId}/status/`, {
      method: "POST",
      body: JSON.stringify({ status })
    });
    showAlert("Cap nhat trang thai thanh cong!");
    loadAdminBookings();
  } catch (err) {
    showAlert(err.message, "danger");
  }
}

async function loadAdminTrainerStudents() {
  const container = document.querySelector("#adminTrainerStudentRows");
  if (!container) return;
  try {
    const bookings = await apiFetch("/admin/trainer-monthly-bookings/");
    container.innerHTML = bookings.length ? bookings.map((b) => `
      <tr>
        <td><strong class="text-brand">${b.booking_code}</strong></td>
        <td>
          <strong>${b.full_name || b.user_username}</strong><br>
          <small class="text-muted">${b.phone || "Chua cap nhat SDT"}</small>
        </td>
        <td>${b.trainer_name}</td>
        <td>${new Date(b.start_date).toLocaleDateString("vi-VN")} - ${new Date(b.end_date).toLocaleDateString("vi-VN")}</td>
        <td>${b.sessions_per_week} buoi/tuan trong ${b.months} thang</td>
        <td><span class="status-badge status-${b.status}">${getStatusLabel(b.status)}</span></td>
        <td>
          <div class="btn-group gap-1">
            ${b.status === "pending" ? `<button class="btn btn-sm btn-success" onclick="updateAdminTrainerMonthlyStatus(${b.id}, 'confirmed')">Xac nhan</button>` : ""}
            ${["pending", "confirmed"].includes(b.status) ? `<button class="btn btn-sm btn-outline-danger" onclick="updateAdminTrainerMonthlyStatus(${b.id}, 'cancelled')">Huy</button>` : ""}
            ${b.status === "confirmed" ? `<button class="btn btn-sm btn-primary" onclick="updateAdminTrainerMonthlyStatus(${b.id}, 'completed')">Hoan thanh</button>` : ""}
          </div>
        </td>
      </tr>
    `).join("") : `<tr><td colspan="7" class="text-center text-muted">Chua co hoc vien dang ky HLV theo thang.</td></tr>`;
  } catch (err) {
    showAlert("Khong the tai danh sach hoc vien HLV: " + err.message, "danger");
  }
}

async function updateAdminTrainerMonthlyStatus(bookingId, status) {
  try {
    await apiFetch(`/admin/trainer-monthly-bookings/${bookingId}/status/`, {
      method: "POST",
      body: JSON.stringify({ status }),
    });
    showAlert("Cap nhat dang ky HLV theo thang thanh cong.");
    loadAdminTrainerStudents();
  } catch (err) {
    showAlert(err.message, "danger");
  }
}

async function loadAdminPayments() {
  const container = document.querySelector("#adminPaymentRows");
  if (!container) return;
  try {
    const payments = await apiFetch("/admin/payments/");
    container.innerHTML = payments.length ? payments.map((p) => {
      const dateStr = new Date(p.created_at).toLocaleString("vi-VN");
      return `
        <tr>
          <td><code class="text-dark font-monospace">${p.transaction_code || "#" + p.id}</code></td>
          <td>${p.payment_title || p.package_name || "-"}</td>
          <td><strong class="text-danger">${money(p.amount)}</strong></td>
          <td><span class="badge bg-secondary text-uppercase">${p.payment_method}</span></td>
          <td><span class="status-badge status-${p.status}">${p.status}</span></td>
          <td><small class="text-muted">${dateStr}</small></td>
          <td>
            ${p.status === "pending" ? `<button class="btn btn-sm btn-brand" onclick="confirmAdminPayment(${p.id})">Duyet thanh toan</button>` : `<span class="text-success"><i class="bi bi-check-circle"></i> a duyet</span>`}
          </td>
        </tr>
      `;
    }).join("") : `<tr><td colspan="7" class="text-center text-muted">Khong co du lieu thanh toan.</td></tr>`;
  } catch (err) {
    showAlert("Khong the tai danh sach thanh toan: " + err.message, "danger");
  }
}

async function confirmAdminPayment(paymentId) {
  if (!confirm("Xac nhan a nhan tien va kich hoat goi tap nay?")) return;
  try {
    await apiFetch(`/admin/payments/${paymentId}/confirm/`, {
      method: "POST",
      body: "{}"
    });
    showAlert("Duyet thanh toan thanh cong!");
    loadAdminPayments();
  } catch (err) {
    showAlert(err.message, "danger");
  }
}

// =========================================================================
// TRAINER DASHBOARD LOGIC
// =========================================================================

async function loadTrainerSchedules() {
  const container = document.querySelector("#trainerScheduleRows");
  if (!container) return;
  try {
    const schedules = await apiFetch("/trainer/schedules/");
    container.innerHTML = schedules.length ? schedules.map((s) => {
      const dateStr = new Date(s.start_time).toLocaleString("vi-VN");
      return `
        <tr>
          <td><strong>${s.gym_class_name}</strong></td>
          <td>${s.room_name}</td>
          <td>${dateStr}</td>
          <td>${s.current_participants}/${s.max_participants}</td>
          <td><span class="status-badge status-${s.status}">${s.status}</span></td>
          <td>
            <button class="btn btn-sm btn-outline-brand" onclick="loadScheduleParticipants(${s.id}, '${s.gym_class_name}', '${dateStr}')">Xem danh sach</button>
          </td>
        </tr>
      `;
    }).join("") : `<tr><td colspan="6" class="text-center text-muted">Khong co lich giang day nao uoc phan cong.</td></tr>`;
  } catch (err) {
    showAlert("Khong the tai lich giang day: " + err.message, "danger");
  }
}

async function loadTrainerPersonalBookings() {
  const container = document.querySelector("#trainerPersonalBookingRows");
  if (!container) return;
  try {
    const bookings = await apiFetch("/trainer/personal-bookings/");
    container.innerHTML = bookings.length ? bookings.map((b) => `
      <tr>
        <td>
          <strong>${b.full_name || b.user_username}</strong><br>
          <small class="text-muted">${b.phone || "Chua cap nhat SDT"}</small>
        </td>
        <td>${new Date(b.start_time).toLocaleString("vi-VN")}</td>
        <td>${new Date(b.end_time).toLocaleTimeString("vi-VN", { hour: "2-digit", minute: "2-digit" })}</td>
        <td><span class="status-badge status-${b.status}">${getStatusLabel(b.status)}</span></td>
        <td>${b.note || ""}</td>
        <td>
          <div class="btn-group gap-1">
            <button class="btn btn-sm btn-success px-2 py-0" onclick="updateTrainerPersonalBookingStatus(${b.id}, 'completed')">Hoan thanh</button>
            <button class="btn btn-sm btn-outline-danger px-2 py-0" onclick="updateTrainerPersonalBookingStatus(${b.id}, 'no_show')">Vang</button>
          </div>
        </td>
      </tr>
    `).join("") : `<tr><td colspan="6" class="text-center text-muted">Chua co lich 1-1 nao.</td></tr>`;
  } catch (err) {
    container.innerHTML = `<tr><td colspan="6" class="text-center text-danger">${err.message}</td></tr>`;
  }
}

async function updateTrainerPersonalBookingStatus(bookingId, status) {
  try {
    await apiFetch(`/trainer/personal-bookings/${bookingId}/status/`, {
      method: "POST",
      body: JSON.stringify({ status }),
    });
    showAlert("Cap nhat lich 1-1 thanh cong.");
    loadTrainerPersonalBookings();
  } catch (err) {
    showAlert(err.message, "danger");
  }
}

async function loadTrainerMonthlyStudents() {
  const container = document.querySelector("#trainerMonthlyStudentRows");
  if (!container) return;
  try {
    const bookings = await apiFetch("/trainer/monthly-bookings/");
    container.innerHTML = bookings.length ? bookings.map((b) => `
      <tr>
        <td>
          <strong>${b.full_name || b.user_username}</strong><br>
          <small class="text-muted">${b.phone || "Chua cap nhat SDT"}</small>
          ${b.fitness_goals ? `<div class="small text-secondary">Muc tieu: ${b.fitness_goals}</div>` : ""}
        </td>
        <td>${new Date(b.start_date).toLocaleDateString("vi-VN")} - ${new Date(b.end_date).toLocaleDateString("vi-VN")}</td>
        <td>${b.sessions_per_week} buoi/tuan, ${b.months} thang</td>
        <td>${b.preferred_time || "-"}</td>
        <td><span class="status-badge status-${b.status}">${getStatusLabel(b.status)}</span></td>
        <td>
          <div class="btn-group gap-1">
            ${b.status === "pending" ? `<button class="btn btn-sm btn-success px-2 py-0" onclick="updateTrainerMonthlyStatus(${b.id}, 'confirmed')">Xac nhan</button>` : ""}
            ${["pending", "confirmed"].includes(b.status) ? `<button class="btn btn-sm btn-outline-danger px-2 py-0" onclick="updateTrainerMonthlyStatus(${b.id}, 'cancelled')">Huy</button>` : ""}
            ${b.status === "confirmed" ? `<button class="btn btn-sm btn-primary px-2 py-0" onclick="updateTrainerMonthlyStatus(${b.id}, 'completed')">Hoan thanh</button>` : ""}
          </div>
        </td>
      </tr>
    `).join("") : `<tr><td colspan="6" class="text-center text-muted">Chua co hoc vien dang ky theo thang.</td></tr>`;
  } catch (err) {
    container.innerHTML = `<tr><td colspan="6" class="text-center text-danger">${err.message}</td></tr>`;
  }
}

async function updateTrainerMonthlyStatus(bookingId, status) {
  try {
    await apiFetch(`/trainer/monthly-bookings/${bookingId}/status/`, {
      method: "POST",
      body: JSON.stringify({ status }),
    });
    showAlert("Cap nhat hoc vien theo thang thanh cong.");
    loadTrainerMonthlyStudents();
  } catch (err) {
    showAlert(err.message, "danger");
  }
}

async function loadScheduleParticipants(scheduleId, className, dateTimeStr) {
  const modalTitle = document.querySelector("#participantModalLabel");
  const container = document.querySelector("#participantRows");

  if (modalTitle) modalTitle.textContent = `Danh sach hoc vien - ${className} (${dateTimeStr})`;
  if (!container) return;

  // Store these for reloading roster later
  window.currentRosterScheduleId = scheduleId;
  window.currentRosterClassName = className;
  window.currentRosterDateTime = dateTimeStr;

  container.innerHTML = `<tr><td colspan="5" class="text-center"><div class="spinner-border spinner-border-sm text-brand"></div> ang tai...</td></tr>`;

  // Show modal using Bootstrap if exists
  const modalEl = document.getElementById("participantModal");
  if (modalEl) {
    let modal = bootstrap.Modal.getInstance(modalEl);
    if (modal) {
      modal.dispose();
    }
    modal = new bootstrap.Modal(modalEl);
    modal.show();
  }

  try {
    const participants = await apiFetch(`/trainer/schedules/${scheduleId}/bookings/`);
    container.innerHTML = participants.length ? participants.map((p, idx) => `
      <tr>
        <td>${idx + 1}</td>
        <td>
          <strong>${p.full_name}</strong> <span class="text-muted">(@${p.username})</span>
          ${p.health_notes || p.fitness_goals ? `
            <div class="mt-1 small">
              ${p.health_notes ? `<span class="badge bg-danger me-1">Suc khoe: ${p.health_notes}</span>` : ''}
              ${p.fitness_goals ? `<span class="badge bg-primary">Muc tieu: ${p.fitness_goals}</span>` : ''}
            </div>
          ` : ''}
          ${p.emergency_contact_name || p.emergency_contact_phone ? `
            <div class="mt-1 small text-secondary">
              Lien he khan cap: ${p.emergency_contact_name || '-'} (${p.emergency_contact_phone || '-'})
            </div>
          ` : ''}
        </td>
        <td>${p.phone || '<i class="text-muted">Chua cap nhat</i>'}</td>
        <td><span class="status-badge status-${p.status}">${getStatusLabel(p.status)}</span></td>
        <td>
          <div class="btn-group gap-1">
            <button class="btn btn-sm btn-success px-2 py-0" onclick="markAttendance(${p.id}, 'completed')">Co mat</button>
            <button class="btn btn-sm btn-outline-danger px-2 py-0" onclick="markAttendance(${p.id}, 'no_show')">Vang mat</button>
          </div>
        </td>
      </tr>
    `).join("") : `<tr><td colspan="5" class="text-center text-muted">Chua co hoc vien nao at lich nay.</td></tr>`;
  } catch (err) {
    container.innerHTML = `<tr><td colspan="5" class="text-center">Lai: ${err.message}</td></tr>`;
  }
}

async function markAttendance(bookingId, status) {
  try {
    await apiFetch(`/trainer/bookings/${bookingId}/attendance/`, {
      method: "POST",
      body: JSON.stringify({ status }),
    });
    showAlert("iem danh hoc vien thanh cong!");
    if (window.currentRosterScheduleId) {
      loadScheduleParticipants(window.currentRosterScheduleId, window.currentRosterClassName, window.currentRosterDateTime);
    }
  } catch (err) {
    showAlert("Loi iem danh: " + err.message, "danger");
  }
}

async function loadTrainerReviews() {
  const container = document.querySelector("#trainerReviewList");
  if (!container) return;
  try {
    const reviews = await apiFetch("/trainer/reviews/");
    if (!reviews || !reviews.length) {
      container.innerHTML = `<p class="text-muted">Chua co anh gia nao tu hoc vien.</p>`;
      return;
    }
    container.innerHTML = reviews.map(r => `
      <div class="col-md-6">
        <div class="border rounded p-3 bg-white h-100 shadow-sm">
          <div class="d-flex justify-content-between mb-2">
            <strong class="text-dark">Hoc vien: @${r.user_username}</strong>
            <span class="text-warning">${"".repeat(r.rating)}${"".repeat(5 - r.rating)}</span>
          </div>
          <p class="mb-1 text-secondary">${r.comment || '<span class="text-muted italic">Khong co nhan xet</span>'}</p>
          <small class="text-muted">${new Date(r.created_at).toLocaleDateString("vi-VN")}</small>
        </div>
      </div>
    `).join("");
  } catch (err) {
    container.innerHTML = `<p class="text-danger">Loi tai anh gia: ${err.message}</p>`;
  }
}


function classCard(item) {
  return `<div class="col-md-6 col-lg-4">
    <div class="card-ui">
      ${classVisual(item)}
      <div class="p-4">
        <span class="tag">${item.category_name || ""}</span>
        <h5 class="mt-3 mb-2 fw-bold">${item.name}</h5>
        <p class="text-muted mb-2">HLV: ${item.trainer_name || "Chưa phân công"}</p>
        <div class="d-flex flex-wrap gap-2 mb-3">
          <span class="badge-soft">${item.difficulty_level || "Cơ bản"}</span>
          <span class="badge-soft">${item.duration_minutes || 60} phút</span>
        </div>
        <a href="schedules.html" class="btn btn-outline-brand w-100">Xem lịch</a>
      </div>
    </div>
  </div>`;
}

function escapeJsString(value) {
  return String(value || "").replace(/\\/g, "\\\\").replace(/'/g, "\\'");
}

function toDatetimeLocalValue(date) {
  const pad = (number) => String(number).padStart(2, "0");
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}T${pad(date.getHours())}:${pad(date.getMinutes())}`;
}

function trainerCard(item) {
  const certs = item.certifications ? `<p class="small text-brand mb-1 fw-bold">Bằng cấp: ${item.certifications}</p>` : "";
  const avatar = item.image
    ? `<img class="trainer-img mb-3" src="${imageUrl(item.image, defaultAvatar)}" alt="${item.name}">`
    : `<div class="trainer-avatar">${getInitials(item.name)}</div>`;
  return `<div class="col-md-6 col-lg-4">
    <div class="card-ui text-center p-4">
      ${avatar}
      <h5 class="fw-bold">${item.name}</h5>
      <p class="text-secondary mb-1">${item.specialty}</p>
      <div class="trainer-meta">
        <div class="trainer-meta-item"><small>Kinh nghiệm</small><strong>${item.experience_years || 0} năm</strong></div>
        <div class="trainer-meta-item"><small>Lớp phụ trách</small><strong>${item.class_count || item.classes_count || 0}</strong></div>
      </div>
      ${certs}
      <div class="d-grid gap-2 mt-3">
        <button class="btn btn-brand" onclick="openTrainerBookingModal(${item.id}, '${escapeJsString(item.name)}')">Đặt lịch 1-1</button>
        <button class="btn btn-outline-brand" type="button" onclick="showTrainerDetail(${item.id})">Xem chi tiết</button>
      </div>
    </div>
  </div>`;
}

async function showTrainerDetail(trainerId) {
  try {
    let modalEl = document.getElementById("trainerDetailModal");
    if (!modalEl) {
      modalEl = document.createElement("div");
      modalEl.id = "trainerDetailModal";
      modalEl.className = "modal fade";
      modalEl.setAttribute("tabindex", "-1");
      modalEl.setAttribute("aria-hidden", "true");
      modalEl.innerHTML = `
        <div class="modal-dialog modal-dialog-centered modal-lg">
          <div class="modal-content border-0 shadow-lg" style="border-radius: var(--radius);">
            <div class="modal-header bg-dark text-white py-3">
              <h5 class="modal-title fw-bold">Thông tin chi tiết HLV</h5>
              <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal" aria-label="Close"></button>
            </div>
            <div class="modal-body" id="trainerDetailModalBody">
              <div class="text-center py-5">
                <div class="spinner-border text-brand" role="status">
                  <span class="visually-hidden">Đang tải...</span>
                </div>
              </div>
            </div>
            <div class="modal-footer bg-light py-2">
              <button type="button" class="btn btn-secondary btn-sm" data-bs-dismiss="modal">Đóng</button>
              <button type="button" class="btn btn-brand btn-sm" id="btnBookTrainerFromDetail">Đặt lịch 1-1</button>
            </div>
          </div>
        </div>
      `;
      document.body.appendChild(modalEl);
    }

    let modal = bootstrap.Modal.getInstance(modalEl);
    if (!modal) {
      modal = new bootstrap.Modal(modalEl);
    }

    // Reset body to loading spinner before opening/fetching
    const bodyEl = document.getElementById("trainerDetailModalBody");
    bodyEl.innerHTML = `
      <div class="text-center py-5">
        <div class="spinner-border text-brand" role="status">
          <span class="visually-hidden">Đang tải...</span>
        </div>
      </div>
    `;

    modal.show();

    // Fetch trainer details and reviews
    const [trainer, reviews] = await Promise.all([
      apiFetch(`/trainers/${trainerId}/`),
      apiFetch(`/trainers/${trainerId}/reviews/`).catch(() => [])
    ]);

    const avatar = trainer.image
      ? `<img class="trainer-img mb-3" src="${imageUrl(trainer.image, defaultAvatar)}" alt="${trainer.name}">`
      : `<div class="trainer-avatar mb-3">${getInitials(trainer.name)}</div>`;

    const certsHtml = trainer.certifications
      ? trainer.certifications.split('\n').filter(c => c.trim()).map(c => `<span class="badge-soft mb-2 me-2" style="font-size: 0.85rem; padding: 6px 12px;">${c}</span>`).join('')
      : `<span class="text-muted small">Chưa cập nhật bằng cấp</span>`;

    let reviewsHtml = "";
    if (reviews && reviews.length > 0) {
      reviewsHtml = reviews.map(r => {
        const stars = "★".repeat(r.rating) + "☆".repeat(5 - r.rating);
        const dateStr = new Date(r.created_at).toLocaleDateString("vi-VN");
        return `
          <div class="border-bottom pb-2 mb-2">
            <div class="d-flex justify-content-between mb-1">
              <strong class="text-dark">@${r.user_username}</strong>
              <span class="text-warning" style="font-size: 0.9rem;">${stars}</span>
            </div>
            <p class="mb-1 text-secondary small">${r.comment || "<i>Không có nhận xét</i>"}</p>
            <small class="text-muted" style="font-size: 0.75rem;">${dateStr}</small>
          </div>
        `;
      }).join("");
    } else {
      reviewsHtml = `<p class="text-muted small italic my-3 text-center">Chưa có đánh giá nào từ học viên</p>`;
    }

    bodyEl.innerHTML = `
      <div class="row g-4">
        <!-- Left Side: Profile Card & Basic Info -->
        <div class="col-md-5 text-center border-end">
          <div class="d-flex flex-column align-items-center h-100 p-2">
            ${avatar}
            <h4 class="fw-bold mt-2 mb-1">${trainer.name}</h4>
            <p class="text-secondary mb-3">${trainer.specialty}</p>
            
            <div class="w-100 bg-light rounded-3 p-3 mb-3 text-start">
              <div class="d-flex justify-content-between mb-2">
                <span class="text-muted"><i class="bi bi-star-fill text-warning me-1"></i> Kinh nghiệm:</span>
                <strong>${trainer.experience_years || 0} năm</strong>
              </div>
              <div class="d-flex justify-content-between mb-0">
                <span class="text-muted"><i class="bi bi-cash-stack text-success me-1"></i> Giá buổi tập:</span>
                <strong class="text-brand">${money(trainer.session_price || 0)}</strong>
              </div>
            </div>
            
            <div class="w-100 text-start pt-2 border-top">
              <p class="mb-2 text-truncate small">
                <i class="bi bi-envelope-fill text-muted me-2"></i>
                <a href="mailto:${trainer.email}" class="text-secondary">${trainer.email}</a>
              </p>
              <p class="mb-0 small">
                <i class="bi bi-telephone-fill text-muted me-2"></i>
                <a href="tel:${trainer.phone}" class="text-secondary">${trainer.phone || "Chưa cập nhật"}</a>
              </p>
            </div>
          </div>
        </div>
        
        <!-- Right Side: Bio, Certifications, and Reviews -->
        <div class="col-md-7">
          <div class="p-2">
            <h5 class="fw-bold mb-2 text-dark"><i class="bi bi-person-lines-fill text-brand me-2"></i>Giới thiệu bản thân</h5>
            <p class="text-secondary small mb-4" style="line-height: 1.6; white-space: pre-line;">
              ${trainer.bio || "Không có giới thiệu nào từ huấn luyện viên này."}
            </p>
            
            <h5 class="fw-bold mb-2 text-dark"><i class="bi bi-award-fill text-brand me-2"></i>Bằng cấp & Chứng chỉ</h5>
            <div class="d-flex flex-wrap mb-4">
              ${certsHtml}
            </div>
            
            <h5 class="fw-bold mb-2 text-dark"><i class="bi bi-chat-left-heart-fill text-brand me-2"></i>Đánh giá từ học viên</h5>
            <div class="trainer-reviews-container overflow-y-auto px-1" style="max-height: 180px;">
              ${reviewsHtml}
            </div>
          </div>
        </div>
      </div>
    `;

    // Hook up booking button in detail modal
    const bookBtn = document.getElementById("btnBookTrainerFromDetail");
    if (bookBtn) {
      bookBtn.onclick = function () {
        const modalInstance = bootstrap.Modal.getInstance(modalEl);
        if (modalInstance) modalInstance.hide();
        setTimeout(() => {
          openTrainerBookingModal(trainer.id, trainer.name);
        }, 350);
      };
    }
  } catch (err) {
    showAlert("Không thể tải thông tin chi tiết HLV: " + err.message, "danger");
  }
}

function openTrainerBookingModal(trainerId, trainerName) {
  if (!localStorage.getItem("gymUser")) {
    location.href = "login.html";
    return;
  }

  const modalEl = document.getElementById("trainerBookingModal");
  if (!modalEl) {
    location.href = "trainers.html";
    return;
  }

  document.getElementById("trainerBookingTrainerId").value = trainerId;
  document.getElementById("trainerBookingTrainerName").textContent = trainerName;

  const startInput = document.getElementById("trainerBookingStart");
  const defaultStart = new Date();
  defaultStart.setDate(defaultStart.getDate() + 1);
  defaultStart.setHours(9, 0, 0, 0);
  startInput.min = toDatetimeLocalValue(new Date());
  startInput.value = toDatetimeLocalValue(defaultStart);
  document.getElementById("trainerBookingDuration").value = "60";
  document.getElementById("trainerBookingMode").value = "single";
  document.getElementById("trainerBookingMonths").value = "1";
  document.getElementById("trainerBookingSessions").value = "3";
  document.getElementById("trainerBookingNote").value = "";

  const modal = new bootstrap.Modal(modalEl);
  modal.show();
}

async function submitTrainerBooking(event) {
  event.preventDefault();
  const form = event.target;
  const bookingMode = form.booking_mode.value;
  const startTime = new Date(form.start_time.value);
  const durationMinutes = parseInt(form.duration_minutes.value, 10);
  const endTime = new Date(startTime.getTime() + durationMinutes * 60 * 1000);

  try {
    if (bookingMode === "monthly") {
      await apiFetch("/trainer-monthly-bookings/", {
        method: "POST",
        body: JSON.stringify({
          trainer: parseInt(form.trainer_id.value, 10),
          start_date: form.start_time.value.slice(0, 10),
          months: parseInt(form.months.value, 10),
          sessions_per_week: parseInt(form.sessions_per_week.value, 10),
          preferred_time: form.start_time.value.slice(11, 16),
          note: form.note.value,
        }),
      });
      const modal = bootstrap.Modal.getInstance(document.getElementById("trainerBookingModal"));
      if (modal) modal.hide();
      showAlert("Đăng ký HLV theo tháng thành công.");
    } else {
      const booking = await apiFetch("/trainer-bookings/", {
        method: "POST",
        body: JSON.stringify({
          trainer: parseInt(form.trainer_id.value, 10),
          start_time: startTime.toISOString(),
          end_time: endTime.toISOString(),
          note: form.note.value,
        }),
      });
      const modal = bootstrap.Modal.getInstance(document.getElementById("trainerBookingModal"));
      if (modal) modal.hide();
      showAlert("Đặt lịch 1-1 với HLV thành công. Vui lòng thanh toán để kích hoạt lịch.");
      openTrainerBookingPaymentModal(booking);
    }
  } catch (error) {
    showAlert(error.message, "danger");
  }
}

function openTrainerBookingPaymentModal(booking) {
  const modalEl = document.getElementById("invoiceModal");
  const modalContent = document.getElementById("invoiceModalContent");
  if (!modalEl || !modalContent) {
    showAlert("Không tìm thấy giao diện thanh toán.", "warning");
    return;
  }

  const amount = Number(booking.trainer_session_price || 0);
  window.pendingPaymentDetails = {
    paymentType: "trainer_booking",
    trainerBookingId: booking.id,
    amount: amount,
    trainerName: booking.trainer_name || "",
    bookingCode: booking.booking_code || "",
  };

  modalContent.innerHTML = `
    <div class="p-3">
      <div class="d-flex justify-content-between mb-2">
        <span class="text-muted">Mã đặt lịch:</span>
        <strong class="font-monospace">${booking.booking_code || "-"}</strong>
      </div>
      <div class="d-flex justify-content-between mb-2">
        <span class="text-muted">Dịch vụ:</span>
        <strong>Đặt lịch 1-1 với HLV ${booking.trainer_name || ""}</strong>
      </div>
      <div class="d-flex justify-content-between mb-2">
        <span class="text-muted">Trạng thái:</span>
        <span class="badge bg-warning text-dark">Chờ thanh toán</span>
      </div>
      <hr>
      <div class="d-flex justify-content-between mb-3">
        <span class="h5 mb-0 fw-bold">Tổng thanh toán:</span>
        <span class="h5 mb-0 fw-bold text-danger">${money(amount)}</span>
      </div>

      <div class="mt-4">
        <label class="form-label fw-bold small text-uppercase text-muted">Chọn phương thức thanh toán</label>
        <div class="form-check border rounded p-3 mb-2 d-flex align-items-center">
          <input class="form-check-input ms-0 me-3" type="radio" name="paymentMethod" id="payMomo" value="momo" checked>
          <label class="form-check-label w-100 fw-bold" for="payMomo">Vi dien tu MoMo</label>
        </div>
        <div class="form-check border rounded p-3 mb-2 d-flex align-items-center">
          <input class="form-check-input ms-0 me-3" type="radio" name="paymentMethod" id="payVnPay" value="vnpay">
          <label class="form-check-label w-100 fw-bold" for="payVnPay">Cong thanh toan VNPay</label>
        </div>
        <div class="form-check border rounded p-3 mb-2 d-flex align-items-center">
          <input class="form-check-input ms-0 me-3" type="radio" name="paymentMethod" id="payBank" value="bank_transfer">
          <label class="form-check-label w-100 fw-bold" for="payBank">Chuyen khoan ngan hang</label>
        </div>
      </div>
    </div>
  `;

  let modal = bootstrap.Modal.getInstance(modalEl);
  if (modal) {
    modal.dispose();
  }
  modal = new bootstrap.Modal(modalEl, {
    backdrop: "static",
    keyboard: false,
  });
  modal.show();

  const confirmBtn = document.getElementById("btnConfirmPayment");
  if (confirmBtn) {
    confirmBtn.onclick = async function () {
      const selectedMethod = document.querySelector('input[name="paymentMethod"]:checked').value;
      await processMockPayment(selectedMethod, modal);
    };
  }
}

function packageCard(item) {
  const freezeInfo = item.is_freezable
    ? `<span class="badge-soft">Hỗ trợ tạm dừng tối đa ${item.max_freeze_days} ngày</span>`
    : `<span class="badge bg-light text-muted border">Không hỗ trợ tạm dừng</span>`;
  return `<div class="col-md-4">
    <div class="card-ui p-4 d-flex flex-column h-100 justify-content-between">
      <div>
        <span class="tag">Gói tập</span>
        <h5 class="mt-3 mb-2 fw-bold">${item.name}</h5>
        <div class="price mb-3">${money(item.price)}</div>
        <p class="text-secondary small mb-2">${item.description || ""}</p>
        <p class="mb-3">${item.duration_days} ngày • ${item.max_bookings_per_week ? item.max_bookings_per_week + " buổi/tuần" : "Không giới hạn"}</p>
        <div class="mb-3">${freezeInfo}</div>
      </div>
      ${getPackageActionButton(item.id)}
    </div>
  </div>`;
}

function getPackageActionButton(packageId) {
  const userStr = localStorage.getItem("gymUser");
  if (!userStr) {
    // Guest: show button, will redirect to login
    return `<button class="btn btn-brand w-100" onclick="registerPackage(${packageId})">Đăng ký gói</button>`;
  }
  const user = JSON.parse(userStr);
  if (user.role === "admin" || user.role === "trainer") {
    return `<button class="btn w-100" disabled>Không khả dụng</button>`;
  }

  // Check if they already have active or pending membership
  const hasActiveOrPending = window.userMemberships && window.userMemberships.some(
    m => m.status === "active" || m.status === "pending"
  );
  if (hasActiveOrPending) {
    return `<button class="btn w-100" disabled>Đã đăng ký gói</button>`;
  }

  return `<button class="btn btn-brand w-100" onclick="registerPackage(${packageId})">Đăng ký gói</button>`;
}

async function registerPackage(id) {
  const userStr = localStorage.getItem("gymUser");
  if (!userStr) {
    location.href = "login.html";
    return;
  }
  const currentUser = JSON.parse(userStr);
  if (currentUser.role === "admin" || currentUser.role === "trainer") {
    showAlert("Chi hoi vien moi co the ang ky goi tap.", "warning");
    return;
  }
  try {
    const membership = await apiFetch("/memberships/", {
      method: "POST",
      body: JSON.stringify({ package: id }),
    });

    const invoice = membership.invoice_details;
    if (!invoice) {
      showAlert("ang ky goi tap thanh cong.");
      await refreshPackagesAndMemberships();
      return;
    }

    // Check if modal elements exist on current page
    const modalEl = document.getElementById("invoiceModal");
    const modalContent = document.getElementById("invoiceModalContent");
    if (!modalEl || !modalContent) {
      // Save details to localStorage so they can be processed on packages.html load
      localStorage.setItem("pendingPaymentDetails", JSON.stringify({
        membershipId: membership.id,
        amount: invoice.total_amount,
        invoiceNumber: invoice.invoice_number,
        packageName: membership.package_name
      }));
      // Redirect to packages page where the modal exists
      showAlert("ang ky goi tap thanh cong. ang chuyen en trang thanh toan...");
      setTimeout(() => { location.href = "packages.html"; }, 800);
      return;
    }

    // Save details for mock payment
    window.pendingPaymentDetails = {
      membershipId: membership.id,
      amount: invoice.total_amount,
      invoiceNumber: invoice.invoice_number,
      packageName: membership.package_name
    };

    // Open invoice modal
    modalContent.innerHTML = `
      <div class="p-3">
        <div class="d-flex justify-content-between mb-2">
          <span class="text-muted">Mã hóa đơn:</span>
          <strong class="font-monospace">${invoice.invoice_number}</strong>
        </div>
        <div class="d-flex justify-content-between mb-2">
          <span class="text-muted">Sản phẩm:</span>
          <strong>Gói tập ${membership.package_name}</strong>
        </div>
        <div class="d-flex justify-content-between mb-2">
          <span class="text-muted">Trạng thái:</span>
          <span class="badge bg-warning text-dark">Chờ thanh toán</span>
        </div>
        <hr>
        <div class="d-flex justify-content-between mb-3">
          <span class="h5 mb-0 fw-bold">Tổng thanh toán:</span>
          <span class="h5 mb-0 fw-bold text-danger">${money(invoice.total_amount)}</span>
        </div>
        
        <div class="mt-4">
          <label class="form-label fw-bold small text-uppercase text-muted">Chọn phương thức thanh toán</label>
          <div class="form-check border rounded p-3 mb-2 d-flex align-items-center">
            <input class="form-check-input ms-0 me-3" type="radio" name="paymentMethod" id="payMomo" value="momo" checked>
            <label class="form-check-label w-100 fw-bold" for="payMomo">
               Ví điện tử MoMo
            </label>
          </div>
          <div class="form-check border rounded p-3 mb-2 d-flex align-items-center">
            <input class="form-check-input ms-0 me-3" type="radio" name="paymentMethod" id="payVnPay" value="vnpay">
            <label class="form-check-label w-100 fw-bold" for="payVnPay">
               Cong thanh toan VNPay
            </label>
          </div>
          <div class="form-check border rounded p-3 mb-2 d-flex align-items-center">
            <input class="form-check-input ms-0 me-3" type="radio" name="paymentMethod" id="payBank" value="bank_transfer">
            <label class="form-check-label w-100 fw-bold" for="payBank">
               Chuyen khoan ngan hang
            </label>
          </div>
        </div>
      </div>
    `;

    let modal = bootstrap.Modal.getInstance(modalEl);
    if (modal) {
      modal.dispose();
    }
    modal = new bootstrap.Modal(modalEl, {
      backdrop: 'static',
      keyboard: false
    });
    modal.show();

    // Hook up confirm button
    const confirmBtn = document.getElementById("btnConfirmPayment");
    if (confirmBtn) {
      confirmBtn.onclick = async function () {
        const selectedMethod = document.querySelector('input[name="paymentMethod"]:checked').value;
        await processMockPayment(selectedMethod, modal);
      };
    }
  } catch (error) {
    showAlert(error.message, "danger");
  }
}

async function processMockPayment(method, modalInstance) {
  if (!window.pendingPaymentDetails) return;
  const details = window.pendingPaymentDetails;
  try {
    let payment = null;
    if (details.paymentType === "trainer_booking") {
      payment = await apiFetch(`/trainer-bookings/${details.trainerBookingId}/payments/`, {
        method: "POST",
        body: JSON.stringify({
          payment_method: method,
        }),
      });
    } else {
      payment = await apiFetch("/payments/", {
        method: "POST",
        body: JSON.stringify({
          membership: details.membershipId,
          payment_method: method
        })
      });
    }

    await apiFetch(`/payments/${payment.id}/confirm/`, {
      method: "POST",
      body: "{}"
    });

    modalInstance.hide();
    if (details.paymentType === "trainer_booking") {
      showAlert("Thanh toan lich 1-1 thanh cong!");
      await loadMyBookings();
    } else {
      showAlert("Thanh toan hoa on thanh cong! The hoi vien a uoc kich hoat.");
      await refreshPackagesAndMemberships();
    }
  } catch (err) {
    showAlert("Loi thanh toan: " + err.message, "danger");
  }
}

async function refreshPackagesAndMemberships() {
  if (localStorage.getItem("gymUser")) {
    try {
      window.userMemberships = await apiFetch("/memberships/my/");
    } catch (err) {
      console.error("Error preloading memberships", err);
    }
  }
  await loadPackages();
  await loadMyMemberships();
}

async function initPackagesPage() {
  await refreshPackagesAndMemberships();

  // Listen to invoiceModal close to refresh list
  const modalEl = document.getElementById("invoiceModal");
  if (modalEl) {
    modalEl.addEventListener('hidden.bs.modal', function () {
      refreshPackagesAndMemberships();
    });
  }

  // Auto trigger payment modal if pending details exist in localStorage
  const pendingStr = localStorage.getItem("pendingPaymentDetails");
  if (pendingStr) {
    localStorage.removeItem("pendingPaymentDetails");
    try {
      const details = JSON.parse(pendingStr);
      payPendingMembership(details.membershipId, details.packageName, details.amount, details.invoiceNumber);
    } catch (e) {
      console.error("Error parsing pendingPaymentDetails", e);
    }
  }
}

async function loadMyMemberships() {
  const container = document.querySelector("#myMembershipRows");
  const section = document.querySelector("#myMembershipsSection");
  if (!container || !section) return;

  const user = localStorage.getItem("gymUser");
  if (!user) {
    section.classList.add("d-none");
    return;
  }

  try {
    const memberships = window.userMemberships || await apiFetch("/memberships/my/");
    window.userMemberships = memberships;
    section.classList.toggle("d-none", !memberships.length);
    if (!memberships.length) return;

    container.innerHTML = memberships.map(m => {
      const isFreezeEligible = m.status === "active" && m.is_freezable;
      return `
        <tr>
          <td><strong>${m.package_name}</strong></td>
          <td><strong class="text-danger">${money(m.package_price)}</strong></td>
          <td>${new Date(m.start_date).toLocaleDateString("vi-VN")}</td>
          <td>${new Date(m.end_date).toLocaleDateString("vi-VN")}</td>
          <td>${statusBadge(m.status)}</td>
          <td>
            <div class="d-flex gap-1">
              ${isFreezeEligible
          ? `<button class="btn btn-sm btn-warning text-dark fw-bold" onclick="showFreezeModal(${m.id})">Tạm dừng</button>`
          : ''
        }
              ${m.status === 'active'
          ? `<button class="btn btn-sm btn-action-delete" onclick="cancelActiveMembership(${m.id})">Hủy gói</button>`
          : ''
        }
              ${m.status === 'pending'
          ? `
                  <button class="btn btn-sm btn-brand fw-bold me-1" onclick="payPendingMembership(${m.id}, '${m.package_name}', ${m.package_price}, '${m.invoice_details ? m.invoice_details.invoice_number : ''}')">Thanh toán</button>
                  <button class="btn btn-sm btn-action-delete" onclick="cancelPendingMembership(${m.id})">Hủy</button>
                `
          : ''
        }
              ${m.status === 'expired' || m.status === 'cancelled' ? '<span class="text-muted small">Không khả dụng</span>' : ''}
            </div>
          </td>
        </tr>
      `;
    }).join("");
    fixVietnameseTextNodes(container);
  } catch (err) {
    console.error("Error loading my memberships", err);
  }
}

async function cancelActiveMembership(membershipId) {
  if (!confirm("Ban co chac chan muon huy goi tap nay khong?")) return;
  try {
    await apiFetch(`/memberships/${membershipId}/cancel/`, {
      method: "POST",
      body: "{}"
    });
    showAlert("a huy goi tap thanh cong.");
    await refreshPackagesAndMemberships();
  } catch (err) {
    showAlert("Loi huy goi tap: " + err.message, "danger");
  }
}

function payPendingMembership(membershipId, packageName, amount, invoiceNumber) {
  const modalEl = document.getElementById("invoiceModal");
  const modalContent = document.getElementById("invoiceModalContent");
  if (!modalEl || !modalContent) {
    showAlert("Khong tim thay giao dien thanh toan.", "danger");
    return;
  }

  window.pendingPaymentDetails = {
    membershipId: membershipId,
    amount: amount,
    invoiceNumber: invoiceNumber,
    packageName: packageName
  };

  modalContent.innerHTML = `
    <div class="p-3">
      <div class="d-flex justify-content-between mb-2">
        <span class="text-muted">Mã hóa đơn:</span>
        <strong class="font-monospace">${invoiceNumber}</strong>
      </div>
      <div class="d-flex justify-content-between mb-2">
        <span class="text-muted">Sản phẩm:</span>
        <strong>Gói tập ${packageName}</strong>
      </div>
      <div class="d-flex justify-content-between mb-2">
        <span class="text-muted">Trạng thái:</span>
        <span class="badge bg-warning text-dark">Chờ thanh toán</span>
      </div>
      <hr>
      <div class="d-flex justify-content-between mb-3">
        <span class="h5 mb-0 fw-bold">Tổng thanh toán:</span>
        <span class="h5 mb-0 fw-bold text-danger">${money(amount)}</span>
      </div>
      
      <div class="mt-4">
        <label class="form-label fw-bold small text-uppercase text-muted">Chọn phương thức thanh toán</label>
        <div class="form-check border rounded p-3 mb-2 d-flex align-items-center">
          <input class="form-check-input ms-0 me-3" type="radio" name="paymentMethod" id="payMomo" value="momo" checked>
          <label class="form-check-label w-100 fw-bold" for="payMomo">
             Vi ien tu MoMo
          </label>
        </div>
        <div class="form-check border rounded p-3 mb-2 d-flex align-items-center">
          <input class="form-check-input ms-0 me-3" type="radio" name="paymentMethod" id="payVnPay" value="vnpay">
          <label class="form-check-label w-100 fw-bold" for="payVnPay">
             Cong thanh toan VNPay
          </label>
        </div>
        <div class="form-check border rounded p-3 mb-2 d-flex align-items-center">
          <input class="form-check-input ms-0 me-3" type="radio" name="paymentMethod" id="payBank" value="bank_transfer">
          <label class="form-check-label w-100 fw-bold" for="payBank">
             Chuyen khoan ngan hang
          </label>
        </div>
      </div>
    </div>
  `;

  let modal = bootstrap.Modal.getInstance(modalEl);
  if (modal) {
    modal.dispose();
  }
  modal = new bootstrap.Modal(modalEl, {
    backdrop: 'static',
    keyboard: false
  });
  modal.show();

  // Hook up confirm button
  const confirmBtn = document.getElementById("btnConfirmPayment");
  if (confirmBtn) {
    confirmBtn.onclick = async function () {
      const selectedMethod = document.querySelector('input[name="paymentMethod"]:checked').value;
      await processMockPayment(selectedMethod, modal);
    };
  }
}

async function cancelPendingMembership(membershipId) {
  if (!confirm("Ban co chac chan muon huy ang ky goi tap nay khong?")) return;
  try {
    await apiFetch(`/memberships/${membershipId}/cancel/`, {
      method: "POST",
      body: "{}"
    });
    showAlert("a huy goi tap thanh cong.");
    await refreshPackagesAndMemberships();
  } catch (err) {
    showAlert("Loi huy goi tap: " + err.message, "danger");
  }
}

function showFreezeModal(membershipId) {
  const modalEl = document.getElementById("freezeModal");
  if (!modalEl) return;
  document.getElementById("freezeMembershipId").value = membershipId;
  let modal = bootstrap.Modal.getInstance(modalEl);
  if (modal) {
    modal.dispose();
  }
  modal = new bootstrap.Modal(modalEl, {
    backdrop: 'static',
    keyboard: false
  });
  modal.show();
}

async function submitFreeze(event) {
  event.preventDefault();
  const form = event.target;
  const membershipId = form.membership_id.value;
  const start_date = form.start_date.value;
  const end_date = form.end_date.value;
  const reason = form.reason.value;

  try {
    await apiFetch(`/memberships/${membershipId}/freeze/`, {
      method: "POST",
      body: JSON.stringify({ start_date, end_date, reason }),
    });

    const modalEl = document.getElementById("freezeModal");
    const modal = bootstrap.Modal.getInstance(modalEl);
    if (modal) {
      modal.hide();
    }
    form.reset();

    showAlert("a tam dung goi tap thanh cong. Ngay het han cua ban a uoc gia han them!");
    await refreshPackagesAndMemberships();
  } catch (err) {
    showAlert("Loi tam dung goi tap: " + err.message, "danger");
  }
}

async function loadAdminInvoices() {
  const container = document.querySelector("#adminInvoiceRows");
  if (!container) return;
  try {
    const invoices = await apiFetch("/admin/invoices/");
    container.innerHTML = invoices.length ? invoices.map((inv) => {
      const dateStr = new Date(inv.created_at).toLocaleString("vi-VN");
      const statusLabel = inv.status === 'paid' ? 'a thanh toan' : inv.status === 'unpaid' ? 'Chua thanh toan' : 'a huy';
      const statusClass = inv.status === 'paid' ? 'bg-success text-white' : 'bg-warning text-dark';

      return `
        <tr>
          <td><strong class="text-brand">${inv.invoice_number}</strong></td>
          <td>${inv.user_username || 'Hoi vien'}</td>
          <td><strong class="text-danger">${money(inv.total_amount)}</strong></td>
          <td><span class="badge ${statusClass}">${statusLabel}</span></td>
          <td><small class="text-muted">${dateStr}</small></td>
        </tr>
      `;
    }).join("") : `<tr><td colspan="5" class="text-center text-muted">Khong co du lieu hoa on.</td></tr>`;
  } catch (err) {
    container.innerHTML = `<tr><td colspan="5" class="text-center text-danger">Lai: ${err.message}</td></tr>`;
  }
}

async function loadScheduleSetupForm() {
  const classSelect = document.getElementById("schedClass");
  const roomSelect = document.getElementById("schedRoom");
  const trainerSelect = document.getElementById("schedTrainer");

  if (!classSelect || !roomSelect || !trainerSelect) return;

  try {
    const [classes, rooms, trainers] = await Promise.all([
      apiFetch("/classes/"),
      apiFetch("/rooms/"),
      apiFetch("/trainers/")
    ]);

    classSelect.innerHTML = classes.map(c => `<option value="${c.id}">${c.name}</option>`).join("");
    roomSelect.innerHTML = rooms.map(r => `<option value="${r.id}">${r.name} (Suc chua: ${r.capacity})</option>`).join("");
    trainerSelect.innerHTML = `<option value="">-- Mac inh (Theo lop hoc) --</option>` +
      trainers.map(t => `<option value="${t.id}">${t.name} (${t.specialty})</option>`).join("");

    await loadAdminScheduleList();
  } catch (err) {
    console.error("Error loading schedule setup form options", err);
  }
}

async function loadAdminScheduleList() {
  const container = document.getElementById("adminScheduleListRows");
  if (!container) return;
  try {
    const schedules = await apiFetch("/schedules/");
    container.innerHTML = schedules.length ? schedules.map(s => `
      <tr>
        <td><strong>${s.gym_class_name}</strong></td>
        <td>${s.trainer_name || '<span class="text-muted">Chưa phân công</span>'}</td>
        <td>${s.room_name}</td>
        <td><small class="text-muted">${formatDateTime(s.start_time)}</small></td>
        <td>
          <div class="btn-group gap-1">
            <button class="btn btn-sm btn-action-edit" onclick="editAdminSchedule(${s.id})">${t("edit")}</button>
            <button class="btn btn-sm btn-action-delete" onclick="deleteAdminSchedule(${s.id})">${t("delete")}</button>
          </div>
        </td>
      </tr>
    `).join("") : `<tr><td colspan="5" class="text-center text-muted">${t("no_schedule_data")}</td></tr>`;
  } catch (err) {
    container.innerHTML = `<tr><td colspan="5" class="text-center text-danger">Lỗi: ${err.message}</td></tr>`;
  }
}

let adminEditScheduleModal = null;
let adminEditTrainerModal = null;

function getAdminModalInstance(modalId) {
  const modalEl = document.getElementById(modalId);
  if (!modalEl) return null;
  return bootstrap.Modal.getOrCreateInstance(modalEl);
}

async function editAdminSchedule(scheduleId) {
  try {
    const [schedule, classes, rooms, trainers] = await Promise.all([
      apiFetch(`/schedules/${scheduleId}/`),
      apiFetch("/classes/"),
      apiFetch("/rooms/"),
      apiFetch("/trainers/"),
    ]);

    const scheduleIdInput = document.getElementById("editScheduleId");
    const classSelect = document.getElementById("editSchedClass");
    const roomSelect = document.getElementById("editSchedRoom");
    const trainerSelect = document.getElementById("editSchedTrainer");
    const startInput = document.getElementById("editSchedStart");
    const endInput = document.getElementById("editSchedEnd");
    const maxInput = document.getElementById("editSchedMax");

    if (!scheduleIdInput || !classSelect || !roomSelect || !trainerSelect || !startInput || !endInput || !maxInput) {
      showAlert("Khong tim thay form sua lich tap.", "danger");
      return;
    }

    scheduleIdInput.value = String(schedule.id);
    classSelect.innerHTML = classes.map((item) => `<option value="${item.id}">${item.name}</option>`).join("");
    roomSelect.innerHTML = rooms.map((item) => `<option value="${item.id}">${item.name}</option>`).join("");
    trainerSelect.innerHTML = `<option value="">-- Khong phan cong --</option>` + trainers.map((item) => `<option value="${item.id}">${item.name}</option>`).join("");

    classSelect.value = String(schedule.gym_class);
    roomSelect.value = String(schedule.room);
    trainerSelect.value = schedule.trainer ? String(schedule.trainer) : "";
    startInput.value = toDatetimeLocalValue(new Date(schedule.start_time));
    endInput.value = toDatetimeLocalValue(new Date(schedule.end_time));
    maxInput.value = String(schedule.max_participants || 1);

    adminEditScheduleModal = getAdminModalInstance("editScheduleModal");
    if (adminEditScheduleModal) adminEditScheduleModal.show();
  } catch (err) {
    showAlert("Khong cap nhat duoc lich tap: " + err.message, "danger");
  }
}

async function submitEditSchedule(event) {
  event.preventDefault();
  const scheduleId = parseInt(document.getElementById("editScheduleId").value, 10);
  const gymClass = parseInt(document.getElementById("editSchedClass").value, 10);
  const room = parseInt(document.getElementById("editSchedRoom").value, 10);
  const trainerRaw = document.getElementById("editSchedTrainer").value;
  const startTime = document.getElementById("editSchedStart").value;
  const endTime = document.getElementById("editSchedEnd").value;
  const maxParticipants = parseInt(document.getElementById("editSchedMax").value, 10);

  if (!scheduleId || !gymClass || !room || !startTime || !endTime || !maxParticipants || maxParticipants < 1) {
    showAlert("Du lieu sua lich tap khong hop le.", "danger");
    return;
  }

  const payload = {
    gym_class: gymClass,
    room,
    start_time: startTime,
    end_time: endTime,
    max_participants: maxParticipants,
    trainer: trainerRaw ? parseInt(trainerRaw, 10) : null,
  };

  try {
    await apiFetch(`/admin/schedules/${scheduleId}/`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    });
    if (adminEditScheduleModal) adminEditScheduleModal.hide();
    showAlert(t("update_schedule_success"));
    await loadAdminScheduleList();
  } catch (err) {
    showAlert("Khong cap nhat duoc lich tap: " + err.message, "danger");
  }
}

async function deleteAdminSchedule(scheduleId) {
  if (!confirm(t("delete_schedule_confirm"))) return;
  try {
    await apiFetch(`/admin/schedules/${scheduleId}/`, { method: "DELETE" });
    showAlert("Da xoa lich tap.");
    await loadAdminScheduleList();
  } catch (err) {
    showAlert("Khong xoa duoc lich tap: " + err.message, "danger");
  }
}

async function submitCreateSchedule(event) {
  event.preventDefault();
  const form = event.target;
  const gym_class = parseInt(form.gym_class.value);
  const room = parseInt(form.room.value);
  const trainerVal = form.trainer.value;
  const trainer = trainerVal ? parseInt(trainerVal) : null;
  const start_time = form.start_time.value;
  const end_time = form.end_time.value;
  const max_participants = parseInt(form.max_participants.value);

  const warningDiv = document.getElementById("scheduleWarning");
  if (warningDiv) {
    warningDiv.classList.add("d-none");
    warningDiv.textContent = "";
  }

  try {
    const payload = { gym_class, room, start_time, end_time, max_participants };
    if (trainer) {
      payload.trainer = trainer;
    }

    await apiFetch("/admin/schedules/create/", {
      method: "POST",
      body: JSON.stringify(payload)
    });

    showAlert("Tao lich tap moi thanh cong!");
    form.reset();
    await loadAdminScheduleList();
  } catch (err) {
    if (warningDiv) {
      warningDiv.textContent = "Canh bao trung lich: " + err.message;
      warningDiv.classList.remove("d-none");
    } else {
      showAlert(err.message, "danger");
    }
  }
}


// =========================================================================
// ADMIN: USER MANAGEMENT
// =========================================================================

function toggleTrainerFields() {
  const role = document.getElementById("userRole").value;
  const extra = document.getElementById("trainerExtraFields");
  if (extra) {
    extra.classList.toggle("d-none", role !== "trainer");
  }
}

async function submitCreateUser(event) {
  event.preventDefault();
  const form = event.target;
  const payload = {
    username: form.username.value,
    email: form.email.value,
    password: form.password.value,
    full_name: form.full_name.value,
    phone: form.phone.value,
    role: form.role.value,
  };

  if (payload.role === "trainer") {
    payload.specialty = form.specialty.value || "General";
    payload.experience_years = parseInt(form.experience_years.value) || 0;
    payload.session_price = parseFloat(form.session_price.value) || 0;
  }

  try {
    const result = await apiFetch("/admin/users/create/", {
      method: "POST",
      body: JSON.stringify(payload),
    });
    showAlert(result.message);
    form.reset();
    toggleTrainerFields();
    await loadAdminTrainerList();
  } catch (err) {
    showAlert(err.message, "danger");
  }
}

async function loadAdminTrainerList() {
  const container = document.getElementById("adminTrainerRows");
  if (!container) return;
  try {
    const trainers = await apiFetch("/admin/trainers/");
    container.innerHTML = trainers.length ? trainers.map((trainerItem) => `
      <tr>
        <td>
          <strong>${trainerItem.name}</strong><br>
          <small class="text-muted">${trainerItem.email || "-"}</small>
        </td>
        <td>${trainerItem.specialty || "-"}</td>
        <td><strong class="text-danger">${money(trainerItem.session_price)}</strong></td>
        <td><span class="badge ${trainerItem.status === "active" ? "bg-success" : "bg-secondary"}">${trainerItem.status}</span></td>
        <td>
          <div class="btn-group gap-1">
            <button class="btn btn-sm btn-action-edit" onclick="editAdminTrainer(${trainerItem.id})">${t("edit")}</button>
            <button class="btn btn-sm btn-action-delete" onclick="deleteAdminTrainer(${trainerItem.id})">${t("delete")}</button>
          </div>
        </td>
      </tr>
    `).join("") : `<tr><td colspan="5" class="text-center text-muted">${t("no_trainer_data")}</td></tr>`;
  } catch (err) {
    container.innerHTML = `<tr><td colspan="5" class="text-center text-danger">${err.message}</td></tr>`;
  }
}

async function editAdminTrainer(trainerId) {
  try {
    const trainers = await apiFetch("/admin/trainers/");
    const trainer = trainers.find((item) => item.id === trainerId);
    if (!trainer) {
      showAlert("Khong tim thay HLV.", "danger");
      return;
    }
    const trainerIdInput = document.getElementById("editTrainerId");
    const nameInput = document.getElementById("editTrainerName");
    const specialtyInput = document.getElementById("editTrainerSpecialty");
    const expInput = document.getElementById("editTrainerExp");
    const priceInput = document.getElementById("editTrainerPrice");
    const statusSelect = document.getElementById("editTrainerStatus");

    if (!trainerIdInput || !nameInput || !specialtyInput || !expInput || !priceInput || !statusSelect) {
      showAlert("Khong tim thay form sua HLV.", "danger");
      return;
    }

    trainerIdInput.value = String(trainer.id);
    nameInput.value = trainer.name || "";
    specialtyInput.value = trainer.specialty || "";
    expInput.value = String(trainer.experience_years || 0);
    priceInput.value = String(trainer.session_price || 0);
    statusSelect.value = trainer.status || "active";

    adminEditTrainerModal = getAdminModalInstance("editTrainerModal");
    if (adminEditTrainerModal) adminEditTrainerModal.show();
  } catch (err) {
    showAlert("Khong cap nhat duoc HLV: " + err.message, "danger");
  }
}

async function submitEditTrainer(event) {
  event.preventDefault();
  const trainerId = parseInt(document.getElementById("editTrainerId").value, 10);
  const name = document.getElementById("editTrainerName").value.trim();
  const specialty = document.getElementById("editTrainerSpecialty").value.trim();
  const experienceYears = parseInt(document.getElementById("editTrainerExp").value, 10);
  const sessionPrice = parseFloat(document.getElementById("editTrainerPrice").value);
  const statusValue = document.getElementById("editTrainerStatus").value;

  if (!trainerId || !name || !specialty || Number.isNaN(experienceYears) || experienceYears < 0 || Number.isNaN(sessionPrice) || sessionPrice < 0) {
    showAlert("Du lieu sua HLV khong hop le.", "danger");
    return;
  }

  try {
    await apiFetch(`/admin/trainers/${trainerId}/`, {
      method: "PATCH",
      body: JSON.stringify({
        name,
        specialty,
        experience_years: experienceYears,
        session_price: sessionPrice,
        status: statusValue,
      }),
    });
    if (adminEditTrainerModal) adminEditTrainerModal.hide();
    showAlert(t("update_trainer_success"));
    await loadAdminTrainerList();
  } catch (err) {
    showAlert("Khong cap nhat duoc HLV: " + err.message, "danger");
  }
}

async function deleteAdminTrainer(trainerId) {
  if (!confirm(t("delete_trainer_confirm"))) return;
  try {
    await apiFetch(`/admin/trainers/${trainerId}/`, { method: "DELETE" });
    showAlert("Da xoa HLV.");
    await loadAdminTrainerList();
  } catch (err) {
    showAlert("Khong xoa duoc HLV: " + err.message, "danger");
  }
}

// =========================================================================
// ADMIN: GYM CLASS MANAGEMENT
// =========================================================================

async function loadAdminClassForm() {
  const categorySelect = document.getElementById("classCategory");
  const trainerSelect = document.getElementById("classTrainer");

  if (!categorySelect || !trainerSelect) return;

  try {
    const [categories, trainers, classes] = await Promise.all([
      apiFetch("/categories/"),
      apiFetch("/trainers/"),
      apiFetch("/classes/"),
    ]);

    categorySelect.innerHTML = categories.map(c => `<option value="${c.id}">${c.name}</option>`).join("");
    trainerSelect.innerHTML = trainers.map(t => `<option value="${t.id}">${t.name} (${t.specialty})</option>`).join("");

    // Load existing class list
    const container = document.getElementById("adminClassListRows");
    if (container) {
      container.innerHTML = classes.length ? classes.map(c => `
        <tr>
          <td><strong>${c.name}</strong></td>
          <td>${c.category_name || "-"}</td>
          <td>${c.trainer_name || "-"}</td>
          <td><span class="badge bg-secondary">${c.difficulty_level}</span></td>
          <td>${c.duration_minutes} phut</td>
          <td><strong class="text-danger">${money(c.price)}</strong></td>
          <td><span class="text-muted">-</span></td>
        </tr>
      `).join("") : `<tr><td colspan="7" class="text-center text-muted">Chua co lop tap nao.</td></tr>`;
    }
  } catch (err) {
    console.error("Error loading admin class form", err);
  }
}

async function submitCreateClass(event) {
  event.preventDefault();
  const form = event.target;
  const payload = {
    name: form.name.value,
    category: parseInt(form.category.value),
    trainer: parseInt(form.trainer.value),
    difficulty_level: form.difficulty_level.value,
    duration_minutes: parseInt(form.duration_minutes.value),
    price: parseFloat(form.price.value) || 0,
    description: form.description.value,
  };

  try {
    await apiFetch("/admin/classes/create/", {
      method: "POST",
      body: JSON.stringify(payload),
    });
    showAlert("Tao lop tap moi thanh cong!");
    form.reset();
    await loadAdminClassForm();
  } catch (err) {
    showAlert(err.message, "danger");
  }
}

// =========================================================================
// ADMIN: PACKAGE MANAGEMENT
// =========================================================================

async function loadAdminPackageList() {
  const container = document.getElementById("adminPackageListRows");
  if (!container) return;
  try {
    const packages = await apiFetch("/membership-packages/");
    container.innerHTML = packages.length ? packages.map(p => `
      <tr>
        <td><strong>${p.name}</strong></td>
        <td><strong class="text-danger">${money(p.price)}</strong></td>
        <td>${p.duration_days} ngay</td>
        <td>${p.max_bookings_per_week ? p.max_bookings_per_week + " buoi" : "Khong gioi han"}</td>
        <td>${p.is_freezable ? `<span class="text-success">Co (${p.max_freeze_days} ngay)</span>` : '<span class="text-muted">Khong</span>'}</td>
        <td>
          <div class="btn-group gap-1">
            <button class="btn btn-sm btn-action-edit" onclick="editAdminPackage(${p.id})">${t("edit")}</button>
            <button class="btn btn-sm btn-action-delete" onclick="deleteAdminPackage(${p.id})">${t("delete")}</button>
          </div>
        </td>
      </tr>
    `).join("") : `<tr><td colspan="6" class="text-center text-muted">${t("no_package_data")}</td></tr>`;
  } catch (err) {
    container.innerHTML = `<tr><td colspan="6" class="text-center text-danger">${err.message}</td></tr>`;
  }
}

async function editAdminPackage(packageId) {
  try {
    const packages = await apiFetch("/membership-packages/");
    const pack = packages.find((item) => item.id === packageId);
    if (!pack) {
      showAlert("Khong tim thay goi tap.", "danger");
      return;
    }

    const name = prompt("Ten goi", pack.name || "");
    if (name === null) return;
    const priceInput = prompt("Gia (VND)", String(pack.price || 0));
    if (priceInput === null) return;
    const daysInput = prompt("So ngay", String(pack.duration_days || 30));
    if (daysInput === null) return;
    const weeklyInput = prompt("Gioi han buoi/tuan (de trong neu khong gioi han)", pack.max_bookings_per_week == null ? "" : String(pack.max_bookings_per_week));
    if (weeklyInput === null) return;
    const freezable = confirm("Goi nay co ho tro tam dung khong?");
    const freezeDaysInput = prompt("So ngay tam dung toi da", String(pack.max_freeze_days || 0));
    if (freezeDaysInput === null) return;

    const price = parseFloat(priceInput);
    const durationDays = parseInt(daysInput, 10);
    const maxFreezeDays = parseInt(freezeDaysInput, 10);
    const maxBookingsPerWeek = weeklyInput.trim() === "" ? null : parseInt(weeklyInput, 10);

    if (Number.isNaN(price) || price < 0) {
      showAlert("Gia goi khong hop le.", "danger");
      return;
    }
    if (Number.isNaN(durationDays) || durationDays < 1) {
      showAlert("So ngay khong hop le.", "danger");
      return;
    }
    if (Number.isNaN(maxFreezeDays) || maxFreezeDays < 0) {
      showAlert("So ngay tam dung khong hop le.", "danger");
      return;
    }
    if (maxBookingsPerWeek !== null && (Number.isNaN(maxBookingsPerWeek) || maxBookingsPerWeek < 1)) {
      showAlert("Gioi han buoi/tuan khong hop le.", "danger");
      return;
    }

    await apiFetch(`/admin/packages/${packageId}/`, {
      method: "PATCH",
      body: JSON.stringify({
        name: name.trim(),
        price,
        duration_days: durationDays,
        max_bookings_per_week: maxBookingsPerWeek,
        is_freezable: freezable,
        max_freeze_days: maxFreezeDays,
      }),
    });
    showAlert("Cap nhat goi tap thanh cong.");
    await loadAdminPackageList();
  } catch (err) {
    showAlert("Khong cap nhat duoc goi tap: " + err.message, "danger");
  }
}

async function deleteAdminPackage(packageId) {
  if (!confirm(t("delete_package_confirm"))) return;
  try {
    await apiFetch(`/admin/packages/${packageId}/`, { method: "DELETE" });
    showAlert("Da xoa goi tap.");
    await loadAdminPackageList();
  } catch (err) {
    showAlert("Khong xoa duoc goi tap: " + err.message, "danger");
  }
}

async function submitCreatePackage(event) {
  event.preventDefault();
  const form = event.target;
  const maxBookings = form.max_bookings_per_week.value;
  const payload = {
    name: form.name.value,
    description: form.description.value,
    price: parseFloat(form.price.value),
    duration_days: parseInt(form.duration_days.value),
    max_bookings_per_week: maxBookings ? parseInt(maxBookings) : null,
    is_freezable: form.is_freezable.checked,
    max_freeze_days: parseInt(form.max_freeze_days.value) || 30,
  };

  try {
    await apiFetch("/admin/packages/create/", {
      method: "POST",
      body: JSON.stringify(payload),
    });
    showAlert("Tao goi tap moi thanh cong!");
    form.reset();
    await loadAdminPackageList();
  } catch (err) {
    showAlert(err.message, "danger");
  }
}

// Chatbot tu van phong gym: tao widget bang JavaScript de nhung duoc tren moi trang.
(function initGymChatbot() {
  const apiBase = typeof API_BASE !== "undefined" ? API_BASE : "http://127.0.0.1:8000/api";
  const chatbotApiUrl = `${apiBase}/chat/`;

  let userType = "";
  let history = [];
  let hasShownGreeting = false;
  let loadingMessageElement = null;

  const welcomeByUserType = {
    Giam_Can:
      "Tuyet voi! Minh se uu tien tu van theo huong giam mo, cardio va thoi quen an uong de duy tri. Ban muon hoi ve lich tap hay dinh duong truoc?",
    Tang_Co:
      "Rat tot! Minh se uu tien tu van theo huong tang co, tap ta, protein va phuc hoi. Ban ang moi tap hay a tap uoc mot thoi gian roi?",
    Van_Phong:
      "Minh hieu roi. Minh se uu tien cac bai giup giam au moi, cai thien tu the va van ong nhe. Ban thuong au moi vung co vai gay, lung hay hong?",
  };

  function createElement(tagName, className, text) {
    const element = document.createElement(tagName);
    if (className) {
      element.className = className;
    }
    if (text) {
      element.textContent = text;
    }
    return element;
  }

  function scrollToBottom(messages) {
    messages.scrollTop = messages.scrollHeight;
  }

  function addMessage(messages, role, content, extraClass) {
    // Dung textContent de tranh XSS tu noi dung nguoi dung nhap.
    const message = createElement("div", `gym-chatbot-message ${role}${extraClass ? ` ${extraClass}` : ""}`);
    message.textContent = content;
    messages.appendChild(message);
    scrollToBottom(messages);
    return message;
  }

  function setFormEnabled(input, button, isEnabled) {
    input.disabled = !isEnabled;
    button.disabled = !isEnabled;
  }

  async function sendChatMessage(message) {
    const response = await fetch(chatbotApiUrl, {
      method: "POST",
      credentials: "include",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        message,
        user_type: userType,
        history,
      }),
    });

    if (!response.ok) {
      throw new Error("Backend chatbot error");
    }

    return response.json();
  }

  function mountChatbot() {
    if (document.querySelector(".gym-chatbot-widget")) {
      return;
    }

    const widget = createElement("section", "gym-chatbot-widget");
    widget.setAttribute("aria-label", "Chatbot tu van phong gym");

    const toggle = createElement("button", "gym-chatbot-toggle", "Chat");
    toggle.type = "button";
    toggle.setAttribute("aria-label", "Mo chatbot");

    const chatWindow = createElement("div", "gym-chatbot-window");
    chatWindow.setAttribute("aria-hidden", "true");

    const header = createElement("header", "gym-chatbot-header");
    const headerText = createElement("div");
    headerText.appendChild(createElement("p", "gym-chatbot-eyebrow", "GYM ASSISTANT"));
    headerText.appendChild(createElement("h2", "gym-chatbot-title", "Tu van tap luyen"));

    const closeButton = createElement("button", "gym-chatbot-close", "");
    closeButton.type = "button";
    closeButton.setAttribute("aria-label", "ong chatbot");

    header.appendChild(headerText);
    header.appendChild(closeButton);

    const messages = createElement("div", "gym-chatbot-messages");
    messages.setAttribute("aria-live", "polite");

    const goals = createElement("div", "gym-chatbot-goals");
    goals.setAttribute("aria-label", "Chon muc tieu tap luyen");

    [
      ["Giam_Can", "Giam can / Giam mo"],
      ["Tang_Co", "Tang co / Tap nang"],
      ["Van_Phong", "Dan van phong / au moi"],
    ].forEach(([type, label]) => {
      const button = createElement("button", "gym-chatbot-goal", label);
      button.type = "button";
      button.dataset.userType = type;
      goals.appendChild(button);
    });

    const form = createElement("form", "gym-chatbot-form");
    form.autocomplete = "off";

    const input = createElement("input", "gym-chatbot-input");
    input.type = "text";
    input.placeholder = "Nhap cau hoi cua ban...";
    input.setAttribute("aria-label", "Nhap cau hoi");

    const sendButton = createElement("button", "gym-chatbot-send", "Gai");
    sendButton.type = "submit";

    form.appendChild(input);
    form.appendChild(sendButton);

    chatWindow.appendChild(header);
    chatWindow.appendChild(messages);
    chatWindow.appendChild(goals);
    chatWindow.appendChild(form);
    widget.appendChild(toggle);
    widget.appendChild(chatWindow);
    document.body.appendChild(widget);

    function openChat() {
      chatWindow.classList.add("is-open");
      chatWindow.setAttribute("aria-hidden", "false");
      toggle.setAttribute("aria-label", "An chatbot");

      if (!hasShownGreeting) {
        addMessage(messages, "bot", "Xin chao! Ban muon tap luyen theo muc tieu nao?");
        hasShownGreeting = true;
      }
    }

    function closeChat() {
      chatWindow.classList.remove("is-open");
      chatWindow.setAttribute("aria-hidden", "true");
      toggle.setAttribute("aria-label", "Mo chatbot");
    }

    toggle.addEventListener("click", () => {
      if (chatWindow.classList.contains("is-open")) {
        closeChat();
      } else {
        openChat();
      }
    });

    closeButton.addEventListener("click", closeChat);

    goals.querySelectorAll(".gym-chatbot-goal").forEach((button) => {
      button.addEventListener("click", () => {
        userType = button.dataset.userType;
        goals.classList.add("is-hidden");
        form.classList.add("is-visible");

        const botWelcome = welcomeByUserType[userType];
        addMessage(messages, "bot", botWelcome);
        history.push({ role: "assistant", content: botWelcome });
        input.focus();
      });
    });

    form.addEventListener("submit", async (event) => {
      event.preventDefault();

      const message = input.value.trim();
      if (!message || !userType) {
        return;
      }

      addMessage(messages, "user", message);
      history.push({ role: "user", content: message });

      input.value = "";
      setFormEnabled(input, sendButton, false);
      loadingMessageElement = addMessage(messages, "bot", "ang tra loi...", "loading");

      try {
        const data = await sendChatMessage(message);
        const reply = data.reply || "Minh chua co cau tra loi phu hop. Ban thu hoi lai ngan gon hon nhe.";

        loadingMessageElement.remove();
        loadingMessageElement = null;
        addMessage(messages, "bot", reply);
        history.push({ role: "assistant", content: reply });
      } catch (error) {
        if (loadingMessageElement) {
          loadingMessageElement.remove();
          loadingMessageElement = null;
        }
        addMessage(messages, "bot", "Hien tai bot chua phan hoi uoc, ban thu lai sau nhe.");
      } finally {
        setFormEnabled(input, sendButton, true);
        input.focus();
      }
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", mountChatbot);
  } else {
    mountChatbot();
  }
})();

