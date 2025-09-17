# ui.py — Streamlit chat UI for One Piece Bot

import streamlit as st
import torch  # just for the device label
from core import chat_router, answer_question, load_notes_and_build_index

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

    strict_mode = st.toggle(
        "Strict (no-generation) mode",
        value=True,
        help="ON = only grounded answers from your notes. OFF = small talk + fallback to local LLM (Ollama)."
    )
    k_val = st.slider("Passages to retrieve (k)", 1, 10, 3)

    if st.button("🧹 Clear chat"):
        st.session_state.pop("messages", None)
        st.rerun()

    st.caption("Notes are loaded from onepiece.db and auto-reloaded periodically.")
    st.caption(f"Device: {'GPU' if torch.cuda.is_available() else 'CPU'}")

# ---------- Session State ----------
if "messages" not in st.session_state:
    st.session_state.messages = []  # list of (role, content, passages)

def render_message(role: str, content: str):
    css = "user" if role == "user" else "bot"
    st.markdown(f'<div class="chat-bubble {css}">{content}</div>', unsafe_allow_html=True)

# ---------- History ----------
for role, content, _passages in st.session_state.messages:
    render_message(role, content)

# ---------- Input ----------
user_msg = st.chat_input("Ask about arcs, characters, or lore… (you can also say hi)")
if user_msg:
    # show user bubble
    st.session_state.messages.append(("user", user_msg, []))
    render_message("user", user_msg)

    # answer (strict vs router)
    with st.spinner("Thinking…"):
        if strict_mode:
            # Grounded, extractive answers only
            res = answer_question(user_msg, k=k_val)
        else:
            # Small talk + RAG + LLM fallback
            res = chat_router(user_msg, k=k_val)

    reply = res.get("reply", "Sorry, I don't know yet.")
    passages = res.get("passages", [])
    st.session_state.messages.append(("bot", reply, passages))
    render_message("bot", reply)

    # Sources expander
    if passages:
        with st.expander("Sources (passages)"):
            for p in passages:
                title = p.get("title", "(untitled)")
                arc = p.get("arc", "?")
                score = p.get("score", 0.0)
                st.markdown(f"- **{title}** ({arc}) — score: `{score:.3f}`")

