# ui.py — Streamlit chat UI for One Piece Bot (single conversational mode)

import streamlit as st
import torch
from core import rag_chat, load_notes_and_build_index

st.set_page_config(page_title="One Piece Chatbot", page_icon="🏴‍☠️", layout="centered")

# ---------- Styles ----------
st.markdown("""
<style>
.chat-bubble { padding: 0.9rem 1rem; border-radius: 12px; margin: 0.35rem 0; line-height: 1.45; }
.user { background: #1f6feb; color: #ffffff; }
.bot  { background: #f7f7f8; color: #111111; }
html[data-theme="dark"] .user { background: #2563eb; color: #e5e7eb; }
html[data-theme="dark"] .bot  { background: #111827; color: #e5e7eb; border: 1px solid #1f2937; }
.src { font-size: 0.9rem; color: #6b7280; margin-top: 0.4rem; }
html[data-theme="dark"] .src { color: #9ca3af; }
</style>
""", unsafe_allow_html=True)

st.title("🏴‍☠️ One Piece Chatbot")

# ---------- Sidebar ----------
with st.sidebar:
    st.header("Controls")

    if st.button("🔄 Rebuild Index"):
        load_notes_and_build_index()
        st.success("Index rebuilt.")

    k_val = st.slider("Passages to retrieve (k)", 1, 10, 5)
    if st.button("🧹 Clear chat"):
        st.session_state.pop("messages", None)
        st.rerun()

    st.caption("Notes are loaded from onepiece.db and auto-reloaded periodically.")
    st.caption(f"Device: {'GPU' if torch.cuda.is_available() else 'CPU'}")

# ---------- Session State ----------
if "messages" not in st.session_state:
    st.session_state.messages = []  # (role, content, passages)

def render_message(role: str, content: str):
    css = "user" if role == "user" else "bot"
    st.markdown(f'<div class="chat-bubble {css}">{content}</div>', unsafe_allow_html=True)

# ---------- History ----------
for role, content, _passages in st.session_state.messages:
    render_message(role, content)

# ---------- Input ----------
user_msg = st.chat_input("Chat or ask anything about One Piece… (you can also say hi)")
if user_msg:
    st.session_state.messages.append(("user", user_msg, []))
    render_message("user", user_msg)

    with st.spinner("Thinking…"):
        res = rag_chat(user_msg, k=k_val)

    reply = res.get("reply", "Sorry, I don't know.")
    passages = res.get("passages", [])
    st.session_state.messages.append(("bot", reply, passages))
    render_message("bot", reply)

    if passages:
        with st.expander("Sources (passages)"):
            for i, p in enumerate(passages, 1):
                title = p.get("title", "(untitled)")
                arc = p.get("arc", "?")
                score = p.get("score", 0.0)
                st.markdown(f"- **[{i}] {title}** ({arc}) — score: `{score:.3f}`")
