from app.text import normalize_text
from app.flow_logger import log_step


def count_keyword_matches(message: str, keywords: list[str], trace: dict | None = None) -> int:
    """Hitung keyword/frasa yang cocok persis atau semua katanya muncul."""
    normalized_message = normalize_text(message)
    message_words = set(normalized_message.split())
    total = 0
    matched_keywords = []

    for keyword in keywords:
        normalized_keyword = normalize_text(keyword)
        if not normalized_keyword:
            continue

        keyword_words = set(normalized_keyword.split())
        exact_phrase_match = normalized_keyword in normalized_message
        loose_word_match = keyword_words.issubset(message_words)
        if exact_phrase_match or loose_word_match:
            total += 1
            matched_keywords.append(keyword)

    log_step(
        trace,
        "count_keyword_matches",
        "Menghitung keyword yang cocok",
        {"matches": total, "matched_keywords": matched_keywords},
    )
    return total


def score_node(message: str, node: dict, trace: dict | None = None) -> dict:
    """Nilai relevansi node dari keyword."""
    matches = count_keyword_matches(message, node.get("keywords", []), trace)
    score = matches * 10
    log_step(
        trace,
        "score_node",
        "Memberi skor node dari keyword",
        {"node_id": node.get("id"), "title": node.get("title"), "matches": matches, "score": score},
    )
    return {
        "node": node,
        "matches": matches,
        "score": score,
    }


def get_node(tree: dict, node_id: str, trace: dict | None = None) -> dict | None:
    """Ambil node aktif dari id."""
    for node in tree.get("nodes", []):
        if node.get("id") == node_id and node.get("enabled", True):
            log_step(trace, "get_node", "Node aktif ditemukan", {"node_id": node_id, "title": node.get("title")})
            return node
    log_step(trace, "get_node", "Node tidak ditemukan atau nonaktif", {"node_id": node_id})
    return None


def get_children(tree: dict, node_id: str, max_depth: int = 20, trace: dict | None = None) -> list[dict]:
    """Ambil child aktif dari node; skip child hilang dan cegah loop traversal."""
    parent = get_node(tree, node_id, trace)
    if not parent:
        return []

    children = []
    visited = {node_id}
    for child_id in parent.get("children", [])[:max_depth]:
        if child_id in visited:
            continue
        visited.add(child_id)

        child = get_node(tree, child_id, trace)
        if child and not _can_reach_node(tree, child["id"], node_id, max_depth=max_depth):
            children.append(child)
    log_step(
        trace,
        "get_children",
        "Mengambil child aktif untuk state",
        {"node_id": node_id, "children": [child["id"] for child in children]},
    )
    return children


def _can_reach_node(tree: dict, start_id: str, target_id: str, max_depth: int = 20) -> bool:
    """Cek apakah start bisa kembali ke target; dipakai untuk cegah loop menu."""
    stack = [(start_id, 0)]
    visited = set()
    while stack:
        current_id, depth = stack.pop()
        if current_id == target_id:
            return True
        if current_id in visited or depth >= max_depth:
            continue
        visited.add(current_id)

        current = get_node(tree, current_id)
        if not current:
            continue
        for child_id in current.get("children", []):
            stack.append((child_id, depth + 1))
    return False


def get_root_nodes(tree: dict, trace: dict | None = None) -> list[dict]:
    """Ambil root aktif untuk fallback/menu awal."""
    roots = []
    for node_id in tree.get("root_nodes", []):
        node = get_node(tree, node_id, trace)
        if node:
            roots.append(node)
    log_step(trace, "get_root_nodes", "Mengambil root state aktif", {"roots": [node["id"] for node in roots]})
    return roots


