import streamlit as st
from dotenv import load_dotenv
load_dotenv()

st.set_page_config(
    page_title="Chloe's Caption AI",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700&family=DM+Sans:wght@300;400;500&display=swap');
    html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
    h1, h2, h3 { font-family: 'Playfair Display', serif; }
    .stButton > button { border-radius: 8px; font-weight: 500; }
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #6C3EF4, #A259F7);
        border: none; color: white;
    }
    .sidebar-logo { text-align: center; padding: 1rem 0 2rem 0; }
    .sidebar-logo h2 { font-family: 'Playfair Display', serif; font-size: 1.4rem; color: #6C3EF4; margin: 0; }
    .sidebar-logo p  { font-size: 0.75rem; color: #888; margin: 0; }
</style>
""", unsafe_allow_html=True)

from database import init_db
init_db()

with st.sidebar:
    st.markdown("""
    <div class="sidebar-logo">
        <h2>✨ Chloe's Caption AI</h2>
        <p>Social Media Automation</p>
    </div>
    """, unsafe_allow_html=True)

    page = st.radio(
        "Navigate",
        [
            "🏠  Dashboard",
            "👤  Clients",
            "🔑  Keywords",
            "📚  Caption Examples",
            "🚀  Generate Captions",
            "📦  Content Batch Generator",
        ],
        label_visibility="collapsed"
    )

page_key = page.split("  ")[-1].strip()

if page_key == "Dashboard":
    from pages.dashboard import show; show()
elif page_key == "Clients":
    from pages.clients import show; show()
elif page_key == "Keywords":
    from pages.keywords import show; show()
elif page_key == "Caption Examples":
    from pages.examples import show; show()
elif page_key == "Generate Captions":
    from pages.generate import show; show()
elif page_key == "Content Batch Generator":
    from pages.batch_generator import show; show()
