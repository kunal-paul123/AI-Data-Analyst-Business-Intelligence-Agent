import os
import re
import streamlit as st
import streamlit.components.v1 as components
import httpx
import pandas as pd
import plotly.express as px

# PAGE CONFIGURATION (Sidebar collapsed by default)
st.set_page_config(
    page_title="AI Data Analyst | BI Agent",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# API Base URL (FastAPI backend)
API_BASE_URL = "http://localhost:8000"


def resolve_chart_path(p: str | None) -> str | None:
    """Finds the actual chart file regardless of Streamlit's working directory."""
    if not p:
        return None
    if os.path.exists(p):
        return p
    root_p = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), p)
    if os.path.exists(root_p):
        return root_p
    base_name = os.path.basename(p)
    charts_p = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "charts", base_name)
    if os.path.exists(charts_p):
        return charts_p
    return None


# CUSTOM CSS: PURE BLACK & WHITE MONOCHROME THEME + LOCKED EXPANDED FLOATING CHAT INPUT
CUSTOM_CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

    /* Completely hide sidebar & toggle */
    [data-testid="stSidebar"], [data-testid="collapsedControl"] {
        display: none !important;
    }

    /* Pure Black Background & Crisp White Text */
    .stApp, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {
        background-color: #000000 !important;
        color: #ffffff !important;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }

    .block-container {
        padding-top: 2.2rem !important;
        padding-bottom: 8.5rem !important;
        max-width: 1380px !important;
    }

    /* Smooth Keyframe Animations */
    @keyframes fadeUp {
        from {
            opacity: 0;
            transform: translateY(14px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }

    @keyframes messageSlideIn {
        from {
            opacity: 0;
            transform: translateY(10px) scale(0.99);
        }
        to {
            opacity: 1;
            transform: translateY(0) scale(1);
        }
    }

    @keyframes floatIdle {
        0%, 100% {
            transform: translateY(0px);
            box-shadow: 0 10px 28px -6px rgba(255, 255, 255, 0.07), 0 0 0 1px rgba(255, 255, 255, 0.04);
        }
        50% {
            transform: translateY(-3px);
            box-shadow: 0 16px 34px -6px rgba(255, 255, 255, 0.11), 0 0 0 1px rgba(255, 255, 255, 0.08);
        }
    }

    @keyframes pulseWhite {
        0%, 100% { opacity: 1; transform: scale(1); }
        50% { opacity: 0.4; transform: scale(0.85); }
    }

    /* Header Styling */
    .header-title {
        font-size: 2.1rem;
        font-weight: 800;
        letter-spacing: -0.03em;
        color: #ffffff;
        margin: 0;
        line-height: 1.2;
        animation: fadeUp 0.6s cubic-bezier(0.16, 1, 0.3, 1) forwards;
    }

    .header-subtitle {
        color: #888888;
        font-size: 0.95rem;
        margin-top: 0.35rem;
        margin-bottom: 0;
        animation: fadeUp 0.7s cubic-bezier(0.16, 1, 0.3, 1) forwards;
    }

    .status-pill {
        display: inline-flex;
        align-items: center;
        gap: 0.45rem;
        background-color: #0a0a0a;
        border: 1px solid #262626;
        color: #e5e5e5;
        padding: 0.3rem 0.75rem;
        border-radius: 999px;
        font-size: 0.75rem;
        font-weight: 600;
        letter-spacing: 0.04em;
        margin-bottom: 0.65rem;
    }

    .status-dot {
        width: 7px;
        height: 7px;
        background-color: #ffffff;
        border-radius: 50%;
        animation: pulseWhite 2s infinite ease-in-out;
    }

    /* Top Refresh Button Styling */
    div.stButton > button {
        background-color: #0a0a0a !important;
        color: #ffffff !important;
        border: 1px solid #2a2a2a !important;
        border-radius: 25px !important;
        padding: 0.55rem 1.1rem !important;
        font-weight: 600 !important;
        font-size: 0.85rem !important;
        transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1) !important;
    }

    div.stButton > button:hover {
        background-color: #ffffff !important;
        color: #000000 !important;
        border-color: #ffffff !important;
        transform: translateY(-2px);
        box-shadow: 0 8px 20px rgba(255, 255, 255, 0.14);
    }

    div.stButton > button:active {
        transform: translateY(0px);
    }

    /* Monochrome KPI Cards */
    .kpi-card {
        background-color: #0a0a0a;
        border: 1px solid #1f1f1f;
        border-radius: 14px;
        padding: 1.45rem 1.35rem;
        transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
        animation: fadeUp 0.75s cubic-bezier(0.16, 1, 0.3, 1) forwards;
        position: relative;
    }

    .kpi-card:hover {
        border-color: #ffffff;
        background-color: #111111;
        transform: translateY(-4px);
        box-shadow: 0 12px 28px -8px rgba(255, 255, 255, 0.08);
    }

    .kpi-title {
        color: #888888;
        font-size: 0.78rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        margin-bottom: 0.55rem;
    }

    .kpi-value {
        color: #ffffff;
        font-size: 1.9rem;
        font-weight: 700;
        letter-spacing: -0.025em;
    }

    /* Native Streamlit Bordered Containers (Charts) */
    [data-testid="stVerticalBlockBorderWrapper"] {
        background-color: #0a0a0a !important;
        border: 1px solid #1f1f1f !important;
        border-radius: 14px !important;
        padding: 0.5rem !important;
        transition: border-color 0.3s ease, transform 0.3s ease;
        animation: fadeUp 0.85s cubic-bezier(0.16, 1, 0.3, 1) forwards;
    }

    [data-testid="stVerticalBlockBorderWrapper"]:hover {
        border-color: #404040 !important;
    }

    /* Clean Example Prompts Card */
    .prompts-card {
        background-color: #0a0a0a;
        border: 1px solid #1f1f1f;
        border-radius: 12px;
        padding: 1rem 1.25rem;
        margin-bottom: 1.25rem;
        animation: fadeUp 0.9s cubic-bezier(0.16, 1, 0.3, 1) forwards;
    }

    .prompts-label {
        color: #888888;
        font-size: 0.75rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        margin-bottom: 0.5rem;
        display: block;
    }

    .prompts-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
        gap: 0.55rem;
        margin-top: 0.45rem;
    }

    .prompt-chip {
        background-color: #000000;
        border: 1px solid #222222;
        border-radius: 8px;
        padding: 0.55rem 0.85rem;
        color: #d4d4d4;
        font-size: 0.84rem;
        transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1);
    }

    .prompt-chip:hover {
        border-color: #ffffff;
        color: #ffffff;
        transform: translateY(-2px);
        background-color: #0d0d0d;
    }

    /* Clean Monochrome Chat Messages */
    [data-testid="stChatMessage"] {
        background-color: #0b0b0b !important;
        border: 1px solid #1e1e1e !important;
        border-radius: 14px !important;
        padding: 1rem 1.25rem !important;
        margin-bottom: 0.85rem !important;
        animation: messageSlideIn 0.35s cubic-bezier(0.16, 1, 0.3, 1) forwards;
        transition: border-color 0.25s ease, transform 0.25s ease;
    }

    [data-testid="stChatMessage"]:hover {
        border-color: #3a3a3a !important;
        transform: translateX(2px);
    }

    [data-testid="stChatMessage"] p,
    [data-testid="stChatMessage"] li,
    [data-testid="stChatMessage"] span {
        color: #f5f5f5 !important;
        line-height: 1.65;
    }

    /* REMOVE GRAY BAR BEHIND CHAT INPUT */
    [data-testid="stBottom"],
    [data-testid="stBottom"] > div,
    [data-testid="stBottomBlockContainer"],
    [data-testid="stChatInput"] {
        background: transparent !important;
        background-color: transparent !important;
        border: none !important;
        box-shadow: none !important;
    }

    /* Compact Floating Chat Input (Idle / Collapsed) */
    [data-testid="stChatInput"] > div {
        box-sizing: border-box !important;
        background-color: #0c0c0c !important;
        border: 1px solid #2c2c2c !important;
        border-radius: 16px !important;
        width: 520px !important;
        max-width: 92vw !important;
        height: 54px !important;
        min-height: 54px !important;
        padding: 6px 10px 6px 16px !important;
        margin: 0 auto 0.65rem auto !important;
        display: flex !important;
        flex-direction: row !important;
        align-items: center !important;
        justify-content: space-between !important;
        gap: 8px !important;
        overflow: hidden !important;
        animation: floatIdle 4s ease-in-out infinite;
        transition:
            width 0.35s cubic-bezier(0.16, 1, 0.3, 1),
            height 0.35s cubic-bezier(0.16, 1, 0.3, 1),
            transform 0.3s cubic-bezier(0.16, 1, 0.3, 1),
            border-color 0.25s ease,
            box-shadow 0.25s ease,
            background-color 0.25s ease !important;
    }

    [data-testid="stChatInput"] > div:hover {
        border-color: #555555 !important;
        background-color: #101010 !important;
    }

    /* Locked Expanded State on Click / Focus */
    [data-testid="stChatInput"] > div.chat-expanded {
        animation: none !important;
        width: 1120px !important;
        max-width: 94vw !important;
        height: 96px !important;
        min-height: 96px !important;
        padding: 12px 14px 12px 18px !important;
        align-items: flex-end !important;
        background-color: #0b0b0b !important;
        border-color: #e5e5e5 !important;
        transform: translateY(-4px) !important;
        box-shadow: 0 18px 40px -8px rgba(255, 255, 255, 0.14), 0 0 0 1px rgba(255, 255, 255, 0.18) !important;
    }

    /* Ensure inner Streamlit wrappers don't clip or misalign text */
    [data-testid="stChatInput"] > div > div {
        box-sizing: border-box !important;
        flex: 1 1 auto !important;
        min-width: 0 !important;
        height: 100% !important;
        display: flex !important;
        align-items: center !important;
        background: transparent !important;
        border: none !important;
        overflow: hidden !important;
    }

    [data-testid="stChatInput"] > div.chat-expanded > div {
        align-items: stretch !important;
    }

    /* Textarea stays locked inside the box without escaping or pushing button out */
    [data-testid="stChatInput"] textarea {
        box-sizing: border-box !important;
        color: #ffffff !important;
        background: transparent !important;
        font-size: 0.95rem !important;
        line-height: 1.4 !important;
        height: 36px !important;
        min-height: 36px !important;
        max-height: 36px !important;
        padding: 8px 0 !important;
        margin: 0 !important;
        overflow-y: auto !important;
        overflow-x: hidden !important;
        resize: none !important;
        flex: 1 1 auto !important;
        width: 100% !important;
        min-width: 0 !important;
    }

    [data-testid="stChatInput"] > div.chat-expanded textarea {
        height: 70px !important;
        min-height: 70px !important;
        max-height: 70px !important;
        padding: 4px 0 !important;
        overflow-y: auto !important;
        resize: none !important;
    }

    [data-testid="stChatInput"] textarea::placeholder {
        color: #777777 !important;
        opacity: 1 !important;
    }

    /* Upward Send Button Always Visible Inside Right Side */
    [data-testid="stChatInput"] button {
        box-sizing: border-box !important;
        background-color: #1a1a1a !important;
        color: #ffffff !important;
        border: 1px solid #2e2e2e !important;
        border-radius: 10px !important;
        width: 36px !important;
        height: 36px !important;
        min-width: 36px !important;
        min-height: 36px !important;
        padding: 0 !important;
        margin: 0 !important;
        display: inline-flex !important;
        align-items: center !important;
        justify-content: center !important;
        flex-shrink: 0 !important;
        align-self: center !important;
        visibility: visible !important;
        opacity: 1 !important;
        position: static !important;
        transition: all 0.2s ease !important;
    }

    [data-testid="stChatInput"] > div.chat-expanded button {
        align-self: flex-end !important;
    }

    [data-testid="stChatInput"] button:hover {
        background-color: #ffffff !important;
        color: #000000 !important;
        border-color: #ffffff !important;
        transform: scale(1.06);
    }

    /* Download Button inside Chat */
    [data-testid="stDownloadButton"] > button {
        background-color: #111111 !important;
        color: #ffffff !important;
        border: 1px solid #333333 !important;
        border-radius: 8px !important;
        font-size: 0.82rem !important;
        transition: all 0.2s ease !important;
    }

    [data-testid="stDownloadButton"] > button:hover {
        background-color: #ffffff !important;
        color: #000000 !important;
        border-color: #ffffff !important;
        transform: translateY(-1px);
    }

    /* Subtle Divider */
    hr {
        border-color: #1a1a1a !important;
        margin: 1.75rem 0 !important;
    }
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


