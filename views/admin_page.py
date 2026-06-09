import streamlit as st

from app.chat_engine import get_node
from app.tree_store import (
    attach_node_to_parent,
    build_tree_rows,
    get_parent_options,
    make_node,
    save_tree,
    split_values,
    validate_node,
)
from views.theme import inject_theme, render_footer, render_navbar


DEFAULT_ADMIN_PASSWORD = "admin"


ADMIN_CSS = """
<style>
.tree-row {
  border: 1px solid rgba(20,20,19,0.08);
  border-radius: 12px;
  padding: 9px 12px;
  margin: 6px 0;
  background: var(--bg-card);
  color: var(--text-main);
  box-shadow: inset 3px 0 0 var(--border-soft);
}
.tree-row.missing {
  opacity: 0.6;
}
.tree-title {
  font-weight: 700;
  line-height: 1.25;
  margin-bottom: 2px;
}
.tree-meta {
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--text-muted);
}
.admin-help {
  border: 1px solid rgba(20,20,19,0.08);
  border-radius: 12px;
  padding: 14px;
  background: var(--bg-card);
  color: var(--text-main);
  margin-bottom: 12px;
}
</style>
"""


def _admin_password() -> str:
    """Ambil password admin dari secrets, fallback ke default untuk lokal."""
    try:
        return str(st.secrets.get("admin_password", DEFAULT_ADMIN_PASSWORD))
    except Exception:
        return DEFAULT_ADMIN_PASSWORD


def require_admin() -> bool:
    """Gate password sederhana. Return True kalau sudah ter-autentikasi."""
    inject_theme()
    render_navbar("admin")
    if st.session_state.get("admin_authed"):
        return True

    st.markdown("## Atur Bot")
    st.markdown(
        '<p class="small-muted">Halaman ini terproteksi. Masukkan password admin untuk lanjut.</p>',
        unsafe_allow_html=True,
    )
    with st.form("admin_login_form"):
        password = st.text_input("Password admin", type="password")
        submitted = st.form_submit_button("Masuk")

    if submitted:
        if password == _admin_password():
            st.session_state.admin_authed = True
            st.rerun()
        else:
            st.error("Password salah.")
    return False


