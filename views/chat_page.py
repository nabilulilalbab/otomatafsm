import html

import streamlit as st

from app.fsm_engine import GLOBAL_ROUTER, handle_back, handle_free_text, handle_reset, handle_select_node
from views.theme import inject_theme, render_footer, render_navbar


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
    trace = st.session_state.last_flow_log
    if not trace:
        st.markdown(
            '<div class="dark-panel"><div class="eyebrow" style="color:#B8B5AA;">Flow Log</div>'
            '<p class="small-muted" style="color:#B8B5AA;">Belum ada proses. Kirim chat atau klik button '
            "untuk melihat alur bot.</p></div>",
            unsafe_allow_html=True,
        )
        return

    st.markdown(
        f"""
        <div class="dark-panel">
          <div class="eyebrow" style="color:#B8B5AA;">Flow Log</div>
          <div class="title" style="font-size:24px;">{html.escape(str(trace.get('trigger', '-')))}</div>
          <p class="small-muted" style="color:#B8B5AA; margin-top:8px;">Input: {html.escape(str(trace.get('input', '') or '-'))}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    for index, step in enumerate(trace.get("steps", []), start=1):
        with st.expander(f"{index}. {step['function']}", expanded=index <= 4):
            st.write(step["message"])
            if step.get("data"):
                st.json(step["data"])
    st.markdown("**Response**")
    st.info(trace.get("response_summary", "-"))


def render_chat_page(tree: dict) -> None:
    """Page chat dengan button group."""
    inject_theme()
    render_navbar("chat")
    init_chat()

    left, right = st.columns([1, 2])
    with left:
        render_flow_log()

    with right:
        st.markdown("## Chat")
        st.markdown(
            '<p class="small-muted">Ketik bebas untuk ganti topik kapan saja, '
            "atau pilih button yang disarankan bot.</p>",
            unsafe_allow_html=True,
        )
        state_label = st.session_state.current_node_id or "GLOBAL_ROUTER"
        breadcrumb = " > ".join(st.session_state.breadcrumb) or "GLOBAL_ROUTER"
        st.markdown(
            f"""
            <div class="automata-card" style="padding:18px 24px;">
              <div class="meta-row" style="border-top:none; padding-top:0;">
                <span class="meta-label">Current State</span><span class="meta-value">{html.escape(state_label)}</span>
              </div>
              <div class="meta-row"><span class="meta-label">Type</span><span class="meta-value">{html.escape(st.session_state.state_type)}</span></div>
              <div class="meta-row"><span class="meta-label">Breadcrumb</span><span class="meta-value">{html.escape(breadcrumb)}</span></div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        col_reset, col_back = st.columns(2)
        if col_reset.button("Reset chat"):
            reset_chat()
            st.rerun()
        if col_back.button("Back", disabled=not st.session_state.state_history):
            process_back(tree)
            st.rerun()

        for message in st.session_state.messages:
            bubble = "chat-user" if message["role"] == "user" else "chat-bot"
            st.markdown(
                f'<div class="{bubble}">{html.escape(message["content"])}</div>',
                unsafe_allow_html=True,
            )

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

    render_footer()