# BACKEND API HELPERS (HTTP Client)
@st.cache_data(ttl=30)
def fetch_kpis():
    """Fetch high-level business KPIs from backend."""
    try:
        with httpx.Client(base_url=API_BASE_URL, timeout=10.0) as client:
            resp = client.get("/api/analytics/kpi")
            if resp.status_code == 200:
                return resp.json()
    except Exception:
        return None
    return None


@st.cache_data(ttl=60)
def fetch_monthly_revenue():
    """Fetch 12-month revenue breakdown."""
    try:
        with httpx.Client(base_url=API_BASE_URL, timeout=10.0) as client:
            resp = client.get("/api/analytics/monthly-revenue")
            if resp.status_code == 200:
                return resp.json()
    except Exception:
        return None
    return None


@st.cache_data(ttl=60)
def fetch_top_products():
    """Fetch top 5 products by revenue."""
    try:
        with httpx.Client(base_url=API_BASE_URL, timeout=10.0) as client:
            resp = client.get("/api/analytics/top-products?n=5&metric=revenue")
            if resp.status_code == 200:
                return resp.json()
    except Exception:
        return None
    return None


def query_agent(question: str) -> dict:
    """Send natural language query to the AI Agent endpoint."""
    try:
        with httpx.Client(base_url=API_BASE_URL, timeout=45.0) as client:
            resp = client.post("/api/chat", json={"question": question})
            if resp.status_code == 200:
                return resp.json()
            return {"answer": f"⚠️ Backend error ({resp.status_code}): {resp.text}"}
    except Exception as e:
        return {"answer": f"⚠️ Connection failed to {API_BASE_URL}. Ensure FastAPI is running! ({str(e)})"}