def render_tree_explorer(tree: dict) -> None:
    """Panel kiri: tree group."""
    st.markdown("#### Tree Bot")
    st.caption("Group yang punya child adalah menu. Group tanpa child dan punya answer adalah jawaban final.")
    if not tree["root_nodes"]:
        st.info("Belum ada root group.")
        return

    for row in build_tree_rows(tree):
        node = get_node(tree, row["node_id"])
        is_menu = bool(node and node.get("children"))
        css_type = "missing" if row["missing"] else "menu" if is_menu else "final"
        type_label = "hilang/nonaktif" if row["missing"] else "menu" if is_menu else "final"
        indent = row["depth"] * 18
        st.markdown(
            f"""
            <div class="tree-row {css_type}" style="margin-left:{indent}px">
              <div class="tree-title">{row['title']}</div>
              <div class="tree-meta">{type_label}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if row["missing"]:
            continue

        if st.button("Pilih", key=row["key"]):
            st.session_state.selected_node_id = row["node_id"]
            st.rerun()


def render_node_detail(tree: dict) -> None:
    """Panel kanan: detail node terpilih."""
    node_id = st.session_state.get("selected_node_id", "")
    node = get_node(tree, node_id) if node_id else None
    st.markdown("#### Detail Group")
    if not node:
        st.info("Pilih group dari tree di kiri untuk melihat detail.")
        return

    st.write(f"ID: `{node['id']}`")
    st.write(f"Judul: **{node['title']}**")
    node_type = "Menu / punya turunan" if node["children"] else "Jawaban final"
    st.write(f"Jenis: **{node_type}**")
    st.write(f"Description: {node['description'] or '-'}")
    st.write("Keywords:")
    st.code(", ".join(node["keywords"]) or "-", language="text")
    st.write("Children:")
    st.code(", ".join(node["children"]) or "-", language="text")
    st.write("Answer:")
    st.write(node["answer"] or "-")


def render_add_node_form(tree: dict) -> None:
    """Form tambah root/child group."""
    st.markdown("#### Tambah Group")
    st.markdown(
        """
        <div class="admin-help">
        <b>Cara isi:</b><br>
        Pilih <b>Letakkan di</b> untuk menentukan parent. Pilih <b>Menu</b> kalau group ini masih punya turunan.
        Pilih <b>Jawaban final</b> kalau group ini langsung membalas user. Kamu tidak perlu isi child id manual.
        </div>
        """,
        unsafe_allow_html=True,
    )

    parent_options = get_parent_options(tree)
    parent_labels = [option["label"] for option in parent_options]
    with st.form("add_node_form", clear_on_submit=True):
        parent_label = st.selectbox("Letakkan di", parent_labels)
        node_type = st.radio("Jenis group", ["Menu / punya turunan", "Jawaban final"], horizontal=True)
        title = st.text_input("Judul button", placeholder="Contoh: Obat Hama")
        description = st.text_area("Description", placeholder="Keterangan yang muncul saat bot menyarankan group ini.")
        keywords = st.text_area("Keywords", placeholder="obat hama\nhama padi\ninsektisida")
        answer = ""
        if node_type == "Jawaban final":
            answer = st.text_area("Answer final", placeholder="Isi jawaban bot saat user memilih group ini.")
        enabled = st.checkbox("Aktif", value=True)
        submitted = st.form_submit_button("Tambah group")

    if not submitted:
        return

    parent_id = parent_options[parent_labels.index(parent_label)]["id"]
    node = make_node(
        title=title,
        description=description,
        keywords=split_values(keywords),
        children=[],
        answer=answer,
        enabled=enabled,
    )
    errors = validate_node(node)
    if errors:
        for error in errors:
            st.error(error)
        return

    attach_node_to_parent(tree, node, parent_id)
    save_tree(tree)
    st.success("Group baru disimpan.")
    st.rerun()


def render_edit_node_form(tree: dict) -> None:
    """Form edit node sederhana."""
    node_id = st.session_state.get("selected_node_id", "")
    node = get_node(tree, node_id) if node_id else None
    if not node:
        return

    st.markdown("#### Edit Group Terpilih")
    st.caption("Untuk edit lanjutan, children ids masih boleh diedit manual. Untuk tambah group baru, gunakan dropdown parent di form Tambah Group.")
    with st.form("edit_node_form"):
        title = st.text_input("Title", value=node["title"])
        description = st.text_area("Description", value=node["description"])
        keywords = st.text_area("Keywords", value="\n".join(node["keywords"]))
        children = st.text_area("Children ids", value="\n".join(node["children"]))
        answer = st.text_area("Answer final", value=node["answer"])
        enabled = st.checkbox("Aktif", value=node["enabled"])
        submitted = st.form_submit_button("Simpan perubahan")

    if submitted:
        node["title"] = title.strip() or node["title"]
        node["description"] = description.strip()
        node["keywords"] = split_values(keywords)
        node["children"] = split_values(children)
        node["answer"] = answer.strip()
        node["enabled"] = enabled
        errors = validate_node(node)
        if errors:
            for error in errors:
                st.error(error)
            return
        save_tree(tree)
        st.success("Perubahan disimpan.")
        st.rerun()

    if st.button("Hapus group terpilih"):
        delete_node(tree, node["id"])
        st.session_state.selected_node_id = ""
        save_tree(tree)
        st.rerun()


def delete_node(tree: dict, node_id: str) -> None:
    """Hapus node dan cabut referensinya dari root/children."""
    tree["nodes"] = [node for node in tree["nodes"] if node["id"] != node_id]
    tree["root_nodes"] = [root_id for root_id in tree["root_nodes"] if root_id != node_id]
    for node in tree["nodes"]:
        node["children"] = [child_id for child_id in node["children"] if child_id != node_id]


def render_settings(tree: dict) -> None:
    """Edit bot name dan fallback."""
    with st.form("settings_form"):
        st.markdown("#### Bot Settings")
        bot_name = st.text_input("Bot name", value=tree["bot_name"])
        fallback = st.text_area("Fallback", value=tree["fallback"])
        submitted = st.form_submit_button("Simpan settings")

    if submitted:
        tree["bot_name"] = bot_name.strip() or tree["bot_name"]
        tree["fallback"] = fallback.strip() or tree["fallback"]
        save_tree(tree)
        st.rerun()


def render_admin_page(tree: dict) -> None:
    """Dashboard admin tree explorer."""
    inject_theme()
    st.markdown(ADMIN_CSS, unsafe_allow_html=True)
    st.markdown("## Atur Bot")
    st.markdown(
        '<p class="small-muted">Semua group disimpan ke <code>data/bot_tree.json</code>.</p>',
        unsafe_allow_html=True,
    )
    st.markdown(
        """
        <div class="automata-card" style="padding:18px 24px;">
          <div class="meta-row" style="border-top:none; padding-top:0;"><span class="meta-label">Group</span><span class="meta-value">State</span></div>
          <div class="meta-row"><span class="meta-label">Children</span><span class="meta-value">Transition</span></div>
          <div class="meta-row"><span class="meta-label">Answer</span><span class="meta-value">Final State Output</span></div>
          <div class="meta-row"><span class="meta-label">Keywords</span><span class="meta-value">Global Router Classifier</span></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if st.button("Keluar admin"):
        st.session_state.admin_authed = False
        st.rerun()

    left, right = st.columns([1, 2])
    with left:
        render_tree_explorer(tree)
    with right:
        render_node_detail(tree)
        st.divider()
        render_edit_node_form(tree)
        st.divider()
        render_add_node_form(tree)
        st.divider()
        render_settings(tree)

    render_footer()
