const API_BASE = "http://127.0.0.1:8000/api";

const SESSION_TIMEOUT_MS = 30 * 60 * 1000;
const SESSION_KEEP_ALIVE_MS = 5 * 60 * 1000;
const LAST_ACTIVITY_KEY = "gymLastActivityAt";
const LOGIN_PAGE = "/login.html";

const PUBLIC_PAGES = new Set([
  "index.html",
  "login.html",
  "register.html",
  "classes.html",
  "trainers.html",
  "packages.html",
  "schedules.html",
  "forgot-password.html",
  "reset-password.html",
  "pt-packages.html",
]);

const PROTECTED_PAGES = new Set([
  "my-bookings.html",
  "admin-dashboard.html",
  "trainer-dashboard.html",
  "my-pt-packages.html",
]);

const ROLE_RULES = {
  "admin-dashboard.html": ["admin"],
  "trainer-dashboard.html": ["trainer", "admin"],
};

let idleTimerId = null;
let lastActivityWriteAt = 0;
let lastKeepAliveAt = 0;
let accessToken = (() => {
  try {
    const user = JSON.parse(localStorage.getItem("gymUser") || "null");
    return user ? user.access : null;
  } catch (_) {
    return null;
  }
})();
let isRefreshing = null; // Global promise for refresh token locking

async function apiFetch(path, options = {}) {
  const { skipAuthRedirect = false, ...fetchOptions } = options;
  
  const headers = {
    "Content-Type": "application/json",
    ...(fetchOptions.headers || {}),
  };
  
  // Wait if refresh is already in progress
  if (isRefreshing) {
    try {
      await isRefreshing;
    } catch (_) {
      // Ignore refresh errors here, retry will handle it
    }
  }

  if (accessToken) {
    headers["Authorization"] = `Bearer ${accessToken}`;
  }

  let response = await fetch(`${API_BASE}${path}`, {
    credentials: "include",
    headers,
    ...fetchOptions,
  });

  // Automatically refresh access token if expired (401)
  if (response.status === 401 && getStoredUser() && !path.includes("/auth/refresh/") && !path.includes("/auth/login/")) {
    if (!isRefreshing) {
      isRefreshing = (async () => {
        try {
          const refreshResponse = await fetch(`${API_BASE}/auth/refresh/`, {
            method: "POST",
            credentials: "include",
            headers: { "Content-Type": "application/json" }
          });
          if (refreshResponse.ok) {
            const refreshData = await refreshResponse.json();
            accessToken = refreshData.access;
            saveUserSession(refreshData);
          } else {
            handleAuthExpired();
            throw new Error("Session expired");
          }
        } catch (refreshErr) {
          handleAuthExpired();
          throw refreshErr;
        } finally {
          isRefreshing = null;
        }
      })();
    }

    try {
      // Wait for the active refresh to complete
      await isRefreshing;
      
      // Retry request with new token
      headers["Authorization"] = `Bearer ${accessToken}`;
      response = await fetch(`${API_BASE}${path}`, {
        credentials: "include",
        headers,
        ...fetchOptions,
      });
    } catch (err) {
      if (!skipAuthRedirect) {
        handleAuthExpired();
      }
      throw err;
    }
  }

  const contentType = response.headers.get("content-type") || "";
  const data = contentType.includes("application/json") ? await response.json() : null;

  if (!response.ok) {
    if (!skipAuthRedirect && (response.status === 401 || response.status === 403)) {
      handleAuthExpired();
    }
    const message = data?.message || data?.detail || "Request failed";
    throw new Error(message);
  }
  return data;
}

function imageUrl(value, fallback) {
  if (!value) return fallback;
  if (value.startsWith("http")) return value;
  return `http://127.0.0.1:8000${value}`;
}

function money(value) {
  return `${Number(value || 0).toLocaleString("vi-VN")} VN\u0110`;
}

function showAlert(message, type = "success") {
  const box = document.getElementById("messages");
  if (!box) return;

  // Tao DOM bang textContent de thong bao loi khong bi chen HTML la.
  box.replaceChildren();
  const alert = document.createElement("div");
  alert.className = `alert alert-${type} alert-dismissible fade show`;
  alert.setAttribute("role", "alert");

  const text = document.createElement("span");
  text.textContent = message;

  const closeButton = document.createElement("button");
  closeButton.type = "button";
  closeButton.className = "btn-close";
  closeButton.setAttribute("data-bs-dismiss", "alert");
  closeButton.setAttribute("aria-label", "Close");

  alert.appendChild(text);
  alert.appendChild(closeButton);
  box.appendChild(alert);
}

