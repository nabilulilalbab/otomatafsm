import streamlit as st

from app.chat_engine import get_node
from app.fsm_engine import GLOBAL_ROUTER, handle_back, handle_free_text, handle_reset, handle_select_node
from app.tree_store import (
    attach_node_to_parent,
    build_tree_rows,
    get_parent_options,
    load_tree,
    make_node,
    save_tree,
    split_values,
    validate_node,
)


st.set_page_config(page_title="Smart Group Menu Bot", layout="wide")


ADMIN_CSS = """
<style>
.tree-row {
  border: 1px solid rgba(128, 128, 128, 0.28);
  border-radius: 8px;
  padding: 9px 12px;
  margin: 6px 0;
  background: var(--secondary-background-color);
  color: var(--text-color);
  box-shadow: inset 3px 0 0 rgba(128, 128, 128, 0.45);
}
.tree-row.missing {
  opacity: 0.68;
}
.tree-title {
  font-weight: 700;
  line-height: 1.25;
  margin-bottom: 2px;
}
.tree-meta {
  font-size: 12px;
  opacity: 0.72;
}
.admin-help {
  border: 1px solid rgba(128, 128, 128, 0.28);
  border-radius: 8px;
  padding: 12px;
  background: var(--secondary-background-color);
  color: var(--text-color);
  margin-bottom: 12px;
}
</style>
"""


def init_chat() -> None:
    """Siapkan memory chat dan button terakhir."""
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {
                "role": "assistant",
                "content": "Halo, ceritain kebutuhanmu. Aku akan sarankan topik yang paling cocok.",
                "buttons": [],
            }
        ]
    if "last_buttons" not in st.session_state:
        st.session_state.last_buttons = []
    if "selected_node_id" not in st.session_state:
        st.session_state.selected_node_id = ""
    if "current_node_id" not in st.session_state:
        st.session_state.current_node_id = GLOBAL_ROUTER
    if "state_history" not in st.session_state:
        st.session_state.state_history = []
    if "last_flow_log" not in st.session_state:
        st.session_state.last_flow_log = {}
    if "state_type" not in st.session_state:
        st.session_state.state_type = "router"
    if "breadcrumb" not in st.session_state:
        st.session_state.breadcrumb = []


def reset_chat() -> None:
    """Kosongkan percakapan tanpa menghapus tree bot."""
    result = handle_reset()
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": result["text"],
            "buttons": [],
        }
    ]
    st.session_state.last_buttons = []
    apply_fsm_result(result)


def append_user_message(text: str) -> None:
    """Tambahkan pesan user ke chat."""
    st.session_state.messages.append({"role": "user", "content": text, "buttons": []})


def append_bot_reply(reply: dict) -> None:
    """Tambahkan response bot dan simpan button terakhir."""
    buttons = reply.get("buttons", [])
    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": reply.get("text", ""),
            "buttons": buttons,
        }
    )
    st.session_state.last_buttons = buttons


def apply_fsm_result(result: dict) -> None:
    """Simpan state FSM terbaru dan flow log terakhir."""
    st.session_state.current_node_id = result.get("current_node_id", GLOBAL_ROUTER)
    st.session_state.state_history = result.get("state_history", [])
    st.session_state.state_type = result.get("state_type", "router")
    st.session_state.breadcrumb = result.get("breadcrumb", [])
    st.session_state.last_flow_log = result.get("trace", {})


def process_free_text(tree: dict, text: str) -> None:
    """Handle chat bebas: selalu pakai classifier global."""
    append_user_message(text)
    result = handle_free_text(text, tree, st.session_state.current_node_id, st.session_state.state_history)
    append_bot_reply(result)
    apply_fsm_result(result)


def process_button(tree: dict, button: dict) -> None:
    """Handle klik button group/sub-group."""
    append_user_message(button["label"])
    result = handle_select_node(button["id"], tree, st.session_state.current_node_id, st.session_state.state_history)
    append_bot_reply(result)
    apply_fsm_result(result)


def process_back(tree: dict) -> None:
    """Handle tombol Back FSM."""
    append_user_message("Back")
    result = handle_back(tree, st.session_state.current_node_id, st.session_state.state_history)
    append_bot_reply(result)
    apply_fsm_result(result)


def render_flow_log() -> None:
    """Panel kiri: flow log hanya untuk trigger terakhir."""
    st.markdown("#### Flow Log")
    trace = st.session_state.last_flow_log
    if not trace:
        st.info("Belum ada proses. Kirim chat atau klik button untuk melihat alur bot.")
        return

    st.write(f"Trigger: `{trace.get('trigger', '-')}`")
    st.write(f"Input: `{trace.get('input', '')}`")
    for index, step in enumerate(trace.get("steps", []), start=1):
        with st.expander(f"{index}. {step['function']}", expanded=index <= 4):
            st.write(step["message"])
            if step.get("data"):
                st.json(step["data"])
    st.markdown("**Response**")
    st.info(trace.get("response_summary", "-"))


def render_chat_tab(tree: dict) -> None:
    """Tab chat dengan button group."""
    left, right = st.columns([1, 2])
    with left:
        render_flow_log()

    with right:
        st.subheader("Chat")
        st.caption("Ketik bebas untuk ganti topik kapan saja, atau pilih button yang disarankan bot.")
        state_label = st.session_state.current_node_id or "GLOBAL_ROUTER"
        breadcrumb = " > ".join(st.session_state.breadcrumb) or "GLOBAL_ROUTER"
        st.caption(
            f"Current state: `{state_label}` | Type: `{st.session_state.state_type}` | "
            f"Breadcrumb: `{breadcrumb}`"
        )

        col_reset, col_back = st.columns(2)
        if col_reset.button("Reset chat"):
            reset_chat()
            st.rerun()
        if col_back.button("Back", disabled=not st.session_state.state_history):
            process_back(tree)
            st.rerun()

        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        if st.session_state.last_buttons:
            cols = st.columns(min(len(st.session_state.last_buttons), 3))
            for index, button in enumerate(st.session_state.last_buttons):
                if cols[index % 3].button(button["label"], key=f"chat_button_{button['id']}_{index}"):
                    process_button(tree, button)
                    st.rerun()

        user_message = st.chat_input("Tulis pesan...")
        if user_message:
            process_free_text(tree, user_message)
            st.rerun()


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
    node_id = st.session_state.selected_node_id
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
    node_id = st.session_state.selected_node_id
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


def render_admin_tab(tree: dict) -> None:
    """Dashboard admin tree explorer."""
    st.markdown(ADMIN_CSS, unsafe_allow_html=True)
    st.subheader("Atur Bot")
    st.caption("Semua group disimpan ke `data/bot_tree.json`.")
    st.info("FSM: Group = State, Children = Transition, Answer = Final State Output, Keywords = Global Router Classifier.")

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


def main() -> None:
    init_chat()
    tree = load_tree()

    chat_tab, admin_tab = st.tabs(["Chat", "Atur Bot"])
    with chat_tab:
        render_chat_tab(tree)
    with admin_tab:
        render_admin_tab(tree)


if __name__ == "__main__":
    main()
