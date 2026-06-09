import streamlit as st


THEME_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');

:root {
  --bg-main: #F0EEE6;
  --bg-card: #E3DACC;
  --bg-dark: #141413;
  --text-main: #141413;
  --text-muted: #6F6D67;
  --border-soft: #D0C7B8;
  --button-dark: #111110;
  --button-hover: #2A2927;
  --text-invert: #F5F3EC;
  --success-muted: #4F6F52;
  --danger-muted: #8A3B2E;
  --warning-muted: #9A6A25;
  --font-sans: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif;
  --font-serif: Georgia, 'Times New Roman', serif;
}

.stApp {
  background: var(--bg-main);
  color: var(--text-main);
  font-family: var(--font-sans);
}

.block-container {
  max-width: 1180px;
  padding-top: 2rem;
  padding-bottom: 4rem;
  padding-left: 2rem;
  padding-right: 2rem;
}

header[data-testid="stHeader"] {
  background: transparent !important;
  box-shadow: none !important;
  z-index: 999990 !important;
}
[data-testid="stDecoration"] { display: none !important; }
[data-testid="stAppDeployButton"] { display: none !important; }
[data-testid="stMainMenu"], #MainMenu { display: none !important; }
[data-testid="stToolbarActions"] { display: none !important; }
footer { visibility: hidden; }

/* Keep header + the control that re-opens a collapsed sidebar visible */
header[data-testid="stHeader"] [data-testid="stToolbar"],
[data-testid="stExpandSidebarButton"],
[data-testid="stSidebarCollapsedControl"],
[data-testid="collapsedControl"] {
  visibility: visible !important;
  display: flex !important;
  opacity: 1 !important;
  z-index: 999999 !important;
}
[data-testid="stExpandSidebarButton"] {
  background: var(--bg-card) !important;
  border: 1px solid var(--border-soft) !important;
  border-radius: 9px !important;
}
[data-testid="stExpandSidebarButton"] *,
[data-testid="stExpandSidebarButton"] span,
[data-testid="stExpandSidebarButton"] svg,
[data-testid="stIconMaterial"],
[data-testid="stSidebarCollapsedControl"] svg,
[data-testid="collapsedControl"] svg {
  color: var(--text-main) !important;
  fill: var(--text-main) !important;
  opacity: 1 !important;
}

h1 {
  font-family: var(--font-sans);
  font-size: clamp(42px, 6vw, 76px) !important;
  line-height: 0.95 !important;
  letter-spacing: -0.06em !important;
  font-weight: 850 !important;
  color: var(--text-main) !important;
}

h2 {
  font-size: clamp(28px, 3.5vw, 40px) !important;
  letter-spacing: -0.035em !important;
  font-weight: 750 !important;
  color: var(--text-main) !important;
}

h3 {
  font-size: clamp(20px, 2.4vw, 26px) !important;
  letter-spacing: -0.03em !important;
  font-weight: 700 !important;
  color: var(--text-main) !important;
}

p, li, span, label, .stMarkdown {
  color: var(--text-main);
}

.editorial { font-family: var(--font-serif); }

.underline-key {
  border-bottom: 6px solid var(--text-main);
  padding-bottom: 2px;
}

.small-muted {
  color: var(--text-muted);
  font-size: 14px;
}

.eyebrow {
  text-transform: uppercase;
  letter-spacing: 0.12em;
  font-size: 12px;
  color: var(--text-muted);
  font-weight: 600;
}

/* Navbar */
.top-nav {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 18px 0 24px 0;
  margin-bottom: 12px;
  border-bottom: 1px solid var(--border-soft);
}
.top-nav .brand {
  font-weight: 900;
  letter-spacing: -0.03em;
  font-size: 22px;
  color: var(--text-main);
}
.top-nav .nav-links {
  display: flex;
  gap: 28px;
  align-items: center;
  font-size: 15px;
}
.top-nav .nav-links a {
  color: var(--text-muted);
  text-decoration: none;
}
.top-nav .nav-links a.active {
  color: var(--text-main);
  font-weight: 600;
}

