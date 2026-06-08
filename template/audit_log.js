const tx = (key, fallback = key) => (window.I18N && window.I18N[key]) || fallback;

function auditFilters() {
  const params = new URLSearchParams();
  params.set("format", "json");
  const actor = document.getElementById("filter-actor").value.trim();
  const action = document.getElementById("filter-action").value.trim();
  const startDate = document.getElementById("filter-start-date").value;
  const endDate = document.getElementById("filter-end-date").value;
  if (actor) params.set("actor", actor);
  if (action) params.set("action", action);
  if (startDate) params.set("start_date", startDate);
  if (endDate) params.set("end_date", endDate);
  return params;
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

async function loadAudit() {
  const params = auditFilters();
  document.getElementById("audit-export-link").href = `/admin/audit/export?${params.toString().replace("format=json&", "")}`;
  const res = await fetch(`/admin/audit?${params.toString()}`);
  const message = document.getElementById("audit-message");
  if (!res.ok) {
    message.textContent = tx("audit.load_failed");
    return;
  }
  const data = await res.json();
  const rows = data.events || [];
  const body = document.getElementById("audit-table-body");
  if (!rows.length) {
    body.innerHTML = "";
    message.textContent = tx("audit.no_events");
    return;
  }

  body.innerHTML = rows.map((event) => `
    <tr>
      <td class="tech-ltr">${formatIsraelTime(event.timestamp)}</td>
      <td class="tech-ltr">${event.actor_email || "-"}</td>
      <td class="tech-ltr">${event.target_email || "-"}</td>
      <td>${event.action || "-"}</td>
      <td>${event.status || "-"}</td>
      <td>${event.source || "-"}</td>
      <td class="tech-ltr"><code>${JSON.stringify(event.metadata || {})}</code></td>
    </tr>
  `).join("");
  message.textContent = "";
}

document.addEventListener("DOMContentLoaded", () => {
  document.getElementById("apply-audit-filters").addEventListener("click", loadAudit);
  loadAudit();
});