function getCurrentPage() {
  return location.pathname.split("/").pop() || "index.html";
}

function isProtectedPage(page = getCurrentPage()) {
  const p = page.toLowerCase();
  if (p.includes("forgot-password") || p.includes("reset-password") || p.includes("login") || p.includes("register")) {
    return false;
  }
  return PROTECTED_PAGES.has(page) || !PUBLIC_PAGES.has(page);
}

function getStoredUser() {
  try {
    return JSON.parse(localStorage.getItem("gymUser") || "null");
  } catch (_) {
    localStorage.removeItem("gymUser");
    return null;
  }
}

function saveUserSession(user) {
  if (!user) return;
  const current = getStoredUser() || {};
  const merged = { ...current, ...user };
  if (merged.access) {
    accessToken = merged.access;
  }
  localStorage.setItem("gymUser", JSON.stringify(merged));
  markUserActivity(true);
}

function clearUserSession() {
  accessToken = null;
  localStorage.removeItem("gymUser");
  localStorage.removeItem(LAST_ACTIVITY_KEY);
  if (idleTimerId) {
    clearTimeout(idleTimerId);
    idleTimerId = null;
  }
}

function normalizeUser(user) {
  if (!user) return null;
  return {
    id: user.id,
    username: user.username,
    email: user.email || "",
    role: user.role || "member",
    full_name: user.full_name || user.username,
  };
}

function renderAuthNav(user) {
  const loggedIn = !!user;

  document.querySelectorAll("[data-auth='guest']").forEach((el) => el.classList.toggle("d-none", loggedIn));
  document.querySelectorAll("[data-auth='user']").forEach((el) => el.classList.toggle("d-none", !loggedIn));

  if (!loggedIn) {
    document.querySelectorAll("[data-role]").forEach((el) => el.classList.add("d-none"));
    return;
  }

  document.querySelectorAll("[data-role]").forEach((el) => {
    const roles = el.getAttribute("data-role").split(",");
    el.classList.toggle("d-none", !roles.includes(user.role));
  });

  const roleLabel = user.role === "admin" ? "Admin" : user.role === "trainer" ? "HLV" : "H\u1ed9i vi\u00ean";
  const nameEl = document.getElementById("navUserName");
  if (nameEl) {
    nameEl.textContent = `${user.full_name || user.username} (${roleLabel})`;
  }
}

function redirectToLogin() {
  const page = getCurrentPage();
  if (page === "login.html") return;
  const next = encodeURIComponent(`${location.pathname}${location.search || ""}`);
  location.href = `${LOGIN_PAGE}?next=${next}`;
}

function redirectAfterLogin(user) {
  const next = new URLSearchParams(location.search).get("next");
  if (next) {
    location.href = next;
    return;
  }
  if (user?.role === "admin") {
    location.href = "/admin-dashboard.html";
    return;
  }
  if (user?.role === "trainer") {
    location.href = "/trainer-dashboard.html";
    return;
  }
  location.href = "/index.html";
}

function enforcePageRole(user) {
  const page = getCurrentPage();
  const allowedRoles = ROLE_RULES[page];
  if (!allowedRoles || !user) return;
  if (!allowedRoles.includes(user.role)) {
    showAlert("Tai khoan cua ban khong co quyen truy cap trang nay.", "warning");
    location.href = "/index.html";
  }
}

function handleAuthExpired() {
  clearUserSession();
  renderAuthNav(null);
  if (isProtectedPage()) {
    redirectToLogin();
  }
}

function isIdleExpired() {
  const lastActivityAt = Number(localStorage.getItem(LAST_ACTIVITY_KEY) || 0);
  return !!lastActivityAt && Date.now() - lastActivityAt >= SESSION_TIMEOUT_MS;
}

function scheduleIdleLogout() {
  if (idleTimerId) clearTimeout(idleTimerId);
  if (!getStoredUser()) return;

  const lastActivityAt = Number(localStorage.getItem(LAST_ACTIVITY_KEY) || Date.now());
  const remainingMs = Math.max(0, SESSION_TIMEOUT_MS - (Date.now() - lastActivityAt));
  idleTimerId = setTimeout(logoutByIdleTimeout, remainingMs);
}