def suggest_groups(message: str, tree: dict, limit: int = 3, trace: dict | None = None) -> list[dict]:
    """Sarankan group paling relevan; fallback ke root jika tidak ada match."""
    normalized_message = normalize_text(message)
    log_step(
        trace,
        "normalize_text",
        "Input dinormalisasi untuk classifier global",
        {"raw": message, "normalized": normalized_message},
    )
    if not normalized_message:
        roots = get_root_nodes(tree, trace)[:limit]
        log_step(trace, "suggest_groups", "Input kosong, fallback ke root groups", {"suggestions": [n["id"] for n in roots]})
        return roots

    scored_nodes = []
    for index, node in enumerate(tree.get("nodes", [])):
        if not node.get("enabled", True):
            continue

        scored = score_node(message, node, trace)
        if scored["score"] <= 0:
            continue

        scored["index"] = index
        scored_nodes.append(scored)

    if not scored_nodes:
        roots = get_root_nodes(tree, trace)[:limit]
        log_step(trace, "suggest_groups", "Tidak ada match, fallback ke root groups", {"suggestions": [n["id"] for n in roots]})
        return roots

    best = sorted(
        scored_nodes,
        key=lambda item: (item["score"], -item["index"]),
        reverse=True,
    )
    suggestions = [item["node"] for item in best[:limit]]
    log_step(trace, "suggest_groups", "Top group suggestion ditemukan", {"suggestions": [n["id"] for n in suggestions]})
    return suggestions


def build_group_reply(nodes: list[dict], fallback: str | None = None, trace: dict | None = None) -> dict:
    """Bangun response menu berisi button pilihan group."""
    if not nodes:
        log_step(trace, "build_group_reply", "Tidak ada node, memakai fallback", {"buttons": 0})
        return {
            "text": fallback or "Belum ada group yang bisa dipilih.",
            "buttons": [],
        }

    lines = ["Aku sarankan pilih salah satu topik ini:"]
    for node in nodes:
        description = node.get("description") or "Buka topik ini."
        lines.append(f"- {node['title']}: {description}")

    reply = {
        "text": "\n".join(lines),
        "buttons": [{"id": node["id"], "label": node["title"]} for node in nodes],
    }
    log_step(trace, "build_group_reply", "Membuat response group suggestion", {"buttons": len(reply["buttons"])})
    return reply


def build_node_reply(node: dict, children: list[dict], trace: dict | None = None) -> dict:
    """Bangun response saat user memilih satu node."""
    if children:
        lines = [f"{node['title']}"]
        if node.get("description"):
            lines.append(node["description"])
        lines.append("Pilih bagian yang paling cocok:")
        for child in children:
            description = child.get("description") or "Buka pilihan ini."
            lines.append(f"- {child['title']}: {description}")
        reply = {
            "text": "\n".join(lines),
            "buttons": [{"id": child["id"], "label": child["title"]} for child in children],
        }
        log_step(trace, "build_node_reply", "Node menu menghasilkan child buttons", {"node_id": node.get("id"), "buttons": len(reply["buttons"])})
        return reply

    if node.get("answer"):
        reply = {
            "text": node["answer"],
            "buttons": [],
        }
        log_step(trace, "build_node_reply", "Node final menghasilkan jawaban", {"node_id": node.get("id")})
        return reply

    log_step(trace, "build_node_reply", "Node tidak punya child atau answer", {"node_id": node.get("id")})
    return {
        "text": "Topik ini belum punya pilihan lanjutan atau jawaban final.",
        "buttons": [],
    }


def resolve_node_selection(node_id: str, tree: dict, trace: dict | None = None) -> dict:
    """Handle klik button group/sub-group."""
    node = get_node(tree, node_id, trace)
    if not node:
        roots = get_root_nodes(tree, trace)
        log_step(trace, "resolve_node_selection", "Pilihan node invalid/nonaktif", {"node_id": node_id})
        return {
            "text": "Pilihan itu belum tersedia atau sedang nonaktif. Coba pilih topik lain ya.",
            "buttons": [{"id": item["id"], "label": item["title"]} for item in roots],
        }

    log_step(trace, "resolve_node_selection", "Pilihan node valid, masuk state node", {"node_id": node_id})
    return build_node_reply(node, get_children(tree, node_id, trace=trace), trace)


def build_reply(message: str, tree: dict, trace: dict | None = None) -> dict:
    """Handle chat bebas dengan global classifier Top 3."""
    suggestions = suggest_groups(message, tree, limit=3, trace=trace)
    return build_group_reply(suggestions, tree.get("fallback"), trace)
