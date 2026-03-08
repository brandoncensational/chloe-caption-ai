import os
import streamlit as st

# ── Load secrets: Streamlit Cloud uses st.secrets, local uses .env ────────────
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Pull API key from st.secrets (cloud) or environment (local)
if not os.environ.get("ANTHROPIC_API_KEY"):
    try:
        os.environ["ANTHROPIC_API_KEY"] = st.secrets["ANTHROPIC_API_KEY"]
    except Exception:
        pass

# ── Password protection (optional) ────────────────────────────────────────────
def _check_password():
    try:
        pwd = st.secrets.get("APP_PASSWORD", "")
    except Exception:
        pwd = os.environ.get("APP_PASSWORD", "")
    if not pwd:
        return True  # no password set — open access
    if st.session_state.get("authenticated"):
        return True
    st.title("🔐 Chloe's Caption AI")
    entered = st.text_input("Enter password", type="password")
    if st.button("Login", type="primary"):
        if entered == pwd:
            st.session_state["authenticated"] = True
            st.rerun()
        else:
            st.error("Incorrect password.")
    return False

if not _check_password():
    st.stop()

# ── Google Drive: write credentials from secrets to temp files on cloud ───────
def _setup_drive_from_secrets():
    try:
        creds_json = st.secrets.get("GOOGLE_DRIVE_CREDENTIALS", "")
        token_json = st.secrets.get("GOOGLE_DRIVE_TOKEN", "")
    except Exception:
        creds_json = os.environ.get("GOOGLE_DRIVE_CREDENTIALS", "")
        token_json = os.environ.get("GOOGLE_DRIVE_TOKEN", "")

    data_dir = os.path.join(os.path.dirname(__file__), "data")
    os.makedirs(data_dir, exist_ok=True)

    if creds_json and not os.path.exists(os.path.join(data_dir, "drive_credentials.json")):
        with open(os.path.join(data_dir, "drive_credentials.json"), "w") as f:
            f.write(creds_json)
    if token_json and not os.path.exists(os.path.join(data_dir, "drive_token.json")):
        with open(os.path.join(data_dir, "drive_token.json"), "w") as f:
            f.write(token_json)

_setup_drive_from_secrets()

# ── Page config ───────────────────────────────────────────────────────────────
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
