const $ = (id) => document.getElementById(id);

function toast(message) {
  const el = $("toast");
  el.textContent = message;
  el.style.display = "block";
  window.setTimeout(() => { el.style.display = "none"; }, 3500);
}

async function api(path, options = {}) {
  const headers = options.headers || {};
  if (options.method && options.method !== "GET") {
    headers["X-API-Key"] = $("apiKey").value;
  }
  const response = await fetch(path, { ...options, headers });
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(body.detail || `Request failed: ${response.status}`);
  }
  return response.json();
}

function metric(label, value) {
  return `<div class="metric"><span>${label}</span><strong>${value}</strong></div>`;
}

function renderMetrics(data) {
  const run = data.latest_run || {};
  $("metrics").innerHTML = [
    metric("Processed", run.processed || 0),
    metric("Passed", run.passed || 0),
    metric("Failed", run.failed || 0),
    metric("Queued", run.queued_for_retry || 0),
    metric("Incidents", data.incidents.length),
  ].join("");
}

function renderIncidents(items) {
  $("incidentCount").textContent = `${items.length} open`;
  $("incidents").innerHTML = items.length ? items.map((item) => `
    <div class="item">
      <strong><span class="${item.severity}">${item.severity.toUpperCase()}</span> · ${item.title}</strong>
      <p><span class="pill">${item.event_id}</span><span class="pill">${item.owner}</span><span class="pill">${item.runbook_slug}</span></p>
    </div>
  `).join("") : `<div class="item"><p>No open incidents.</p></div>`;
}

function renderRetries(items) {
  $("retryCount").textContent = `${items.length} shown`;
  $("retries").innerHTML = items.length ? items.map((item) => `
    <div class="item">
      <strong>${item.status.toUpperCase()} · ${item.event_id}</strong>
      <p>${item.reason}</p>
      <p><span class="pill">${item.attempts} attempts</span><span class="pill">next ${item.next_attempt_at}</span></p>
    </div>
  `).join("") : `<div class="item"><p>No retry items.</p></div>`;
}

function renderFindings(items) {
  $("findingCount").textContent = `${items.length} shown`;
  $("findings").innerHTML = items.length ? items.map((item) => `
    <div class="item">
      <strong><span class="${item.severity}">${item.severity}</span> · ${item.check_name}</strong>
      <p>${item.event_id}: ${item.message}</p>
    </div>
  `).join("") : `<div class="item"><p>No validation findings.</p></div>`;
}

function renderRunbooks(items) {
  $("runbooks").innerHTML = items.map((item) => `
    <div class="item">
      <strong>${item.title}</strong>
      <p><span class="pill">${item.slug}</span>${item.path}</p>
    </div>
  `).join("");
}

async function refresh() {
  const [dashboard, runbooks] = await Promise.all([
    api("/api/dashboard"),
    api("/api/runbooks"),
  ]);
  renderMetrics(dashboard);
  renderIncidents(dashboard.incidents);
  renderRetries(dashboard.retries);
  renderFindings(dashboard.findings);
  renderRunbooks(runbooks);
}

async function action(path, label) {
  try {
    const result = await api(path, { method: "POST" });
    toast(`${label}: ${JSON.stringify(result)}`);
    await refresh();
  } catch (error) {
    toast(error.message);
  }
}

$("ingestBtn").addEventListener("click", () => action("/api/ingest/sample", "Sample ingest"));
$("runBtn").addEventListener("click", () => action("/api/integrations/run", "Validation run"));
$("retryBtn").addEventListener("click", () => action("/api/retries/process", "Retry processing"));

refresh().catch((error) => toast(error.message));

