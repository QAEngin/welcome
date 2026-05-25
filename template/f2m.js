let pendingF2mDone = null;

function escapeHtml(value) {
  return String(value ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

async function loadF2mCustomers() {
  const res = await fetch("/f2m-data");
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

  data.customers.forEach((c) => {
    const hasDomain = Boolean(c.domain);
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td class="name-cell">${escapeHtml(c.name)}</td>
      <td class="domain-cell ${hasDomain ? "" : "missing"}">${escapeHtml(c.domain || "MISSING")}</td>
      <td class="email-cell">
        <span class="email-wrap">
          <span class="email-text">${escapeHtml(c.email)}</span>
          <button class="copy-email-btn" type="button" data-email="${escapeHtml(c.email)}" title="העתקת מייל">
            <i class="fa-regular fa-copy"></i>
          </button>
        </span>
      </td>
      <td>
        <button class="status-btn waiting" data-row="${Number(c.row)}">
          ${escapeHtml(c.status || "ממתין")}
        </button>
      </td>
    `;

    tbody.appendChild(tr);
  });

  document.querySelectorAll(".status-btn").forEach((btn) => {
    btn.addEventListener("click", function () {
      const row = parseInt(this.dataset.row, 10);
      pendingF2mDone = { row, buttonEl: this };
      document.getElementById("f2m-confirm-modal").style.display = "flex";
    });
  });

  document.querySelectorAll(".copy-email-btn").forEach((btn) => {
    btn.addEventListener("click", async function () {
      await copyEmail(this.dataset.email || "", this);
    });
  });
}

async function copyEmail(email, buttonEl) {
  if (!email) return;

  try {
    if (navigator.clipboard && window.isSecureContext) {
      await navigator.clipboard.writeText(email);
    } else {
      const input = document.createElement("input");
      input.value = email;
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
    alert("שגיאה בהעתקת מייל: " + err.message);
  }
}

async function confirmF2mDone() {
  const task = pendingF2mDone;
  pendingF2mDone = null;
  document.getElementById("f2m-confirm-modal").style.display = "none";
  if (!task) return;

  const btn = task.buttonEl;
  btn.disabled = true;

  try {
    const res = await fetch("/f2m-done", {
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
      loadF2mCustomers();
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

document.getElementById("f2m-confirm-no").addEventListener("click", () => {
  pendingF2mDone = null;
  document.getElementById("f2m-confirm-modal").style.display = "none";
});

document.getElementById("f2m-confirm-yes").addEventListener("click", async () => {
  await confirmF2mDone();
});

document.querySelectorAll(".instruction-thumb").forEach((thumb) => {
  thumb.addEventListener("click", function () {
    const modal = document.getElementById("image-preview-modal");
    const image = document.getElementById("image-preview");
    image.src = this.dataset.previewSrc || "";
    modal.style.display = "flex";
  });
});

function closeImagePreview() {
  const modal = document.getElementById("image-preview-modal");
  const image = document.getElementById("image-preview");
  modal.style.display = "none";
  image.src = "";
}

document.getElementById("image-preview-close").addEventListener("click", closeImagePreview);
document.getElementById("image-preview-modal").addEventListener("click", (event) => {
  if (event.target.id === "image-preview-modal") {
    closeImagePreview();
  }
});

loadF2mCustomers();
setInterval(loadF2mCustomers, 20000);
