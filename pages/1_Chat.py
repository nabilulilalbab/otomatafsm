import streamlit as st

from app.tree_store import load_tree
from views.chat_page import render_chat_page


st.set_page_config(page_title="Chat | Otomata FSM Chatbot", layout="wide")

tree = load_tree()
render_chat_page(tree)
