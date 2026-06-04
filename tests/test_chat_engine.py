from app.chat_engine import (
    build_node_reply,
    build_reply,
    count_keyword_matches,
    get_children,
    resolve_node_selection,
    score_node,
    suggest_groups,
)
from app.flow_logger import finish_trace, log_step, new_trace
from app.fsm_engine import (
    EVENT_BACK,
    EVENT_FREE_TEXT,
    EVENT_RESET,
    EVENT_SELECT_NODE,
    GLOBAL_ROUTER,
    STATE_FINAL,
    STATE_MENU,
    STATE_ROUTER,
    build_breadcrumb,
    export_fsm_edges,
    get_state_type,
    handle_back,
    handle_free_text,
    handle_reset,
    handle_select_node,
    initial_fsm_state,
    is_transition_allowed,
)
from app.text import normalize_text, slugify
from app.tree_store import build_tree_rows, load_tree, normalize_node, normalize_tree, save_tree, split_values
from app.tree_store import attach_node_to_parent, get_parent_options


def test_normalize_text_removes_symbols_and_lowercases():
    assert normalize_text("OBAT!!! PADI???") == "obat padi"


def test_flow_logger_creates_single_trigger_trace():
    trace = new_trace("FREE_TEXT", "saya mau beli obat")
    log_step(trace, "test_func", "step jalan", {"ok": True})
    finish_trace(trace, "selesai")

    assert trace["trigger"] == "FREE_TEXT"
    assert trace["input"] == "saya mau beli obat"
    assert trace["steps"][0]["function"] == "test_func"
    assert trace["response_summary"] == "selesai"


def test_initial_fsm_state_starts_at_global_router():
    state = initial_fsm_state()

    assert state["current_node_id"] == GLOBAL_ROUTER
    assert state["state_history"] == []


def test_normalize_text_collapses_extra_spaces():
    assert normalize_text("  Padi   Kuning??   Banget ") == "padi kuning banget"


def test_slugify_makes_safe_node_id():
    assert slugify("Obat Pertanian!") == "obat_pertanian"


def test_split_values_accepts_commas_and_new_lines():
    values = split_values("obat, pestisida\nfungisida")

    assert values == ["obat", "pestisida", "fungisida"]


def test_normalize_node_handles_missing_title_keywords_and_children():
    node = normalize_node({"answer": "Jawaban aman."})

    assert node["title"] == "Group Tanpa Nama"
    assert node["id"] == "group_tanpa_nama"
    assert node["keywords"] == []
    assert node["children"] == []


def test_normalize_tree_skips_duplicate_node_id():
    tree = normalize_tree(
        {
            "root_nodes": ["a"],
            "nodes": [
                {"id": "a", "title": "A", "keywords": ["a"], "answer": "A"},
                {"id": "a", "title": "A Duplicate", "keywords": ["dup"], "answer": "Dup"},
            ],
        }
    )

    assert len(tree["nodes"]) == 1
    assert tree["nodes"][0]["title"] == "A"


def test_save_and_load_tree_roundtrip(tmp_path):
    path = tmp_path / "bot_tree.json"
    data = {
        "bot_name": "Test Bot",
        "fallback": "fallback",
        "root_nodes": ["root"],
        "nodes": [
            {
                "id": "root",
                "title": "Root",
                "description": "Root desc",
                "keywords": ["root"],
                "children": [],
                "answer": "Root answer",
                "enabled": True,
            }
        ],
    }

    save_tree(data, path)
    loaded = load_tree(path)

    assert loaded["bot_name"] == "Test Bot"
    assert loaded["nodes"][0]["title"] == "Root"


def test_load_tree_corrupt_json_falls_back_to_default(tmp_path):
    path = tmp_path / "bot_tree.json"
    path.write_text("{bad json", encoding="utf-8")

    loaded = load_tree(path)

    assert loaded["bot_name"] == "Asisten Sawah"
    assert loaded["nodes"] == []


