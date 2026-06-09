import json
from pathlib import Path

from app.text import slugify


DEFAULT_TREE_PATH = Path("data/bot_tree.json")
DEFAULT_FALLBACK = "Aku belum yakin topiknya. Pilih salah satu area ini dulu ya."


def default_tree_data() -> dict:
    """Tree kosong yang tetap aman untuk app."""
    return {
        "bot_name": "Asisten Pertanian",
        "fallback": DEFAULT_FALLBACK,
        "root_nodes": [],
        "nodes": [],
    }


def ensure_tree_file(path: Path | str = DEFAULT_TREE_PATH) -> Path:
    """Pastikan file tree tersedia."""
    tree_path = Path(path)
    tree_path.parent.mkdir(parents=True, exist_ok=True)
    if not tree_path.exists():
        save_tree(default_tree_data(), tree_path)
    return tree_path


def load_tree(path: Path | str = DEFAULT_TREE_PATH) -> dict:
    """Baca tree bot dari JSON; kalau rusak, fallback ke tree kosong."""
    tree_path = ensure_tree_file(path)
    try:
        data = json.loads(tree_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        data = default_tree_data()
    return normalize_tree(data)


def save_tree(data: dict, path: Path | str = DEFAULT_TREE_PATH) -> None:
    """Simpan tree bot ke JSON."""
    tree_path = Path(path)
    tree_path.parent.mkdir(parents=True, exist_ok=True)
    safe_data = normalize_tree(data)
    tree_path.write_text(json.dumps(safe_data, indent=2, ensure_ascii=False), encoding="utf-8")


def split_values(value: str) -> list[str]:
    """Ubah textarea jadi list, dipisah koma atau baris baru."""
    raw_values = value.replace("\n", ",").split(",")
    return [item.strip() for item in raw_values if item.strip()]


def normalize_node(node: dict) -> dict:
    """Rapikan satu node agar semua field wajib selalu ada."""
    title = (node.get("title") or node.get("name") or "Group Tanpa Nama").strip()
    keywords = node.get("keywords") or []
    children = node.get("children") or []
    if isinstance(keywords, str):
        keywords = split_values(keywords)
    if isinstance(children, str):
        children = split_values(children)

    return {
        "id": (node.get("id") or slugify(title)).strip() or "group",
        "title": title,
        "description": (node.get("description") or "").strip(),
        "keywords": [keyword.strip() for keyword in keywords if keyword.strip()],
        "children": [child_id.strip() for child_id in children if child_id.strip()],
        "answer": (node.get("answer") or "").strip(),
        "enabled": bool(node.get("enabled", True)),
    }


def normalize_tree(data: dict) -> dict:
    """Rapikan tree dan tangani duplicate id dengan mengambil node pertama."""
    bot_name = (data.get("bot_name") or "Asisten Pertanian").strip()
    fallback = (data.get("fallback") or DEFAULT_FALLBACK).strip()
    nodes = []
    seen_ids = set()
    for node in data.get("nodes", []):
        normalized = normalize_node(node)
        if normalized["id"] in seen_ids:
            continue
        seen_ids.add(normalized["id"])
        nodes.append(normalized)

    root_nodes = data.get("root_nodes") or []
    if isinstance(root_nodes, str):
        root_nodes = split_values(root_nodes)
    valid_ids = {node["id"] for node in nodes}
    safe_roots = [node_id for node_id in root_nodes if node_id in valid_ids]
    if not safe_roots:
        safe_roots = [node["id"] for node in nodes if node["enabled"]][:3]

    return {
        "bot_name": bot_name,
        "fallback": fallback,
        "root_nodes": safe_roots,
        "nodes": nodes,
    }


def make_node(
    title: str,
    description: str = "",
    keywords: list[str] | None = None,
    children: list[str] | None = None,
    answer: str = "",
    enabled: bool = True,
) -> dict:
    """Buat node baru dari form admin."""
    return normalize_node(
        {
            "id": unique_node_id(title),
            "title": title,
            "description": description,
            "keywords": keywords or [],
            "children": children or [],
            "answer": answer,
            "enabled": enabled,
        }
    )


def unique_node_id(title: str) -> str:
    """Buat id node sederhana berbasis waktu agar tidak bentrok."""
    from time import time

    return f"{slugify(title)}_{int(time() * 1000)}"


def validate_node(node: dict) -> list[str]:
    """Balikin daftar error node agar UI bisa kasih feedback jelas."""
    errors = []
    if not node.get("title"):
        errors.append("Judul group wajib diisi.")
    if not node.get("keywords"):
        errors.append("Minimal isi satu keyword agar classifier bisa menyarankan group.")
    if not node.get("children") and not node.get("answer"):
        errors.append("Isi child group atau answer final.")
    return errors


def get_parent_options(tree: dict) -> list[dict]:
    """Daftar parent untuk dropdown admin, termasuk root."""
    options = [{"id": "", "label": "Menu Utama / Root"}]
    for node in tree.get("nodes", []):
        if node.get("enabled", True):
            options.append({"id": node["id"], "label": node["title"]})
    return options


def attach_node_to_parent(tree: dict, node: dict, parent_id: str = "") -> dict:
    """Tambahkan node baru ke tree dan hubungkan ke parent/root."""
    tree["nodes"].append(node)
    if parent_id:
        parent = _find_node_any_status(tree, parent_id)
        if parent and node["id"] not in parent["children"]:
            parent["children"].append(node["id"])
    elif node["id"] not in tree["root_nodes"]:
        tree["root_nodes"].append(node["id"])
    return tree


def build_tree_rows(tree: dict, max_depth: int = 20) -> list[dict]:
    """Buat daftar baris tree dengan key unik berbasis path untuk UI."""
    rows = []
    for root_id in tree.get("root_nodes", []):
        _append_tree_rows(tree, root_id, rows, path=[], depth=0, max_depth=max_depth)
    return rows


def _append_tree_rows(
    tree: dict,
    node_id: str,
    rows: list[dict],
    path: list[str],
    depth: int,
    max_depth: int,
) -> None:
    """Recursive helper untuk tree explorer; aman untuk shared child dan loop."""
    row_key = "__".join(path + [node_id])
    if node_id in path:
        rows.append(
            {
                "node_id": node_id,
                "title": f"{node_id} (loop dilewati)",
                "depth": depth,
                "key": f"loop__{row_key}",
                "missing": True,
            }
        )
        return

    node = _find_node_any_status(tree, node_id)
    if not node or not node.get("enabled", True):
        rows.append(
            {
                "node_id": node_id,
                "title": f"{node_id} (hilang/nonaktif)",
                "depth": depth,
                "key": f"missing__{row_key}",
                "missing": True,
            }
        )
        return

    rows.append(
        {
            "node_id": node["id"],
            "title": node["title"],
            "depth": depth,
            "key": f"select__{row_key}",
            "missing": False,
        }
    )

    if depth >= max_depth:
        return

    for child_id in node.get("children", []):
        _append_tree_rows(tree, child_id, rows, path + [node_id], depth + 1, max_depth)


def _find_node_any_status(tree: dict, node_id: str) -> dict | None:
    """Ambil node tanpa filter enabled; khusus untuk render tree admin."""
    for node in tree.get("nodes", []):
        if node.get("id") == node_id:
            return node
    return None