function markUserActivity(force = false) {
  if (!getStoredUser()) return;

  const now = Date.now();
  if (!force && now - lastActivityWriteAt < 1000) return;

  lastActivityWriteAt = now;
  localStorage.setItem(LAST_ACTIVITY_KEY, String(now));
  scheduleIdleLogout();
  refreshServerSessionIfNeeded(false);
}

async function refreshServerSessionIfNeeded(force = false) {
  if (!getStoredUser()) return;

  const now = Date.now();
  if (!force && now - lastKeepAliveAt < SESSION_KEEP_ALIVE_MS) return;

  lastKeepAliveAt = now;
  try {
    await apiFetch("/profile/me/", { skipAuthRedirect: true });
  } catch (_) {
    handleAuthExpired();
  }
}

function bindIdleActivityEvents() {
  ["click", "mousemove", "keydown", "scroll", "touchstart"].forEach((eventName) => {
    document.addEventListener(eventName, () => markUserActivity(false), { passive: true });
  });
}

async function logoutByIdleTimeout() {
  clearUserSession();
  try {
    await apiFetch("/auth/logout/", { method: "POST", body: "{}", skipAuthRedirect: true });
  } catch (_) {
    // Neu session da het han tren server, frontend van can dua ve login.
  } finally {
    redirectToLogin();
  }
}

async function logout() {
  if (!confirm("Bạn có chắc chắn muốn đăng xuất không?")) return;
  try {
    await apiFetch("/auth/logout/", { method: "POST", body: "{}", skipAuthRedirect: true });
  } catch (_) {
    // Logout nen idempotent: du server da het session, frontend van xoa trang thai local.
  } finally {
    clearUserSession();
    location.href = LOGIN_PAGE;
  }
}

async function setAuthNav() {
  const page = getCurrentPage();
  const storedUser = getStoredUser();

  if (!storedUser) {
    clearUserSession();
    renderAuthNav(null);
    if (isProtectedPage(page)) {
      redirectToLogin();
    }
    return;
  }

  if (isIdleExpired()) {
    await logoutByIdleTimeout();
    return;
  }

  try {
    const sessionUser = normalizeUser(await apiFetch("/profile/me/", { skipAuthRedirect: true }));
    lastKeepAliveAt = Date.now();
    saveUserSession(sessionUser);
    renderAuthNav(sessionUser);
    enforcePageRole(sessionUser);

    if (page === "login.html") {
      redirectAfterLogin(sessionUser);
    }
  } catch (_) {
    clearUserSession();
    renderAuthNav(null);
    if (isProtectedPage(page)) {
      redirectToLogin();
    }
  }
}