# ─────────────────────────────────────────────────────────────
# MAIN DASHBOARD HEADER & TOP REFRESH BUTTON
# ─────────────────────────────────────────────────────────────
head_col1, head_col2 = st.columns([5, 1.2], vertical_alignment="center")

with head_col1:
    st.markdown(
        """
        <h1 class="header-title">AI Data Analyst & Business Intelligence</h1>
        <p class="header-subtitle">
            Real-time metrics & conversational AI analyst grounded in live sales data.
        </p>
        """,
        unsafe_allow_html=True
    )

with head_col2:
    st.write("")
    if st.button("Refresh Data", use_container_width=True):
        with st.spinner("Refreshing..."):
            st.cache_data.clear()
        st.rerun()

st.markdown("---")


# ─────────────────────────────────────────────────────────────
# SECTION 1: ANIMATED MONOCHROME KPI CARDS
# ─────────────────────────────────────────────────────────────
with st.spinner("Loading key metrics..."):
    kpi_data = fetch_kpis()

c1, c2, c3, c4 = st.columns(4)

if kpi_data:
    rev_str = f"₹{kpi_data['total_revenue']:,.2f}"
    orders_str = f"{kpi_data['total_orders']:,}"
    cust_str = f"{kpi_data['total_customers']:,}"
    aov_str = f"₹{kpi_data['average_order_value']:,.2f}"
