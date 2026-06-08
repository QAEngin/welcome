let currentScope = "all";
let debounceTimer = null;
let lastTickets = [];

function escapeHtml(value) {
  return String(value ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

function israelDatePreview() {
  return new Intl.DateTimeFormat("he-IL", {
    timeZone: "Asia/Jerusalem",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date());
}

function priorityClass(priority) {
  return `priority-${String(priority || "medium").toLowerCase()}`;
}

function renderStats(stats) {
  document.getElementById("stat-all").textContent = stats?.all ?? 0;
  document.getElementById("stat-unassigned").textContent = stats?.unassigned ?? 0;
  document.getElementById("stat-waiting").textContent = `${stats?.waiting ?? 0} Waiting`;
}

function renderTickets(tickets, users) {
  const list = document.getElementById("ticket-list");
  const empty = document.getElementById("tickets-empty");
  lastTickets = Array.isArray(tickets) ? tickets : [];
  list.innerHTML = "";

  if (!Array.isArray(tickets) || tickets.length === 0) {
    empty.style.display = "block";
    return;
  }

  empty.style.display = "none";
  tickets.forEach((ticket) => {
    const row = document.createElement("article");
    row.className = "ticket-row";
    row.dataset.ticketId = ticket.id;
    const assigneeOptions = ['<option value="">Unassigned</option>']
      .concat((users || []).map((user) => `<option value="${escapeHtml(user)}" ${ticket.assigned_to === user ? "selected" : ""}>${escapeHtml(user)}</option>`))
      .join("");
    const firstAttachment = Array.isArray(ticket.attachments) ? ticket.attachments[0] : null;
    const statusClass = ticket.status === "Done" ? "done" : "waiting";
    row.innerHTML = `
      <div class="ticket-id">${escapeHtml(ticket.ticket_id)}</div>
      <div class="ticket-main">
        <h3>${escapeHtml(ticket.service_type || "General")} ${ticket.domain ? `<span class="ticket-meta">/ ${escapeHtml(ticket.domain)}</span>` : ""}</h3>
        <p>${escapeHtml(ticket.description)}</p>
      </div>
      <div class="ticket-meta">
        <strong>${escapeHtml(ticket.ticket_type)}</strong><br>
        ${escapeHtml(ticket.creator)}<br>${escapeHtml(ticket.created_at_display)}
      </div>
      <select class="assignee-select" data-ticket-id="${ticket.id}">${assigneeOptions}</select>
      <select class="status-select" data-ticket-id="${ticket.id}">
        <option value="Waiting" ${ticket.status === "Waiting" ? "selected" : ""}>Waiting</option>
        <option value="Done" ${ticket.status === "Done" ? "selected" : ""}>Done</option>
      </select>
      <div class="ticket-actions">
        <span class="pill ${statusClass}">${escapeHtml(ticket.status)}</span>
        <span class="pill ${priorityClass(ticket.priority)}">${escapeHtml(ticket.priority)}</span>
        ${firstAttachment ? `<button class="attachment-link" type="button" data-image-url="${escapeHtml(firstAttachment.url)}" title="Open JPG"><i class="fa-regular fa-image"></i></button>` : ""}
      </div>
    `;
    row.addEventListener("click", (event) => {
      if (event.target.closest("select, button, a, input, textarea")) return;
      openTicketDetail(ticket.id);
    });
    list.appendChild(row);
  });

  document.querySelectorAll(".assignee-select").forEach((select) => {
    select.addEventListener("change", () => updateTicket(select.dataset.ticketId, { assigned_to: select.value }));
  });
  document.querySelectorAll(".status-select").forEach((select) => {
    select.addEventListener("change", () => updateTicket(select.dataset.ticketId, { status: select.value }));
  });
  document.querySelectorAll(".attachment-link").forEach((button) => {
    button.addEventListener("click", (event) => {
      event.stopPropagation();
      openImagePreview(button.dataset.imageUrl || "");
    });
  });
}

function getTicket(ticketId) {
  const numericId = Number(String(ticketId).replace("#", ""));
  return lastTickets.find((ticket) => Number(ticket.id) === numericId);
}

function detailItem(label, value) {
  return `
    <div class="detail-item">
      <span>${escapeHtml(label)}</span>
      <strong>${escapeHtml(value || "-")}</strong>
    </div>
  `;
}

function openTicketDetail(ticketId) {
  const ticket = getTicket(ticketId);
  if (!ticket) return;

  document.getElementById("detail-kicker").textContent = `${ticket.service_type || "Ticket"} ${ticket.domain ? `/ ${ticket.domain}` : ""}`;
  document.getElementById("detail-title").textContent = ticket.ticket_id || `#${String(ticket.id).padStart(4, "0")}`;
  document.getElementById("detail-grid").innerHTML = [
    detailItem("Ticket Type", ticket.ticket_type),
    detailItem("Service Type", ticket.service_type),
    detailItem("Domain", ticket.domain),
    detailItem("Priority", ticket.priority),
    detailItem("Status", ticket.status),
    detailItem("Assigned To", ticket.assigned_to || "Unassigned"),
    detailItem("Creator", ticket.creator),
    detailItem("Created", ticket.created_at_display),
    detailItem("Internal ID", ticket.id),
  ].join("");
  document.getElementById("detail-description").textContent = ticket.description || "";
  document.getElementById("detail-solution").textContent = ticket.solution || "-";

  const attachments = Array.isArray(ticket.attachments) ? ticket.attachments : [];
  const attachmentHost = document.getElementById("detail-attachments");
  attachmentHost.innerHTML = attachments.length
    ? attachments.map((file, index) => `
        <button class="detail-image-btn" type="button" data-image-url="${escapeHtml(file.url)}">
          <i class="fa-regular fa-image"></i>
          <span>JPG ${index + 1}</span>
        </button>
      `).join("")
    : "";
  attachmentHost.querySelectorAll(".detail-image-btn").forEach((button) => {
    button.addEventListener("click", () => openImagePreview(button.dataset.imageUrl || ""));
  });

  const modal = document.getElementById("ticket-detail-modal");
  modal.classList.add("open");
  modal.setAttribute("aria-hidden", "false");
}

function closeTicketDetail() {
  const modal = document.getElementById("ticket-detail-modal");
  modal.classList.remove("open");
  modal.setAttribute("aria-hidden", "true");
}

function openImagePreview(url) {
  if (!url) return;
  const modal = document.getElementById("image-modal");
  document.getElementById("image-preview").src = url;
  modal.classList.add("open");
  modal.setAttribute("aria-hidden", "false");
}

function closeImagePreview() {
  const modal = document.getElementById("image-modal");
  modal.classList.remove("open");
  modal.setAttribute("aria-hidden", "true");
  document.getElementById("image-preview").src = "";
}

async function loadTickets() {
  const params = new URLSearchParams({
    scope: currentScope,
    status: document.getElementById("status-filter").value,
    assignee: document.getElementById("assignee-filter").value,
    priority: document.getElementById("priority-filter").value,
    search: document.getElementById("ticket-search").value,
  });
  const res = await fetch(`/support-tickets-data?${params.toString()}`);
  if (!res.ok) return;
  const data = await res.json();
  renderStats(data.stats);
  renderTickets(data.tickets, data.users);
  document.getElementById("next-ticket-id").textContent = data.next_id || "#0001";
}

async function updateTicket(ticketId, changes) {
  const payload = { ticket_id: ticketId, ...changes };
  const res = await fetch("/support-tickets-update", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok || !data.ok) {
    alert(data.message || "Update failed");
  }
  await loadTickets();
}

function openModal() {
  document.getElementById("created-preview").value = israelDatePreview();
  document.getElementById("ticket-form-message").textContent = "";
  document.getElementById("ticket-modal").classList.add("open");
  document.getElementById("ticket-modal").setAttribute("aria-hidden", "false");
}

function closeModal() {
  document.getElementById("ticket-modal").classList.remove("open");
  document.getElementById("ticket-modal").setAttribute("aria-hidden", "true");
}

function syncDomainRequirement() {
  const serviceType = document.getElementById("service-type").value.trim();
  const domainField = document.getElementById("domain-field");
  const domainInput = document.getElementById("domain-input");
  const required = serviceType === "\u05de\u05e8\u05db\u05d6\u05d9\u05d9\u05d4";
  domainField.classList.toggle("visible", required);
  domainInput.required = required;
  if (!required) domainInput.value = "";
}

async function submitTicket(event) {
  event.preventDefault();
  const form = event.currentTarget;
  const message = document.getElementById("ticket-form-message");
  const submit = form.querySelector(".create-ticket-btn");
  message.textContent = "";
  submit.disabled = true;

  try {
    const res = await fetch("/support-tickets-create", {
      method: "POST",
      body: new FormData(form),
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok || !data.ok) {
      throw new Error(data.message || "Create failed");
    }
    form.reset();
    syncDomainRequirement();
    closeModal();
    await loadTickets();
  } catch (err) {
    message.textContent = err.message;
  } finally {
    submit.disabled = false;
  }
}

document.addEventListener("DOMContentLoaded", () => {
  const portalToggle = document.querySelector(".portal-toggle");
  if (portalToggle) {
    portalToggle.addEventListener("click", () => {
      portalToggle.closest(".portal-menu")?.classList.toggle("collapsed");
    });
  }

  document.querySelectorAll(".ticket-tab").forEach((button) => {
    button.addEventListener("click", () => {
      document.querySelectorAll(".ticket-tab").forEach((tab) => tab.classList.remove("active"));
      button.classList.add("active");
      currentScope = button.dataset.scope || "all";
      loadTickets();
    });
  });

  ["status-filter", "assignee-filter", "priority-filter"].forEach((id) => {
    document.getElementById(id).addEventListener("change", loadTickets);
  });
  document.getElementById("ticket-search").addEventListener("input", () => {
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(loadTickets, 160);
  });
  document.getElementById("open-ticket-modal").addEventListener("click", openModal);
  document.getElementById("close-ticket-modal").addEventListener("click", closeModal);
  document.getElementById("ticket-modal").addEventListener("click", (event) => {
    if (event.target.id === "ticket-modal") closeModal();
  });
  document.getElementById("close-detail-modal").addEventListener("click", closeTicketDetail);
  document.getElementById("ticket-detail-modal").addEventListener("click", (event) => {
    if (event.target.id === "ticket-detail-modal") closeTicketDetail();
  });
  document.getElementById("close-image-modal").addEventListener("click", closeImagePreview);
  document.getElementById("image-modal").addEventListener("click", (event) => {
    if (event.target.id === "image-modal") closeImagePreview();
  });
  document.getElementById("service-type").addEventListener("input", syncDomainRequirement);
  document.getElementById("ticket-form").addEventListener("submit", submitTicket);

  loadTickets();
});
