let pendingHumanServiceDone = null;

function escapeHtml(value) {
  return String(value ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

async function copyText(value, buttonEl) {
  if (!value) return;

  try {
    if (navigator.clipboard && window.isSecureContext) {
      await navigator.clipboard.writeText(value);
    } else {
      const input = document.createElement("input");
      input.value = value;
      document.body.appendChild(input);
      input.select();
      document.execCommand("copy");
      input.remove();
    }

    buttonEl.classList.add("copied");
    buttonEl.innerHTML = '<i class="fa-solid fa-check"></i>';
    setTimeout(() => {
      buttonEl.classList.remove("copied");
      buttonEl.innerHTML = '<i class="fa-regular fa-copy"></i>';
    }, 1200);
  } catch (err) {
    alert("שגיאה בהעתקה: " + err.message);
  }
}

async function loadDomainByOrder(orderId, row) {
  const cell = document.getElementById("domain-" + row);
  if (!cell) return;

  if (!orderId) {
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
    cell.innerText = domain || "MISSING";
    cell.classList.toggle("missing", !domain);
  } catch (err) {
    cell.innerText = "MISSING";
    cell.classList.add("missing");
  }
}

async function loadHumanServiceCustomers() {
  const res = await fetch("/human-service-data");
  const data = await res.json();

  const tbody = document.getElementById("customers-body");
  const count = document.getElementById("waiting-count");
  const empty = document.getElementById("empty-message");

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
      <td class="ltr-cell">
        <span class="number-wrap">
          <span class="number-text">${escapeHtml(customer.hip)}</span>
          <button class="copy-inline" type="button" data-copy="${escapeHtml(customer.hip)}" title="העתקת חיפ">
            <i class="fa-regular fa-copy"></i>
          </button>
        </span>
      </td>
      <td>
        <button class="status-btn waiting" type="button" data-row="${Number(customer.row)}">
          ממתין
        </button>
      </td>
    `;
    tbody.appendChild(tr);
    loadDomainByOrder(customer.order_id, customer.row);
  });

  document.querySelectorAll(".copy-inline").forEach((btn) => {
    btn.addEventListener("click", async function () {
      await copyText(this.dataset.copy || "", this);
    });
  });

  document.querySelectorAll(".status-btn").forEach((btn) => {
    btn.addEventListener("click", function () {
      pendingHumanServiceDone = {
        row: parseInt(this.dataset.row, 10),
        buttonEl: this,
      };
      document.getElementById("human-service-confirm-modal").style.display = "flex";
    });
  });
}

async function confirmHumanServiceDone() {
  const task = pendingHumanServiceDone;
  pendingHumanServiceDone = null;
  document.getElementById("human-service-confirm-modal").style.display = "none";
  if (!task) return;

  const btn = task.buttonEl;
  btn.disabled = true;

  try {
    const res = await fetch("/human-service-done", {
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

document.getElementById("human-service-confirm-no").addEventListener("click", () => {
  pendingHumanServiceDone = null;
  document.getElementById("human-service-confirm-modal").style.display = "none";
});

document.getElementById("human-service-confirm-yes").addEventListener("click", async () => {
  await confirmHumanServiceDone();
});

loadHumanServiceCustomers();
