function renderUsers(serviceKey, users) {
  const host = document.getElementById(`${serviceKey}-users`);
  if (!host) return;
  if (!Array.isArray(users) || users.length === 0) {
    host.innerHTML = '<span class="active-user-empty">No active users</span>';
    return;
  }
  host.innerHTML = users
    .map((u) => `<span class="active-user-chip">${u}</span>`)
    .join("");
}

function renderWaiting(serviceKey, waiting) {
  const value = Number(waiting) || 0;
  const countEl = document.getElementById(`${serviceKey}-waiting-count`);
  const barEl = document.getElementById(`${serviceKey}-waiting-bar`);
  if (countEl) countEl.textContent = String(value);
  if (barEl) {
    const width = Math.min(100, value * 5);
    barEl.style.width = `${width}%`;
  }
}

async function loadDashboardData() {
  try {
    const res = await fetch("/dashboard-data");
    if (!res.ok) return;
    const data = await res.json();
    renderWaiting("sms", data?.sms?.waiting);
    renderUsers("sms", data?.sms?.active_users);
    renderWaiting("bot", data?.bot?.waiting);
    renderUsers("bot", data?.bot?.active_users);
    renderWaiting("recordings", data?.recordings?.waiting);
    renderUsers("recordings", data?.recordings?.active_users);
  } catch (err) {
    console.error("dashboard data error", err);
  }
}

document.addEventListener("DOMContentLoaded", () => {
  loadDashboardData();
  setInterval(loadDashboardData, 20000);
});
