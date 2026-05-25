let pendingRecordingStorageDone = null;
const loadedDomains = new Map();

function escapeHtml(value) {
  return String(value ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

async function loadDomainByOrder(orderId, row) {
  const cell = document.getElementById("domain-" + row);
  if (!cell) return;

  if (loadedDomains.has(row)) {
    const domain = loadedDomains.get(row);
    cell.innerText = domain || "MISSING";
    cell.classList.toggle("missing", !domain);
    return;
  }

  if (!orderId) {
    loadedDomains.set(row, "");
    cell.innerText = "MISSING";
    cell.classList.add("missing");
    return;
  }

  try {
    const res = await fetch("/domain-by-order", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ order_id: orderId }),
    });
    const data = await res.json();
    const domain = data.ok && data.domain ? data.domain : "";
    loadedDomains.set(row, domain);
    cell.innerText = domain || "MISSING";
    cell.classList.toggle("missing", !domain);
  } catch (err) {
    loadedDomains.set(row, "");
    cell.innerText = "MISSING";
    cell.classList.add("missing");
  }
}

async function loadRecordingStorageCustomers() {
  const tbody = document.getElementById("customers-body");
  const count = document.getElementById("waiting-count");
  const empty = document.getElementById("empty-message");

  const res = await fetch("/recording-storage-data");
  if (!res.ok) {
    tbody.innerHTML = "";
    count.innerText = "0";
    empty.style.display = "block";
    empty.innerText = "שגיאה בטעינת לקוחות";
    return;
  }

  const data = await res.json();
  tbody.innerHTML = "";
  count.innerText = data.count || 0;

  if (!data.count) {
    empty.style.display = "block";
    return;
  }

  empty.style.display = "none";

  data.customers.forEach((customer) => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${escapeHtml(customer.name)}</td>
      <td class="domain-cell" id="domain-${Number(customer.row)}">...</td>
      <td>${escapeHtml(customer.storage_size || "בלי נפח")}</td>
      <td>
        <button class="status-btn waiting" type="button" data-row="${Number(customer.row)}">
          ${escapeHtml(customer.status || "ממתין")}
        </button>
      </td>
    `;
    tbody.appendChild(tr);
    loadDomainByOrder(customer.order_id, customer.row);
  });

  document.querySelectorAll(".status-btn").forEach((btn) => {
    btn.addEventListener("click", function () {
      pendingRecordingStorageDone = {
        row: parseInt(this.dataset.row, 10),
        buttonEl: this,
      };
      document.getElementById("recording-storage-confirm-modal").style.display = "flex";
    });
  });
}

async function confirmRecordingStorageDone() {
  const task = pendingRecordingStorageDone;
  pendingRecordingStorageDone = null;
  document.getElementById("recording-storage-confirm-modal").style.display = "none";
  if (!task) return;

  const btn = task.buttonEl;
  btn.disabled = true;

  try {
    const res = await fetch("/recording-storage-done", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ row: task.row }),
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok || !data.ok) {
      throw new Error(data.message || "Update failed");
    }

    btn.classList.remove("waiting");
    btn.classList.add("done");
    btn.innerText = "בוצע";
    setTimeout(() => {
      btn.closest("tr").remove();
    }, 500);
  } catch (err) {
    btn.disabled = false;
    alert("שגיאה בעדכון סטטוס: " + err.message);
  }
}

document.getElementById("search").addEventListener("input", function () {
  const term = this.value.toLowerCase();
  document.querySelectorAll("#customers-body tr").forEach((tr) => {
    tr.style.display = tr.innerText.toLowerCase().includes(term) ? "" : "none";
  });
});

document.getElementById("recording-storage-confirm-no").addEventListener("click", () => {
  pendingRecordingStorageDone = null;
  document.getElementById("recording-storage-confirm-modal").style.display = "none";
});

document.getElementById("recording-storage-confirm-yes").addEventListener("click", async () => {
  await confirmRecordingStorageDone();
});

loadRecordingStorageCustomers();
