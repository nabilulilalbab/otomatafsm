from app.chat_engine import build_reply, get_children, get_node, resolve_node_selection
from app.flow_logger import finish_trace, log_step, new_trace


GLOBAL_ROUTER = ""
STATE_ROUTER = "router"
STATE_MENU = "menu"
STATE_FINAL = "final"
EVENT_FREE_TEXT = "FREE_TEXT"
EVENT_SELECT_NODE = "SELECT_NODE"
EVENT_BACK = "BACK"
EVENT_RESET = "RESET"


def initial_fsm_state() -> dict:
    """State awal FSM untuk session chat."""
    return {
        "current_node_id": GLOBAL_ROUTER,
        "state_history": [],
    }


def handle_free_text(text: str, tree: dict, current_node_id: str = "", state_history: list[str] | None = None) -> dict:
    """Event FREE_TEXT: selalu masuk global router untuk ganti topik bebas."""
    trace = new_trace(EVENT_FREE_TEXT, text)
    state_history = list(state_history or [])
    log_step(
        trace,
        "handle_free_text",
        "Menerima chat bebas dan mengarahkannya ke GLOBAL_ROUTER",
        {"previous_state": current_node_id, "history": state_history},
    )

    reply = build_reply(text, tree, trace)
    next_state = GLOBAL_ROUTER
    log_step(trace, "handle_free_text", "State diset ke GLOBAL_ROUTER karena ini global classifier", {"next_state": next_state})

    return _fsm_result(tree, reply, next_state, state_history, finish_trace(trace, _summary(reply)))


def handle_select_node(node_id: str, tree: dict, current_node_id: str = "", state_history: list[str] | None = None) -> dict:
    """Event SELECT_NODE: validasi node, transisi ke node, tampilkan output node."""
    trace = new_trace(EVENT_SELECT_NODE, node_id)
    state_history = list(state_history or [])
    log_step(
        trace,
        "handle_select_node",
        "Menerima pilihan button sebagai event transisi FSM",
        {"current_state": current_node_id, "selected_node_id": node_id, "history": state_history},
    )

    node = get_node(tree, node_id, trace)
    if not node:
        reply = resolve_node_selection(node_id, tree, trace)
        log_step(trace, "handle_select_node", "Transisi ditolak karena node invalid/nonaktif", {"next_state": current_node_id})
        return _fsm_result(tree, reply, current_node_id, state_history, finish_trace(trace, _summary(reply)))

    allowed, reason = is_transition_allowed(tree, current_node_id, node_id, trace)
    if not allowed:
        reply = {
            "text": "Pilihan itu bukan transisi dari state saat ini. Ketik topik baru kalau ingin ganti arah percakapan.",
            "buttons": [{"id": child["id"], "label": child["title"]} for child in get_children(tree, current_node_id, trace=trace)],
        }
        log_step(
            trace,
            "handle_select_node",
            "Transisi ditolak oleh validasi FSM",
            {"current_state": current_node_id, "target_state": node_id, "reason": reason},
        )
        return _fsm_result(tree, reply, current_node_id, state_history, finish_trace(trace, _summary(reply)))

    if current_node_id and current_node_id != node_id:
        state_history.append(current_node_id)

    reply = resolve_node_selection(node_id, tree, trace)
    log_step(
        trace,
        "handle_select_node",
        "Transisi valid, current_state berpindah",
        {
            "next_state": node_id,
            "state_type": get_state_type(tree, node_id),
            "history": state_history,
            "breadcrumb": build_breadcrumb(tree, node_id, state_history),
        },
    )
    return _fsm_result(tree, reply, node_id, state_history, finish_trace(trace, _summary(reply)))


