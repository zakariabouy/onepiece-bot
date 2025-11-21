# ui.py — Enhanced Streamlit chat UI for One Piece Bot with Background Image

import streamlit as st
import torch
from core import rag_chat, load_notes_and_build_index
import base64
from pathlib import Path

st.set_page_config(
    page_title="One Piece Chatbot", 
    page_icon="🏴‍☠️", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------- Enhanced Styles with Background Image ----------
st.markdown("""
<style>
    /* Import Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700&display=swap');
    
    /* Global Styles */
    .stApp {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        font-family: 'Poppins', sans-serif;
    }
    
    /* Main container */
    .main .block-container {
        padding: 2rem 3rem;
        max-width: 1200px;
        margin: 0 auto;
    }
    
    /* Title styling */
    h1 {
        color: white !important;
        text-align: center;
        font-weight: 700;
        font-size: 3rem !important;
        margin-bottom: 0.5rem !important;
        text-shadow: 3px 3px 6px rgba(0,0,0,0.4);
        animation: titleFloat 3s ease-in-out infinite;
    }
    
    @keyframes titleFloat {
        0%, 100% { transform: translateY(0px); }
        50% { transform: translateY(-5px); }
    }
    
    /* Subtitle */
    .subtitle {
        text-align: center;
        color: rgba(255,255,255,0.95);
        font-size: 1.2rem;
        margin-bottom: 2rem;
        font-weight: 500;
        text-shadow: 1px 1px 3px rgba(0,0,0,0.3);
    }
    
    /* Chat container with background */
    .chat-container {
        background: white;
        border-radius: 20px;
        padding: 0;
        box-shadow: 0 15px 50px rgba(0,0,0,0.3);
        min-height: 500px;
        max-height: 600px;
        overflow: hidden;
        margin-bottom: 1.5rem;
        position: relative;
        border: 3px solid rgba(255,255,255,0.3);
    }
    
    /* Background image overlay */
    .chat-bg {
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background-image: url('https://images.unsplash.com/photo-1589519160732-57fc498494f8?w=1200');
        background-size: cover;
        background-position: center;
        opacity: 0.08;
        pointer-events: none;
        z-index: 0;
    }
    
    /* Scrollable messages area */
    .messages-area {
        position: relative;
        z-index: 1;
        padding: 2rem;
        max-height: 600px;
        overflow-y: auto;
    }
    
    html[data-theme="dark"] .chat-container {
        background: #1a1d29;
        border-color: rgba(255,255,255,0.1);
    }
    
    /* Welcome message styling */
    .welcome-box {
        text-align: center;
        padding: 4rem 2rem;
        background: linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%);
        border-radius: 15px;
        margin: 2rem;
        border: 2px dashed rgba(102, 126, 234, 0.3);
    }
    
    .welcome-box h3 {
        color: #667eea !important;
        margin-bottom: 1rem;
        font-size: 1.8rem;
    }
    
    .welcome-box p {
        color: #718096;
        font-size: 1.1rem;
        margin: 0.5rem 0;
    }
    
    .example-queries {
        display: flex;
        justify-content: center;
        gap: 1rem;
        margin-top: 1.5rem;
        flex-wrap: wrap;
    }
    
    .example-query {
        background: white;
        padding: 0.6rem 1.2rem;
        border-radius: 20px;
        color: #667eea;
        font-size: 0.9rem;
        border: 2px solid #667eea;
        cursor: pointer;
        transition: all 0.3s ease;
        box-shadow: 0 2px 8px rgba(102, 126, 234, 0.2);
    }
    
    .example-query:hover {
        background: #667eea;
        color: white;
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
    }
    
    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #667eea 0%, #764ba2 100%);
    }
    
    [data-testid="stSidebar"] h2, 
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] label {
        color: white !important;
    }
    
    /* Button styling */
    .stButton button {
        width: 100%;
        background: white !important;
        color: #667eea !important;
        border: 2px solid white !important;
        border-radius: 12px;
        padding: 0.7rem 1rem;
        font-weight: 600 !important;
        transition: all 0.3s ease;
        font-size: 1rem;
    }
    
    .stButton button:hover {
        background: rgba(255,255,255,0.95) !important;
        transform: translateY(-3px);
        box-shadow: 0 6px 16px rgba(0,0,0,0.2);
    }
    
    .stButton button p {
        color: #667eea !important;
        font-weight: 600;
    }
    
    /* Expander styling */
    .streamlit-expanderHeader {
        background: linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%);
        border-radius: 12px;
        font-weight: 600;
        border: 1px solid rgba(102, 126, 234, 0.2);
        padding: 1rem;
    }
    
    html[data-theme="dark"] .streamlit-expanderHeader {
        background: #2d3748;
    }
    
    /* Chat message containers */
    .stChatMessage {
        padding: 1rem;
        margin: 0.8rem 0;
        border-radius: 15px;
        animation: messageSlide 0.4s ease-out;
    }
    
    @keyframes messageSlide {
        from {
            opacity: 0;
            transform: translateX(-20px);
        }
        to {
            opacity: 1;
            transform: translateX(0);
        }
    }
    
    [data-testid="stChatMessageContent"] {
        background: transparent;
    }
    
    /* User message styling */
    [data-testid="stChatMessage"][data-testid*="user"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
    }
    
    /* Bot message styling */
    [data-testid="stChatMessage"]:not([data-testid*="user"]) {
        background: rgba(241, 243, 245, 0.95);
        border: 1px solid rgba(102, 126, 234, 0.2);
    }
    
    html[data-theme="dark"] [data-testid="stChatMessage"]:not([data-testid*="user"]) {
        background: rgba(45, 55, 72, 0.95);
        border-color: #4a5568;
    }
    
    /* Sources badge */
    .sources-badge {
        display: inline-block;
        background: rgba(102, 126, 234, 0.2);
        color: #667eea;
        padding: 0.4rem 1rem;
        border-radius: 15px;
        font-size: 0.85rem;
        font-weight: 600;
        margin-top: 0.8rem;
        border: 1px solid rgba(102, 126, 234, 0.3);
    }
    
    html[data-theme="dark"] .sources-badge {
        background: rgba(102, 126, 234, 0.3);
        color: #a5b4fc;
    }
    
    /* Chat input styling */
    .stChatInput {
        border-radius: 15px;
        border: 2px solid rgba(255,255,255,0.3);
        box-shadow: 0 5px 20px rgba(0,0,0,0.2);
    }
    
    .stChatInput > div {
        border-radius: 15px;
    }
    
    /* Scrollbar */
    .messages-area::-webkit-scrollbar {
        width: 10px;
    }
    
    .messages-area::-webkit-scrollbar-track {
        background: rgba(241, 243, 245, 0.5);
        border-radius: 10px;
    }
    
    .messages-area::-webkit-scrollbar-thumb {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 10px;
    }
    
    .messages-area::-webkit-scrollbar-thumb:hover {
        background: linear-gradient(135deg, #764ba2 0%, #667eea 100%);
    }
    
    /* Info cards in sidebar */
    .info-card {
        background: rgba(255,255,255,0.2);
        padding: 1.2rem;
        border-radius: 15px;
        margin: 1rem 0;
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255,255,255,0.3);
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    }
    
    .info-card h3 {
        margin-top: 0;
        color: white !important;
        font-size: 1.2rem;
    }
    
    /* Slider styling */
    .stSlider {
        padding: 0.5rem 0;
    }
    
    /* Loading spinner */
    .stSpinner > div {
        border-color: #667eea !important;
    }
    
    /* Stats badge */
    .stat-badge {
        background: rgba(255,255,255,0.25);
        padding: 0.5rem 1rem;
        border-radius: 10px;
        margin: 0.3rem 0;
        display: flex;
        align-items: center;
        gap: 0.5rem;
        font-size: 0.95rem;
    }
</style>
""", unsafe_allow_html=True)

# ---------- Header ----------
st.title("🏴‍☠️ One Piece Chatbot")
st.markdown('<p class="subtitle">⚓ Your AI companion for exploring the Grand Line ⚓</p>', unsafe_allow_html=True)

# ---------- Sidebar ----------
with st.sidebar:
    st.markdown("## ⚙️ Controls")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 Rebuild Index"):
            with st.spinner("Rebuilding..."):
                load_notes_and_build_index()
            st.success("✓ Index rebuilt!")
    
    with col2:
        if st.button("🧹 Clear Chat"):
            st.session_state.pop("messages", None)
            st.rerun()
    
    st.markdown("---")
    
    k_val = st.slider("📊 Passages to retrieve", 1, 10, 5, help="Number of relevant passages to search")
    temp_val = st.slider("🌡️ Temperature", 0.0, 1.0, 0.5, 0.1, help="Higher = more creative responses")
    
    st.markdown("---")
    
    # Info section
    st.markdown('<div class="info-card">', unsafe_allow_html=True)
    st.markdown("### 📌 System Info")
    device_emoji = "🚀" if torch.cuda.is_available() else "💻"
    device_name = "GPU (CUDA)" if torch.cuda.is_available() else "CPU"
    st.markdown(f'<div class="stat-badge">{device_emoji} <strong>Device:</strong> {device_name}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="stat-badge">🗄️ <strong>Database:</strong> onepiece.db</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Quick tips
    st.markdown('<div class="info-card">', unsafe_allow_html=True)
    st.markdown("### 💡 Quick Tips")
    st.markdown("""
    - Ask about **characters** 🏴‍☠️
    - Explore **story arcs** 📖
    - Discover **abilities** ⚡
    - Learn about **locations** 🗺️
    """)
    st.markdown('</div>', unsafe_allow_html=True)

# ---------- Session State ----------
if "messages" not in st.session_state:
    st.session_state.messages = []

# ---------- Chat Display ----------
# Using Streamlit's native chat display with custom container
chat_container = st.container()

with chat_container:
    if not st.session_state.messages:
        # Welcome message with example queries
        st.markdown("""
        <div class="welcome-box">
            <h3>👋 Welcome aboard the Thousand Sunny!</h3>
            <p>🏴‍☠️ I'm your guide to the One Piece universe</p>
            <p>Ask me anything about characters, arcs, events, and more!</p>
            <div class="example-queries">
                <div class="example-query">🎩 Tell me about Luffy</div>
                <div class="example-query">⚔️ What is Marineford?</div>
                <div class="example-query">🍊 Who is Nami?</div>
                <div class="example-query">🌊 Explain Devil Fruits</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        # Display messages using Streamlit's chat components
        for role, content, passages in st.session_state.messages:
            with st.chat_message(role, avatar="👤" if role == "user" else "🏴‍☠️"):
                st.markdown(content)
                if role == "assistant" and passages:
                    passage_count = len(passages)
                    st.markdown(f'<span class="sources-badge">📚 {passage_count} source{"s" if passage_count != 1 else ""}</span>', unsafe_allow_html=True)

# ---------- Chat Input ----------
user_msg = st.chat_input("💬 Type your message here...")

if user_msg:
    # Add user message
    st.session_state.messages.append(("user", user_msg, []))
    
    # Display user message immediately
    with st.chat_message("user", avatar="👤"):
        st.markdown(user_msg)
    
    # Get bot response
    with st.chat_message("assistant", avatar="🏴‍☠️"):
        with st.spinner("🤔 Thinking..."):
            res = rag_chat(user_msg, k=k_val, temperature=temp_val)
        
        reply = res.get("reply", "Sorry, I don't know.")
        passages = res.get("passages", [])
        
        st.markdown(reply)
        
        if passages:
            passage_count = len(passages)
            st.markdown(f'<span class="sources-badge">📚 {passage_count} source{"s" if passage_count != 1 else ""}</span>', unsafe_allow_html=True)
        
        # Add bot message to history
        st.session_state.messages.append(("assistant", reply, passages))

# ---------- Show source details in expander ----------
if st.session_state.messages:
    last_role, last_content, last_passages = st.session_state.messages[-1]
    if last_role == "assistant" and last_passages:
        with st.expander("🔍 View Source Details", expanded=False):
            for i, p in enumerate(last_passages, 1):
                title = p.get("title", "(untitled)")
                arc = p.get("arc", "?")
                score = p.get("score", 0.0)
                text = p.get("text", "")[:200] + "..." if len(p.get("text", "")) > 200 else p.get("text", "")
                
                st.markdown(f"""
                <div style="background: rgba(102, 126, 234, 0.05); padding: 1rem; border-radius: 10px; margin: 0.5rem 0; border-left: 4px solid #667eea;">
                    <strong style="color: #667eea; font-size: 1.1rem;">[{i}] {title}</strong><br>
                    <span style="color: #718096;">📖 Arc: <code>{arc}</code> | 🎯 Relevance: <code>{score:.3f}</code></span><br>
                    <p style="margin-top: 0.5rem; color: #4a5568;">{text}</p>
                </div>
                """, unsafe_allow_html=True)

# ---------- Footer ----------
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: rgba(255,255,255,0.8); padding: 1rem;">
    <p>Made with ❤️ for One Piece fans | Powered by RAG & AI</p>
</div>
""", unsafe_allow_html=True)