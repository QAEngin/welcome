const tx = (key, fallback = key) => (window.I18N && window.I18N[key]) || fallback;

function formatMessage(key, values = {}) {
  return tx(key).replace(/\{(\w+)\}/g, (_, name) => values[name] ?? "");
}

function userFilters() {
  const params = new URLSearchParams();
  const email = document.getElementById("filter-email").value.trim();
  const status = document.getElementById("filter-status").value;
  const createdFrom = document.getElementById("filter-created-from").value;
  const createdTo = document.getElementById("filter-created-to").value;
  params.set("format", "json");
  if (email) params.set("email", email);
  if (status) params.set("status", status);
  if (createdFrom) params.set("created_from", createdFrom);
  if (createdTo) params.set("created_to", createdTo);
  return params;
}

function userBadge(label, kind) {
  return `<span class="badge ${kind}">${label}</span>`;
}

const israelDateFormatter = new Intl.DateTimeFormat("en-GB", {
  timeZone: "Asia/Jerusalem",
  day: "2-digit",
  month: "short",
  year: "numeric",
  hour: "2-digit",
  minute: "2-digit",
  hour12: false,
});

function formatIsraelTime(value) {
  if (!value) return "-";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return `${israelDateFormatter.format(date)} IL`;
}

function roleLabel(role) {
  return role === "admin" ? tx("role.admin") : tx("role.user");
}

async function loadUsers() {
  const message = document.getElementById("users-message");
  message.textContent = tx("admin.loading_users");
  const res = await fetch(`/admin/users?${userFilters().toString()}`);
  if (!res.ok) {
    message.textContent = tx("admin.load_users_failed");
    return;
  }
  const data = await res.json();
  const rows = data.users || [];
  const body = document.getElementById("users-table-body");
  if (!rows.length) {
    body.innerHTML = "";
    message.textContent = tx("admin.no_users");
    return;
  }

  body.innerHTML = rows.map((user) => `
    <tr>
      <td class="tech-ltr">${user.email}</td>
      <td>${userBadge(user.disabled ? tx("admin.disabled") : tx("admin.enabled"), user.disabled ? "danger" : "success")}</td>
      <td>${userBadge(roleLabel(user.role), user.role === "admin" ? "info" : "neutral")}</td>
      <td class="tech-ltr">${formatIsraelTime(user.created_at)}</td>
      <td class="tech-ltr">${formatIsraelTime(user.last_sign_in_at)}</td>
      <td class="actions">
        <button type="button" class="table-btn" onclick="toggleUserDisabled('${user.uid}', ${!user.disabled})">${user.disabled ? tx("admin.enable") : tx("admin.disable")}</button>
        <button type="button" class="table-btn" onclick="changeUserRole('${user.uid}', '${user.role === "admin" ? "user" : "admin"}')">${user.role === "admin" ? tx("admin.make_user") : tx("admin.make_admin")}</button>
        <button type="button" class="table-btn" onclick="resetPassword('${user.uid}')">${tx("admin.reset_password")}</button>
      </td>
    </tr>
  `).join("");
  message.textContent = "";
}

async function createUser() {
  const message = document.getElementById("create-user-message");
  message.textContent = tx("admin.creating_user");
  const payload = {
    email: document.getElementById("new-user-email").value.trim(),
    password: document.getElementById("new-user-password").value,
    role: document.getElementById("new-user-role").value,
  };
  const res = await fetch("/admin/users", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const data = await res.json();
  if (!res.ok || !data.ok) {
    message.textContent = data.message || tx("admin.create_failed");
    return;
  }
  message.textContent = formatMessage("admin.created_user", { email: data.user.email });
  document.getElementById("new-user-email").value = "";
  document.getElementById("new-user-password").value = "";
  document.getElementById("new-user-role").value = "user";
  await loadUsers();
}

async function toggleUserDisabled(uid, disabled) {
  const res = await fetch(`/admin/users/${uid}/disable`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ disabled }),
  });
  if (res.ok) await loadUsers();
}

async function changeUserRole(uid, role) {
  const res = await fetch(`/admin/users/${uid}/role`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ role }),
  });
  if (res.ok) await loadUsers();
}

async function resetPassword(uid) {
  const res = await fetch(`/admin/users/${uid}/reset-password`, { method: "POST" });
  const data = await res.json();
  if (!res.ok || !data.ok) {
    alert(data.message || tx("admin.reset_failed"));
    return;
  }
  window.prompt(tx("admin.reset_link"), data.reset_link);
}

document.addEventListener("DOMContentLoaded", () => {
  document.getElementById("apply-user-filters").addEventListener("click", loadUsers);
  document.getElementById("create-user-btn").addEventListener("click", createUser);
  document.getElementById("toggle-create-user").addEventListener("click", () => {
    document.getElementById("create-user-card").classList.toggle("hidden");
  });
  loadUsers();
});