else:
    rev_str, orders_str, cust_str, aov_str = "₹0.00", "0", "0", "₹0.00"

with c1:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-title">Total Revenue</div>
        <div class="kpi-value">{rev_str}</div>
    </div>
    """, unsafe_allow_html=True)

with c2:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-title">Completed Orders</div>
        <div class="kpi-value">{orders_str}</div>
    </div>
    """, unsafe_allow_html=True)

with c3:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-title">Registered Customers</div>
        <div class="kpi-value">{cust_str}</div>
    </div>
    """, unsafe_allow_html=True)

with c4:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-title">Avg Order Value (AOV)</div>
        <div class="kpi-value">{aov_str}</div>
    </div>
    """, unsafe_allow_html=True)

st.write("")


# ─────────────────────────────────────────────────────────────
# SECTION 2: MONOCHROME CHARTS & VISUALIZATIONS
# ─────────────────────────────────────────────────────────────
col_chart1, col_chart2 = st.columns([1.45, 1])

# Chart 1: Monthly Revenue Area Chart
with col_chart1:
    with st.container(border=True):
        st.markdown("#### Monthly Revenue Trend")
        with st.spinner("Loading monthly revenue chart..."):
            monthly_data = fetch_monthly_revenue()

        if monthly_data:
            df_monthly = pd.DataFrame(monthly_data)
            fig_monthly = px.area(
                df_monthly,
                x="month",
                y="revenue",
                labels={"revenue": "Revenue (₹)", "month": "Month"}
            )
            fig_monthly.update_traces(
                line=dict(width=2.5, color="#ffffff"),
                fillcolor="rgba(255, 255, 255, 0.10)",
                mode="lines+markers",
                marker=dict(size=6, color="#ffffff", line=dict(width=1.5, color="#000000"))
            )
            fig_monthly.update_layout(
                template="plotly_dark",
                paper_bgcolor="#0a0a0a",
                plot_bgcolor="#0a0a0a",
                font=dict(color="#a3a3a3", family="Inter, sans-serif"),
                xaxis=dict(gridcolor="#1a1a1a", zerolinecolor="#1a1a1a"),
                yaxis=dict(gridcolor="#1a1a1a", zerolinecolor="#1a1a1a"),
                margin=dict(l=15, r=15, t=15, b=15),
                height=310,
                hovermode="x unified",
                hoverlabel=dict(bgcolor="#000000", bordercolor="#ffffff", font_color="#ffffff")
            )
            st.plotly_chart(fig_monthly, use_container_width=True)
        else:
            st.info("No monthly revenue data available. Verify backend is running.")