/* Cards */
.automata-card {
  background: var(--bg-card);
  border-radius: 18px;
  padding: 28px;
  border: 1px solid rgba(20,20,19,0.08);
  margin-bottom: 16px;
}
.automata-card h3 { margin-top: 0; margin-bottom: 12px; }

.dark-panel {
  background: var(--bg-dark);
  color: var(--text-invert);
  border-radius: 22px;
  padding: 32px;
  min-height: 200px;
  margin-bottom: 16px;
}
.dark-panel h2, .dark-panel h3, .dark-panel p, .dark-panel span {
  color: var(--text-invert) !important;
}
.dark-panel .title { font-family: var(--font-serif); font-size: 36px; line-height: 1.05; }

.meta-row {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  border-top: 1px solid var(--border-soft);
  padding: 14px 0;
  font-size: 14px;
}
.meta-label {
  text-transform: uppercase;
  letter-spacing: 0.08em;
  font-size: 12px;
  color: var(--text-muted);
}
.meta-value { font-weight: 600; color: var(--text-main); }

.state-pill {
  border: 1px solid rgba(245,243,236,0.35);
  border-radius: 999px;
  padding: 6px 14px;
  display: inline-block;
  margin: 4px 6px 4px 0;
  font-size: 13px;
}

/* Chat bubbles */
.chat-bot {
  background: var(--bg-card);
  color: var(--text-main);
  border-radius: 18px;
  padding: 16px 20px;
  margin-bottom: 14px;
  max-width: 78%;
  white-space: pre-wrap;
}
.chat-user {
  background: var(--bg-dark);
  color: var(--text-invert);
  border-radius: 18px;
  padding: 16px 20px;
  margin-left: auto;
  margin-bottom: 14px;
  max-width: 78%;
  white-space: pre-wrap;
}

.badge {
  display: inline-block;
  border-radius: 999px;
  padding: 4px 12px;
  font-size: 12px;
  letter-spacing: 0.04em;
  font-weight: 600;
}
.badge-accepted { background: var(--success-muted); color: var(--text-invert); }
.badge-rejected { background: var(--danger-muted); color: var(--text-invert); }

/* Buttons */
.stButton > button,
[data-testid="stBaseButton-secondary"],
[data-testid="stBaseButton-primary"] {
  background: var(--button-dark) !important;
  background-color: var(--button-dark) !important;
  color: var(--text-invert) !important;
  border: 1px solid var(--button-dark) !important;
  border-radius: 9px !important;
  padding: 0.65rem 1.1rem !important;
  font-weight: 600 !important;
  box-shadow: none !important;
}
[data-testid="stBaseButton-secondary"] *,
[data-testid="stBaseButton-primary"] *,
[data-testid="stBaseButton-secondary"] [data-testid="stMarkdownContainer"] p,
[data-testid="stBaseButton-primary"] [data-testid="stMarkdownContainer"] p {
  color: var(--text-invert) !important;
  fill: var(--text-invert) !important;
}
[data-testid="stBaseButton-secondary"]:hover,
[data-testid="stBaseButton-primary"]:hover {
  background: var(--button-hover) !important;
  background-color: var(--button-hover) !important;
  border-color: var(--button-hover) !important;
}
[data-testid="stBaseButton-secondary"]:disabled,
[data-testid="stBaseButton-primary"]:disabled {
  background: var(--button-dark) !important;
  background-color: var(--button-dark) !important;
  border-color: var(--button-dark) !important;
  opacity: 1 !important;
}
[data-testid="stBaseButton-secondary"]:disabled *,
[data-testid="stBaseButton-primary"]:disabled * {
  color: rgba(245,243,236,0.45) !important;
}

