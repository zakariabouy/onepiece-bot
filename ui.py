# ui.py — Enhanced Streamlit chat UI for One Piece Bot with Background Image

import streamlit as st
import os
import re
import sys

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
from core import rag_chat, load_notes_and_build_index

import base64
from pathlib import Path

st.set_page_config(
    page_title="One Piece Chatbot",
    page_icon="🏴‍☠️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------- Character Image Helper ----------
CHARACTER_IMAGE_DIR = Path("data/characters")

def get_safe_filename(name: str) -> str:
    """Convert character name to safe filename."""
    return re.sub(r'[^\w\-]', '_', name.lower()).strip('_') + ".jpg"

def find_character_image(question: str, answer: str) -> tuple[str, Path] | None:
    """
    Only show character image if the QUESTION is specifically asking about that character.
    This prevents showing random images when a character is just mentioned in passing.
    """
    # Only check the question, not the answer - to avoid false matches
    question_lower = question.lower().strip()
    
    # Patterns that indicate asking about a specific character
    # e.g., "who is luffy", "tell me about zoro", "what is nami's backstory"
    asking_patterns = [
        r"who\s+is\s+",
        r"tell\s+me\s+about\s+",
        r"what\s+(is|are|about|does|did|can|was|were)\s+.{0,20}('s|s')?\s*",
        r"describe\s+",
        r"explain\s+",
        r"^(luffy|zoro|nami|sanji|robin|chopper|franky|brook|jinbe|usopp)",  # Starts with name
    ]
    
    is_asking_about_character = any(re.search(p, question_lower) for p in asking_patterns)
    
    if not is_asking_about_character:
        return None
    
    # Character mappings: (regex pattern for question, display name, filename)
    # Only match if character name appears near the asking pattern
    characters = [
        # Straw Hats (most common)
        (r'\bluffy\b', "Monkey D. Luffy", "monkey_d__luffy"),
        (r'\bzoro\b', "Roronoa Zoro", "roronoa_zoro"),
        (r'\bnami\b', "Nami", "nami"),
        (r'\busopp\b', "Usopp", "usopp"),
        (r'\bsanji\b', "Sanji", "sanji"),
        (r'\bchopper\b', "Tony Tony Chopper", "tony_tony_chopper"),
        (r'\brobin\b', "Nico Robin", "nico_robin"),
        (r'\bfranky\b', "Franky", "franky"),
        (r'\bbrook\b', "Brook", "brook"),
        (r'\bjinbe\b', "Jinbe", "jinbe"),
        
        # Major characters
        (r'\bshanks\b', "Shanks", "shanks"),
        (r'\bace\b', "Portgas D. Ace", "portgas_d__ace"),
        (r'\bsabo\b', "Sabo", "sabo"),
        (r'\blaw\b', "Trafalgar Law", "trafalgar_law"),
        (r'\bkaido\b', "Kaido", "kaido"),
        (r'\bbig\s*mom\b', "Big Mom", "big_mom"),
        (r'\bblackbeard\b', "Blackbeard", "blackbeard"),
        (r'\bwhitebeard\b', "Whitebeard", "whitebeard"),
        (r'\bdoflamingo\b', "Doflamingo", "donquixote_doflamingo"),
        (r'\bmihawk\b', "Dracule Mihawk", "dracule_mihawk"),
        (r'\bhancock\b', "Boa Hancock", "boa_hancock"),
        (r'\bkatakuri\b', "Katakuri", "katakuri"),
        (r'\bmarco\b', "Marco", "marco"),
        (r'\bgarp\b', "Monkey D. Garp", "monkey_d__garp"),
        (r'\brayleigh\b', "Silvers Rayleigh", "silvers_rayleigh"),
        (r'\broger\b', "Gol D. Roger", "gol_d__roger"),
        (r'\benel\b', "Enel", "enel"),
        (r'\bcrocodile\b', "Crocodile", "crocodile"),
        (r'\bbuggy\b', "Buggy", "buggy"),
        (r'\byamato\b', "Yamato", "yamato"),
        (r'\bvivi\b', "Nefertari Vivi", "nefertari_vivi"),
        (r'\bsmoker\b', "Smoker", "smoker"),
        (r'\bkoby\b', "Koby", "koby"),
        (r'\bcarrot\b', "Carrot", "carrot"),
        (r'\bbonney\b', "Jewelry Bonney", "jewelry_bonney"),
        (r'\bkid\b', "Eustass Kid", "eustass_kid"),
        (r'\baokiji\b', "Aokiji", "aokiji"),
        (r'\bkizaru\b', "Kizaru", "kizaru"),
        (r'\bfujitora\b', "Fujitora", "fujitora"),
        (r'\bmagellan\b', "Magellan", "magellan"),
        (r'\bivankov\b', "Ivankov", "emporio_ivankov"),
        (r'\balvida\b', "Alvida", "alvida"),
        (r'\barlong\b', "Arlong", "arlong"),
    ]
    
    for pattern, display_name, filename_base in characters:
        if re.search(pattern, question_lower):
            img_path = CHARACTER_IMAGE_DIR / f"{filename_base}.jpg"
            if img_path.exists():
                return (display_name, img_path)
    
    return None

# ---------- Load Local Background Image ----------
def get_base64_image(image_path: Path) -> str | None:
    """Convert local image to base64 for CSS embedding."""
    try:
        with image_path.open("rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    except Exception as e:
        st.error(f"Error loading background image: {e}")
        return None


bg_image_path = Path("data/assets/bg.jpeg")
bg_base64 = get_base64_image(bg_image_path) if bg_image_path.exists() else None
if not bg_base64:
    st.warning("Background image not found at data/assets/bg.jpeg – using gradient instead.")

# Decide background CSS depending on whether the image is available
if bg_base64:
    background_css = f"""
        background-image:
            linear-gradient(135deg, rgba(0,0,0,0.80), rgba(0,0,0,0.88)),
            url("data:image/jpeg;base64,{bg_base64}");
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
    """
else:
    background_css = """
        background: linear-gradient(135deg, #020617 0%, #0f172a 40%, #1e293b 100%);
    """

# ---------- Enhanced Styles with Background Image ----------
st.markdown(
    f"""
<style>
    /* Import Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700&display=swap');
    
    /* Global Styles */
    .stApp {{
        {background_css}
        font-family: 'Poppins', sans-serif;
    }}
    
    /* Main container */
    .main .block-container {{
        padding: 2rem 3rem;
        max-width: 1200px;
        margin: 0 auto;
    }}
    
    /* Title styling */
    h1 {{
        color: white !important;
        text-align: center;
        font-weight: 700;
        font-size: 3rem !important;
        margin-bottom: 0.5rem !important;
        text-shadow: 3px 3px 6px rgba(0,0,0,0.4);
        animation: titleFloat 3s ease-in-out infinite;
    }}
    
    @keyframes titleFloat {{
        0%, 100% {{ transform: translateY(0px); }}
        50% {{ transform: translateY(-5px); }}
    }}
    
    /* Subtitle */
    .subtitle {{
        text-align: center;
        color: rgba(255,255,255,0.95);
        font-size: 1.2rem;
        margin-bottom: 2rem;
        font-weight: 500;
        text-shadow: 1px 1px 3px rgba(0,0,0,0.3);
    }}
    
    /* Chat container (not strictly needed with st.chat_message but kept for future layouts) */
    .chat-container {{
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
    }}
    
    /* Scrollable messages area */
    .messages-area {{
        position: relative;
        z-index: 1;
        padding: 2rem;
        max-height: 600px;
        overflow-y: auto;
    }}
    
    html[data-theme="dark"] .chat-container {{
        background: #1a1d29;
        border-color: rgba(255,255,255,0.1);
    }}
    
    /* Welcome message styling */
    .welcome-box {{
        text-align: center;
        padding: 4rem 2rem;
        background: linear-gradient(135deg, rgba(56, 189, 248, 0.18) 0%, rgba(129, 140, 248, 0.18) 100%);
        border-radius: 15px;
        margin: 2rem;
        border: 2px dashed rgba(129, 140, 248, 0.6);
        backdrop-filter: blur(12px);
    }}
    
    .welcome-box h3 {{
        color: #e5e7eb !important;
        margin-bottom: 1rem;
        font-size: 1.8rem;
    }}
    
    .welcome-box p {{
        color: #e5e7eb;
        font-size: 1.05rem;
        margin: 0.4rem 0;
    }}
    
    .example-queries {{
        display: flex;
        justify-content: center;
        gap: 1rem;
        margin-top: 1.5rem;
        flex-wrap: wrap;
    }}
    
    .example-query {{
        background: rgba(15,23,42,0.9);
        padding: 0.6rem 1.4rem;
        border-radius: 999px;
        color: #e5e7eb;
        font-size: 0.9rem;
        border: 2px solid rgba(129, 140, 248, 0.9);
        cursor: default;
        box-shadow: 0 2px 10px rgba(15,23,42,0.8);
    }}
    
    /* Sidebar styling — new ocean / night gradient */
    [data-testid="stSidebar"] {{
        background: linear-gradient(180deg, #020617 0%, #0b1220 35%, #111827 65%, #1d2440 100%);
        color: #e5e7eb;
    }}
    
    [data-testid="stSidebar"] h2, 
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] label {{
        color: #e5e7eb !important;
    }}
    
    /* Button styling */
    .stButton button {{
        width: 100%;
        background: #e5e7eb !important;
        color: #1d4ed8 !important;
        border: 2px solid transparent !important;
        border-radius: 14px;
        padding: 0.7rem 1rem;
        font-weight: 600 !important;
        transition: all 0.25s ease;
        font-size: 0.98rem;
        box-shadow: 0 6px 16px rgba(0,0,0,0.35);
    }}
    
    .stButton button:hover {{
        background: #ffffff !important;
        transform: translateY(-2px);
        box-shadow: 0 8px 20px rgba(0,0,0,0.45);
    }}
    
    .stButton button p {{
        color: inherit !important;
        font-weight: 600;
    }}
    
    /* Expander styling */
    .streamlit-expanderHeader {{
        background: linear-gradient(135deg, rgba(30, 64, 175, 0.28) 0%, rgba(59, 130, 246, 0.28) 100%);
        border-radius: 12px;
        font-weight: 600;
        border: 1px solid rgba(129, 140, 248, 0.5);
        padding: 1rem;
        color: #e5e7eb !important;
    }}
    
    html[data-theme="dark"] .streamlit-expanderHeader {{
        background: rgba(15,23,42,0.9);
        border-color: rgba(148, 163, 184, 0.6);
    }}
    
    /* Chat message containers */
    .stChatMessage {{
        padding: 1rem;
        margin: 0.8rem 0;
        border-radius: 15px;
        animation: messageSlide 0.4s ease-out;
    }}
    
    @keyframes messageSlide {{
        from {{
            opacity: 0;
            transform: translateY(6px);
        }}
        to {{
            opacity: 1;
            transform: translateY(0);
        }}
    }}
    
    [data-testid="stChatMessageContent"] {{
        background: transparent;
    }}
    
    /* User message styling + text color (light & dark) */
    [data-testid="stChatMessage"][data-testid*="user"] {{
        background: linear-gradient(135deg, #4f46e5 0%, #0ea5e9 100%);
        color: #f9fafb !important;
    }}
    [data-testid="stChatMessage"][data-testid*="user"] * {{
        color: #f9fafb !important;
    }}
    
    /* Bot message styling (light mode) */
    [data-testid="stChatMessage"]:not([data-testid*="user"]) {{
        background: rgba(243, 244, 246, 0.96);
        border: 1px solid rgba(148, 163, 184, 0.6);
        color: #111827;
    }}
    [data-testid="stChatMessage"]:not([data-testid*="user"]) * {{
        color: #111827;
    }}
    
    /* Bot message styling (dark mode) */
    html[data-theme="dark"] [data-testid="stChatMessage"]:not([data-testid*="user"]) {{
        background: rgba(15, 23, 42, 0.94);
        border-color: rgba(148, 163, 184, 0.7);
        color: #e5e7eb;
    }}
    html[data-theme="dark"] [data-testid="stChatMessage"]:not([data-testid*="user"]) * {{
        color: #e5e7eb;
    }}
    
    /* Sources badge */
    .sources-badge {{
        display: inline-block;
        background: rgba(129, 140, 248, 0.16);
        color: #e5e7eb;
        padding: 0.4rem 1rem;
        border-radius: 15px;
        font-size: 0.85rem;
        font-weight: 600;
        margin-top: 0.8rem;
        border: 1px solid rgba(129, 140, 248, 0.7);
    }}
    
    html[data-theme="light"] .sources-badge {{
        background: rgba(129, 140, 248, 0.10);
        color: #1f2933;
        border-color: rgba(129, 140, 248, 0.8);
    }}
    
    /* Chat input styling */
    .stChatInput {{
        border-radius: 15px;
        border: 2px solid rgba(148,163,184,0.7);
        box-shadow: 0 5px 20px rgba(0,0,0,0.4);
        background: rgba(15,23,42,0.95);
    }}
    
    .stChatInput > div {{
        border-radius: 15px;
    }}
    
    /* Scrollbar */
    .messages-area::-webkit-scrollbar {{
        width: 10px;
    }}
    
    .messages-area::-webkit-scrollbar-track {{
        background: rgba(15,23,42,0.6);
        border-radius: 10px;
    }}
    
    .messages-area::-webkit-scrollbar-thumb {{
        background: linear-gradient(135deg, #4f46e5 0%, #0ea5e9 100%);
        border-radius: 10px;
    }}
    
    .messages-area::-webkit-scrollbar-thumb:hover {{
        background: linear-gradient(135deg, #0ea5e9 0%, #4f46e5 100%);
    }}
    
    /* Info cards in sidebar */
    .info-card {{
        background: rgba(15,23,42,0.85);
        padding: 1.2rem;
        border-radius: 15px;
        margin: 1rem 0;
        backdrop-filter: blur(10px);
        border: 1px solid rgba(148,163,184,0.7);
        box-shadow: 0 4px 14px rgba(0,0,0,0.55);
    }}
    
    .info-card h3 {{
        margin-top: 0;
        color: #e5e7eb !important;
        font-size: 1.1rem;
    }}
    
    /* Slider styling */
    .stSlider {{
        padding: 0.5rem 0;
    }}
    
    /* Loading spinner */
    .stSpinner > div {{
        border-color: #4f46e5 !important;
    }}
    
    /* Stats badge */
    .stat-badge {{
        background: rgba(15,23,42,0.95);
        padding: 0.5rem 1rem;
        border-radius: 10px;
        margin: 0.3rem 0;
        display: flex;
        align-items: center;
        gap: 0.5rem;
        font-size: 0.95rem;
        color: #e5e7eb;
        border: 1px solid rgba(148,163,184,0.8);
    }}
</style>
""",
    unsafe_allow_html=True,
)

# ---------- Header ----------
st.title("🏴‍☠️ One Piece Chatbot")
st.markdown(
    '<p class="subtitle">⚓ Your AI companion for exploring the Grand Line ⚓</p>',
    unsafe_allow_html=True,
)

# ---------- Sidebar ----------
with st.sidebar:
    # Header with logo
    st.markdown("""
    <div style="text-align: center; padding: 1rem 0;">
        <h1 style="margin: 0; font-size: 2.5rem;">🏴‍☠️</h1>
        <h2 style="margin: 0.5rem 0; color: #E63946;">One Piece Bot</h2>
        <p style="color: #888; font-size: 0.85rem;">Your AI Nakama</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")

    # Clear chat button - full width, styled
    if st.button("🧹 Clear Chat", use_container_width=True, type="secondary"):
        st.session_state.pop("messages", None)
        st.rerun()

    st.markdown("---")
    
    # Settings section
    st.markdown("### ⚙️ Settings")
    
    k_val = st.slider(
        "📊 Passages to retrieve",
        1,
        10,
        5,
        help="Number of relevant passages to search",
    )
    temp_val = st.slider(
        "🌡️ Temperature",
        0.0,
        1.0,
        0.5,
        0.1,
        help="Higher = more creative responses",
    )

    st.markdown("---")

    # Quick tips - collapsible
    with st.expander("💡 Quick Tips", expanded=False):
        st.markdown("""
        - Ask about **characters** 🏴‍☠️  
        - Explore **story arcs** 📖  
        - Discover **abilities** ⚡  
        - Learn about **locations** 🗺️
        """)
    
    # System info - collapsible
    with st.expander("📌 System Info", expanded=False):
        st.markdown("""
        - **LLM:** Groq Cloud (LLaMA 3.1)
        - **Embeddings:** FastEmbed
        - **Database:** SQLite (2,300+ notes)
        """)
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #666; font-size: 0.75rem;">
        <p>Made with ❤️ for One Piece fans</p>
        <p><a href="https://github.com/zakariabouy/onepiece-bot" target="_blank" style="color: #888;">GitHub</a></p>
    </div>
    """, unsafe_allow_html=True)

# ---------- Session State ----------
if "messages" not in st.session_state:
    st.session_state.messages = []

# ---------- Chat Display ----------
chat_container = st.container()

with chat_container:
    if not st.session_state.messages:
        # Welcome message with example queries
        st.markdown(
            """
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
        """,
            unsafe_allow_html=True,
        )
    else:
        # Display messages using Streamlit's chat components
        for role, content, passages in st.session_state.messages:
            with st.chat_message(role, avatar="👤" if role == "user" else "🏴‍☠️"):
                st.markdown(content)
                if role == "assistant" and passages:
                    passage_count = len(passages)
                    st.markdown(
                        f'<span class="sources-badge">📚 {passage_count} source{"s" if passage_count != 1 else ""}</span>',
                        unsafe_allow_html=True,
                    )

# ---------- Chat Input ----------
user_msg = st.chat_input("💬 Type your message here...")

if user_msg:
    # Add user message
    st.session_state.messages.append(("user", user_msg, []))

    # Display user message immediately
    with st.chat_message("user", avatar="👤"):
        st.markdown(user_msg)

    # Build conversation history for context
    history = []
    for role, content, _ in st.session_state.messages[:-1]:  # Exclude the just-added user message
        history.append({"role": role, "content": content})
    
    # Get bot response with conversation memory
    with st.chat_message("assistant", avatar="🏴‍☠️"):
        with st.spinner("🤔 Thinking..."):
            res = rag_chat(user_msg, k=k_val, temperature=temp_val, history=history)

        reply = res.get("reply", "Sorry, I don't know.")
        passages = res.get("passages", [])

        # Only show character image if question is ABOUT that character
        char_info = find_character_image(user_msg, reply)
        if char_info:
            char_name, img_path = char_info
            col1, col2 = st.columns([1, 3])
            with col1:
                st.image(str(img_path), caption=char_name, width=150)
            with col2:
                st.markdown(reply)
        else:
            st.markdown(reply)

        if passages:
            passage_count = len(passages)
            st.markdown(
                f'<span class="sources-badge">📚 {passage_count} source{"s" if passage_count != 1 else ""}</span>',
                unsafe_allow_html=True,
            )

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
                text = (
                    p.get("text", "")[:200] + "..."
                    if len(p.get("text", "")) > 200
                    else p.get("text", "")
                )

                st.markdown(
                    f"""
                <div style="background: rgba(15,23,42,0.8); padding: 1rem; border-radius: 10px; margin: 0.5rem 0; border-left: 4px solid #4f46e5;">
                    <strong style="color: #e5e7eb; font-size: 1.05rem;">[{i}] {title}</strong><br>
                    <span style="color: #cbd5f5;">📖 Arc: <code>{arc}</code> | 🎯 Relevance: <code>{score:.3f}</code></span><br>
                    <p style="margin-top: 0.5rem; color: #e5e7eb;">{text}</p>
                </div>
                """,
                    unsafe_allow_html=True,
                )

# ---------- Footer ----------
st.markdown("---")
st.markdown(
    """
<div style="text-align: center; color: rgba(248,250,252,0.85); padding: 1rem;">
    <p>Made with ❤️ for One Piece fans | Powered by RAG & AI</p>
</div>
""",
    unsafe_allow_html=True,
)