function injectLayout() {
  const currentPage = getCurrentPage();

  // Favicon injection
  let favLink = document.querySelector("link[rel='icon']");
  if (!favLink) {
    favLink = document.createElement("link");
    favLink.rel = "icon";
    favLink.type = "image/png";
    favLink.href = "assets/images/logo.png";
    document.head.appendChild(favLink);
  }

  // Meta description injection
  let metaDesc = document.querySelector("meta[name='description']");
  if (!metaDesc) {
    metaDesc = document.createElement("meta");
    metaDesc.name = "description";
    metaDesc.content = "Gym Booking - Giải pháp quản lý đặt lịch tập gym, huấn luyện viên cá nhân và lớp học thông minh.";
    document.head.appendChild(metaDesc);
  }

  // Navbar
  let navEl = document.querySelector("nav.navbar");
  if (navEl) navEl.remove();
  
  navEl = document.createElement("nav");
  navEl.className = "navbar navbar-expand-lg navbar-dark fixed-top";
  navEl.innerHTML = `
    <div class="container">
      <a class="navbar-brand fw-bold" href="index.html"><img class="brand-logo" src="assets/images/logo.png" alt="">Gym Booking</a>
      <button class="navbar-toggler" data-bs-toggle="collapse" data-bs-target="#nav" aria-label="Mở menu"><span class="navbar-toggler-icon"></span></button>
      <div id="nav" class="collapse navbar-collapse">
        <ul class="navbar-nav ms-auto align-items-lg-center">
          <li class="nav-item"><a class="nav-link" href="classes.html">Lớp tập</a></li>
          <li class="nav-item"><a class="nav-link" href="trainers.html">HLV</a></li>
          <li class="nav-item"><a class="nav-link" href="packages.html">Gói tập</a></li>
          <li class="nav-item"><a class="nav-link" href="pt-packages.html">Gói PT</a></li>
          <li class="nav-item d-none" data-role="member"><a class="nav-link" href="my-bookings.html">Lịch của tôi</a></li>
          <li class="nav-item d-none" data-role="member"><a class="nav-link" href="my-pt-packages.html">Gói PT của tôi</a></li>
          <li class="nav-item d-none" data-role="trainer,admin"><a class="nav-link" href="trainer-dashboard.html">Lịch dạy HLV</a></li>
          <li class="nav-item d-none" data-role="admin"><a class="nav-link" href="admin-dashboard.html">Quản lý Admin</a></li>
          <li class="nav-item" data-auth="guest"><a class="nav-link" href="login.html">Đăng nhập</a></li>
          <li class="nav-item d-none" data-auth="user">
            <span id="navUserName" class="me-lg-2 text-light"></span>
            <button class="btn btn-outline-light btn-sm ms-lg-2" onclick="logout()">Đăng xuất</button>
          </li>
        </ul>
      </div>
    </div>
  `;
  document.body.insertBefore(navEl, document.body.firstChild);

  // Set active link in navbar
  navEl.querySelectorAll(".nav-link").forEach(link => {
    const href = link.getAttribute("href");
    if (href && (currentPage === href || (currentPage === "index.html" && href === "index.html") || (currentPage === "" && href === "index.html"))) {
      link.classList.add("active");
    } else {
      link.classList.remove("active");
    }
  });

  // Footer
  let footerEl = document.querySelector("footer.footer");
  if (footerEl) footerEl.remove();
  
  footerEl = document.createElement("footer");
  footerEl.className = "footer py-5 bg-dark text-light mt-auto";
  footerEl.innerHTML = `
    <div class="container">
      <div class="row g-4">
        <div class="col-md-4">
          <a class="navbar-brand fw-bold text-white fs-4 d-flex align-items-center gap-2 mb-3" href="index.html">
            <img class="brand-logo" src="assets/images/logo.png" alt="" style="width: 32px; height: 32px; border-radius: 8px;">
            Gym Booking
          </a>
          <p class="text-secondary small">Giải pháp quản lý phòng tập thông minh, đặt lịch huấn luyện viên 1-1 và quản lý gói tập tối ưu.</p>
        </div>
        <div class="col-md-4">
          <h6 class="text-uppercase fw-bold text-white mb-3">Liên kết nhanh</h6>
          <ul class="list-unstyled text-secondary small d-flex flex-column gap-2">
            <li><a href="classes.html" class="text-secondary">Lớp tập</a></li>
            <li><a href="trainers.html" class="text-secondary">Huấn luyện viên (HLV)</a></li>
            <li><a href="packages.html" class="text-secondary">Gói tập hội viên</a></li>
            <li><a href="pt-packages.html" class="text-secondary">Gói PT cá nhân</a></li>
          </ul>
        </div>
        <div class="col-md-4">
          <h6 class="text-uppercase fw-bold text-white mb-3">Liên hệ</h6>
          <p class="text-secondary small mb-2"><i class="bi bi-geo-alt me-2 text-brand"></i> Tầng 5, Tòa nhà DEHA, Hà Nội</p>
          <p class="text-secondary small mb-2"><i class="bi bi-telephone me-2 text-brand"></i> Hotline: 1900 6868</p>
          <p class="text-secondary small"><i class="bi bi-envelope me-2 text-brand"></i> support@gymbooking.vn</p>
        </div>
      </div>
      <hr class="border-secondary my-4">
      <div class="d-flex flex-column flex-sm-row justify-content-between align-items-center gap-2">
        <span class="text-secondary small">© 2026 Gym Booking. Tất cả quyền được bảo lưu.</span>
        <div class="d-flex gap-3">
          <a href="#" class="text-secondary fs-5"><i class="bi bi-facebook"></i></a>
          <a href="#" class="text-secondary fs-5"><i class="bi bi-instagram"></i></a>
          <a href="#" class="text-secondary fs-5"><i class="bi bi-youtube"></i></a>
        </div>
      </div>
    </div>
  `;
  document.body.appendChild(footerEl);
}

window.markUserActivity = markUserActivity;
window.logout = logout;

document.addEventListener("DOMContentLoaded", () => {
  injectLayout();
  bindIdleActivityEvents();
  setAuthNav();
});
