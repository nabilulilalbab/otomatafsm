async function loadHome() {
  try {
    const res = await fetch("/api/tree");
    const data = await res.json();

    const botName = document.getElementById("bot-name");
    if (data.bot_name) botName.textContent = data.bot_name;

    const stats = data.stats || {};
    const statsEl = document.getElementById("panel-stats");
    const entries = [
      ["Total Group", stats.total],
      ["Root State", stats.root],
      ["Menu State", stats.menu],
      ["Final State", stats.final],
    ];
    statsEl.innerHTML = entries
      .map(
        ([lbl, num]) =>
          `<div class="panel-stat"><div class="num">${num ?? "-"}</div><div class="lbl">${lbl}</div></div>`
      )
      .join("");

    const links = document.getElementById("root-links");
    links.innerHTML = (data.roots || [])
      .map(
        (r) =>
          `<a class="link-row" href="/chat"><span class="link-title">${escapeHtml(
            r.title
          )}</span><span class="link-category">Root State</span></a>`
      )
      .join("");
  } catch (e) {
    console.error("Gagal memuat data tree", e);
  }
}

function escapeHtml(s) {
  const div = document.createElement("div");
  div.textContent = s == null ? "" : String(s);
  return div.innerHTML;
}

loadHome();
