const $ = (selector) => document.querySelector(selector);
let selectedTrace = null;

async function api(path, options = {}) {
  const response = await fetch(path, {
    headers: { "content-type": "application/json", ...(options.headers || {}) },
    ...options
  });
  const payload = await response.json();
  if (!response.ok) throw new Error(payload.error || "Request failed");
  return payload;
}

function badge(status) {
  return `<span class="badge ${status}">${status.replaceAll("_", " ")}</span>`;
}

function renderMetrics(data) {
  const entries = [
    ["Recipients", data.counts.recipients],
    ["Pending approvals", data.counts.pendingApprovals],
    ["Batches", data.counts.batches],
    ["Open incidents", data.counts.openIncidents],
    ["Inventory (kg)", data.currentInventoryKg],
    ["Verified animal-days", data.verifiedAnimalDays]
  ];
  $("#metrics").innerHTML = entries
    .map(([label, value]) => `<div class="metric"><span>${label}</span><strong>${value}</strong></div>`)
    .join("");
}

function renderTrace(trace = selectedTrace) {
  const container = $("#rule-trace");
  if (!trace || trace.length === 0) {
    container.innerHTML = '<p class="empty">Create a batch to see deterministic pass/fail decisions.</p>';
    return;
  }
  container.innerHTML = `<div class="trace">${trace
    .map((item) => `<div class="trace-item">${badge(item.status)}<div><strong>${item.ruleId}</strong><br>${item.message}</div></div>`)
    .join("")}</div>`;
}

function renderMatches(matches, batches) {
  const container = $("#matches");
  if (!matches.length) return (container.innerHTML = '<p class="empty">No matches yet.</p>');
  container.innerHTML = matches
    .map((match) => {
      const batch = batches.find((item) => item.id === match.batchId);
      const actions = [];
      if (match.status === "pending_approval") actions.push(`<button class="small" data-approve="${match.id}">Approve synthetic match</button>`);
      if (["approved", "pending_approval"].includes(match.status)) actions.push(`<button class="small danger" data-suspend="${batch.id}">Run incident suspension</button>`);
      actions.push(`<button class="small secondary" data-trace="${match.id}">View trace</button>`);
      return `<article class="card">
        <header><h3>${batch?.productName || match.batchId}</h3>${badge(match.status)}</header>
        <p>Score: <strong>${match.score}</strong> · Rule version: <code>${match.ruleVersion}</code></p>
        <p>${match.summary}</p><div class="actions">${actions.join("")}</div>
      </article>`;
    })
    .join("");

  container.querySelectorAll("[data-approve]").forEach((button) => button.addEventListener("click", () => mutate(`/api/matches/${button.dataset.approve}/approve`)));
  container.querySelectorAll("[data-suspend]").forEach((button) => button.addEventListener("click", () => mutate(`/api/batches/${button.dataset.suspend}/suspend`, { reason: "Synthetic recall drill" })));
  container.querySelectorAll("[data-trace]").forEach((button) => button.addEventListener("click", () => {
    selectedTrace = matches.find((item) => item.id === button.dataset.trace)?.ruleTrace || null;
    renderTrace();
  }));
}

function renderTasks(tasks) {
  const container = $("#tasks");
  if (!tasks.length) return (container.innerHTML = '<p class="empty">Approve an eligible match to generate tasks.</p>');
  container.innerHTML = tasks
    .sort((a, b) => a.sequence - b.sequence)
    .map((task) => `<article class="card"><header><h3>${task.sequence}. ${task.type.replaceAll("_", " ")}</h3>${badge(task.status)}</header><p>${task.instruction}</p>${task.status === "pending" ? `<div class="actions"><button class="small" data-complete="${task.id}">Record synthetic evidence</button></div>` : ""}</article>`)
    .join("");
  container.querySelectorAll("[data-complete]").forEach((button) => button.addEventListener("click", () => mutate(`/api/tasks/${button.dataset.complete}/complete`, { evidence: { note: "Synthetic custody evidence", recordedAt: new Date().toISOString() } })));
}

function renderImpacts(impacts, matches) {
  const container = $("#impacts");
  const buttons = matches.filter((item) => item.status === "approved").map((item) => `<button class="small" data-impact="${item.id}">Calculate ${item.id.slice(0, 12)}…</button>`).join("");
  const cards = impacts.map((impact) => `<article class="card"><header><h3>${impact.verifiedAnimalDays} animal-days</h3>${badge(impact.claimStatus)}</header><p>${impact.reason}</p></article>`).join("");
  container.innerHTML = `${buttons ? `<div class="actions">${buttons}</div>` : ""}${cards || '<p class="empty">Impact stays blocked until every evidence task is complete.</p>'}`;
  container.querySelectorAll("[data-impact]").forEach((button) => button.addEventListener("click", () => mutate(`/api/matches/${button.dataset.impact}/impact`)));
}

function renderAudit(events) {
  const container = $("#audit");
  if (!events.length) return (container.innerHTML = '<p class="empty">No audit events yet.</p>');
  container.innerHTML = events.map((event) => `<article class="card"><strong>${event.action}</strong><p>${event.entityType}: <code>${event.entityId}</code><br>${new Date(event.occurredAt).toLocaleString()}</p></article>`).join("");
}

async function refresh() {
  const data = await api("/api/dashboard");
  renderMetrics(data);
  renderMatches(data.recentMatches, data.batches);
  renderTasks(data.tasks);
  renderImpacts(data.impacts, data.recentMatches);
  renderAudit(data.auditEvents);
  renderTrace();
}

async function mutate(path, body = {}) {
  try {
    await api(path, { method: "POST", body: JSON.stringify(body) });
    $("#form-status").textContent = "Action recorded.";
  } catch (error) {
    $("#form-status").textContent = error.message;
  }
  await refresh();
}

$("#batch-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const form = new FormData(event.currentTarget);
  const body = {
    recipientId: "rec-shelter-a",
    animalGroupId: "grp-dogs-a",
    productName: form.get("productName"),
    quantityKg: Number(form.get("quantityKg")),
    sourceType: form.get("sourceType"),
    dietClass: form.get("dietClass"),
    flags: form.get("recalled") ? ["recalled"] : []
  };
  try {
    const result = await api("/api/matches", { method: "POST", body: JSON.stringify(body) });
    selectedTrace = result.match.ruleTrace;
    $("#form-status").textContent = result.match.summary;
  } catch (error) {
    $("#form-status").textContent = error.message;
  }
  await refresh();
});

$("#reset-button").addEventListener("click", async () => {
  selectedTrace = null;
  await mutate("/api/reset");
});

refresh().catch((error) => {
  $("#form-status").textContent = error.message;
});