def handle_back(tree: dict, current_node_id: str = "", state_history: list[str] | None = None) -> dict:
    """Event BACK: kembali ke state sebelumnya jika ada."""
    trace = new_trace(EVENT_BACK, "Back")
    state_history = list(state_history or [])
    log_step(trace, "handle_back", "Menerima event BACK", {"current_state": current_node_id, "history": state_history})

    if not state_history:
        reply = build_reply("", tree, trace)
        log_step(trace, "handle_back", "History kosong, kembali ke root suggestions", {"next_state": GLOBAL_ROUTER})
        return _fsm_result(tree, reply, GLOBAL_ROUTER, [], finish_trace(trace, _summary(reply)))

    previous_state = state_history.pop()
    if previous_state == GLOBAL_ROUTER:
        reply = build_reply("", tree, trace)
        log_step(trace, "handle_back", "Previous state adalah GLOBAL_ROUTER", {"next_state": GLOBAL_ROUTER})
        return _fsm_result(tree, reply, GLOBAL_ROUTER, state_history, finish_trace(trace, _summary(reply)))

    reply = resolve_node_selection(previous_state, tree, trace)
    log_step(trace, "handle_back", "Kembali ke state sebelumnya", {"next_state": previous_state, "history": state_history})
    return _fsm_result(tree, reply, previous_state, state_history, finish_trace(trace, _summary(reply)))


def handle_reset() -> dict:
    """Event RESET: kosongkan current state dan history."""
    trace = new_trace(EVENT_RESET, "Reset")
    log_step(trace, "handle_reset", "Reset FSM ke GLOBAL_ROUTER", {"next_state": GLOBAL_ROUTER, "history": []})
    reply = {
        "text": "Chat di-reset. Kamu bisa mulai dari topik apa saja.",
        "buttons": [],
    }
    return _fsm_result({"nodes": [], "root_nodes": []}, reply, GLOBAL_ROUTER, [], finish_trace(trace, _summary(reply)))


def _fsm_result(tree: dict, reply: dict, current_node_id: str, state_history: list[str], trace: dict) -> dict:
    """Bentuk standar result FSM untuk frontend."""
    return {
        "text": reply.get("text", ""),
        "buttons": reply.get("buttons", []),
        "current_node_id": current_node_id,
        "state_history": state_history,
        "state_type": get_state_type(tree, current_node_id),
        "breadcrumb": build_breadcrumb(tree, current_node_id, state_history),
        "trace": trace,
    }


def _summary(reply: dict) -> str:
    """Ringkas output untuk panel flow log."""
    button_count = len(reply.get("buttons", []))
    if button_count:
        return f"Menampilkan {button_count} button pilihan."
    return "Menampilkan jawaban final tanpa button."


def get_state_type(tree: dict, node_id: str) -> str:
    """Tentukan tipe state formal: router, menu, atau final."""
    if node_id == GLOBAL_ROUTER:
        return STATE_ROUTER
    node = get_node(tree, node_id)
    if not node:
        return "unknown"
    if node.get("children"):
        return STATE_MENU
    return STATE_FINAL


def is_transition_allowed(tree: dict, current_node_id: str, target_node_id: str, trace: dict | None = None) -> tuple[bool, str]:
    """Validasi transisi FSM: dari router boleh ke root/hasil suggestion; dari node harus ke child."""
    if current_node_id == GLOBAL_ROUTER:
        log_step(trace, "is_transition_allowed", "Transisi dari GLOBAL_ROUTER diizinkan", {"target_state": target_node_id})
        return True, "router_allows_selection"

    current = get_node(tree, current_node_id, trace)
    if not current:
        log_step(trace, "is_transition_allowed", "Current state tidak valid", {"current_state": current_node_id})
        return False, "current_state_invalid"

    if target_node_id in current.get("children", []):
        log_step(
            trace,
            "is_transition_allowed",
            "Target adalah child dari current state",
            {"current_state": current_node_id, "target_state": target_node_id},
        )
        return True, "target_is_child"

    return False, "target_not_child"


def build_breadcrumb(tree: dict, current_node_id: str, state_history: list[str] | None = None) -> list[str]:
    """Bangun breadcrumb title dari history + current state."""
    titles = []
    for node_id in list(state_history or []) + ([current_node_id] if current_node_id else []):
        if node_id == GLOBAL_ROUTER:
            titles.append("GLOBAL_ROUTER")
            continue
        node = get_node(tree, node_id)
        if node:
            titles.append(node["title"])
    return titles


def export_fsm_edges(tree: dict) -> list[dict]:
    """Export edge FSM untuk diagram/laporan otomata."""
    edges = []
    for root_id in tree.get("root_nodes", []):
        edges.append({"from": "GLOBAL_ROUTER", "to": root_id, "event": "FREE_TEXT_MATCH_OR_ROOT"})
    for node in tree.get("nodes", []):
        for child_id in node.get("children", []):
            edges.append({"from": node["id"], "to": child_id, "event": "SELECT_NODE"})
    return edges
