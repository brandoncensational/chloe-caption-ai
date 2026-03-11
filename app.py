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
    page_title="Censational Social Media Manager",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ── Global CSS: hide sidebar, style top nav, branding ─────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700&family=DM+Sans:wght@300;400;500;600&display=swap');
    html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
    h1, h2, h3 { font-family: 'Playfair Display', serif; }

    /* ── HIDE SIDEBAR COMPLETELY ── */
    [data-testid="stSidebar"] { display: none !important; }
    [data-testid="stSidebarNav"] { display: none !important; }
    [data-testid="collapsedControl"] { display: none !important; }
    section[data-testid="stSidebar"] { display: none !important; }

    /* ── TOP NAV STYLING ── */
    div[data-testid="stHorizontalBlock"]:has(> div > div > div > .stButton > button.nav-btn) {
        border-bottom: 2px solid #2a2a3e;
        padding-bottom: 0.5rem;
        margin-bottom: 1rem;
    }
    .nav-btn {
        border: none !important;
        border-radius: 8px 8px 0 0 !important;
        font-weight: 500 !important;
        font-size: 0.85rem !important;
        padding: 0.5rem 0.75rem !important;
        background: transparent !important;
        color: #aaa !important;
        transition: all 0.2s !important;
    }
    .nav-btn:hover {
        background: #2a2a3e !important;
        color: #fff !important;
    }
    .nav-active {
        background: linear-gradient(135deg, #6C3EF4, #A259F7) !important;
        color: white !important;
        font-weight: 600 !important;
    }

    /* ── BUTTON STYLING ── */
    .stButton > button { border-radius: 8px; font-weight: 500; }
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #6C3EF4, #A259F7);
        border: none; color: white;
    }

    /* ── AUTH CARD STYLING ── */
    .auth-container {
        max-width: 440px;
        margin: 2rem auto;
        padding: 2.5rem;
        background: white;
        border-radius: 16px;
        box-shadow: 0 4px 24px rgba(0,0,0,0.08);
    }
    .auth-header {
        text-align: center;
        margin-bottom: 2rem;
    }
    .auth-header h1 {
        font-family: 'Playfair Display', serif;
        font-size: 1.8rem;
        color: #FFFFFF;
        margin: 0;
    }
    .auth-header p {
        color: #aaa;
        font-size: 0.9rem;
        margin: 0.25rem 0 0 0;
    }
    .brand-bar {
        text-align: center;
        padding: 0.75rem 0;
        margin-bottom: 0.5rem;
    }
    .brand-bar h2 {
        font-family: 'Playfair Display', serif;
        font-size: 1.3rem;
        color: #FFFFFF;
        margin: 0;
        display: inline;
    }
    .brand-bar span { color: #aaa; font-size: 0.75rem; }

    /* ── USER BADGE ── */
    .user-badge {
        display: inline-block;
        padding: 0.2rem 0.6rem;
        border-radius: 20px;
        font-size: 0.7rem;
        font-weight: 600;
        text-transform: uppercase;
    }
    .user-badge.master { background: #6C3EF4; color: white; }
    .user-badge.user { background: #e8e0ff; color: #6C3EF4; }
</style>
""", unsafe_allow_html=True)

from database import (
    init_db, create_user, authenticate_user, get_user_by_email, hash_password
)
init_db()


# ═══════════════════════════════════════════════════════════════════════════════
# AUTHENTICATION
# ═══════════════════════════════════════════════════════════════════════════════

def _check_master_login(email: str, password: str) -> dict | None:
    """Check if credentials match a master account defined in .env / st.secrets."""
    for i in range(1, 5):  # Support up to 4 master accounts
        try:
            m_email = st.secrets.get(f"MASTER_EMAIL_{i}", "")
        except Exception:
            m_email = os.environ.get(f"MASTER_EMAIL_{i}", "")
        try:
            m_pass = st.secrets.get(f"MASTER_PASS_{i}", "")
        except Exception:
            m_pass = os.environ.get(f"MASTER_PASS_{i}", "")
        try:
            m_name = st.secrets.get(f"MASTER_NAME_{i}", "")
        except Exception:
            m_name = os.environ.get(f"MASTER_NAME_{i}", f"Master {i}")

        if m_email and m_pass and email.lower().strip() == m_email.lower().strip() and password == m_pass:
            return {
                "id": None,
                "email": m_email,
                "name": m_name or f"Master {i}",
                "role": "master",
                "business_name": "",
            }
    return None


def show_auth_page():
    """Display login / sign-up screen."""
    st.markdown("""
    <div class="auth-header">
        <h1>Censational</h1>
        <p>Social Media Manager</p>
    </div>
    """, unsafe_allow_html=True)

    auth_tab = st.radio(
        "auth_mode", ["Log In", "Sign Up"],
        horizontal=True, label_visibility="collapsed",
        key="auth_tab"
    )

    if auth_tab == "Log In":
        _show_login()
    else:
        _show_signup()


def _show_login():
    with st.form("login_form"):
        email = st.text_input("Email", placeholder="you@example.com")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Log In", type="primary", use_container_width=True)

    if submitted:
        if not email or not password:
            st.error("Please enter both email and password.")
            return

        # 1. Check master accounts (from .env)
        master = _check_master_login(email, password)
        if master:
            st.session_state["user"] = master
            st.success(f"Welcome back, {master['name']}!")
            st.rerun()
            return

        # 2. Check regular users (from database)
        user = authenticate_user(email, password)
        if user:
            st.session_state["user"] = user
            st.success(f"Welcome back, {user['name']}!")
            st.rerun()
            return

        st.error("Invalid email or password.")


def _show_signup():
    with st.form("signup_form"):
        name = st.text_input("Your Name *", placeholder="Jane Smith")
        email = st.text_input("Email *", placeholder="you@example.com")
        business = st.text_input("Business Name *", placeholder="Your business or brand name")
        website = st.text_input("Website URL (optional)", placeholder="https://yourbusiness.com")
        password = st.text_input("Password *", type="password")
        password2 = st.text_input("Confirm Password *", type="password")
        submitted = st.form_submit_button("Create Account", type="primary", use_container_width=True)

    if submitted:
        if not all([name.strip(), email.strip(), business.strip(), password]):
            st.error("Please fill in all required fields.")
            return
        if password != password2:
            st.error("Passwords don't match.")
            return
        if len(password) < 6:
            st.error("Password must be at least 6 characters.")
            return

        # Check if email already exists
        existing = get_user_by_email(email)
        if existing:
            st.error("An account with this email already exists. Please log in instead.")
            return

        try:
            user = create_user(
                email=email,
                password=password,
                name=name.strip(),
                role="user",
                business_name=business.strip(),
                website_url=website.strip(),
            )
            if user:
                # Auto-create their first client from signup info
                from database import add_client
                try:
                    add_client(
                        name=business.strip(),
                        industry="",
                        brand_voice="",
                        target_audience="",
                        platforms="Instagram, Facebook",
                        notes=f"Website: {website}" if website else "",
                        owner_id=user["id"],
                    )
                except Exception:
                    pass  # Client name might conflict

                st.session_state["user"] = user
                st.success(f"Account created! Welcome, {name}!")
                st.rerun()
        except Exception as e:
            if "UNIQUE" in str(e):
                st.error("An account with this email already exists.")
            else:
                st.error(f"Error creating account: {e}")


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN APP
# ═══════════════════════════════════════════════════════════════════════════════

# Init session state
if "user" not in st.session_state:
    st.session_state["user"] = None
if "current_page" not in st.session_state:
    st.session_state["current_page"] = "Dashboard"

# Handle nav_override from dashboard quick actions
if "nav_override" in st.session_state:
    st.session_state["current_page"] = st.session_state.pop("nav_override")

# ── Auth gate ──────────────────────────────────────────────────────────────────
if st.session_state["user"] is None:
    show_auth_page()
    st.stop()

# ── User is logged in ─────────────────────────────────────────────────────────
user = st.session_state["user"]
is_master = user.get("role") == "master"

# Store user context for pages to access
st.session_state["is_master"] = is_master
st.session_state["user_owner_id"] = user.get("id") if not is_master else None

# ── Top brand bar + user info ──────────────────────────────────────────────────
top_left, top_right = st.columns([4, 2])
with top_left:
    st.markdown("""
    <div class="brand-bar">
        <h2>Censational</h2>
        <span> &nbsp;Social Media Manager</span>
    </div>
    """, unsafe_allow_html=True)
with top_right:
    role_class = "master" if is_master else "user"
    role_label = "MASTER" if is_master else "USER"
    st.markdown(
        f'<div style="text-align:right;padding-top:0.5rem;">'
        f'<span style="color:#ccc;font-size:0.85rem;">{user["name"]}</span> '
        f'<span class="user-badge {role_class}">{role_label}</span>'
        f'</div>',
        unsafe_allow_html=True
    )

# ── Horizontal Tab Navigation ──────────────────────────────────────────────────
PAGES = [
    ("🏠", "Dashboard"),
    ("👤", "Clients"),
    ("🔑", "Keywords"),
    ("📚", "Examples"),
    ("🚀", "Generate"),
    ("📦", "Batch Generator"),
]

nav_cols = st.columns(len(PAGES) + 1)  # +1 for logout button

for i, (icon, label) in enumerate(PAGES):
    with nav_cols[i]:
        is_active = st.session_state["current_page"] == label
        btn_class = "nav-btn nav-active" if is_active else "nav-btn"
        # Streamlit doesn't support custom CSS classes on buttons directly,
        # so we use a workaround with the button label and session state
        if st.button(
            f"{icon} {label}",
            key=f"nav_{label}",
            use_container_width=True,
            type="primary" if is_active else "secondary",
        ):
            st.session_state["current_page"] = label
            st.rerun()

with nav_cols[-1]:
    if st.button("🚪 Log Out", key="nav_logout", use_container_width=True):
        st.session_state["user"] = None
        st.session_state["current_page"] = "Dashboard"
        # Clear other session state
        for key in list(st.session_state.keys()):
            if key not in ("user", "current_page"):
                del st.session_state[key]
        st.rerun()

st.markdown("---")

# ── Page Routing ───────────────────────────────────────────────────────────────
page = st.session_state["current_page"]

if page == "Dashboard":
    from pages.dashboard import show; show()
elif page == "Clients":
    from pages.clients import show; show()
elif page == "Keywords":
    from pages.keywords import show; show()
elif page == "Examples":
    from pages.examples import show; show()
elif page == "Generate":
    from pages.generate import show; show()
elif page == "Batch Generator":
    from pages.batch_generator import show; show()