def _tree():
    return normalize_tree(
        {
            "fallback": "fallback",
            "root_nodes": ["obat", "masalah", "budidaya"],
            "nodes": [
                {
                    "id": "obat",
                    "title": "Obat Pertanian",
                    "description": "Tentang obat.",
                    "keywords": ["obat", "pestisida", "hama"],
                    "children": ["analisa", "belajar"],
                    "answer": "",
                    "enabled": True,
                },
                {
                    "id": "analisa",
                    "title": "Analisa Gejala",
                    "description": "Analisa gejala.",
                    "keywords": ["gejala", "tanaman sakit", "padi sakit"],
                    "children": ["daun"],
                    "answer": "",
                    "enabled": True,
                },
                {
                    "id": "belajar",
                    "title": "Belajar Jenis Obat",
                    "description": "Belajar obat.",
                    "keywords": ["belajar obat", "jenis obat"],
                    "children": [],
                    "answer": "Jenis obat: insektisida, fungisida, herbisida.",
                    "enabled": True,
                },
                {
                    "id": "daun",
                    "title": "Gejala Daun",
                    "description": "Daun bermasalah.",
                    "keywords": ["daun", "kuning", "pucat"],
                    "children": [],
                    "answer": "Cek pola daun dan air.",
                    "enabled": True,
                },
                {
                    "id": "masalah",
                    "title": "Masalah Padi",
                    "description": "Masalah umum padi.",
                    "keywords": ["padi bermasalah", "padi sakit", "padi aneh"],
                    "children": ["daun"],
                    "answer": "",
                    "enabled": True,
                },
                {
                    "id": "budidaya",
                    "title": "Budidaya Padi",
                    "description": "Tanam sampai panen.",
                    "keywords": ["budidaya", "tanam", "panen"],
                    "children": [],
                    "answer": "Budidaya mencakup tanam, air, pupuk, panen.",
                    "enabled": True,
                },
                {
                    "id": "disabled",
                    "title": "Disabled",
                    "description": "Nonaktif.",
                    "keywords": ["rahasia"],
                    "children": [],
                    "answer": "Tidak boleh muncul.",
                    "enabled": False,
                },
            ],
        }
    )


def test_count_keyword_matches_exact_and_loose_order():
    assert count_keyword_matches("padi obat hama", ["obat hama"]) == 1


def test_score_node_exact_keyword():
    node = {"keywords": ["obat"]}

    scored = score_node("saya mau beli obat", node)

    assert scored["score"] == 10


def test_suggest_groups_exact_keyword():
    suggestions = suggest_groups("saya mau beli obat", _tree())

    assert suggestions[0]["id"] == "obat"


def test_suggest_groups_loose_keyword():
    suggestions = suggest_groups("obat buat tanaman padi sakit", _tree())

    assert {item["id"] for item in suggestions[:2]} == {"obat", "analisa"}


def test_suggest_groups_multiple_group_match_limited_to_top_three():
    suggestions = suggest_groups("obat hama padi sakit panen", _tree(), limit=3)

    assert len(suggestions) <= 3
    assert "obat" in {item["id"] for item in suggestions}


def test_ambiguous_input_suggests_problem_group():
    suggestions = suggest_groups("padi bermasalah", _tree())

    assert suggestions[0]["id"] == "masalah"


def test_random_input_falls_back_to_root_groups():
    suggestions = suggest_groups("halo bang", _tree())

    assert [item["id"] for item in suggestions] == ["obat", "masalah", "budidaya"]


def test_empty_input_falls_back_to_root_groups():
    suggestions = suggest_groups("   ", _tree())

    assert [item["id"] for item in suggestions] == ["obat", "masalah", "budidaya"]


def test_capital_and_symbols_still_match():
    suggestions = suggest_groups("OBAT!!! PADI???", _tree())

    assert suggestions[0]["id"] == "obat"


def test_disabled_node_is_not_suggested():
    suggestions = suggest_groups("rahasia", _tree())

    assert "disabled" not in {item["id"] for item in suggestions}


def test_disabled_final_node_cannot_be_selected():
    reply = resolve_node_selection("disabled", _tree())

    assert "belum tersedia" in reply["text"]


def test_build_reply_returns_group_buttons():
    reply = build_reply("saya mau beli obat", _tree())

    assert reply["buttons"]
    assert reply["buttons"][0]["id"] == "obat"


def test_node_menu_displays_children_buttons():
    reply = resolve_node_selection("obat", _tree())

    assert reply["buttons"] == [
        {"id": "analisa", "label": "Analisa Gejala"},
        {"id": "belajar", "label": "Belajar Jenis Obat"},
    ]


def test_node_final_displays_answer():
    reply = resolve_node_selection("belajar", _tree())

    assert reply["text"] == "Jenis obat: insektisida, fungisida, herbisida."
    assert reply["buttons"] == []


def test_missing_child_id_is_skipped_safely():
    tree = normalize_tree(
        {
            "root_nodes": ["a"],
            "nodes": [{"id": "a", "title": "A", "keywords": ["a"], "children": ["missing"]}],
        }
    )

    assert get_children(tree, "a") == []


def test_child_loop_does_not_duplicate_parent():
    tree = normalize_tree(
        {
            "root_nodes": ["a"],
            "nodes": [
                {"id": "a", "title": "A", "keywords": ["a"], "children": ["b"]},
                {"id": "b", "title": "B", "keywords": ["b"], "children": ["a"]},
            ],
        }
    )

    children = get_children(tree, "b")

    assert children == []