# Chart 2: Top Products Horizontal Bar Chart
with col_chart2:
    with st.container(border=True):
        st.markdown("#### Top 5 Products by Revenue")
        with st.spinner("Loading product performance..."):
            top_prod_data = fetch_top_products()

        if top_prod_data:
            df_prod = pd.DataFrame(top_prod_data)
            df_prod = df_prod.sort_values(by="revenue", ascending=True)

            fig_prod = px.bar(
                df_prod,
                x="revenue",
                y="name",
                orientation="h",
                labels={"revenue": "Revenue (₹)", "name": ""}
            )
            fig_prod.update_traces(
                marker=dict(
                    color="#ffffff",
                    line=dict(color="#000000", width=0)
                ),
                opacity=0.92
            )
            fig_prod.update_layout(
                template="plotly_dark",
                paper_bgcolor="#0a0a0a",
                plot_bgcolor="#0a0a0a",
                font=dict(color="#a3a3a3", family="Inter, sans-serif"),
                xaxis=dict(gridcolor="#1a1a1a", zerolinecolor="#1a1a1a"),
                yaxis=dict(gridcolor="rgba(0,0,0,0)", tickfont=dict(color="#e5e5e5")),
                margin=dict(l=15, r=15, t=15, b=15),
                height=310,
                hoverlabel=dict(bgcolor="#000000", bordercolor="#ffffff", font_color="#ffffff")
            )
            st.plotly_chart(fig_prod, use_container_width=True)
        else:
            st.info("No product data available.")

st.markdown("---")


# ─────────────────────────────────────────────────────────────
# SECTION 3: CLEAN AI CONVERSATIONAL ANALYST
# ─────────────────────────────────────────────────────────────
st.markdown("### Ask the AI Data Analyst")
st.caption("Ask natural language business questions. The agent queries live database tools and returns grounded insights.")