/* Inputs: style the baseweb wrapper, keep the inner field borderless */
.stTextInput [data-baseweb="input"],
.stTextArea [data-baseweb="textarea"],
.stTextArea [data-baseweb="base-input"] {
  background: #F7F5ED !important;
  border: 1px solid var(--border-soft) !important;
  border-radius: 14px !important;
}
.stTextInput input,
.stTextArea textarea {
  background: transparent !important;
  border: none !important;
  box-shadow: none !important;
  color: var(--text-main) !important;
}
.stTextInput [data-baseweb="input"]:focus-within,
.stTextArea [data-baseweb="textarea"]:focus-within {
  border-color: var(--button-dark) !important;
  box-shadow: none !important;
}

/* Chat input: single rounded container, no inner double border */
[data-testid="stChatInput"] {
  background: #F7F5ED !important;
  border: 1px solid var(--border-soft) !important;
  border-radius: 16px !important;
}
[data-testid="stChatInput"] > div,
[data-testid="stChatInput"] [data-baseweb="textarea"],
[data-testid="stChatInput"] [data-baseweb="base-input"] {
  background: transparent !important;
  border: none !important;
  box-shadow: none !important;
}
[data-testid="stChatInput"] textarea {
  background: transparent !important;
  border: none !important;
  box-shadow: none !important;
  color: var(--text-main) !important;
}
[data-testid="stChatInput"]:focus-within {
  border-color: var(--button-dark) !important;
}
[data-testid="stChatInputSubmitButton"] {
  background: var(--button-dark) !important;
  border-radius: 9px !important;
  color: var(--text-invert) !important;
}
[data-testid="stChatInputSubmitButton"] svg { fill: var(--text-invert) !important; color: var(--text-invert) !important; }
[data-testid="stChatInputSubmitButton"]:disabled { opacity: 0.4 !important; }

/* Sidebar blends with theme */
[data-testid="stSidebar"] {
  background: #EAE5DA;
  border-right: 1px solid var(--border-soft);
}
[data-testid="stSidebar"] * { color: var(--text-main); }

hr { border: none; border-top: 1px solid var(--border-soft); }

/* Footer */
.site-footer {
  background: var(--bg-dark);
  color: #B8B5AA;
  border-radius: 22px;
  padding: 56px 40px;
  margin-top: 72px;
}
.site-footer .footer-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 56px;
}
.site-footer .footer-brand {
  font-weight: 900;
  letter-spacing: -0.03em;
  font-size: 20px;
  color: var(--text-invert);
}
.site-footer h4 {
  color: var(--text-invert);
  font-size: 13px;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  margin: 0 0 16px 0;
}
.site-footer .footer-col span {
  display: block;
  color: #B8B5AA;
  margin-bottom: 12px;
  font-size: 14px;
}
</style>
"""


def inject_theme() -> None:
    """Suntik CSS tema editorial. Aman dipanggil berkali-kali per page."""
    st.markdown(THEME_CSS, unsafe_allow_html=True)


def render_navbar(active: str = "") -> None:
    """Navbar minimal editorial. `active` salah satu: home, chat, admin."""
    def cls(name: str) -> str:
        return "active" if name == active else ""

    st.markdown(
        f"""
        <div class="top-nav">
          <div class="brand">OTOMATA</div>
          <div class="nav-links">
            <a class="{cls('home')}">Home</a>
            <a class="{cls('chat')}">Chat</a>
            <a class="{cls('admin')}">Atur Bot</a>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_footer() -> None:
    """Footer editorial gelap, teks saja tanpa link eksternal."""
    st.markdown(
        """
        <div class="site-footer">
          <div class="footer-grid">
            <div class="footer-col">
              <div class="footer-brand">OTOMATA CHATBOT</div>
              <span class="small-muted">Finite State Machine assistant</span>
            </div>
            <div class="footer-col">
              <h4>Features</h4>
              <span>Global Router</span>
              <span>State Navigation</span>
              <span>Flow Log</span>
              <span>Admin Editor</span>
            </div>
            <div class="footer-col">
              <h4>Resources</h4>
              <span>Automata Theory</span>
              <span>Examples</span>
              <span>Documentation</span>
            </div>
            <div class="footer-col">
              <h4>Project</h4>
              <span>About</span>
              <span>Repository</span>
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
