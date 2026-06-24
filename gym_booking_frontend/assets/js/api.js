const API_BASE = "http://127.0.0.1:8000/api";

const SESSION_TIMEOUT_MS = 30 * 60 * 1000;
const SESSION_KEEP_ALIVE_MS = 5 * 60 * 1000;
const LAST_ACTIVITY_KEY = "gymLastActivityAt";
const LOGIN_PAGE = "login.html";

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
]);

const PROTECTED_PAGES = new Set([
  "my-bookings.html",
  "admin-dashboard.html",
  "trainer-dashboard.html",
]);

const ROLE_RULES = {
  "admin-dashboard.html": ["admin"],
  "trainer-dashboard.html": ["trainer", "admin"],
};

let idleTimerId = null;
let lastActivityWriteAt = 0;
let lastKeepAliveAt = 0;
let accessToken = null;
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
  if (response.status === 401 && !path.includes("/auth/refresh/") && !path.includes("/auth/login/")) {
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
  if (user && user.access) {
    accessToken = user.access;
  }
  localStorage.setItem("gymUser", JSON.stringify(user));
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
  if (page === LOGIN_PAGE) return;
  const next = encodeURIComponent(`${page}${location.search || ""}`);
  location.href = `${LOGIN_PAGE}?next=${next}`;
}

function redirectAfterLogin(user) {
  const next = new URLSearchParams(location.search).get("next");
  if (next) {
    location.href = next;
    return;
  }
  if (user?.role === "admin") {
    location.href = "admin-dashboard.html";
    return;
  }
  if (user?.role === "trainer") {
    location.href = "trainer-dashboard.html";
    return;
  }
  location.href = "index.html";
}

function enforcePageRole(user) {
  const page = getCurrentPage();
  const allowedRoles = ROLE_RULES[page];
  if (!allowedRoles || !user) return;
  if (!allowedRoles.includes(user.role)) {
    showAlert("Tai khoan cua ban khong co quyen truy cap trang nay.", "warning");
    location.href = "index.html";
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

  if (storedUser && isIdleExpired()) {
    await logoutByIdleTimeout();
    return;
  }

  try {
    const sessionUser = normalizeUser(await apiFetch("/profile/me/", { skipAuthRedirect: true }));
    lastKeepAliveAt = Date.now();
    saveUserSession(sessionUser);
    renderAuthNav(sessionUser);
    enforcePageRole(sessionUser);

    if (page === LOGIN_PAGE) {
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

window.markUserActivity = markUserActivity;
window.logout = logout;

document.addEventListener("DOMContentLoaded", () => {
  bindIdleActivityEvents();
  setAuthNav();
});