def test_node_without_keywords_does_not_crash():
    tree = normalize_tree({"root_nodes": ["a"], "nodes": [{"id": "a", "title": "A", "answer": "A"}]})

    assert suggest_groups("anything", tree) == [tree["nodes"][0]]


def test_node_without_answer_and_children_returns_safe_message():
    reply = build_node_reply({"id": "x", "title": "Kosong", "answer": "", "children": []}, [])

    assert "belum punya" in reply["text"]


def test_invalid_selection_id_does_not_crash():
    reply = resolve_node_selection("missing", _tree())

    assert "belum tersedia" in reply["text"]


def test_all_root_disabled_returns_safe_fallback():
    tree = normalize_tree(
        {
            "fallback": "fallback",
            "root_nodes": ["a"],
            "nodes": [{"id": "a", "title": "A", "keywords": ["a"], "enabled": False}],
        }
    )

    reply = build_reply("random", tree)

    assert reply["text"] == "fallback"
    assert reply["buttons"] == []


def test_admin_tree_rows_have_unique_keys_for_shared_child():
    tree = normalize_tree(
        {
            "root_nodes": ["analisa", "masalah"],
            "nodes": [
                {"id": "analisa", "title": "Analisa", "keywords": ["analisa"], "children": ["gejala_daun"]},
                {"id": "masalah", "title": "Masalah", "keywords": ["masalah"], "children": ["gejala_daun"]},
                {"id": "gejala_daun", "title": "Gejala Daun", "keywords": ["daun"], "answer": "Cek daun."},
            ],
        }
    )

    rows = build_tree_rows(tree)
    keys = [row["key"] for row in rows]
    gejala_rows = [row for row in rows if row["node_id"] == "gejala_daun"]

    assert len(gejala_rows) == 2
    assert len(keys) == len(set(keys))


def test_admin_tree_rows_show_loop_without_infinite_recursion():
    tree = normalize_tree(
        {
            "root_nodes": ["a"],
            "nodes": [
                {"id": "a", "title": "A", "keywords": ["a"], "children": ["b"]},
                {"id": "b", "title": "B", "keywords": ["b"], "children": ["a"]},
            ],
        }
    )

    rows = build_tree_rows(tree)

    assert len(rows) == 3
    assert rows[-1]["missing"] is True
    assert "loop dilewati" in rows[-1]["title"]


def test_parent_options_include_root_and_enabled_nodes():
    tree = _tree()

    options = get_parent_options(tree)

    assert options[0] == {"id": "", "label": "Menu Utama / Root"}
    assert {"id": "obat", "label": "Obat Pertanian"} in options
    assert {"id": "disabled", "label": "Disabled"} not in options


def test_attach_node_to_parent_adds_child_to_parent():
    tree = _tree()
    node = normalize_node({"id": "baru", "title": "Baru", "keywords": ["baru"], "answer": "Jawab"})

    attach_node_to_parent(tree, node, "obat")
    parent = next(item for item in tree["nodes"] if item["id"] == "obat")

    assert "baru" in parent["children"]
    assert node in tree["nodes"]


def test_attach_node_to_parent_empty_parent_adds_root():
    tree = _tree()
    node = normalize_node({"id": "root_baru", "title": "Root Baru", "keywords": ["root"], "answer": "Jawab"})

    attach_node_to_parent(tree, node, "")

    assert "root_baru" in tree["root_nodes"]


def test_fsm_free_text_exact_keyword_creates_trace_and_buttons():
    result = handle_free_text("saya mau beli obat", _tree())

    assert result["current_node_id"] == GLOBAL_ROUTER
    assert result["buttons"][0]["id"] == "obat"
    assert result["trace"]["trigger"] == EVENT_FREE_TEXT
    assert result["trace"]["response_summary"]


def test_fsm_free_text_loose_keyword_matches():
    result = handle_free_text("obat buat tanaman padi sakit", _tree())

    assert {button["id"] for button in result["buttons"][:2]} == {"obat", "analisa"}


def test_fsm_random_free_text_falls_back_to_root():
    result = handle_free_text("halo bang", _tree())

    assert [button["id"] for button in result["buttons"]] == ["obat", "masalah", "budidaya"]


def test_fsm_select_valid_node_moves_current_state_and_history():
    result = handle_select_node("obat", _tree())

    assert result["current_node_id"] == "obat"
    assert result["state_history"] == []
    assert result["state_type"] == STATE_MENU
    assert result["trace"]["trigger"] == EVENT_SELECT_NODE


