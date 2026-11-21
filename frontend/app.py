import os
import re
from pathlib import Path
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

# backend URL
API_BASE_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

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


# LOAD SEPARATE CSS FILE
css_file = Path(__file__).parent / "style.css"
if css_file.exists():
    with open(css_file, "r", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


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
    """Send a natural language query to the AI Agent endpoint."""
    try:
        with httpx.Client(base_url=API_BASE_URL, timeout=45.0) as client:
            resp = client.post(
                "/api/chat",
                json={"question": question}
            )

            try:
                data = resp.json()
            except ValueError:
                data = {}

            if resp.is_success:
                return {
                    "question": data.get("question", question),
                    "answer": data.get("answer", "No answer received."),
                    "chart_path": data.get("chart_path")
                }

            error_message = (
                data.get("detail")
                or data.get("message")
                or resp.text
                or "Unknown backend error"
            )

            return {
                "question": question,
                "answer": f"Backend error ({resp.status_code}): {error_message}",
                "chart_path": None
            }

    except httpx.ConnectError:
        return {
            "question": question,
            "answer": (
                f"Connection failed to {API_BASE_URL}. "
                "Please ensure FastAPI is running."
            ),
            "chart_path": None
        }

    except httpx.TimeoutException:
        return {
            "question": question,
            "answer": "The AI agent took too long to respond. Please try again.",
            "chart_path": None
        }

    except httpx.RequestError as e:
        return {
            "question": question,
            "answer": f"Request failed: {str(e)}",
            "chart_path": None
        }

    except Exception as e:
        return {
            "question": question,
            "answer": f"Unexpected error: {str(e)}",
            "chart_path": None
        }


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
        with st.status("Analyzing & preparing response...", expanded=True) as status:
            st.write("Querying sales records...")
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
