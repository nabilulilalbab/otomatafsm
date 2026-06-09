"""HTTP API tipis untuk UI editorial (webui/). Membungkus core app/ tanpa mengubahnya."""

import os
from pathlib import Path

from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from app.chat_engine import get_node
from app.fsm_engine import handle_back, handle_free_text, handle_reset, handle_select_node
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


BASE_DIR = Path(__file__).parent
WEBUI_DIR = BASE_DIR / "webui"
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin")

app = FastAPI(title="Otomata FSM Chatbot API")


# ---------- request models ----------

class ChatRequest(BaseModel):
    text: str = ""
    current_node_id: str = ""
    state_history: list[str] = []


class SelectRequest(BaseModel):
    node_id: str
    current_node_id: str = ""
    state_history: list[str] = []


class NavRequest(BaseModel):
    current_node_id: str = ""
    state_history: list[str] = []


class NodeCreateRequest(BaseModel):
    title: str = ""
    description: str = ""
    keywords: str = ""
    answer: str = ""
    parent_id: str = ""
    enabled: bool = True


class NodeUpdateRequest(BaseModel):
    title: str = ""
    description: str = ""
    keywords: str = ""
    children: str = ""
    answer: str = ""
    enabled: bool = True


class SettingsRequest(BaseModel):
    bot_name: str = ""
    fallback: str = ""


# ---------- helpers ----------

def _require_admin(password: str | None) -> None:
    if password != ADMIN_PASSWORD:
        raise HTTPException(status_code=401, detail="Password admin salah.")


def _find_node_any_status(tree: dict, node_id: str) -> dict | None:
    for node in tree.get("nodes", []):
        if node.get("id") == node_id:
            return node
    return None


# ---------- chat API (stateless, state datang dari client) ----------

@app.get("/api/tree")
def api_tree() -> dict:
    tree = load_tree()
    nodes = tree.get("nodes", [])
    enabled = [n for n in nodes if n.get("enabled", True)]
    menu = [n for n in enabled if n.get("children")]
    final = [n for n in enabled if not n.get("children") and n.get("answer")]
    roots = [
        {"id": n["id"], "title": n["title"]}
        for n in (get_node(tree, rid) for rid in tree.get("root_nodes", []))
        if n
    ]
    return {
        "bot_name": tree.get("bot_name", ""),
        "stats": {
            "total": len(nodes),
            "root": len(tree.get("root_nodes", [])),
            "menu": len(menu),
            "final": len(final),
        },
        "roots": roots,
    }


@app.post("/api/chat")
def api_chat(req: ChatRequest) -> dict:
    tree = load_tree()
    return handle_free_text(req.text, tree, req.current_node_id, req.state_history)


@app.post("/api/select")
def api_select(req: SelectRequest) -> dict:
    tree = load_tree()
    return handle_select_node(req.node_id, tree, req.current_node_id, req.state_history)


@app.post("/api/back")
def api_back(req: NavRequest) -> dict:
    tree = load_tree()
    return handle_back(tree, req.current_node_id, req.state_history)


@app.post("/api/reset")
def api_reset() -> dict:
    return handle_reset()


# ---------- admin API (baca/tulis data/bot_tree.json via tree_store) ----------

@app.get("/api/admin/tree")
def api_admin_tree(x_admin_password: str | None = Header(default=None)) -> dict:
    _require_admin(x_admin_password)
    tree = load_tree()
    return {
        "bot_name": tree["bot_name"],
        "fallback": tree["fallback"],
        "root_nodes": tree["root_nodes"],
        "nodes": tree["nodes"],
        "rows": build_tree_rows(tree),
        "parent_options": get_parent_options(tree),
    }


@app.post("/api/admin/node")
def api_admin_add_node(req: NodeCreateRequest, x_admin_password: str | None = Header(default=None)) -> dict:
    _require_admin(x_admin_password)
    tree = load_tree()
    node = make_node(
        title=req.title,
        description=req.description,
        keywords=split_values(req.keywords),
        children=[],
        answer=req.answer,
        enabled=req.enabled,
    )
    errors = validate_node(node)
    if errors:
        return JSONResponse(status_code=400, content={"errors": errors})
    attach_node_to_parent(tree, node, req.parent_id)
    save_tree(tree)
    return {"ok": True, "id": node["id"]}


@app.put("/api/admin/node/{node_id}")
def api_admin_update_node(
    node_id: str, req: NodeUpdateRequest, x_admin_password: str | None = Header(default=None)
) -> dict:
    _require_admin(x_admin_password)
    tree = load_tree()
    node = _find_node_any_status(tree, node_id)
    if not node:
        raise HTTPException(status_code=404, detail="Node tidak ditemukan.")
    node["title"] = req.title.strip() or node["title"]
    node["description"] = req.description.strip()
    node["keywords"] = split_values(req.keywords)
    node["children"] = split_values(req.children)
    node["answer"] = req.answer.strip()
    node["enabled"] = req.enabled
    errors = validate_node(node)
    if errors:
        return JSONResponse(status_code=400, content={"errors": errors})
    save_tree(tree)
    return {"ok": True}


@app.delete("/api/admin/node/{node_id}")
def api_admin_delete_node(node_id: str, x_admin_password: str | None = Header(default=None)) -> dict:
    _require_admin(x_admin_password)
    tree = load_tree()
    tree["nodes"] = [n for n in tree["nodes"] if n["id"] != node_id]
    tree["root_nodes"] = [rid for rid in tree["root_nodes"] if rid != node_id]
    for node in tree["nodes"]:
        node["children"] = [cid for cid in node["children"] if cid != node_id]
    save_tree(tree)
    return {"ok": True}


@app.put("/api/admin/settings")
def api_admin_settings(req: SettingsRequest, x_admin_password: str | None = Header(default=None)) -> dict:
    _require_admin(x_admin_password)
    tree = load_tree()
    tree["bot_name"] = req.bot_name.strip() or tree["bot_name"]
    tree["fallback"] = req.fallback.strip() or tree["fallback"]
    save_tree(tree)
    return {"ok": True}


@app.post("/api/admin/login")
def api_admin_login(x_admin_password: str | None = Header(default=None)) -> dict:
    _require_admin(x_admin_password)
    return {"ok": True}


# ---------- pages ----------

@app.get("/")
def page_home() -> FileResponse:
    return FileResponse(WEBUI_DIR / "index.html")


@app.get("/chat")
def page_chat() -> FileResponse:
    return FileResponse(WEBUI_DIR / "chat.html")


@app.get("/admin")
def page_admin() -> FileResponse:
    return FileResponse(WEBUI_DIR / "admin.html")


app.mount("/static", StaticFiles(directory=WEBUI_DIR / "static"), name="static")