def test_fsm_select_invalid_node_does_not_crash_or_move_state():
    result = handle_select_node("missing", _tree(), current_node_id="obat", state_history=[GLOBAL_ROUTER])

    assert result["current_node_id"] == "obat"
    assert result["state_history"] == [GLOBAL_ROUTER]
    assert "belum tersedia" in result["text"]


def test_fsm_select_disabled_node_is_rejected():
    result = handle_select_node("disabled", _tree(), current_node_id="obat", state_history=[GLOBAL_ROUTER])

    assert result["current_node_id"] == "obat"
    assert "belum tersedia" in result["text"]


def test_fsm_rejects_non_child_transition_from_current_state():
    result = handle_select_node("budidaya", _tree(), current_node_id="obat", state_history=[])

    assert result["current_node_id"] == "obat"
    assert "bukan transisi" in result["text"]


def test_fsm_menu_node_outputs_child_buttons():
    result = handle_select_node("obat", _tree())

    assert [button["id"] for button in result["buttons"]] == ["analisa", "belajar"]


def test_fsm_final_node_outputs_answer_without_buttons():
    result = handle_select_node("belajar", _tree(), current_node_id="obat", state_history=[GLOBAL_ROUTER])

    assert result["current_node_id"] == "belajar"
    assert result["state_type"] == STATE_FINAL
    assert result["buttons"] == []
    assert "insektisida" in result["text"]


def test_fsm_history_grows_across_transitions():
    first = handle_select_node("obat", _tree())
    second = handle_select_node("analisa", _tree(), first["current_node_id"], first["state_history"])

    assert second["state_history"] == ["obat"]


def test_fsm_back_returns_previous_state():
    result = handle_back(_tree(), current_node_id="analisa", state_history=["obat"])

    assert result["current_node_id"] == "obat"
    assert result["state_history"] == []
    assert result["trace"]["trigger"] == EVENT_BACK


def test_fsm_back_empty_history_is_safe():
    result = handle_back(_tree(), current_node_id="")

    assert result["current_node_id"] == GLOBAL_ROUTER
    assert result["buttons"]


def test_fsm_reset_clears_state_and_history():
    result = handle_reset()

    assert result["current_node_id"] == GLOBAL_ROUTER
    assert result["state_history"] == []
    assert result["buttons"] == []
    assert result["trace"]["trigger"] == EVENT_RESET


def test_fsm_free_text_from_inside_state_changes_topic_globally():
    result = handle_free_text("panen", _tree(), current_node_id="obat", state_history=[GLOBAL_ROUTER])

    assert result["current_node_id"] == GLOBAL_ROUTER
    assert "budidaya" in {button["id"] for button in result["buttons"]}


def test_trace_is_new_per_trigger_not_appended():
    first = handle_free_text("obat", _tree())
    second = handle_select_node("obat", _tree(), first["current_node_id"], first["state_history"])

    assert first["trace"]["trigger"] == EVENT_FREE_TEXT
    assert second["trace"]["trigger"] == EVENT_SELECT_NODE
    assert first["trace"] is not second["trace"]


def test_fsm_trace_contains_core_function_steps():
    result = handle_free_text("obat", _tree())
    functions = {step["function"] for step in result["trace"]["steps"]}

    assert "handle_free_text" in functions
    assert "normalize_text" in functions
    assert "suggest_groups" in functions
    assert "build_group_reply" in functions


def test_get_state_type_router_menu_final():
    tree = _tree()

    assert get_state_type(tree, GLOBAL_ROUTER) == STATE_ROUTER
    assert get_state_type(tree, "obat") == STATE_MENU
    assert get_state_type(tree, "belajar") == STATE_FINAL


def test_transition_allowed_from_router_and_child_only():
    tree = _tree()

    assert is_transition_allowed(tree, GLOBAL_ROUTER, "budidaya")[0] is True
    assert is_transition_allowed(tree, "obat", "analisa")[0] is True
    assert is_transition_allowed(tree, "obat", "budidaya")[0] is False


def test_breadcrumb_uses_history_titles():
    breadcrumb = build_breadcrumb(_tree(), "analisa", ["obat"])

    assert breadcrumb == ["Obat Pertanian", "Analisa Gejala"]


def test_export_fsm_edges_contains_router_and_child_transitions():
    edges = export_fsm_edges(_tree())

    assert {"from": "GLOBAL_ROUTER", "to": "obat", "event": "FREE_TEXT_MATCH_OR_ROOT"} in edges
    assert {"from": "obat", "to": "analisa", "event": "SELECT_NODE"} in edges


def test_rejected_transition_is_logged():
    result = handle_select_node("budidaya", _tree(), current_node_id="obat", state_history=[])
    messages = [step["message"] for step in result["trace"]["steps"]]

    assert "Transisi ditolak oleh validasi FSM" in messages
