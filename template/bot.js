let pendingBotDone = null;

async function loadBotCustomers() {
  const res = await fetch("/bot-data");
  const data = await res.json();

  const tbody = document.getElementById("customers-body");
  const count = document.getElementById("waiting-count");
  const empty = document.getElementById("empty-message");

  tbody.innerHTML = "";
  count.innerText = data.count;

  if (data.count === 0) {
    empty.style.display = "block";
    return;
  }

  empty.style.display = "none";

  data.customers.forEach((c) => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${c.name}</td>
      <td id="domain-${c.row}">...</td>
      <td>${c.did}</td>
      <td>
        <button class="status-btn waiting" data-row="${c.row}">
          סטטוס ממתין
        </button>
      </td>
    `;

    tbody.appendChild(tr);
    loadDomain(c.client_id, c.row);
  });

  document.querySelectorAll(".status-btn").forEach((btn) => {
    btn.addEventListener("click", function () {
      const row = parseInt(this.dataset.row, 10);
      pendingBotDone = { row, buttonEl: this };
      document.getElementById("bot-confirm-modal").style.display = "flex";
    });
  });
}

async function confirmBotDone() {
  const task = pendingBotDone;
  pendingBotDone = null;
  document.getElementById("bot-confirm-modal").style.display = "none";
  if (!task) return;

  const btn = task.buttonEl;
  btn.classList.remove("waiting");
  btn.classList.add("done");
  btn.innerText = "בוצע";

  await fetch("/bot-done", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ row: task.row }),
  });

  setTimeout(() => {
    btn.closest("tr").remove();
  }, 500);
}

async function loadDomain(client_id, row) {
  if (!client_id) return;
  try {
    const res = await fetch("/fireberry-by-id", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ idnumber: client_id }),
    });

    const data = await res.json();
    if (data.ok && data.domain) {
      const cell = document.getElementById("domain-" + row);
      if (cell) {
        cell.innerText = data.domain;
      }
    }
  } catch (e) {
    console.log("Domain lookup failed", e);
  }
}

document.getElementById("search").addEventListener("input", function () {
  const term = this.value.toLowerCase();
  document.querySelectorAll("#customers-body tr").forEach((tr) => {
    tr.style.display = tr.innerText.toLowerCase().includes(term) ? "" : "none";
  });
});

document.getElementById("bot-confirm-no").addEventListener("click", () => {
  pendingBotDone = null;
  document.getElementById("bot-confirm-modal").style.display = "none";
});

document.getElementById("bot-confirm-yes").addEventListener("click", async () => {
  await confirmBotDone();
});

loadBotCustomers();
setInterval(loadBotCustomers, 20000);
