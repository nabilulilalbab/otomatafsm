let adminPass = "";
let currentTree = null;
let selectedId = "";

function $(id) {
  return document.getElementById(id);
}
function show(id) { $(id).classList.remove("hidden"); }
function hide(id) { $(id).classList.add("hidden"); }
function escapeHtml(s) {
  const div = document.createElement("div");
  div.textContent = s == null ? "" : String(s);
  return div.innerHTML;
}

async function api(method, url, body) {
  const res = await fetch(url, {
    method,
    headers: {
      "Content-Type": "application/json",
      "X-Admin-Password": adminPass,
    },
    body: body ? JSON.stringify(body) : undefined,
  });
  const data = await res.json().catch(() => ({}));
  return { ok: res.ok, status: res.status, data };
}

async function login() {
  adminPass = $("admin-pass").value;
  const res = await api("POST", "/api/admin/login", {});
  if (res.ok) {
    hide("login-view");
    show("admin-view");
    await loadTree();
  } else {
    show("login-error");
  }
}

async function loadTree() {
  const res = await api("GET", "/api/admin/tree");
  if (!res.ok) return;
  currentTree = res.data;
  renderRows();
  renderParentOptions();
  $("set-name").value = currentTree.bot_name || "";
  $("set-fallback").value = currentTree.fallback || "";
}

function findNode(id) {
  return (currentTree.nodes || []).find((n) => n.id === id) || null;
}

function renderRows() {
  const rows = currentTree.rows || [];
  $("tree-rows").innerHTML = rows
    .map((row) => {
      if (row.missing) {
        return `<div class="tree-row missing"><span class="t-title">${escapeHtml(
          row.title
        )}</span><span class="t-type">hilang/nonaktif</span></div>`;
      }
      const node = findNode(row.node_id);
      const isMenu = node && node.children && node.children.length;
      const type = isMenu ? "menu" : "final";
      const indent = (row.depth || 0) * 16;
      return `<div class="tree-row" data-id="${escapeHtml(
        row.node_id
      )}" style="margin-left:${indent}px"><span class="t-title">${escapeHtml(
        row.title
      )}</span><span class="t-type">${type}</span></div>`;
    })
    .join("");

  document.querySelectorAll(".tree-row[data-id]").forEach((rowEl) => {
    rowEl.addEventListener("click", () => selectNode(rowEl.dataset.id));
  });
}

function renderParentOptions() {
  const opts = currentTree.parent_options || [];
  $("add-parent").innerHTML = opts
    .map((o) => `<option value="${escapeHtml(o.id)}">${escapeHtml(o.label)}</option>`)
    .join("");
}

function selectNode(id) {
  selectedId = id;
  const node = findNode(id);
  if (!node) return;
  hide("detail-empty");
  show("edit-form");
  $("edit-id").value = node.id;
  $("edit-title").value = node.title || "";
  $("edit-desc").value = node.description || "";
  $("edit-keywords").value = (node.keywords || []).join("\n");
  $("edit-children").value = (node.children || []).join("\n");
  $("edit-answer").value = node.answer || "";
  $("edit-enabled").value = node.enabled ? "true" : "false";
  hide("edit-error");
  hide("edit-ok");
}

async function addNode() {
  hide("add-error");
  hide("add-ok");
  const body = {
    title: $("add-title").value,
    description: $("add-desc").value,
    keywords: $("add-keywords").value,
    answer: $("add-type").value === "final" ? $("add-answer").value : "",
    parent_id: $("add-parent").value,
    enabled: true,
  };
  const res = await api("POST", "/api/admin/node", body);
  if (res.ok) {
    show("add-ok");
    $("add-title").value = "";
    $("add-desc").value = "";
    $("add-keywords").value = "";
    $("add-answer").value = "";
    await loadTree();
  } else {
    const errs = (res.data && res.data.errors) || [res.data.detail || "Gagal menambah group."];
    $("add-error").textContent = errs.join(" ");
    show("add-error");
  }
}

async function saveNode() {
  hide("edit-error");
  hide("edit-ok");
  const body = {
    title: $("edit-title").value,
    description: $("edit-desc").value,
    keywords: $("edit-keywords").value,
    children: $("edit-children").value,
    answer: $("edit-answer").value,
    enabled: $("edit-enabled").value === "true",
  };
  const res = await api("PUT", `/api/admin/node/${encodeURIComponent(selectedId)}`, body);
  if (res.ok) {
    show("edit-ok");
    await loadTree();
  } else {
    const errs = (res.data && res.data.errors) || [res.data.detail || "Gagal menyimpan."];
    $("edit-error").textContent = errs.join(" ");
    show("edit-error");
  }
}

async function deleteNode() {
  if (!selectedId) return;
  const res = await api("DELETE", `/api/admin/node/${encodeURIComponent(selectedId)}`);
  if (res.ok) {
    selectedId = "";
    hide("edit-form");
    show("detail-empty");
    await loadTree();
  }
}

async function saveSettings() {
  hide("set-ok");
  const res = await api("PUT", "/api/admin/settings", {
    bot_name: $("set-name").value,
    fallback: $("set-fallback").value,
  });
  if (res.ok) {
    show("set-ok");
    await loadTree();
  }
}

$("btn-login").addEventListener("click", login);
$("admin-pass").addEventListener("keydown", (e) => {
  if (e.key === "Enter") login();
});
$("btn-add").addEventListener("click", addNode);
$("btn-save").addEventListener("click", saveNode);
$("btn-delete").addEventListener("click", deleteNode);
$("btn-settings").addEventListener("click", saveSettings);
