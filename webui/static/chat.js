const state = {
  messages: [],
  current_node_id: "",
  state_history: [],
  last_buttons: [],
};

const el = {
  log: document.getElementById("chat-log"),
  buttons: document.getElementById("chat-buttons"),
  input: document.getElementById("chat-input"),
  send: document.getElementById("btn-send"),
  reset: document.getElementById("btn-reset"),
  back: document.getElementById("btn-back"),
  stCurrent: document.getElementById("st-current"),
  stType: document.getElementById("st-type"),
  stBreadcrumb: document.getElementById("st-breadcrumb"),
  flowTrigger: document.getElementById("flow-trigger"),
  flowSteps: document.getElementById("flow-steps"),
  shell: document.getElementById("app-shell"),
  toggleLog: document.getElementById("btn-toggle-log"),
};

let logVisible = false;

function toggleLog() {
  logVisible = !logVisible;
  el.shell.classList.toggle("show-log", logVisible);
  el.toggleLog.textContent = logVisible ? "Sembunyikan flow log" : "Tampilkan flow log";
}

function escapeHtml(s) {
  const div = document.createElement("div");
  div.textContent = s == null ? "" : String(s);
  return div.innerHTML;
}

async function postJson(url, body) {
  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body || {}),
  });
  return res.json();
}

function renderMessages() {
  el.log.innerHTML = state.messages
    .map((m) => {
      const cls = m.role === "user" ? "chat-user" : "chat-bot";
      return `<div class="${cls}">${escapeHtml(m.content)}</div>`;
    })
    .join("");
  el.log.scrollTop = el.log.scrollHeight;
}

function renderButtons() {
  el.buttons.innerHTML = "";
  state.last_buttons.forEach((b) => {
    const btn = document.createElement("button");
    btn.className = "btn-light";
    btn.textContent = b.label;
    btn.addEventListener("click", () => onSelect(b));
    el.buttons.appendChild(btn);
  });
}

function renderState() {
  el.stCurrent.textContent = state.current_node_id || "GLOBAL_ROUTER";
  el.stType.textContent = state.stateType || "router";
  el.stBreadcrumb.textContent =
    (state.breadcrumb && state.breadcrumb.join(" > ")) || "GLOBAL_ROUTER";
  el.back.disabled = !(state.state_history && state.state_history.length);
}

function renderFlow(trace) {
  if (!trace || !trace.trigger) {
    el.flowTrigger.textContent = "Belum ada proses";
    el.flowSteps.innerHTML =
      '<div class="flow-empty">Kirim chat atau klik button untuk melihat alur bot.</div>';
    return;
  }
  el.flowTrigger.textContent = trace.trigger;
  const steps = (trace.steps || [])
    .map(
      (s, i) =>
        `<div class="flow-step"><div class="fn">${i + 1}. ${escapeHtml(
          s.function
        )}</div><div class="msg">${escapeHtml(s.message)}</div></div>`
    )
    .join("");
  const summary = trace.response_summary
    ? `<div class="flow-step"><div class="fn">Response</div><div class="msg">${escapeHtml(
        trace.response_summary
      )}</div></div>`
    : "";
  el.flowSteps.innerHTML = steps + summary;
}

function applyResult(result) {
  state.current_node_id = result.current_node_id || "";
  state.state_history = result.state_history || [];
  state.stateType = result.state_type || "router";
  state.breadcrumb = result.breadcrumb || [];
  state.last_buttons = result.buttons || [];
  state.messages.push({ role: "assistant", content: result.text || "" });
  renderMessages();
  renderButtons();
  renderState();
  renderFlow(result.trace);
}

async function onSend() {
  const text = el.input.value.trim();
  if (!text) return;
  state.messages.push({ role: "user", content: text });
  renderMessages();
  el.input.value = "";
  const result = await postJson("/api/chat", {
    text,
    current_node_id: state.current_node_id,
    state_history: state.state_history,
  });
  applyResult(result);
}

async function onSelect(button) {
  state.messages.push({ role: "user", content: button.label });
  renderMessages();
  const result = await postJson("/api/select", {
    node_id: button.id,
    current_node_id: state.current_node_id,
    state_history: state.state_history,
  });
  applyResult(result);
}

async function onBack() {
  state.messages.push({ role: "user", content: "Back" });
  renderMessages();
  const result = await postJson("/api/back", {
    current_node_id: state.current_node_id,
    state_history: state.state_history,
  });
  applyResult(result);
}

async function onReset() {
  const result = await postJson("/api/reset", {});
  state.messages = [{ role: "assistant", content: result.text || "" }];
  state.current_node_id = result.current_node_id || "";
  state.state_history = result.state_history || [];
  state.stateType = result.state_type || "router";
  state.breadcrumb = result.breadcrumb || [];
  state.last_buttons = [];
  renderMessages();
  renderButtons();
  renderState();
  renderFlow(result.trace);
}

el.send.addEventListener("click", onSend);
el.input.addEventListener("keydown", (e) => {
  if (e.key === "Enter") onSend();
});
el.back.addEventListener("click", onBack);
el.reset.addEventListener("click", onReset);
el.toggleLog.addEventListener("click", toggleLog);

// greeting
state.messages.push({
  role: "assistant",
  content: "Halo, ceritain kebutuhanmu. Aku akan sarankan topik yang paling cocok.",
});
renderMessages();
renderState();
