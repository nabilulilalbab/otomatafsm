import streamlit as st

from app.tree_store import load_tree
from views.admin_page import render_admin_page, require_admin


st.set_page_config(page_title="Atur Bot | Otomata FSM Chatbot", layout="wide")

if require_admin():
    tree = load_tree()
    render_admin_page(tree)