st.markdown(
    """
    <div class="prompts-card">
        <span class="prompts-label">Suggested Queries</span>
        <div class="prompts-grid">
            <div class="prompt-chip">"What were the top 5 products by revenue?"</div>
            <div class="prompt-chip">"Why did revenue decline last month?"</div>
            <div class="prompt-chip">"How many customers are active vs inactive?"</div>
            <div class="prompt-chip">"Show me monthly revenue as a bar chart"</div>
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

# 1. Initialize chat history in session_state
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": "Hello! I am your AI Business Analyst. Ask me anything about your revenue, orders, products, or customers."
        }
    ]

# 2. Render all past chat messages
for idx, msg in enumerate(st.session_state.messages):
    avatar = "⚡" if msg["role"] == "assistant" else "👤"
    with st.chat_message(msg["role"], avatar=avatar):
        st.markdown(msg["content"])

        valid_chart = resolve_chart_path(msg.get("chart_path"))
        if valid_chart:
            st.image(valid_chart, use_container_width=True)
            with open(valid_chart, "rb") as file:
                st.download_button(
                    label="📥 Download Chart",
                    data=file,
                    file_name=os.path.basename(valid_chart),
                    mime="image/png",
                    key=f"dl_{os.path.basename(valid_chart)}_{idx}"
                )

# 3. Floating Expandable Chat Input bar
user_input = st.chat_input("Ask any business analytics question...")

components.html(
    """
    <script>
    (function() {
        const parentDoc = window.parent.document;
        const parentWin = window.parent;

        function getChatElements() {
            const chatBox = parentDoc.querySelector('[data-testid="stChatInput"] > div');
            const textarea = chatBox ? chatBox.querySelector('textarea') : null;
            return { chatBox, textarea };
        }

        function syncTextareaHeight(chatBox, textarea) {
            if (!chatBox || !textarea) return;
            const expanded = chatBox.classList.contains('chat-expanded');
            textarea.style.height = expanded ? '70px' : '36px';
        }

        function collapseIfEmpty() {
            const { chatBox, textarea } = getChatElements();
            if (!chatBox || !textarea) return;
            const hasText = textarea.value.trim().length > 0;
            const isFocused = parentDoc.activeElement === textarea;
            if (!hasText && !isFocused) {
                chatBox.classList.remove('chat-expanded');
            }
            syncTextareaHeight(chatBox, textarea);
        }

        function attachListeners() {
            const { chatBox, textarea } = getChatElements();
            if (!chatBox) return;

            if (!chatBox.dataset.bound) {
                chatBox.dataset.bound = "true";

                chatBox.addEventListener('click', (e) => {
                    if (e.target.closest('button')) return;
                    chatBox.classList.add('chat-expanded');
                    syncTextareaHeight(chatBox, textarea);
                    if (textarea) textarea.focus();
                });

                if (textarea) {
                    textarea.addEventListener('focus', () => {
                        chatBox.classList.add('chat-expanded');
                        syncTextareaHeight(chatBox, textarea);
                    });

                    textarea.addEventListener('input', () => {
                        chatBox.classList.add('chat-expanded');
                        syncTextareaHeight(chatBox, textarea);
                    });

                    textarea.addEventListener('blur', () => {
                        setTimeout(collapseIfEmpty, 100);
                    });
                }
            }

            if (!parentDoc.body.dataset.outsideCollapseBound) {
                parentDoc.body.dataset.outsideCollapseBound = "true";
                parentDoc.addEventListener('click', (e) => {
                    const { chatBox: currentBox, textarea: currentTa } = getChatElements();
                    if (!currentBox) return;
                    if (!currentBox.contains(e.target)) {
                        if (currentTa && parentDoc.activeElement === currentTa) {
                            currentTa.blur();
                        }
                        setTimeout(collapseIfEmpty, 100);
                    }
                }, true);
            }
        }

        attachListeners();
        const interval = setInterval(() => {
            attachListeners();
            collapseIfEmpty();
        }, 300);

        parentWin.addEventListener('beforeunload', () => clearInterval(interval));
    })();
    </script>
    """,
    height=0,
)

# 4. Handle prompt submission with clean status loader
if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user", avatar="👤"):
        st.markdown(user_input)

    with st.chat_message("assistant", avatar="⚡"):
        with st.status("Analyzing database & preparing response...", expanded=True) as status:
            st.write("Querying live sales records...")
            response = query_agent(user_input)
            answer_text = response.get("answer", "No answer received.")
            chart_path = response.get("chart_path")

            if not chart_path and "charts/" in answer_text:
                match = re.search(r"charts/[\w\-_]+\.png", answer_text)
                if match:
                    chart_path = match.group(0)

            valid_chart = resolve_chart_path(chart_path)
            status.update(label="Analysis complete", state="complete", expanded=False)

        st.markdown(answer_text)

        if valid_chart:
            st.image(valid_chart, use_container_width=True)
            with open(valid_chart, "rb") as file:
                st.download_button(
                    label="📥 Download Chart",
                    data=file,
                    file_name=os.path.basename(valid_chart),
                    mime="image/png",
                    key=f"dl_live_{os.path.basename(valid_chart)}_{len(st.session_state.messages)}"
                )

    st.session_state.messages.append({
        "role": "assistant",
        "content": answer_text,
        "chart_path": valid_chart
    })