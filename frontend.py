import streamlit as st

from app.tree_store import load_tree
from views.theme import inject_theme, render_footer, render_navbar


st.set_page_config(page_title="Otomata FSM Chatbot", layout="wide")


def count_node_types(tree: dict) -> dict:
    """Hitung ringkasan tree untuk statistik di home."""
    nodes = tree.get("nodes", [])
    enabled = [node for node in nodes if node.get("enabled", True)]
    menu = [node for node in enabled if node.get("children")]
    final = [node for node in enabled if not node.get("children") and node.get("answer")]
    return {
        "total": len(nodes),
        "enabled": len(enabled),
        "menu": len(menu),
        "final": len(final),
        "root": len(tree.get("root_nodes", [])),
    }


def render_home() -> None:
    """Landing page editorial: hero, statistik tree, fitur, dan CTA navigasi."""
    inject_theme()
    render_navbar("home")

    tree = load_tree()
    stats = count_node_types(tree)

    st.markdown('<div class="eyebrow">Finite State Machine assistant</div>', unsafe_allow_html=True)
    st.markdown(
        '<h1>Otomata chatbot yang menelusuri setiap '
        '<span class="underline-key">transition</span>.</h1>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<p class="editorial" style="font-size:19px; max-width:720px; color:var(--text-muted);">'
        "Ketik kebutuhanmu dengan bahasa bebas. Bot mengklasifikasi topik ke state yang relevan, "
        "lalu kamu menavigasi transition lewat tombol. State, event, dan output terlihat jelas "
        "melalui panel flow log."
        "</p>",
        unsafe_allow_html=True,
    )

    left, right = st.columns([3, 2])
    if left.button("Mulai Chat", use_container_width=True, type="primary"):
        st.switch_page("pages/1_Chat.py")
    if right.button("Atur Bot", use_container_width=True):
        st.switch_page("pages/2_Atur_Bot.py")

    st.write("")

    stat_col, panel_col = st.columns([2, 3])
    with stat_col:
        st.markdown(
            f"""
            <div class="automata-card">
              <h3>Ringkasan Bot</h3>
              <div class="meta-row"><span class="meta-label">Total Group</span><span class="meta-value">{stats['total']}</span></div>
              <div class="meta-row"><span class="meta-label">Root State</span><span class="meta-value">{stats['root']}</span></div>
              <div class="meta-row"><span class="meta-label">Menu State</span><span class="meta-value">{stats['menu']}</span></div>
              <div class="meta-row"><span class="meta-label">Final State</span><span class="meta-value">{stats['final']}</span></div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with panel_col:
        st.markdown(
            f"""
            <div class="dark-panel">
              <div class="eyebrow" style="color:#B8B5AA;">Current Machine</div>
              <div class="title">{tree.get('bot_name', 'Otomata FSM Chatbot')}</div>
              <div style="margin-top:18px;">
                <span class="state-pill">GLOBAL_ROUTER</span>
                <span class="state-pill">MENU</span>
                <span class="state-pill">FINAL</span>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("## Fitur Utama")
    features = [
        ("Global Router", "Klasifikasi free text ke Top 3 group paling relevan berdasarkan keyword."),
        ("State Navigation", "Pilih tombol untuk transisi ke sub-state. Tersedia Back dan Reset."),
        ("Flow Log", "Lihat alur keputusan bot per trigger: normalize, scoring, sampai response."),
        ("Admin Editor", "Atur state tree (group, children, answer, keywords) tanpa edit kode."),
    ]
    cols = st.columns(2)
    for index, (title, desc) in enumerate(features):
        cols[index % 2].markdown(
            f"""
            <div class="automata-card">
              <h3>{title}</h3>
              <p class="small-muted">{desc}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    render_footer()


render_home()
